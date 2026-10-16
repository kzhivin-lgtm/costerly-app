from __future__ import annotations

from typing import Any


_EXCLUSION_CODES = {
    "none", "cover", "blank", "administrative", "other_trade", "unrelated",
}
_OBJECT_FIELDS = {
    "object_id", "transport_label", "quantity", "quantity_explicit",
    "identity_pages", "dossier_pages", "visual_group_ids", "visual_identity",
    "boundary_basis",
}
_COVERAGE_FIELDS = {"page_number", "object_ids", "exclusion_code"}

DETECTION_REGISTRY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["objects", "page_coverage"],
    "properties": {
        "objects": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": sorted(_OBJECT_FIELDS),
            "properties": {
                "object_id": {"type": "string"}, "transport_label": {"type": "string"},
                "quantity": {"type": "number", "minimum": 0}, "quantity_explicit": {"type": "boolean"},
                "identity_pages": {"type": "array", "items": {"type": "integer", "minimum": 1}},
                "dossier_pages": {"type": "array", "items": {"type": "integer", "minimum": 1}},
                "visual_group_ids": {"type": "array", "items": {"type": "string"}},
                "visual_identity": {"type": "string"}, "boundary_basis": {"type": "string"},
            },
        }},
        "page_coverage": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": sorted(_COVERAGE_FIELDS),
            "properties": {
                "page_number": {"type": "integer", "minimum": 1},
                "object_ids": {"type": "array", "items": {"type": "string"}},
                "exclusion_code": {"type": "string", "enum": sorted(_EXCLUSION_CODES)},
            },
        }},
    },
}


class DetectionRegistrySchemaError(ValueError):
    pass


def validate_detection_registry(
    result: dict[str, Any],
    *,
    visual_group_ids: set[str] | None = None,
    page_numbers: set[int] | None = None,
) -> dict[str, Any]:
    if (
        not isinstance(result, dict)
        or set(result) != {"objects", "page_coverage"}
        or not isinstance(result["objects"], list)
        or not isinstance(result["page_coverage"], list)
    ):
        raise DetectionRegistrySchemaError("registry must contain objects and page_coverage")

    object_ids: set[str] = set()
    assigned_visual_groups: list[str] = []
    for index, item in enumerate(result["objects"], start=1):
        if not isinstance(item, dict) or set(item) != _OBJECT_FIELDS:
            raise DetectionRegistrySchemaError("registry object fields do not match contract")
        object_id = str(item["object_id"])
        if object_id != f"object-{index:03d}":
            raise DetectionRegistrySchemaError("registry object IDs must be ordered")
        object_ids.add(object_id)
        if not all(str(item[key]).strip() for key in ("transport_label", "visual_identity", "boundary_basis")):
            raise DetectionRegistrySchemaError("registry identity fields are required")
        if not isinstance(item["quantity"], (int, float)) or item["quantity"] < 0 or not isinstance(item["quantity_explicit"], bool):
            raise DetectionRegistrySchemaError("registry quantity is invalid")
        if not isinstance(item["identity_pages"], list) or not all(isinstance(page, int) and page > 0 for page in item["identity_pages"]):
            raise DetectionRegistrySchemaError("registry identity pages are invalid")
        if not isinstance(item["dossier_pages"], list) or not item["dossier_pages"] or len(item["dossier_pages"]) > 12 or not all(isinstance(page, int) and page > 0 for page in item["dossier_pages"]):
            raise DetectionRegistrySchemaError("registry dossier pages are invalid")
        if not isinstance(item["visual_group_ids"], list) or not all(isinstance(group_id, str) and group_id for group_id in item["visual_group_ids"]):
            raise DetectionRegistrySchemaError("registry visual groups are invalid")
        assigned_visual_groups.extend(item["visual_group_ids"])

    if len(assigned_visual_groups) != len(set(assigned_visual_groups)):
        raise DetectionRegistrySchemaError("visual groups cannot belong to multiple commercial objects")
    if visual_group_ids is not None and not set(assigned_visual_groups).issubset(visual_group_ids):
        raise DetectionRegistrySchemaError("registry references an unknown visual group")
    if page_numbers is not None:
        declared_object_pages = {
            page
            for item in result["objects"]
            for key in ("identity_pages", "dossier_pages")
            for page in item[key]
        }
        if not declared_object_pages.issubset(page_numbers):
            raise DetectionRegistrySchemaError("registry references an unknown physical page")

    covered_pages: set[int] = set()
    for item in result["page_coverage"]:
        if not isinstance(item, dict) or set(item) != _COVERAGE_FIELDS:
            raise DetectionRegistrySchemaError("page coverage fields do not match contract")
        page_number = item["page_number"]
        assigned_objects = item["object_ids"]
        exclusion_code = item["exclusion_code"]
        if not isinstance(page_number, int) or page_number < 1 or page_number in covered_pages:
            raise DetectionRegistrySchemaError("page coverage must contain each page once")
        if (
            not isinstance(assigned_objects, list)
            or len(assigned_objects) != len(set(assigned_objects))
            or not all(
                isinstance(object_id, str) and object_id in object_ids
                for object_id in assigned_objects
            )
        ):
            raise DetectionRegistrySchemaError("page coverage object IDs are invalid")
        if exclusion_code not in _EXCLUSION_CODES:
            raise DetectionRegistrySchemaError("page coverage exclusion code is invalid")
        if assigned_objects and exclusion_code != "none":
            raise DetectionRegistrySchemaError("object evidence page cannot have an exclusion code")
        if not assigned_objects and exclusion_code == "none":
            raise DetectionRegistrySchemaError("unassigned page requires an exclusion code")
        covered_pages.add(page_number)
    if page_numbers is not None and covered_pages != page_numbers:
        raise DetectionRegistrySchemaError("page coverage must account for every physical page exactly once")
    return result
