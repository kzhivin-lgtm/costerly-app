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
PAIRWISE_RELATION_CRITERIA = (
    "explicit_document_relation",
    "dimension_equality",
    "dimension_transform",
    "matching_topology",
    "unique_geometry",
    "direct_shared_structure",
)
PAIRWISE_RELATION_STATE_CODES = frozenset({"Y", "N", "C", "U"})
PAIRWISE_RELATIONSHIP_CODES = {
    "N": "none",
    "P": "positive_non_tree_relation",
    "S": "same_object_view",
    "D": "object_detail",
    "R": "reference_link",
}
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

# V4.38 stores a compact, exact-once assessment for every pair of
# object-evidence groups.  The first character identifies the resulting
# relation (N none, S same object, D object detail, R reference).  The next
# six characters follow PAIRWISE_RELATION_CRITERIA and are Y positive, N
# checked-negative, C conflict, or U unreadable/not comparable.  Detailed
# observations are emitted only for Y facts below, avoiding a verbose negative
# prose row for every pair while preserving every negative decision.
DETECTION_PAIR_RELATION_STATES_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {"type": "string"},
}

DETECTION_PAIR_RELATION_FACTS_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "pair_index",
            "evidence_facts",
            "commercial_inseparability",
        ],
        "properties": {
            "pair_index": {"type": "integer", "minimum": 0},
            "evidence_facts": copy.deepcopy(
                DETECTION_PAIRWISE_MERGE_PROOF_JSON_SCHEMA["items"]["properties"][
                    "evidence_facts"
                ]
            ),
            "commercial_inseparability": {"type": "string"},
        },
    },
}

DETECTION_DIMENSION_INVENTORY_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["group_id", "dimension_readings"],
        "properties": {
            "group_id": {"type": "string"},
            "dimension_readings": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
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


def _ordered_pair_ids(group_ids: set[str]) -> list[tuple[str, str]]:
    ordered_group_ids = sorted(group_ids)
    return [
        (group_id_a, group_id_b)
        for index, group_id_a in enumerate(ordered_group_ids)
        for group_id_b in ordered_group_ids[index + 1:]
    ]


def _validate_pairwise_evidence_facts(
    evidence_facts: object,
    *,
    page_count: int,
) -> tuple[set[str], list[dict[str, Any]]]:
    if not isinstance(evidence_facts, list) or not evidence_facts:
        raise DetectionRegistrySchemaError("pairwise merge proof evidence facts are invalid")
    evidence_types: set[str] = set()
    evidence_fact_keys: set[tuple[str, tuple[int, ...], str]] = set()
    normalized: list[dict[str, Any]] = []
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
        normalized.append({
            "evidence_type": evidence_type,
            "evidence_pages": list(evidence_pages),
            "observation": observation,
        })
    return evidence_types, normalized


def validate_detection_dimension_inventory(
    inventory: object,
    *,
    visual_group_ids: set[str],
) -> list[dict[str, Any]]:
    """Keep every readable dimension once, including an explicit empty row."""
    if not isinstance(inventory, list):
        raise DetectionRegistrySchemaError("dimension inventory must be a list")
    by_group_id: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if (
            not isinstance(row, dict)
            or set(row) != {"group_id", "dimension_readings"}
            or not isinstance(row.get("group_id"), str)
            or row["group_id"] not in visual_group_ids
            or row["group_id"] in by_group_id
            or not isinstance(row.get("dimension_readings"), list)
            or not all(
                isinstance(reading, str) and reading.strip()
                for reading in row["dimension_readings"]
            )
        ):
            raise DetectionRegistrySchemaError("dimension inventory is invalid")
        readings = [reading.strip() for reading in row["dimension_readings"]]
        if len(readings) != len(set(readings)):
            raise DetectionRegistrySchemaError("dimension inventory is invalid")
        by_group_id[row["group_id"]] = {
            "group_id": row["group_id"],
            "dimension_readings": readings,
        }
    if set(by_group_id) != visual_group_ids:
        raise DetectionRegistrySchemaError(
            "dimension inventory must account for every visual group exactly once"
        )
    return [by_group_id[group_id] for group_id in sorted(visual_group_ids)]


def validate_detection_pair_relation_ledger(
    pair_relation_states: object,
    pair_relation_facts: object,
    *,
    object_evidence_group_ids: set[str],
    page_count: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate every pair and derive the positive proof graph deterministically.

    `pair_relation_states` is deliberately dense and compact.  The model cannot
    omit a difficult pair, while the persisted expanded audit remains readable.
    """
    expected_pairs = _ordered_pair_ids(object_evidence_group_ids)
    if (
        not isinstance(pair_relation_states, list)
        or len(pair_relation_states) != len(expected_pairs)
        or not all(isinstance(state, str) for state in pair_relation_states)
    ):
        raise DetectionRegistrySchemaError(
            "pair relation ledger must account for every object-evidence pair exactly once"
        )
    if not isinstance(pair_relation_facts, list):
        raise DetectionRegistrySchemaError("pair relation facts must be a list")

    facts_by_pair_index: dict[int, dict[str, Any]] = {}
    for row in pair_relation_facts:
        if (
            not isinstance(row, dict)
            or set(row) != {
                "pair_index", "evidence_facts", "commercial_inseparability",
            }
            or not isinstance(row.get("pair_index"), int)
            or not 0 <= row["pair_index"] < len(expected_pairs)
            or row["pair_index"] in facts_by_pair_index
            or not isinstance(row.get("commercial_inseparability"), str)
        ):
            raise DetectionRegistrySchemaError("pair relation facts are invalid")
        evidence_types, normalized_facts = _validate_pairwise_evidence_facts(
            row["evidence_facts"], page_count=page_count
        )
        facts_by_pair_index[row["pair_index"]] = {
            "evidence_types": evidence_types,
            "evidence_facts": normalized_facts,
            "commercial_inseparability": row["commercial_inseparability"].strip(),
        }

    proofs: list[dict[str, Any]] = []
    expanded_audit: list[dict[str, Any]] = []
    for pair_index, ((group_id_a, group_id_b), encoded_state) in enumerate(
        zip(expected_pairs, pair_relation_states, strict=True)
    ):
        if (
            len(encoded_state) != 1 + len(PAIRWISE_RELATION_CRITERIA)
            or encoded_state[0] not in PAIRWISE_RELATIONSHIP_CODES
            or any(
                criterion_state not in PAIRWISE_RELATION_STATE_CODES
                for criterion_state in encoded_state[1:]
            )
        ):
            raise DetectionRegistrySchemaError("pair relation state is invalid")
        relation = PAIRWISE_RELATIONSHIP_CODES[encoded_state[0]]
        criteria_states = dict(zip(
            PAIRWISE_RELATION_CRITERIA, encoded_state[1:], strict=True
        ))
        positive_criteria = {
            criterion
            for criterion, state in criteria_states.items()
            if state == "Y"
        }
        facts_row = facts_by_pair_index.get(pair_index)
        if bool(positive_criteria) != bool(facts_row):
            raise DetectionRegistrySchemaError(
                "pair relation facts must record every positive criterion and no negative-only pair"
            )
        evidence_facts: list[dict[str, Any]] = []
        commercial_inseparability = ""
        if facts_row is not None:
            evidence_types = facts_row["evidence_types"]
            if not positive_criteria.issubset(evidence_types) or not evidence_types.issubset(positive_criteria):
                raise DetectionRegistrySchemaError(
                    "pair relation facts do not match criterion states"
                )
            evidence_facts = facts_row["evidence_facts"]
            commercial_inseparability = facts_row["commercial_inseparability"]
        if relation in PAIRWISE_EVIDENCE_RELATIONSHIPS:
            if not positive_criteria or not commercial_inseparability:
                raise DetectionRegistrySchemaError(
                    "positive pair relation needs facts and commercial basis"
                )
            proofs.append({
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": relation,
                "evidence_facts": evidence_facts,
                "commercial_inseparability": commercial_inseparability,
            })
        elif relation == "positive_non_tree_relation" and not positive_criteria:
            raise DetectionRegistrySchemaError(
                "positive non-tree relation needs positive criteria"
            )
        expanded_audit.append({
            "pair_index": pair_index,
            "group_id_a": group_id_a,
            "group_id_b": group_id_b,
            "relationship": relation,
            "criterion_states": criteria_states,
            "evidence_facts": evidence_facts,
            "commercial_inseparability": commercial_inseparability,
        })
    return proofs, expanded_audit


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
        evidence_types, _ = _validate_pairwise_evidence_facts(
            proof["evidence_facts"], page_count=page_count
        )
        evidence_facts = proof["evidence_facts"]
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
    commercial_components: list[list[str]] | None = None,
) -> list[str]:
    """Validate shared Evidence against completed commercial packages.

    The first pass checks only the serialized IDs so the runtime can derive the
    commercial components. The final pass receives those components after the
    standalone-package audit and proves that a shared view reaches at least two
    distinct commercial packages, never merely two related visual groups.
    """
    if (
        not isinstance(group_ids, list)
        or not all(isinstance(group_id, str) and group_id for group_id in group_ids)
        or group_ids != sorted(group_ids)
        or len(group_ids) != len(set(group_ids))
        or not set(group_ids).issubset(visual_group_ids)
    ):
        raise DetectionRegistrySchemaError("registry shared reference groups are invalid")
    shared_group_ids = set(group_ids)
    merge_endpoint_group_ids = {
        group_id
        for proof in proofs
        if proof.get("relationship") in MERGE_EVIDENCE_RELATIONSHIPS
        for group_id in (str(proof["group_id_a"]), str(proof["group_id_b"]))
    }
    if shared_group_ids.intersection(merge_endpoint_group_ids):
        raise DetectionRegistrySchemaError(
            "shared reference evidence cannot participate in a merge proof",
            details={
                "shared_reference_merge_group_ids": sorted(
                    shared_group_ids.intersection(merge_endpoint_group_ids)
                ),
            },
        )
    if commercial_components is None:
        return group_ids

    package_anchor_by_group_id = {
        group_id: component[0]
        for component in commercial_components
        for group_id in component
    }
    linked_package_anchors = {group_id: set() for group_id in shared_group_ids}
    for proof in proofs:
        group_id_a = str(proof["group_id_a"])
        group_id_b = str(proof["group_id_b"])
        if proof.get("relationship") == REFERENCE_RELATIONSHIP:
            for shared_group_id, other_group_id in (
                (group_id_a, group_id_b),
                (group_id_b, group_id_a),
            ):
                if shared_group_id in linked_package_anchors:
                    package_anchor = package_anchor_by_group_id.get(other_group_id)
                    if package_anchor:
                        linked_package_anchors[shared_group_id].add(package_anchor)
    if any(
            len(package_anchors) < 2
            for package_anchors in linked_package_anchors.values()
    ):
        raise DetectionRegistrySchemaError(
            "shared reference evidence must connect at least two distinct proven packages without a merge",
            details={
                "shared_reference_package_anchors": {
                    group_id: sorted(package_anchors)
                    for group_id, package_anchors in linked_package_anchors.items()
                },
            },
        )
    return group_ids


def derive_detection_standalone_package_group_ids(
    components: list[list[str]],
) -> list[str]:
    """Derive singleton-package anchors from the accepted proof graph.

    A singleton is an absence of an accepted merge edge, not a second decision
    the model must repeat in a top-level list.  Deriving it here preserves the
    exact same audit fact while eliminating a frequent non-semantic failure.
    """
    return sorted(
        component[0] for component in components if len(component) == 1
    )


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
