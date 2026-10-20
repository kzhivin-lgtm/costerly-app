from __future__ import annotations
import copy
from collections import deque
from itertools import combinations
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
    "supporting_relation",
})
MERGE_EVIDENCE_RELATIONSHIPS = frozenset({
    "same_object_view",
    "object_detail",
})
REFERENCE_RELATIONSHIP = "reference_link"
SUPPORTING_RELATIONSHIP = "supporting_relation"
DIMENSION_AXES = frozenset({"width", "height", "depth", "other"})
DIMENSION_SCOPES = frozenset({
    "overall", "subassembly", "component", "unknown",
})
DIMENSION_UNITS = frozenset({"mm", "cm", "m", "in", "ft", "unknown"})
PROOF_PARENT_DECISIONS = frozenset({
    "new_object_root",
    "attach_to_group",
})
PROOF_PARENT_ROOT_GROUP_ID = "ROOT"
PROOF_PARENT_RELATIONSHIPS = frozenset({
    "new_object_root",
    *MERGE_EVIDENCE_RELATIONSHIPS,
    REFERENCE_RELATIONSHIP,
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

DETECTION_DIMENSION_INVENTORY_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["group_id", "dimensions"],
        "properties": {
            "group_id": {"type": "string"},
            "dimensions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "dimension_id", "literal", "axis", "scope", "unit",
                    ],
                    "properties": {
                        "dimension_id": {"type": "string"},
                        "literal": {"type": "string"},
                        "axis": {"type": "string", "enum": sorted(DIMENSION_AXES)},
                        "scope": {"type": "string", "enum": sorted(DIMENSION_SCOPES)},
                        "unit": {"type": "string", "enum": sorted(DIMENSION_UNITS)},
                    },
                },
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
    """Keep literal, typed source dimensions once for every visual group.

    Detection never converts values or guesses units.  ``literal`` is exactly
    what was read from the drawing, while axis and scope make later local graph
    construction inspectable without asking the model to compare pairs again.
    """
    if not isinstance(inventory, list):
        raise DetectionRegistrySchemaError("dimension inventory must be a list")
    by_group_id: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if (
            not isinstance(row, dict)
            or set(row) != {"group_id", "dimensions"}
            or not isinstance(row.get("group_id"), str)
            or row["group_id"] not in visual_group_ids
            or row["group_id"] in by_group_id
            or not isinstance(row.get("dimensions"), list)
        ):
            raise DetectionRegistrySchemaError("dimension inventory is invalid")
        dimension_ids: set[str] = set()
        dimensions: list[dict[str, str]] = []
        for dimension in row["dimensions"]:
            if (
                not isinstance(dimension, dict)
                or set(dimension) != {
                    "dimension_id", "literal", "axis", "scope", "unit",
                }
                or not isinstance(dimension.get("dimension_id"), str)
                or not dimension["dimension_id"].strip()
                or not isinstance(dimension.get("literal"), str)
                or not dimension["literal"].strip()
                or dimension.get("axis") not in DIMENSION_AXES
                or dimension.get("scope") not in DIMENSION_SCOPES
                or dimension.get("unit") not in DIMENSION_UNITS
                or dimension["dimension_id"] in dimension_ids
            ):
                raise DetectionRegistrySchemaError("dimension inventory is invalid")
            dimension_ids.add(dimension["dimension_id"])
            dimensions.append({
                "dimension_id": dimension["dimension_id"].strip(),
                "literal": dimension["literal"].strip(),
                "axis": dimension["axis"],
                "scope": dimension["scope"],
                "unit": dimension["unit"],
            })
        by_group_id[row["group_id"]] = {
            "group_id": row["group_id"],
            "dimensions": dimensions,
        }
    if set(by_group_id) != visual_group_ids:
        raise DetectionRegistrySchemaError(
            "dimension inventory must account for every visual group exactly once"
        )
    return [by_group_id[group_id] for group_id in sorted(visual_group_ids)]


def normalize_detection_dimension_inventory_group_ids(
    inventory: object,
    group_id_mapping: dict[str, str],
) -> object:
    """Map provider-facing group IDs before local graph compilation."""
    if not isinstance(inventory, list):
        return inventory
    normalized = copy.deepcopy(inventory)
    for row in normalized:
        if isinstance(row, dict):
            raw_group_id = str(row.get("group_id") or "")
            row["group_id"] = group_id_mapping.get(raw_group_id, raw_group_id)
    return normalized


def _dimension_equality_key(dimension: dict[str, str]) -> tuple[str, str, str, str] | None:
    """Return an exact source comparison key, never a converted measurement."""
    if (
        dimension["axis"] == "other"
        or dimension["scope"] == "unknown"
    ):
        return None
    return (
        dimension["axis"],
        dimension["scope"],
        dimension["literal"].replace(",", ".").strip(),
        dimension["unit"],
    )


def _dimension_fact_observation(
    left: dict[str, str], right: dict[str, str],
) -> str:
    unit = "" if left["unit"] == "unknown" else f" {left['unit']}"
    return (
        f"{left['dimension_id']} and {right['dimension_id']} both state "
        f"{left['scope']} {left['axis']} {left['literal']}{unit} literally."
    )


def _hard_dimension_conflict(
    left_dimensions: list[dict[str, str]],
    right_dimensions: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Find direct, same-role overall conflicts without comparing details.

    Different values in a section and an elevation are normal.  A conflict is
    material only when two same-kind depictions each state incompatible overall
    dimensions on the same axis and unit.
    """
    conflicts: list[dict[str, str]] = []
    for left in left_dimensions:
        for right in right_dimensions:
            if (
                left["scope"] == right["scope"] == "overall"
                and left["axis"] == right["axis"] != "other"
                and left["unit"] == right["unit"]
                and left["literal"].replace(",", ".").strip()
                != right["literal"].replace(",", ".").strip()
            ):
                conflicts.append({
                    "dimension_id_a": left["dimension_id"],
                    "dimension_id_b": right["dimension_id"],
                    "axis": left["axis"],
                    "unit": left["unit"],
                    "literal_a": left["literal"],
                    "literal_b": right["literal"],
                })
    return conflicts


def _overall_dimension_transform_pairs(
    left_dimensions: list[dict[str, str]],
    right_dimensions: list[dict[str, str]],
) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Find literal cross-axis overall matches without unit conversion.

    A transform needs two independent cross-axis readings. One cross-axis
    number is merely a weak coincidence, while two readings with distinct
    source IDs establish a rotation or axis-swapped depiction deterministically.
    """
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    for left in left_dimensions:
        for right in right_dimensions:
            if (
                left["scope"] == right["scope"] == "overall"
                and left["axis"] != right["axis"]
                and left["axis"] != "other"
                and right["axis"] != "other"
                and left["unit"] == right["unit"]
                and left["literal"].replace(",", ".").strip()
                == right["literal"].replace(",", ".").strip()
            ):
                pairs.append((left, right))
    return pairs


def _dimension_transform_fact_observation(
    pairs: list[tuple[dict[str, str], dict[str, str]]],
) -> str:
    readings = "; ".join(
        f"{left['dimension_id']} {left['axis']} {left['literal']} maps to "
        f"{right['dimension_id']} {right['axis']} {right['literal']}"
        for left, right in pairs
    )
    return f"Two literal overall cross-axis readings establish a transform: {readings}."


def compile_detection_dimension_graph(
    inventory: list[dict[str, Any]],
    *,
    visual_groups: list[dict[str, Any]],
    page_drawing_codes: dict[int, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Build the positive graph locally from literal dimensions and sheet codes.

    The model supplies islands, their classification and literal dimensions.
    It never decides a package edge.  One exact matching source dimension is
    recorded as support.  Two distinct matching *overall* dimensions establish
    a merge.  A verified per-sheet DRAWING NAME code establishes an authored
    source-root tree for that sheet, unless two same-kind views directly
    contradict one another on an overall dimension.
    """
    dimensions_by_group_id = {
        str(row["group_id"]): list(row["dimensions"])
        for row in inventory
    }
    group_by_id = {
        str(group["group_id"]): group
        for group in visual_groups
    }
    group_ids = sorted(group_by_id)
    pairs_checked = len(group_ids) * (len(group_ids) - 1) // 2
    edge_inputs: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    conflict_pairs: set[tuple[str, str]] = set()
    source_root_conflict_exclusion_count = 0

    def edge_for(left_group_id: str, right_group_id: str) -> dict[str, Any]:
        pair = tuple(sorted((left_group_id, right_group_id)))
        return edge_inputs.setdefault(pair, {
            "group_id_a": pair[0],
            "group_id_b": pair[1],
            "facts": [],
            "root_code": None,
            "overall_equality_count": 0,
            "overall_transform_count": 0,
            "hard_conflict": False,
        })

    for group_id_a, group_id_b in combinations(group_ids, 2):
        group_a = group_by_id[group_id_a]
        group_b = group_by_id[group_id_b]
        dimensions_a = dimensions_by_group_id[group_id_a]
        dimensions_b = dimensions_by_group_id[group_id_b]
        same_kind = (
            str(group_a.get("representation_kind") or "")
            == str(group_b.get("representation_kind") or "")
        )
        pair_conflicts = _hard_dimension_conflict(dimensions_a, dimensions_b)
        if same_kind and pair_conflicts:
            conflict_pairs.add(tuple(sorted((group_id_a, group_id_b))))
            conflicts.append({
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "conflicts": pair_conflicts,
            })

        equality_pairs: list[tuple[dict[str, str], dict[str, str]]] = []
        for dimension_a in dimensions_a:
            key_a = _dimension_equality_key(dimension_a)
            if key_a is None:
                continue
            for dimension_b in dimensions_b:
                if key_a == _dimension_equality_key(dimension_b):
                    equality_pairs.append((dimension_a, dimension_b))
        transform_pairs = _overall_dimension_transform_pairs(
            dimensions_a, dimensions_b,
        )
        independent_transform_pairs = [
            pair for pair in transform_pairs
            if len({left["dimension_id"] for left, _ in transform_pairs}) >= 2
            and len({right["dimension_id"] for _, right in transform_pairs}) >= 2
        ]
        if equality_pairs or independent_transform_pairs:
            edge = edge_for(group_id_a, group_id_b)
            for dimension_a, dimension_b in equality_pairs:
                edge["facts"].append({
                    "evidence_type": "dimension_equality",
                    "evidence_pages": sorted({
                        int(group_a["page_number"]), int(group_b["page_number"]),
                    }),
                    "observation": _dimension_fact_observation(dimension_a, dimension_b),
                })
                if (
                    dimension_a["scope"] == dimension_b["scope"] == "overall"
                    and dimension_a["axis"] == dimension_b["axis"]
                ):
                    edge["overall_equality_count"] += 1
            if independent_transform_pairs:
                edge["facts"].append({
                    "evidence_type": "dimension_transform",
                    "evidence_pages": sorted({
                        int(group_a["page_number"]), int(group_b["page_number"]),
                    }),
                    "observation": _dimension_transform_fact_observation(
                        independent_transform_pairs,
                    ),
                })
                edge["overall_transform_count"] = len(independent_transform_pairs)
            if same_kind and pair_conflicts:
                edge["hard_conflict"] = True

    groups_by_page: dict[int, list[str]] = {}
    for group_id, group in group_by_id.items():
        groups_by_page.setdefault(int(group["page_number"]), []).append(group_id)
    for page_number, page_group_ids in groups_by_page.items():
        drawing_code = page_drawing_codes.get(page_number)
        if not drawing_code or len(page_group_ids) < 2:
            continue
        anchor_group_id = min(page_group_ids)
        for group_id in sorted(page_group_ids):
            if group_id == anchor_group_id:
                continue
            if tuple(sorted((anchor_group_id, group_id))) in conflict_pairs:
                source_root_conflict_exclusion_count += 1
                continue
            edge = edge_for(anchor_group_id, group_id)
            edge["root_code"] = drawing_code
            edge["facts"].append({
                "evidence_type": "explicit_document_relation",
                "evidence_pages": [page_number],
                "observation": (
                    f"Page {page_number} DRAWING NAME literally identifies "
                    f"the authored sheet as {drawing_code}."
                ),
            })

    relation_edges: list[dict[str, Any]] = []
    for pair in sorted(edge_inputs):
        edge = edge_inputs[pair]
        facts_by_key: dict[tuple[str, tuple[int, ...], str], dict[str, Any]] = {}
        for fact in edge["facts"]:
            facts_by_key[(
                fact["evidence_type"], tuple(fact["evidence_pages"]), fact["observation"],
            )] = fact
        facts = list(facts_by_key.values())
        if not facts:
            continue
        is_merge = (
            bool(edge["root_code"])
            or (
                (
                    edge["overall_equality_count"] >= 2
                    or edge["overall_transform_count"] >= 2
                )
                and not edge["hard_conflict"]
            )
        )
        relationship = "same_object_view" if is_merge else "supporting_relation"
        if edge["root_code"]:
            commercial_basis = (
                f"The literal per-sheet DRAWING NAME {edge['root_code']} establishes "
                "one authored source-root package; review remains required."
            )
        elif edge["overall_transform_count"] >= 2:
            commercial_basis = (
                "Two independent literal overall dimensions match after an "
                "axis swap, without conversion."
            )
        elif is_merge:
            commercial_basis = (
                "Two independent literal overall dimensions match without conversion."
            )
        else:
            commercial_basis = (
                "Literal matching dimension is retained as support only; it does not "
                "establish one commercial object."
            )
        relation_edges.append({
            "group_id_a": edge["group_id_a"],
            "group_id_b": edge["group_id_b"],
            "relationship": relationship,
            "evidence_facts": facts,
            "commercial_inseparability": commercial_basis,
        })

    audit = {
        "compiler_version": "v1",
        "pairs_checked": pairs_checked,
        "page_drawing_codes": {
            str(page_number): code
            for page_number, code in sorted(page_drawing_codes.items())
        },
        "dimension_equality_fact_count": sum(
            fact["evidence_type"] == "dimension_equality"
            for edge in relation_edges
            for fact in edge["evidence_facts"]
        ),
        "dimension_transform_fact_count": sum(
            fact["evidence_type"] == "dimension_transform"
            for edge in relation_edges
            for fact in edge["evidence_facts"]
        ),
        "source_root_merge_edge_count": sum(
            any(
                fact["evidence_type"] == "explicit_document_relation"
                for fact in edge["evidence_facts"]
            )
            for edge in relation_edges
            if edge["relationship"] == "same_object_view"
        ),
        "source_root_conflict_exclusion_count": source_root_conflict_exclusion_count,
        "dimension_conflicts": conflicts,
    }
    return relation_edges, conflicts, audit


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


def partition_detection_relation_edges(
    relation_edges: object,
    *,
    visual_group_ids: set[str],
    page_count: int,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Keep usable positive relations while isolating weak merge candidates.

    V4.40 records the complete *positive* relation graph rather than asking the
    provider to repeat a quadratic matrix of negative observations. A malformed
    or semantically weak candidate must remain inspectable, but it must not
    erase independently valid components or their singleton fallbacks.

    Returns normalized relation edges, accepted merge edges, reference links,
    and rejected-candidate audit rows, in that order. Structural errors inside
    an individual relation are isolated in the audit for the same reason.
    """
    if not isinstance(relation_edges, list):
        raise DetectionRegistrySchemaError("relation edges must be a list")

    required = {
        "group_id_a", "group_id_b", "relationship",
        "evidence_facts", "commercial_inseparability",
    }
    normalized_edges: list[dict[str, Any]] = []
    accepted_merge_edges: list[dict[str, Any]] = []
    reference_links: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for edge_index, edge in enumerate(relation_edges):
        rejected_base = {"edge_index": edge_index}
        if not isinstance(edge, dict) or set(edge) != required:
            rejected_candidates.append({
                **rejected_base,
                "rejection_stage": "structural",
                "reason": "relation fields do not match contract",
            })
            continue

        group_id_a = str(edge.get("group_id_a") or "")
        group_id_b = str(edge.get("group_id_b") or "")
        relationship = edge.get("relationship")
        if (
            group_id_a >= group_id_b
            or group_id_a not in visual_group_ids
            or group_id_b not in visual_group_ids
        ):
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": str(relationship or ""),
                "rejection_stage": "structural",
                "reason": "relation endpoints are not two ordered known groups",
            })
            continue
        if relationship not in PAIRWISE_EVIDENCE_RELATIONSHIPS:
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": str(relationship or ""),
                "rejection_stage": "structural",
                "reason": "relation type is invalid",
            })
            continue
        pair = (group_id_a, group_id_b)
        if pair in seen_pairs:
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": relationship,
                "rejection_stage": "structural",
                "reason": "duplicate relation for the same pair",
            })
            continue
        seen_pairs.add(pair)
        try:
            evidence_types, evidence_facts = _validate_pairwise_evidence_facts(
                edge["evidence_facts"], page_count=page_count
            )
        except DetectionRegistrySchemaError:
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": relationship,
                "rejection_stage": "structural",
                "reason": "relation evidence facts are invalid",
            })
            continue
        commercial_inseparability = str(
            edge.get("commercial_inseparability") or ""
        ).strip()
        if not commercial_inseparability:
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": relationship,
                "rejection_stage": "structural",
                "reason": "relation commercial basis is blank",
            })
            continue

        normalized = {
            "group_id_a": group_id_a,
            "group_id_b": group_id_b,
            "relationship": relationship,
            "evidence_facts": evidence_facts,
            "commercial_inseparability": commercial_inseparability,
        }
        normalized_edges.append(normalized)
        if relationship == REFERENCE_RELATIONSHIP:
            reference_links.append(normalized)
            continue
        if relationship == SUPPORTING_RELATIONSHIP:
            continue
        has_accepted_merge_basis = (
            "explicit_document_relation" in evidence_types
            or "dimension_transform" in evidence_types
            or (
                len(evidence_facts) >= 2
                and bool(set(evidence_types).intersection(
                    _NON_EXPLICIT_MERGE_SUPPORT_TYPES
                ))
            )
        )
        if not has_accepted_merge_basis:
            rejected_candidates.append({
                **rejected_base,
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "relationship": relationship,
                "rejection_stage": "merge_threshold",
                "reason": (
                    "merge needs an explicit document relation, an exact "
                    "dimension transform, or two independent evidence facts"
                ),
                "evidence_facts": evidence_facts,
                "commercial_inseparability": commercial_inseparability,
            })
            continue
        accepted_merge_edges.append(normalized)
    return (
        normalized_edges,
        accepted_merge_edges,
        reference_links,
        rejected_candidates,
    )


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
