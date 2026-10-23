from __future__ import annotations

import re
from typing import Any


_BBOX_KEYS = (
    "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
)
_DIMENSION_TOKEN_RE = re.compile(
    r"(?<![A-Za-zА-Яа-я])(?:[1-9]\d{2,}|\d+(?:[.,]\d+)?\s*(?:mm|cm|m|in|ft))\b",
    re.IGNORECASE,
)


def _valid_bbox(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    try:
        left, top, right, bottom = (int(value[key]) for key in _BBOX_KEYS)
    except (KeyError, TypeError, ValueError):
        return False
    return left >= 0 and top >= 0 and right > left and bottom > top


def _nearby_text_clusters(facts: list[dict[str, Any]]) -> int:
    """Count annotations, not separate OCR lines within one annotation."""
    boxes = [fact["bbox"] for fact in facts]
    clusters: list[list[dict[str, Any]]] = []
    for bbox in boxes:
        for cluster in clusters:
            if any(
                bbox["top_left_x"] <= existing["bottom_right_x"] + 48
                and existing["top_left_x"] <= bbox["bottom_right_x"] + 48
                and bbox["top_left_y"] <= existing["bottom_right_y"] + 48
                and existing["top_left_y"] <= bbox["bottom_right_y"] + 48
                for existing in cluster
            ):
                cluster.append(bbox)
                break
        else:
            clusters.append([bbox])
    return len(clusters)


def assess_detection_source_capability(
    *,
    source_facts: list[dict[str, Any]],
    page_count: int,
    page_dimensions: dict[int, tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Decide whether a document has enough coordinate evidence for V5.

    The ordinary V5 path needs more than a page footer or an isolated note. A
    page contributes usable spatial evidence when it has a coordinate-bearing
    dimension-like literal, or two distinct local text facts. This is a
    source-capability decision, never a document-type or filename rule.
    """
    if page_count < 1:
        raise ValueError("source capability requires at least one page")

    facts_by_page: dict[int, list[dict[str, Any]]] = {
        page_number: [] for page_number in range(1, page_count + 1)
    }
    for fact in source_facts:
        if not isinstance(fact, dict):
            continue
        page_number = fact.get("page_number")
        if not isinstance(page_number, int) or page_number not in facts_by_page:
            continue
        if not _valid_bbox(fact.get("bbox")):
            continue
        text = " ".join(str(fact.get("text") or "").split())
        if text:
            facts_by_page[page_number].append({**fact, "text": text})

    page_audit: list[dict[str, Any]] = []
    capable_pages: list[int] = []
    for page_number in range(1, page_count + 1):
        facts = facts_by_page[page_number]
        width, height = (page_dimensions or {}).get(page_number, (0, 0))
        non_footer_facts = [
            fact for fact in facts
            if height <= 0
            or int(fact["bbox"]["top_left_y"]) < round(height * 0.88)
        ]
        dimension_facts = [
            fact for fact in non_footer_facts
            if _DIMENSION_TOKEN_RE.search(str(fact.get("text") or ""))
        ]
        # Two independently positioned annotations are sufficient to retain
        # the normal V5 evidence path even when neither one is a dimension.
        local_facts = [
            fact for fact in non_footer_facts
            if (
                width <= 0 or height <= 0
                or (
                    int(fact["bbox"]["bottom_right_y"]) > round(height * 0.12)
                    and int(fact["bbox"]["top_left_y"]) < round(height * 0.88)
                )
            )
        ]
        local_cluster_count = _nearby_text_clusters(local_facts)
        usable = bool(dimension_facts) or local_cluster_count >= 2
        if usable:
            capable_pages.append(page_number)
        page_audit.append({
            "page_number": page_number,
            "coordinate_fact_count": len(facts),
            "dimension_like_fact_count": len(dimension_facts),
            "localized_fact_position_count": local_cluster_count,
            "has_usable_spatial_evidence": usable,
        })

    all_pages = set(range(1, page_count + 1))
    capable = set(capable_pages)
    route_eligible = not capable
    return {
        "contract_version": "v5_12_source_capability_v1",
        "page_count": page_count,
        "source_fact_count": sum(len(facts) for facts in facts_by_page.values()),
        "capable_page_numbers": sorted(capable),
        "source_degraded_page_numbers": sorted(all_pages - capable),
        "mixed_evidence_document": bool(capable) and capable != all_pages,
        "route_eligible": route_eligible,
        "route_reason": (
            "all_pages_lack_usable_coordinate_evidence"
            if route_eligible
            else "ordinary_v5_retains_usable_coordinate_evidence"
        ),
        "pages": page_audit,
    }


def validate_detection_visual_only_partitions(
    partitions: object,
    *,
    object_view_ids: set[str],
) -> list[dict[str, Any]]:
    """Validate a complete visual-only partition and its cited visual tree."""
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("visual-only membership must contain object partitions")
    seen_view_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    allowed_types = {
        "complete_physical_envelope",
        "direct_continuity",
        "alternate_projection",
        "visible_author_label",
        "matching_unique_structure",
        "compatible_dimensions",
    }
    generic_markers = (
        "same page", "same material", "same colour", "same color",
        "same frame type", "nearby", "adjacent", "similar size",
    )
    for index, partition in enumerate(partitions, start=1):
        if not isinstance(partition, dict) or set(partition) != {
            "group_ids", "visual_basis",
        }:
            raise ValueError("visual-only partition fields are invalid")
        group_ids = partition.get("group_ids")
        bases = partition.get("visual_basis")
        if (
            not isinstance(group_ids, list) or not group_ids
            or len(group_ids) != len(set(group_ids))
            or not all(isinstance(group_id, str) and group_id in object_view_ids for group_id in group_ids)
            or not isinstance(bases, list) or not bases
        ):
            raise ValueError("visual-only partition references are invalid")
        duplicate_ids = seen_view_ids.intersection(group_ids)
        if duplicate_ids:
            raise ValueError("visual-only partition duplicates an object view")
        seen_view_ids.update(group_ids)

        adjacency = {group_id: set() for group_id in group_ids}
        normalized_bases: list[dict[str, Any]] = []
        for basis in bases:
            if not isinstance(basis, dict) or set(basis) != {
                "evidence_type", "view_ids", "observation",
            }:
                raise ValueError("visual-only basis fields are invalid")
            evidence_type = basis.get("evidence_type")
            view_ids = basis.get("view_ids")
            observation = " ".join(str(basis.get("observation") or "").split())
            if (
                evidence_type not in allowed_types
                or not isinstance(view_ids, list) or not view_ids
                or len(view_ids) != len(set(view_ids))
                or not set(view_ids).issubset(group_ids)
                or len(observation) < 12
                or any(marker in observation.lower() for marker in generic_markers)
            ):
                raise ValueError("visual-only basis is invalid or generic")
            if len(group_ids) == 1:
                if evidence_type != "complete_physical_envelope" or view_ids != group_ids:
                    raise ValueError("visual-only singleton requires its complete envelope")
            elif len(view_ids) < 2:
                raise ValueError("visual-only multi-view basis must connect two views")
            for left in view_ids:
                for right in view_ids:
                    if left != right:
                        adjacency[left].add(right)
            normalized_bases.append({
                "evidence_type": evidence_type,
                "view_ids": list(view_ids),
                "observation": observation,
            })

        if len(group_ids) > 1:
            reached = {group_ids[0]}
            frontier = [group_ids[0]]
            while frontier:
                current = frontier.pop()
                for neighbour in adjacency[current] - reached:
                    reached.add(neighbour)
                    frontier.append(neighbour)
            if reached != set(group_ids):
                raise ValueError("visual-only multi-view bases do not connect the partition")
        normalized.append({
            "object_index": index,
            "group_ids": list(group_ids),
            "visual_basis": normalized_bases,
        })
    if seen_view_ids != object_view_ids:
        raise ValueError("visual-only membership must account for every object view")
    return normalized
