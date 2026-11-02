"""TU Wien-inspired, evidence-only dimension graph for Estimation.

This module intentionally stops before interpreting product construction.  It
records the relationship candidates between source numbers, vector lines and
Detection-owned views so the later assembly stage never has to treat a naked
OCR number as a global object dimension.
"""

from __future__ import annotations

from collections import defaultdict
from math import hypot
import re
from typing import Any, Mapping


DIMENSION_GRAPH_V1 = "estimation_dimension_graph_v1"
_NUMBER = re.compile(r"^\s*(?:Ø\s*)?(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\s*$", re.IGNORECASE)


def _bbox(value: Any) -> dict[str, float] | None:
    if not isinstance(value, Mapping):
        return None
    try:
        left, top = float(value["top_left_x"]), float(value["top_left_y"])
        right, bottom = float(value["bottom_right_x"]), float(value["bottom_right_y"])
    except (KeyError, TypeError, ValueError):
        return None
    if right <= left or bottom <= top:
        return None
    return {"top_left_x": left, "top_left_y": top, "bottom_right_x": right, "bottom_right_y": bottom}


def _centre(box: Mapping[str, float]) -> tuple[float, float]:
    return ((box["top_left_x"] + box["bottom_right_x"]) / 2, (box["top_left_y"] + box["bottom_right_y"]) / 2)


def _distance_to_box(point: tuple[float, float], box: Mapping[str, float]) -> float:
    x, y = point
    dx = max(box["top_left_x"] - x, 0.0, x - box["bottom_right_x"])
    dy = max(box["top_left_y"] - y, 0.0, y - box["bottom_right_y"])
    return hypot(dx, dy)


def _dimension_numbers(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for block in ((payload.get("evidence") or {}).get("ocr_blocks") or []):
        if not isinstance(block, Mapping):
            continue
        match = _NUMBER.match(str(block.get("text") or ""))
        box = _bbox(block.get("bbox"))
        ref = str(block.get("block_ref") or "")
        try:
            page_number = int(block.get("page_number"))
        except (TypeError, ValueError):
            continue
        if not match or box is None or not ref or page_number < 1:
            continue
        result.append({
            "dimension_id": f"dimension-{len(result) + 1:03d}",
            "page_number": page_number,
            "raw_text": str(block["text"]),
            "numeric_value": float(match.group(1).replace(",", ".")),
            "printed_unit": (match.group(2) or "").casefold() or None,
            "bbox": box,
            "evidence_refs": [ref],
            "source": str(block.get("source") or "ocr"),
        })
    return result


def _views(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    views = []
    for page in ((payload.get("object") or {}).get("evidence_pages") or []):
        if not isinstance(page, Mapping):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        for index, region in enumerate(page.get("regions") or [], start=1):
            box = _bbox(region)
            if box is None:
                continue
            views.append({"view_id": f"p{page_number}-view-{index:03d}", "page_number": page_number, "bbox": box})
    return views


def _page_capabilities(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    context = ((payload.get("evidence") or {}).get("geometry_context") or {})
    by_page = {
        int(item.get("page_number")): item
        for item in context.get("page_profiles") or []
        if isinstance(item, Mapping) and str(item.get("page_number") or "").isdigit()
    }
    result = []
    for page_number, profile in sorted(by_page.items()):
        raw_metrics = profile.get("raw_metrics") or {}
        result.append({
            "page_number": page_number,
            "representation": profile.get("representation"),
            "coordinate_evidence": profile.get("coordinate_evidence"),
            "eligible_mechanisms": list(profile.get("eligible_mechanisms") or []),
            "native_text_span_count": raw_metrics.get("native_text_span_count"),
            "vector_primitive_count": raw_metrics.get("vector_primitive_count"),
            "vector_summary_status": raw_metrics.get("vector_summary_status"),
        })
    return result


def _vector_line_candidates(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    context = ((payload.get("evidence") or {}).get("geometry_context") or {})
    result = []
    for item in context.get("vector_line_segments") or []:
        if not isinstance(item, Mapping):
            continue
        try:
            page_number = int(item.get("page_number"))
            x1, y1 = float((item.get("start") or {})["x"]), float((item.get("start") or {})["y"])
            x2, y2 = float((item.get("end") or {})["x"]), float((item.get("end") or {})["y"])
        except (KeyError, TypeError, ValueError):
            continue
        segment_id = str(item.get("segment_id") or "").strip()
        if not segment_id or page_number < 1 or (x1 == x2 and y1 == y2):
            continue
        result.append({
            "segment_id": segment_id, "page_number": page_number,
            "orientation": str(item.get("orientation") or "unknown"),
            "start": {"x": x1, "y": y1}, "end": {"x": x2, "y": y2},
            "coordinate_basis": str(item.get("coordinate_basis") or "native_pdf_vector"),
        })
    return result


def _distance_to_segment(point: tuple[float, float], segment: Mapping[str, Any]) -> float:
    x, y = point
    start, end = segment["start"], segment["end"]
    x1, y1, x2, y2 = start["x"], start["y"], end["x"], end["y"]
    dx, dy = x2 - x1, y2 - y1
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return hypot(x - x1, y - y1)
    ratio = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length_squared))
    return hypot(x - (x1 + ratio * dx), y - (y1 + ratio * dy))


def build_dimension_graph(*, input_row: Mapping[str, Any]) -> dict[str, Any]:
    """Build an auditable graph without claiming construction or an axis.

    A spatial nearest-view or number-to-native-line relation is deliberately a
    candidate, not a proof that the number measures that view. Arrowheads,
    line pairs, axes and construction remain unresolved here.
    """
    payload = input_row.get("input_payload") or {}
    if payload.get("contract_version") != "estimation_input_v4":
        raise ValueError("dimension graph requires estimation_input_v4")
    views = _views(payload)
    numbers = _dimension_numbers(payload)
    vector_lines = _vector_line_candidates(payload)
    views_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for view in views:
        views_by_page[int(view["page_number"])].append(view)
    lines_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for line in vector_lines:
        lines_by_page[int(line["page_number"])].append(line)
    links = []
    for number in numbers:
        point = _centre(number["bbox"])
        candidates = views_by_page[int(number["page_number"])]
        if not candidates:
            pass
        else:
            nearest = min(candidates, key=lambda view: (_distance_to_box(point, view["bbox"]), view["view_id"]))
            links.append({
                "relation_id": f"near-{number['dimension_id']}",
                "from_dimension_id": number["dimension_id"],
                "to_view_id": nearest["view_id"],
                "relation": "nearest_view_candidate",
                "distance_px": round(_distance_to_box(point, nearest["bbox"]), 3),
                "basis": "coordinate_proximity",
            })
        line_candidates = lines_by_page[int(number["page_number"])]
        if line_candidates:
            nearest_line = min(
                line_candidates,
                key=lambda line: (_distance_to_segment(point, line), line["segment_id"]),
            )
            distance = _distance_to_segment(point, nearest_line)
            if distance <= 120:
                links.append({
                    "relation_id": f"line-{number['dimension_id']}",
                    "from_dimension_id": number["dimension_id"],
                    "to_segment_id": nearest_line["segment_id"],
                    "relation": "number_to_vector_line_candidate",
                    "distance_px": round(distance, 3),
                    "basis": "source_vector_line_proximity",
                })
    object_payload = payload.get("object") or {}
    return {
        "contract_version": DIMENSION_GRAPH_V1,
        "input_id": str(input_row.get("input_id") or ""),
        "object_input_revision": int(input_row.get("object_input_revision") or 1),
        "run_id": str(payload.get("run_id") or ""),
        "company_id": str(payload.get("company_id") or ""),
        "object_id": str(object_payload.get("object_id") or ""),
        "object_name": str(object_payload.get("object_name") or ""),
        "quantity": object_payload.get("quantity") or 1,
        "status": "ready",
        "page_capabilities": _page_capabilities(payload),
        "views": views,
        "vector_line_candidates": vector_lines,
        "dimension_numbers": numbers,
        "relations": links,
        "limitations": [
            "number-to-view and number-to-vector-line relations are candidates, not dimension-line proofs",
            "this result contains no construction, material, catalog, price or production claim",
        ],
    }
