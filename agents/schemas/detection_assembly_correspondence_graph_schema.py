from __future__ import annotations

from itertools import combinations
from typing import Any


PAIR_RELATIONS = {"same_assembly", "separate_assemblies", "insufficient"}
REPRESENTATION_ROLES = {"complete_assembly", "supporting_view_or_detail"}


DETECTION_ASSEMBLY_CORRESPONDENCE_GRAPH_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["representation_roles", "pair_relations"],
    "properties": {
        "representation_roles": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["representation_id", "role", "visible_identity"],
                "properties": {
                    "representation_id": {"type": "string"},
                    "role": {"type": "string", "enum": sorted(REPRESENTATION_ROLES)},
                    "visible_identity": {"type": "string"},
                },
            },
        },
        "pair_relations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "first_representation_id",
                    "second_representation_id",
                    "relation",
                    "basis",
                ],
                "properties": {
                    "first_representation_id": {"type": "string"},
                    "second_representation_id": {"type": "string"},
                    "relation": {"type": "string", "enum": sorted(PAIR_RELATIONS)},
                    "basis": {"type": "string"},
                },
            },
        },
    },
}


class DetectionAssemblyCorrespondenceGraphError(ValueError):
    pass


def _expected_pairs(representation_ids: list[str]) -> set[tuple[str, str]]:
    return set(combinations(representation_ids, 2))


def normalize_detection_assembly_graph(
    result: dict[str, Any],
    *,
    representation_ids: list[str],
) -> dict[str, Any]:
    """Normalize harmless provider ordering without changing graph meaning."""
    if not isinstance(result, dict):
        return result
    ranks = {representation_id: index for index, representation_id in enumerate(representation_ids)}
    roles = result.get("representation_roles")
    if isinstance(roles, list) and all(isinstance(role, dict) for role in roles):
        result["representation_roles"] = sorted(
            roles,
            key=lambda role: ranks.get(str(role.get("representation_id")), len(ranks)),
        )
    relations = result.get("pair_relations")
    if isinstance(relations, list):
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            first = str(relation.get("first_representation_id") or "")
            second = str(relation.get("second_representation_id") or "")
            if ranks.get(first, len(ranks)) > ranks.get(second, len(ranks)):
                relation["first_representation_id"] = second
                relation["second_representation_id"] = first
        result["pair_relations"] = sorted(
            relations,
            key=lambda relation: (
                ranks.get(str(relation.get("first_representation_id")), len(ranks)),
                ranks.get(str(relation.get("second_representation_id")), len(ranks)),
            ),
        )
    return result


def validate_detection_assembly_correspondence_graph(
    result: dict[str, Any],
    *,
    representation_ids: list[str],
) -> dict[str, Any]:
    """Validate one exhaustive pairwise correspondence graph."""
    expected_ids = set(representation_ids)
    if (
        len(representation_ids) < 2
        or len(representation_ids) != len(expected_ids)
        or not isinstance(result, dict)
        or set(result) != {"representation_roles", "pair_relations"}
        or not isinstance(result["representation_roles"], list)
        or not isinstance(result["pair_relations"], list)
    ):
        raise DetectionAssemblyCorrespondenceGraphError(
            "assembly correspondence graph fields do not match contract"
        )

    roles_by_id: dict[str, dict[str, Any]] = {}
    for role in result["representation_roles"]:
        required = {"representation_id", "role", "visible_identity"}
        representation_id = role.get("representation_id") if isinstance(role, dict) else None
        if (
            not isinstance(role, dict)
            or set(role) != required
            or not isinstance(representation_id, str)
            or representation_id not in expected_ids
            or representation_id in roles_by_id
            or role.get("role") not in REPRESENTATION_ROLES
            or not isinstance(role.get("visible_identity"), str)
            or not role["visible_identity"].strip()
        ):
            raise DetectionAssemblyCorrespondenceGraphError("representation role is invalid")
        roles_by_id[representation_id] = role
    if set(roles_by_id) != expected_ids:
        raise DetectionAssemblyCorrespondenceGraphError(
            "graph must classify every representation exactly once"
        )

    expected_pairs = _expected_pairs(representation_ids)
    observed_pairs: set[tuple[str, str]] = set()
    for relation in result["pair_relations"]:
        required = {
            "first_representation_id",
            "second_representation_id",
            "relation",
            "basis",
        }
        if not isinstance(relation, dict) or set(relation) != required:
            raise DetectionAssemblyCorrespondenceGraphError("pair relation fields are invalid")
        first = relation["first_representation_id"]
        second = relation["second_representation_id"]
        pair = (first, second)
        if (
            not isinstance(first, str)
            or not isinstance(second, str)
            or pair not in expected_pairs
            or pair in observed_pairs
            or relation["relation"] not in PAIR_RELATIONS
            or not isinstance(relation["basis"], str)
            or not relation["basis"].strip()
        ):
            raise DetectionAssemblyCorrespondenceGraphError("pair relation is invalid")
        observed_pairs.add(pair)
    if observed_pairs != expected_pairs:
        raise DetectionAssemblyCorrespondenceGraphError(
            "graph must account for every representation pair exactly once"
        )
    return result


def derive_detection_assembly_correspondence(
    graph: dict[str, Any],
    *,
    representation_ids: list[str],
) -> tuple[dict[str, Any], str]:
    """Keep direct graph facts without promoting uncertainty to a false lock."""
    relations = graph["pair_relations"]

    parents = {representation_id: representation_id for representation_id in representation_ids}

    def find(representation_id: str) -> str:
        while parents[representation_id] != representation_id:
            parents[representation_id] = parents[parents[representation_id]]
            representation_id = parents[representation_id]
        return representation_id

    def union(first: str, second: str) -> None:
        first_root = find(first)
        second_root = find(second)
        if first_root != second_root:
            parents[second_root] = first_root

    for relation in relations:
        if relation["relation"] == "same_assembly":
            union(relation["first_representation_id"], relation["second_representation_id"])

    roles_by_id = {
        role["representation_id"]: role
        for role in graph["representation_roles"]
    }
    components: dict[str, list[str]] = {}
    for representation_id in representation_ids:
        components.setdefault(find(representation_id), []).append(representation_id)

    conflicting_component_roots = {
        find(relation["first_representation_id"])
        for relation in relations
        if relation["relation"] == "separate_assemblies"
        and find(relation["first_representation_id"]) == find(relation["second_representation_id"])
    }

    candidates: list[dict[str, Any]] = []
    non_assembly_representation_ids: list[str] = []
    for root, members in components.items():
        positive_same_bases = [
            relation["basis"].strip()
            for relation in relations
            if relation["relation"] == "same_assembly"
            and relation["first_representation_id"] in members
            and relation["second_representation_id"] in members
        ]
        if root in conflicting_component_roots or not positive_same_bases:
            non_assembly_representation_ids.extend(members)
            continue
        representative = members[0]
        candidates.append({
            "candidate_id": f"assembly-{len(candidates) + 1:03d}",
            "representation_ids": members,
            "visual_identity": roles_by_id[representative]["visible_identity"].strip(),
            "correspondence_basis": (
                "direct same-assembly correspondence graph"
                + f": {'; '.join(positive_same_bases)}"
            ),
        })

    result = {
        "assembly_candidates": candidates,
        "non_assembly_representation_ids": non_assembly_representation_ids,
        "must_separate_representation_pairs": [
            {
                "first_representation_id": relation["first_representation_id"],
                "second_representation_id": relation["second_representation_id"],
                "basis": relation["basis"],
            }
            for relation in relations
            if relation["relation"] == "separate_assemblies"
        ],
    }
    if conflicting_component_roots:
        return result, "graph_partial_conflicting_positive_component"
    if any(relation["relation"] == "insufficient" for relation in relations):
        return result, "graph_partial_constraints"
    return result, "graph_decisive"
