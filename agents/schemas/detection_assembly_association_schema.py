from __future__ import annotations

from typing import Any


DETECTION_ASSEMBLY_ASSOCIATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["attach_existing", "new_objects"],
    "properties": {
        "attach_existing": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "visual_group_ids",
                    "object_id",
                    "association_basis",
                    "evidence_page_numbers",
                ],
                "properties": {
                    "visual_group_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "object_id": {"type": "string"},
                    "association_basis": {"type": "string"},
                    "evidence_page_numbers": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
        "new_objects": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "visual_group_ids",
                    "visual_identity",
                    "boundary_basis",
                    "quantity",
                    "quantity_explicit",
                    "evidence_page_numbers",
                ],
                "properties": {
                    "visual_group_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                    "visual_identity": {"type": "string"},
                    "boundary_basis": {"type": "string"},
                    "quantity": {"type": "number", "minimum": 1},
                    "quantity_explicit": {"type": "boolean"},
                    "evidence_page_numbers": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
    },
}


class DetectionAssemblyAssociationSchemaError(ValueError):
    """Association resolver output cannot safely amend a locked Registry."""


def _group_ids(value: object, *, name: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(group_id, str) and group_id for group_id in value)
        or len(value) != len(set(value))
    ):
        raise DetectionAssemblyAssociationSchemaError(f"{name} visual group IDs are invalid")
    return value


def _pages(value: object, *, name: str) -> list[int]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(page, int) and page > 0 for page in value)
        or len(value) != len(set(value))
    ):
        raise DetectionAssemblyAssociationSchemaError(f"{name} evidence pages are invalid")
    return value


def validate_detection_assembly_association(
    result: dict[str, Any],
    *,
    orphan_group_ids: set[str],
    existing_object_ids: set[str],
    page_count: int,
) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"attach_existing", "new_objects"}:
        raise DetectionAssemblyAssociationSchemaError(
            "assembly association must contain only attach_existing and new_objects"
        )
    attached = result["attach_existing"]
    new_objects = result["new_objects"]
    if not isinstance(attached, list) or not isinstance(new_objects, list):
        raise DetectionAssemblyAssociationSchemaError("assembly association lists are invalid")

    assigned_group_ids: list[str] = []
    for index, item in enumerate(attached, start=1):
        name = f"attach_existing[{index}]"
        required = {
            "visual_group_ids", "object_id", "association_basis", "evidence_page_numbers",
        }
        if not isinstance(item, dict) or set(item) != required:
            raise DetectionAssemblyAssociationSchemaError(f"{name} fields do not match contract")
        if item["object_id"] not in existing_object_ids:
            raise DetectionAssemblyAssociationSchemaError(f"{name} references an unknown object")
        if not isinstance(item["association_basis"], str) or not item["association_basis"].strip():
            raise DetectionAssemblyAssociationSchemaError(f"{name} association basis is required")
        assigned_group_ids.extend(_group_ids(item["visual_group_ids"], name=name))
        pages = _pages(item["evidence_page_numbers"], name=name)
        if any(page > page_count for page in pages):
            raise DetectionAssemblyAssociationSchemaError(f"{name} references pages outside the upload")

    for index, item in enumerate(new_objects, start=1):
        name = f"new_objects[{index}]"
        required = {
            "visual_group_ids", "visual_identity", "boundary_basis", "quantity",
            "quantity_explicit", "evidence_page_numbers",
        }
        if not isinstance(item, dict) or set(item) != required:
            raise DetectionAssemblyAssociationSchemaError(f"{name} fields do not match contract")
        if not all(isinstance(item[key], str) and item[key].strip() for key in ("visual_identity", "boundary_basis")):
            raise DetectionAssemblyAssociationSchemaError(f"{name} identity fields are required")
        if not isinstance(item["quantity"], (int, float)) or item["quantity"] < 1:
            raise DetectionAssemblyAssociationSchemaError(f"{name} quantity is invalid")
        if not isinstance(item["quantity_explicit"], bool):
            raise DetectionAssemblyAssociationSchemaError(f"{name} quantity_explicit is invalid")
        assigned_group_ids.extend(_group_ids(item["visual_group_ids"], name=name))
        pages = _pages(item["evidence_page_numbers"], name=name)
        if any(page > page_count for page in pages):
            raise DetectionAssemblyAssociationSchemaError(f"{name} references pages outside the upload")

    assigned = set(assigned_group_ids)
    if assigned != orphan_group_ids or len(assigned_group_ids) != len(assigned):
        raise DetectionAssemblyAssociationSchemaError(
            "assembly association must resolve every orphan assembly view exactly once"
        )
    return result
