from __future__ import annotations

from typing import Any


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
                    "related_group_ids",
                ],
                "properties": {
                    "group_id": {"type": "string"},
                    "page_number": {"type": "integer", "minimum": 1},
                    "location_hint": {"type": "string"},
                    "visual_description": {"type": "string"},
                    "representation_kind": {"type": "string"},
                    "related_group_ids": {"type": "array", "items": {"type": "string"}},
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
        related = group.get("related_group_ids")
        if isinstance(related, list):
            group["related_group_ids"] = list(dict.fromkeys(
                canonical_ids[related_id]
                for related_id in related
                if related_id in canonical_ids and related_id != raw_id
            ))
        group["group_id"] = canonical_ids[raw_id]
    return result


def validate_detection_visual_map(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"visual_groups"}:
        raise DetectionVisualMapSchemaError("visual map must contain only visual_groups")
    groups = result["visual_groups"]
    if not isinstance(groups, list):
        raise DetectionVisualMapSchemaError("visual_groups must be a list")

    group_ids: set[str] = set()
    for index, group in enumerate(groups, start=1):
        required = {
            "group_id", "page_number", "location_hint", "visual_description",
            "representation_kind", "related_group_ids",
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
            or not isinstance(group["related_group_ids"], list)
        ):
            raise DetectionVisualMapSchemaError("visual group is invalid")
        group_ids.add(expected_id)

    for group in groups:
        group_id = group["group_id"]
        related = group["related_group_ids"]
        if (
            len(set(related)) != len(related)
            or group_id in related
            or not all(related_id in group_ids for related_id in related)
        ):
            raise DetectionVisualMapSchemaError("visual group relations are invalid")
    return result
