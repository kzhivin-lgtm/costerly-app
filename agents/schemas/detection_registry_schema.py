from __future__ import annotations
import copy
from collections import deque
from typing import Any

DETECTION_REGISTRY_JSON_SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["objects"],"properties":{"objects":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"],"properties":{"object_id":{"type":"string"},"transport_label":{"type":"string"},"quantity":{"type":"number","minimum":0},"quantity_explicit":{"type":"boolean"},"identity_pages":{"type":"array","items":{"type":"integer","minimum":1}},"estimation_evidence_pages":{"type":"array","items":{"type":"integer","minimum":1}},"visual_group_ids":{"type":"array","minItems":1,"items":{"type":"string"}},"visual_identity":{"type":"string"},"boundary_basis":{"type":"string"}}}}}}

PAIRWISE_MERGE_EVIDENCE_TYPES = frozenset({
    "explicit_document_relation",
    "dimension_equality",
    "matching_topology",
    "dimension_transform",
    "unique_geometry",
    "direct_shared_structure",
})
PAIRWISE_EVIDENCE_RELATIONSHIPS = frozenset({
    "same_object_view",
    "object_detail",
    "reference_link",
})
MERGE_EVIDENCE_RELATIONSHIPS = frozenset({
    "same_object_view",
    "object_detail",
})
REFERENCE_RELATIONSHIP = "reference_link"
PROOF_PARENT_DECISIONS = frozenset({
    "new_object_root",
    "attach_to_group",
})
PROOF_PARENT_ROOT_GROUP_ID = "ROOT"
PROOF_PARENT_RELATIONSHIPS = frozenset({
    "new_object_root",
    *PAIRWISE_EVIDENCE_RELATIONSHIPS,
})
_NON_EXPLICIT_MERGE_SUPPORT_TYPES = frozenset({
    "dimension_equality",
    "matching_topology",
    "dimension_transform",
    "unique_geometry",
})

DETECTION_PAIRWISE_MERGE_PROOF_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "group_id_a",
            "group_id_b",
            "relationship",
            "evidence_facts",
            "commercial_inseparability",
        ],
        "properties": {
            "group_id_a": {"type": "string"},
            "group_id_b": {"type": "string"},
            "relationship": {
                "type": "string",
                "enum": sorted(PAIRWISE_EVIDENCE_RELATIONSHIPS),
            },
            "evidence_facts": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["evidence_type", "evidence_pages", "observation"],
                    "properties": {
                        "evidence_type": {
                            "type": "string",
                            "enum": sorted(PAIRWISE_MERGE_EVIDENCE_TYPES),
                        },
                        "evidence_pages": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "integer", "minimum": 1},
                        },
                        "observation": {"type": "string"},
                    },
                },
            },
            "commercial_inseparability": {"type": "string"},
        },
    },
}

DETECTION_STANDALONE_PACKAGE_GROUP_IDS_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}

DETECTION_SHARED_REFERENCE_GROUP_IDS_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}

DETECTION_BLOCKED_MERGE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["candidate_parent_group_id", "conflict_type", "observation"],
    "properties": {
        "candidate_parent_group_id": {"type": "string"},
        "conflict_type": {"type": "string", "enum": ["dimension_conflict"]},
        "observation": {"type": "string"},
    },
}

# A proof parent is emitted for every visual group.  It makes the model choose
# between a new commercial candidate and an evidence-backed join, instead of
# making an optional global edge list easy to omit.  Runtime turns accepted
# attachment decisions back into the same typed proof forest used by V4.17.
DETECTION_PROOF_PARENT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "decision",
        "parent_group_id",
        "relationship",
        "evidence_facts",
        "decision_reason",
    ],
    "properties": {
        "decision": {
            "type": "string",
            "enum": sorted(PROOF_PARENT_DECISIONS),
        },
        "parent_group_id": {"type": "string"},
        "relationship": {
            "type": "string",
            "enum": sorted(PROOF_PARENT_RELATIONSHIPS),
        },
        "evidence_facts": {
            "type": "array",
            "items": copy.deepcopy(
                DETECTION_PAIRWISE_MERGE_PROOF_JSON_SCHEMA["items"]["properties"][
                    "evidence_facts"
                ]["items"]
            ),
        },
        "blocked_merge": copy.deepcopy(DETECTION_BLOCKED_MERGE_JSON_SCHEMA),
        "decision_reason": {"type": "string"},
    },
}

class DetectionRegistrySchemaError(ValueError):
    """Registry contract failure with safe deterministic diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details or {}


def validate_detection_registry(
    result: dict[str, Any],
    *,
    visual_group_ids: set[str] | None = None,
    object_evidence_group_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"objects"} or not isinstance(result["objects"], list):
        raise DetectionRegistrySchemaError("registry must contain only objects")
    required = {"object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"}
    visual_group_references: dict[str, list[str]] = {}
    for index, item in enumerate(result["objects"], start=1):
        if not isinstance(item, dict) or set(item) != required:
            raise DetectionRegistrySchemaError("registry object fields do not match contract")
        if str(item["object_id"]) != f"object-{index:03d}":
            raise DetectionRegistrySchemaError("registry object IDs must be ordered")
        if not str(item["transport_label"]).strip() or not str(item["visual_identity"]).strip() or not str(item["boundary_basis"]).strip():
            raise DetectionRegistrySchemaError("registry identity fields are required")
        if not isinstance(item["quantity"], (int,float)) or item["quantity"] < 0 or not isinstance(item["quantity_explicit"], bool):
            raise DetectionRegistrySchemaError("registry quantity is invalid")
        if not isinstance(item["identity_pages"], list) or not all(isinstance(page,int) and page > 0 for page in item["identity_pages"]):
            raise DetectionRegistrySchemaError("registry pages are invalid")
        if not isinstance(item["estimation_evidence_pages"], list) or not item["estimation_evidence_pages"] or not all(isinstance(page,int) and page > 0 for page in item["estimation_evidence_pages"]):
            raise DetectionRegistrySchemaError("registry estimation evidence pages are invalid")
        if not set(item["identity_pages"]).issubset(item["estimation_evidence_pages"]):
            raise DetectionRegistrySchemaError("registry identity pages must be estimation evidence")
        if (
            not isinstance(item["visual_group_ids"], list)
            or not item["visual_group_ids"]
            or not all(
                isinstance(group_id, str) and group_id
                for group_id in item["visual_group_ids"]
            )
            or len(item["visual_group_ids"]) != len(set(item["visual_group_ids"]))
        ):
            raise DetectionRegistrySchemaError("registry visual groups are invalid")
        for group_id in item["visual_group_ids"]:
            visual_group_references.setdefault(group_id, []).append(item["object_id"])
    assigned_visual_groups = set(visual_group_references)
    if visual_group_ids is not None and not assigned_visual_groups.issubset(visual_group_ids):
        raise DetectionRegistrySchemaError("registry references an unknown visual group")
    if object_evidence_group_ids is not None:
        non_object_evidence_group_ids = sorted(
            group_id
            for group_id in assigned_visual_groups
            if group_id not in object_evidence_group_ids
        )
        if non_object_evidence_group_ids:
            raise DetectionRegistrySchemaError(
                "registry visual groups must be object evidence",
                details={"non_object_evidence_group_ids": non_object_evidence_group_ids},
            )
        unassigned_object_evidence_group_ids = sorted(
            object_evidence_group_ids - assigned_visual_groups
        )
        if unassigned_object_evidence_group_ids:
            raise DetectionRegistrySchemaError(
                "registry must account for every object-evidence group",
                details={
                    "unassigned_object_evidence_group_ids": (
                        unassigned_object_evidence_group_ids
                    ),
                },
            )
    return result


def validate_detection_pairwise_merge_proofs(
    proofs: object,
    *,
    visual_group_ids: set[str],
    page_count: int,
) -> list[dict[str, Any]]:
    """Validate evidence-backed joins before any commercial object exists.

    The provider may state only visual groups and pairwise proof edges. Object
    membership is deliberately absent from this contract: connected proof-tree
    components are the single source from which runtime derives each commercial
    object. A singleton visual group is a valid component and needs no edge.
    """
    if not isinstance(proofs, list):
        raise DetectionRegistrySchemaError("pairwise merge proofs must be a list")
    if not visual_group_ids:
        if proofs:
            raise DetectionRegistrySchemaError(
                "pairwise merge proofs cannot reference an empty object-evidence inventory"
            )
        return []
    seen_edges: set[tuple[str, str]] = set()
    adjacency: dict[str, set[str]] = {
        group_id: set() for group_id in visual_group_ids
    }
    required = {
        "group_id_a", "group_id_b", "relationship",
        "evidence_facts", "commercial_inseparability",
    }
    for proof in proofs:
        if not isinstance(proof, dict) or set(proof) != required:
            raise DetectionRegistrySchemaError("pairwise merge proof fields do not match contract")
        group_id_a = str(proof["group_id_a"] or "")
        group_id_b = str(proof["group_id_b"] or "")
        if (
            group_id_a >= group_id_b
            or group_id_a not in visual_group_ids
            or group_id_b not in visual_group_ids
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof groups are invalid")
        if (
            not isinstance(proof["relationship"], str)
            or proof["relationship"] not in PAIRWISE_EVIDENCE_RELATIONSHIPS
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof relationship is invalid")
        evidence_facts = proof["evidence_facts"]
        if (
            not isinstance(evidence_facts, list)
            or not evidence_facts
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof evidence facts are invalid")
        evidence_types: set[str] = set()
        evidence_fact_keys: set[tuple[str, tuple[int, ...], str]] = set()
        for evidence_fact in evidence_facts:
            if (
                not isinstance(evidence_fact, dict)
                or set(evidence_fact) != {"evidence_type", "evidence_pages", "observation"}
            ):
                raise DetectionRegistrySchemaError("pairwise merge proof evidence facts are invalid")
            evidence_type = evidence_fact["evidence_type"]
            evidence_pages = evidence_fact["evidence_pages"]
            observation = str(evidence_fact["observation"] or "").strip()
            if (
                not isinstance(evidence_type, str)
                or evidence_type not in PAIRWISE_MERGE_EVIDENCE_TYPES
                or not isinstance(evidence_pages, list)
                or not evidence_pages
                or len(evidence_pages) != len(set(evidence_pages))
                or not all(
                    isinstance(page, int) and 1 <= page <= page_count
                    for page in evidence_pages
                )
                or not observation
            ):
                raise DetectionRegistrySchemaError("pairwise merge proof evidence facts are invalid")
            evidence_fact_key = (evidence_type, tuple(sorted(evidence_pages)), observation)
            if evidence_fact_key in evidence_fact_keys:
                raise DetectionRegistrySchemaError("pairwise merge proof evidence facts are invalid")
            evidence_fact_keys.add(evidence_fact_key)
            evidence_types.add(evidence_type)
        relationship = proof["relationship"]
        has_standalone_dimension_transform = (
            "dimension_transform" in evidence_types
        )
        if relationship in MERGE_EVIDENCE_RELATIONSHIPS and (
            "explicit_document_relation" not in evidence_types
            and not has_standalone_dimension_transform
            and (
                len(evidence_facts) < 2
                or not set(evidence_types).intersection(
                    _NON_EXPLICIT_MERGE_SUPPORT_TYPES
                )
            )
        ):
            raise DetectionRegistrySchemaError(
                "pairwise merge needs an explicit document relation, a dimension transform, or two independent evidence facts"
            )
        if (
            not str(proof["commercial_inseparability"] or "").strip()
        ):
            raise DetectionRegistrySchemaError("pairwise merge proof commercial basis is invalid")
        edge_key = (group_id_a, group_id_b)
        if edge_key in seen_edges:
            raise DetectionRegistrySchemaError("pairwise merge proofs repeat a relation")
        seen_edges.add(edge_key)
        if relationship in MERGE_EVIDENCE_RELATIONSHIPS:
            adjacency[group_id_a].add(group_id_b)
            adjacency[group_id_b].add(group_id_a)

    visited: set[str] = set()
    for group_id in sorted(visual_group_ids):
        if group_id in visited:
            continue
        component: set[str] = set()
        queue = deque([group_id])
        edge_count = 0
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            edge_count += len(adjacency[current])
            queue.extend(adjacency[current] - component)
        visited.update(component)
        if edge_count // 2 != max(0, len(component) - 1):
            raise DetectionRegistrySchemaError(
                "pairwise merge proofs must form one minimal proof tree",
                details={
                    "group_ids": sorted(component),
                    "expected_proof_count": max(0, len(component) - 1),
                    "actual_proof_count": edge_count // 2,
                },
            )

    return proofs


def derive_detection_pairwise_merge_proofs_from_parent_links(
    visual_groups: object,
    *,
    page_count: int,
) -> list[dict[str, Any]]:
    """Build the proof forest from one required decision per visual group.

    Every group must either begin a new component or attach to an already
    emitted group.  Parent ordering prevents a cycle by construction.  The
    normal pairwise validator remains authoritative for evidence strength,
    duplicate relations, and the resulting minimal proof tree.
    """
    if not isinstance(visual_groups, list) or not visual_groups:
        raise DetectionRegistrySchemaError("visual groups require proof-parent decisions")

    proofs: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()
    required_parent_fields = {
        "decision",
        "parent_group_id",
        "relationship",
        "evidence_facts",
        "decision_reason",
    }
    for group in visual_groups:
        if not isinstance(group, dict):
            raise DetectionRegistrySchemaError("visual group proof-parent is invalid")
        group_id = str(group.get("group_id") or "")
        parent = group.get("proof_parent")
        if (
            not group_id
            or not isinstance(parent, dict)
            or set(parent) not in (
                required_parent_fields,
                required_parent_fields | {"blocked_merge"},
            )
        ):
            raise DetectionRegistrySchemaError("visual group proof-parent is invalid")
        decision = parent["decision"]
        parent_group_id = str(parent["parent_group_id"] or "")
        relationship = parent["relationship"]
        evidence_facts = parent["evidence_facts"]
        decision_reason = str(parent["decision_reason"] or "").strip()
        if not decision_reason:
            raise DetectionRegistrySchemaError("visual group proof-parent requires a factual reason")

        if decision == "new_object_root":
            if (
                parent_group_id != PROOF_PARENT_ROOT_GROUP_ID
                or relationship != "new_object_root"
                or evidence_facts != []
            ):
                raise DetectionRegistrySchemaError("new-object root proof-parent is invalid")
            blocked_merge = parent.get("blocked_merge")
            if blocked_merge is not None:
                if (
                    not isinstance(blocked_merge, dict)
                    or set(blocked_merge) != {
                        "candidate_parent_group_id", "conflict_type", "observation",
                    }
                    or str(blocked_merge["candidate_parent_group_id"] or "") not in seen_group_ids
                    or blocked_merge["conflict_type"] != "dimension_conflict"
                    or not str(blocked_merge["observation"] or "").strip()
                ):
                    raise DetectionRegistrySchemaError("root blocked-merge evidence is invalid")
        elif decision == "attach_to_group":
            if (
                parent_group_id not in seen_group_ids
                or relationship not in PAIRWISE_EVIDENCE_RELATIONSHIPS
                or not isinstance(evidence_facts, list)
                or not evidence_facts
                or "blocked_merge" in parent
            ):
                raise DetectionRegistrySchemaError("attachment proof-parent is invalid")
            proofs.append({
                "group_id_a": min(group_id, parent_group_id),
                "group_id_b": max(group_id, parent_group_id),
                "relationship": relationship,
                "evidence_facts": evidence_facts,
                "commercial_inseparability": decision_reason,
            })
        else:
            raise DetectionRegistrySchemaError("visual group proof-parent decision is invalid")
        seen_group_ids.add(group_id)

    return validate_detection_pairwise_merge_proofs(
        proofs,
        visual_group_ids=seen_group_ids,
        page_count=page_count,
    )


def derive_detection_proof_components(
    proofs: list[dict[str, Any]],
    *,
    visual_group_ids: set[str],
) -> list[list[str]]:
    """Return canonical commercial candidates from a validated proof forest."""
    component_group_ids = visual_group_ids
    adjacency: dict[str, set[str]] = {
        group_id: set() for group_id in component_group_ids
    }
    for proof in proofs:
        if proof.get("relationship") not in MERGE_EVIDENCE_RELATIONSHIPS:
            continue
        group_id_a = str(proof["group_id_a"])
        group_id_b = str(proof["group_id_b"])
        adjacency[group_id_a].add(group_id_b)
        adjacency[group_id_b].add(group_id_a)

    components: list[list[str]] = []
    visited: set[str] = set()
    for group_id in sorted(component_group_ids):
        if group_id in visited:
            continue
        component: list[str] = []
        queue = deque([group_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            queue.extend(sorted(adjacency[current] - visited))
        components.append(sorted(component))
    return components


def validate_detection_shared_reference_group_ids(
    group_ids: object,
    *,
    proofs: list[dict[str, Any]],
    visual_group_ids: set[str],
) -> list[str]:
    """Validate non-commercial shared Evidence without oriented graph roles."""
    if (
        not isinstance(group_ids, list)
        or not all(isinstance(group_id, str) and group_id for group_id in group_ids)
        or group_ids != sorted(group_ids)
        or len(group_ids) != len(set(group_ids))
        or not set(group_ids).issubset(visual_group_ids)
    ):
        raise DetectionRegistrySchemaError("registry shared reference groups are invalid")
    shared_group_ids = set(group_ids)
    reference_degree = {group_id: 0 for group_id in shared_group_ids}
    merge_endpoint_group_ids: set[str] = set()
    for proof in proofs:
        group_id_a = str(proof["group_id_a"])
        group_id_b = str(proof["group_id_b"])
        if proof.get("relationship") == REFERENCE_RELATIONSHIP:
            if group_id_a in reference_degree:
                reference_degree[group_id_a] += 1
            if group_id_b in reference_degree:
                reference_degree[group_id_b] += 1
        elif proof.get("relationship") in MERGE_EVIDENCE_RELATIONSHIPS:
            merge_endpoint_group_ids.update({group_id_a, group_id_b})
    if (
        shared_group_ids.intersection(merge_endpoint_group_ids)
        or any(degree < 2 for degree in reference_degree.values())
    ):
        raise DetectionRegistrySchemaError(
            "shared reference evidence must connect multiple packages without a merge"
        )
    return group_ids


def validate_detection_standalone_package_group_ids(
    group_ids: object,
    *,
    components: list[list[str]],
    commercial_visual_group_ids: set[str],
) -> list[str]:
    """Require the compact explicit declaration of every singleton package.

    Graph connectivity already proves the complementary outcome: every
    commercial group not named here is part of a non-singleton proven component.
    The runtime derives and persists the full per-group ledger from that graph,
    avoiding a redundant model row for every member of a merged component.
    """
    component_group_ids = {
        group_id for component in components for group_id in component
    }
    if component_group_ids != commercial_visual_group_ids:
        raise DetectionRegistrySchemaError(
            "registry proof components do not cover commercial visual groups"
        )
    expected_group_ids = sorted(
        component[0] for component in components if len(component) == 1
    )
    if (
        not isinstance(group_ids, list)
        or not all(isinstance(group_id, str) and group_id for group_id in group_ids)
        or group_ids != sorted(group_ids)
        or len(group_ids) != len(set(group_ids))
        or group_ids != expected_group_ids
    ):
        raise DetectionRegistrySchemaError(
            "registry standalone package groups do not match proof graph",
            details={
                "expected_standalone_package_group_ids": expected_group_ids,
                "received_standalone_package_group_ids": group_ids,
            },
        )
    return group_ids


def derive_detection_package_decision_audit(
    components: list[list[str]],
    *,
    shared_reference_group_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Persist the complete package outcome deterministically from the graph."""
    decisions = [
        {
            "group_id": group_id,
            "package_disposition": (
                "part_of_proven_component"
                if len(component) > 1
                else "standalone_package"
            ),
            "component_anchor_group_id": component[0],
        }
        for component in components
        for group_id in component
    ]
    decisions.extend(
        {
            "group_id": group_id,
            "package_disposition": "shared_reference_evidence",
            "component_anchor_group_id": None,
        }
        for group_id in sorted(shared_reference_group_ids or [])
    )
    return decisions
