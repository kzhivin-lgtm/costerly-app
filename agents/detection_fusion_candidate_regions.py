"""Deterministic visual recall candidates derived inside Evidence Fusion.

Candidate regions are not Islands and never decide object identity. They are
Mistral graphic areas enriched with MyPDF/Mistral source facts. When Mistral
finds no graphic area on a content page, spatial source-fact clusters provide
a conservative recall fallback for Registry's full-page inspection.
"""

from __future__ import annotations

from typing import Any

from agents.pdf_page_inspection import compact_page_profile_audit


_BBOX_KEYS = (
    "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
)
# 500 px at the rendered 200 dpi is about 64 mm: enough to keep a sparse
# dimension grid together without bridging separated drawing areas.
_TEXT_CLUSTER_GAP_PX = 500
_TEXT_CLUSTER_MIN_FACTS = 2
_TEXT_CLUSTER_MIN_WIDTH_RATIO = 0.18
_TEXT_CLUSTER_MIN_HEIGHT_RATIO = 0.30
_TEXT_CLUSTER_PADDING_PX = 80


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        result = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    if (
        result["bottom_right_x"] <= result["top_left_x"]
        or result["bottom_right_y"] <= result["top_left_y"]
    ):
        return None
    return result


def _centre_inside(point_bbox: dict[str, int], area_bbox: dict[str, int]) -> bool:
    x = (point_bbox["top_left_x"] + point_bbox["bottom_right_x"]) / 2
    y = (point_bbox["top_left_y"] + point_bbox["bottom_right_y"]) / 2
    return (
        area_bbox["top_left_x"] <= x <= area_bbox["bottom_right_x"]
        and area_bbox["top_left_y"] <= y <= area_bbox["bottom_right_y"]
    )


def _centre(bbox: dict[str, int]) -> tuple[float, float]:
    return (
        (bbox["top_left_x"] + bbox["bottom_right_x"]) / 2,
        (bbox["top_left_y"] + bbox["bottom_right_y"]) / 2,
    )


def _page_dimensions(page: dict[str, Any], facts: list[dict[str, Any]]) -> tuple[int, int]:
    dimensions = page.get("dimensions") if isinstance(page.get("dimensions"), dict) else {}
    for width_key, height_key in (("width", "height"), ("image_width", "image_height")):
        try:
            width, height = int(dimensions[width_key]), int(dimensions[height_key])
        except (KeyError, TypeError, ValueError):
            continue
        if width > 0 and height > 0:
            return width, height
    max_x = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_x", 0) for fact in facts), default=0)
    max_y = max(((_bbox(fact.get("bbox")) or {}).get("bottom_right_y", 0) for fact in facts), default=0)
    return max(1, max_x), max(1, max_y)


def _text_cluster_candidates(
    *,
    page_number: int,
    page: dict[str, Any],
    source_facts: list[dict[str, Any]],
    ordinal: int,
) -> list[dict[str, Any]]:
    """Build broad recall boxes from disconnected Fusion text clusters.

    This is deliberately only used when Mistral supplied no graphic region for
    the page. A cluster is a recall hint, so broad boxes are acceptable, while
    every final Island and fact owner remains decided later by Registry/code.
    """
    entries = [
        (fact, bbox)
        for fact in source_facts
        if fact.get("page_number") == page_number
        if (bbox := _bbox(fact.get("bbox"))) is not None
    ]
    if len(entries) < _TEXT_CLUSTER_MIN_FACTS:
        return []
    remaining = set(range(len(entries)))
    components: list[list[int]] = []
    while remaining:
        component = {remaining.pop()}
        frontier = list(component)
        while frontier:
            current = frontier.pop()
            current_x, current_y = _centre(entries[current][1])
            adjacent = [
                index for index in remaining
                if max(
                    abs(current_x - _centre(entries[index][1])[0]),
                    abs(current_y - _centre(entries[index][1])[1]),
                ) <= _TEXT_CLUSTER_GAP_PX
            ]
            for index in adjacent:
                remaining.remove(index)
                component.add(index)
                frontier.append(index)
        if len(component) >= _TEXT_CLUSTER_MIN_FACTS:
            components.append(sorted(component))

    page_width, page_height = _page_dimensions(page, [fact for fact, _ in entries])
    min_width = max(1, round(page_width * _TEXT_CLUSTER_MIN_WIDTH_RATIO))
    min_height = max(1, round(page_height * _TEXT_CLUSTER_MIN_HEIGHT_RATIO))
    candidates: list[dict[str, Any]] = []
    for indexes in sorted(components, key=lambda values: (
        min(entries[index][1]["top_left_y"] for index in values),
        min(entries[index][1]["top_left_x"] for index in values),
    )):
        boxes = [entries[index][1] for index in indexes]
        left = min(box["top_left_x"] for box in boxes) - _TEXT_CLUSTER_PADDING_PX
        top = min(box["top_left_y"] for box in boxes) - _TEXT_CLUSTER_PADDING_PX
        right = max(box["bottom_right_x"] for box in boxes) + _TEXT_CLUSTER_PADDING_PX
        bottom = max(box["bottom_right_y"] for box in boxes) + _TEXT_CLUSTER_PADDING_PX
        centre_x, centre_y = (left + right) / 2, (top + bottom) / 2
        left = round(centre_x - max(min_width, right - left) / 2)
        right = round(centre_x + max(min_width, right - left) / 2)
        top = round(centre_y - max(min_height, bottom - top) / 2)
        bottom = round(centre_y + max(min_height, bottom - top) / 2)
        bbox = {
            "top_left_x": max(0, left),
            "top_left_y": max(0, top),
            "bottom_right_x": min(page_width, right),
            "bottom_right_y": min(page_height, bottom),
        }
        if bbox["bottom_right_x"] <= bbox["top_left_x"] or bbox["bottom_right_y"] <= bbox["top_left_y"]:
            continue
        ordinal += 1
        candidates.append({
            "candidate_region_id": f"CR-P{page_number:03d}-{ordinal:03d}",
            "page_number": page_number,
            "bbox": bbox,
            "basis": "fusion_text_cluster",
            "source_fact_ids": [str(entries[index][0]["fact_id"]) for index in indexes],
        })
    return candidates


def build_detection_fusion_candidate_regions(
    ocr_package: dict[str, Any] | None,
    source_facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return stable, source-enriched graphic or fallback text-cluster regions."""
    candidates: list[dict[str, Any]] = []
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number < 1:
            continue
        ordinal = 0
        for block in page.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            bbox = _bbox(block)
            if bbox is None:
                continue
            ordinal += 1
            source_fact_ids = [
                str(fact["fact_id"])
                for fact in source_facts
                if (
                    fact.get("page_number") == page_number
                    and (fact_bbox := _bbox(fact.get("bbox"))) is not None
                    and _centre_inside(fact_bbox, bbox)
                )
            ]
            candidates.append({
                "candidate_region_id": f"CR-P{page_number:03d}-{ordinal:03d}",
                "page_number": page_number,
                "bbox": bbox,
                "basis": "mistral_graphic_region",
                "source_fact_ids": source_fact_ids,
            })
        if ordinal == 0:
            candidates.extend(_text_cluster_candidates(
                page_number=page_number, page=page, source_facts=source_facts,
                ordinal=ordinal,
            ))
    return candidates


def build_detection_fusion_page_profile_audit(
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Expose passive per-page PDF capability data beside Fusion's output.

    V6.1 deliberately does not use profiles to add, remove or change a
    Candidate Region. The audit reaches the same Fusion operation so later
    routing can be calibrated against real benchmark documents without
    changing today's Island or package behaviour.
    """
    return compact_page_profile_audit(ocr_package)


def format_detection_fusion_candidate_regions(
    candidates: list[dict[str, Any]],
) -> str:
    """Append the compact recall layer to the single Fusion handoff."""
    if not candidates:
        return "CANDIDATE REGIONS: no usable Fusion recall regions."
    lines = [
        "CANDIDATE REGIONS (Fusion recall aid, not Islands):",
        "CR=id|P=page|B=x1,y1,x2,y2|K=recall basis|SF=source facts inside region.",
    ]
    for candidate in candidates:
        bbox = candidate["bbox"]
        facts = ",".join(candidate["source_fact_ids"]) or "-"
        lines.append(
            f"{candidate['candidate_region_id']}|P{candidate['page_number']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},"
            f"{bbox['bottom_right_x']},{bbox['bottom_right_y']}|"
            f"K={candidate['basis']}|SF={facts}"
        )
    return "\n".join(lines)


def format_detection_candidate_pair_queue(
    candidates: list[dict[str, Any]],
    baskets: list[list[str]] | None = None,
) -> str:
    """Format deterministic proto-region comparisons for the Registry call.

    The queue is deliberately evidence, not an identity decision.  Registry
    may return semantic facts only for its mapped final Islands.
    """
    if not candidates:
        return "CANDIDATE PAIR QUEUE: no comparable Candidate Regions."
    lines = [
        "CANDIDATE PAIR QUEUE (Q, deterministic Dimension candidates):",
        "Q=id|A=Candidate Region|B=Candidate Region|DS=dimension score|C=cycle.",
        "For every Q pair, inspect all five semantic criteria.  Return a positive "
        "semantic fact only when its final Islands map to the two Q endpoints.",
    ]
    for index, candidate in enumerate(candidates, start=1):
        lines.append(
            f"Q{index:03d}|A={candidate['group_id_a']}|B={candidate['group_id_b']}|"
            f"DS={float(candidate.get('dimension_similarity_score') or 0):.3f}|"
            f"C={candidate.get('cycle') or 'discovery'}"
        )
    for index, basket in enumerate(baskets or [], start=1):
        if len(basket) > 1:
            lines.append(f"B{index:03d}|MEMBERS={','.join(sorted(basket))}")
    return "\n".join(lines)
