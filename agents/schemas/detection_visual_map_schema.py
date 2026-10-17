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
                    "related_groups",
                ],
                "properties": {
                    "group_id": {"type": "string"},
                    "page_number": {"type": "integer", "minimum": 1},
                    "location_hint": {"type": "string"},
                    "visual_description": {"type": "string"},
                    "representation_kind": {"type": "string"},
                    "related_groups": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["group_id", "relation_type", "match_basis"],
                            "properties": {
                                "group_id": {"type": "string"},
                                "relation_type": {
                                    "type": "string",
                                    "enum": ["same_assembly_view", "object_detail"],
                                },
                                "match_basis": {"type": "string"},
                            },
                        },
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
        related = group.get("related_groups")
        if isinstance(related, list):
            normalized_related: list[dict[str, Any]] = []
            seen_related: set[str] = set()
            for relation in related:
                if not isinstance(relation, dict):
                    continue
                related_id = str(relation.get("group_id") or "")
                if (
                    related_id not in canonical_ids
                    or related_id == raw_id
                    or related_id in seen_related
                ):
                    continue
                normalized_relation = dict(relation)
                normalized_relation["group_id"] = canonical_ids[related_id]
                normalized_related.append(normalized_relation)
                seen_related.add(related_id)
            group["related_groups"] = normalized_related
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
            "representation_kind", "related_groups",
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
            or not isinstance(group["related_groups"], list)
        ):
            raise DetectionVisualMapSchemaError("visual group is invalid")
        group_ids.add(expected_id)

    for group in groups:
        group_id = group["group_id"]
        related = group["related_groups"]
        related_ids = [str(relation.get("group_id") or "") for relation in related if isinstance(relation, dict)]
        if (
            len(related_ids) != len(related)
            or len(set(related_ids)) != len(related_ids)
            or group_id in related_ids
            or not all(related_id in group_ids for related_id in related_ids)
            or not all(
                isinstance(relation, dict)
                and set(relation) == {"group_id", "relation_type", "match_basis"}
                and relation["relation_type"] in {"same_assembly_view", "object_detail"}
                and str(relation["match_basis"] or "").strip()
                for relation in related
            )
        ):
            raise DetectionVisualMapSchemaError("visual group relations are invalid")
    return result


def visual_group_adjacency(groups: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Return the explicit, positive correspondence graph for Registry checks."""
    adjacency = {str(group["group_id"]): set() for group in groups}
    for group in groups:
        group_id = str(group["group_id"])
        for relation in group["related_groups"]:
            related_id = str(relation["group_id"])
            adjacency[group_id].add(related_id)
            adjacency[related_id].add(group_id)
    return adjacency
