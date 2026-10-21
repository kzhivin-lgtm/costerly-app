"""Deterministic visual recall candidates derived inside Evidence Fusion.

Candidate regions are not Islands and never decide object identity.  They are
Mistral graphic areas enriched with the MyPDF/Mistral source facts that fall in
the same page area.  Registry uses them only for its post-visual recall check.
"""

from __future__ import annotations

from typing import Any


_BBOX_KEYS = (
    "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
)


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


def build_detection_fusion_candidate_regions(
    ocr_package: dict[str, Any] | None,
    source_facts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return stable, source-enriched Mistral graphic regions per page."""
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
    return candidates


def format_detection_fusion_candidate_regions(
    candidates: list[dict[str, Any]],
) -> str:
    """Append the compact recall layer to the single Fusion handoff."""
    if not candidates:
        return "CANDIDATE REGIONS: no usable Mistral graphic regions."
    lines = [
        "CANDIDATE REGIONS (Fusion recall aid, not Islands):",
        "CR=id|P=page|B=x1,y1,x2,y2|SF=source facts inside region.",
    ]
    for candidate in candidates:
        bbox = candidate["bbox"]
        facts = ",".join(candidate["source_fact_ids"]) or "-"
        lines.append(
            f"{candidate['candidate_region_id']}|P{candidate['page_number']}|"
            f"B={bbox['top_left_x']},{bbox['top_left_y']},"
            f"{bbox['bottom_right_x']},{bbox['bottom_right_y']}|SF={facts}"
        )
    return "\n".join(lines)


def format_detection_candidate_pair_queue(
    candidates: list[dict[str, Any]],
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
    return "\n".join(lines)
