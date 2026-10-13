"""Bridge Resolver-cleared catalog offers into Material Engine inputs.

This module deliberately has no database or UI dependency.  It converts
immutable Object Facts plus already-loaded catalog rows into a document-wide
plan. The runtime currently exposes that plan as diagnostics while the
project-level purchase-plan presentation is being connected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from use_cases.estimate_material_resolution import _company_candidates
from use_cases.material_engine import (
    MaterialDemand,
    MaterialEngineError,
    MaterialPlan,
    MaterialSupplyCandidate,
    plan_material_purchases,
)
from use_cases.material_identity_status import (
    material_identity_status,
    material_pricing_selection_key,
    pricing_policy_by_family_code,
)
from use_cases.material_price_resolver import _canonical_unit, _effective


_LINEAR_UNITS = frozenset({"lm", "mm", "cm"})
_REFERENCE_DISCRETE_PACKAGE_QUANTITIES = {
    "ea": Decimal("1"),
    "set": Decimal("1"),
    "pair": Decimal("2"),
    "dozen": Decimal("12"),
}


@dataclass(frozen=True)
class MaterialEngineShadow:
    """Read-only document-wide Material Engine outcome and explicit gaps."""

    plan: MaterialPlan | None
    demand_count: int
    candidate_count: int
    unresolved_requirement_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _positive(value: Any) -> Decimal | None:
    result = _decimal(value)
    return result if result is not None and result > 0 else None


def _ex_vat(value: Decimal, offer: Mapping[str, Any], vat_percent: Decimal) -> Decimal:
    return value / (Decimal("1") + vat_percent / Decimal("100")) if offer.get("vat_included") is True else value


def _offer_kind(offer: Mapping[str, Any]) -> str:
    dimensions = dict(offer.get("purchasable_dimensions") or {})
    has_length = _positive(dimensions.get("length_mm")) is not None
    has_width = _positive(dimensions.get("width_mm")) is not None
    unit = _canonical_unit(offer.get("normalized_unit"))
    if has_length and has_width:
        return "sheet"
    if has_length and unit in _LINEAR_UNITS:
        return "linear_stock"
    return "piece"


def _purchase_price_and_quantity(
    offer: Mapping[str, Any],
    *,
    kind: str,
    vat_percent: Decimal,
) -> tuple[Decimal, Decimal] | None:
    """Translate one source offer to one physical purchase unit, ex VAT.

    The stored source price is preferred whenever the source unit itself is a
    discrete purchase unit.  Where a source prices continuous stock by square
    or linear metre, the concrete supplier format determines the price of one
    sheet or bar.  No inferred waste factor is introduced here.
    """
    normalized_price = _positive(offer.get("normalized_price"))
    source_price = _positive(offer.get("source_price"))
    conversion = _positive(offer.get("conversion_factor"))
    normalized_unit = _canonical_unit(offer.get("normalized_unit"))
    dimensions = dict(offer.get("purchasable_dimensions") or {})
    if normalized_price is None:
        return None

    if kind == "sheet":
        length = _positive(dimensions.get("length_mm"))
        width = _positive(dimensions.get("width_mm"))
        if length is None or width is None:
            return None
        if normalized_unit == "sqm":
            return _ex_vat(normalized_price * length * width / Decimal("1000000"), offer, vat_percent), Decimal("1")
        if source_price is None:
            return None
        return _ex_vat(source_price, offer, vat_percent), Decimal("1")

    if kind == "linear_stock":
        length = _positive(dimensions.get("length_mm"))
        if length is None:
            return None
        if normalized_unit in _LINEAR_UNITS:
            metres = length / Decimal("1000")
            return _ex_vat(normalized_price * metres, offer, vat_percent), Decimal("1")
        if source_price is None:
            return None
        return _ex_vat(source_price, offer, vat_percent), Decimal("1")

    if source_price is not None:
        package_quantity = conversion if normalized_unit == "ea" and conversion is not None else Decimal("1")
        return _ex_vat(source_price, offer, vat_percent), package_quantity
    if conversion is None:
        return None
    return _ex_vat(normalized_price * conversion, offer, vat_percent), Decimal("1")


def company_supply_candidates(
    *,
    requirement_name: str,
    material_family: str,
    specifications: Mapping[str, Any] | None,
    company_material_items: Sequence[Mapping[str, Any]],
    company_offers: Sequence[Mapping[str, Any]],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    material_families: Sequence[Mapping[str, Any]],
    currency: str = "ILS",
    price_scope: str = "material_only",
    vat_percent: Decimal | int | float | str = Decimal("18"),
    as_of: date | None = None,
) -> tuple[str | None, tuple[MaterialSupplyCandidate, ...]]:
    """Return every physically purchasable, Estimate Ready company offer.

    This preserves Resolver compatibility but intentionally does not choose a
    winner.  Material Engine compares complete estimate-wide baskets later.
    """
    effective_date = as_of or date.today()
    normalized_currency = str(currency or "").upper().strip()
    vat = _positive(vat_percent)
    if len(normalized_currency) != 3 or vat is None:
        raise ValueError("currency and vat_percent are required")
    policies = pricing_policy_by_family_code(material_pricing_policies, families=material_families)
    selection_key = material_pricing_selection_key(
        material_family=material_family,
        specifications=specifications,
        pricing_policies=policies,
    )
    if selection_key is None:
        return None, ()
    facts = dict(specifications or {})
    result: list[MaterialSupplyCandidate] = []
    for item in _company_candidates(
        requirement_name=requirement_name,
        material_family=material_family,
        specifications=facts,
        company_material_items=company_material_items,
    ):
        item_key = material_pricing_selection_key(
            material_family=str((item.get("specifications") or {}).get("material_family") or ""),
            specifications=item.get("specifications") or {},
            pricing_policies=policies,
        )
        if item_key != selection_key:
            continue
        item_id = str(item.get("company_material_id") or "")
        for offer in company_offers:
            if str(offer.get("company_material_id") or "") != item_id:
                continue
            if str(offer.get("status") or "") != "active" or not _effective(offer, effective_date):
                continue
            if str(offer.get("currency") or "").upper() != normalized_currency:
                continue
            if str(offer.get("price_scope") or "material_only") != price_scope:
                continue
            status = material_identity_status(
                item, pricing_policies=policies,
                purchasable_dimensions=offer.get("purchasable_dimensions"),
            )
            if status.tone not in {"blue", "green"}:
                continue
            offer_id = str(offer.get("offer_id") or "").strip()
            if not offer_id:
                continue
            kind = _offer_kind(offer)
            price_and_quantity = _purchase_price_and_quantity(offer, kind=kind, vat_percent=vat)
            if price_and_quantity is None:
                continue
            price, package_quantity = price_and_quantity
            result.append(MaterialSupplyCandidate(
                candidate_id=f"company-offer:{offer_id}",
                material_family=material_family,
                selection_key=selection_key,
                purchase_kind=kind,
                price_per_purchase_unit=price,
                currency=normalized_currency,
                purchasable_dimensions=offer.get("purchasable_dimensions") or None,
                package_quantity=package_quantity,
                authority="company",
                offer_id=offer_id,
            ))
    return selection_key, tuple(sorted(result, key=lambda candidate: candidate.candidate_id))


def israel_reference_supply_candidates(
    *,
    material_family: str,
    specifications: Mapping[str, Any] | None,
    pricing_identities: Sequence[Mapping[str, Any]],
    pricing_identity_prices: Sequence[Mapping[str, Any]],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    material_families: Sequence[Mapping[str, Any]],
    family_supply_formats: Sequence[Mapping[str, Any]],
    currency: str = "ILS",
    price_scope: str = "material_only",
    as_of: date | None = None,
) -> tuple[str | None, tuple[MaterialSupplyCandidate, ...]]:
    """Return concrete Israel Reference candidates for one complete Pricing Key.

    A family format is paired only with a price expressed in its continuous
    basis: square metre for sheets and linear metre for stock. A reference
    price per sheet is never copied onto every generic family format, because
    the catalog does not establish that pairing. Discrete prices need no
    geometric format.
    """
    effective_date = as_of or date.today()
    normalized_currency = str(currency or "").upper().strip()
    if len(normalized_currency) != 3:
        raise ValueError("currency is required")
    policies = pricing_policy_by_family_code(material_pricing_policies, families=material_families)
    selection_key = material_pricing_selection_key(
        material_family=material_family,
        specifications=specifications,
        pricing_policies=policies,
    )
    if selection_key is None:
        return None, ()
    family_code = selection_key.split("|", 1)[0]
    family_id = str((policies.get(family_code) or {}).get("family_id") or "")
    prices_by_identity: dict[str, list[Mapping[str, Any]]] = {}
    for price in pricing_identity_prices:
        identity_id = str(price.get("pricing_identity_id") or "")
        if identity_id:
            prices_by_identity.setdefault(identity_id, []).append(price)
    formats = [
        row for row in family_supply_formats
        if row.get("active") is not False and str(row.get("family_id") or "") == family_id
    ]

    result: list[MaterialSupplyCandidate] = []
    for identity in pricing_identities:
        identity_id = str(identity.get("pricing_identity_id") or "").strip()
        attributes = dict(identity.get("price_attributes") or {})
        identity_key = material_pricing_selection_key(
            material_family=str(attributes.get("material_family") or material_family),
            specifications=attributes,
            pricing_policies=policies,
        )
        if not identity_id or identity_key != selection_key:
            continue
        for price in prices_by_identity.get(identity_id, ()):
            if str(price.get("status") or "") != "active" or not _effective(price, effective_date):
                continue
            if str(price.get("currency") or "").upper() != normalized_currency:
                continue
            if str(price.get("price_scope") or "") != price_scope:
                continue
            price_id = str(price.get("pricing_identity_price_id") or "").strip()
            typical = _positive(price.get("price_typical"))
            if not price_id or typical is None:
                continue
            unit = _canonical_unit(price.get("unit"))
            if unit == "sqm":
                for supply_format in formats:
                    dimensions = dict(supply_format.get("purchasable_dimensions") or {})
                    length = _positive(dimensions.get("length_mm"))
                    width = _positive(dimensions.get("width_mm"))
                    format_id = str(supply_format.get("supply_format_id") or "").strip()
                    if not format_id or length is None or width is None:
                        continue
                    result.append(MaterialSupplyCandidate(
                        candidate_id=f"israel-reference:{price_id}:{format_id}",
                        material_family=material_family,
                        selection_key=selection_key,
                        purchase_kind="sheet",
                        price_per_purchase_unit=typical * length * width / Decimal("1000000"),
                        currency=normalized_currency,
                        purchasable_dimensions=dimensions,
                        authority="israel_reference",
                        reference_price_id=price_id,
                    ))
            elif unit in _LINEAR_UNITS:
                for supply_format in formats:
                    dimensions = dict(supply_format.get("purchasable_dimensions") or {})
                    length = _positive(dimensions.get("length_mm"))
                    format_id = str(supply_format.get("supply_format_id") or "").strip()
                    if not format_id or length is None:
                        continue
                    result.append(MaterialSupplyCandidate(
                        candidate_id=f"israel-reference:{price_id}:{format_id}",
                        material_family=material_family,
                        selection_key=selection_key,
                        purchase_kind="linear_stock",
                        price_per_purchase_unit=typical * length / Decimal("1000"),
                        currency=normalized_currency,
                        purchasable_dimensions=dimensions,
                        authority="israel_reference",
                        reference_price_id=price_id,
                    ))
            elif unit in _REFERENCE_DISCRETE_PACKAGE_QUANTITIES:
                result.append(MaterialSupplyCandidate(
                    candidate_id=f"israel-reference:{price_id}",
                    material_family=material_family,
                    selection_key=selection_key,
                    purchase_kind="piece",
                    price_per_purchase_unit=typical,
                    currency=normalized_currency,
                    package_quantity=_REFERENCE_DISCRETE_PACKAGE_QUANTITIES[unit],
                    authority="israel_reference",
                    reference_price_id=price_id,
                ))
    return selection_key, tuple(sorted(result, key=lambda candidate: candidate.candidate_id))


def shadow_material_plan(
    *,
    facts_by_object: Mapping[str, Mapping[str, Any]],
    catalogs: Mapping[str, Sequence[Mapping[str, Any]]],
    vat_percent: Decimal | int | float | str = Decimal("18"),
) -> MaterialEngineShadow:
    """Build one document-wide plan from rectangular parts, without writes.

    Requirements without complete part geometry remain explicit gaps. They are
    not silently converted into an area percentage or invented price.
    """
    demands: list[MaterialDemand] = []
    candidates: dict[str, MaterialSupplyCandidate] = {}
    unresolved: list[str] = []
    reasons: set[str] = set()
    candidate_cache: dict[tuple[str, str, tuple[tuple[str, str], ...]], tuple[str | None, tuple[MaterialSupplyCandidate, ...]]] = {}

    for object_id, raw_facts in sorted(facts_by_object.items()):
        facts = raw_facts.get("facts_payload", raw_facts)
        if not isinstance(facts, Mapping):
            continue
        materials = {
            str(row.get("requirement_id") or ""): row
            for row in facts.get("materials") or []
            if isinstance(row, Mapping) and str(row.get("requirement_id") or "")
        }
        parts_by_requirement: dict[str, list[Mapping[str, Any]]] = {}
        for part in facts.get("parts") or []:
            if isinstance(part, Mapping):
                parts_by_requirement.setdefault(str(part.get("material_requirement_id") or ""), []).append(part)
        for requirement_id, material in sorted(materials.items()):
            parts = parts_by_requirement.get(requirement_id) or []
            if not parts:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("material_parts_missing")
                continue
            specs = dict(material.get("specification") or {})
            cache_key = (
                str(material.get("source_name") or material.get("family") or ""),
                str(material.get("family") or ""),
                tuple(sorted((str(key), str(value)) for key, value in specs.items())),
            )
            selection_key, company_candidates = candidate_cache.setdefault(
                cache_key,
                company_supply_candidates(
                    requirement_name=cache_key[0], material_family=cache_key[1], specifications=specs,
                    company_material_items=catalogs.get("items") or (),
                    company_offers=catalogs.get("offers") or (),
                    material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                    material_families=catalogs.get("material_families") or (),
                    vat_percent=vat_percent,
                ),
            )
            if selection_key is None:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("material_pricing_key_incomplete")
                continue
            _reference_key, reference_candidates = israel_reference_supply_candidates(
                material_family=cache_key[1],
                specifications=specs,
                pricing_identities=catalogs.get("identities") or (),
                pricing_identity_prices=catalogs.get("prices") or (),
                material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                material_families=catalogs.get("material_families") or (),
                family_supply_formats=catalogs.get("family_supply_formats") or (),
            )
            compatible = (*company_candidates, *reference_candidates)
            for candidate in compatible:
                candidates[candidate.candidate_id] = candidate
            candidate_ids = tuple(candidate.candidate_id for candidate in compatible)
            if not candidate_ids:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("assumption_required")
                continue
            for part in parts:
                demand_id = f"{object_id}:{part.get('part_id')}"
                try:
                    demands.append(MaterialDemand(
                        demand_id=demand_id,
                        object_id=str(object_id),
                        material_family=str(material.get("family") or ""),
                        selection_key=selection_key,
                        quantity=part.get("quantity"),
                        unit="piece",
                        compatible_candidate_ids=candidate_ids,
                        part_id=str(part.get("part_id") or "") or None,
                        length_mm=part.get("length_mm"),
                        width_mm=part.get("width_mm"),
                        rotation_allowed=bool(part.get("rotation_allowed")),
                    ))
                except MaterialEngineError:
                    unresolved.append(demand_id)
                    reasons.add("material_part_geometry_invalid")
    plan = plan_material_purchases(demands=demands, candidates=tuple(candidates.values())) if demands else None
    if plan and plan.status == "needs_review":
        unresolved.extend(plan.unresolved_demand_ids)
        reasons.update(plan.reason_codes)
    return MaterialEngineShadow(
        plan=plan,
        demand_count=len(demands),
        candidate_count=len(candidates),
        unresolved_requirement_ids=tuple(sorted(set(unresolved))),
        reason_codes=tuple(sorted(reasons)),
    )
