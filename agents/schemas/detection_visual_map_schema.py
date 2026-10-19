from __future__ import annotations

from typing import Any

COMMERCIAL_VISUAL_GROUP_ROLES = {
    "assembly_view",
    "component_detail",
    "document_context",
}

# These are observable reasons, not private chain-of-thought.  Persisting them
# makes a role decision reviewable without asking the model to restate its full
# reasoning after an object-boundary failure.
COMMERCIAL_ROLE_BASIS_TYPES = {
    "finished_envelope",
    "overall_product_dimensions",
    "identifiable_product_graphic",
    "alternate_product_view",
    "explicit_section_or_detail",
    "fragment_without_finished_envelope",
    "explicit_parent_relation",
    "administrative_or_navigation_context",
    "schedule_legend_or_table",
}

_ROLE_REQUIRED_BASIS_TYPES = {
    "assembly_view": {
        "finished_envelope",
        "overall_product_dimensions",
        "identifiable_product_graphic",
        "alternate_product_view",
    },
    "component_detail": {
        "explicit_section_or_detail",
        "fragment_without_finished_envelope",
        "explicit_parent_relation",
    },
    "document_context": {
        "administrative_or_navigation_context",
        "schedule_legend_or_table",
    },
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
                ],
                "properties": {
                    "group_id": {"type": "string"},
                    "page_number": {"type": "integer", "minimum": 1},
                    "location_hint": {"type": "string"},
                    "visual_description": {"type": "string"},
                    "representation_kind": {"type": "string"},
                    "commercial_role": {
                        "type": "string",
                        "enum": sorted(COMMERCIAL_VISUAL_GROUP_ROLES),
                    },
                    "role_basis": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "string",
                            "enum": sorted(COMMERCIAL_ROLE_BASIS_TYPES),
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
        group["group_id"] = canonical_ids[raw_id]
    return result


def validate_detection_visual_map(
    result: dict[str, Any],
    *,
    require_commercial_roles: bool = False,
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
            "representation_kind",
        }
        if require_commercial_roles:
            required.update({"commercial_role", "role_basis"})
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
            or (
                require_commercial_roles
                and (
                    group["commercial_role"] not in COMMERCIAL_VISUAL_GROUP_ROLES
                    or not isinstance(group["role_basis"], list)
                    or not group["role_basis"]
                    or not all(isinstance(basis, str) for basis in group["role_basis"])
                    or len(group["role_basis"]) != len(set(group["role_basis"]))
                    or not set(group["role_basis"]).issubset(
                        COMMERCIAL_ROLE_BASIS_TYPES
                    )
                    or not set(group["role_basis"]).intersection(
                        _ROLE_REQUIRED_BASIS_TYPES[group["commercial_role"]]
                    )
                )
            )
        ):
            raise DetectionVisualMapSchemaError("visual group is invalid")
        group_ids.add(expected_id)
    return result
