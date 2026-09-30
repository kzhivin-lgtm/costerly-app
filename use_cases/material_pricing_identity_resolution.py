"""Resolve an estimation price class without pretending to know an exact SKU.

The Price Source sees supplier language. The canonical catalog records detailed
physical variants. This resolver sits between them and only answers the
question relevant to an estimate: which approved price class applies?
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal, Mapping, Sequence

from use_cases.material_identity_resolution import (
    _specification_equal,
    normalize_material_phrase,
)


PricingIdentityStatus = Literal["resolved", "shortlist", "needs_review"]

# These words must never be promoted into a pricing identity. They remain
# evidence, useful for an eventual human review and for a supplier's own list.
IGNORED_PRICE_VARIATION_FIELDS = frozenset(
    {
        "colour",
        "color",
        "decor",
        "pattern",
        "supplier_sku",
        "supplier_name",
        "marketing_name",
    }
)


@dataclass(frozen=True)
class PricingIdentityCandidate:
    pricing_identity_id: str
    score: Decimal
    matched_price_attributes: tuple[str, ...]


@dataclass(frozen=True)
class PricingIdentityResolution:
    status: PricingIdentityStatus
    selected_pricing_identity_id: str | None = None
    candidates: tuple[PricingIdentityCandidate, ...] = ()
    reason_codes: tuple[str, ...] = ()


PricingIdentityIndex = Mapping[tuple[str, str], tuple[Mapping[str, Any], ...]]


def _value(value: Any) -> str:
    return normalize_material_phrase(value)


def _effective_attributes(
    *,
    material_family: str | None,
    specifications: Mapping[str, Any] | None,
) -> dict[str, Any]:
    values = {
        key: value
        for key, value in dict(specifications or {}).items()
        if value not in (None, "", [], {}) and key not in IGNORED_PRICE_VARIATION_FIELDS
    }
    if material_family:
        family = _value(material_family)
        family = {
            "birch plywood": "plywood",
            "all birch plywood": "plywood",
            "mdf board": "mdf",
            "solid timber laminated": "laminated solid wood panel",
            "solid timber lami": "laminated solid wood panel",
            "solid timber butcher block": "laminated solid wood panel",
            "butcher block panel": "laminated solid wood panel",
        }.get(family, family)
        values["material_family"] = family
    return values


def build_material_pricing_identity_index(
    pricing_identities: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], tuple[Mapping[str, Any], ...]]:
    """Bucket active identities by the one mandatory matching fact: material family.

    Family-less identities remain available in every same-market bucket because
    the legacy resolver permits them. This preserves resolution behaviour while
    avoiding a full scan of unrelated material families for every source row.
    """
    familyless_by_market: dict[str, list[Mapping[str, Any]]] = {}
    by_market_and_family: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    active_identities: list[tuple[str, str, Mapping[str, Any]]] = []
    for identity in pricing_identities:
        market = str(identity.get("market_code") or "").upper().strip()
        if not market or str(identity.get("status") or "") != "active":
            continue
        family = _value((identity.get("price_attributes") or {}).get("material_family"))
        active_identities.append((market, family, identity))
        if family:
            by_market_and_family.setdefault((market, family), []).append(identity)
        else:
            familyless_by_market.setdefault(market, []).append(identity)

    result: dict[tuple[str, str], tuple[Mapping[str, Any], ...]] = {}
    for market, family, _identity in active_identities:
        if not family or (market, family) in result:
            continue
        result[(market, family)] = tuple(
            by_market_and_family[(market, family)] + familyless_by_market.get(market, [])
        )
    return result


def _compatible(
    identity: Mapping[str, Any], requested: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    attributes = dict(identity.get("price_attributes") or {})
    matched: list[str] = []
    for key, requested_value in requested.items():
        if key not in attributes:
            continue
        if not _specification_equal(requested_value, attributes[key]):
            return False, ()
        matched.append(key)
    # A class with a material family must not be chosen merely because the
    # incoming row says nothing. Its family is a necessary price-bearing fact.
    if attributes.get("material_family") and "material_family" not in matched:
        return False, ()
    return True, tuple(sorted(matched))


def resolve_material_pricing_identity(
    *,
    material_family: str | None,
    specifications: Mapping[str, Any] | None,
    market_code: str,
    pricing_identities: Sequence[Mapping[str, Any]],
    pricing_identity_index: PricingIdentityIndex | None = None,
    shortlist_limit: int = 5,
) -> PricingIdentityResolution:
    """Return one safe estimation class, never a decoration-driven pseudo-match."""

    if shortlist_limit < 1 or shortlist_limit > 5:
        raise ValueError("shortlist_limit must be between 1 and 5")
    market = str(market_code or "").upper().strip()
    requested = _effective_attributes(
        material_family=material_family,
        specifications=specifications,
    )
    if not _value(requested.get("material_family")):
        return PricingIdentityResolution(
            status="needs_review", reason_codes=("pricing_material_family_missing",)
        )

    requested_family = _value(requested.get("material_family"))
    identities_to_consider = (
        pricing_identity_index.get((market, requested_family), ())
        if pricing_identity_index is not None
        else pricing_identities
    )
    candidates: list[PricingIdentityCandidate] = []
    for identity in identities_to_consider:
        if str(identity.get("market_code") or "").upper() != market:
            continue
        if str(identity.get("status") or "") != "active":
            continue
        compatible, matched = _compatible(identity, requested)
        if not compatible:
            continue
        price_attributes = dict(identity.get("price_attributes") or {})
        # More requested price-bearing facts is stronger. Fewer unproven facts
        # is safer, so raw plywood 4 mm beats an arbitrary birch grade when the
        # supplier only stated raw plywood 4 mm.
        unproven = len(set(price_attributes) - set(matched))
        score = Decimal("100") + Decimal(len(matched) * 10) - Decimal(unproven)
        candidates.append(
            PricingIdentityCandidate(
                pricing_identity_id=str(identity["pricing_identity_id"]),
                score=score,
                matched_price_attributes=matched,
            )
        )
    candidates.sort(key=lambda row: (-row.score, row.pricing_identity_id))
    if candidates and (len(candidates) == 1 or candidates[0].score > candidates[1].score):
        return PricingIdentityResolution(
            status="resolved",
            selected_pricing_identity_id=candidates[0].pricing_identity_id,
            candidates=tuple(candidates[:shortlist_limit]),
        )
    if candidates:
        return PricingIdentityResolution(
            status="shortlist",
            candidates=tuple(candidates[:shortlist_limit]),
            reason_codes=("ambiguous_pricing_identity",),
        )
    return PricingIdentityResolution(
        status="needs_review", reason_codes=("pricing_identity_not_found",)
    )
