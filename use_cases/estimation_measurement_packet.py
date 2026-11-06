"""Bounded source measurements for CB Parts V4.1, no model calls or OCR repair.

Reuse the existing evidence map/scale policy. Only line candidates supported
at both endpoints, associated with one nearby numeric label, are transported.
Coordinates use the actual enlarged image including margin/header, like Front.
None of these checks establishes physical dimension ownership.
"""
import base64
from copy import deepcopy
from io import BytesIO
import json

from PIL import Image

from use_cases.estimation_evidence_map import build_evidence_map
from use_cases.estimation_cb_bays import _fields, _list
from use_cases.estimation_cb_parts import positive
from use_cases.estimation_cb_spans import _text


def detail_frames(content):
    pages, frames, pending = {}, {}, None
    for item in content:
        if item["type"] == "text":
            try:
                meta = json.loads(item["text"])
            except (ValueError, TypeError):
                continue
            if not isinstance(meta, dict):
                continue
            if "displayed_image_pixels" in meta and "view_regions" in meta:
                pages[meta["source_evidence_ref"]] = meta
            if "detail_of_existing_view" in meta:
                pending = meta
        elif item["type"] == "image" and pending:
            meta, pending = pending, None
            page = pages[meta["source_evidence_ref"]]
            region = meta["detail_of_existing_view"]
            with Image.open(BytesIO(base64.b64decode(item["source"]["data"]))) as img:
                size = img.size
            pw, ph = page["displayed_image_pixels"]
            x, y = region["bbox_normalized"][:2]
            frame = region["coordinate_frame_pixels"]
            if abs((pw / ph) / (frame[0] / frame[1]) - 1) > .015:
                raise ValueError("measurement image/frame aspect ratio mismatch")
            vid = region["view_id"]
            if vid in frames:
                raise ValueError("duplicate measurement image identity")
            frames[vid] = {"page_number": page["page_number"], "source_ref": meta["source_evidence_ref"],
                "source_frame": list(frame), "page_size": [pw, ph], "detail_size": list(size),
                "crop_origin": [max(0, int((x - .015) * pw)), max(0, int((y - .015) * ph))],
                "header": meta["generated_header_height_px"]}
    return frames


def source_to_detail(point, frame):
    return [round((point[axis] * frame["page_size"][i] / frame["source_frame"][i]
        - frame["crop_origin"][i] + (frame["header"] if i == 1 else 0))
        * 1000 / frame["detail_size"][i], 3) for i, axis in enumerate(("x", "y"))]


def _center(number):
    b = number["bbox"]
    return {"x": (b["top_left_x"] + b["bottom_right_x"]) / 2,
            "y": (b["top_left_y"] + b["bottom_right_y"]) / 2}


def _single_label_supported(number, line, page_numbers):
    """No nearest-line promotion. Chain overall spans with multiple labels fail."""
    if len(line.get("endpoint_crossing_candidates", [])) != 2 or not all(line["endpoint_crossing_candidates"]):
        return False
    axis, other = ("x", "y") if line["orientation"] == "horizontal" else ("y", "x")
    a, b = sorted((line["start"][axis], line["end"][axis]))
    p = line["start"][other]
    center = _center(number)
    box = number["bbox"]
    label_size = min(box["bottom_right_x"] - box["top_left_x"], box["bottom_right_y"] - box["top_left_y"])
    tolerance = max(2, label_size * 1.5)
    if not a <= center[axis] <= b or abs(center[other] - p) > tolerance:
        return False
    label_ids = {n["dimension_id"] for n in page_numbers
        if a <= _center(n)[axis] <= b and abs(_center(n)[other] - p) <= tolerance}
    return label_ids == {number["dimension_id"]}


def build_measurement_packet(*, input_row, page_bytes, content, front, source_map=None):
    evidence = source_map if source_map is not None else build_evidence_map(input_row=input_row, page_bytes_by_ref=page_bytes)
    if evidence.get("input_id") != input_row["input_id"]:
        raise ValueError("measurement map belongs to another object")
    if len(evidence["dimensions"]) > 200:
        raise ValueError("measurement packet exceeds 200 source numbers; no silent truncation")
    frames = detail_frames(content)
    fronts = [f for g in front["front_groups"] for f in g["fronts"]]
    dimensions = []
    for number in evidence["dimensions"]:
        page_numbers = [n for n in evidence["dimensions"] if n["page_number"] == number["page_number"]]
        locations, candidates = [], []
        for vid, frame in frames.items():
            if frame["page_number"] != number["page_number"]:
                continue
            center = source_to_detail(_center(number), frame)
            if not (0 <= center[0] <= 1000 and frame["header"] / frame["detail_size"][1] * 1000 <= center[1] <= 1000):
                continue
            locations.append({"view_id": vid, "label_center_1000": center})
            for line in number["line_candidates"]:
                if not _single_label_supported(number, line, page_numbers):
                    continue
                a, b = source_to_detail(line["start"], frame), source_to_detail(line["end"], frame)
                if any(not 0 <= v <= 1000 for v in a + b):
                    continue
                endpoints = a + b
                if any(c["view_id"] == vid and c["orientation"] == line["orientation"] and
                       max(abs(x - y) for x, y in zip(c["endpoints_1000"], endpoints)) < 3 for c in candidates):
                    continue
                inside, outside = [], []
                if line["orientation"] == "horizontal":
                    left, right = sorted((a[0], b[0]))
                    for f in fronts:
                        if f["view_id"] != vid or not f.get("bbox_1000"):
                            continue
                        cx = (f["bbox_1000"][0] + f["bbox_1000"][2]) / 2
                        (inside if left <= cx <= right else outside).append(f["id"])
                candidates.append({"candidate_id": f"{number['dimension_id']}/{line['segment_id']}/{vid}",
                    "view_id": vid, "orientation": line["orientation"], "endpoints_1000": endpoints,
                    "front_centres_inside_x": inside, "front_centres_outside_x": outside,
                    "basis": "two_crossings_one_label_raster_or_native_candidate_not_ownership_proof"})
        dimensions.append({"source_id": number["dimension_id"], "label": number["raw_text"],
            "value_mm": number["interpreted_value_mm"], "unit_basis": number["unit_basis"],
            "evidence_refs": list(number["evidence_refs"]), "locations": locations, "candidates": candidates})
    packet = {"version": "cb_measurement_packet_v1", "input_id": input_row["input_id"],
        "scale_policy": evidence["dimension_scale_gate"], "pages": evidence["pages"], "dimensions": dimensions,
        "limitations": ["Numeric OCR labels can be annotations rather than physical dimensions.",
            "Scale policy is an estimating convention unless units are printed.",
            "Endpoints are supported stroke candidates, not verified arrowheads or ownership.",
            "Front boxes are fallible model locations; interval lists are same-image projections only.",
            "Truncated raster extraction means candidate coverage is incomplete, not proven absent."]}
    if len(json.dumps(packet)) > 120000:
        raise ValueError("measurement packet text exceeds bound")
    return packet


def resolve_measured_dimensions(raw, *, packet, scope):
    """Copy source numbers by immutable ID; reject contradictory span membership."""
    sources = {d["source_id"]: d for d in packet["dimensions"]}
    if packet["input_id"] != scope["input_id"]:
        raise ValueError("measurement packet belongs to another object")
    _list(raw.get("dimensions"), "measured dimensions", 1, 300)
    resolved, audit, anchors, seen = [], [], {}, set()
    for d in raw["dimensions"]:
        if not isinstance(d, dict):
            raise ValueError("measured dimension must be an object")
        _text(d.get("id"), "dimension ID", 80)
        _text(d.get("reason"), "dimension reason", 1200)
        if d["id"] in seen:
            raise ValueError("duplicate measured dimension")
        seen.add(d["id"])
        if "source_id" not in d:
            _fields(d, "id value_mm reason", "assumed dimension")
            value = positive(d["value_mm"], "assumed millimetres")
            resolved.append({"id": d["id"], "value": value, "unit": "mm", "basis": "assumption",
                "view_id": None, "label": "", "reason": d["reason"]})
            audit.append({"id": d["id"], "basis": "explicit_model_assumption", "value_mm": value})
            continue
        _fields(d, "id source_id candidate_id view_id reason", "source dimension reference")
        if not isinstance(d["source_id"], str) or d["source_id"] not in sources:
            raise ValueError("unknown source dimension")
        source = sources[d["source_id"]]
        value = positive(source["value_mm"], "source millimetres unavailable")
        if d["view_id"] not in {loc["view_id"] for loc in source["locations"]}:
            raise ValueError("dimension label is not in the selected image")
        candidate = None
        if d["candidate_id"] is not None:
            matches = [c for c in source["candidates"] if c["candidate_id"] == d["candidate_id"] and c["view_id"] == d["view_id"]]
            if len(matches) != 1:
                raise ValueError("unknown source line candidate")
            candidate = matches[0]
        anchors[d["id"]] = {"source_id": d["source_id"], "candidate": candidate}
        resolved.append({"id": d["id"], "value": value, "unit": "mm", "basis": "drawing_reading",
            "view_id": d["view_id"], "label": source["label"], "reason": d["reason"]})
        audit.append({"id": d["id"], "source_id": d["source_id"], "candidate_id": d["candidate_id"],
            "value_mm": value, "unit_basis": source["unit_basis"], "evidence_refs": source["evidence_refs"],
            "ownership_verified": False})
    checks = []
    fronts = {f["id"]: f for g in scope["front"]["front_groups"] for f in g["fronts"]}
    for run in raw.get("runs", []):
        selected = [anchors[k] for k in run["width_ids"] if k in anchors]
        ids = [a["source_id"] for a in selected]
        if len(set(ids)) != len(ids):
            raise ValueError("one source dimension counted twice in a run")
        intervals = [a["candidate"] for a in selected]
        # Only check a complete, same-image horizontal chain. A mixture with an
        # assumed/different-view interval is explicitly not certified or repaired.
        complete = bool(intervals) and len(intervals) == len(run["width_ids"]) and all(
            c and c["orientation"] == "horizontal" and c["view_id"] == run["view_id"] for c in intervals)
        if not complete:
            checks.append({"run_id": run["id"], "status": "no_complete_same_view_width_anchor"})
            continue
        spans = sorted((min(c["endpoints_1000"][0], c["endpoints_1000"][2]), max(c["endpoints_1000"][0], c["endpoints_1000"][2])) for c in intervals)
        if any(b[0] < a[1] - 3 or b[0] > a[1] + 3 for a, b in zip(spans, spans[1:])):
            raise ValueError("width source intervals overlap or leave a gap")
        front_ids = [f["id"] for b in run["bays"] for f in b["fronts"]]
        checked, unchecked = [], []
        for fid in front_ids:
            if fid not in fronts or fronts[fid]["view_id"] != run["view_id"] or not fronts[fid].get("bbox_1000"):
                unchecked.append(fid)
                continue
            box = fronts[fid]["bbox_1000"]
            if not spans[0][0] - 3 <= (box[0] + box[2]) / 2 <= spans[-1][1] + 3:
                raise ValueError(f"{run['id']}: front {fid} lies outside selected width source intervals")
            checked.append(fid)
        checks.append({"run_id": run["id"], "status": "partial_front_interval_check" if unchecked else "same_view_front_centres_consistent_not_ownership_proof",
            "checked_front_ids": checked, "unchecked_front_ids": unchecked})
    converted = deepcopy(raw)
    converted["dimensions"] = resolved
    return converted, {"dimensions": audit, "run_checks": checks}
