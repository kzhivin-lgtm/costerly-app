"""Source-local evidence enrichment of Dimension Graph, not new Detection.

One bounded CPU pass per supplied page at Analyze. No model/network requests,
polling or global cache. Raster lines and native lines remain candidates, never
proof of dimension-line endpoints or physical component ownership.
"""
from __future__ import annotations

from copy import deepcopy
from collections import defaultdict
from io import BytesIO
from math import hypot
import re
from typing import Any, Mapping

import numpy as np
from PIL import Image

from use_cases.estimation_dimension_graph import build_dimension_graph, source_coordinate_frame
from use_cases.estimation_dimension_scale import build_dimension_scale_gate

EVIDENCE_MAP_VERSION = "estimation_evidence_map_v1"
MAX_RASTER_SIDE = 2200
MAX_LINES = 3000
_INDEX = re.compile(r"\b[A-Z]{1,4}[-.]?\d{1,4}\b", re.IGNORECASE)


def _raster_lines(data: bytes, text_boxes: tuple = ()) -> tuple[list[dict], tuple[int, int], bool]:
    with Image.open(BytesIO(data)) as source:
        image = source.convert("RGB")
    image.thumbnail((MAX_RASTER_SIDE, MAX_RASTER_SIDE))
    pixels = np.asarray(image)
    # Include light CAD dimension strokes and coloured annotations. Text strokes
    # are not silently classified as dimension lines: topology is still pending.
    ink = pixels.min(axis=2) < 235
    lines = []
    for orientation, plane in (("horizontal", ink), ("vertical", ink.T)):
        closed = plane.copy()
        closed[:, 1:-1] |= plane[:, :-2] & plane[:, 2:]
        for perpendicular, row in enumerate(closed):
            changes = np.diff(np.pad(row.astype(np.int8), (1, 1)))
            starts, ends = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1) - 1
            for start, end in zip(starts, ends):
                if end - start < 12:
                    continue
                # Merge neighbouring scan rows of the SAME stroke only.
                duplicate = next((line for line in reversed(lines[-60:])
                    if line["orientation"] == orientation and 0 <= perpendicular - line["p"] <= 3
                    and abs(start - line["a"]) <= 3 and abs(end - line["b"]) <= 3), None)
                if duplicate is not None:
                    continue
                lines.append({"orientation": orientation, "p": int(perpendicular), "a": int(start), "b": int(end)})
    truncated = len(lines) > MAX_LINES
    # Never conceal truncation. Long strokes only are retained if page density
    # exceeds the bound; a short unavailable dimension remains unresolved.
    if truncated:
        lines = sorted(lines, key=lambda line: line["b"] - line["a"], reverse=True)[:MAX_LINES]
    result = []
    for index, line in enumerate(lines, 1):
        horizontal = line["orientation"] == "horizontal"
        x1, y1 = (line["a"], line["p"]) if horizontal else (line["p"], line["a"])
        x2, y2 = (line["b"], line["p"]) if horizontal else (line["p"], line["b"])
        # Reject strokes wholly contained in OCR labels, but never erase a
        # text bounding box from the image: OCR boxes can cross a real line.
        if any(left * image.width - 1 <= x1 <= right * image.width + 1
               and left * image.width - 1 <= x2 <= right * image.width + 1
               and top * image.height - 1 <= y1 <= bottom * image.height + 1
               and top * image.height - 1 <= y2 <= bottom * image.height + 1
               for left, top, right, bottom in text_boxes):
            continue
        result.append({"segment_id": f"raster-{index:04d}", "orientation": line["orientation"],
            "start": {"x": x1, "y": y1}, "end": {"x": x2, "y": y2},
            "coordinate_basis": "raster_line_candidate"})
    # A continuous chain dimension has intermediate extension lines. Preserve
    # its subspans as candidates instead of treating the whole chain as each
    # printed dimension. T-junctions on furniture are also candidates, not proof.
    spans = []
    for line in result:
        horizontal = line["orientation"] == "horizontal"
        axis, other = ("x", "y") if horizontal else ("y", "x")
        a, b = line["start"][axis], line["end"][axis]
        p = line["start"][other]
        breaks = sorted({cross["start"][axis] for cross in result
            if cross["orientation"] != line["orientation"] and a + 4 < cross["start"][axis] < b - 4
            and min(cross["start"][other], cross["end"][other]) - 3 <= p
                <= max(cross["start"][other], cross["end"][other]) + 3})
        deduped = []
        for value in breaks:
            if not deduped or value - deduped[-1] > 4:
                deduped.append(value)
        for index, (left, right) in enumerate(zip([a, *deduped], [*deduped, b])):
            if not deduped or right - left < 12:
                continue
            spans.append({**line, "segment_id": f"{line['segment_id']}-span-{index}",
                "start": {axis: left, other: p}, "end": {axis: right, other: p}})
    return result + spans[:MAX_LINES], image.size, truncated or len(spans) > MAX_LINES


def _line_candidates(number: Mapping, lines: list[dict], frame: tuple[float, float]) -> list[dict]:
    box = number["bbox"]
    center = ((box["top_left_x"] + box["bottom_right_x"]) / 2,
              (box["top_left_y"] + box["bottom_right_y"]) / 2)
    candidates = []
    for line in lines:
        if line["orientation"] not in {"horizontal", "vertical"}:
            continue
        h = line["orientation"] == "horizontal"
        axis, other = ("x", "y") if h else ("y", "x")
        a, b = sorted((line["start"][axis], line["end"][axis]))
        p = (line["start"][other] + line["end"][other]) / 2
        along, across = center if h else center[::-1]
        gap = max(a - along, 0, along - b)
        distance = abs(across - p)
        # Relative page-coordinate bounds, not furniture dimensions.
        if distance > min(frame) * .025 or gap > max(frame) * .04:
            continue
        score = distance + gap * 2
        if "-span-" in line["segment_id"] and gap == 0:
            score -= 1  # Prefer a bounded chain interval over its whole stroke.
        endpoints = [line["start"], line["end"]]
        supports = []
        for point in endpoints:
            crossing = [other_line["segment_id"] for other_line in lines
                if other_line["orientation"] in {"horizontal", "vertical"} and other_line["orientation"] != line["orientation"]
                and abs(other_line["start"][axis] - point[axis]) <= min(frame) * .004
                and min(other_line["start"][other], other_line["end"][other]) - min(frame) * .004 <= point[other]
                    <= max(other_line["start"][other], other_line["end"][other]) + min(frame) * .004]
            supports.append(crossing[:3])
        candidates.append((score, {**line, "endpoint_crossing_candidates": supports,
                                   "distance_to_label": round(hypot(distance, gap), 2)}))
    return [line for _, line in sorted(candidates, key=lambda entry: (entry[0], entry[1]["segment_id"]))[:3]]


def build_evidence_map(*, input_row: Mapping[str, Any], page_bytes_by_ref: Mapping[str, bytes],
                       page_cache: dict | None = None) -> dict[str, Any]:
    """Enrich immutable graph facts; return explicit unavailable/ambiguous states."""
    graph = build_dimension_graph(input_row=input_row)
    payload = input_row["input_payload"]
    cache = page_cache if page_cache is not None else {}
    scale = build_dimension_scale_gate(dimension_graph=graph)
    convention = (scale.get("decision") or {}).get("required_unit")
    artifacts = {a["page_number"]: a for a in (payload.get("evidence") or {}).get("artifacts") or []
                 if a.get("artifact_kind") == "page" and a.get("storage_ref") and a.get("page_number")}
    pages, numbers = [], []
    for page_number in sorted({n["page_number"] for n in graph["dimension_numbers"]}):
        frame = source_coordinate_frame(payload, page_number)
        ref = (artifacts.get(page_number) or {}).get("storage_ref")
        lines, status, truncated = [], "coordinate_frame_unavailable", False
        if frame:
            lines = [deepcopy(line) for line in graph["vector_line_candidates"] if line["page_number"] == page_number
                     and line["coordinate_basis"] == "native_pdf_vector_rendered_pixels"]
            if lines:
                status = "native_candidates"
            elif ref in page_bytes_by_ref:
                try:
                    boxes = tuple(sorted({tuple(float(block["bbox"][key]) / frame[i % 2]
                        for i, key in enumerate(("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")))
                        for container in ("evidence", "document_context")
                        for block in (payload.get(container) or {}).get("ocr_blocks") or []
                        if block.get("page_number") == page_number and block.get("bbox")
                        and all(key in block["bbox"] for key in ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y"))}))
                    cache_key = (ref, boxes)
                    if cache_key not in cache:
                        cache[cache_key] = _raster_lines(page_bytes_by_ref[ref], boxes)
                    raster, size, truncated = cache[cache_key]
                    for line in raster:
                        converted = deepcopy(line)
                        converted["segment_id"] = f"p{page_number}-{line['segment_id']}"
                        for end in ("start", "end"):
                            converted[end] = {axis: round(line[end][axis] * frame[i] / size[i], 3)
                                              for i, axis in enumerate(("x", "y"))}
                        lines.append(converted)
                    status = "raster_candidates" if lines else "no_lines_found"
                except (OSError, ValueError):
                    status = "image_unreadable"
            else:
                status = "page_image_unavailable"
        pages.append({"page_number": page_number, "source_ref": ref, "coordinate_frame": frame,
                      "line_status": status, "line_count": len(lines), "truncated": truncated})
        for number in (n for n in graph["dimension_numbers"] if n["page_number"] == page_number):
            unit = number.get("printed_unit") or convention
            candidates = _line_candidates(number, lines, frame) if frame else []
            numbers.append({**number, "interpreted_value_mm": number["numeric_value"] * {"mm": 1, "cm": 10, "m": 1000}[unit] if unit else None,
                "unit_basis": "explicit_source" if number.get("printed_unit") else "scale_policy_assumption",
                "line_candidates": candidates,
                "view_candidates": [r["to_view_id"] for r in graph["relations"]
                    if r.get("from_dimension_id") == number["dimension_id"] and r.get("to_view_id")],
                "ownership_status": "unresolved"})
    texts = {}
    indexes = defaultdict(list)
    for container in ("evidence", "document_context"):
        for kind in ("ocr_blocks", "ocr_literal_items"):
            for block in (payload.get(container) or {}).get(kind) or []:
                ref = block.get("block_ref")
                if not ref or ref in texts or not str(block.get("text") or "").strip():
                    continue
                texts[ref] = {key: deepcopy(block[key]) for key in ("block_ref", "page_number", "text", "bbox", "source") if key in block}
                for token in sorted(set(_INDEX.findall(str(block["text"]).upper()))):
                    indexes[token].append(ref)
    return {"contract_version": EVIDENCE_MAP_VERSION, "input_id": graph["input_id"],
        "views": graph["views"], "pages": pages, "dimensions": numbers,
        "text_nodes": list(texts.values()),
        "index_links": [{"index": token, "evidence_refs": refs, "relation": "same_literal_index_candidate"}
                        for token, refs in sorted(indexes.items()) if len(refs) > 1],
        "dimension_scale_gate": scale,
        "limitations": ["Line endpoints are stroke endpoints, not verified arrowheads or physical boundaries.",
                        "Nearest views and crossing strokes are candidates only. Ownership requires visual interpretation.",
                        "No measurement may be inferred from pixel length without a separate scale/geometry witness."]}


def interpret_evidence_map(raw: Mapping[str, Any], *, source_map: Mapping[str, Any], zone_ids: set[str]) -> dict[str, Any]:
    """Validate references, never certify a model's physical interpretation."""
    if not isinstance(raw, Mapping):
        raise ValueError("Analyze requires evidence_readings before construction")
    source_views = {view["view_id"]: view for view in source_map["views"]}
    numbers = {number["dimension_id"]: number for number in source_map["dimensions"]}
    projections = {"front_elevation", "side_elevation", "top_plan", "section", "isometric", "unknown"}
    views, readings, seen = [], [], set()
    for view in raw.get("views") or []:
        vid = view.get("view_id")
        if vid not in source_views or vid in seen or view.get("projection") not in projections:
            raise ValueError("evidence map has an unknown/duplicate view or projection")
        if view.get("horizontal_axis") not in {None, "width", "depth"}:
            raise ValueError("evidence map has an invalid view axis")
        seen.add(vid)
        views.append({"view_id": vid, "projection": view["projection"], "horizontal_axis": view.get("horizontal_axis")})
    if set(source_views) != seen:
        raise ValueError("evidence map must acknowledge each source view, unknown is permitted")
    seen = set()
    for reading in raw.get("dimensions") or []:
        did, vid = reading.get("dimension_id"), reading.get("view_id")
        zone, axis = reading.get("scope_id"), reading.get("axis")
        if did not in numbers or did in seen or vid not in source_views:
            raise ValueError("evidence map dimension/view is unknown or duplicated")
        number = numbers[did]
        if number["page_number"] != source_views[vid]["page_number"]:
            raise ValueError("evidence map dimension cannot belong to a different page view")
        if zone is not None and zone not in zone_ids:
            raise ValueError("evidence map cannot invent a construction zone")
        if axis not in {None, "width", "height", "depth", "thickness"}:
            raise ValueError("evidence map has an invalid dimension axis")
        orientation = reading.get("local_orientation")
        if orientation not in {"horizontal", "vertical", "unknown"}:
            raise ValueError("evidence map requires local dimension orientation")
        candidate_id = reading.get("candidate_id")
        candidate = next((c for c in number["line_candidates"] if c["segment_id"] == candidate_id), None)
        if candidate_id is not None and (candidate is None or candidate["orientation"] != orientation):
            raise ValueError("evidence map has an unknown or contradictory line candidate")
        between = reading.get("between")
        if not isinstance(between, list) or len(between) != 2 or not all(isinstance(s, str) and s.strip() for s in between):
            raise ValueError("evidence map requires two described physical boundaries")
        seen.add(did)
        readings.append({"dimension_id": did, "view_id": vid, "scope_id": zone, "axis": axis,
            "local_orientation": orientation, "candidate_id": candidate_id,
            "between": [s[:250] for s in between], "measures": str(reading.get("measures") or "")[:350],
            "numeric_value": number["numeric_value"], "printed_unit": number["printed_unit"],
            "interpreted_value_mm": number["interpreted_value_mm"], "unit_basis": number["unit_basis"],
            "evidence_refs": number["evidence_refs"], "basis": "visual_interpretation",
            "validation": "source_references_checked_not_physical_ownership"})
    from use_cases.estimation_2vn_resolver import _expected_axis
    by_view = {view["view_id"]: view for view in views}
    axis_readings = defaultdict(list)
    conflicts = []
    for item in readings:
        item["ownership_status"] = "visual_interpretation"
        if item["scope_id"] is None or item["axis"] not in {"width", "height", "depth"}:
            continue
        view = by_view[item["view_id"]]
        expected = _expected_axis(projection=view["projection"], orientation=item["local_orientation"], top_plan_axis=view["horizontal_axis"])
        if expected != item["axis"]:
            item["ownership_status"] = "conflicting"
            conflicts.append({"reason": "projection_axis_mismatch", "dimension_ids": [item["dimension_id"]]})
        axis_readings[(item["scope_id"], item["axis"])].append(item)
    for (scope_id, axis), items in axis_readings.items():
        values = {item["interpreted_value_mm"] for item in items if item["interpreted_value_mm"] is not None}
        if len(values) > 1 and max(values) - min(values) > max(3, max(values) * .003):
            for item in items:
                item["ownership_status"] = "conflicting"
            conflicts.append({"reason": "multiple_values_for_one_assembly_axis", "scope_id": scope_id,
                "axis": axis, "dimension_ids": [item["dimension_id"] for item in items]})
    return {**deepcopy(dict(source_map)), "view_readings": views, "dimension_readings": readings,
            "conflicts": conflicts, "status": "needs_review" if conflicts else "interpreted_not_certified",
            "uninterpreted_dimension_ids": sorted(set(numbers) - seen)}


def apply_evidence_measurements(extraction: Mapping[str, Any], *, scope: Mapping[str, Any]) -> dict[str, Any]:
    """Expand compact references, preserving the existing Calculation/2VN contract."""
    result = deepcopy(dict(extraction))
    evidence = scope.get("evidence_map") or {}
    if not evidence:
        return result
    readings = {r["dimension_id"]: r for r in evidence["dimension_readings"]}
    views = {v["view_id"]: v for v in evidence["view_readings"]}
    emitted_views = {v["view_id"]: v for v in result.get("view_interpretations") or []}
    bindings = list(result.get("dimension_bindings") or [])
    convention = (evidence["dimension_scale_gate"].get("decision") or {}).get("required_unit")
    for assembly in result.get("assemblies") or []:
        for axis, value in list((assembly.get("dimensions") or {}).items()):
            if not isinstance(value, Mapping) or "measurement_id" not in value:
                continue
            reading = readings.get(value["measurement_id"])
            if reading is None or reading["scope_id"] != assembly.get("assembly_id") or reading["axis"] != axis:
                raise ValueError("Calculation measurement reference changed evidence ownership")
            view = views[reading["view_id"]]
            if reading["view_id"] in emitted_views and emitted_views[reading["view_id"]] != view:
                raise ValueError("Calculation measurement reference changed evidence projection")
            unit = reading["printed_unit"] or convention
            if not unit:
                raise ValueError("Calculation measurement reference requires resolved units")
            emitted_views[reading["view_id"]] = view
            assembly["dimensions"][axis] = {"value": reading["numeric_value"], "unit": unit,
                "unit_basis": "explicit_source" if reading["printed_unit"] else "document_convention_assumption",
                "basis": "source", "evidence_refs": reading["evidence_refs"], "assumption_reason": None}
            if reading.get("ownership_status") == "conflicting":
                assembly["dimensions"][axis].update(basis="assumption", evidence_refs=[],
                    assumption_reason="Conflicting evidence-map ownership; selected value remains an estimating assumption.")
                result.setdefault("omissions", []).append(f"{assembly['assembly_id']}.{axis}: conflicting evidence-map reading {reading['dimension_id']}")
                continue
            if any(b.get("assembly_id") == assembly["assembly_id"] and b.get("axis") == axis for b in bindings):
                raise ValueError("Calculation measurement reference duplicates an explicit binding")
            bindings.append({"assembly_id": assembly["assembly_id"], "axis": axis,
                "view_id": reading["view_id"], "local_orientation": reading["local_orientation"],
                "dimension_id": reading["dimension_id"], "resolution": "direct"})
    result["dimension_bindings"] = bindings
    result["view_interpretations"] = list(emitted_views.values())
    return result
