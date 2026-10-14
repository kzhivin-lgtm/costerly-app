"""Bridge Resolver-cleared catalog offers into Material Engine inputs.

This module deliberately has no database or UI dependency.  It converts
immutable Object Facts plus already-loaded catalog rows into a document-wide
plan. The runtime currently exposes that plan as diagnostics while the
project-level purchase-plan presentation is being connected.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
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


def _catalog_family_for_reference_identity(
    material_family: Any,
    *,
    pricing_policies: Mapping[str, Mapping[str, Any]],
) -> str | None:
    """Return a current Family code stored by an Israel Reference position."""
    raw = str(material_family or "").strip()
    return raw if raw in pricing_policies else None


@dataclass(frozen=True)
class MaterialEngineShadow:
    """Read-only document-wide Material Engine outcome and explicit gaps."""

    plan: MaterialPlan | None
    demand_count: int
    candidate_count: int
    unresolved_requirement_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    candidate_authorities: tuple[tuple[str, str], ...] = ()
    applied_defaults: tuple[Mapping[str, Any], ...] = ()


def material_plan_input_fingerprint(
    *,
    facts_by_object: Mapping[str, Mapping[str, Any]],
    material_norm_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    material_default_variants: Sequence[Mapping[str, Any]] = (),
) -> str:
    """Fingerprint the complete Material Engine input, including manual norms."""
    payload = {
        "facts_by_object": facts_by_object,
        "material_norm_overrides": {
            f"{object_id}:{requirement_id}": dict(value)
            for (object_id, requirement_id), value in sorted((material_norm_overrides or {}).items())
        },
        "material_default_variants": [
            dict(value) for value in sorted(
                material_default_variants,
                key=lambda row: (
                    str(row.get("family_id") or ""),
                    int(row.get("priority") or 0),
                    str(row.get("default_variant_id") or ""),
                ),
            )
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _allocation_weight(allocation: Any) -> Decimal:
    if allocation.area_mm2 is not None:
        return allocation.area_mm2
    if allocation.length_mm is not None and allocation.width_mm is not None:
        return allocation.length_mm * allocation.width_mm
    if allocation.length_mm is not None:
        return allocation.length_mm
    return allocation.quantity or Decimal("1")


def material_plan_object_cost_allocations(result: MaterialEngineShadow) -> dict[tuple[str, str], Decimal]:
    """Allocate every rounded project purchase cost back to its material demand."""
    result_by_requirement: dict[tuple[str, str], Decimal] = {}
    for line in result.plan.lines if result.plan else ():
        weights_by_requirement: dict[tuple[str, str], Decimal] = {}
        for allocation in line.allocations:
            if not allocation.material_requirement_id:
                continue
            weight = _allocation_weight(allocation)
            if weight <= 0:
                continue
            key = (allocation.object_id, str(allocation.material_requirement_id))
            weights_by_requirement[key] = weights_by_requirement.get(key, Decimal("0")) + weight
        denominator = sum(weights_by_requirement.values(), Decimal("0"))
        if denominator <= 0:
            continue
        total_cost = line.total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        allocated = Decimal("0")
        ordered = sorted(weights_by_requirement.items())
        for index, (key, weight) in enumerate(ordered):
            if index == len(ordered) - 1:
                allocated_cost = total_cost - allocated
            else:
                allocated_cost = (total_cost * weight / denominator).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP,
                )
                allocated += allocated_cost
            result_by_requirement[key] = result_by_requirement.get(key, Decimal("0")) + (
                allocated_cost
            )
    return result_by_requirement


def material_plan_snapshot(
    result: MaterialEngineShadow,
    *,
    input_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Serialize one Engine outcome for the estimate-level plan record.

    The snapshot preserves whole-purchase lines and per-part traceability. It
    also records the proportional allocation of shared purchase cost back to
    every object requirement, so Object Detail totals reconcile with the
    estimate-wide purchase plan.
    """
    plan = result.plan
    authorities = dict(result.candidate_authorities)
    lines = []
    for line in plan.lines if plan else ():
        lines.append({
            "selection_key": line.selection_key,
            "candidate_id": line.candidate_id,
            "authority": authorities.get(line.candidate_id),
            "purchase_kind": line.purchase_kind,
            "purchase_quantity": float(line.purchase_quantity),
            "price_per_purchase_unit": float(line.price_per_purchase_unit),
            "total_cost": float(line.total_cost),
            "currency": line.currency,
            "allocations": [
                {
                    "demand_id": allocation.demand_id,
                    "purchase_index": allocation.purchase_index,
                    "object_id": allocation.object_id,
                    "material_requirement_id": allocation.material_requirement_id,
                    "length_mm": None if allocation.length_mm is None else float(allocation.length_mm),
                    "width_mm": None if allocation.width_mm is None else float(allocation.width_mm),
                    "area_mm2": None if allocation.area_mm2 is None else float(allocation.area_mm2),
                    "quantity": None if allocation.quantity is None else float(allocation.quantity),
                    "rotated": allocation.rotated,
                }
                for allocation in line.allocations
            ],
        })
    return {
        "contract_version": "estimate_material_plan_v1",
        "status": plan.status if plan else "needs_review",
        "input_fingerprint": input_fingerprint,
        "algorithm_version": plan.algorithm_version if plan else "material_engine_v1",
        "demand_count": result.demand_count,
        "candidate_count": result.candidate_count,
        "lines": lines,
        "unresolved_requirement_ids": list(result.unresolved_requirement_ids),
        "reason_codes": list(result.reason_codes if result.reason_codes else (plan.reason_codes if plan else ())),
        "object_material_costs": [
            {
                "object_id": object_id,
                "material_requirement_id": requirement_id,
                "cost_ex_vat": float(cost),
            }
            for (object_id, requirement_id), cost in sorted(
                material_plan_object_cost_allocations(result).items()
            )
        ],
        "applied_material_defaults": [dict(value) for value in result.applied_defaults],
    }


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


def _canonical_requirement_unit(value: Any) -> str:
    return _canonical_unit(str(value or "")).replace("²", "2")


def _present_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _resolver_family_code(
    material_family: str,
    *,
    policies: Mapping[str, Mapping[str, Any]],
) -> str | None:
    family_code = str(material_family or "").strip()
    return family_code if family_code in policies else None


def _active_default_specifications(
    *,
    material_family: str,
    specifications: Mapping[str, Any],
    material_default_variants: Sequence[Mapping[str, Any]],
    pricing_identities: Sequence[Mapping[str, Any]],
    pricing_identity_prices: Sequence[Mapping[str, Any]],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    material_families: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    """Complete an evidenced family from a live Israel-backed default variant.

    Defaults fill only facts absent from OCR. They cannot infer a missing
    family and they become ineligible if their linked Israel price is inactive.
    """
    policies = pricing_policy_by_family_code(material_pricing_policies, families=material_families)
    family_code = _resolver_family_code(material_family, policies=policies)
    policy = policies.get(str(family_code or ""))
    family_id = str((policy or {}).get("family_id") or "")
    if not family_id:
        return dict(specifications), None
    identities = {
        str(row.get("pricing_identity_id") or ""): row
        for row in pricing_identities
        if str(row.get("market_code") or "IL") == "IL" and str(row.get("status") or "") == "active"
    }
    active_price_ids = {
        str(row.get("pricing_identity_id") or "")
        for row in pricing_identity_prices
        if str(row.get("status") or "") == "active"
        and str(row.get("price_scope") or "") == "material_only"
        and _positive(row.get("price_typical")) is not None
    }
    for variant in sorted(
        material_default_variants,
        key=lambda row: (int(row.get("priority") or 0), str(row.get("default_variant_id") or "")),
    ):
        if str(variant.get("family_id") or "") != family_id:
            continue
        identity_id = str(variant.get("reference_pricing_identity_id") or "")
        identity = identities.get(identity_id)
        if identity is None or identity_id not in active_price_ids:
            continue
        defaults = dict(variant.get("default_specifications") or {})
        applied = {key: value for key, value in defaults.items() if not _present_value(specifications.get(key))}
        if not applied:
            continue
        effective = {**specifications, **applied}
        selection_key = material_pricing_selection_key(
            material_family=material_family,
            specifications=effective,
            pricing_policies=policies,
        )
        identity_attributes = dict(identity.get("price_attributes") or {})
        identity_family = _catalog_family_for_reference_identity(
            identity_attributes.get("material_family") or material_family,
            pricing_policies=policies,
        )
        identity_key = material_pricing_selection_key(
            material_family=str(identity_family or ""),
            specifications={**identity_attributes, "material_family": identity_family},
            pricing_policies=policies,
        )
        if selection_key is None or identity_key != selection_key:
            continue
        return effective, {
            "default_variant_id": str(variant.get("default_variant_id") or ""),
            "reference_pricing_identity_id": identity_id,
            "family_code": family_code,
            "applied_specifications": applied,
        }
    return dict(specifications), None


def _demand_from_net_requirement(
    *,
    demand_id: str,
    object_id: str,
    requirement_id: str,
    material_family: str,
    selection_key: str,
    total_quantity: Decimal,
    unit: str,
    candidate_ids: tuple[str, ...],
) -> MaterialDemand | None:
    normalized = _canonical_requirement_unit(unit)
    common = {
        "demand_id": demand_id,
        "object_id": object_id,
        "material_requirement_id": requirement_id,
        "material_family": material_family,
        "selection_key": selection_key,
        "quantity": Decimal("1"),
        "unit": unit,
        "compatible_candidate_ids": candidate_ids,
    }
    if normalized in {"m2", "sqm", "square_meter", "square_metre"}:
        return MaterialDemand(**common, area_mm2=total_quantity * Decimal("1000000"))
    if normalized in {"m", "lm", "linear_meter", "linear_metre"}:
        return MaterialDemand(**common, linear_length_mm=total_quantity * Decimal("1000"))
    if normalized in {"mm", "cm"}:
        multiplier = Decimal("10") if normalized == "cm" else Decimal("1")
        return MaterialDemand(**common, linear_length_mm=total_quantity * multiplier)
    if normalized in {"piece", "ea", "set", "pair", "dozen", "sheet"}:
        return MaterialDemand(**{**common, "quantity": total_quantity})
    return None


def _direct_count_unit(candidates: Sequence[MaterialSupplyCandidate]) -> str | None:
    """Allow an extracted count only for an unambiguously discrete material.

    A raw count without rectangular parts cannot establish metres or square
    metres. It can still be a useful fact for hinges, handles and other
    discrete hardware, provided every Resolver-cleared candidate is a
    discrete purchase. The candidate, not the extraction model, supplies the
    unit.
    """
    return "piece" if candidates and all(candidate.purchase_kind == "piece" for candidate in candidates) else None


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
        identity_family = _catalog_family_for_reference_identity(
            attributes.get("material_family") or material_family,
            pricing_policies=policies,
        )
        if identity_family is None:
            continue
        identity_key = material_pricing_selection_key(
            material_family=identity_family,
            specifications={**attributes, "material_family": identity_family},
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
    material_norm_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    vat_percent: Decimal | int | float | str = Decimal("18"),
) -> MaterialEngineShadow:
    """Build one document-wide purchase plan from facts and approved norms.

    Geometry remains preferred for sheets and stock. A user-edited per-item
    norm is deliberately converted to an aggregate physical demand instead of
    fabricating new cut dimensions.
    """
    demands: list[MaterialDemand] = []
    candidates: dict[str, MaterialSupplyCandidate] = {}
    unresolved: list[str] = []
    reasons: set[str] = set()
    applied_defaults: list[Mapping[str, Any]] = []
    candidate_cache: dict[tuple[str, str, tuple[tuple[str, str], ...]], tuple[str | None, tuple[MaterialSupplyCandidate, ...]]] = {}

    overrides = material_norm_overrides or {}
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
            specs, default_trace = _active_default_specifications(
                material_family=str(material.get("family") or ""),
                specifications=dict(material.get("specification") or {}),
                material_default_variants=catalogs.get("material_default_variants") or (),
                pricing_identities=catalogs.get("identities") or (),
                pricing_identity_prices=catalogs.get("prices") or (),
                material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                material_families=catalogs.get("material_families") or (),
            )
            if default_trace is not None:
                applied_defaults.append({
                    "object_id": str(object_id),
                    "material_requirement_id": requirement_id,
                    **default_trace,
                })
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
            override = overrides.get((str(object_id), requirement_id))
            object_quantity = _positive(facts.get("quantity")) or Decimal("1")
            material_quantity = _positive(material.get("quantity"))
            if override:
                override_unit = str(override.get("unit") or "")
                override_quantity = _positive(override.get("quantity_per_item"))
                if override_quantity is None or _canonical_requirement_unit(override_unit) != _canonical_requirement_unit(material.get("unit")):
                    unresolved.append(f"{object_id}:{requirement_id}")
                    reasons.add("manual_material_norm_invalid")
                    continue
                material_quantity = override_quantity * object_quantity
                direct_demand = _demand_from_net_requirement(
                    demand_id=f"{object_id}:{requirement_id}:manual-norm",
                    object_id=str(object_id),
                    requirement_id=requirement_id,
                    material_family=str(material.get("family") or ""),
                    selection_key=selection_key,
                    total_quantity=material_quantity,
                    unit=override_unit,
                    candidate_ids=candidate_ids,
                )
                if direct_demand is None:
                    unresolved.append(f"{object_id}:{requirement_id}")
                    reasons.add("manual_material_norm_unit_unsupported")
                    continue
                demands.append(direct_demand)
                reasons.add("manual_material_norm_without_geometry")
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
                        material_requirement_id=requirement_id,
                        length_mm=part.get("length_mm"),
                        width_mm=part.get("width_mm"),
                        rotation_allowed=bool(part.get("rotation_allowed")),
                    ))
                except MaterialEngineError:
                    unresolved.append(demand_id)
                    reasons.add("material_part_geometry_invalid")
            if parts:
                continue
            if material_quantity is None:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("material_quantity_missing")
                continue
            # Explicit historical/manual units remain supported. Newly
            # extracted V3 facts leave this null and obtain a unit only from a
            # discrete resolved candidate.
            direct_unit = str(material.get("unit") or "").strip() or _direct_count_unit(compatible)
            if direct_unit is None:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("material_geometry_required")
                continue
            direct_demand = _demand_from_net_requirement(
                demand_id=f"{object_id}:{requirement_id}:net-demand",
                object_id=str(object_id),
                requirement_id=requirement_id,
                material_family=str(material.get("family") or ""),
                selection_key=selection_key,
                total_quantity=material_quantity,
                unit=direct_unit,
                candidate_ids=candidate_ids,
            )
            if direct_demand is None:
                unresolved.append(f"{object_id}:{requirement_id}")
                reasons.add("material_unit_unsupported_for_purchase_plan")
                continue
            demands.append(direct_demand)
    plan = plan_material_purchases(demands=demands, candidates=tuple(candidates.values())) if demands else None
    if plan and unresolved:
        # A partially priced document is not Final Approval-ready. Keep the
        # resolved purchase lines as traceable diagnostics, but carry every
        # earlier Resolver gap into the plan status rather than allowing one
        # successful demand to turn the whole estimate green.
        plan = replace(
            plan,
            status="needs_review",
            unresolved_demand_ids=tuple(sorted(set((*plan.unresolved_demand_ids, *unresolved)))),
            reason_codes=tuple(sorted(set((*plan.reason_codes, *reasons)))),
        )
    if plan and plan.status == "needs_review":
        unresolved.extend(plan.unresolved_demand_ids)
        reasons.update(plan.reason_codes)
    return MaterialEngineShadow(
        plan=plan,
        demand_count=len(demands),
        candidate_count=len(candidates),
        unresolved_requirement_ids=tuple(sorted(set(unresolved))),
        reason_codes=tuple(sorted(reasons)),
        candidate_authorities=tuple(sorted(
            (candidate_id, candidate.authority)
            for candidate_id, candidate in candidates.items()
        )),
        applied_defaults=tuple(sorted(
            applied_defaults,
            key=lambda row: (str(row["object_id"]), str(row["material_requirement_id"])),
        )),
    )
