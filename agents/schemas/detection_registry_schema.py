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
    if set(rows_by_pair) != expected_pairs:
        raise DetectionRegistrySchemaError("semantic pairwise ledger must account for every same-page pair")

    edges: list[dict[str, Any]] = []
    for pair in sorted(rows_by_pair):
        row = rows_by_pair[pair]
        facts = [
            {"evidence_type": check["evidence_type"],
             "evidence_pages": [page_by_group[pair[0]]],
             "observation": check["observation"]}
            for check in row["checks"].values() if check["state"] == "present"
        ]
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
