from __future__ import annotations
import copy
from collections import deque
from typing import Any

DETECTION_REGISTRY_JSON_SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["objects"],"properties":{"objects":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"],"properties":{"object_id":{"type":"string"},"transport_label":{"type":"string"},"quantity":{"type":"number","minimum":0},"quantity_explicit":{"type":"boolean"},"identity_pages":{"type":"array","items":{"type":"integer","minimum":1}},"estimation_evidence_pages":{"type":"array","items":{"type":"integer","minimum":1}},"visual_group_ids":{"type":"array","minItems":1,"items":{"type":"string"}},"visual_identity":{"type":"string"},"boundary_basis":{"type":"string"}}}}}}

PAIRWISE_MERGE_EVIDENCE_TYPES = frozenset({
    "explicit_document_relation",
    "matching_topology",
    "dimension_transform",
    "unique_geometry",
    "direct_shared_structure",
})
PAIRWISE_EVIDENCE_RELATIONSHIPS = frozenset({
    "same_object_view",
    "object_detail",
    "context_reference_link",
})
MERGE_EVIDENCE_RELATIONSHIPS = frozenset({
    "same_object_view",
    "object_detail",
})
CONTEXT_REFERENCE_RELATIONSHIP = "context_reference_link"
PACKAGE_DECISION_DISPOSITIONS = frozenset({
    "part_of_proven_component",
    "standalone_package",
})
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
            "from_group_id",
            "to_group_id",
            "relationship",
            "evidence_facts",
            "commercial_inseparability",
        ],
        "properties": {
            "from_group_id": {"type": "string"},
            "to_group_id": {"type": "string"},
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

DETECTION_PACKAGE_DECISION_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "group_id",
            "package_disposition",
            "component_anchor_group_id",
            "decision_reason",
        ],
        "properties": {
            "group_id": {"type": "string"},
            "package_disposition": {
                "type": "string",
                "enum": sorted(PACKAGE_DECISION_DISPOSITIONS),
            },
            "component_anchor_group_id": {"type": "string"},
            "decision_reason": {"type": "string"},
        },
    },
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
    context_source_group_ids: set[str] = set()
    context_target_group_ids: set[str] = set()
    merge_endpoint_group_ids: set[str] = set()
    required = {
        "from_group_id", "to_group_id", "relationship",
        "evidence_facts", "commercial_inseparability",
    }
    for proof in proofs:
        if not isinstance(proof, dict) or set(proof) != required:
            raise DetectionRegistrySchemaError("pairwise merge proof fields do not match contract")
        from_group_id = str(proof["from_group_id"] or "")
        to_group_id = str(proof["to_group_id"] or "")
        if (
            from_group_id == to_group_id
            or from_group_id not in visual_group_ids
            or to_group_id not in visual_group_ids
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
        if relationship == CONTEXT_REFERENCE_RELATIONSHIP:
            context_source_group_ids.add(from_group_id)
            context_target_group_ids.add(to_group_id)
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
        edge_key = tuple(sorted((from_group_id, to_group_id)))
        if edge_key in seen_edges:
            raise DetectionRegistrySchemaError("pairwise merge proofs repeat a relation")
        seen_edges.add(edge_key)
        if relationship in MERGE_EVIDENCE_RELATIONSHIPS:
            merge_endpoint_group_ids.update({from_group_id, to_group_id})
            adjacency[from_group_id].add(to_group_id)
            adjacency[to_group_id].add(from_group_id)

    if context_source_group_ids.intersection(context_target_group_ids):
        raise DetectionRegistrySchemaError(
            "context reference links cannot form a context chain"
        )
    if context_source_group_ids.intersection(merge_endpoint_group_ids):
        raise DetectionRegistrySchemaError(
            "context reference source cannot participate in a merge proof"
        )

    visited: set[str] = set()
    for group_id in sorted(visual_group_ids - context_source_group_ids):
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
                "from_group_id": group_id,
                "to_group_id": parent_group_id,
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
    context_source_group_ids = {
        str(proof["from_group_id"])
        for proof in proofs
        if proof.get("relationship") == CONTEXT_REFERENCE_RELATIONSHIP
    }
    component_group_ids = visual_group_ids - context_source_group_ids
    adjacency: dict[str, set[str]] = {
        group_id: set() for group_id in component_group_ids
    }
    for proof in proofs:
        if proof.get("relationship") not in MERGE_EVIDENCE_RELATIONSHIPS:
            continue
        from_group_id = str(proof["from_group_id"])
        to_group_id = str(proof["to_group_id"])
        adjacency[from_group_id].add(to_group_id)
        adjacency[to_group_id].add(from_group_id)

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


def validate_detection_package_decisions(
    decisions: object,
    *,
    components: list[list[str]],
    commercial_visual_group_ids: set[str],
) -> list[dict[str, Any]]:
    """Require an explicit, proof-consistent package outcome for every group.

    A classified commercial island has only two outcomes after graph validation:
    it belongs to a proven merge component or it is a singleton commercial
    package. Context-reference sources are deliberately outside this ledger,
    because they are shared Evidence rather than a commercial candidate.
    """
    required = {
        "group_id",
        "package_disposition",
        "component_anchor_group_id",
        "decision_reason",
    }
    if not isinstance(decisions, list) or not all(
        isinstance(item, dict) and set(item) == required for item in decisions
    ):
        raise DetectionRegistrySchemaError(
            "registry package decision fields do not match contract"
        )

    component_by_group_id = {
        group_id: component
        for component in components
        for group_id in component
    }
    if set(component_by_group_id) != commercial_visual_group_ids:
        raise DetectionRegistrySchemaError(
            "registry proof components do not cover commercial visual groups"
        )

    decisions_by_group_id: dict[str, dict[str, Any]] = {}
    for item in decisions:
        group_id = str(item["group_id"] or "")
        component = component_by_group_id.get(group_id)
        if group_id in decisions_by_group_id or component is None:
            raise DetectionRegistrySchemaError("registry package decision group is invalid")
        expected_disposition = (
            "part_of_proven_component"
            if len(component) > 1
            else "standalone_package"
        )
        if (
            item["package_disposition"] != expected_disposition
            or str(item["component_anchor_group_id"] or "") != component[0]
            or not str(item["decision_reason"] or "").strip()
        ):
            raise DetectionRegistrySchemaError(
                "registry package decision conflicts with proof graph",
                details={
                    "group_id": group_id,
                    "expected_disposition": expected_disposition,
                    "expected_component_anchor_group_id": component[0],
                },
            )
        decisions_by_group_id[group_id] = item

    if set(decisions_by_group_id) != commercial_visual_group_ids:
        raise DetectionRegistrySchemaError(
            "registry must decide every commercial visual group as component or standalone package",
            details={
                "missing_package_decision_group_ids": sorted(
                    commercial_visual_group_ids - set(decisions_by_group_id)
                ),
                "unexpected_package_decision_group_ids": sorted(
                    set(decisions_by_group_id) - commercial_visual_group_ids
                ),
            },
        )
    return decisions
