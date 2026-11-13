"""Resolve Block envelopes against orthographic PDF boundaries and Detection OCR."""

import argparse
from collections import defaultdict
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import pymupdf

from tools.estimation_casework_geometry import resolve_casework_group
from tools.estimation_orthographic_geometry import resolve_orthographic_group
from tools.probe_cb_block_boundaries import rectangular


EDGE_TOLERANCE = 3
ELEVATIONS = {"Front elevation", "Rear view", "Side view"}
AUDIT_FILE = "estimation-offline-all-islands-evidence.json"


def arrow_tips(segments, frame_size=None):
    """Find opposed sloping legs that meet at a dimension arrow tip."""
    incident = defaultdict(list)
    for a, b in segments:
        dx, dy = (b[i] - a[i] for i in (0, 1))
        if min(abs(dx), abs(dy)) < .15 or max(abs(dx), abs(dy)) > 45:
            continue
        incident[a].append((dx, dy))
        incident[b].append((-dx, -dy))
    tips = set()
    for point, vectors in incident.items():
        for a, b in combinations(vectors, 2):
            axis = int(abs(a[1]) > abs(a[0]))
            other = 1 - axis
            aspect = frame_size[other] / frame_size[axis] if frame_size else 1
            if (a[axis] * b[axis] > 0 and a[other] * b[other] < 0
                    and abs(a[axis] - b[axis]) <= .2 * abs(a[axis])
                    and .025 <= abs(a[other] / a[axis]) * aspect <= .45
                    and .025 <= abs(b[other] / b[axis]) * aspect <= .45):
                tips.add((axis, point))
    return tips


def path_spans(segments, tips):
    grouped = defaultdict(set)
    for axis, point in tips:
        grouped[axis, round(point[1 - axis], 1)].add(point[axis])
    for (axis, across), positions in grouped.items():
        positions = sorted(positions)
        for start, end in zip(positions, positions[1:]):
            if end - start < 4:
                continue
            line = [(min(a[axis], b[axis]), max(a[axis], b[axis])) for a, b in segments
                    if abs(a[1 - axis] - across) <= 1 and abs(b[1 - axis] - across) <= 1]
            if not any(lo <= start + 1 and hi >= end - 1 for lo, hi in line):
                continue
            span = {"axis": "xy"[axis], "bounds": [start, end], "across": across}
            if end - start <= 35:
                # Short dimensions can have both arrows and the caption outside
                # the measured span. Use the continuous dimension line to find the caption.
                lo, hi = start, end
                for _ in range(len(line)):
                    connected = [(a, b) for a, b in line if a <= hi + 1 and b >= lo - 1]
                    extended = min(a for a, _ in connected), max(b for _, b in connected)
                    if extended == (lo, hi):
                        break
                    lo, hi = extended
                if lo < start - 3 and hi > end + 3:
                    span["caption_bounds"] = [lo, hi]
            yield span


def printed_spans(page, view, inventory, *, fragmented=False):
    """Bind OCR labels to dimension paths, including separated same-style strokes."""
    left, top, right, bottom = view["bbox_normalized"]
    clip = pymupdf.Rect(left * page.rect.width, top * page.rect.height,
                       right * page.rect.width, bottom * page.rect.height)
    zoom = 1100 / clip.width
    origin = (clip * zoom).irect
    width, height = view["width"], view["height"]

    def project(point):
        point = point * page.rotation_matrix
        return (round((point.x * zoom - origin.x0) * 1000 / width, 3),
                round((point.y * zoom - origin.y0) * 1000 / height, 3))

    spans = []
    styled = defaultdict(list)
    for path in page.get_drawings():
        local = []
        for kind, *points in path["items"]:
            if kind == "re":
                rect = points[0]
                points = (rect.tl, rect.tr, rect.br, rect.bl, rect.tl)
            elif kind != "l":
                continue
            projected = list(map(project, points))
            local.extend((a, b) for a, b in zip(projected, projected[1:]) if
                         all((-15 if fragmented else 0) <= coordinate <= (1015 if fragmented else 1000)
                             for coordinate in (*a, *b)))
        if fragmented:
            width_pt = path["width"] or 0
            if path["color"] and max(path["color"]) - min(path["color"]) < .02 and 0 < width_pt < .5:
                styled[(path["color"], round(width_pt, 2))].extend((line, path["seqno"]) for line in local)
        else:
            spans.extend({**span, "native_path_id": path["seqno"]} for span in path_spans(local, arrow_tips(local)))
    for paths in styled.values():
        lines = [line for line, _ in paths]
        for dimension in path_spans(lines, arrow_tips(lines, (width, height))):
            axis = "xy".index(dimension["axis"])
            across = dimension["across"]
            low, high = dimension["bounds"]
            witnesses = sorted({pid for (a, b), pid in paths
                                if any(abs(point[1-axis] - across) <= 1 and
                                       min(abs(point[axis] - edge) for edge in (low, high)) <= 1 for point in (a, b))})
            spans.append({**dimension, "native_path_ids": witnesses})

    proposed = defaultdict(list)
    for occurrence in inventory:
        if occurrence.get("value_mm") is None or not occurrence.get("normalized_bbox"):
            continue
        box = occurrence["normalized_bbox"]
        center = [(box["top_left_" + axis] + box["bottom_right_" + axis]) * 500 for axis in "xy"]
        choices = []
        for span in spans:
            if occurrence.get("label_axis", span["axis"]) != span["axis"]:
                continue
            axis = "xy".index(span["axis"])
            low, high = span["bounds"]
            caption_low, caption_high = span.get("caption_bounds", (low, high))
            extended_caption = (not low <= center[axis] <= high
                                and caption_low <= center[axis] <= caption_high)
            if extended_caption:
                low, high = caption_low, caption_high
            gap = max(low - center[axis], center[axis] - high, 0)
            across = abs(center[1 - axis] - span["across"])
            if across <= (58 if fragmented or extended_caption else 90) and gap <= (45 if fragmented else 155):
                score = across + 1.8 * gap + .15 * abs(center[axis] - (low + high) / 2)
                choices.append((score, span))
        if choices:
            score, span = min(choices, key=lambda item: item[0])
            proposed[(span["axis"], tuple(span["bounds"]), span["across"])].append((score, {
                **span, "view_id": view["view_id"], "page": view["page"],
                "label": occurrence["original_text"], "value_mm": float(occurrence["value_mm"]),
                "source_id": occurrence["occurrence_id"], "source_refs": occurrence["source_refs"],
                "unit_basis": occurrence["unit_basis"],
                **({"render_basis": occurrence["render_basis"]} if occurrence.get("render_basis") else {}),
            }))
    resolved = []
    for options in proposed.values():
        score, closest = min(options, key=lambda item: item[0])
        if len({row["value_mm"] for distance, row in options if distance <= score + 2}) == 1:
            resolved.append(closest)
    return resolved


def close(first, second):
    return abs(first - second) <= EDGE_TOLERANCE


def normalized(view, axis, coordinates):
    size = view["width" if axis == "x" else "height"]
    return [round(value * 1000 / size, 3) for value in coordinates]


def span(view, axis, coordinates, first, last, contours):
    low, high = normalized(view, axis, coordinates)
    if low >= high or not 0 <= low < high <= 1000:
        raise ValueError("boundary pair must lie in its source Island")
    return {"view_id": view["view_id"], "page": view["page"], "axis": axis, "bounds_1000": [low, high],
            "from": first, "to": last, "contour_ids": list(dict.fromkeys(contours))}


def project_value(bounds, source):
    a, b = source["bounds"]
    return (bounds[1] - bounds[0]) * source["value_mm"] / (b - a)


def bind_dimension(boundary, printed, *, allow_estimate=False):
    """Verify both endpoints before adopting a printed value."""
    low, high = boundary["bounds_1000"]
    same_axis = [row for row in printed[boundary["view_id"]] if row["axis"] == boundary["axis"]]
    exact = [row for row in same_axis if close(low, row["bounds"][0]) and close(high, row["bounds"][1])]
    if len({row["value_mm"] for row in exact}) == 1:
        source = min(exact, key=lambda row: abs(low - row["bounds"][0]) + abs(high - row["bounds"][1]))
        return {**boundary, "value_mm": source["value_mm"], "method": "printed_dimension", "sources": [source]}
    if not exact and allow_estimate:
        anchors = [row for row in same_axis if row["bounds"][0] <= low + EDGE_TOLERANCE
                   and high <= row["bounds"][1] + EDGE_TOLERANCE]
        if anchors:
            source = min(anchors, key=lambda row: row["bounds"][1] - row["bounds"][0])
            return {**boundary, "value_mm": round(project_value([low, high], source)), "method": "scaled_projection",
                    "sources": [source]}
    return {**boundary, "value_mm": None, "method": "unresolved", "sources": []}


def by_id(view):
    return {row["id"]: row for row in view["candidates"]}


def unique(items):
    return items[0] if len(items) == 1 else None


def horizontal_edges(contour):
    points = contour["polygon"]
    return [(min(a[0], b[0]), (a[1] + b[1]) / 2, max(a[0], b[0]))
            for a, b in zip(points, points[1:] + points[:1])
            if abs(a[1] - b[1]) <= 1 and abs(a[0] - b[0]) > 2]


def common_floor_difference(frame, floor_span, printed, installed):
    """Cross-check the lower block's installed top against the shared floor datum."""
    candidates = [row for row in printed[frame["view_id"]] if row["axis"] == "y"
                  and close(row["bounds"][0], frame["bounds_1000"][0])
                  and close(row["bounds"][1], floor_span["bounds_1000"][1])]
    if len({row["value_mm"] for row in candidates}) != 1 or installed["method"] != "printed_dimension":
        return bind_dimension(frame, printed, allow_estimate=True)
    overall = candidates[0]
    value = overall["value_mm"] - installed["value_mm"]
    projection = project_value(frame["bounds_1000"], overall)
    if value <= 0 or abs(projection - value) > max(10, .02 * value):
        return bind_dimension(frame, printed, allow_estimate=True)
    return {**frame, "value_mm": value, "method": "shared_floor_difference",
            "sources": [overall, *installed["sources"]], "subtract_mm": installed["value_mm"],
            "installed_top_boundary": installed, "projection_check_mm": round(projection)}


def linked_side(views, block, parts):
    """Identify the physical plate, its side profile and the legs from Locator."""
    extension = block.get("supported_top")
    if not extension:
        return None
    vid = extension["view_id"]
    view = views[vid]
    contours = by_id(view)
    attached = contours[extension["attached_side"]]
    _, panel_top, right, panel_bottom = attached["bbox"]
    top_ids = extension["top"]["contour_ids"]
    top_box = extension["top"]["bbox"]
    supports = extension["supports"]
    floor = max(row["bbox"][3] for row in supports)

    # The side of a covered base can be a separate native contour below a
    # continuous upright side profile. A narrower floor rail is the plinth.
    candidates = [row for row in view["candidates"] if row != attached and rectangular(row)
                  and abs(row["bbox"][1] - panel_bottom) <= 2
                  and abs(row["bbox"][2] - right) <= 2 and row["bbox"][3] < floor - 2]
    carcass = unique(candidates)
    if carcass is None:
        return None
    base = carcass["bbox"]
    plinth = unique([row for row in view["candidates"] if rectangular(row)
                    and abs(row["bbox"][1] - base[3]) <= 2 and abs(row["bbox"][3] - floor) <= 2
                    and base[0] < row["bbox"][0] < row["bbox"][2] < base[2]])
    if plinth is None or not any(row["role"] == "plinth" and block["id"] in row.get("attached_block_ids", [])
                                for row in parts):
        return None

    # The physical seating ledge may be joined to the upright in one PDF path.
    # Find the shoulder over the carcass, separated from the tall silhouette.
    ledge = unique([edge for edge in horizontal_edges(attached)
                    if edge[0] <= base[0] + 2 and edge[2] > base[0] + 2
                    and 1 < base[1] - edge[1] < .08 * (base[2] - base[0])])
    upper = unique([edge for edge in horizontal_edges(attached) if abs(edge[1] - panel_top) <= 1])
    if ledge is None or upper is None or abs(upper[2] - right) > 2:
        return None
    return view, attached, carcass, plinth, ledge, upper, top_ids, top_box, supports, floor


def linked_plan(views, projections, printed, side_depth, side_calibration):
    """Confirm the plan's axes against the visible side footprint."""
    estimated_depth = project_value(side_depth["bounds_1000"], side_calibration)
    matches = []
    for vid, view in views.items():
        if projections[vid] != "Top view":
            continue
        for contour in view["candidates"]:
            if not rectangular(contour):
                continue
            x0, y0, x1, y1 = contour["bbox"]
            for axis in "xy":
                depth_coords, width_coords = ((x0, x1), (y0, y1)) if axis == "x" else ((y0, y1), (x0, x1))
                across = 1 - "xy".index(axis)
                along = 1 - across
                attached = set()
                for neighbor in view["candidates"]:
                    if neighbor["id"] == contour["id"] or not rectangular(neighbor):
                        continue
                    box = neighbor["bbox"]
                    overlap = min(contour["bbox"][across + 2], box[across + 2]) - max(contour["bbox"][across], box[across])
                    if overlap < .8 * (width_coords[1] - width_coords[0]):
                        continue
                    if abs(box[along + 2] - depth_coords[0]) <= 2:
                        attached.add(0)
                    if abs(box[along] - depth_coords[1]) <= 2:
                        attached.add(1)
                depth_edges = ("first tabletop edge", "opposite tabletop edge")
                if attached == {0}:
                    depth_edges = ("attached tabletop edge", "outer tabletop edge")
                elif attached == {1}:
                    depth_edges = ("outer tabletop edge", "attached tabletop edge")
                depth = bind_dimension(span(view, axis, depth_coords, *depth_edges, [contour["id"]]), printed)
                width = bind_dimension(span(view, "y" if axis == "x" else "x", width_coords,
                                            "first lateral tabletop edge", "opposite lateral tabletop edge",
                                            [contour["id"]]), printed)
                if (depth["value_mm"] is not None and width["value_mm"] is not None and
                        abs(depth["value_mm"] - estimated_depth) <= max(10, .02 * estimated_depth)):
                    matches.append((width, depth))
    return unique(matches)


def resolve_supported_group(plan, views, projections, printed):
    """Resolve a supported top and the frame/cover construction that it abuts."""
    blocks = plan["blocks"]
    by_basis = defaultdict(list)
    for block in blocks:
        by_basis[block["basis"]].append(block)
    base = unique(by_basis["shared_drawer_frame"])
    back = unique(by_basis["matched_framed_panel"])
    top = unique(by_basis["independently_supported_extension"])
    if not all((base, back, top)):
        return {}
    parts = plan["object_parts"]
    if not any(row.get("envelope_block_id") == top["id"] and base["id"] in row.get("attached_block_ids", [])
               for row in parts):
        return {}
    side = linked_side(views, base, parts)
    if side is None:
        return {}
    view, attached, case, plinth, ledge, upright, plate_ids, plate, supports, floor = side
    if projections[view["view_id"]] != "Side view":
        return {}
    a, seat_y, _ = ledge
    rear = case["bbox"][2]
    case_floor = case["bbox"][3]
    v = attached["id"]
    height_bound = span(view, "y", (seat_y, floor), "seat upper edge", "floor at plinth bottom", [v, plinth["id"]])
    installed = bind_dimension(height_bound, printed)
    base_height = bind_dimension(span(view, "y", (seat_y, case_floor), "seat upper edge",
                                     "carcass lower edge at plinth top", [v, case["id"], plinth["id"]]),
                                 printed, allow_estimate=True)
    base_depth = bind_dimension(span(view, "x", (a, rear), "seat front edge", "rear edge of carcass",
                                    [v, case["id"]]), printed)
    back_depth = bind_dimension(span(view, "x", (upright[0], upright[2]), "front edge of upright",
                                    "rear edge of upright", [v]), printed)
    top_height = bind_dimension(span(view, "y", (plate[1], floor), "tabletop upper edge", "floor at leg foot",
                                     plate_ids + [row["contour_id"] for row in supports]), printed)
    leg = unique(supports)
    leg_height = None
    if leg:
        leg_height = bind_dimension(span(view, "y", (leg["bbox"][1], leg["bbox"][3]), "underside at support contact",
                                         "floor at leg foot", [leg["contour_id"]]), printed, allow_estimate=True)

    # The top's plane is measured on the plan. An independent side ratio
    # selects the matching plan contour and prevents swapping width and depth.
    top_width = top_depth = {"value_mm": None, "method": "unresolved"}
    if base_depth["method"] == "printed_dimension":
        side_footprint = span(view, "x", (plate[0], plate[2]), "attached tabletop edge", "outer tabletop edge",
                              plate_ids)
        footprint = linked_plan(views, projections, printed, side_footprint, base_depth["sources"][0])
        if footprint:
            top_width, top_depth = footprint
            top_depth = {**top_depth, "axis_crosscheck": side_footprint,
                         "axis_calibration": base_depth["sources"][0]}

    for face in base["appearances"]:
        vid = face["view_id"]
        elevation = views[vid]
        frame = unique([item for item in back["appearances"] if item["view_id"] == vid])
        if frame is None or projections[vid] not in {"Front elevation", "Rear view"}:
            continue
        contours = by_id(elevation)
        cover = contours[face["edges"]["top"]]
        plinth_appearance = unique([item for part in parts if part["role"] == "plinth"
                                   for item in part["appearances"] if item["view_id"] == vid])
        cx0, cy0, cx1, cy1 = cover["bbox"]
        bx0, by0, bx1, by1 = frame["bbox"]
        if (plinth_appearance is None or not rectangular(cover) or abs(cy0 - by1) > 2
                or abs(cy1 - face["bbox"][1]) > 2 or cx1 - cx0 < 8 * (cy1 - cy0)):
            continue
        base_width = bind_dimension(span(elevation, "x", (cx0, cx1), "left seat cover edge",
                                        "right seat cover edge", [cover["id"]]), printed)
        carcass_width = bind_dimension(span(elevation, "x", (face["bbox"][0], face["bbox"][2]),
                                           "left drawer carcass edge", "right drawer carcass edge",
                                           [face["frame"]]), printed)
        back_width = bind_dimension(span(elevation, "x", (bx0, bx1), "left frame edge", "right frame edge",
                                         [frame["frame"]]), printed)
        frame_height = span(elevation, "y", (by0, by1), "upper frame edge", "frame bottom at top of seat",
                            [frame["frame"], cover["id"]])
        overall = span(elevation, "y", (by0, plinth_appearance["bbox"][3]), "upper frame edge",
                       "floor at plinth bottom", [frame["frame"], plinth_appearance["contour_id"]])
        back_height = common_floor_difference(frame_height, overall, printed, installed)
        return {
            base["id"]: {"width": base_width, "depth": base_depth, "height": base_height,
                         "installed_height": installed, "carcass_width": carcass_width},
            back["id"]: {"width": back_width, "depth": back_depth, "height": back_height},
            top["id"]: {"width": top_width, "depth": top_depth, "height": top_height, "leg_height": leg_height},
        }
    return {}


def run_block_geometry(pdf_path, audit_path, source, analyze, key, *, dimension_reader=None,
                       dimension_unit=None, saved_dimension_inventory=None):
    """Build Block Geometry directly from one Analyze output and its source evidence."""
    audit_bytes = audit_path.read_bytes()
    if sha256(audit_bytes).hexdigest() != analyze["source_audit_sha256"]:
        raise ValueError("Analyze and native geometry must use the same source packet")
    audit = json.loads(audit_bytes)
    if sha256(pdf_path.read_bytes()).hexdigest() != audit["source_sha256"][key]:
        raise ValueError("PDF does not match the source packet")
    detection = source.get("detection_context", source)
    objects = {row["object_id"]: row for row in detection["objects"]}
    results = {}
    local_inventory = {}
    if saved_dimension_inventory:
        if saved_dimension_inventory["source_audit_sha256"] != analyze["source_audit_sha256"]:
            raise ValueError("Saved dimension OCR belongs to a different source packet")
        local_inventory.update(saved_dimension_inventory["local_dimension_inventory"])
    with pymupdf.open(pdf_path) as pdf:
        for oid, obj in analyze["objects"].items():
            views = {row["view_id"]: row for row in audit["documents"][key] if row["object_id"] == oid}
            source_object = objects[oid]
            islands = {row["island_id"]: row for row in source_object["islands"]}
            if views.keys() != islands.keys():
                raise ValueError("Detection and Analyze Island membership differ")
            for vid, view in views.items():
                island = islands[vid]
                frame = island["coordinate_frame_pixels"]
                coords = [island["bbox"][name] / frame[index % 2] for index, name in enumerate(
                    ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y"))]
                if island["page_number"] != view["page"] or any(abs(a - b) > .0003
                        for a, b in zip(coords, view["bbox_normalized"], strict=True)):
                    raise ValueError("Detection and Analyze Island frames differ")
            inventory = {row["group_id"]: row["occurrences"] for row in source_object["dimension_inventory"]}
            measurable = {vid: view for vid, view in views.items()
                          if analyze["islands"][vid] in ELEVATIONS | {"Top view", "Section"}}
            if dimension_reader:
                from tools.estimation_local_dimension_ocr import read_dimension_labels

                local_inventory.update(read_dimension_labels(
                    pdf, {vid: view for vid, view in measurable.items() if not inventory.get(vid)},
                    dimension_reader, dimension_unit,
                ))
            coordinate_inventory = source_object.get("coordinate_dimension_inventory", {})
            printed = {}
            for vid, view in measurable.items():
                supplemental = local_inventory.get(vid) or coordinate_inventory.get(vid, [])
                if analyze["islands"][vid] == "Section" and not supplemental:
                    continue
                page = pdf[view["page"] - 1]
                spans = printed_spans(page, view, inventory.get(vid, []),
                                      fragmented=bool(local_inventory.get(vid)))
                if not spans and supplemental:
                    spans = printed_spans(page, view, supplemental, fragmented=True)
                printed[vid] = spans
            readings = resolve_supported_group(obj["planner"], views, analyze["islands"], printed)
            if not readings:
                readings = resolve_orthographic_group(
                    obj["planner"], views, analyze["islands"], printed, source_object["accepted_observations"],
                    span=span, bind_dimension=bind_dimension, elevations=ELEVATIONS, edge_tolerance=EDGE_TOLERANCE,
                )
            if not readings and any(printed.values()):
                readings = resolve_casework_group(
                    obj["planner"], obj["front"], views, analyze["islands"], printed, source_object["accepted_observations"],
                    span=span, bind_dimension=bind_dimension,
                )
            unknown = {"value_mm": None, "method": "unresolved"}
            results[oid] = {"blocks": [
                {"block_id": block["id"], "basis": block["basis"],
                 "measurements": readings.get(block["id"], dict.fromkeys(("width", "depth", "height"), unknown))}
                for block in obj["planner"]["blocks"]], "printed_dimensions": printed}
    result = {"stage": "Block Geometry", "analyze_version": analyze["version"], "provider_calls": 0,
              "source_audit_sha256": analyze["source_audit_sha256"], "objects": results}
    if local_inventory:
        result["local_dimension_inventory"] = local_inventory
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pdf", "source", "geometry", "analyze", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--dimension-reader", type=Path, help="Local OCR executable for missing numeric evidence")
    parser.add_argument("--dimension-unit", choices=("mm", "cm"), help="Assumed unit for local OCR only")
    args = parser.parse_args()
    if bool(args.dimension_reader) != bool(args.dimension_unit):
        parser.error("--dimension-reader and --dimension-unit must be supplied together")
    result = run_block_geometry(args.pdf, args.geometry / AUDIT_FILE, json.loads(args.source.read_bytes()),
                                json.loads(args.analyze.read_bytes()), args.key, dimension_reader=args.dimension_reader,
                                dimension_unit=args.dimension_unit)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, ensure_ascii=False)
        output.write("\n")


if __name__ == "__main__":
    main()
