"""Resolve an Estimation material requirement without re-reading source files.

This is deliberately a pure coordinator. Detection supplies the extracted
requirement and evidence; the coordinator only links it to a company's known
material or to Israel's approved pricing identity. Supplier SKUs are retained
in offer provenance but are never an input to matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Mapping, Sequence

from use_cases.material_identity_resolution import (
    _hard_compatibility,
    normalize_material_phrase,
)
from use_cases.material_price_resolver import _canonical_unit, _effective, _unit_price_multiplier
from use_cases.material_pricing_identity_resolution import (
    PricingIdentityResolution,
    resolve_material_pricing_identity,
)


EstimateMaterialStatus = Literal["resolved", "needs_review"]
EstimateMaterialAuthority = Literal["company", "israel_pricing"]


@dataclass(frozen=True)
class EstimateMaterialResolution:
    status: EstimateMaterialStatus
    authority: EstimateMaterialAuthority | None = None
    company_material_id: str | None = None
    pricing_identity_id: str | None = None
    offer_ids: tuple[str, ...] = ()
    pricing_identity_price_id: str | None = None
    price_low: Decimal | None = None
    price_typical: Decimal | None = None
    price_high: Decimal | None = None
    unit: str | None = None
    currency: str | None = None
    price_scope: str | None = None
    reason_codes: tuple[str, ...] = ()


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _valid_price_range(row: Mapping[str, Any], multiplier: Decimal) -> tuple[Decimal, Decimal, Decimal] | None:
    low = _decimal(row.get("price_low"))
    typical = _decimal(row.get("price_typical"))
    high = _decimal(row.get("price_high"))
    if low is None or typical is None or high is None or low < 0 or not low <= typical <= high:
        return None
    return low * multiplier, typical * multiplier, high * multiplier


def _company_candidates(
    *,
    requirement_name: str,
    material_family: str | None,
    specifications: Mapping[str, Any],
    company_material_items: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    normalized_name = normalize_material_phrase(requirement_name)
    if not normalized_name:
        return ()
    candidates: list[Mapping[str, Any]] = []
    for item in company_material_items:
        if str(item.get("status") or "private") == "archived":
            continue
        if normalize_material_phrase(item.get("normalized_name") or item.get("canonical_name")) != normalized_name:
            continue
        # Company `category` is a company-facing taxonomy, not the extraction
        # material family. It must not turn an otherwise explicit company
        # material into a false miss. Structured facts still reject conflicts.
        compatible, _matched = _hard_compatibility(
            item,
            category_code=None,
            specifications=specifications,
        )
        if compatible:
            candidates.append(item)
    return tuple(candidates)


def _company_offer_ids(
    *,
    company_material_id: str,
    company_offers: Sequence[Mapping[str, Any]],
    requested_unit: str,
    currency: str,
    price_scope: str,
    as_of: date,
) -> tuple[str, ...]:
    result: list[str] = []
    for offer in company_offers:
        if str(offer.get("company_material_id") or "") != company_material_id:
            continue
        if str(offer.get("status") or "") != "active" or not _effective(offer, as_of):
            continue
        if str(offer.get("currency") or "").upper() != currency:
            continue
        if str(offer.get("price_scope") or "material_only") != price_scope:
            continue
        if _unit_price_multiplier(str(offer.get("normalized_unit") or ""), requested_unit) is None:
            continue
        if _decimal(offer.get("normalized_price")) is None:
            continue
        offer_id = str(offer.get("offer_id") or "").strip()
        if offer_id:
            result.append(offer_id)
    return tuple(sorted(set(result)))


def _resolve_israel_price(
    *,
    identity: PricingIdentityResolution,
    pricing_identity_prices: Sequence[Mapping[str, Any]],
    requested_unit: str,
    currency: str,
    price_scope: str,
    as_of: date,
) -> EstimateMaterialResolution:
    if identity.status != "resolved" or not identity.selected_pricing_identity_id:
        return EstimateMaterialResolution(
            status="needs_review",
            reason_codes=identity.reason_codes or ("pricing_identity_requires_review",),
        )
    candidates: list[tuple[Mapping[str, Any], tuple[Decimal, Decimal, Decimal]]] = []
    for row in pricing_identity_prices:
        if str(row.get("pricing_identity_id") or "") != identity.selected_pricing_identity_id:
            continue
        if str(row.get("status") or "") != "active" or not _effective(row, as_of):
            continue
        if str(row.get("currency") or "").upper() != currency:
            continue
        if str(row.get("price_scope") or "") != price_scope:
            continue
        multiplier = _unit_price_multiplier(str(row.get("unit") or ""), requested_unit)
        if multiplier is None:
            continue
        price_range = _valid_price_range(row, multiplier)
        if price_range is not None:
            candidates.append((row, price_range))
    if len(candidates) != 1:
        return EstimateMaterialResolution(
            status="needs_review",
            pricing_identity_id=identity.selected_pricing_identity_id,
            reason_codes=("pricing_identity_price_not_found" if not candidates else "ambiguous_pricing_identity_price",),
        )
    row, (low, typical, high) = candidates[0]
    price_id = str(row.get("pricing_identity_price_id") or "").strip()
    if not price_id:
        return EstimateMaterialResolution(
            status="needs_review",
            pricing_identity_id=identity.selected_pricing_identity_id,
            reason_codes=("pricing_identity_price_id_missing",),
        )
    return EstimateMaterialResolution(
        status="resolved",
        authority="israel_pricing",
        pricing_identity_id=identity.selected_pricing_identity_id,
        pricing_identity_price_id=price_id,
        price_low=low,
        price_typical=typical,
        price_high=high,
        unit=requested_unit,
        currency=currency,
        price_scope=price_scope,
    )


def resolve_estimate_material_requirement(
    *,
    requirement_name: str,
    material_family: str | None,
    specifications: Mapping[str, Any] | None,
    requested_unit: str,
    company_material_items: Sequence[Mapping[str, Any]],
    company_offers: Sequence[Mapping[str, Any]],
    pricing_identities: Sequence[Mapping[str, Any]],
    pricing_identity_prices: Sequence[Mapping[str, Any]],
    market_code: str = "IL",
    currency: str = "ILS",
    price_scope: str = "material_only",
    as_of: date | None = None,
) -> EstimateMaterialResolution:
    """Use a unique compatible company material, else Israel pricing, else review."""

    unit = _canonical_unit(requested_unit)
    resolved_currency = str(currency or "").upper().strip()
    effective_date = as_of or date.today()
    if not unit:
        raise ValueError("requested_unit is required")
    if len(resolved_currency) != 3:
        raise ValueError("currency must be a three-letter code")
    facts = dict(specifications or {})
    company_candidates = _company_candidates(
        requirement_name=requirement_name,
        material_family=material_family,
        specifications=facts,
        company_material_items=company_material_items,
    )
    if len(company_candidates) > 1:
        return EstimateMaterialResolution(
            status="needs_review", reason_codes=("ambiguous_company_material",)
        )
    if len(company_candidates) == 1:
        company_material_id = str(company_candidates[0].get("company_material_id") or "").strip()
        offer_ids = _company_offer_ids(
            company_material_id=company_material_id,
            company_offers=company_offers,
            requested_unit=unit,
            currency=resolved_currency,
            price_scope=price_scope,
            as_of=effective_date,
        )
        if not offer_ids:
            return EstimateMaterialResolution(
                status="needs_review",
                company_material_id=company_material_id or None,
                reason_codes=("company_offer_not_usable",),
            )
        return EstimateMaterialResolution(
            status="resolved",
            authority="company",
            company_material_id=company_material_id,
            offer_ids=offer_ids,
            unit=unit,
            currency=resolved_currency,
            price_scope=price_scope,
        )
    identity = resolve_material_pricing_identity(
        material_family=material_family,
        specifications=facts,
        market_code=market_code,
        pricing_identities=pricing_identities,
    )
    return _resolve_israel_price(
        identity=identity,
        pricing_identity_prices=pricing_identity_prices,
        requested_unit=unit,
        currency=resolved_currency,
        price_scope=price_scope,
        as_of=effective_date,
    )
