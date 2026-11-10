"""Conservative same-sheet dimension proof for ordinary Detection."""

from collections import Counter
from decimal import Decimal
from itertools import groupby, pairwise, product

from agents.schemas.detection_registry_schema import _V5_COMMON_DIMENSIONS_MM

# Reuse the Fingerprint's scoring bands for small and large spans. A common
# large span needs a separately printed and matching measurement sequence.
SMALL_SPAN_MM = 100
LARGE_SPAN_MM = 1200


def positioned_occurrences(inventory):
    return [
        (Decimal(str(row["value_mm"])), row["normalized_bbox"], frozenset(row["source_fact_ids"]))
        for row in inventory["occurrences"]
        if row.get("normalized_bbox") and row.get("source_fact_ids") and row.get("value_mm") is not None
    ]


def _measurement_lines(occurrences, exclude_values):
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
            yield axis, sorted(line, key=lambda row: row[1])


def neighbor_spans(occurrences, exclude_values):
    """Find consecutive informative labels aligned along one measurement line."""
    pairs = {}
    for _, line in _measurement_lines(occurrences, exclude_values):
        for left, right in pairwise(line):
            a, b = left[3], right[3]
            if a == b or {a, b} <= _V5_COMMON_DIMENSIONS_MM or left[4] & right[4]:
                continue
            pairs.setdefault((a, b), []).append(left[4] | right[4])
    return pairs


def _repeated_span_chains(occurrences, rare_totals):
    """Find evenly spaced repeated spans corroborated by a separately printed total."""
    chains = set()
    for axis, line in _measurement_lines(occurrences, rare_totals):
        for value, run in groupby(line, key=lambda row: row[3]):
            labels = list(run)
            if len(labels) < 3 or value in _V5_COMMON_DIMENSIONS_MM:
                continue
            sources = [label[4] for label in labels]
            all_sources = frozenset().union(*sources)
            if len(all_sources) != sum(map(len, sources)):
                continue
            positions = [label[1] for label in labels]
            gaps = [right - left for left, right in pairwise(positions)]
            gap = min(gaps)
            if gap <= 0 or max(gaps) > 1.25 * gap:
                continue
            midpoint = (positions[0] + positions[-1]) / 2
            for total, bbox, total_sources in occurrences:
                if total not in rare_totals or total_sources & all_sources:
                    continue
                if abs(total - value * len(labels)) > total * Decimal("0.005"):
                    continue
                centre = (bbox[f"top_left_{axis}"] + bbox[f"bottom_right_{axis}"]) / 2
                if abs(centre - midpoint) <= 0.25 * gap:
                    chains.add((axis, total, value, len(labels), all_sources | total_sources))
    return chains


def _matching_repeated_chains(left, right, rare_totals):
    return sorted({
        (a[1], a[2], a[3])
        for a, b in product(_repeated_span_chains(left, rare_totals), _repeated_span_chains(right, rare_totals))
        if a[:4] == b[:4] and not (a[4] & b[4])
    })


def dimension_anchors(usage, eligible_ids):
    """Find 100-point same-sheet pairs with independent dimensional structure."""
    occurrences = {
        row["group_id"]: positioned_occurrences(row) for row in usage["dimension_inventory"]
    }
    frequency = Counter(value for rows in occurrences.values() for value in {value for value, _, _ in rows})
    proofs = []
    for row in usage["dimension_graph_audit"]["dimension_similarity_candidates"]:
        a, b = row["group_id_a"], row["group_id_b"]
        if not row["same_page"] or row["dimension_similarity_score"] < 100 or not {a, b} <= eligible_ids:
            continue
        exact_extents = {
            Decimal(feature["left_mm"])
            for feature in row["features"]
            if feature["left_mm"] == feature["right_mm"]
            and Decimal(feature["left_mm"]) >= LARGE_SPAN_MM
        }
        if not exact_extents:
            continue
        extent_sources = {
            value: [(left_sources, right_sources)
                    for left_sources, right_sources in product(
                        (sources for v, _, sources in occurrences[a] if v == value),
                        (sources for v, _, sources in occurrences[b] if v == value),
                    ) if not left_sources & right_sources]
            for value in exact_extents
        }
        rare_extents = {value for value in exact_extents if frequency[value] == 2}
        confirmed_extents = sorted(value for value, sources in extent_sources.items() if sources)
        confirmed_rare = [value for value in confirmed_extents if value in rare_extents]
        left_chains = neighbor_spans(occurrences[a], rare_extents)
        right_chains = neighbor_spans(occurrences[b], rare_extents)
        corroboration = {
            chain: {
                value for value in confirmed_extents if any(
                    not (left_chain & right_chain or left_chain & left_extent or right_chain & right_extent
                         or left_chain & right_extent or right_chain & left_extent)
                    for left_extent, right_extent in extent_sources[value]
                    for left_chain, right_chain in product(left_chains[chain], right_chains[chain])
                )
            }
            for chain in left_chains.keys() & right_chains.keys()
        }
        corroborating = sorted(chain for chain, extents in corroboration.items() if extents)
        independent_extents = any(
            not ((left_a | right_a) & (left_b | right_b))
            for i, first in enumerate(confirmed_rare) for second in confirmed_rare[i+1:]
            for (left_a, right_a), (left_b, right_b) in product(extent_sources[first], extent_sources[second])
        )
        repeated_chains = _matching_repeated_chains(occurrences[a], occurrences[b], set(confirmed_rare))
        if corroborating or independent_extents or repeated_chains:
            proofs.append({
                "group_id_a": a, "group_id_b": b,
                "relationship": "same_object_view",
                "requires_common_extent": not (
                    independent_extents or repeated_chains
                    or any(extents & rare_extents for extents in corroboration.values())
                ),
                "rare_exact_extents_mm": [str(value) for value in confirmed_rare],
                "exact_extents_mm": [str(value) for value in confirmed_extents],
                "corroborating_ordered_spans_mm": [[str(value) for value in pair] for pair in corroborating],
                "corroborating_repeated_chains": [
                    {"total_mm": str(total), "span_mm": str(span), "count": count}
                    for total, span, count in repeated_chains
                ],
            })
    return proofs
