from __future__ import annotations

import copy

from typing import Any

COMMERCIAL_VISUAL_GROUP_ROLES = {
    "assembly_view",
    "component_detail",
    "document_context",
}

# V4.12 separates a provider's observable depiction classification from the
# runtime's commercial role.  This prevents one response from labelling a
# group a component and then using it as an object's complete representation.
DEPICTION_SCOPES = {
    "complete_product_representation",
    "partial_component_representation",
    "document_context",
}

# These are observable reasons, not private chain-of-thought.  Persisting them
# makes the scope decision reviewable without asking the model to restate its
# full reasoning after an object-boundary failure.
DEPICTION_SCOPE_BASIS_TYPES = {
    "complete_outer_envelope",
    "overall_product_dimensions",
    "product_specific_geometry",
    "alternate_product_view",
    "explicit_section_cut",
    "cropped_or_open_boundary",
    "explicit_parent_reference",
    "administrative_context",
    "navigation_only_plan",
    "table_with_semantic_headers",
}

_SCOPE_ALLOWED_BASIS_TYPES = {
    "complete_product_representation": {
        "complete_outer_envelope",
        "overall_product_dimensions",
        "product_specific_geometry",
        "alternate_product_view",
    },
    "partial_component_representation": {
        "explicit_section_cut",
        "cropped_or_open_boundary",
        "explicit_parent_reference",
    },
    "document_context": {
        "administrative_context",
        "navigation_only_plan",
        "table_with_semantic_headers",
    },
}

DEPICTION_SCOPE_TO_COMMERCIAL_ROLE = {
    "complete_product_representation": "assembly_view",
    "partial_component_representation": "component_detail",
    "document_context": "document_context",
}

# The returned visual-map shape stays compatible with the established Registry
# and Evidence code.  Scope and its raw basis remain in the provider audit;
# derived role fields are internal runtime facts, never accepted from Claude.
_SCOPE_BASIS_TO_ROLE_BASIS = {
    "complete_outer_envelope": "finished_envelope",
    "overall_product_dimensions": "overall_product_dimensions",
    "product_specific_geometry": "identifiable_product_graphic",
    "alternate_product_view": "alternate_product_view",
    "explicit_section_cut": "explicit_section_or_detail",
    "cropped_or_open_boundary": "fragment_without_finished_envelope",
    "explicit_parent_reference": "explicit_parent_relation",
    "administrative_context": "administrative_context",
    "navigation_only_plan": "navigation_only_plan",
    "table_with_semantic_headers": "table_with_semantic_headers",
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
                    "depiction_scope": {
                        "type": "string",
                        "enum": sorted(DEPICTION_SCOPES),
                    },
                    "scope_basis": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "string",
                            "enum": sorted(DEPICTION_SCOPE_BASIS_TYPES),
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
    require_depiction_scope: bool = False,
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
        if require_depiction_scope:
            required.update({"depiction_scope", "scope_basis"})
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
                require_depiction_scope
                and (
                    group["depiction_scope"] not in DEPICTION_SCOPES
                    or not isinstance(group["scope_basis"], list)
                    or not group["scope_basis"]
                    or not all(isinstance(basis, str) for basis in group["scope_basis"])
                    or len(group["scope_basis"]) != len(set(group["scope_basis"]))
                    or not set(group["scope_basis"]).issubset(
                        _SCOPE_ALLOWED_BASIS_TYPES[group["depiction_scope"]]
                    )
                )
            )
        ):
            raise DetectionVisualMapSchemaError("visual group is invalid")
        group_ids.add(expected_id)
    return result


def derive_detection_visual_map_commercial_roles(
    scoped_visual_map: dict[str, Any],
) -> dict[str, Any]:
    """Map validated depiction scopes to the Registry's internal role contract."""
    derived_groups: list[dict[str, Any]] = []
    for group in scoped_visual_map["visual_groups"]:
        derived_group = {
            key: copy.deepcopy(group[key])
            for key in (
                "group_id",
                "page_number",
                "location_hint",
                "visual_description",
                "representation_kind",
            )
        }
        derived_group["commercial_role"] = DEPICTION_SCOPE_TO_COMMERCIAL_ROLE[
            group["depiction_scope"]
        ]
        derived_group["role_basis"] = [
            _SCOPE_BASIS_TO_ROLE_BASIS[basis]
            for basis in group["scope_basis"]
        ]
        derived_groups.append(derived_group)
    return {"visual_groups": derived_groups}
