"""Pure Estimation v2 object-facts contract and cost composition.

This module does not call an LLM, database, Labor Engine, or UI code. The
extraction layer may return evidence-backed object facts only. Deterministic
engines provide cost lines, and this module decides whether self cost is safe
to publish.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite
import re
from typing import Any, AbstractSet, Mapping, Sequence


OBJECT_FACTS_CONTRACT_VERSION = "estimation_object_facts_v2"
OBJECT_ESTIMATE_CONTRACT_VERSION = "estimation_object_composition_v1"

OBJECT_FACT_STATUS_VALUES = frozenset({"ready", "review_required", "failed"})
OBJECT_ESTIMATE_STATUS_VALUES = frozenset({"complete", "review_required", "failed"})
COST_LINE_STATUS_VALUES = frozenset({"resolved", "estimated", "review_required", "failed"})
COST_SECTION_VALUES = frozenset({"material", "labor", "machinery", "purchased_component", "overhead"})
REVIEW_SEVERITY_VALUES = frozenset({"blocking", "warning"})
PROVENANCE_VALUES = frozenset({"explicit", "derived", "estimated"})

LABOR_OPERATION_VALUES = frozenset({
    "estimate_review", "shop_drawing", "cnc_programming", "sheet_nesting",
    "supplier_quotation", "quality_inspection", "panel_material_handling",
    "panel_saw_cutting", "cnc_router_profile_cutting", "cnc_vertical_drilling",
    "cnc_horizontal_drilling", "cnc_grooving", "cnc_pocketing",
    "manual_panel_cutting", "manual_drilling", "manual_routing", "edge_banding",
    "veneer_lamination", "solid_wood_ripping", "solid_wood_crosscutting",
    "solid_wood_jointing_planing", "solid_wood_profiling", "solid_wood_glueup",
    "wood_sanding", "carcass_assembly", "drawer_assembly", "door_front_fitting",
    "hardware_installation", "workshop_dry_fit", "sheet_laser_cutting",
    "sheet_shearing", "metal_profile_cutting", "metal_drilling", "metal_milling",
    "metal_punching", "sheet_metal_bending", "metal_profile_bending",
    "metal_rolling", "mig_mag_welding", "tig_welding", "metal_grinding",
    "metal_polishing", "metal_assembly", "finish_surface_preparation",
    "wood_staining", "wood_priming", "wood_lacquering", "wet_spray_painting",
    "powder_coating_preparation", "powder_coating_application", "sandblasting",
    "galvanizing", "protective_packaging",
})

ESTIMATION_REASON_CODE_VALUES = frozenset({
    "evidence_anchor_missing", "evidence_conflict", "invalid_evidence_reference",
    "quantity_missing", "quantity_invalid", "dimensions_missing", "dimensions_conflict",
    "material_requirement_missing", "material_quantity_missing",
    "material_identity_unresolved", "material_identity_ambiguous", "material_price_unresolved",
    "manufacturing_feature_unsupported", "machinery_route_unresolved",
    "machinery_cost_unresolved", "purchased_component_price_unresolved",
    "labor_result_unavailable", "labor_review_required",
    "overhead_result_unavailable", "overhead_review_required",
    "cost_currency_mismatch", "extraction_failed", "deterministic_engine_failed",
})

_FACT_FIELDS = frozenset({
    "contract_version", "input_id", "object_input_revision", "run_id", "company_id",
    "object_id", "object_name", "quantity", "status", "dimensions_mm",
    "materials", "features", "manufacturing_features", "purchased_components",
    "labor_operations", "source_facts", "review_items", "primary_preview_ref",
})
_MATERIAL_FIELDS = frozenset({
    "requirement_id", "source_name", "family", "specification", "quantity", "unit",
    "evidence_refs",
})
_SOURCE_FACT_FIELDS = frozenset({"path", "value", "provenance", "evidence_refs"})
_REVIEW_ITEM_FIELDS = frozenset({"code", "severity", "path", "message", "evidence_refs"})
_MANUFACTURING_FEATURE_FIELDS = frozenset({
    "feature_id", "process", "material_requirement_id", "measurements", "flags", "evidence_refs",
})
_MANUFACTURING_MEASUREMENT_FIELDS = frozenset({
    "thickness_mm", "part_count", "sheet_count", "path_length_m", "pass_count",
    "hole_count", "pocket_count", "edge_banding_length_m",
})
_MANUFACTURING_FLAG_FIELDS = frozenset({
    "production_file_ready", "rectangular_parts_only", "single_face_processing",
    "standard_operations_only", "has_freeform_contours", "has_internal_cutouts",
    "has_pockets", "has_horizontal_or_end_drilling", "has_repeated_hole_patterns",
    "has_tight_positional_relationships", "straight_edge_to_edge_cuts_only",
    "rough_finish_acceptable", "material_and_thickness_supported",
})
_PURCHASED_COMPONENT_FIELDS = frozenset({
    "component_id", "component_type", "quantity", "unit", "specification", "evidence_refs",
})
_LABOR_OPERATION_FIELDS = frozenset({
    "operation_id", "operation_code", "route", "quantity", "unit", "batch_key",
    "machine_code", "material_requirement_ids", "basis", "provenance",
    "evidence_refs", "confidence",
})
_PURCHASED_SPECIFICATION_FIELDS = frozenset({
    "width_mm", "depth_mm", "height_mm", "thickness_mm", "material", "finish",
    "cutout_count", "installation_scope",
})
_COST_LINE_FIELDS = frozenset({
    "line_id", "section", "status", "amount", "currency", "source_ref", "reason_codes",
})
_ALLOWED_SPECIFICATION_FIELDS = frozenset({
    "thickness_mm", "width_mm", "height_mm", "length_mm", "diameter_mm",
    "wall_thickness_mm",
    "profile_section", "species", "grade", "alloy", "temper", "finish", "surface",
    "color", "coating", "density_class", "fire_rating", "moisture_resistance",
    "supplier_sku",
})
_ALLOWED_FEATURE_FIELDS = frozenset({
    "shelf_count", "door_count", "drawer_count", "toe_kick", "back_panel",
    "plumbing_cutout", "finish", "visible_finish",
    "profile_section_mm", "coating", "open_face", "bend_count", "anchor_count",
})
_FORBIDDEN_EXTRACTION_KEYS = frozenset({
    "price", "unit_price", "unit_cost", "cost", "hours", "minutes", "rate",
    "labor_rate", "machine_cost", "overhead", "margin", "sale_price", "vat", "total",
})
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_MONEY = Decimal("0.01")


class EstimationV2ContractError(ValueError):
    pass


def _exact_keys(value: Mapping[str, Any], allowed: AbstractSet[str], name: str) -> None:
    missing = set(allowed) - set(value)
    extra = set(value) - set(allowed)
    if missing:
        raise EstimationV2ContractError(f"{name} missing keys: {sorted(missing)}")
    if extra:
        raise EstimationV2ContractError(f"{name} has extra keys: {sorted(extra)}")


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EstimationV2ContractError(f"{name} must be an object")
    return value


def _sequence(value: Any, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise EstimationV2ContractError(f"{name} must be an array")
    return value


def _identifier(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not _ID_PATTERN.fullmatch(text):
        raise EstimationV2ContractError(f"{name} must be a stable identifier")
    return text


def _text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise EstimationV2ContractError(f"{name} must be non-empty")
    return text


def _positive_number(value: Any, name: str, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool):
        raise EstimationV2ContractError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise EstimationV2ContractError(f"{name} must be numeric") from exc
    if not isfinite(result) or result <= 0:
        raise EstimationV2ContractError(f"{name} must be greater than zero")
    return result


def _nonnegative_number(value: Any, name: str, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool):
        raise EstimationV2ContractError(f"{name} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise EstimationV2ContractError(f"{name} must be numeric") from exc
    if not isfinite(result) or result < 0:
        raise EstimationV2ContractError(f"{name} must be zero or greater")
    return result


def _evidence_refs(value: Any, name: str) -> tuple[str, ...]:
    refs = tuple(_text(item, f"{name}[]") for item in _sequence(value, name))
    if len(refs) != len(set(refs)):
        raise EstimationV2ContractError(f"{name} must not contain duplicates")
    return refs


def _reject_forbidden_keys(value: Any, path: str = "facts") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_EXTRACTION_KEYS:
                raise EstimationV2ContractError(f"{path}.{key} is owned by a deterministic engine")
            _reject_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")


def validate_object_facts(
    payload: Mapping[str, Any],
    *,
    allowed_material_families: AbstractSet[str],
) -> dict[str, Any]:
    """Validate bounded extraction output without deriving or pricing anything."""
    facts = dict(_mapping(payload, "facts"))
    _exact_keys(facts, _FACT_FIELDS, "facts")
    _reject_forbidden_keys(facts)
    if facts["contract_version"] != OBJECT_FACTS_CONTRACT_VERSION:
        raise EstimationV2ContractError("facts.contract_version is unsupported")
    for field in ("input_id", "run_id", "company_id", "object_id"):
        _identifier(facts[field], f"facts.{field}")
    _text(facts["object_name"], "facts.object_name")
    revision = facts["object_input_revision"]
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise EstimationV2ContractError("facts.object_input_revision must be a positive integer")
    quantity = _positive_number(facts["quantity"], "facts.quantity", allow_none=True)
    status = str(facts["status"])
    if status not in OBJECT_FACT_STATUS_VALUES:
        raise EstimationV2ContractError("facts.status is unsupported")

    dimensions = _mapping(facts["dimensions_mm"], "facts.dimensions_mm")
    _exact_keys(dimensions, frozenset({"width", "depth", "height"}), "facts.dimensions_mm")
    dimension_values = {
        key: _positive_number(value, f"facts.dimensions_mm.{key}", allow_none=True)
        for key, value in dimensions.items()
    }

    materials = _sequence(facts["materials"], "facts.materials")
    material_requirement_ids: set[str] = set()
    material_evidence_complete = True
    material_quantities_complete = True
    for index, value in enumerate(materials):
        material = _mapping(value, f"facts.materials[{index}]")
        _exact_keys(material, _MATERIAL_FIELDS, f"facts.materials[{index}]")
        requirement_id = _identifier(material["requirement_id"], f"facts.materials[{index}].requirement_id")
        if requirement_id in material_requirement_ids:
            raise EstimationV2ContractError("material requirement ids must be unique")
        material_requirement_ids.add(requirement_id)
        _text(material["source_name"], f"facts.materials[{index}].source_name")
        family = _text(material["family"], f"facts.materials[{index}].family")
        if family not in allowed_material_families:
            raise EstimationV2ContractError(f"facts.materials[{index}].family is not in the versioned catalog")
        specification = _mapping(material["specification"], f"facts.materials[{index}].specification")
        extra_spec = set(specification) - set(_ALLOWED_SPECIFICATION_FIELDS)
        if extra_spec:
            raise EstimationV2ContractError(f"facts.materials[{index}].specification has unsupported keys: {sorted(extra_spec)}")
        material_quantity = _positive_number(material["quantity"], f"facts.materials[{index}].quantity", allow_none=True)
        material_quantities_complete = material_quantities_complete and material_quantity is not None
        _text(material["unit"], f"facts.materials[{index}].unit")
        material_refs = _evidence_refs(material["evidence_refs"], f"facts.materials[{index}].evidence_refs")
        material_evidence_complete = material_evidence_complete and bool(material_refs)

    features = _mapping(facts["features"], "facts.features")
    extra_features = set(features) - set(_ALLOWED_FEATURE_FIELDS)
    if extra_features:
        raise EstimationV2ContractError(f"facts.features has unsupported keys: {sorted(extra_features)}")
    for key, value in features.items():
        name = f"facts.features.{key}"
        if key in {"shelf_count", "door_count", "drawer_count", "bend_count", "anchor_count"}:
            parsed = _nonnegative_number(value, name)
            if parsed is None or not parsed.is_integer():
                raise EstimationV2ContractError(f"{name} must be a nonnegative integer")
        elif key in {"profile_section_mm"}:
            _positive_number(value, name)
        elif key in {"toe_kick", "back_panel", "plumbing_cutout", "open_face"}:
            if not isinstance(value, bool):
                raise EstimationV2ContractError(f"{name} must be boolean")
        else:
            _text(value, name)

    manufacturing_ids: set[str] = set()
    for index, value in enumerate(_sequence(facts["manufacturing_features"], "facts.manufacturing_features")):
        feature = _mapping(value, f"facts.manufacturing_features[{index}]")
        _exact_keys(feature, _MANUFACTURING_FEATURE_FIELDS, f"facts.manufacturing_features[{index}]")
        feature_id = _identifier(feature["feature_id"], f"facts.manufacturing_features[{index}].feature_id")
        if feature_id in manufacturing_ids:
            raise EstimationV2ContractError("manufacturing feature ids must be unique")
        manufacturing_ids.add(feature_id)
        if feature["process"] not in {"cnc_router", "sheet_laser"}:
            raise EstimationV2ContractError(f"facts.manufacturing_features[{index}].process is unsupported")
        material_requirement_id = _identifier(
            feature["material_requirement_id"],
            f"facts.manufacturing_features[{index}].material_requirement_id",
        )
        if material_requirement_id not in material_requirement_ids:
            raise EstimationV2ContractError(f"facts.manufacturing_features[{index}] references an unknown material")
        measurements = _mapping(feature["measurements"], f"facts.manufacturing_features[{index}].measurements")
        _exact_keys(measurements, _MANUFACTURING_MEASUREMENT_FIELDS, f"facts.manufacturing_features[{index}].measurements")
        for key, measurement in measurements.items():
            _nonnegative_number(measurement, f"facts.manufacturing_features[{index}].measurements.{key}", allow_none=True)
        flags = _mapping(feature["flags"], f"facts.manufacturing_features[{index}].flags")
        _exact_keys(flags, _MANUFACTURING_FLAG_FIELDS, f"facts.manufacturing_features[{index}].flags")
        for key, flag in flags.items():
            if flag not in {"yes", "no", "unknown"}:
                raise EstimationV2ContractError(f"facts.manufacturing_features[{index}].flags.{key} is unsupported")
        _evidence_refs(feature["evidence_refs"], f"facts.manufacturing_features[{index}].evidence_refs")

    component_ids: set[str] = set()
    purchased_quantities_complete = True
    for index, value in enumerate(_sequence(facts["purchased_components"], "facts.purchased_components")):
        component = _mapping(value, f"facts.purchased_components[{index}]")
        _exact_keys(component, _PURCHASED_COMPONENT_FIELDS, f"facts.purchased_components[{index}]")
        component_id = _identifier(component["component_id"], f"facts.purchased_components[{index}].component_id")
        if component_id in component_ids:
            raise EstimationV2ContractError("purchased component ids must be unique")
        component_ids.add(component_id)
        _identifier(component["component_type"], f"facts.purchased_components[{index}].component_type")
        component_quantity = _positive_number(
            component["quantity"],
            f"facts.purchased_components[{index}].quantity",
            allow_none=True,
        )
        purchased_quantities_complete = (
            purchased_quantities_complete and component_quantity is not None
        )
        _text(component["unit"], f"facts.purchased_components[{index}].unit")
        specification = _mapping(component["specification"], f"facts.purchased_components[{index}].specification")
        extra_component_spec = set(specification) - set(_PURCHASED_SPECIFICATION_FIELDS)
        if extra_component_spec:
            raise EstimationV2ContractError(
                f"facts.purchased_components[{index}].specification has unsupported keys: {sorted(extra_component_spec)}"
            )
        _evidence_refs(component["evidence_refs"], f"facts.purchased_components[{index}].evidence_refs")

    operation_ids: set[str] = set()
    labor_operations = _sequence(facts["labor_operations"], "facts.labor_operations")
    labor_evidence_complete = True
    for index, value in enumerate(labor_operations):
        operation = _mapping(value, f"facts.labor_operations[{index}]")
        _exact_keys(operation, _LABOR_OPERATION_FIELDS, f"facts.labor_operations[{index}]")
        operation_id = _identifier(
            operation["operation_id"], f"facts.labor_operations[{index}].operation_id"
        )
        if operation_id in operation_ids:
            raise EstimationV2ContractError("labor operation ids must be unique")
        operation_ids.add(operation_id)
        if operation["operation_code"] not in LABOR_OPERATION_VALUES:
            raise EstimationV2ContractError(
                f"facts.labor_operations[{index}].operation_code is unsupported"
            )
        if operation["route"] not in {"in_house_manual", "in_house_machine"}:
            raise EstimationV2ContractError(
                f"facts.labor_operations[{index}].route is unsupported"
            )
        _positive_number(operation["quantity"], f"facts.labor_operations[{index}].quantity")
        _text(operation["unit"], f"facts.labor_operations[{index}].unit")
        _text(operation["batch_key"], f"facts.labor_operations[{index}].batch_key")
        machine_code = operation["machine_code"]
        if operation["route"] == "in_house_machine":
            _identifier(machine_code, f"facts.labor_operations[{index}].machine_code")
        elif machine_code is not None:
            raise EstimationV2ContractError(
                f"facts.labor_operations[{index}].machine_code must be null for manual work"
            )
        requirement_ids = _sequence(
            operation["material_requirement_ids"],
            f"facts.labor_operations[{index}].material_requirement_ids",
        )
        for requirement_id in requirement_ids:
            resolved_id = _identifier(
                requirement_id,
                f"facts.labor_operations[{index}].material_requirement_ids[]",
            )
            if resolved_id not in material_requirement_ids:
                raise EstimationV2ContractError(
                    f"facts.labor_operations[{index}] references an unknown material"
                )
        _text(operation["basis"], f"facts.labor_operations[{index}].basis")
        if operation["provenance"] not in PROVENANCE_VALUES:
            raise EstimationV2ContractError(
                f"facts.labor_operations[{index}].provenance is unsupported"
            )
        confidence = operation["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 100:
            raise EstimationV2ContractError(
                f"facts.labor_operations[{index}].confidence must be between 0 and 100"
            )
        operation_refs = _evidence_refs(
            operation["evidence_refs"], f"facts.labor_operations[{index}].evidence_refs"
        )
        labor_evidence_complete = labor_evidence_complete and bool(operation_refs)

    for index, value in enumerate(_sequence(facts["source_facts"], "facts.source_facts")):
        source = _mapping(value, f"facts.source_facts[{index}]")
        _exact_keys(source, _SOURCE_FACT_FIELDS, f"facts.source_facts[{index}]")
        _text(source["path"], f"facts.source_facts[{index}].path")
        if str(source["provenance"]) not in PROVENANCE_VALUES:
            raise EstimationV2ContractError(f"facts.source_facts[{index}].provenance is unsupported")
        if isinstance(source["value"], (Mapping, Sequence)) and not isinstance(source["value"], (str, bytes)):
            raise EstimationV2ContractError(f"facts.source_facts[{index}].value must be scalar")
        _evidence_refs(source["evidence_refs"], f"facts.source_facts[{index}].evidence_refs")

    blocking = 0
    for index, value in enumerate(_sequence(facts["review_items"], "facts.review_items")):
        item = _mapping(value, f"facts.review_items[{index}]")
        _exact_keys(item, _REVIEW_ITEM_FIELDS, f"facts.review_items[{index}]")
        if str(item["code"]) not in ESTIMATION_REASON_CODE_VALUES:
            raise EstimationV2ContractError(f"facts.review_items[{index}].code is unsupported")
        if str(item["severity"]) not in REVIEW_SEVERITY_VALUES:
            raise EstimationV2ContractError(f"facts.review_items[{index}].severity is unsupported")
        blocking += int(item["severity"] == "blocking")
        _text(item["path"], f"facts.review_items[{index}].path")
        _text(item["message"], f"facts.review_items[{index}].message")
        _evidence_refs(item["evidence_refs"], f"facts.review_items[{index}].evidence_refs")

    preview = _text(facts["primary_preview_ref"], "facts.primary_preview_ref")
    if not preview.startswith("storage://rfq-estimation-evidence/"):
        raise EstimationV2ContractError("facts.primary_preview_ref must reference private estimation evidence")
    missing_ready_facts = (
        quantity is None
        or not materials
        or not material_quantities_complete
        or not material_evidence_complete
        or not purchased_quantities_complete
        or not labor_operations
        or not labor_evidence_complete
    )
    if status == "ready" and (blocking or missing_ready_facts):
        raise EstimationV2ContractError("ready facts cannot contain blocking review items or required-fact gaps")
    if status == "review_required" and not blocking:
        raise EstimationV2ContractError("review_required facts need at least one blocking review item")
    if status == "failed" and not any(item.get("code") == "extraction_failed" for item in facts["review_items"]):
        raise EstimationV2ContractError("failed facts require extraction_failed")
    return facts


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise EstimationV2ContractError(f"{name} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise EstimationV2ContractError(f"{name} must be numeric") from exc
    if not result.is_finite() or result < 0:
        raise EstimationV2ContractError(f"{name} must be zero or greater")
    return result


def _money(value: Decimal) -> float:
    return float(value.quantize(_MONEY, rounding=ROUND_HALF_UP))


def compose_object_estimate(
    *,
    facts: Mapping[str, Any],
    cost_lines: Sequence[Mapping[str, Any]],
    allowed_material_families: AbstractSet[str],
    default_markup_percent: Decimal = Decimal("30"),
) -> dict[str, Any]:
    """Compose self cost only from deterministic, auditable engine results."""
    validated = validate_object_facts(facts, allowed_material_families=allowed_material_families)
    normalized_lines: list[dict[str, Any]] = []
    line_ids: set[str] = set()
    reasons = {str(item["code"]) for item in validated["review_items"] if item["severity"] == "blocking"}
    fallback_reasons: set[str] = set()
    currencies: set[str] = set()
    failed_line = False
    for index, value in enumerate(cost_lines):
        line = dict(_mapping(value, f"cost_lines[{index}]"))
        _exact_keys(line, _COST_LINE_FIELDS, f"cost_lines[{index}]")
        line_id = _identifier(line["line_id"], f"cost_lines[{index}].line_id")
        if line_id in line_ids:
            raise EstimationV2ContractError("cost line ids must be unique")
        line_ids.add(line_id)
        section = str(line["section"])
        status = str(line["status"])
        if section not in COST_SECTION_VALUES or status not in COST_LINE_STATUS_VALUES:
            raise EstimationV2ContractError(f"cost_lines[{index}] has unsupported section or status")
        currency = str(line["currency"] or "").upper()
        if len(currency) != 3:
            raise EstimationV2ContractError(f"cost_lines[{index}].currency must be a three-letter code")
        currencies.add(currency)
        line_reasons = tuple(str(code) for code in _sequence(line["reason_codes"], f"cost_lines[{index}].reason_codes"))
        unknown_reasons = set(line_reasons) - set(ESTIMATION_REASON_CODE_VALUES)
        if unknown_reasons:
            raise EstimationV2ContractError(f"cost_lines[{index}] has unsupported reason codes: {sorted(unknown_reasons)}")
        if status in {"resolved", "estimated"}:
            amount = _decimal(line["amount"], f"cost_lines[{index}].amount")
            if status == "resolved" and line_reasons:
                raise EstimationV2ContractError("resolved cost lines cannot carry blocking reason codes")
            if status == "estimated" and not line_reasons:
                raise EstimationV2ContractError("estimated cost lines require a fallback reason code")
            fallback_reasons.update(line_reasons)
        else:
            if line["amount"] is not None:
                raise EstimationV2ContractError("unresolved cost lines cannot carry an amount")
            if not line_reasons:
                raise EstimationV2ContractError("unresolved cost lines require a reason code")
            amount = None
            reasons.update(line_reasons)
            failed_line = failed_line or status == "failed"
        _text(line["source_ref"], f"cost_lines[{index}].source_ref")
        normalized_lines.append({**line, "currency": currency, "amount": None if amount is None else _money(amount)})

    required_sections = {"labor", "overhead"}
    if validated["materials"]:
        required_sections.add("material")
    if validated["manufacturing_features"]:
        required_sections.add("machinery")
    if validated["purchased_components"]:
        required_sections.add("purchased_component")
    present_resolved = {
        line["section"] for line in normalized_lines
        if line["status"] in {"resolved", "estimated"}
    }
    missing_sections = required_sections - present_resolved
    missing_reasons = {
        "material": "material_price_unresolved",
        "labor": "labor_result_unavailable",
        "machinery": "machinery_cost_unresolved",
        "purchased_component": "purchased_component_price_unresolved",
        "overhead": "overhead_result_unavailable",
    }
    reasons.update(missing_reasons[section] for section in missing_sections)
    if len(currencies) > 1:
        reasons.add("cost_currency_mismatch")

    resolved_total = sum(
        (_decimal(line["amount"], f"resolved.{line['line_id']}") for line in normalized_lines
         if line["status"] in {"resolved", "estimated"}),
        Decimal("0"),
    )
    section_totals = {
        section: _money(sum(
            (_decimal(line["amount"], f"section.{section}") for line in normalized_lines
             if line["status"] in {"resolved", "estimated"} and line["section"] == section),
            Decimal("0"),
        ))
        for section in sorted(COST_SECTION_VALUES)
    }
    complete = validated["status"] == "ready" and not reasons and not failed_line
    failed = validated["status"] == "failed" or failed_line
    status = "failed" if failed else "complete" if complete else "review_required"
    quantity = (
        None
        if validated["quantity"] is None
        else _decimal(validated["quantity"], "facts.quantity")
    )
    self_cost_total = resolved_total if complete else None
    self_cost_unit = (
        self_cost_total / quantity
        if self_cost_total is not None and quantity is not None
        else None
    )
    markup_percent = _decimal(default_markup_percent, "default_markup_percent")
    markup = markup_percent / Decimal("100")
    selling_unit = self_cost_unit * (Decimal("1") + markup) if self_cost_unit is not None else None
    currency = next(iter(currencies)) if len(currencies) == 1 else None
    return {
        "contract_version": OBJECT_ESTIMATE_CONTRACT_VERSION,
        "input_id": validated["input_id"],
        "object_input_revision": validated["object_input_revision"],
        "run_id": validated["run_id"],
        "company_id": validated["company_id"],
        "object_id": validated["object_id"],
        "object_name": validated["object_name"],
        "quantity": validated["quantity"],
        "status": status,
        "reason_codes": sorted(reasons),
        "fallback_reason_codes": sorted(fallback_reasons),
        "currency": currency,
        "cost_lines": sorted(normalized_lines, key=lambda item: (item["section"], item["line_id"])),
        "section_totals": section_totals,
        "resolved_cost_subtotal": _money(resolved_total),
        "self_cost_unit": None if self_cost_unit is None else _money(self_cost_unit),
        "self_cost_total": None if self_cost_total is None else _money(self_cost_total),
        "selling_price_unit_suggestion": None if selling_unit is None else _money(selling_unit),
        "selling_price_markup_percent": _money(markup_percent),
        "primary_preview_ref": validated["primary_preview_ref"],
    }
