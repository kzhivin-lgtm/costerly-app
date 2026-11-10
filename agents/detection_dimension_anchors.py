"""Conservative same-sheet dimension proof for ordinary Detection."""

from collections import Counter
from decimal import Decimal
from itertools import pairwise, product

from agents.schemas.detection_registry_schema import _V5_COMMON_DIMENSIONS_MM

# Reuse the Fingerprint's scoring bands for small and large spans. For an
# automatic anchor, the large span must be exact and occur in only two Views.
SMALL_SPAN_MM = 100
LARGE_SPAN_MM = 1200


def positioned_occurrences(inventory):
    return [
        (Decimal(str(row["value_mm"])), row["normalized_bbox"], frozenset(row["source_fact_ids"]))
        for row in inventory["occurrences"]
        if row.get("normalized_bbox") and row.get("source_fact_ids") and row.get("value_mm") is not None
    ]


def neighbor_spans(occurrences, exclude_values):
    """Find consecutive informative labels aligned along one measurement line."""
    pairs = {}
    for axis, perpendicular in (("x", "y"), ("y", "x")):
        items = []
        for value, bbox, sources in occurrences:
            if value < SMALL_SPAN_MM or value in exclude_values:
                continue
            start = bbox[f"top_left_{perpendicular}"]
            end = bbox[f"bottom_right_{perpendicular}"]
            along = (bbox[f"top_left_{axis}"] + bbox[f"bottom_right_{axis}"]) / 2
            items.append(((start + end) / 2, along, end - start, value, sources))
        lines = []
        for item in sorted(items, key=lambda row: row[0]):
            if not lines or item[0] - lines[-1][0][0] > max(item[2], lines[-1][0][2]) * 0.65:
                lines.append([item])
            else:
                lines[-1].append(item)
        for line in lines:
            for left, right in pairwise(sorted(line, key=lambda row: row[1])):
                a, b = left[3], right[3]
                if a == b or {a, b} <= _V5_COMMON_DIMENSIONS_MM or left[4] & right[4]:
                    continue
                pairs.setdefault((a, b), []).append(left[4] | right[4])
    return pairs


def dimension_anchors(usage, eligible_ids):
    """Find actual Q pairs with a rare exact extent and independent corroboration."""
    occurrences = {
        row["group_id"]: positioned_occurrences(row) for row in usage["dimension_inventory"]
    }
    frequency = Counter(value for rows in occurrences.values() for value in {value for value, _, _ in rows})
    proofs = []
    for row in usage["dimension_graph_audit"]["dimension_similarity_candidates"]:
        a, b = row["group_id_a"], row["group_id_b"]
        if not row["same_page"] or row["dimension_similarity_score"] < 100 or not {a, b} <= eligible_ids:
            continue
        rare_values = {
            Decimal(feature["left_mm"])
            for feature in row["features"]
            if feature["left_mm"] == feature["right_mm"]
            and Decimal(feature["left_mm"]) >= LARGE_SPAN_MM
            and frequency[Decimal(feature["left_mm"])] == 2
        }
        if not rare_values:
            continue
        rare_sources = {
            value: [(left_sources, right_sources)
                    for left_sources, right_sources in product(
                        (sources for v, _, sources in occurrences[a] if v == value),
                        (sources for v, _, sources in occurrences[b] if v == value),
                    ) if not left_sources & right_sources]
            for value in rare_values
        }
        confirmed_rare = sorted(value for value, sources in rare_sources.items() if sources)
        left_chains = neighbor_spans(occurrences[a], rare_values)
        right_chains = neighbor_spans(occurrences[b], rare_values)
        corroborating = [
            chain for chain in sorted(left_chains.keys() & right_chains.keys())
            if any(
                not (left_chain & right_chain or left_chain & left_extent or right_chain & right_extent
                     or left_chain & right_extent or right_chain & left_extent)
                for value in confirmed_rare
                for left_extent, right_extent in rare_sources[value]
                for left_chain, right_chain in product(left_chains[chain], right_chains[chain])
            )
        ]
        independent_extents = any(
            not ((left_a | right_a) & (left_b | right_b))
            for i, first in enumerate(confirmed_rare) for second in confirmed_rare[i+1:]
            for (left_a, right_a), (left_b, right_b) in product(rare_sources[first], rare_sources[second])
        )
        if corroborating or independent_extents:
            proofs.append({
                "group_id_a": a, "group_id_b": b,
                "relationship": "same_object_view",
                "rare_exact_extents_mm": [str(value) for value in confirmed_rare],
                "corroborating_ordered_spans_mm": [[str(value) for value in pair] for pair in corroborating],
            })
    return proofs
