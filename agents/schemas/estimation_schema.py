from __future__ import annotations

from typing import Any


ESTIMATION_STATUS_VALUES = {"estimated", "needs_review", "failed"}

REQUIRED_RESULT_FIELDS = {
    "estimate_id",
    "run_id",
    "company_id",
    "object_id",
    "object_name",
    "object_quantity",
    "status",
    "file_evidence_summary",
    "materials",
    "labor",
    "manufacturing",
    "estimation_notes",
    "missing_information",
    "confidence",
}

REQUIRED_MANUFACTURING_FIELDS = {
    "process",
    "material_family",
    "measurements",
    "flags",
    "evidence_pages",
    "confidence",
    "notes",
}

MANUFACTURING_MEASUREMENT_FIELDS = (
    "thickness_mm", "part_count", "sheet_count", "path_length_m",
    "machine_minutes", "pass_count", "hole_count", "pocket_minutes",
    "edge_banding_length_m",
)
MANUFACTURING_FLAG_FIELDS = (
    "production_file_ready", "rectangular_parts_only", "single_face_processing",
    "standard_operations_only", "has_freeform_contours", "has_internal_cutouts",
    "has_pockets", "has_horizontal_or_end_drilling", "has_repeated_hole_patterns",
    "has_tight_positional_relationships", "straight_edge_to_edge_cuts_only",
    "rough_finish_acceptable", "material_and_thickness_supported",
    "has_curves_or_shaped_edges", "precision_or_repeatability_required",
)
NORMALIZED_MANUFACTURING_FIELDS = {
    "process", "material_family", "evidence_pages", "confidence", "notes",
    *MANUFACTURING_MEASUREMENT_FIELDS, *MANUFACTURING_FLAG_FIELDS,
}
WOOD_CNC_MATERIALS = {
    "melamine_white", "melamine_colored", "plywood_exposed",
    "plywood_white_formica_two_sided", "birch_plywood", "green_mdf",
}
SHEET_LASER_MATERIALS = {"carbon_steel", "stainless_steel", "aluminum", "sheet_metal"}

REQUIRED_MATERIAL_FIELDS = {
    "group_name",
    "item_name",
    "catalog_match_query",
    "unit",
    "quantity",
    "quantity_basis",
    "evidence_pages",
    "confidence",
    "notes",
}

REQUIRED_LABOR_FIELDS = {
    "group_name",
    "work_name",
    "role",
    "hours",
    "hours_basis",
    "evidence_pages",
    "confidence",
    "notes",
}


ESTIMATION_RESULT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(REQUIRED_RESULT_FIELDS),
    "properties": {
        "estimate_id": {"type": "string"},
        "run_id": {"type": "string"},
        "company_id": {"type": "string"},
        "object_id": {"type": "string"},
        "object_name": {"type": "string"},
        "object_quantity": {"type": "number", "minimum": 0},
        "status": {"type": "string", "enum": sorted(ESTIMATION_STATUS_VALUES)},
        "file_evidence_summary": {"type": "string"},
        "materials": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(REQUIRED_MATERIAL_FIELDS),
                "properties": {
                    "group_name": {"type": "string"},
                    "item_name": {"type": "string"},
                    "catalog_match_query": {"type": "string"},
                    "unit": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 0},
                    "quantity_basis": {"type": "string"},
                    "evidence_pages": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "notes": {"type": "string"},
                },
            },
        },
        "labor": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(REQUIRED_LABOR_FIELDS),
                "properties": {
                    "group_name": {"type": "string"},
                    "work_name": {"type": "string"},
                    "role": {"type": "string"},
                    "hours": {"type": "number", "minimum": 0},
                    "hours_basis": {"type": "string"},
                    "evidence_pages": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "notes": {"type": "string"},
                },
            },
        },
        "manufacturing": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": sorted(REQUIRED_MANUFACTURING_FIELDS),
                "properties": {
                    "process": {"type": "string", "enum": ["cnc_router", "sheet_laser"]},
                    "material_family": {"type": "string"},
                    "measurements": {
                        "type": "array",
                        "items": {"type": ["number", "null"]},
                        "minItems": len(MANUFACTURING_MEASUREMENT_FIELDS),
                        "maxItems": len(MANUFACTURING_MEASUREMENT_FIELDS),
                    },
                    "flags": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["yes", "no", "unknown"]},
                        "minItems": len(MANUFACTURING_FLAG_FIELDS),
                        "maxItems": len(MANUFACTURING_FLAG_FIELDS),
                    },
                    "evidence_pages": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "notes": {"type": "string"},
                },
            },
        },
        "estimation_notes": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 100},
    },
}


class EstimationSchemaError(ValueError):
    pass


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EstimationSchemaError(f"{name} must be dict")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise EstimationSchemaError(f"{name} must be list")
    return value


def _check_required_keys(payload: dict[str, Any], required: set[str], name: str) -> None:
    missing = required - set(payload.keys())
    if missing:
        raise EstimationSchemaError(f"{name} missing keys: {sorted(missing)}")


def _check_no_extra_keys(payload: dict[str, Any], allowed: set[str], name: str) -> None:
    extra = set(payload.keys()) - allowed
    if extra:
        raise EstimationSchemaError(f"{name} has extra keys: {sorted(extra)}")


def _check_number_range(value: Any, name: str, min_value: float, max_value: float) -> None:
    if not isinstance(value, (int, float)):
        raise EstimationSchemaError(f"{name} must be number")
    if value < min_value or value > max_value:
        raise EstimationSchemaError(f"{name} must be between {min_value} and {max_value}")


def validate_estimation_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate one-object Estimation Agent output before DB persistence.

    The agent is allowed to estimate material quantities and labor hours. It is
    not allowed to return material prices, labor rates, overhead, VAT, or final
    totals; deterministic engine code owns those calculations.
    """
    result = _require_dict(result, "estimation_result")
    _check_required_keys(result, REQUIRED_RESULT_FIELDS, "estimation_result")
    _check_no_extra_keys(result, REQUIRED_RESULT_FIELDS, "estimation_result")

    if result["status"] not in ESTIMATION_STATUS_VALUES:
        raise EstimationSchemaError(
            f"estimation_result.status must be one of {sorted(ESTIMATION_STATUS_VALUES)}"
        )

    _check_number_range(result["object_quantity"], "object_quantity", 0, 999999)
    _check_number_range(result["confidence"], "confidence", 0, 100)

    materials = _require_list(result["materials"], "materials")
    labor = _require_list(result["labor"], "labor")
    manufacturing = _require_list(result["manufacturing"], "manufacturing")
    _require_list(result["estimation_notes"], "estimation_notes")
    _require_list(result["missing_information"], "missing_information")

    for index, item in enumerate(materials):
        name = f"materials[{index}]"
        item = _require_dict(item, name)
        _check_required_keys(item, REQUIRED_MATERIAL_FIELDS, name)
        _check_no_extra_keys(item, REQUIRED_MATERIAL_FIELDS, name)
        _check_number_range(item["quantity"], f"{name}.quantity", 0, 999999)
        _check_number_range(item["confidence"], f"{name}.confidence", 0, 100)

    for index, item in enumerate(labor):
        name = f"labor[{index}]"
        item = _require_dict(item, name)
        _check_required_keys(item, REQUIRED_LABOR_FIELDS, name)
        _check_no_extra_keys(item, REQUIRED_LABOR_FIELDS, name)
        _check_number_range(item["hours"], f"{name}.hours", 0, 999999)
        _check_number_range(item["confidence"], f"{name}.confidence", 0, 100)

    normalized_manufacturing = []
    for index, item in enumerate(manufacturing):
        name = f"manufacturing[{index}]"
        item = _require_dict(item, name)
        if set(item) == NORMALIZED_MANUFACTURING_FIELDS:
            normalized = item
        else:
            _check_required_keys(item, REQUIRED_MANUFACTURING_FIELDS, name)
            _check_no_extra_keys(item, REQUIRED_MANUFACTURING_FIELDS, name)
            measurements = _require_list(item["measurements"], f"{name}.measurements")
            flags = _require_list(item["flags"], f"{name}.flags")
            if len(measurements) != len(MANUFACTURING_MEASUREMENT_FIELDS):
                raise EstimationSchemaError(f"{name}.measurements has an invalid length")
            if len(flags) != len(MANUFACTURING_FLAG_FIELDS):
                raise EstimationSchemaError(f"{name}.flags has an invalid length")
            normalized = {
                "process": item["process"],
                "material_family": None if item["material_family"] == "unknown" else item["material_family"],
                "evidence_pages": item["evidence_pages"],
                "confidence": item["confidence"],
                "notes": item["notes"],
                **dict(zip(MANUFACTURING_MEASUREMENT_FIELDS, measurements)),
                **dict(zip(MANUFACTURING_FLAG_FIELDS, flags)),
            }
        if normalized["process"] not in {"cnc_router", "sheet_laser"}:
            raise EstimationSchemaError(f"{name}.process is unsupported")
        material_family = normalized.get("material_family")
        if material_family in WOOD_CNC_MATERIALS:
            normalized["process"] = "cnc_router"
        elif material_family in SHEET_LASER_MATERIALS:
            normalized["process"] = "sheet_laser"
        for field in MANUFACTURING_MEASUREMENT_FIELDS:
            value = normalized[field]
            if value is not None:
                _check_number_range(value, f"{name}.{field}", 0, 999999)
        for field in MANUFACTURING_FLAG_FIELDS:
            if normalized[field] not in {"yes", "no", "unknown"}:
                raise EstimationSchemaError(f"{name}.{field} must be yes, no, or unknown")
        _check_number_range(normalized["confidence"], f"{name}.confidence", 0, 100)
        normalized_manufacturing.append(normalized)

    result["manufacturing"] = normalized_manufacturing

    return result
