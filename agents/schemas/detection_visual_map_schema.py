from __future__ import annotations

from typing import Any

VISUAL_REPRESENTATION_SCOPES = {
    "product_representation",
    "document_context",
}

DERIVED_COMMERCIAL_VISUAL_GROUP_ROLES = {
    "assembly_view",
    "component_detail",
    "document_context",
}


DETECTION_VISUAL_MAP_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["visual_groups"],
    "properties": {
        "visual_groups": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "group_id",
                    "page_number",
                    "location_hint",
                    "visual_description",
                    "representation_kind",
                    "representation_scope",
                ],
                "properties": {
                    "group_id": {"type": "string"},
                    "page_number": {"type": "integer", "minimum": 1},
                    "location_hint": {"type": "string"},
                    "visual_description": {"type": "string"},
                    "representation_kind": {"type": "string"},
                    "representation_scope": {
                        "type": "string",
                        "enum": sorted(VISUAL_REPRESENTATION_SCOPES),
                    },
                },
            },
        },
    },
}


class DetectionVisualMapSchemaError(ValueError):
    pass


def normalize_detection_visual_map_group_ids(result: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize provider group IDs without changing visual content.

    The IDs are internal join keys, not model judgment. Claude may choose a
    different but unique sequence despite the JSON example, so normalize that
    presentation variance before enforcing the strict map-to-registry join.
    """
    if not isinstance(result, dict) or not isinstance(result.get("visual_groups"), list):
        return result
    groups = result["visual_groups"]
    raw_ids: list[str] = []
    for group in groups:
        if not isinstance(group, dict):
            return result
        raw_id = str(group.get("group_id") or "").strip()
        if not raw_id:
            return result
        raw_ids.append(raw_id)
    if len(raw_ids) != len(set(raw_ids)):
        return result

    canonical_ids = {
        raw_id: f"view-{index:03d}"
        for index, raw_id in enumerate(raw_ids, start=1)
    }
    for group, raw_id in zip(groups, raw_ids, strict=True):
        group["group_id"] = canonical_ids[raw_id]
    return result


def validate_detection_visual_map(
    result: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"visual_groups"}:
        raise DetectionVisualMapSchemaError("visual map must contain only visual_groups")
    groups = result["visual_groups"]
    if not isinstance(groups, list):
        raise DetectionVisualMapSchemaError("visual_groups must be a list")

    group_ids: set[str] = set()
    for index, group in enumerate(groups, start=1):
        required = {
            "group_id", "page_number", "location_hint", "visual_description",
            "representation_kind", "representation_scope",
        }
        if not isinstance(group, dict) or set(group) != required:
            raise DetectionVisualMapSchemaError("visual group fields do not match contract")
        expected_id = f"view-{index:03d}"
        if str(group["group_id"]) != expected_id:
            raise DetectionVisualMapSchemaError("visual group IDs must be ordered")
        if (
            not isinstance(group["page_number"], int)
            or group["page_number"] < 1
            or not all(str(group[key]).strip() for key in (
                "location_hint", "visual_description", "representation_kind",
            ))
            or group["representation_scope"] not in VISUAL_REPRESENTATION_SCOPES
        ):
            raise DetectionVisualMapSchemaError("visual group is invalid")
        group_ids.add(expected_id)
    return result


def derive_detection_visual_group_roles(
    visual_map: dict[str, Any],
    *,
    assigned_visual_group_ids: set[str],
) -> dict[str, str]:
    """Derive commercial roles after, never before, boundary resolution.

    The model maps only whether pixels are a product representation or document
    context. The accepted object graph owns the commercial interpretation:
    linked product representations are assembly views, unlinked physical
    depictions are details, and document context stays context.
    """
    roles: dict[str, str] = {}
    for group in visual_map["visual_groups"]:
        group_id = group["group_id"]
        if group_id in assigned_visual_group_ids:
            roles[group_id] = "assembly_view"
        elif group["representation_scope"] == "document_context":
            roles[group_id] = "document_context"
        else:
            roles[group_id] = "component_detail"
    return roles
