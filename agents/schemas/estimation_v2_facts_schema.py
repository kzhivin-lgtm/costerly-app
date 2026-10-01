from __future__ import annotations

from typing import Any, Iterable

SPECIFICATION_KEYS = (
    "thickness_mm", "width_mm", "length_mm", "diameter_mm", "wall_thickness_mm",
    "profile_section", "species", "grade", "alloy", "temper", "finish", "surface",
    "color", "coating", "density_class", "fire_rating", "moisture_resistance",
    "supplier_sku",
)
FEATURE_KEYS = (
    "shelf_count", "door_count", "drawer_count", "toe_kick", "back_panel",
    "plumbing_cutout", "installation_scope", "finish", "visible_finish",
    "profile_section_mm", "coating", "open_face", "bend_count", "anchor_count",
)
MANUFACTURING_MEASUREMENT_KEYS = (
    "thickness_mm", "part_count", "sheet_count", "path_length_m", "pass_count",
    "hole_count", "pocket_count", "edge_banding_length_m",
)
MANUFACTURING_FLAG_KEYS = (
    "production_file_ready", "rectangular_parts_only", "single_face_processing",
    "standard_operations_only", "has_freeform_contours", "has_internal_cutouts",
    "has_pockets", "has_horizontal_or_end_drilling", "has_repeated_hole_patterns",
    "has_tight_positional_relationships", "straight_edge_to_edge_cuts_only",
    "rough_finish_acceptable", "material_and_thickness_supported",
)
PURCHASED_SPECIFICATION_KEYS = (
    "width_mm", "depth_mm", "height_mm", "thickness_mm", "material", "finish",
    "cutout_count", "installation_scope",
)
TRANSPORT_FIELDS = frozenset({
    "status", "dimensions_mm", "materials", "features", "manufacturing_features",
    "purchased_components", "source_facts", "review_items",
    "labor_operations",
})


def _strict_object(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def _string_array() -> dict[str, Any]:
    return {"type": "array", "items": {"type": "string"}}


def _key_value_items(*, values: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": "array",
        "items": _strict_object({
            "key": {"type": "string"},
            "value": values or {"type": "string"},
        }),
    }


def build_estimation_v2_facts_schema(allowed_material_families: Iterable[str]) -> dict[str, Any]:
    families = sorted({str(value).strip() for value in allowed_material_families if str(value).strip()})
    if not families:
        raise ValueError("allowed_material_families must not be empty")
    material = _strict_object({
        "requirement_id": {"type": "string"},
        "source_name": {"type": "string"},
        "family": {"type": "string"},
        "specification_items": _key_value_items(),
        "quantity": {"type": "number"},
        "unit": {"type": "string"},
        "evidence_refs": _string_array(),
    })
    manufacturing_feature = _strict_object({
        "feature_id": {"type": "string"},
        "process": {"type": "string", "enum": ["cnc_router", "sheet_laser"]},
        "material_requirement_id": {"type": "string"},
        "measurement_items": _key_value_items(),
        "flag_items": _key_value_items(
            values={"type": "string", "enum": ["yes", "no", "unknown"]},
        ),
        "evidence_refs": _string_array(),
    })
    purchased_component = _strict_object({
        "component_id": {"type": "string"},
        "component_type": {"type": "string"},
        "quantity": {"type": "number"},
        "unit": {"type": "string"},
        "specification_items": _key_value_items(),
        "evidence_refs": _string_array(),
    })
    source_fact = _strict_object({
        "path": {"type": "string"},
        "value": {"type": "string"},
        "provenance": {"type": "string"},
        "evidence_refs": _string_array(),
    })
    review_item = _strict_object({
        "code": {"type": "string"},
        "severity": {"type": "string", "enum": ["blocking", "warning"]},
        "path": {"type": "string"},
        "message": {"type": "string"},
        "evidence_refs": _string_array(),
    })
    labor_operation = _strict_object({
        "operation_id": {"type": "string"},
        "operation_code": {"type": "string"},
        "quantity": {"type": "number"},
        "unit": {"type": "string"},
        "batch_key": {"type": "string"},
        "material_requirement_ids": _string_array(),
        "basis": {"type": "string"},
        "provenance": {"type": "string"},
        "evidence_refs": _string_array(),
        "confidence": {"type": "number"},
    })
    return _strict_object({
        "status": {"type": "string", "enum": ["ready", "review_required", "failed"]},
        "dimensions_mm": {"type": "array", "items": {"type": "number"}},
        "materials": {"type": "array", "items": material},
        "features": _key_value_items(),
        "manufacturing_features": {"type": "array", "items": manufacturing_feature},
        "purchased_components": {"type": "array", "items": purchased_component},
        "source_facts": {"type": "array", "items": source_fact},
        "review_items": {"type": "array", "items": review_item},
        "labor_operations": {"type": "array", "items": labor_operation},
    })
