from __future__ import annotations
import copy
import math
import re
from collections import deque
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Any

DETECTION_REGISTRY_JSON_SCHEMA: dict[str, Any] = {"type":"object","additionalProperties":False,"required":["objects"],"properties":{"objects":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["object_id","transport_label","quantity","quantity_explicit","identity_pages","estimation_evidence_pages","visual_group_ids","visual_identity","boundary_basis"],"properties":{"object_id":{"type":"string"},"transport_label":{"type":"string"},"quantity":{"type":"number","minimum":0},"quantity_explicit":{"type":"boolean"},"identity_pages":{"type":"array","items":{"type":"integer","minimum":1}},"estimation_evidence_pages":{"type":"array","items":{"type":"integer","minimum":1}},"visual_group_ids":{"type":"array","minItems":1,"items":{"type":"string"}},"visual_identity":{"type":"string"},"boundary_basis":{"type":"string"}}}}}}

PAIRWISE_MERGE_EVIDENCE_TYPES = frozenset({
    "explicit_document_relation",
    "dimension_equality",
    "visual_dimension_similarity",
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
ENVELOPE_CHAIN_AXES = frozenset({"horizontal", "vertical", "unknown"})
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
SEMANTIC_PAIRWISE_EVIDENCE_TYPES = frozenset({
    "explicit_document_relation", "dimension_transform", "matching_topology",
    "unique_geometry", "direct_shared_structure",
})
SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES = frozenset({
    *SEMANTIC_PAIRWISE_EVIDENCE_TYPES,
    "visual_dimension_similarity",
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
        "required": ["group_id", "envelope_chains"],
        "properties": {
            "group_id": {"type": "string"},
            "ocr_literal_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
            "envelope_chains": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "chain_id", "axis", "segments", "direct_total",
                        "source_fact_ids",
                    ],
                    "properties": {
                        "chain_id": {"type": "string"},
                        "axis": {
                            "type": "string",
                            "enum": sorted(ENVELOPE_CHAIN_AXES),
                        },
                        "segments": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "direct_total": {"type": "string"},
                        "normalized_bbox": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "top_left_x", "top_left_y",
                                "bottom_right_x", "bottom_right_y",
                            ],
                            "properties": {
                                "top_left_x": {"type": "number", "minimum": 0, "maximum": 1},
                                "top_left_y": {"type": "number", "minimum": 0, "maximum": 1},
                                "bottom_right_x": {"type": "number", "minimum": 0, "maximum": 1},
                                "bottom_right_y": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                        "source_fact_ids": {
                            "type": "array", "items": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}

# The Registry receives a coordinate-bearing census of literal
# dimension candidates from both authored PDF text and OCR.  It must account
# for every entry instead of silently dropping a readable value during its
# visual interpretation.
DETECTION_DIMENSION_CANDIDATE_DECISIONS_JSON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["candidate_ids", "group_id", "decision", "reason"],
        "properties": {
            "candidate_ids": {
                "type": "array", "minItems": 1, "items": {"type": "string"},
            },
            "group_id": {"type": "string"},
            "decision": {
                "type": "string",
                "enum": [
                    "outer_total",
                    "outer_segment",
                    "internal_dimension",
                    "not_a_dimension",
                    "outside_object_evidence",
                ],
            },
            "reason": {"type": "string"},
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
    source_fact_ids_by_group: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Keep every readable outer dimension chain for each axis.

    The model records visible direct totals and, only where necessary, the
    contiguous segments that span exactly the same outer line.  Runtime alone
    computes totals and pairwise equality.
    """
    if not isinstance(inventory, list):
        raise DetectionRegistrySchemaError("dimension inventory must be a list")
    by_group_id: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if (
            not isinstance(row, dict)
            or frozenset(row) not in {
                frozenset({"group_id", "envelope_chains"}),
                frozenset({"group_id", "ocr_literal_ids", "envelope_chains"}),
            }
            or not isinstance(row.get("group_id"), str)
            or row["group_id"] not in visual_group_ids
            or row["group_id"] in by_group_id
            or not isinstance(row.get("envelope_chains"), list)
            or (
                "ocr_literal_ids" in row
                and (
                    not isinstance(row["ocr_literal_ids"], list)
                    or not all(
                        isinstance(value, str) and value.strip()
                        for value in row["ocr_literal_ids"]
                    )
                    or len(row["ocr_literal_ids"]) != len(set(row["ocr_literal_ids"]))
                )
            )
        ):
            raise DetectionRegistrySchemaError("dimension inventory is invalid")
        chain_ids: set[str] = set()
        envelope_chains: list[dict[str, Any]] = []
        for chain in row["envelope_chains"]:
            required_chain_fields = {
                "chain_id", "axis", "segments", "direct_total",
            }
            if source_fact_ids_by_group is not None:
                required_chain_fields.add("source_fact_ids")
            allowed_chain_fields = required_chain_fields | {"normalized_bbox"}
            normalized_bbox = chain.get("normalized_bbox") if isinstance(chain, dict) else None
            if (
                not isinstance(chain, dict)
                or not required_chain_fields.issubset(chain)
                or not set(chain).issubset(allowed_chain_fields)
                or not isinstance(chain.get("chain_id"), str)
                or not chain["chain_id"].strip()
                or chain.get("axis") not in ENVELOPE_CHAIN_AXES
                or not isinstance(chain.get("segments"), list)
                or not isinstance(chain.get("direct_total"), str)
                or (
                    source_fact_ids_by_group is not None
                    and (
                        not isinstance(chain.get("source_fact_ids"), list)
                        or not all(
                            isinstance(value, str) and value.strip()
                            for value in chain["source_fact_ids"]
                        )
                        or len(chain["source_fact_ids"]) != len(set(chain["source_fact_ids"]))
                        or not set(chain["source_fact_ids"]).issubset(
                        set(source_fact_ids_by_group.get(row["group_id"], []))
                        )
                    )
                )
                or chain["chain_id"] in chain_ids
                or not all(
                    isinstance(value, str) and value.strip()
                    for value in chain["segments"]
                )
                or (
                    not chain["direct_total"].strip()
                    and len(chain["segments"]) < 2
                )
                or (
                    normalized_bbox is not None
                    and (
                        not isinstance(normalized_bbox, dict)
                        or set(normalized_bbox) != {
                            "top_left_x", "top_left_y",
                            "bottom_right_x", "bottom_right_y",
                        }
                        or not all(
                            isinstance(value, (int, float)) and 0 <= value <= 1
                            for value in normalized_bbox.values()
                        )
                        or normalized_bbox["bottom_right_x"] <= normalized_bbox["top_left_x"]
                        or normalized_bbox["bottom_right_y"] <= normalized_bbox["top_left_y"]
                    )
                )
            ):
                raise DetectionRegistrySchemaError("dimension inventory is invalid")
            chain_ids.add(chain["chain_id"])
            normalized_chain = {
                "chain_id": chain["chain_id"].strip(),
                "axis": chain["axis"],
                "segments": [value.strip() for value in chain["segments"]],
                "direct_total": chain["direct_total"].strip(),
                "source_fact_ids": [
                    value.strip() for value in chain.get("source_fact_ids") or []
                ],
            }
            if normalized_bbox is not None:
                normalized_chain["normalized_bbox"] = {
                    key: round(float(normalized_bbox[key]), 6)
                    for key in (
                        "top_left_x", "top_left_y",
                        "bottom_right_x", "bottom_right_y",
                    )
                }
            envelope_chains.append(normalized_chain)
        by_group_id[row["group_id"]] = {
            "group_id": row["group_id"],
            "ocr_literal_ids": list(row.get("ocr_literal_ids") or []),
            "envelope_chains": envelope_chains,
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


def normalize_empty_detection_envelope_chains(
    inventory: object,
) -> tuple[object, list[str]]:
    """Canonicalize a provider's empty chain as no readable chain.

    An empty synthetic chain has no factual content: it is the provider's
    representation of the existing ``envelope_chains: []`` state. Removing
    only that exact shape preserves every literal measurement and lets the
    remaining islands enter the deterministic equality comparison.
    """
    if not isinstance(inventory, list):
        return inventory, []
    normalized = copy.deepcopy(inventory)
    normalized_group_ids: set[str] = set()
    required_chain_key_sets = {
        frozenset({"chain_id", "axis", "segments", "direct_total"}),
        frozenset({
            "chain_id", "axis", "segments", "direct_total", "source_fact_ids",
        }),
    }
    for row in normalized:
        if not isinstance(row, dict) or not isinstance(row.get("envelope_chains"), list):
            continue
        retained_chains: list[object] = []
        for chain in row["envelope_chains"]:
            is_empty_chain = (
                isinstance(chain, dict)
                and frozenset(chain) in required_chain_key_sets
                and not str(chain.get("direct_total") or "").strip()
                and chain.get("segments") == []
                and not list(chain.get("source_fact_ids") or [])
            )
            if is_empty_chain:
                group_id = str(row.get("group_id") or "").strip()
                if group_id:
                    normalized_group_ids.add(group_id)
                continue
            retained_chains.append(chain)
        row["envelope_chains"] = retained_chains
    return normalized, sorted(normalized_group_ids)


_DIMENSION_LITERAL_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*$")
_ENVELOPE_EQUALITY_TOLERANCE = Decimal("0.02")
_DIMENSION_SIMILARITY_GRAPH_THRESHOLD = 0.55
_SAME_PAGE_DIMENSION_COHORT_MINIMUM = Decimal("150")
_SAME_PAGE_DIMENSION_COHORT_BONUS = 0.45
_DIMENSION_CONVERGENCE_MINIMUM = Decimal("20")
_SAME_PAGE_DIMENSION_CONVERGENCE_MATCHES = 3


def _decimal_literal(value: str) -> Decimal | None:
    match = _DIMENSION_LITERAL_RE.match(value)
    if not match:
        return None
    try:
        return Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None


def _dimension_chain_candidates(chain: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every literal and geometric-sum candidate without ranking one."""
    direct_total = _decimal_literal(chain["direct_total"])
    segments = [_decimal_literal(value) for value in chain["segments"]]
    if any(value is None for value in segments):
        return []
    segmented_total = sum(segments, Decimal("0")) if len(segments) >= 2 else None
    candidates: list[dict[str, Any]] = []
    if direct_total is not None:
        candidates.append({**chain, "total": direct_total, "source": "literal"})
    if segmented_total is not None:
        candidates.append({**chain, "total": segmented_total, "source": "segmented_sum"})
    return candidates


def _envelope_values_equal(left: Decimal, right: Decimal) -> tuple[bool, Decimal]:
    """Allow a two-percent drawing tolerance for rounded drawing dimensions."""
    if left <= 0 or right <= 0:
        return False, abs(left - right)
    difference = abs(left - right)
    return difference / max(left, right) <= _ENVELOPE_EQUALITY_TOLERANCE, difference


def _dimension_equality_observation(
    left: dict[str, Any], right: dict[str, Any], *, difference: Decimal,
    feature_weight: float, same_page_cohort: bool, matched_occurrence_count: int,
    left_occurrence_count: int, right_occurrence_count: int, edge_pattern: bool,
) -> str:
    comparison = "exactly matches" if not difference else (
        f"matches within 2% drawing tolerance (difference {difference})"
    )
    cohort_clause = (
        " Same-page repeated large-dimension cohort bonus applied."
        if same_page_cohort else ""
    )
    edge_pattern_clause = (
        " Repeated occurrences span opposite normalized Island bounds."
        if edge_pattern else ""
    )
    return (
        f"Dimension fingerprint value {left['total']} {comparison} value "
        f"{right['total']}; matched occurrences {matched_occurrence_count}/"
        f"{left_occurrence_count} and {matched_occurrence_count}/"
        f"{right_occurrence_count}; feature weight {feature_weight:.3f}."
        f"{cohort_clause}{edge_pattern_clause}"
    )


def _dimension_magnitude_weight(value: Decimal) -> float:
    """Reduce the influence of common drawing increments and tiny dimensions."""
    if value < 20:
        return 0.02
    if value < 50:
        return 0.12
    if value < 100:
        return 0.25
    if value < 200:
        return 0.45
    if value < 1_000:
        return 0.80
    return 1.0


def _dimension_specificity(*, document_group_count: int, value_group_count: int) -> float:
    """Discount ubiquitous increments without making them disappear entirely."""
    _ = document_group_count
    if value_group_count < 2:
        return 0.0
    return 1.0 / math.sqrt(value_group_count)


def _normalized_bbox_center(chain: dict[str, Any]) -> tuple[float, float] | None:
    bbox = chain.get("normalized_bbox")
    if not isinstance(bbox, dict):
        return None
    try:
        return (
            (float(bbox["top_left_x"]) + float(bbox["bottom_right_x"])) / 2,
            (float(bbox["top_left_y"]) + float(bbox["bottom_right_y"])) / 2,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _matched_occurrences_form_edge_pattern(
    occurrences: list[tuple[dict[str, Any], dict[str, Any]]],
) -> bool:
    """Detect the same repeated value at opposite bounds of both Islands.

    This is a bounded topology bonus, not an object-merge decision. It only
    applies where at least two independently printed occurrences match and the
    occurrences span substantially apart left/right or top/bottom in each
    Island. Absolute page edges are intentionally not required because an
    Island bbox can include attached annotations or white margin.
    """
    if len(occurrences) < 2:
        return False
    centres = [(_normalized_bbox_center(left), _normalized_bbox_center(right))
               for left, right in occurrences]
    if any(left is None or right is None for left, right in centres):
        return False
    for axis in (0, 1):
        left_positions = [left[axis] for left, _ in centres if left is not None]
        right_positions = [right[axis] for _, right in centres if right is not None]
        if (
            max(left_positions) - min(left_positions) >= 0.45
            and max(right_positions) - min(right_positions) >= 0.45
        ):
            return True
    return False


def _occurrence_feature_weight(
    *,
    value: Decimal,
    value_group_count: int,
    tolerance_factor: float,
    same_page_cohort: bool,
) -> float:
    """Weight one literal match before multiplicity and topology are applied."""
    magnitude = _dimension_magnitude_weight(value)
    specificity = _dimension_specificity(
        document_group_count=0, value_group_count=value_group_count,
    )
    # A ubiquitous dimension remains weak supporting evidence. It is not erased,
    # because repeated independent occurrences can still form a useful pattern.
    weight = magnitude * (0.30 + 0.70 * specificity) * tolerance_factor
    if same_page_cohort:
        weight += _SAME_PAGE_DIMENSION_COHORT_BONUS * magnitude
    return min(0.95, round(weight, 6))


def _accumulate_independent_feature_weights(weights: list[float]) -> float:
    """Noisy-OR accumulation: each independent feature raises bounded confidence."""
    remaining = 1.0
    for weight in weights:
        remaining *= 1.0 - min(0.95, max(0.0, weight))
    return round(1.0 - remaining, 6)


def compile_detection_dimension_graph(
    inventory: list[dict[str, Any]],
    *,
    visual_groups: list[dict[str, Any]],
    page_drawing_codes: dict[int, str],
    document_dimension_unit: str = "unknown",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Compile Dimension Fingerprints into a Weighted Similarity graph.

    The result is an undirected supporting-evidence graph. Each literal
    occurrence is compared once, with its source provenance, multiplicity and
    normalized Island position preserved. Dimensions alone never merge a
    package into a commercial object.
    """
    candidates_by_group_id = {
        str(row["group_id"]): [
            candidate
            for chain in row["envelope_chains"]
            for candidate in _dimension_chain_candidates(chain)
        ]
        for row in inventory
    }
    group_by_id = {
        str(group["group_id"]): group
        for group in visual_groups
    }
    group_ids = sorted(group_by_id)
    pairs_checked = len(group_ids) * (len(group_ids) - 1) // 2
    edge_inputs: dict[tuple[str, str], dict[str, Any]] = {}
    similarity_candidates: list[dict[str, Any]] = []
    value_group_counts: dict[Decimal, int] = {}
    value_groups_by_page: dict[tuple[int, Decimal], set[str]] = {}
    for group_id, candidates in candidates_by_group_id.items():
        page_number = int(group_by_id[group_id]["page_number"])
        for value in {candidate["total"] for candidate in candidates}:
            value_group_counts[value] = value_group_counts.get(value, 0) + 1
            value_groups_by_page.setdefault((page_number, value), set()).add(group_id)
    invalid_chain_count = sum(
        sum(not _dimension_chain_candidates(chain) for chain in row["envelope_chains"])
        for row in inventory
    )

    def edge_for(left_group_id: str, right_group_id: str) -> dict[str, Any]:
        pair = tuple(sorted((left_group_id, right_group_id)))
        return edge_inputs.setdefault(pair, {
            "group_id_a": pair[0],
            "group_id_b": pair[1],
            "facts": [],
            "feature_pairs": [],
        })

    for group_id_a, group_id_b in combinations(group_ids, 2):
        candidate_matches: list[dict[str, Any]] = []
        for chain_a in candidates_by_group_id[group_id_a]:
            for chain_b in candidates_by_group_id[group_id_b]:
                equal, difference = _envelope_values_equal(
                    chain_a["total"], chain_b["total"],
                )
                if not equal:
                    continue
                frequency = min(
                    value_group_counts.get(chain_a["total"], 0),
                    value_group_counts.get(chain_b["total"], 0),
                )
                tolerance_factor = float(
                    1 - difference / max(chain_a["total"], chain_b["total"])
                )
                same_page_cohort = (
                    chain_a["total"] == chain_b["total"]
                    and chain_a["total"] >= _SAME_PAGE_DIMENSION_COHORT_MINIMUM
                    and group_by_id[group_id_a]["page_number"]
                    == group_by_id[group_id_b]["page_number"]
                    and len(value_groups_by_page.get(
                        (int(group_by_id[group_id_a]["page_number"]), chain_a["total"]),
                        set(),
                    )) >= 2
                )
                feature_weight = _occurrence_feature_weight(
                    value=min(chain_a["total"], chain_b["total"]),
                    value_group_count=frequency,
                    tolerance_factor=tolerance_factor,
                    same_page_cohort=same_page_cohort,
                )
                if feature_weight > 0:
                    candidate_matches.append({
                        "base_weight": feature_weight,
                        "chain_a": chain_a,
                        "chain_b": chain_b,
                        "difference": difference,
                        "same_page_cohort": same_page_cohort,
                    })
        if candidate_matches:
            candidate_matches.sort(
                key=lambda item: (
                    0 if item["difference"] == 0 else 1,
                    item["difference"], -item["base_weight"],
                    item["chain_a"]["chain_id"], item["chain_b"]["chain_id"],
                )
            )
            selected_matches: list[dict[str, Any]] = []
            used_a: set[str] = set()
            used_b: set[str] = set()
            for match in candidate_matches:
                chain_a = match["chain_a"]
                chain_b = match["chain_b"]
                if chain_a["chain_id"] in used_a or chain_b["chain_id"] in used_b:
                    continue
                selected_matches.append(match)
                used_a.add(chain_a["chain_id"])
                used_b.add(chain_b["chain_id"])
            matches_by_value_pair: dict[tuple[Decimal, Decimal], list[dict[str, Any]]] = {}
            for match in selected_matches:
                key = (match["chain_a"]["total"], match["chain_b"]["total"])
                matches_by_value_pair.setdefault(key, []).append(match)

            feature_rows: list[dict[str, Any]] = []
            for value_pair, matches in sorted(matches_by_value_pair.items()):
                left_value, right_value = value_pair
                left_occurrence_count = sum(
                    chain["total"] == left_value
                    for chain in candidates_by_group_id[group_id_a]
                )
                right_occurrence_count = sum(
                    chain["total"] == right_value
                    for chain in candidates_by_group_id[group_id_b]
                )
                matched_occurrence_count = len(matches)
                base_weight = max(match["base_weight"] for match in matches)
                occurrence_weight = 1 - (1 - base_weight) ** matched_occurrence_count
                coverage = matched_occurrence_count / max(
                    left_occurrence_count, right_occurrence_count,
                )
                edge_pattern = (
                    min(left_value, right_value) >= Decimal("20")
                    and _matched_occurrences_form_edge_pattern([
                        (match["chain_a"], match["chain_b"])
                        for match in matches
                    ])
                )
                feature_weight = occurrence_weight * (0.70 + 0.30 * coverage)
                if edge_pattern:
                    feature_weight += 0.15
                feature_weight = round(min(0.95, feature_weight), 6)
                feature_rows.append({
                    "left": matches[0]["chain_a"],
                    "right": matches[0]["chain_b"],
                    "difference": min(match["difference"] for match in matches),
                    "same_page_cohort": any(
                        match["same_page_cohort"] for match in matches
                    ),
                    "matched_occurrence_count": matched_occurrence_count,
                    "left_occurrence_count": left_occurrence_count,
                    "right_occurrence_count": right_occurrence_count,
                    "edge_pattern": edge_pattern,
                    "feature_weight": feature_weight,
                    "value_pair": [str(left_value), str(right_value)],
                })
            similarity_score = _accumulate_independent_feature_weights([
                row["feature_weight"] for row in feature_rows
            ])
            same_page = (
                group_by_id[group_id_a]["page_number"]
                == group_by_id[group_id_b]["page_number"]
            )
            # A single common dimension is weak. Several distinct dimensions
            # agreeing on one drawing sheet are independent corroboration,
            # even when each literal is common across the document. Keep this
            # as a supporting relation only: object/package assembly remains a
            # later model decision based on all evidence channels.
            convergent_dimension_values = sorted({
                str(feature["left"]["total"])
                for feature in feature_rows
                if min(feature["left"]["total"], feature["right"]["total"])
                >= _DIMENSION_CONVERGENCE_MINIMUM
            }, key=Decimal)
            convergence_support = (
                same_page
                and len(convergent_dimension_values)
                >= _SAME_PAGE_DIMENSION_CONVERGENCE_MATCHES
            )
            passes_graph_threshold = (
                similarity_score >= _DIMENSION_SIMILARITY_GRAPH_THRESHOLD
                or convergence_support
            )
            similarity_candidates.append({
                "group_id_a": group_id_a,
                "group_id_b": group_id_b,
                "score": similarity_score,
                "feature_count": len(feature_rows),
                "matched_occurrence_count": len(selected_matches),
                "features": [{
                    key: value for key, value in row.items()
                    if key not in {"left", "right", "difference", "same_page_cohort"}
                } for row in feature_rows],
                "distinct_convergent_dimension_values": convergent_dimension_values,
                "same_page_dimension_convergence": convergence_support,
                "passes_graph_threshold": passes_graph_threshold,
            })
            # Weak similarities remain visible in the audit, but cannot become
            # a graph relation that later influences package assembly.
            if not passes_graph_threshold:
                continue
            edge = edge_for(group_id_a, group_id_b)
            page_numbers = sorted({
                int(group_by_id[group_id_a]["page_number"]),
                int(group_by_id[group_id_b]["page_number"]),
            })
            for feature in feature_rows:
                edge["facts"].append({
                    "evidence_type": "dimension_equality",
                    "evidence_pages": page_numbers,
                    "observation": _dimension_equality_observation(
                        feature["left"], feature["right"],
                        difference=feature["difference"],
                        feature_weight=feature["feature_weight"],
                        same_page_cohort=feature["same_page_cohort"],
                        matched_occurrence_count=feature["matched_occurrence_count"],
                        left_occurrence_count=feature["left_occurrence_count"],
                        right_occurrence_count=feature["right_occurrence_count"],
                        edge_pattern=feature["edge_pattern"],
                    ),
                })
                edge["feature_pairs"].append(feature)
            edge["dimension_similarity_score"] = similarity_score

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
        relationship = "supporting_relation"
        commercial_basis = (
            "Dimension-chain similarity is supporting evidence only and does not "
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
        "compiler_version": "v4_56_occurrence_aware_dimension_fingerprint_weighted_similarity",
        "pairs_checked": pairs_checked,
        "document_dimension_unit": document_dimension_unit,
        "page_drawing_codes": {
            str(page_number): code
            for page_number, code in sorted(page_drawing_codes.items())
        },
        "dimension_fingerprint_value_count": sum(
            len(candidates) for candidates in candidates_by_group_id.values()
        ),
        "dimension_fingerprint_occurrence_count": sum(
            len(candidates) for candidates in candidates_by_group_id.values()
        ),
        "invalid_envelope_chain_count": invalid_chain_count,
        "dimension_equality_fact_count": sum(
            fact["evidence_type"] == "dimension_equality"
            for edge in relation_edges
            for fact in edge["evidence_facts"]
        ),
        "dimension_transform_fact_count": 0,
        "source_root_merge_edge_count": 0,
        "source_root_conflict_exclusion_count": 0,
        "dimension_conflicts": [],
        "source_codes_used_for_graph": False,
        "near_envelope_equality_fact_count": sum(
            "2% drawing tolerance" in fact["observation"]
            for edge in relation_edges
            for fact in edge["evidence_facts"]
        ),
        "dimension_similarity_edges": [
            {
                "group_id_a": edge["group_id_a"],
                "group_id_b": edge["group_id_b"],
                "score": edge["dimension_similarity_score"],
                "feature_count": len(edge["feature_pairs"]),
                "matched_occurrence_count": sum(
                    feature["matched_occurrence_count"]
                    for feature in edge["feature_pairs"]
                ),
            }
            for edge in sorted(edge_inputs.values(), key=lambda edge: (
                edge["group_id_a"], edge["group_id_b"],
            ))
        ],
        "dimension_similarity_candidates": sorted(
            similarity_candidates,
            key=lambda candidate: (
                candidate["group_id_a"], candidate["group_id_b"],
            ),
        ),
        "dimension_similarity_graph_threshold": _DIMENSION_SIMILARITY_GRAPH_THRESHOLD,
        "dimension_equality_tolerance_percent": float(
            _ENVELOPE_EQUALITY_TOLERANCE * 100
        ),
        "same_page_dimension_convergence_minimum": (
            _SAME_PAGE_DIMENSION_CONVERGENCE_MATCHES
        ),
    }
    return relation_edges, [], audit


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


def derive_detection_dimension_package_candidates(
    relation_edges: list[dict[str, Any]],
    *,
    visual_group_ids: set[str],
) -> list[list[str]]:
    """Return provisional components from Dimension Graph support edges.

    These are investigation candidates only. They deliberately do not change
    commercial object ownership, which remains reserved for the later graph
    containing all evidence types.
    """
    adjacency: dict[str, set[str]] = {
        group_id: set() for group_id in visual_group_ids
    }
    for edge in relation_edges:
        if edge.get("relationship") != "supporting_relation":
            continue
        group_id_a = str(edge.get("group_id_a") or "")
        group_id_b = str(edge.get("group_id_b") or "")
        if group_id_a not in adjacency or group_id_b not in adjacency:
            continue
        adjacency[group_id_a].add(group_id_b)
        adjacency[group_id_b].add(group_id_a)

    components: list[list[str]] = []
    visited: set[str] = set()
    for group_id in sorted(visual_group_ids):
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


def compile_detection_semantic_pairwise_ledger(
    ledger: object,
    *,
    visual_groups: list[dict[str, Any]],
    page_count: int,
    page_drawing_codes: dict[int, str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate every same-page semantic comparison and emit positive edges."""
    if not isinstance(ledger, list):
        raise DetectionRegistrySchemaError("semantic pairwise ledger is invalid")
    page_by_group = {
        str(group.get("group_id") or ""): int(group["page_number"])
        for group in visual_groups if isinstance(group, dict)
    }
    expected_pairs = {
        (left, right)
        for left, right in combinations(sorted(page_by_group), 2)
        if page_by_group[left] == page_by_group[right]
    }
    rows_by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    ignored_pairs: list[dict[str, str]] = []
    page_drawing_codes = page_drawing_codes or {}
    for row in ledger:
        if not isinstance(row, dict) or set(row) != {"group_id_a", "group_id_b", "checks"}:
            raise DetectionRegistrySchemaError("semantic pairwise ledger is invalid")
        pair = tuple(sorted((
            str(row["group_id_a"] or ""), str(row["group_id_b"] or ""),
        )))
        if pair not in expected_pairs:
            # The Registry occasionally compares an adjacent cross-page pair
            # even though the contract asks only for same-page pairs. It has
            # no graph effect and must not invalidate an otherwise complete
            # ledger. Preserve its omission explicitly for run diagnostics.
            ignored_pairs.append({
                "group_id_a": pair[0], "group_id_b": pair[1],
                "reason": "not_a_retained_same_page_pair",
            })
            continue
        if pair in rows_by_pair or not isinstance(row["checks"], list):
            raise DetectionRegistrySchemaError("semantic pairwise ledger pairs are invalid")
        checks: dict[str, dict[str, Any]] = {}
        for check in row["checks"]:
            if not isinstance(check, dict) or set(check) != {"evidence_type", "state", "observation"}:
                raise DetectionRegistrySchemaError("semantic pairwise ledger checks are invalid")
            evidence_type = str(check["evidence_type"] or "")
            state = str(check["state"] or "")
            observation = str(check["observation"] or "").strip()
            if (
                evidence_type not in SEMANTIC_PAIRWISE_EVIDENCE_TYPES
                or evidence_type in checks
                or state not in {"present", "absent", "unknown"}
                # A negative conclusion may explain why the evidence type is
                # absent. It is audit reasoning, not a graph fact. `unknown`
                # must stay blank because no factual conclusion was reached.
                or (state == "present" and not observation)
                or (state == "unknown" and observation)
            ):
                raise DetectionRegistrySchemaError("semantic pairwise ledger checks are invalid")
            checks[evidence_type] = {
                "evidence_type": evidence_type, "state": state,
                "observation": observation,
            }
        if set(checks) != SEMANTIC_PAIRWISE_EVIDENCE_TYPES:
            raise DetectionRegistrySchemaError("semantic pairwise ledger must check every evidence type")
        rows_by_pair[pair] = {"group_id_a": pair[0], "group_id_b": pair[1], "checks": checks}
    # A truncated response may omit the last comparisons. Preserve the fact
    # that Registry did not assess them, but do not reject the RFQ or invent a
    # semantic relation. Runtime inserts explicit `unknown` checks, so every
    # graph pair remains inspectable and safely edge-free.
    unassessed_pairs = sorted(expected_pairs - set(rows_by_pair))
    for pair in unassessed_pairs:
        rows_by_pair[pair] = {
            "group_id_a": pair[0],
            "group_id_b": pair[1],
            "checks": {
                evidence_type: {
                    "evidence_type": evidence_type,
                    "state": "unknown",
                    "observation": "",
                }
                for evidence_type in SEMANTIC_PAIRWISE_EVIDENCE_TYPES
            },
        }

    edges: list[dict[str, Any]] = []
    demoted_document_relations: list[dict[str, str]] = []
    for pair in sorted(rows_by_pair):
        row = rows_by_pair[pair]
        page_number = page_by_group[pair[0]]
        source_page_code = re.sub(
            r"[^A-Z0-9]", "", str(page_drawing_codes.get(page_number) or "").upper()
        )
        facts = []
        for check in row["checks"].values():
            if check["state"] != "present":
                continue
            if check["evidence_type"] == "explicit_document_relation":
                observation_code = re.sub(
                    r"[^A-Z0-9]", "", check["observation"].upper()
                )
                if not source_page_code or source_page_code not in observation_code:
                    demoted_document_relations.append({
                        "group_id_a": pair[0], "group_id_b": pair[1],
                        "page_number": str(page_number),
                        "source_page_code": source_page_code,
                        "observation": check["observation"],
                        "reason": "explicit_document_relation_requires_literal_page_code",
                    })
                    continue
            facts.append({
                "evidence_type": check["evidence_type"],
                "evidence_pages": [page_number],
                "observation": check["observation"],
            })
        if facts:
            edges.append({
                "group_id_a": pair[0], "group_id_b": pair[1],
                "relationship": SUPPORTING_RELATIONSHIP,
                "evidence_facts": facts,
                "commercial_inseparability": "Semantic evidence is supporting only until full package review.",
            })
    audit = {
        "same_page_pair_count": len(expected_pairs),
        "checks_per_pair": len(SEMANTIC_PAIRWISE_EVIDENCE_TYPES),
        "positive_semantic_edge_count": len(edges),
        "ignored_non_same_page_pair_count": len(ignored_pairs),
        "ignored_non_same_page_pairs": ignored_pairs,
        "unassessed_same_page_pair_count": len(unassessed_pairs),
        "unassessed_same_page_pairs": [
            {"group_id_a": pair[0], "group_id_b": pair[1]}
            for pair in unassessed_pairs
        ],
        "demoted_explicit_document_relation_count": len(demoted_document_relations),
        "demoted_explicit_document_relations": demoted_document_relations,
        "ledger": [
            {"group_id_a": row["group_id_a"], "group_id_b": row["group_id_b"],
             "checks": [row["checks"][kind] for kind in sorted(row["checks"])]}
            for _, row in sorted(rows_by_pair.items())
        ],
    }
    return edges, audit


def merge_detection_relation_edges(*edge_sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union typed facts from independent graph channels into one edge per pair."""
    merged: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for edges in edge_sets:
        for edge in edges:
            pair = (str(edge["group_id_a"]), str(edge["group_id_b"]))
            merged.setdefault(pair, []).extend(edge.get("evidence_facts") or [])
    return [{
        "group_id_a": pair[0], "group_id_b": pair[1],
        "relationship": SUPPORTING_RELATIONSHIP,
        "evidence_facts": facts,
        "commercial_inseparability": "Typed graph evidence is supporting only until full package review.",
    } for pair, facts in sorted(merged.items())]


_V5_GENERIC_SEMANTIC_RE = re.compile(
    r"\b(same page|both elevations?|same room|adjacent|same material|same colour|"
    r"same color|same plinth|looks similar|visual impression|same h\s*=?\s*60)\b",
    re.IGNORECASE,
)
_V5_HARD_GENERIC_SEMANTIC_RE = re.compile(r"\bsame h\s*=?\s*60\b", re.IGNORECASE)
_V5_NON_SHARED_STRUCTURE_RE = re.compile(
    r"\b(same|identical|matching)\s+(material|profile|hardware|specification|construction)|"
    r"\b(material|hardware)\s+specifications?\b|"
    r"\b(structural|construction)\s+(principle|methodology|method|system|type)\b|"
    r"\bframe\s+(principle|methodology|method|system|type)\b",
    re.IGNORECASE,
)
_V5_STRUCTURAL_WITNESS_KINDS = frozenset({
    "endpoint_complete_view_contains_partial",
    "third_view_shows_both",
})
_V5_CONCRETE_SEMANTIC_RE = re.compile(
    r"\d|\b(carcass|bay|door|drawer|shelf|panel|track|frame|"
    r"compartment|sequence|component|dimension|reference|callout|boundary)\b",
    re.IGNORECASE,
)
_V5_SEMANTIC_POINTS = {
    "dimension_transform": 35,
    "visual_dimension_similarity": 45,
    "matching_topology": 30,
    "unique_geometry": 30,
    "direct_shared_structure": 20,
}
_V5_BRACKETED_SOURCE_FACT_ID_RE = re.compile(r"^\[([^\[\]]+)\]$")


def _canonical_detection_v5_source_fact_ids(
    cited_ids: list[str],
    *,
    known_source_ids: set[str],
) -> tuple[list[str], list[dict[str, str]]]:
    """Canonicalize only a known source ID wrapped once for display.

    The membership handoff renders OCR IDs as ``[SF00001]`` for readability.
    A Registry response may repeat that wrapper. Accept it only when the
    unwrapped token is already a known source ID; never guess or rewrite an
    otherwise unknown citation.
    """
    canonical_ids: list[str] = []
    normalizations: list[dict[str, str]] = []
    for cited_id in cited_ids:
        canonical_id = cited_id
        match = _V5_BRACKETED_SOURCE_FACT_ID_RE.fullmatch(cited_id)
        if cited_id not in known_source_ids and match:
            unwrapped = match.group(1)
            if unwrapped in known_source_ids:
                canonical_id = unwrapped
                normalizations.append({
                    "original_source_fact_id": cited_id,
                    "canonical_source_fact_id": canonical_id,
                    "reason": "known_source_id_display_wrapper",
                })
        canonical_ids.append(canonical_id)
    return sorted(set(canonical_ids)), normalizations


def compile_detection_v5_object_hypotheses(
    hypotheses: object,
    *,
    visual_groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep non-overlapping multi-View Registry hypotheses as a semantic search boundary."""
    object_group_ids = {
        str(group.get("group_id") or "") for group in visual_groups
        if group.get("evidence_class") == "object_evidence"
    }
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    claimed: set[str] = set()
    if not isinstance(hypotheses, list):
        return [], {"accepted": [], "rejected": [{"reason": "object_hypotheses_not_list"}]}
    for index, raw in enumerate(hypotheses):
        if not isinstance(raw, dict) or set(raw) != {"group_ids", "hypothesis_reason", "evidence"}:
            rejected.append({"index": index, "reason": "object_hypothesis_fields_invalid"})
            continue
        group_ids = sorted({str(group_id or "") for group_id in raw["group_ids"]}) if isinstance(raw["group_ids"], list) else []
        reason = str(raw["hypothesis_reason"] or "").strip()
        evidence = raw["evidence"] if isinstance(raw["evidence"], list) else []
        if len(group_ids) < 2 or not reason or not evidence or not set(group_ids).issubset(object_group_ids):
            rejected.append({"index": index, "reason": "object_hypothesis_members_invalid"})
            continue
        overlap = sorted(set(group_ids).intersection(claimed))
        if overlap:
            rejected.append({"index": index, "reason": "object_hypothesis_overlaps", "group_ids": overlap})
            continue
        claimed.update(group_ids)
        accepted.append({"group_ids": group_ids, "hypothesis_reason": reason, "evidence": evidence})
    return accepted, {"accepted": accepted, "rejected": rejected}


def compile_detection_v5_hypothesis_membership_edges(
    hypotheses: list[dict[str, Any]],
    semantic_facts: list[dict[str, Any]],
    *,
    visual_groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Turn validated full-page membership proposals into minimal proof trees.

    Registry is the only stage that can compare complete rendered views.  It
    proposes one non-overlapping group set per physical item.  Runtime still
    validates every typed fact and builds the exact ``N - 1`` graph, but does
    not replace the full-page visual decision with a second threshold based on
    OCR coverage or dimension similarity.
    """
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups
        if isinstance(group, dict) and group.get("evidence_class") == "object_evidence"
    }
    facts_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for fact in semantic_facts:
        pair = tuple(sorted((str(fact["group_id_a"]), str(fact["group_id_b"]))))
        facts_by_pair.setdefault(pair, []).append(fact)

    edges: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, hypothesis in enumerate(hypotheses):
        group_ids = sorted({str(group_id) for group_id in hypothesis.get("group_ids") or []})
        group_id_set = set(group_ids)
        parent = {group_id: group_id for group_id in group_ids}

        def root(group_id: str) -> str:
            while parent[group_id] != group_id:
                parent[group_id] = parent[parent[group_id]]
                group_id = parent[group_id]
            return group_id

        proposal_edges: list[dict[str, Any]] = []
        local_pairs = sorted(
            pair for pair in facts_by_pair
            if set(pair).issubset(group_id_set)
        )
        for pair in local_pairs:
            if root(pair[0]) == root(pair[1]):
                continue
            facts = facts_by_pair[pair]
            proposal_edges.append({
                "group_id_a": pair[0],
                "group_id_b": pair[1],
                "page_a": int(groups_by_id[pair[0]].get("page_number") or 0),
                "page_b": int(groups_by_id[pair[1]].get("page_number") or 0),
                "same_page": (
                    int(groups_by_id[pair[0]].get("page_number") or 0)
                    == int(groups_by_id[pair[1]].get("page_number") or 0)
                ),
                "relationship": "same_object_view",
                "evidence_facts": [
                    {
                        "evidence_type": fact["evidence_type"],
                        "evidence_pages": [],
                        "observation": fact["observation"],
                        "source_fact_ids": fact["source_fact_ids"],
                    }
                    for fact in facts
                ],
                "commercial_inseparability": hypothesis["hypothesis_reason"],
                "membership_basis": "registry_pair_local_connected_hypothesis",
            })
            parent[root(pair[1])] = root(pair[0])
        components = sorted({root(group_id) for group_id in group_ids})
        if len(components) != 1:
            rejected.append({
                "index": index,
                "reason": "membership_hypothesis_pair_local_graph_disconnected",
                "group_ids": group_ids,
                "local_fact_pairs": [list(pair) for pair in local_pairs],
                "component_count": len(components),
            })
            continue
        edges.extend(proposal_edges)
        accepted.append({
            "index": index,
            "group_ids": group_ids,
            "edge_count": len(proposal_edges),
        })
    return edges, {
        "compiler_version": "v6_36_registry_pair_local_membership_tree",
        "accepted": accepted,
        "rejected": rejected,
    }


def compile_detection_v637_hypothesis_coverage_components(
    hypotheses: list[dict[str, Any]],
    semantic_facts: list[dict[str, Any]],
    *,
    visual_groups: list[dict[str, Any]],
) -> tuple[list[list[str]], dict[str, Any]]:
    """Accept a multi-view hypothesis only when local facts cover every View.

    A fabrication drawing can establish one object through complementary
    projections.  Those proof pairs need not form a visual chain: a plan may
    support one view while an elevation supports another.  Runtime therefore
    keeps the model's non-overlapping group decision only after every member
    has pair-local, typed evidence inside that exact group.  This returns
    components, not invented root-to-member graph edges.
    """
    object_group_ids = {
        str(group.get("group_id") or "")
        for group in visual_groups
        if isinstance(group, dict) and group.get("evidence_class") == "object_evidence"
    }
    accepted: list[list[str]] = []
    rejected: list[dict[str, Any]] = []
    facts_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for fact in semantic_facts:
        pair = tuple(sorted((str(fact["group_id_a"]), str(fact["group_id_b"]))))
        facts_by_pair.setdefault(pair, []).append(fact)

    for index, hypothesis in enumerate(hypotheses):
        group_ids = sorted({str(group_id) for group_id in hypothesis.get("group_ids") or []})
        group_id_set = set(group_ids)
        if len(group_ids) < 2 or not group_id_set.issubset(object_group_ids):
            rejected.append({
                "index": index,
                "reason": "membership_hypothesis_members_invalid",
                "group_ids": group_ids,
            })
            continue
        local_pairs = sorted(
            pair for pair in facts_by_pair
            if set(pair).issubset(group_id_set)
        )
        covered_group_ids = {
            group_id
            for pair in local_pairs
            for group_id in pair
        }
        missing_group_ids = sorted(group_id_set - covered_group_ids)
        if missing_group_ids:
            rejected.append({
                "index": index,
                "reason": "membership_hypothesis_pair_local_coverage_incomplete",
                "group_ids": group_ids,
                "missing_group_ids": missing_group_ids,
                "local_fact_pairs": [list(pair) for pair in local_pairs],
            })
            continue
        if len(group_ids) > 2 and len(local_pairs) < 2:
            rejected.append({
                "index": index,
                "reason": "membership_hypothesis_requires_multiple_independent_local_pairs",
                "group_ids": group_ids,
                "local_fact_pairs": [list(pair) for pair in local_pairs],
            })
            continue
        accepted.append(group_ids)

    return accepted, {
        "compiler_version": "v6_37_pair_local_hypothesis_coverage",
        "accepted": [
            {"group_ids": component, "local_fact_pair_count": sum(
                set(pair).issubset(set(component)) for pair in facts_by_pair
            )}
            for component in accepted
        ],
        "rejected": rejected,
    }


def compile_detection_v5_membership_edges(
    raw_edges: object,
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate Registry-selected sparse membership links into a proof forest.

    The Registry sees the complete PNG page and returns only positive links.
    A link is accepted only when its typed visual evidence passes the existing
    semantic validator, connects two object-evidence Islands and does not add
    a redundant cycle. Runtime never enumerates missing pairs or invents a
    membership edge from OCR or dimension similarity.
    """
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups
        if isinstance(group, dict) and group.get("evidence_class") == "object_evidence"
    }
    if not isinstance(raw_edges, list):
        return [], {
            "compiler_version": "v5_7_registry_membership_edge_tree",
            "accepted": [],
            "rejected": [{"reason": "membership_edges_not_list"}],
        }

    parent = {group_id: group_id for group_id in groups_by_id}

    def find(group_id: str) -> str:
        while parent[group_id] != group_id:
            parent[group_id] = parent[parent[group_id]]
            group_id = parent[group_id]
        return group_id

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_edges):
        if not isinstance(raw, dict) or set(raw) != {
            "group_id_a", "group_id_b", "membership_reason", "evidence",
        }:
            rejected.append({"index": index, "reason": "membership_edge_fields_invalid"})
            continue
        left, right = sorted((str(raw["group_id_a"] or ""), str(raw["group_id_b"] or "")))
        reason = str(raw["membership_reason"] or "").strip()
        evidence = raw["evidence"] if isinstance(raw["evidence"], list) else []
        pair = (left, right)
        if (
            not reason
            or not evidence
            or left == right
            or not set(pair).issubset(groups_by_id)
        ):
            rejected.append({"index": index, "reason": "membership_edge_endpoints_or_evidence_invalid"})
            continue
        if pair in seen_pairs:
            rejected.append({"index": index, "reason": "membership_edge_duplicate", "group_ids": list(pair)})
            continue
        fact_candidates = [
            {"group_id_a": left, "group_id_b": right, **item}
            for item in evidence
            if isinstance(item, dict)
        ]
        facts, fact_audit = compile_detection_v5_semantic_facts(
            fact_candidates, visual_groups=visual_groups, source_facts=source_facts,
        )
        if not facts:
            rejected.append({
                "index": index,
                "reason": "membership_edge_has_no_validated_visual_fact",
                "group_ids": list(pair),
                "evidence_rejected": fact_audit["rejected"],
            })
            continue
        if find(left) == find(right):
            rejected.append({
                "index": index,
                "reason": "membership_edge_creates_cycle",
                "group_ids": list(pair),
            })
            continue
        parent[find(right)] = find(left)
        seen_pairs.add(pair)
        edge = {
            "group_id_a": left,
            "group_id_b": right,
            "page_a": int(groups_by_id[left].get("page_number") or 0),
            "page_b": int(groups_by_id[right].get("page_number") or 0),
            "same_page": (
                int(groups_by_id[left].get("page_number") or 0)
                == int(groups_by_id[right].get("page_number") or 0)
            ),
            "relationship": "same_object_view",
            "evidence_facts": [
                {
                    "evidence_type": fact["evidence_type"],
                    "evidence_pages": [],
                    "observation": fact["observation"],
                    "source_fact_ids": fact["source_fact_ids"],
                }
                for fact in facts
            ],
            "commercial_inseparability": reason,
            "membership_basis": "registry_full_page_membership_edge",
        }
        edges.append(edge)
        accepted.append({"index": index, "group_ids": list(pair), "edge_count": 1})
    return edges, {
        "compiler_version": "v5_7_registry_membership_edge_tree",
        "accepted": accepted,
        "rejected": rejected,
    }


def compile_detection_v5_semantic_facts(
    facts: object,
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
    allowed_evidence_types: frozenset[str] = SEMANTIC_PAIRWISE_EVIDENCE_TYPES,
    require_pair_endpoint_visual_sources: bool = False,
    reject_document_relation_for_merge: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep grounded V5 positive facts and audit every rejected candidate."""
    object_groups = {
        str(group.get("group_id") or "") for group in visual_groups
        if group.get("evidence_class") == "object_evidence"
    }
    source_ids = {str(fact.get("fact_id") or "") for fact in source_facts}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    source_id_normalizations: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    if not isinstance(facts, list):
        return [], {"accepted": [], "rejected": [{"reason": "semantic_facts_not_list"}]}
    for index, raw in enumerate(facts):
        if not isinstance(raw, dict):
            rejected.append({"index": index, "reason": "fact_not_object"})
            continue
        required = {"group_id_a", "group_id_b", "evidence_type", "strength", "observation", "source_fact_ids"}
        if not required.issubset(raw) or not set(raw).issubset(
            required | {"structural_witness"}
        ):
            rejected.append({"index": index, "reason": "fact_fields_invalid"})
            continue
        left, right = sorted((str(raw["group_id_a"] or ""), str(raw["group_id_b"] or "")))
        kind = str(raw["evidence_type"] or "")
        strength = str(raw["strength"] or "")
        observation = str(raw["observation"] or "").strip()
        raw_cited = (
            [str(value) for value in raw["source_fact_ids"] if str(value)]
            if isinstance(raw["source_fact_ids"], list)
            else []
        )
        cited, normalizations = _canonical_detection_v5_source_fact_ids(
            raw_cited, known_source_ids=source_ids,
        )
        if left == right or left not in object_groups or right not in object_groups:
            rejected.append({"index": index, "reason": "endpoints_not_distinct_object_evidence"})
            continue
        if kind not in allowed_evidence_types or not observation or strength not in {"direct", "single_object_sheet", "standard"}:
            rejected.append({"index": index, "reason": "type_or_observation_invalid"})
            continue
        if kind == "explicit_document_relation" and strength not in {
            "direct", "single_object_sheet",
        }:
            rejected.append({"index": index, "reason": "document_relation_requires_direct_strength"})
            continue
        if kind != "explicit_document_relation" and strength != "standard":
            rejected.append({"index": index, "reason": "non_document_relation_requires_standard_strength"})
            continue
        structural_witness = raw.get("structural_witness")
        if kind == "direct_shared_structure":
            if not isinstance(structural_witness, dict) or set(structural_witness) != {
                "kind", "witness_view_id", "joined_parts", "connection",
            }:
                rejected.append({"index": index, "reason": "direct_shared_structure_requires_physical_witness"})
                continue
            witness_kind = str(structural_witness.get("kind") or "")
            witness_view_id = str(structural_witness.get("witness_view_id") or "")
            joined_parts = structural_witness.get("joined_parts")
            connection = str(structural_witness.get("connection") or "").strip()
            if (
                witness_kind not in _V5_STRUCTURAL_WITNESS_KINDS
                or witness_view_id not in object_groups
                or not isinstance(joined_parts, list)
                or not 2 <= len(joined_parts) <= 3
                or not all(isinstance(part, str) and part.strip() for part in joined_parts)
                or not connection
            ):
                rejected.append({"index": index, "reason": "direct_shared_structure_witness_invalid"})
                continue
            if (
                witness_kind == "endpoint_complete_view_contains_partial"
                and witness_view_id not in {left, right}
            ) or (
                witness_kind == "third_view_shows_both"
                and witness_view_id in {left, right}
            ):
                rejected.append({"index": index, "reason": "direct_shared_structure_witness_endpoint_invalid"})
                continue
            if f"registry_view:{witness_view_id}" not in cited:
                rejected.append({"index": index, "reason": "direct_shared_structure_witness_source_missing"})
                continue
            if _V5_NON_SHARED_STRUCTURE_RE.search(f"{observation} {connection}"):
                rejected.append({"index": index, "reason": "direct_shared_structure_is_generic_specification"})
                continue
        if _V5_HARD_GENERIC_SEMANTIC_RE.search(observation) or (
            _V5_GENERIC_SEMANTIC_RE.search(observation)
            and not _V5_CONCRETE_SEMANTIC_RE.search(observation)
        ):
            rejected.append({"index": index, "reason": "generic_observation", "observation": observation})
            continue
        if not set(cited).issubset(source_ids):
            rejected.append({"index": index, "reason": "unknown_source_fact"})
            continue
        source_id_normalizations.extend({
            "index": index,
            "group_id_a": left,
            "group_id_b": right,
            **normalization,
        } for normalization in normalizations)
        if kind == "explicit_document_relation" and not cited:
            rejected.append({"index": index, "reason": "document_relation_requires_source"})
            continue
        if reject_document_relation_for_merge and kind == "explicit_document_relation":
            rejected.append({
                "index": index,
                "reason": "document_relation_is_context_not_merge_evidence",
            })
            continue
        if require_pair_endpoint_visual_sources:
            required_sources = {
                f"registry_view:{left}", f"registry_view:{right}",
            }
            if not required_sources.issubset(set(cited)):
                rejected.append({
                    "index": index,
                    "reason": "pair_endpoint_visual_sources_missing",
                    "required_source_fact_ids": sorted(required_sources),
                    "source_fact_ids": cited,
                })
                continue
        if kind == "dimension_transform" and (len(cited) < 2 or len(re.findall(r"\d", observation)) < 2):
            rejected.append({"index": index, "reason": "transform_requires_two_readings"})
            continue
        if kind == "visual_dimension_similarity":
            endpoint_sources = {
                f"registry_view:{left}", f"registry_view:{right}",
            }
            if (
                not endpoint_sources.issubset(set(cited))
                or len(re.findall(r"\d+(?:[.,]\d+)?", observation)) < 2
            ):
                rejected.append({
                    "index": index,
                    "reason": "visual_dimension_similarity_requires_two_visible_readings",
                })
                continue
        key = (left, right, kind, observation)
        if key in seen:
            rejected.append({"index": index, "reason": "duplicate_fact"})
            continue
        seen.add(key)
        accepted.append({
            "group_id_a": left, "group_id_b": right, "evidence_type": kind,
            "strength": strength, "observation": observation, "source_fact_ids": cited,
            **(
                {"structural_witness": {
                    "kind": str(structural_witness["kind"]),
                    "witness_view_id": str(structural_witness["witness_view_id"]),
                    "joined_parts": [part.strip() for part in structural_witness["joined_parts"]],
                    "connection": str(structural_witness["connection"]).strip(),
                }}
                if kind == "direct_shared_structure" else {}
            ),
        })
    return accepted, {
        "accepted": accepted,
        "rejected": rejected,
        "source_id_normalizations": source_id_normalizations,
    }


def compile_detection_v5_visual_dimension_conflicts(
    conflicts: object,
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
    allowed_pairs: set[tuple[str, str]],
) -> tuple[dict[tuple[str, str], str], dict[str, Any]]:
    """Keep only explicit visual dimension contradictions as merge guards.

    This is intentionally not a negative graph channel. A conflict is emitted
    only when the visual-only Registry can read incompatible measurements in
    both Views. Missing or unreadable dimensions produce no record.
    """
    object_groups = {
        str(group.get("group_id") or "") for group in visual_groups
        if group.get("evidence_class") == "object_evidence"
    }
    source_ids = {str(fact.get("fact_id") or "") for fact in source_facts}
    accepted: dict[tuple[str, str], str] = {}
    rejected: list[dict[str, Any]] = []
    normalizations: list[dict[str, Any]] = []
    if not isinstance(conflicts, list):
        return {}, {"accepted": [], "rejected": [{"reason": "dimension_conflicts_not_list"}]}
    for index, raw in enumerate(conflicts):
        if not isinstance(raw, dict) or set(raw) != {
            "group_id_a", "group_id_b", "readings_a", "readings_b",
            "observation", "source_fact_ids",
        }:
            rejected.append({"index": index, "reason": "dimension_conflict_fields_invalid"})
            continue
        left, right = sorted((
            str(raw.get("group_id_a") or ""),
            str(raw.get("group_id_b") or ""),
        ))
        pair = (left, right)
        observation = str(raw.get("observation") or "").strip()
        readings_a = raw.get("readings_a")
        readings_b = raw.get("readings_b")
        raw_cited = (
            [str(value) for value in raw["source_fact_ids"] if str(value)]
            if isinstance(raw.get("source_fact_ids"), list) else []
        )
        cited, fact_normalizations = _canonical_detection_v5_source_fact_ids(
            raw_cited, known_source_ids=source_ids,
        )
        required_sources = {f"registry_view:{left}", f"registry_view:{right}"}
        readings_are_numeric = (
            isinstance(readings_a, list)
            and isinstance(readings_b, list)
            and all(
                isinstance(reading, str)
                and re.fullmatch(
                    r"\s*\d+(?:[.,]\d+)?\s*(?:mm|cm|m)?\s*",
                    reading,
                    re.IGNORECASE,
                )
                for reading in [*readings_a, *readings_b]
            )
        )
        if (
            left == right
            or not set(pair).issubset(object_groups)
            or pair not in allowed_pairs
            or not observation
            or not isinstance(readings_a, list)
            or not isinstance(readings_b, list)
            or not readings_a
            or not readings_b
            or not readings_are_numeric
            or not required_sources.issubset(set(cited))
            or not set(cited).issubset(source_ids)
        ):
            rejected.append({"index": index, "reason": "dimension_conflict_not_grounded"})
            continue
        if pair in accepted:
            rejected.append({"index": index, "reason": "duplicate_dimension_conflict"})
            continue
        accepted[pair] = observation
        normalizations.extend({
            "index": index,
            "group_id_a": left,
            "group_id_b": right,
            **normalization,
        } for normalization in fact_normalizations)
    return accepted, {
        "accepted": [
            {"group_id_a": pair[0], "group_id_b": pair[1], "observation": observation}
            for pair, observation in sorted(accepted.items())
        ],
        "rejected": rejected,
        "source_id_normalizations": normalizations,
    }


def compile_detection_v5_nested_duplicate_islands(
    duplicates: object,
    *,
    visual_groups: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, Any]]:
    """Accept only a grounded, visually contained Island fragment.

    The Registry, not rectangle overlap, decides whether a fragment lacks an
    independent drawing boundary. Runtime merely requires strong containment,
    same-page geometry and both immutable View sources before removing it.
    """
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups
        if group.get("evidence_class") == "object_evidence"
    }
    source_ids = {str(fact.get("fact_id") or "") for fact in source_facts}
    accepted: dict[str, str] = {}
    rejected: list[dict[str, Any]] = []

    def core_bbox(group: dict[str, Any]) -> tuple[int, int, int, int] | None:
        value = group.get("core_bbox")
        if not isinstance(value, dict):
            return None
        keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
        if set(value) != set(keys) or not all(isinstance(value[key], int) for key in keys):
            return None
        left, top, right, bottom = (value[key] for key in keys)
        return (left, top, right, bottom) if right > left and bottom > top else None

    if not isinstance(duplicates, list):
        return {}, {"accepted": [], "rejected": [{"reason": "nested_duplicates_not_list"}]}
    for index, raw in enumerate(duplicates):
        required = {"child_group_id", "parent_group_id", "observation", "source_fact_ids"}
        if not isinstance(raw, dict) or set(raw) != required:
            rejected.append({"index": index, "reason": "nested_duplicate_fields_invalid"})
            continue
        child_id = str(raw.get("child_group_id") or "")
        parent_id = str(raw.get("parent_group_id") or "")
        observation = str(raw.get("observation") or "").strip()
        raw_cited = raw.get("source_fact_ids")
        cited, _ = _canonical_detection_v5_source_fact_ids(
            [str(value) for value in raw_cited if str(value)]
            if isinstance(raw_cited, list) else [],
            known_source_ids=source_ids,
        )
        child = groups_by_id.get(child_id)
        parent = groups_by_id.get(parent_id)
        child_bbox = core_bbox(child) if child else None
        parent_bbox = core_bbox(parent) if parent else None
        if (
            child_id == parent_id
            or child_id in accepted
            or child is None
            or parent is None
            or not observation
            or child_bbox is None
            or parent_bbox is None
            or int(child.get("page_number") or 0) != int(parent.get("page_number") or 0)
            or not {
                f"registry_view:{child_id}", f"registry_view:{parent_id}",
            }.issubset(set(cited))
            or not set(cited).issubset(source_ids)
        ):
            rejected.append({"index": index, "reason": "nested_duplicate_not_grounded"})
            continue
        child_left, child_top, child_right, child_bottom = child_bbox
        parent_left, parent_top, parent_right, parent_bottom = parent_bbox
        child_area = (child_right - child_left) * (child_bottom - child_top)
        parent_area = (parent_right - parent_left) * (parent_bottom - parent_top)
        overlap_area = max(0, min(child_right, parent_right) - max(child_left, parent_left)) * max(
            0, min(child_bottom, parent_bottom) - max(child_top, parent_top),
        )
        contained_fraction = overlap_area / child_area if child_area else 0.0
        if parent_area <= child_area or contained_fraction < 0.85:
            rejected.append({
                "index": index,
                "reason": "nested_duplicate_geometry_insufficient",
                "contained_fraction": round(contained_fraction, 4),
            })
            continue
        accepted[child_id] = parent_id
    return accepted, {
        "accepted": [
            {"child_group_id": child_id, "parent_group_id": parent_id}
            for child_id, parent_id in sorted(accepted.items())
        ],
        "rejected": rejected,
    }


def compile_detection_v5_merge_edges(
    dimension_edges: list[dict[str, Any]],
    semantic_facts: list[dict[str, Any]],
    *,
    visual_groups: list[dict[str, Any]] | None = None,
    group_bboxes: dict[str, dict[str, float]] | None = None,
    allow_runtime_merges: bool = True,
    merge_blocked_pairs: dict[tuple[str, str], str] | None = None,
    allow_batch_confirmation: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Merge from a minimal semantic proof forest plus deterministic Dimensions."""
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in dimension_edges:
        pair = (str(edge["group_id_a"]), str(edge["group_id_b"]))
        row = by_pair.setdefault(pair, {"dimension_score": 0.0, "semantic_facts": [], "dimension_facts": []})
        row["dimension_score"] = max(row["dimension_score"], float(edge.get("dimension_similarity_score") or 0))
        row["dimension_facts"].extend(edge.get("evidence_facts") or [])
    for fact in semantic_facts:
        pair = (str(fact["group_id_a"]), str(fact["group_id_b"]))
        by_pair.setdefault(pair, {"dimension_score": 0.0, "semantic_facts": [], "dimension_facts": []})["semantic_facts"].append(fact)
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups or [] if isinstance(group, dict)
    }
    group_ids = sorted(groups_by_id) or sorted({group_id for pair in by_pair for group_id in pair})
    candidate_pairs = sorted({tuple(sorted(pair)) for pair in by_pair})

    def candidate_key(pair: tuple[str, str]) -> tuple[int, float, int, str, str]:
        left_group, right_group = groups_by_id.get(pair[0], {}), groups_by_id.get(pair[1], {})
        left_page = int(left_group.get("page_number") or 0)
        right_page = int(right_group.get("page_number") or 0)
        left_box = (group_bboxes or {}).get(pair[0]) or {}
        right_box = (group_bboxes or {}).get(pair[1]) or {}
        try:
            left_x = (float(left_box["top_left_x"]) + float(left_box["bottom_right_x"])) / 2
            left_y = (float(left_box["top_left_y"]) + float(left_box["bottom_right_y"])) / 2
            right_x = (float(right_box["top_left_x"]) + float(right_box["bottom_right_x"])) / 2
            right_y = (float(right_box["top_left_y"]) + float(right_box["bottom_right_y"])) / 2
            distance = (left_x - right_x) ** 2 + (left_y - right_y) ** 2
        except (KeyError, TypeError, ValueError):
            distance = float("inf")
        return (1 if left_page != right_page else 0, distance, min(left_page, right_page), pair[0], pair[1])

    edges: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    components: dict[str, str] = {group_id: group_id for group_id in group_ids}

    def root(group_id: str) -> str:
        components.setdefault(group_id, group_id)
        while components[group_id] != group_id:
            components[group_id] = components[components[group_id]]
            group_id = components[group_id]
        return group_id

    blocked_pairs = {
        tuple(sorted(pair)): reason
        for pair, reason in (merge_blocked_pairs or {}).items()
    }

    for pair in sorted(candidate_pairs, key=candidate_key):
        row = by_pair.get(pair, {"dimension_score": 0.0, "semantic_facts": [], "dimension_facts": []})
        if root(pair[0]) == root(pair[1]):
            audit.append({"group_id_a": pair[0], "group_id_b": pair[1], "skipped": "internal_package_pair"})
            continue
        if not row["dimension_facts"] and not row["semantic_facts"]:
            audit.append({"group_id_a": pair[0], "group_id_b": pair[1], "inspected": True, "merge": False})
            continue
        kinds = {fact["evidence_type"] for fact in row["semantic_facts"]}
        direct_label = any(fact["evidence_type"] == "explicit_document_relation" and fact["strength"] == "direct" for fact in row["semantic_facts"])
        semantic_points = sum(
            (
                100 if fact["strength"] == "direct" else
                55 if fact["strength"] == "single_object_sheet" else
                0 if fact["evidence_type"] == "explicit_document_relation" else
                _V5_SEMANTIC_POINTS[fact["evidence_type"]]
            )
            for fact in row["semantic_facts"]
        )
        edge_score = min(100.0, row["dimension_score"] + semantic_points)
        identity_fact = bool(kinds.intersection({
            "explicit_document_relation", "matching_topology", "unique_geometry",
            "direct_shared_structure", "visual_dimension_similarity",
        }))
        semantic_proof = len(kinds) >= 2 and identity_fact
        merge = allow_runtime_merges and pair not in blocked_pairs and (
            direct_label
            or semantic_proof
            or (row["dimension_score"] >= 85 and bool(kinds))
            or (edge_score >= 100 and identity_fact)
        )
        facts = [*row["dimension_facts"], *[
            {
                "evidence_type": fact["evidence_type"],
                "evidence_pages": [],
                "observation": fact["observation"],
                "source_fact_ids": fact["source_fact_ids"],
                **(
                    {"structural_witness": fact["structural_witness"]}
                    if "structural_witness" in fact else {}
                ),
            }
            for fact in row["semantic_facts"]
        ]]
        edges.append({
            "group_id_a": pair[0], "group_id_b": pair[1],
            "page_a": int(groups_by_id.get(pair[0], {}).get("page_number") or 0),
            "page_b": int(groups_by_id.get(pair[1], {}).get("page_number") or 0),
            "same_page": int(groups_by_id.get(pair[0], {}).get("page_number") or 0) == int(groups_by_id.get(pair[1], {}).get("page_number") or 0),
            "relationship": "same_object_view" if merge else SUPPORTING_RELATIONSHIP,
            "evidence_facts": facts,
            "commercial_inseparability": "V5 deterministic merge policy",
            "dimension_similarity_score": row["dimension_score"],
            "edge_score": edge_score,
        })
        audit.append({
            "group_id_a": pair[0], "group_id_b": pair[1],
            "dimension_similarity_score": row["dimension_score"],
            "edge_score": edge_score, "merge": merge,
            **({"merge_blocked": blocked_pairs[pair]} if pair in blocked_pairs else {}),
        })
        if merge:
            components[root(pair[1])] = root(pair[0])

    # Grow a confirmed package through existing same-page Q support. This is
    # the deterministic one-to-batch step: no new pair is searched and a
    # cross-page edge can never be promoted here.
    confirmed_roots = {
        root(str(edge["group_id_a"])) for edge in edges
        if edge["relationship"] == "same_object_view"
    }
    changed = allow_batch_confirmation
    while changed:
        changed = False
        for edge in edges:
            if edge["relationship"] == "same_object_view" or not edge["same_page"]:
                continue
            pair = tuple(sorted((str(edge["group_id_a"]), str(edge["group_id_b"]))))
            if pair in blocked_pairs:
                continue
            left_root, right_root = root(str(edge["group_id_a"])), root(str(edge["group_id_b"]))
            if left_root == right_root:
                continue
            anchored = left_root in confirmed_roots or right_root in confirmed_roots
            semantic_support = any(
                fact.get("evidence_type") != "dimension_equality"
                for fact in edge["evidence_facts"]
            )
            if not anchored or (edge["dimension_similarity_score"] < 40 and not semantic_support):
                continue
            components[right_root] = left_root
            confirmed_roots.discard(right_root)
            confirmed_roots.add(left_root)
            edge["relationship"] = "same_object_view"
            edge["commercial_inseparability"] = "V5 deterministic batch confirmation"
            audit.append({
                "group_id_a": edge["group_id_a"], "group_id_b": edge["group_id_b"],
                "dimension_similarity_score": edge["dimension_similarity_score"],
                "edge_score": edge["edge_score"], "merge": True,
                "batch_confirmation": True,
            })
            changed = True

    return edges, {
        "compiler_version": (
            "v5_5_global_semantic_proof_forest"
            if allow_runtime_merges else "v5_7_supporting_graph_only"
        ),
        "candidate_order": [{"group_id_a": pair[0], "group_id_b": pair[1]} for pair in sorted(candidate_pairs, key=candidate_key)],
        "edges": audit,
    }


def validate_detection_v5_final_result(
    registry: dict[str, Any],
    *,
    visual_groups: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    source_facts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Final V5 gate: ownership and accepted graph must be internally real.

    This is deliberately an invariant check, not a second interpretation pass.
    Weak or rejected facts never reach it; corrupt references stop File Review.
    """
    # The caller removes document_context before normalizing the visual map.
    # At this final gate, every retained group is therefore object Evidence.
    object_group_ids = {str(group.get("group_id") or "") for group in visual_groups}
    validate_detection_registry(
        registry,
        visual_group_ids=object_group_ids,
        object_evidence_group_ids=object_group_ids,
    )
    source_ids = {str(fact.get("fact_id") or "") for fact in source_facts}
    for edge in graph_edges:
        left = str(edge.get("group_id_a") or "")
        right = str(edge.get("group_id_b") or "")
        if left == right or left not in object_group_ids or right not in object_group_ids:
            raise DetectionRegistrySchemaError("V5 graph has invalid endpoints")
        if edge.get("relationship") not in {"same_object_view", SUPPORTING_RELATIONSHIP}:
            raise DetectionRegistrySchemaError("V5 graph has invalid relationship")
        facts = edge.get("evidence_facts")
        if not isinstance(facts, list) or not facts:
            raise DetectionRegistrySchemaError("V5 graph edge has no accepted evidence")
        for fact in facts:
            cited = fact.get("source_fact_ids") if isinstance(fact, dict) else None
            if not isinstance(cited, list) or not set(map(str, cited)).issubset(source_ids):
                raise DetectionRegistrySchemaError("V5 graph cites an unknown source fact")
    return registry


_V5_COMMON_DIMENSIONS_MM = frozenset({300, 400, 450, 500, 600, 800, 900, 1000, 1200})


def compile_detection_v5_dimension_graph(
    fingerprints: list[dict[str, Any]], *, visual_groups: list[dict[str, Any]],
    group_bboxes: dict[str, dict[str, float]] | None = None,
    allowed_pairs: set[tuple[str, str]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Score Dimension Equality through Q, or build Q for proto-regions.

    ``allowed_pairs`` is the pre-Registry Candidate Pair Queue translated onto
    final Islands.  When supplied, this function must never discover a new
    pair.  Without it, it performs the bounded proto-region discovery that
    creates Q.
    """
    groups_by_id = {
        str(group.get("group_id") or ""): group
        for group in visual_groups if isinstance(group, dict)
    }
    group_ids = set(groups_by_id)
    occurrences = {
        str(row.get("group_id") or ""): [item for item in row.get("occurrences") or [] if item.get("value_mm") is not None]
        for row in fingerprints if str(row.get("group_id") or "") in group_ids
    }
    frequency: dict[Decimal, int] = {}
    for values in occurrences.values():
        for value in {Decimal(str(item["value_mm"])) for item in values}:
            frequency[value] = frequency.get(value, 0) + 1

    def size_points(value: Decimal) -> float:
        if value < 100: return 2
        if value < 600: return 5
        if value < 1200: return 8
        if value < 2200: return 14
        return 20

    def precision(left: Decimal, right: Decimal) -> float:
        difference = abs(left - right)
        if not difference: return 2.5
        ratio = difference / max(left, right)
        return 1.75 if ratio <= Decimal("0.01") else 1.0

    def rarity(left: Decimal, right: Decimal) -> float:
        count = max(frequency.get(left, 1), frequency.get(right, 1))
        return 1.75 if count <= 2 else 1.25 if count <= 5 else 0.8

    def score_pair(left_id: str, right_id: str) -> tuple[float, list[dict[str, Any]], list[dict[str, Any]]]:
        raw_matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for left in occurrences.get(left_id, []):
            for right in occurrences.get(right_id, []):
                left_value, right_value = Decimal(str(left["value_mm"])), Decimal(str(right["value_mm"]))
                if left_value <= 0 or right_value <= 0 or abs(left_value - right_value) / max(left_value, right_value) > Decimal("0.02"):
                    continue
                raw_matches.append((left, right))
        raw_matches.sort(key=lambda pair: (abs(Decimal(str(pair[0]["value_mm"])) - Decimal(str(pair[1]["value_mm"]))), str(pair[0]["occurrence_id"]), str(pair[1]["occurrence_id"])))
        used_left: set[str] = set()
        used_right: set[str] = set()
        used_left_slots: set[str] = set()
        used_right_slots: set[str] = set()
        matched: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for left, right in raw_matches:
            left_slot = str(left.get("ambiguity_key") or left["occurrence_id"])
            right_slot = str(right.get("ambiguity_key") or right["occurrence_id"])
            if (
                left["occurrence_id"] in used_left or right["occurrence_id"] in used_right
                or left_slot in used_left_slots or right_slot in used_right_slots
            ):
                continue
            used_left.add(left["occurrence_id"])
            used_right.add(right["occurrence_id"])
            used_left_slots.add(left_slot)
            used_right_slots.add(right_slot)
            matched.append((left, right))
        by_value: dict[tuple[Decimal, Decimal], list[tuple[dict[str, Any], dict[str, Any]]]] = {}
        for pair in matched:
            key = (Decimal(str(pair[0]["value_mm"])), Decimal(str(pair[1]["value_mm"])))
            by_value.setdefault(key, []).append(pair)
        score = 0.0
        facts: list[dict[str, Any]] = []
        feature_rows: list[dict[str, Any]] = []
        for (left_value, right_value), value_matches in sorted(by_value.items()):
            count = len(value_matches)
            occurrence_factor = 1.0 if count == 1 else 1.25 if count == 2 else 1.5 if count == 3 else 1.75
            common_factor = 0.8 if int(min(left_value, right_value)) in _V5_COMMON_DIMENSIONS_MM else 1.0
            points = size_points(min(left_value, right_value)) * precision(left_value, right_value) * rarity(left_value, right_value) * common_factor * occurrence_factor
            score += points
            fact_ids = sorted({fact_id for pair in value_matches for item in pair for fact_id in item["source_fact_ids"]})
            observation = f"{left_value} mm matches {right_value} mm; {count} paired occurrence(s); {points:.2f} points."
            facts.append({"evidence_type": "dimension_equality", "evidence_pages": [], "observation": observation, "source_fact_ids": fact_ids})
            feature_rows.append({"left_mm": str(left_value), "right_mm": str(right_value), "matched_occurrences": count, "points": round(points, 3)})
        score = round(min(100.0, score), 3)
        return score, facts, feature_rows

    def page(group_id: str) -> int:
        return int(groups_by_id[group_id].get("page_number") or 0)

    def centre(group_id: str) -> tuple[float, float] | None:
        bbox = (group_bboxes or {}).get(group_id) or {}
        try:
            return (
                (float(bbox["top_left_x"]) + float(bbox["bottom_right_x"])) / 2,
                (float(bbox["top_left_y"]) + float(bbox["bottom_right_y"])) / 2,
            )
        except (KeyError, TypeError, ValueError):
            return None

    def candidate_key(seed: str, target: str) -> tuple[int, float, int, float, str]:
        seed_centre, target_centre = centre(seed), centre(target)
        distance = (
            (seed_centre[0] - target_centre[0]) ** 2
            + (seed_centre[1] - target_centre[1]) ** 2
            if seed_centre is not None and target_centre is not None
            else float("inf")
        )
        same_page = page(seed) == page(target)
        return (
            0 if same_page else 1,
            distance if same_page else float(abs(page(seed) - page(target))),
            abs(page(seed) - page(target)), distance, target,
        )

    threshold = 25.0
    edges: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    evaluated_pairs: set[tuple[str, str]] = set()
    discovery_parents: dict[str, str] = {group_id: group_id for group_id in group_ids}

    def discovery_root(group_id: str) -> str:
        while discovery_parents[group_id] != group_id:
            discovery_parents[group_id] = discovery_parents[discovery_parents[group_id]]
            group_id = discovery_parents[group_id]
        return group_id

    def record_pair(left_id: str, right_id: str, *, cycle: str) -> float:
        score, facts, feature_rows = score_pair(left_id, right_id)
        candidate = {
            "group_id_a": left_id, "group_id_b": right_id,
            "page_a": page(left_id), "page_b": page(right_id),
            "same_page": page(left_id) == page(right_id),
            "cycle": cycle, "dimension_similarity_score": score,
            "features": feature_rows,
        }
        candidates.append(candidate)
        if score >= threshold:
            edges.append({
                "group_id_a": left_id, "group_id_b": right_id,
                "page_a": page(left_id), "page_b": page(right_id),
                "same_page": page(left_id) == page(right_id), "cycle": cycle,
                "relationship": SUPPORTING_RELATIONSHIP, "evidence_facts": facts,
                "commercial_inseparability": "V5 dimension support",
                "dimension_similarity_score": score,
            })
        return score

    # Final, classified Islands are authoritative for same-page comparison.
    # Fusion Candidate Regions only prioritize cross-page work. They may miss a
    # real Island, so they must never prevent any final same-page pair from
    # receiving its deterministic Dimension comparison.
    for page_number in sorted({page(group_id) for group_id in group_ids}):
        page_group_ids = sorted(
            group_id for group_id in group_ids if page(group_id) == page_number
        )
        for left_id, right_id in combinations(page_group_ids, 2):
            pair = (left_id, right_id)
            evaluated_pairs.add(pair)
            score = record_pair(
                left_id, right_id, cycle="same_page_all_to_all",
            )
            if score >= threshold:
                discovery_parents[discovery_root(right_id)] = discovery_root(left_id)

    if allowed_pairs is not None:
        # Keep the bounded Candidate Q for cross-page revalidation. Same-page
        # pairs above have already been evaluated from final Registry Islands.
        for left_id, right_id in sorted(allowed_pairs):
            if left_id not in group_ids or right_id not in group_ids or left_id == right_id:
                continue
            pair = tuple(sorted((left_id, right_id)))
            if pair in evaluated_pairs:
                continue
            evaluated_pairs.add(pair)
            record_pair(left_id, right_id, cycle="q_revalidation")
    else:
        # Cross-page discovery remains bounded below.
        for seed in sorted(group_ids):
            if discovery_root(seed) != seed:
                continue
            for target in sorted((group_id for group_id in group_ids if page(group_id) != page(seed)), key=lambda group_id: candidate_key(seed, group_id)):
                left_id, right_id = sorted((seed, target))
                pair = (left_id, right_id)
                if pair in evaluated_pairs:
                    continue
                evaluated_pairs.add(pair)
                score = record_pair(left_id, right_id, cycle="cross_page_discovery")
                if score >= 85:
                    break

    parents: dict[str, str] = {group_id: group_id for group_id in group_ids}

    def root(group_id: str) -> str:
        while parents[group_id] != group_id:
            parents[group_id] = parents[parents[group_id]]
            group_id = parents[group_id]
        return group_id

    for edge in edges:
        if edge["same_page"]:
            parents[root(str(edge["group_id_b"]))] = root(str(edge["group_id_a"]))
    provisional_components: dict[str, list[str]] = {}
    for group_id in sorted(group_ids):
        provisional_components.setdefault(root(group_id), []).append(group_id)
    provisional_components_list = [
        component for component in provisional_components.values() if len(component) >= 3
    ]
    return edges, {
        "compiler_version": (
            "v5_10_6_final_same_page_all_pairs_q_cross_page_threshold_25"
            if allowed_pairs is not None
            else "v5_10_4_same_page_all_pairs_threshold_25"
        ),
        "dimension_edge_threshold": threshold,
        "provisional_components": provisional_components_list,
        "dimension_similarity_candidates": candidates,
        "dimension_similarity_edges": [{key: row[key] for key in ("group_id_a", "group_id_b", "page_a", "page_b", "same_page", "cycle", "dimension_similarity_score")} for row in edges],
    }


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


def derive_detection_v5_dominant_page_attachment_edges(
    proof_components: list[list[str]],
    *,
    visual_groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach the one orphan inside an otherwise dominant same-page package.

    This is a package-completion policy, not a seventh semantic criterion.
    It does not inspect a new pair, alter Registry membership, or cross pages.
    """
    page_by_group = {
        str(group.get("group_id") or ""): int(group.get("page_number") or 0)
        for group in visual_groups
    }
    edges: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for page_number in sorted(set(page_by_group.values())):
        page_groups = {group_id for group_id, page in page_by_group.items() if page == page_number}
        page_components = [sorted(set(component).intersection(page_groups)) for component in proof_components]
        page_components = [component for component in page_components if component]
        confirmed = [component for component in page_components if len(component) >= 2]
        singletons = [component[0] for component in page_components if len(component) == 1]
        dominant = max(confirmed, key=lambda component: (len(component), tuple(component)), default=[])
        competing = sum(len(component) for component in confirmed if component != dominant)
        attach = []
        if len(dominant) >= 6 and len(singletons) == 1 and competing == 0:
            attach = singletons
            root = dominant[0]
            orphan = attach[0]
            edges.append({
                "group_id_a": min(root, orphan), "group_id_b": max(root, orphan),
                "page_a": page_number, "page_b": page_number, "same_page": True,
                "relationship": "same_object_view",
                "evidence_facts": [{
                    "evidence_type": "deterministic_page_context",
                    "evidence_pages": [page_number],
                    "observation": "One standalone View completes the only dominant same-page package.",
                    "source_fact_ids": [],
                }],
                "commercial_inseparability": "V5.6.1 deterministic dominant-page attachment",
                "dimension_similarity_score": 0.0, "edge_score": 0.0,
            })
        audit.append({
            "page_number": page_number, "dominant_view_count": len(dominant),
            "standalone_group_ids": singletons, "competing_view_count": competing,
            "attached_group_ids": attach,
        })
    return edges, audit


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
