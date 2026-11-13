"""Measure verified part rows on the orthographic projection of a casework block."""

from collections import defaultdict

import pymupdf

from tools.estimation_block_geometry import bind_dimension, span
from tools.estimation_casework_geometry import measure
from tools.probe_cb_block_boundaries import envelope, rectangular
from use_cases.estimation_cb_geometry_parts import geometry_dimension


def _bounds(reading, view, axis):
    size = view["width" if axis == "x" else "height"]
    return [value * size / 1000 for value in reading["bounds_1000"]]


def _rows(view, box):
    left, top, right, bottom = box
    rows = []
    for contour in sorted(view["candidates"], key=lambda c: c["bbox"][1]):
        a, b, c, d = contour["bbox"]
        if (left - 5 <= a < c <= right + 5 and top - 2 <= b < d <= bottom + 2
                and c - a >= .10 * (right - left) and rectangular(contour)):
            row = next((group for group in rows if abs(b - group[0]["bbox"][1]) <= 1.25
                        and abs(d - group[0]["bbox"][3]) <= 1.25), None)
            if row is None:
                rows.append([contour])
            else:
                row.append(contour)
    return [sorted(row, key=lambda c: c["bbox"][0]) for row in rows]


def _full_row(row, count, box):
    left, _, right, _ = box
    tolerance = max(6, .045 * (right - left))
    return (len(row) == count and abs(row[0]["bbox"][0] - left) <= tolerance
            and abs(row[-1]["bbox"][2] - right) <= tolerance
            and all(abs(a["bbox"][2] - b["bbox"][0]) <= 4 for a, b in zip(row, row[1:])))


def _one(rows):
    return rows[0] if len(rows) == 1 else None


def _rectangle_sizes(view, contour, printed):
    a, b, c, d = contour["bbox"]
    return tuple(geometry_dimension(measure(view, axis, ends, names, [contour["id"]], printed, span, bind_dimension))
                 for axis, ends, names in (
                     ("x", (a, c), ("part left edge", "part right edge")),
                     ("y", (b, d), ("part upper edge", "part lower edge")),
                 ))


def casework_plinth_spans(readings, views, printed):
    """Read a lower rail adjoining the verified carcass floor boundary."""
    rails = {}
    for dimensions in readings.values():
        height = dimensions.get("height", {})
        vid = height.get("view_id")
        if vid not in views or not height.get("bounds_1000"):
            continue
        if height.get("to") not in {"body bottom above plinth", "body bottom above shared plinth"}:
            continue
        view = views[vid]
        top, bottom = _bounds(height, view, "y")
        body_ids = set(height["contour_ids"])
        shell = envelope(c["bbox"] for c in view["candidates"] if c["id"] in body_ids)
        width = shell[2] - shell[0]
        if width < .25 * view["width"]:
            continue
        candidates = [c for c in view["candidates"] if abs(c["bbox"][1] - bottom) <= 2
                      and .85 * width <= c["bbox"][2] - c["bbox"][0] <= 1.15 * width
                      and abs(c["bbox"][0] - shell[0]) <= .12 * width
                      and 3 <= c["bbox"][3] - c["bbox"][1] <= .25 * (bottom - top)]
        if rail := _one(candidates):
            sizes = _rectangle_sizes(view, rail, printed)
            if all(d["mm"] for d in sizes):
                rails[vid, rail["id"]] = sizes
    return list(rails.values())


def casework_closure_spans(item, readings, views, printed):
    """Corroborate a leader-bound detached rectangular closure in elevation."""
    shapes = [ref["outline_px"] for ref in item["source_refs"] if ref.get("outline_px")]
    if len(shapes) != 1 or len(shapes[0]) != 4:
        return None
    left, top, right, bottom = envelope((x, y, x, y) for x, y in shapes[0])
    if bottom - top <= 0:
        return None
    ratio = (right - left) / (bottom - top)
    by_view = defaultdict(list)
    for values in readings.values():
        width, height = values.get("width", {}), values.get("height", {})
        vid = height.get("view_id")
        if (vid in views and vid == width.get("view_id") and height.get("bounds_1000")
                and width.get("bounds_1000") and width.get("value_mm") and height.get("value_mm")):
            by_view[vid].append((*_bounds(width, views[vid], "x"), _bounds(height, views[vid], "y")[0]))
    matches = []
    for vid, bounds in by_view.items():
        view = views[vid]
        upper = min(top for _, _, top in bounds)
        for contour in view["candidates"]:
            a, b, c, d = contour["bbox"]
            if (rectangular(contour) and 8 < upper - d <= .3 * view["height"]
                    and .70 * ratio <= (c - a) / (d - b) <= 1.40 * ratio
                    and any(min(c, hi) - max(a, lo) >= .8 * (c - a) for lo, hi, _ in bounds)):
                matches.append((view, contour))
    return _rectangle_sizes(*matches[0], printed) if len(matches) == 1 else None


def _native_lines(pdf, view):
    page = pdf[view["page"] - 1]
    clip = pymupdf.Rect(*(n * (page.rect.width if i % 2 == 0 else page.rect.height)
                         for i, n in enumerate(view["bbox_normalized"])))
    zoom = 1100 / clip.width
    origin = (clip * zoom).irect

    def point(raw):
        p = raw * page.rotation_matrix
        return p.x * zoom - origin.x0, p.y * zoom - origin.y0

    for path in page.get_drawings():
        color = path.get("color")
        if not color or max(color) > .2 or path["type"] != "s":
            continue
        for kind, *points in path["items"]:
            if kind == "l":
                yield path["seqno"], path["width"], tuple(map(point, points))


def _upright_mirror_sizes(block, readings, face, views, printed, pdf):
    width, height = readings["width"], readings["height"]
    plan, section = views[width["view_id"]], views[height["view_id"]]
    if (pdf is None or width["axis"] != "y" or not height.get("value_mm")
            or readings.get("depth", {}).get("from") != "rear face of mounting panel"):
        return None
    source = views[face["view_id"]]
    shell = [row["bbox"] for row in source["candidates"]
             if row["id"] in block["appearances"][face["view_id"]] and row["id"] != face["candidate_id"]]
    if not shell or not face.get("bbox_px"):
        return None
    a, b, c, d = face["bbox_px"]
    # A partially visible mounting face is not a reliable scale reference.
    # The plan and section still have independent dimension evidence.
    left, top, right, bottom = envelope(shell)
    height_ratio = (d - b) / (bottom - top) if top <= b < d <= bottom else None
    width_ratio = (c - a) / (right - left) if height_ratio is not None and right - left >= c - a else None

    panel, = (row for row in plan["candidates"] if row["id"] == width["contour_ids"][0])
    plan_matches = []
    for ident, _, (a, b) in _native_lines(pdf, plan):
        if abs(a[0] - b[0]) > 1 or min(abs(a[0] - edge) for edge in panel["bbox"][::2]) > 4:
            continue
        bounds = sorted((a[1], b[1]))
        if bounds[0] < 0 or bounds[1] > plan["height"] or bounds[1] <= panel["bbox"][3] + 3:
            continue
        if bounds[1] - bounds[0] < .25 * (panel["bbox"][3] - panel["bbox"][1]):
            continue
        boundary = span(plan, "y", bounds, "first end of mirror edge", "last end of mirror edge",
                        [f"pdf-path-{ident}"])
        reading = bind_dimension(boundary, printed)
        if (reading["value_mm"] and reading["value_mm"] < width["value_mm"]
                and (width_ratio is None or abs(reading["value_mm"] / width["value_mm"] - width_ratio) <= .08)):
            plan_matches.append(reading)
    mirror_width = _one(plan_matches)
    if not mirror_width:
        return None

    top, bottom = _bounds(height, section, "y")
    shell_ids = set(height["contour_ids"])
    left, _, right, _ = envelope(c["bbox"] for c in section["candidates"] if c["id"] in shell_ids)
    dimensions = [r for r in printed[section["view_id"]] if r["axis"] == "y"]
    section_matches = []
    for contour in section["candidates"]:
        a, b, c, d = contour["bbox"]
        if not (rectangular(contour) and top < b < d < bottom
                and min(abs(c - left), abs(a - right)) <= 2):
            continue
        pair = [_one([r for r in dimensions if abs(r["bounds"][0] * section["height"] / 1000 - end) <= 2])
                for end in (b, d)]
        if all(pair) and abs(pair[0]["bounds"][1] - pair[1]["bounds"][1]) <= 1:
            size = pair[0]["value_mm"] - pair[1]["value_mm"]
            if (0 < size < height["value_mm"]
                    and (height_ratio is None or abs(size / height["value_mm"] - height_ratio) <= .08)):
                boundary = span(section, "y", (b, d), "top of mirror", "bottom of mirror", [contour["id"]])
                section_matches.append({**boundary, "value_mm": size, "method": "shared_floor_difference",
                                        "sources": pair})
    mirror_height = _one(section_matches)
    if mirror_height:
        return geometry_dimension(mirror_width), geometry_dimension(mirror_height)
    return None


def casework_lighting_span(item, readings, views, printed, pdf):
    """Size a drawn straight lighting route inside its verified plan footprint."""
    depth = readings.get("depth", {})
    vid = depth.get("view_id")
    if vid not in views or len(depth.get("contour_ids", ())) != 1:
        return None
    view = views[vid]
    contour = next((c for c in view["candidates"] if c["id"] == depth["contour_ids"][0]), None)
    if not contour or not rectangular(contour):
        return None
    left, top, right, bottom = contour["bbox"]
    refs = {ref["annotation_id"]: ref for ref in item["source_refs"] if ref["view_id"] == vid and ref.get("tips")}
    if len(refs) != 1:
        return None
    ref, = refs.values()
    tips = [(x, y) for tip in ref["tips"] for x, y in [tip["xy_px"]]
            if left + 2 < x < right - 2 and top + 2 < y < bottom - 2]
    if len(tips) < 2:
        return None
    axis = int(bottom - top > right - left)
    cross = 1 - axis
    along = [p[axis] for p in tips]
    parallel = [p[cross] for p in tips]
    if max(parallel) - min(parallel) > 8 or max(along) - min(along) < 10:
        return None
    at = sum(parallel) / len(parallel)
    extent = contour["bbox"][axis::2]
    paths = defaultdict(list)
    for ident, weight, (a, b) in _native_lines(pdf, view):
        low, high = sorted((a[axis], b[axis]))
        if (extent[0] - 2 <= low < high <= extent[1] + 2 and high - low >= 2
                and abs(a[cross] - b[cross]) <= 1.5 and abs((a[cross] + b[cross]) / 2 - at) <= 5):
            paths[(round(weight, 3), round((a[cross] + b[cross]) / 6) * 3)].append((low, high, ident))
    matches = []
    for segments in paths.values():
        first = min(row[0] for row in segments)
        last = max(row[1] for row in segments)
        if (first <= min(along) and last >= max(along)
                and all(any(a - 5 <= x <= b + 5 for a, b, _ in segments) for x in along)):
            matches.append((first, last, segments))
    match = _one(matches)
    if not match:
        return None
    first, last, segments = match
    measured = geometry_dimension(measure(view, "xy"[axis], (first, last),
                                  ("first visible lighting endpoint", "last visible lighting endpoint"),
                                  [contour["id"]], printed, span, bind_dimension))
    if measured["mm"]:
        return {**measured, "basis": "lighting_route_projection",
                "refs": [*measured["refs"], f'{vid}:{ref["annotation_id"]}',
                         *(f'{vid}:pdf-path-{i}' for i in sorted({row[2] for row in segments}))],
                "reason": "Span of the straight route. Verify strip breaks and wiring at installation."}
    return None


def source_casework_part_geometry(block, readings, faces, views, printed, *, glazed, pdf=None):
    """Transfer a uniquely matched component row to the existing Front instances."""
    height = readings.get("height", {})
    width = readings.get("width", {})
    vid = height.get("view_id")
    if vid not in views or not height.get("bounds_1000") or not width.get("value_mm"):
        return {}, None
    view = views[vid]
    top, bottom = _bounds(height, view, "y")
    contours = {row["id"]: row for row in view["candidates"]}
    if width.get("view_id") == vid:
        left, right = _bounds(width, view, "x")
    elif block["basis"] == "source_labelled_drawer_bank" and height.get("contour_ids"):
        left, _, right, _ = envelope(contours[cid]["bbox"] for cid in height["contour_ids"])
    elif block["basis"] == "mirror_upright" and width.get("view_id") in views:
        mirrors = [face for face in faces if face["role"] == "mirror"]
        if len(mirrors) == 1 and (sizes := _upright_mirror_sizes(block, readings, mirrors[0], views, printed, pdf)):
            face, = mirrors
            return {f'{face["view_id"]}:{face["candidate_id"]}': sizes}, None
        return {}, None
    else:
        return {}, None
    bounds = left, top, right, bottom
    rows = _rows(view, bounds)
    by_role = defaultdict(list)
    for face in faces:
        by_role[face["role"]].append(face)
    matches = {}

    def dimensions(a, b, c, d, ids):
        return tuple(geometry_dimension(measure(view, axis, ends, names, ids, printed, span, bind_dimension))
                     for axis, ends, names in (
                         ("x", (a, c), ("part left edge", "part right edge")),
                         ("y", (b, d), ("part upper edge", "part lower edge")),
                     ))

    def bind(role, row):
        for face, contour in zip(sorted(by_role[role], key=lambda face: face["bbox_px"][0]), row, strict=True):
            matches[f'{face["view_id"]}:{face["candidate_id"]}'] = dimensions(*contour["bbox"], [contour["id"]])

    if block["basis"] == "mirror_upright" and len(by_role["mirror"]) == 1:
        face = _one([c for c in contours.values() if rectangular(c)
                     and left < c["bbox"][0] < c["bbox"][2] < right
                     and top < c["bbox"][1] < c["bbox"][3] <= bottom
                     and c["bbox"][2] - c["bbox"][0] >= .7 * (right - left)
                     and c["bbox"][3] - c["bbox"][1] >= .7 * (bottom - top)])
        if face:
            bind("mirror", [face])

    drawers = by_role["drawer"]
    drawer_row = None
    if drawers and all(face.get("bbox_px") for face in drawers):
        drawer_rows = [row for row in rows if _full_row(row, len(drawers), bounds)]
        if block["basis"] == "source_labelled_drawer_bank":
            # A bank with one thin cap, one shallow operating band and one taller lower panel.
            ordered = sorted(drawer_rows, key=lambda row: row[0]["bbox"][1])
            if len(ordered) == 3 and all(abs(a[0]["bbox"][3] - b[0]["bbox"][1]) <= 3
                                         for a, b in zip(ordered, ordered[1:])):
                heights = [row[0]["bbox"][3] - row[0]["bbox"][1] for row in ordered]
                if heights[0] < .65 * heights[1] and heights[2] > 2 * heights[1]:
                    drawer_row = ordered[1]
        else:
            drawer_row = _one([row for row in drawer_rows if abs(row[0]["bbox"][3] - bottom) <= 3])
        if drawer_row:
            bind("drawer", drawer_row)

    doors = by_role["hinged_door"]
    if doors and all(face.get("bbox_px") for face in doors):
        band_bottom = min(c["bbox"][1] for c in drawer_row) if drawer_row else bottom
        candidates = [row for row in rows if abs(row[0]["bbox"][3] - band_bottom) <= 3]
        door_row = _one([row for row in candidates if _full_row(row, len(doors), bounds)])
        if not door_row:
            # A compound contour can hide one end face. Require a unique
            # contiguous bank and corroboration by an enclosing source outline.
            inferred = []
            for row in candidates:
                if len(row) != len(doors) - 1 or len(row) < 2 or abs(row[-1]["bbox"][2] - right) > 6:
                    continue
                a, y, _, end = row[0]["bbox"]
                if (not all(abs(p["bbox"][2] - q["bbox"][0]) <= 4 for p, q in zip(row, row[1:]))
                        or not .85 <= (a - left) / (row[0]["bbox"][2] - a) <= 1.15):
                    continue
                witness = _one([c for c in contours.values() if abs(c["bbox"][0] - left) <= 6
                                and abs(c["bbox"][2] - right) <= 6 and abs(c["bbox"][3] - end) <= 3
                                and c["bbox"][1] <= y])
                if witness:
                    inferred.append([{"id": witness["id"], "bbox": (left, y, a, end)}, *row])
            door_row = _one(inferred)
        if door_row:
            bind("hinged_door", door_row)

    if block["basis"] == "return_door_band" and len(by_role["mirror"]) == 1 and doors:
        mirror, = by_role["mirror"]
        visible = [face["bbox_px"] for face in doors if face["view_id"] == mirror["view_id"] and face.get("bbox_px")]
        if mirror.get("bbox_px") and len(visible) == len(doors):
            first, _, last, _ = envelope(visible)
            a, _, c, _ = mirror["bbox_px"]
            ratio = (c - a) / (last - first)
            matched = _one([row for row in contours.values() if rectangular(row)
                            and left < row["bbox"][0] < row["bbox"][2] < right
                            and top <= row["bbox"][1] <= top + .12 * (bottom - top)
                            and .3 * (bottom - top) <= row["bbox"][3] - row["bbox"][1] <= .85 * (bottom - top)
                            and abs((row["bbox"][2] - row["bbox"][0]) / (right - left) - ratio) <= .05])
            if matched:
                bind("mirror", [matched])

    glass_height = None
    shelves = by_role["pull_out_shelf"]
    if glazed and drawer_row and len(shelves) == 2 * len(drawers):
        glass_rows = []
        for row in rows:
            row = [c for c in row if c["bbox"][2] - c["bbox"][0] >= .45 * (right - left) / len(drawers)]
            if len(row) != len(drawers) or _full_row(row, len(drawers), bounds):
                continue
            end = row[0]["bbox"][3]
            shelf = _one([other for other in rows if _full_row(other, len(drawers), bounds)
                          and abs(other[0]["bbox"][1] - end) <= 2 and other is not drawer_row])
            if shelf and all(c["bbox"][1] < end - 4 for c in row):
                glass_rows.append(row)
        if len(glass_rows) == 2:
            measurements = [dimensions(*c["bbox"], [c["id"]])[1] for row in glass_rows for c in row]
            values = [size["mm"] for size in measurements]
            if all(values) and max(values) - min(values) <= 5:
                glass_height = {**measurements[0], "refs": list(dict.fromkeys(
                    ref for size in measurements for ref in size["refs"]))}
    return matches, glass_height
