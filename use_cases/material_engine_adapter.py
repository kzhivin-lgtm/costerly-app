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
import re
from typing import Any, Mapping, Sequence

from use_cases.material_identity_resolution import _hard_compatibility, normalize_material_phrase
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
    pricing_key_fact_fields,
    pricing_policy_by_family_code,
)
from use_cases.material_price_resolver import _canonical_unit, _effective
from use_cases.metal_mass_calculator import kilograms_per_metre, kilograms_per_sheet
from use_cases.estimation_assumption_price_contract import (
    ASSUMPTION_PRICE_V1,
    validate_assumption_price_v1,
)


_LINEAR_UNITS = frozenset({"lm", "mm", "cm"})
_REFERENCE_DISCRETE_PACKAGE_QUANTITIES = {
    "ea": Decimal("1"),
    "set": Decimal("1"),
    "pair": Decimal("2"),
    "dozen": Decimal("12"),
}
_PHYSICAL_PURCHASABLE_DIMENSION_KEYS = frozenset({
    "length_mm", "width_mm", "height_mm", "thickness_mm", "diameter_mm",
})
_DRAWER_SLIDE_LAST_RESORT_DEPTH_MM = 400
_ASSUMPTION_ALLOWANCE_ILS = Decimal("200")
_ASSUMPTION_SHEET_DIMENSIONS = {"length_mm": Decimal("2440"), "width_mm": Decimal("1220")}


def _complete_common_sheet_finish(*, material_family: str, source_name: object, specifications: Mapping[str, Any]) -> dict[str, Any]:
    effective = dict(specifications)
    phrase = normalize_material_phrase(str(source_name or ""))
    if material_family == "mdf_hdf" and not _present_value(effective.get("board_type")):
        effective["board_type"] = "mdf"
    if material_family == "mdf_hdf" and "veneer" in phrase and not _present_value(effective.get("surface")):
        effective["surface"] = "veneer_two_sided"
    return effective


@dataclass(frozen=True)
class MaterialEngineResult:
    """Document-wide Material Engine outcome and explicit catalog gaps."""

    plan: MaterialPlan | None
    demand_count: int
    candidate_count: int
    unresolved_requirement_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    candidate_authorities: tuple[tuple[str, str], ...] = ()
    candidate_display_names: tuple[tuple[str, str], ...] = ()
    candidate_purchase_forms: tuple[tuple[str, Mapping[str, Any]], ...] = ()
    applied_defaults: tuple[Mapping[str, Any], ...] = ()
    assumption_fallbacks: tuple[Mapping[str, Any], ...] = ()


def material_plan_input_fingerprint(
    *,
    facts_by_object: Mapping[str, Mapping[str, Any]],
    material_norm_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    material_purchase_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    material_default_variants: Sequence[Mapping[str, Any]] = (),
) -> str:
    """Fingerprint the complete Material Engine input, including manual norms."""
    payload = {
        "facts_by_object": facts_by_object,
        "material_norm_overrides": {
            f"{object_id}:{requirement_id}": dict(value)
            for (object_id, requirement_id), value in sorted((material_norm_overrides or {}).items())
        },
        "material_purchase_overrides": {str(key): dict(value) for key, value in sorted((material_purchase_overrides or {}).items())},
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


def _apply_purchase_quantity_overrides(plan: MaterialPlan | None, overrides: Mapping[str, Mapping[str, Any]]) -> MaterialPlan | None:
    if plan is None or not overrides:
        return plan
    return replace(plan, lines=tuple(
        replace(line, purchase_quantity=quantity, total_cost=line.price_per_purchase_unit * quantity, purchase_quantity_is_manual=True)
        if (quantity := _positive((overrides.get(line.selection_key) or {}).get("purchase_quantity"))) is not None else line
        for line in plan.lines
    ))


def _allocation_weight(allocation: Any) -> Decimal:
    if allocation.area_mm2 is not None:
        return allocation.area_mm2
    if allocation.length_mm is not None and allocation.width_mm is not None:
        return allocation.length_mm * allocation.width_mm
    if allocation.length_mm is not None:
        return allocation.length_mm
    return allocation.quantity or Decimal("1")


def material_plan_object_cost_allocations(result: MaterialEngineResult) -> dict[tuple[str, str], Decimal]:
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
    result: MaterialEngineResult,
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
    display_names = dict(result.candidate_display_names)
    purchase_forms = dict(result.candidate_purchase_forms)
    lines = []
    for line in plan.lines if plan else ():
        lines.append({
            "selection_key": line.selection_key,
            "candidate_id": line.candidate_id,
            "authority": authorities.get(line.candidate_id),
            "display_name": display_names.get(line.candidate_id),
            "purchase_kind": line.purchase_kind,
            "purchasable_dimensions": dict(
                purchase_forms.get(line.candidate_id, {}).get("purchasable_dimensions") or {}
            ),
            "package_quantity": purchase_forms.get(line.candidate_id, {}).get("package_quantity"),
            "purchase_quantity": float(line.purchase_quantity),
            "purchase_quantity_is_manual": line.purchase_quantity_is_manual,
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
        "algorithm_version": plan.algorithm_version if plan else "material_engine_v2",
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
        "assumption_fallbacks": [dict(value) for value in result.assumption_fallbacks],
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


def _physical_purchase_dimensions(value: Mapping[str, Any] | None) -> dict[str, float]:
    """Expose physical format dimensions, never catalog provenance metadata."""
    result: dict[str, float] = {}
    for key, raw in dict(value or {}).items():
        if str(key) not in _PHYSICAL_PURCHASABLE_DIMENSION_KEYS:
            continue
        numeric = _positive(raw)
        if numeric is not None:
            result[str(key)] = float(numeric)
    return result


def _canonical_requirement_unit(value: Any) -> str:
    return _canonical_unit(str(value or "")).replace("²", "2")


def _assumption_selection_key(*, material_family: str, object_id: str, requirement_id: str) -> str:
    """Keep no-source allowance groups deterministic without pretending C or I matched."""
    family = re.sub(r"[^a-z0-9_.:-]+", "_", str(material_family or "material").casefold()).strip("_")
    requirement = re.sub(r"[^a-z0-9_.:-]+", "_", str(requirement_id or "requirement").casefold()).strip("_")
    return f"assumption:{object_id}:{family or 'material'}:{requirement or 'requirement'}"


def _assumption_candidate(
    *, object_id: str, requirement_id: str, material: Mapping[str, Any],
    selection_key: str | None, parts: Sequence[Mapping[str, Any]], reason_code: str,
) -> tuple[MaterialSupplyCandidate, dict[str, Any]]:
    """Create the mandatory, visibly low-confidence A purchase candidate.

    The price is an explicit ILS allowance, not a hidden C/I catalog match.
    Geometry receives a conventional whole sheet so the ordinary project-wide
    nesting algorithm still determines how many allowance sheets are needed.
    """
    material_family = str(material.get("family") or "material")
    has_sheet_geometry = any(
        _positive(part.get("length_mm")) is not None and _positive(part.get("width_mm")) is not None
        for part in parts
    )
    raw_unit = str(material.get("unit") or "").strip()
    normalized_unit = _canonical_requirement_unit(raw_unit)
    if has_sheet_geometry:
        # The A fallback must remain physically capable of producing every
        # declared finished panel. Do not recycle a conventional 2440x1220
        # sheet when the evidence requires a larger one, and never split the
        # panel to make a catalogue format appear compatible.
        max_length = max(_positive(part.get("length_mm")) or Decimal("0") for part in parts)
        max_width = max(_positive(part.get("width_mm")) or Decimal("0") for part in parts)
        dimensions = {
            "length_mm": max(_ASSUMPTION_SHEET_DIMENSIONS["length_mm"], max_length + Decimal("3")),
            "width_mm": max(_ASSUMPTION_SHEET_DIMENSIONS["width_mm"], max_width + Decimal("3")),
        }
        purchase_kind, rationale_unit = "sheet", "sheet"
    elif normalized_unit in {"m", "mm", "cm", "lm"} or material_family == "edge_banding":
        purchase_kind, rationale_unit, dimensions = "linear_cut", "m", None
    elif material_family.startswith("hardware_") or normalized_unit in {"ea", "piece", "set", "pair"}:
        purchase_kind, rationale_unit, dimensions = "piece", "piece", None
    else:
        purchase_kind, rationale_unit, dimensions = "direct", "piece", None
    # An A is a priced estimate-local fallback, not a physically compatible
    # substitute for another demand which merely shares the same incomplete
    # C/I pricing key.  Keep it requirement-scoped so, for example, a painted
    # facade sheet and an unspecified paint finish never need one impossible
    # purchase candidate to satisfy both a sheet and a direct demand.
    resolved_key = _assumption_selection_key(
        material_family=material_family, object_id=object_id, requirement_id=requirement_id,
    )
    assumption_price = validate_assumption_price_v1({
        "contract_version": ASSUMPTION_PRICE_V1,
        "material_requirement_id": requirement_id,
        "amount": float(_ASSUMPTION_ALLOWANCE_ILS), "currency": "ILS", "unit": rationale_unit,
        "confidence": 0, "basis_kind": "estimator_allowance",
        "rationale": [
            "No compatible Company Catalog or Israel Reference purchase candidate was available.",
            f"A fixed 200 ILS allowance was applied for {rationale_unit} ({reason_code}).",
        ],
        "source_candidates": [],
    })
    candidate = MaterialSupplyCandidate(
        candidate_id=f"assumption:{object_id}:{requirement_id}:{purchase_kind}",
        material_family=material_family, selection_key=resolved_key,
        purchase_kind=purchase_kind, price_per_purchase_unit=_ASSUMPTION_ALLOWANCE_ILS,
        currency="ILS", purchasable_dimensions=dimensions, authority="assumption",
        display_name=str(material.get("source_name") or material_family),
    )
    fallback = {
        "object_id": object_id, "material_requirement_id": requirement_id,
        "source_name": str(material.get("source_name") or material_family),
        "material_family": material_family, "specification": dict(material.get("specification") or {}),
        "selection_key": resolved_key, "quantity_per_item": None, "unit": rationale_unit,
        "reason_code": reason_code, "resolution": "assumption_fallback",
        "assumption_price": assumption_price,
    }
    return candidate, fallback


def _sheet_candidate_fits_finished_parts(
    candidate: MaterialSupplyCandidate, parts: Sequence[Mapping[str, Any]],
) -> bool:
    """Return whether one stock sheet can physically produce every part type."""
    if candidate.purchase_kind != "sheet":
        return False
    dimensions = dict(candidate.purchasable_dimensions or {})
    stock_length = _positive(dimensions.get("length_mm"))
    stock_width = _positive(dimensions.get("width_mm"))
    kerf = _positive(candidate.kerf_mm) or Decimal("0")
    if stock_length is None or stock_width is None:
        return False
    for part in parts:
        length = _positive(part.get("length_mm"))
        width = _positive(part.get("width_mm"))
        if length is None or width is None:
            return False
        unrotated = length + kerf <= stock_length and width + kerf <= stock_width
        rotated = bool(part.get("rotation_allowed")) and width + kerf <= stock_length and length + kerf <= stock_width
        if not unrotated and not rotated:
            return False
    return True


def _present_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _resolver_family_code(
    material_family: str,
    *,
    policies: Mapping[str, Mapping[str, Any]],
) -> str | None:
    family_code = str(material_family or "").strip()
    return family_code if family_code in policies else None


def _company_candidates(
    *,
    requirement_name: str,
    material_family: str | None,
    specifications: Mapping[str, Any],
    company_material_items: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Find compatible Company items without consulting a retired resolver."""
    normalized_name = normalize_material_phrase(requirement_name)
    candidates: list[Mapping[str, Any]] = []
    for item in company_material_items:
        if str(item.get("status") or "private") == "archived":
            continue
        item_specs = dict(item.get("specifications") or {})
        same_name = bool(normalized_name) and normalize_material_phrase(
            item.get("normalized_name") or item.get("canonical_name")
        ) == normalized_name
        same_family = bool(material_family) and normalize_material_phrase(
            item_specs.get("material_family")
        ) == normalize_material_phrase(material_family)
        if not same_name and not same_family:
            continue
        compatible, _matched = _hard_compatibility(
            item, category_code=None, specifications=specifications,
        )
        if compatible:
            candidates.append(item)
    return tuple(candidates)


def _active_default_specifications(
    *,
    material_family: str,
    specifications: Mapping[str, Any],
    material_default_variants: Sequence[Mapping[str, Any]],
    reference_positions: Sequence[Mapping[str, Any]],
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
    positions = {
        str(row.get("reference_position_id") or ""): row
        for row in reference_positions
        if str(row.get("family_code") or "") == family_code
    }

    def has_evidenced_non_applicability_key(
        *, applicability: Mapping[str, Any], policy: Mapping[str, Any] | None,
    ) -> bool:
        """A default may complete a recognised Family, never alter a key fact.

        Applicability is the Family/subtype identity that selected a default,
        such as MDF plus its stated veneer face. Any other populated Pricing
        Key fact is an exact resolver input and must be matched as-is.
        """
        for attribute_code in (policy or {}).get("pricing_key_attribute_codes") or ():
            fields = {str(attribute_code), *pricing_key_fact_fields(str(attribute_code))}
            present_fields = {
                field for field in fields if _present_value(specifications.get(field))
            }
            if not present_fields:
                continue
            if not any(
                field in applicability and specifications.get(field) == applicability[field]
                for field in present_fields
            ):
                return True
        return False

    price_scope = "retail_package" if str(family_code or "").startswith("hardware_") else "material_only"
    for variant in sorted(
        material_default_variants,
        key=lambda row: (int(row.get("priority") or 0), str(row.get("default_variant_id") or "")),
    ):
        if str(variant.get("family_id") or "") != family_id:
            continue
        position_id = str(variant.get("reference_position_id") or "")
        position = positions.get(position_id)
        if position is None:
            continue
        has_active_price = any(
            str(price.get("status") or "") == "active"
            and str(price.get("price_scope") or "") == price_scope
            and _positive(price.get("price_typical")) is not None
            for price in position.get("prices") or ()
        )
        if not has_active_price:
            continue
        applicability = dict(variant.get("applicability_specifications") or {})
        if any(specifications.get(key) != value for key, value in applicability.items()):
            continue
        if has_evidenced_non_applicability_key(applicability=applicability, policy=policy):
            continue
        defaults = dict(variant.get("default_specifications") or {})
        applied = {key: value for key, value in defaults.items() if not _present_value(specifications.get(key))}
        if not applied and price_scope != "retail_package":
            continue
        effective = {**specifications, **applied}
        selection_key = material_pricing_selection_key(
            material_family=material_family,
            specifications=effective,
            pricing_policies=policies,
        )
        position_key = material_pricing_selection_key(
            material_family=family_code,
            specifications=dict(position.get("specifications") or {}),
            pricing_policies=policies,
        )
        if selection_key is None:
            continue
        purchase_specifications = effective
        if position_key != selection_key:
            # A default may legitimately connect a more detailed requirement
            # to its approved generic purchasable baseline.  Example:
            # melamine-one-sided MDF without a thickness uses the 17-mm
            # generic laminated MDF position.  The original surface stays in
            # the immutable Object Facts; only the purchase request is mapped
            # to the baseline position.
            if not applicability:
                continue
            purchase_specifications = dict(effective)
            position_specs = dict(position.get("specifications") or {})
            for attribute_code in (policy or {}).get("pricing_key_attribute_codes") or ():
                for field in pricing_key_fact_fields(str(attribute_code)):
                    if _present_value(position_specs.get(field)):
                        purchase_specifications[field] = position_specs[field]
                        break
            purchase_key = material_pricing_selection_key(
                material_family=material_family,
                specifications=purchase_specifications,
                pricing_policies=policies,
            )
            if purchase_key != position_key:
                continue
        trace = {
            "default_variant_id": str(variant.get("default_variant_id") or ""),
            "reference_position_id": position_id,
            "family_code": family_code,
            "applied_specifications": applied,
        }
        if purchase_specifications != effective:
            trace["source_specifications"] = dict(specifications)
            trace["purchase_specifications"] = purchase_specifications
        return purchase_specifications, trace
    return dict(specifications), None


def _apply_drawer_slide_last_resort_default(
    *,
    material_family: str,
    specifications: Mapping[str, Any],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    material_families: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    """Complete an otherwise unspecified drawer slide with the approved fallback.

    This is deterministic Material Engine policy, not an Estimation Agent fact
    and not a catalog default variant.  An explicit source depth always wins.
    """
    policies = pricing_policy_by_family_code(material_pricing_policies, families=material_families)
    if _resolver_family_code(material_family, policies=policies) != "hardware_drawer_slide":
        return dict(specifications), None
    if _present_value(specifications.get("depth_mm")):
        return dict(specifications), None
    effective = {**specifications, "depth_mm": _DRAWER_SLIDE_LAST_RESORT_DEPTH_MM}
    return effective, {
        "policy": "drawer_slide_last_resort_depth",
        "family_code": "hardware_drawer_slide",
        "applied_specifications": {"depth_mm": _DRAWER_SLIDE_LAST_RESORT_DEPTH_MM},
    }


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


def _interim_sheet_count_unit(candidates: Sequence[MaterialSupplyCandidate]) -> str | None:
    """Keep an extracted positive sheet-material count costable during V3 intake.

    This is intentionally a bounded interim fallback.  It applies only where
    every Resolver-cleared candidate is a sheet, records its use in the plan,
    and never invents a dimension, area, or linear quantity.
    """
    return "sheet" if candidates and all(candidate.purchase_kind == "sheet" for candidate in candidates) else None


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
            kind = _offer_kind(offer)
            # A discrete package is itself the required purchase format.  It
            # has no geometric dimensions to provide.
            status_dimensions = offer.get("purchasable_dimensions") or (
                {} if kind == "piece" else None
            )
            status = material_identity_status(
                item, pricing_policies=policies,
                purchasable_dimensions=status_dimensions,
            )
            package_is_complete = kind == "piece" and status.missing == ("purchase format",)
            if status.tone not in {"blue", "green"} and not package_is_complete:
                continue
            offer_id = str(offer.get("offer_id") or "").strip()
            if not offer_id:
                continue
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
                display_name=str(item.get("canonical_name") or item.get("normalized_name") or ""),
                offer_id=offer_id,
            ))
    return selection_key, tuple(sorted(result, key=lambda candidate: candidate.candidate_id))


def israel_reference_supply_candidates(
    *,
    material_family: str,
    specifications: Mapping[str, Any] | None,
    reference_positions: Sequence[Mapping[str, Any]],
    material_pricing_policies: Sequence[Mapping[str, Any]],
    material_families: Sequence[Mapping[str, Any]],
    currency: str = "ILS",
    price_scope: str = "material_only",
    reference_position_id: str | None = None,
    as_of: date | None = None,
) -> tuple[str | None, tuple[MaterialSupplyCandidate, ...]]:
    """Return candidates from one exact Israel Reference position.

    A position is a completed Family plus Pricing Key.  Its price and physical
    purchase formats belong together.  No historical price identity or generic
    Family format is eligible here.
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
    result: list[MaterialSupplyCandidate] = []
    for position in reference_positions:
        if reference_position_id and str(position.get("reference_position_id") or "") != reference_position_id:
            continue
        family_code = str(position.get("family_code") or "")
        if family_code not in policies:
            continue
        position_key = material_pricing_selection_key(
            material_family=family_code,
            specifications=dict(position.get("specifications") or {}),
            pricing_policies=policies,
        )
        if position_key != selection_key:
            continue
        position_id = str(position.get("reference_position_id") or "").strip()
        if not position_id:
            continue
        formats = [
            row for row in position.get("supply_formats") or () if row.get("active") is not False
        ]
        for price in position.get("prices") or ():
            if str(price.get("status") or "") != "active" or not _effective(price, effective_date):
                continue
            if str(price.get("currency") or "").upper() != normalized_currency:
                continue
            if str(price.get("price_scope") or "") != price_scope:
                continue
            price_id = str(price.get("model_price_id") or "").strip()
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
                        candidate_id=f"israel-reference:{position_id}:{price_id}:{format_id}",
                        material_family=material_family,
                        selection_key=selection_key,
                        purchase_kind="sheet",
                        price_per_purchase_unit=typical * length * width / Decimal("1000000"),
                        currency=normalized_currency,
                        purchasable_dimensions=dimensions,
                        authority="israel_reference",
                        display_name=str(position.get("canonical_name") or ""),
                        reference_price_id=price_id,
                    ))
            elif unit == "sheet":
                # A source price expressed per sheet is safe only when the
                # physical sheet format belongs to this exact Reference
                # listing.  It must never be combined with a Family default
                # or another listing's format.
                for supply_format in formats:
                    dimensions = dict(supply_format.get("purchasable_dimensions") or {})
                    length = _positive(dimensions.get("length_mm"))
                    width = _positive(dimensions.get("width_mm"))
                    format_id = str(supply_format.get("supply_format_id") or "").strip()
                    if not format_id or length is None or width is None:
                        continue
                    result.append(MaterialSupplyCandidate(
                        candidate_id=f"israel-reference:{position_id}:{price_id}:{format_id}",
                        material_family=material_family,
                        selection_key=selection_key,
                        purchase_kind="sheet",
                        price_per_purchase_unit=typical,
                        currency=normalized_currency,
                        purchasable_dimensions=dimensions,
                        authority="israel_reference",
                        display_name=str(position.get("canonical_name") or ""),
                        reference_price_id=price_id,
                    ))
            elif unit in _LINEAR_UNITS:
                for supply_format in formats:
                    dimensions = dict(supply_format.get("purchasable_dimensions") or {})
                    length = _positive(dimensions.get("length_mm"))
                    format_id = str(supply_format.get("supply_format_id") or "").strip()
                    if not format_id or length is None:
                        continue
                    is_edge_cut = family_code == "edge_banding"
                    result.append(MaterialSupplyCandidate(
                        candidate_id=f"israel-reference:{position_id}:{price_id}:{format_id}",
                        material_family=material_family,
                        selection_key=selection_key,
                        purchase_kind="linear_cut" if is_edge_cut else "linear_stock",
                        price_per_purchase_unit=typical if is_edge_cut else typical * length / Decimal("1000"),
                        currency=normalized_currency,
                        purchasable_dimensions=dimensions,
                        authority="israel_reference",
                        display_name=str(position.get("canonical_name") or ""),
                        reference_price_id=price_id,
                    ))
            elif unit == "kg":
                specifications = dict(position.get("specifications") or {})
                for supply_format in formats:
                    dimensions = dict(supply_format.get("purchasable_dimensions") or {})
                    length = _positive(dimensions.get("length_mm"))
                    width = _positive(dimensions.get("width_mm"))
                    format_id = str(supply_format.get("supply_format_id") or "").strip()
                    if not format_id or length is None:
                        continue
                    if width is not None:
                        kilograms = kilograms_per_sheet(
                            specifications=specifications, length_mm=length, width_mm=width,
                        )
                        kind = "sheet"
                    else:
                        kilograms_per_m = kilograms_per_metre(
                            family_code=family_code, specifications=specifications,
                        )
                        kilograms = None if kilograms_per_m is None else kilograms_per_m * length / Decimal("1000")
                        kind = "linear_stock"
                    if kilograms is None:
                        continue
                    result.append(MaterialSupplyCandidate(
                        candidate_id=f"israel-reference:{position_id}:{price_id}:{format_id}",
                        material_family=material_family, selection_key=selection_key,
                        purchase_kind=kind, price_per_purchase_unit=typical * kilograms,
                        currency=normalized_currency, purchasable_dimensions=dimensions,
                        authority="israel_reference", display_name=str(position.get("canonical_name") or ""),
                        reference_price_id=price_id,
                    ))
            elif unit == "m3":
                result.append(MaterialSupplyCandidate(
                    candidate_id=f"israel-reference:{position_id}:{price_id}",
                    material_family=material_family, selection_key=selection_key,
                    purchase_kind="volume_direct", price_per_purchase_unit=typical,
                    currency=normalized_currency, authority="israel_reference",
                    display_name=str(position.get("canonical_name") or ""),
                    reference_price_id=price_id,
                ))
            elif unit in _REFERENCE_DISCRETE_PACKAGE_QUANTITIES:
                result.append(MaterialSupplyCandidate(
                    candidate_id=f"israel-reference:{position_id}:{price_id}",
                    material_family=material_family,
                    selection_key=selection_key,
                    purchase_kind="piece",
                    price_per_purchase_unit=typical,
                    currency=normalized_currency,
                    package_quantity=_REFERENCE_DISCRETE_PACKAGE_QUANTITIES[unit],
                    authority="israel_reference",
                    display_name=str(position.get("canonical_name") or ""),
                    reference_price_id=price_id,
                ))
    return selection_key, tuple(sorted(result, key=lambda candidate: candidate.candidate_id))


def _operation_supply_candidates(operation_code, material_family, catalogs, vat_percent):
    """Resolve a per-piece service in Company Catalog and Israel Reference."""
    operation = next((row for row in catalogs.get("operations", ())
                      if row.get("operation_code") == operation_code and row.get("active") is True), None)
    if not operation:
        return ()
    today = date.today()
    selection_key = f"operation:{operation_code}:{material_family}" if material_family else f"operation:{operation_code}"
    display_name = str(operation.get("operation_name") or operation_code)
    candidates = []
    for offer in catalogs.get("supplier_operation_offers", ()):
        if (offer.get("operation_id") != operation.get("operation_id") or offer.get("status") != "active"
                or offer.get("pricing_basis") != "piece" or offer.get("currency") != "ILS"
                or type(offer.get("vat_included")) is not bool
                or not _effective(offer, today)):
            continue
        amount = _positive(offer.get("source_price"))
        offer_id = offer.get("operation_offer_id")
        if amount is None or not offer_id:
            continue
        candidates.append(MaterialSupplyCandidate(
            candidate_id=f"supplier-operation:{offer_id}", material_family=operation_code,
            selection_key=selection_key, purchase_kind="piece",
            price_per_purchase_unit=_ex_vat(amount, offer, vat_percent), authority="company", currency="ILS",
            display_name=display_name, offer_id=str(offer_id),
        ))
    for price in catalogs.get("israel_operation_prices", ()):
        if (price.get("operation_id") != operation.get("operation_id")
                or price.get("material_family_code") != material_family
                or price.get("status") != "active" or price.get("market_code") != "IL"
                or price.get("unit") != "piece" or price.get("currency") != "ILS"
                or not price.get("source_id") or not _effective(price, today)):
            continue
        amount = _positive(price.get("price_ex_vat"))
        price_id = price.get("operation_service_price_id")
        if amount is None or not price_id:
            continue
        candidates.append(MaterialSupplyCandidate(
            candidate_id=f"israel-operation:{price_id}", material_family=operation_code,
            selection_key=selection_key, purchase_kind="piece", price_per_purchase_unit=amount,
            authority="israel_reference", currency="ILS", display_name=display_name, reference_price_id=str(price_id),
        ))
    return tuple(candidates)


def build_material_plan(
    *,
    facts_by_object: Mapping[str, Mapping[str, Any]],
    catalogs: Mapping[str, Sequence[Mapping[str, Any]]],
    material_norm_overrides: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    material_purchase_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    vat_percent: Decimal | int | float | str = Decimal("18"),
    allow_estimator_allowance: bool = True,
) -> MaterialEngineResult:
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
    assumption_fallbacks: list[dict[str, Any]] = []
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
            def add_assumption_fallback(*, reason_code: str, selection_key: str | None = None) -> None:
                total_quantity = _positive(material.get("quantity"))
                object_quantity = _positive(facts.get("quantity")) or Decimal("1")
                assumption_fallbacks.append({
                    "object_id": str(object_id),
                    "material_requirement_id": requirement_id,
                    "source_name": str(material.get("source_name") or material.get("family") or "Material"),
                    "material_family": str(material.get("family") or ""),
                    "specification": {
                        **dict(material.get("specification") or {}),
                        **({"operation_code": material["operation_code"]} if material.get("operation_code") else {}),
                    },
                    "selection_key": selection_key,
                    "quantity_per_item": (
                        None if total_quantity is None else float(total_quantity / object_quantity)
                    ),
                    "object_quantity": float(object_quantity),
                    "unit": material.get("unit"),
                    "reason_code": reason_code,
                    "resolution": "assumption_fallback",
                    "parts": [dict(part) for part in parts],
                })

            parts = parts_by_requirement.get(requirement_id) or []
            if reason := material.get("assumption_reason"):
                add_assumption_fallback(reason_code=str(reason))
                reasons.add("assumption_fallback")
                continue
            if material.get("item_kind") == "operation_service":
                operation_code = str(material.get("operation_code") or "")
                worktop_family = str((material.get("specification") or {}).get("worktop_family") or "")
                compatible = _operation_supply_candidates(operation_code, worktop_family, catalogs, Decimal(str(vat_percent)))
                quantity = _positive(material.get("quantity"))
                if not compatible or quantity is None or _canonical_requirement_unit(material.get("unit")) != "ea":
                    add_assumption_fallback(reason_code="supplier_operation_quote_required")
                    reasons.add("assumption_fallback")
                    continue
                candidates.update((candidate.candidate_id, candidate) for candidate in compatible)
                demands.append(MaterialDemand(
                    demand_id=f"{object_id}:{requirement_id}:service", object_id=str(object_id),
                    material_requirement_id=requirement_id, material_family=operation_code,
                    selection_key=compatible[0].selection_key, quantity=quantity, unit="piece",
                    compatible_candidate_ids=tuple(candidate.candidate_id for candidate in compatible),
                ))
                continue
            specs = _complete_common_sheet_finish(material_family=str(material.get("family") or ""), source_name=material.get("source_name"), specifications=dict(material.get("specification") or {}))
            specs, drawer_slide_trace = _apply_drawer_slide_last_resort_default(
                material_family=str(material.get("family") or ""),
                specifications=specs,
                material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                material_families=catalogs.get("material_families") or (),
            )
            hint = normalize_material_phrase(material.get("identity_hint"))
            hint_tokens = set(hint.split())
            positions = catalogs.get("reference_positions") or ()
            if hint_tokens:
                positions = tuple(row for row in positions if hint_tokens <=
                                  set(normalize_material_phrase(row.get("canonical_name")).split()))
            specs, default_trace = _active_default_specifications(
                material_family=str(material.get("family") or ""),
                specifications=specs,
                material_default_variants=catalogs.get("material_default_variants") or (),
                reference_positions=positions,
                material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                material_families=catalogs.get("material_families") or (),
            )
            if default_trace is not None:
                applied_defaults.append({
                    "object_id": str(object_id),
                    "material_requirement_id": requirement_id,
                    **default_trace,
                })
            if drawer_slide_trace is not None:
                applied_defaults.append({
                    "object_id": str(object_id),
                    "material_requirement_id": requirement_id,
                    **drawer_slide_trace,
                })
            price_scope = (
                "retail_package"
                if str(_resolver_family_code(
                    str(material.get("family") or ""),
                    policies=pricing_policy_by_family_code(
                        catalogs.get("material_pricing_policies") or (),
                        families=catalogs.get("material_families") or (),
                    ),
                ) or "").startswith("hardware_")
                else "material_only"
            )
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
                    price_scope=price_scope,
                    vat_percent=vat_percent,
                ),
            )
            if selection_key is None:
                add_assumption_fallback(reason_code="material_pricing_key_incomplete")
                reasons.add("assumption_fallback")
                continue
            _reference_key, reference_candidates = israel_reference_supply_candidates(
                material_family=cache_key[1],
                specifications=specs,
                reference_positions=positions,
                material_pricing_policies=catalogs.get("material_pricing_policies") or (),
                material_families=catalogs.get("material_families") or (),
                price_scope=price_scope,
                reference_position_id=(
                    str(default_trace.get("reference_position_id") or "")
                    if default_trace is not None else None
                ),
            )
            if parts:
                def fitting_candidates(rows):
                    return tuple(row for row in rows if row.purchase_kind != "sheet"
                                 or _sheet_candidate_fits_finished_parts(row, parts))

                company_candidates = fitting_candidates(company_candidates)
                reference_candidates = fitting_candidates(reference_candidates)
            if facts.get("composition_version") == "cb_parts_material_demand_v1":
                if hint_tokens:
                    def named_candidates(rows):
                        exact = tuple(row for row in rows if normalize_material_phrase(row.display_name) == hint)
                        matches = exact or tuple(row for row in rows
                                                 if hint_tokens <= set(normalize_material_phrase(row.display_name).split()))
                        return matches if len({normalize_material_phrase(row.display_name) for row in matches}) <= 1 else ()

                    company_candidates = named_candidates(company_candidates)
                    reference_candidates = named_candidates(reference_candidates)
                compatible = (*company_candidates, *reference_candidates)
                if not parts and _canonical_requirement_unit(material.get("unit")) == "ea":
                    compatible = tuple(candidate for candidate in compatible if candidate.purchase_kind == "piece")
            else:
                compatible = company_candidates or reference_candidates
            if purchase_variant := material.get("purchase_variant"):
                selection_key = f"{selection_key}|variant={purchase_variant}"
                compatible = tuple(
                    replace(candidate, candidate_id=f"{candidate.candidate_id}:variant:{purchase_variant}",
                            selection_key=selection_key, display_name=f"{candidate.display_name}, {purchase_variant}")
                    for candidate in compatible
                )
            for candidate in compatible:
                candidates[candidate.candidate_id] = candidate
            candidate_ids = tuple(candidate.candidate_id for candidate in compatible)
            if not candidate_ids:
                add_assumption_fallback(
                    reason_code="no_company_or_israel_candidate", selection_key=selection_key,
                )
                reasons.add("assumption_fallback")
                continue
            override = overrides.get((str(object_id), requirement_id))
            object_quantity = _positive(facts.get("quantity")) or Decimal("1")
            material_quantity = _positive(material.get("quantity"))
            if override:
                override_unit = str(override.get("unit") or "")
                override_quantity = _positive(override.get("quantity_per_item"))
                sheet_area_override = bool(parts) and all(candidate.purchase_kind == "sheet" for candidate in compatible) and _canonical_requirement_unit(override_unit) in {"m2", "sqm", "square_meter", "square_metre"}
                if override_quantity is None or (not sheet_area_override and _canonical_requirement_unit(override_unit) != _canonical_requirement_unit(material.get("unit"))):
                    add_assumption_fallback(
                        reason_code="manual_material_norm_invalid", selection_key=selection_key,
                    )
                    reasons.add("assumption_fallback")
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
                    add_assumption_fallback(
                        reason_code="manual_material_norm_unit_unsupported", selection_key=selection_key,
                    )
                    reasons.add("assumption_fallback")
                    continue
                demands.append(direct_demand)
                reasons.add("manual_material_norm_without_geometry")
                continue
            demand_count_before_parts = len(demands)
            part_geometry_invalid = False
            for part in parts:
                demand_id = f"{object_id}:{part.get('part_id')}"
                try:
                    thickness = _positive(specs.get("thickness_mm") or specs.get("thickness"))
                    part_quantity = _positive(part.get("quantity"))
                    part_length = _positive(part.get("length_mm"))
                    part_width = _positive(part.get("width_mm"))
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
                        volume_mm3=(part_quantity * part_length * part_width * thickness
                                    if thickness is not None and part_quantity is not None
                                    and part_length is not None and part_width is not None else None),
                        rotation_allowed=bool(part.get("rotation_allowed")),
                    ))
                except MaterialEngineError:
                    part_geometry_invalid = True
            if part_geometry_invalid:
                del demands[demand_count_before_parts:]
                add_assumption_fallback(
                    reason_code="material_part_geometry_invalid", selection_key=selection_key,
                )
                reasons.add("assumption_fallback")
            if parts:
                continue
            # Explicit historical/manual units remain supported. Newly
            # extracted V3 facts leave this null and obtain a unit only from a
            # discrete resolved candidate.
            direct_unit = str(material.get("unit") or "").strip() or _direct_count_unit(compatible)
            if material_quantity is None and direct_unit is not None:
                # Source authority and consumption basis are independent. A
                # resolver-cleared discrete C/I item stays C/I when a rough
                # sketch omitted its count; the conservative one-per-finished
                # item quantity is an explicit construction assumption, not a
                # fake loss of catalog coverage.
                material_quantity = object_quantity
                applied_defaults.append({
                    "object_id": str(object_id),
                    "material_requirement_id": requirement_id,
                    "default_type": "assumed_one_discrete_item_per_finished_object",
                    "quantity_per_item": 1.0,
                    "unit": direct_unit,
                })
                reasons.add("assumed_discrete_quantity")
            if material_quantity is None:
                add_assumption_fallback(
                    reason_code="material_quantity_missing", selection_key=selection_key,
                )
                reasons.add("assumption_fallback")
                continue
            if direct_unit is None:
                direct_unit = _interim_sheet_count_unit(compatible)
                if direct_unit is not None:
                    reasons.add("interim_sheet_count_without_geometry")
            if direct_unit is None:
                add_assumption_fallback(
                    reason_code="material_geometry_required", selection_key=selection_key,
                )
                reasons.add("assumption_fallback")
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
                add_assumption_fallback(
                    reason_code="material_unit_unsupported_for_purchase_plan", selection_key=selection_key,
                )
                reasons.add("assumption_fallback")
                continue
            demands.append(direct_demand)
    for fallback in assumption_fallbacks:
        object_id = str(fallback["object_id"])
        requirement_id = str(fallback["material_requirement_id"])
        parts = tuple(item for item in fallback.pop("parts", []) if isinstance(item, Mapping))
        if not allow_estimator_allowance:
            fallback["resolution"] = "assumption_required"
            unresolved.append(f"{object_id}:{requirement_id}")
            continue
        material = {
            "source_name": fallback["source_name"], "family": fallback["material_family"],
            "specification": fallback["specification"], "unit": fallback.get("unit"),
        }
        candidate, priced_fallback = _assumption_candidate(
            object_id=object_id, requirement_id=requirement_id, material=material,
            selection_key=fallback.get("selection_key"), parts=parts,
            reason_code=str(fallback["reason_code"]),
        )
        candidates[candidate.candidate_id] = candidate
        fallback.update({
            "selection_key": candidate.selection_key, "unit": priced_fallback["unit"],
            "assumption_price": priced_fallback["assumption_price"],
        })
        if candidate.purchase_kind == "sheet" and parts:
            appended = 0
            for part in parts:
                try:
                    demands.append(MaterialDemand(
                        demand_id=f"{object_id}:{part.get('part_id')}:assumption",
                        object_id=object_id, material_family=candidate.material_family,
                        selection_key=candidate.selection_key, quantity=part.get("quantity"), unit="piece",
                        compatible_candidate_ids=(candidate.candidate_id,),
                        part_id=str(part.get("part_id") or "") or None,
                        material_requirement_id=requirement_id,
                        length_mm=part.get("length_mm"), width_mm=part.get("width_mm"),
                        rotation_allowed=bool(part.get("rotation_allowed")),
                    ))
                    appended += 1
                except MaterialEngineError:
                    continue
            if appended:
                continue
        quantity_per_item = _positive(fallback.get("quantity_per_item")) or Decimal("1")
        object_quantity = _positive(fallback.get("object_quantity")) or Decimal("1")
        total_quantity = quantity_per_item * object_quantity
        demand_kwargs: dict[str, Any] = {}
        if candidate.purchase_kind == "linear_cut":
            demand_kwargs["linear_length_mm"] = total_quantity * Decimal("1000")
            total_quantity = Decimal("1")
        demands.append(MaterialDemand(
            demand_id=f"{object_id}:{requirement_id}:assumption",
            object_id=object_id, material_family=candidate.material_family,
            selection_key=candidate.selection_key,
            quantity=total_quantity, unit="piece",
            compatible_candidate_ids=(candidate.candidate_id,),
            material_requirement_id=requirement_id,
            **demand_kwargs,
        ))
        reasons.add("assumption_fallback")
    plan = plan_material_purchases(demands=demands, candidates=tuple(candidates.values())) if demands else None
    plan = _apply_purchase_quantity_overrides(plan, material_purchase_overrides or {})
    if plan and plan.status == "needs_review":
        unresolved.extend(plan.unresolved_demand_ids)
        reasons.update(plan.reason_codes)
    return MaterialEngineResult(
        plan=plan,
        demand_count=len(demands),
        candidate_count=len(candidates),
        unresolved_requirement_ids=tuple(sorted(set(unresolved))),
        reason_codes=tuple(sorted(reasons)),
        candidate_authorities=tuple(sorted(
            (candidate_id, candidate.authority)
            for candidate_id, candidate in candidates.items()
        )),
        candidate_display_names=tuple(sorted(
            (candidate_id, candidate.display_name)
            for candidate_id, candidate in candidates.items()
            if candidate.display_name
        )),
        candidate_purchase_forms=tuple(sorted(
            (
                candidate_id,
                {
                    "purchasable_dimensions": _physical_purchase_dimensions(
                        candidate.purchasable_dimensions
                    ),
                    "package_quantity": float(candidate.package_quantity),
                },
            )
            for candidate_id, candidate in candidates.items()
        )),
        applied_defaults=tuple(sorted(
            applied_defaults,
            key=lambda row: (str(row["object_id"]), str(row["material_requirement_id"])),
        )),
        assumption_fallbacks=tuple(sorted(
            assumption_fallbacks,
            key=lambda row: (str(row["object_id"]), str(row["material_requirement_id"])),
        )),
    )
