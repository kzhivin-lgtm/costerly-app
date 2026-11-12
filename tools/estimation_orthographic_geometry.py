"""Bind Blocks with linked elevations to their native plan projections."""

from statistics import median

from tools.probe_cb_block_boundaries import envelope, rectangular


def pixel_scale(view, axis, printed):
    size = view["width" if axis == "x" else "height"]
    anchors = [row for row in printed[view["view_id"]] if row["axis"] == axis]
    scales = [row["value_mm"] * 1000 / (size * (row["bounds"][1] - row["bounds"][0])) for row in anchors]
    if not scales:
        return None
    scale = median(scales)
    # Prefer the longest dimension when the other dimensions agree with it.
    # Very short dimensions can be distorted by trim and arrow placement.
    source = max(anchors, key=lambda row: row["value_mm"])
    if not all(abs(value / scale - 1) < .045 for value in scales):
        return None
    return source["value_mm"] * 1000 / (size * (source["bounds"][1] - source["bounds"][0])), source


def overlap(first, second):
    return max(0, min(first[1], second[1]) - max(first[0], second[0]))


def expand_front(box, extensions, rails, candidates, lower_row):
    """Resolve visible shell borders without including the separate worktop/plinth."""
    face_left, face_top, face_right, face_bottom = box
    width = face_right - face_left
    best = []
    for contour in candidates:
        a, top, b, bottom = contour["bbox"]
        if (rectangular(contour) and a <= face_left + 2 and b >= face_right - 2
                and b - a <= 1.08 * width and top <= face_top and bottom >= face_bottom
                and face_top - top <= 12 and bottom - face_bottom <= 12):
            best.append(contour)
    shell = min(best, key=lambda row: row["area"]) if best else None
    shell_box = shell["bbox"] if shell else box
    ids = [shell["id"]] if shell else []
    left, top, right, bottom = envelope([shell_box, *(row["bbox"] for row in extensions)])
    ids.extend(row["contour_id"] for row in extensions)
    extent = (face_left, face_right)

    # Prefer actual straight shell edges close to the visible fronts.
    for index, target in ((1, face_top), (3, face_bottom)):
        if index == 3 and bottom > face_bottom + 12:
            continue
        options = []
        for contour in candidates:
            for a, b in zip(contour["polygon"], contour["polygon"][1:] + contour["polygon"][:1]):
                if abs(a[1] - b[1]) > 1:
                    continue
                at = (a[1] + b[1]) / 2
                covers = overlap(extent, sorted((a[0], b[0])))
                distance = (target - at) if index == 1 else (at - target)
                if 1.1 <= distance <= 10 and covers >= (.65 if lower_row and index == 1 else .95) * width:
                    options.append((covers, distance, at, contour["id"]))
        if options:
            _, _, at, ident = max(options)
            if index == 1:
                top = min(top, at)
            else:
                bottom = max(bottom, at)
            ids.append(ident)
    for rail in rails:
        a, at, b, _ = rail["bbox"]
        if 0 < at - face_bottom <= 5 and overlap(extent, (a, b)) >= .3 * width:
            bottom = at if bottom <= face_bottom + 12 else bottom
            ids.append(rail["contour_id"])
    return (left, top, right, bottom), ids


def front_envelopes(plan, views):
    records = {}
    plinths = [appearance for part in plan["object_parts"] if part["role"] == "plinth"
               for appearance in part.get("appearances", [])]
    for block in plan["blocks"]:
        appearances = block["appearances"]
        if not isinstance(appearances, list) or len(appearances) != 1:
            continue
        appearance, = appearances
        vid = appearance["view_id"]
        if "positions" not in block:
            continue
        faces = [face for slot in block["positions"] for face in slot]
        view = views[vid]
        box = appearance["bbox"]
        rails = [r for r in plinths if r["view_id"] == vid]
        lower = block["basis"] != "tall_stack_candidate" and any(
            0 < row["bbox"][1] - box[3] <= 5 and
            overlap((box[0], box[2]), (row["bbox"][0], row["bbox"][2])) > .3 * (box[2] - box[0])
            for row in rails)
        extensions = [row for row in block.get("fixed_extensions", []) if row["view_id"] == vid]
        bounds, sources = expand_front(box, extensions, rails, view["candidates"], lower)
        records[block["id"]] = {"view": vid, "box": bounds, "faces": faces, "sources": faces + sources,
                                "basis": block["basis"], "lower": lower, "extensions": extensions, "face_bottom": box[3],
                                "plan_refs": appearance.get("matching_plan_spans", [])}
    return records


def orient_elevations(views, plan, records, printed, linked, span, bind_dimension):
    """Find the two transforms using a marked plan span and a detached shell."""
    scales = [pixel_scale(plan, axis, printed) for axis in "xy"]
    contours = {row["id"]: row for row in plan["candidates"]}
    frame = envelope(row["bbox"] for row in contours.values())
    routes = {}
    primary = []
    for record in records.values():
        vid = record["view"]
        front = views[vid]
        if vid not in linked or not record["plan_refs"]:
            continue
        scale = pixel_scale(front, "x", printed)
        if scale is None:
            continue
        edge = envelope(row["bbox"] for row in front["candidates"])
        target = envelope(contours[ident]["bbox"] for ident in record["plan_refs"])
        for axis, plan_scale in enumerate(scales):
            if plan_scale is None:
                continue
            full_span = frame[axis + 2] - frame[axis]
            front_span = edge[2] - edge[0]
            if abs(scale[0] * front_span / (plan_scale[0] * full_span) - 1) > .035:
                continue
            ratio = full_span / front_span
            for sign in (-1, 1):
                start = frame[axis if sign == 1 else axis + 2]
                projected = sorted(start + sign * ratio * (value - edge[0])
                                   for value in record["box"][::2])
                if all(abs(a - b) <= max(5, .008 * full_span)
                       for a, b in zip(projected, target[axis::2])):
                    primary.append((vid, axis, start, sign * ratio, edge[0], record["plan_refs"]))
    if len(primary) != 1:
        return routes
    vid, axis, start, ratio, origin, refs = primary[0]
    routes[vid] = (axis, start, ratio, origin, refs)
    axis = 1 - axis
    if scales[axis] is None:
        return routes

    for secondary in sorted(linked - routes.keys()):
        view = views[secondary]
        scale = pixel_scale(view, "x", printed)
        if scale is None:
            continue
        related = [row for row in records.values() if row["view"] == secondary]
        ratio = scale[0] / scales[axis][0]
        options = []
        for record in related:
            if record["lower"] or record["extensions"]:
                continue
            boundary = span(view, "x", record["box"][::2], "left shell edge", "right shell edge", record["sources"])
            width = bind_dimension(boundary, printed)
            if width["value_mm"] is None:
                continue
            for contour in contours.values():
                a, b = contour["bbox"][axis::2]
                other = contour["bbox"][1 - axis::2]
                if b - a <= 0 or abs((b - a) * scales[axis][0] / width["value_mm"] - 1) > .035:
                    continue
                if min(abs(other[0] - frame[1 - axis]), abs(other[1] - frame[3 - axis])) > 3:
                    continue
                for sign in (-1, 1):
                    start = a if sign == 1 else b
                    origin = record["box"][0]
                    predicted = [start + sign * ratio * (value - origin)
                                 for row in related for value in row["box"][::2]]
                    if min(predicted) >= frame[axis] - 10 and max(predicted) <= frame[axis + 2] + 10:
                        options.append((axis, start, sign * ratio, origin, [contour["id"]]))
        if len(options) == 1:
            routes[secondary] = options[0]
    return routes


def cross_extent(polygon, axis, interval):
    """Extrema of the source polygon clipped to the block's frontage interval."""
    low, high = interval
    other = 1 - axis
    points = [p[other] for p in polygon if low <= p[axis] <= high]
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        for at in (low, high):
            if min(a[axis], b[axis]) < at < max(a[axis], b[axis]):
                points.append(a[other] + (b[other] - a[other]) * (at - a[axis]) / (b[axis] - a[axis]))
    return (min(points), max(points)) if points else None


def depth_geometry(view, record, route, worktop):
    axis, start, ratio, origin, _ = route
    across = 1 - axis
    lo, hi = sorted(start + ratio * (value - origin) for value in record["box"][::2])
    interval = (lo + 2, hi - 2)
    width = hi - lo
    contours = view["candidates"]
    if width <= 8:
        return None

    if record["lower"] and worktop:
        frame = envelope(row["bbox"] for row in contours)
        rear = frame[across]
        options = []
        for face in contours:
            box = face["bbox"]
            if face["area"] > .75 * (box[2] - box[0]) * (box[3] - box[1]):
                continue
            for a, b in zip(face["polygon"], face["polygon"][1:] + face["polygon"][:1]):
                shared = overlap((lo, hi), sorted((a[axis], b[axis])))
                if abs(a[across] - b[across]) <= 1 and shared >= .35 * width and a[across] > rear + 10:
                    options.append((shared, a[across], face["id"]))
        if options:
            _, outer, ident = max(options)
            wall_refs = [row["id"] for row in contours if abs(row["bbox"][across] - rear) <= 2
                         and overlap((lo, hi), row["bbox"][axis::2]) >= .1 * width]
            if wall_refs:
                return across, (rear, outer), [ident, *wall_refs], True
        return None

    body_options = []
    for face in contours:
        box = face["bbox"]
        if overlap((lo, hi), box[axis::2]) < .86 * width:
            continue
        extent = cross_extent(face["polygon"], axis, interval)
        if extent and extent[1] - extent[0] > .12 * width:
            # An oversized L-shaped base footprint cannot substitute for a separate upper cabinet.
            fit = abs(box[axis] - lo) + abs(box[axis + 2] - hi)
            if record["plan_refs"]:
                hints = [r for r in contours if r["id"] in record["plan_refs"]]
                if not any(abs(r["bbox"][across] - extent[1]) <= 3 for r in hints):
                    continue
            if fit <= .14 * width or record["plan_refs"] or (record["extensions"] and fit <= .6 * width):
                body_options.append((fit, face["id"], extent))
    if not body_options:
        return None
    body_options.sort()
    _, body_id, (rear, front) = body_options[0]
    if len(body_options) > 1 and abs(body_options[1][0] - body_options[0][0]) < 2:
        return None
    strip_candidates = []
    for row in contours:
        box = row["bbox"]
        covered = overlap((lo, hi), box[axis::2])
        if covered > 0 and abs(box[across] - front) <= 2 and 0 < box[across + 2] - front <= .13 * (front - rear):
            strip_candidates.append((covered, row))
    attached = [row for _, row in strip_candidates] if sum(length for length, _ in strip_candidates) >= .8 * width else []
    if attached:
        front = max(row["bbox"][across + 2] for row in attached)
    return across, (rear, front), [body_id, *(row["id"] for row in attached)], False


def resolve_orthographic_group(plan, views, projections, printed, observations, *,
                               span, bind_dimension, elevations, edge_tolerance):
    """Use locked front groups and independent plan evidence where available."""
    top_views = [view for vid, view in views.items() if projections[vid] == "Top view" and view["candidates"]]
    if len(top_views) != 1:
        return {}
    plan_view, = top_views
    plan_id = plan_view["view_id"]
    linked = {b if a == plan_id else a for row in observations if row["evidence_type"] == "matching_topology"
              for a, b in [(row["group_id_a"], row["group_id_b"])] if plan_id in (a, b)}
    linked &= {vid for vid, projection in projections.items() if projection in elevations}
    records = front_envelopes(plan, views)
    routes = orient_elevations(views, plan_view, records, printed, linked, span, bind_dimension)
    if not linked:
        return {}
    worktop = any(row["role"] == "worktop" for row in plan["object_parts"])

    def measure(view, axis, ends, first, last, ids):
        boundary = span(view, axis, ends, first, last, ids)
        value = bind_dimension(boundary, printed)
        exact_print_exists = any(
            row["axis"] == axis and all(abs(a - b) <= edge_tolerance
                                        for a, b in zip(row["bounds"], boundary["bounds_1000"]))
            for row in printed[view["view_id"]])
        if value["value_mm"] is not None or exact_print_exists:
            return value
        calibration = pixel_scale(view, axis, printed)
        if calibration:
            scale, source = calibration
            projected = (ends[1] - ends[0]) * scale
            return {**boundary, "value_mm": round(projected / 5) * 5, "method": "scaled_projection",
                    "sources": [source]}
        return value

    result = {}
    for bid, record in records.items():
        vid = record["view"]
        if vid not in linked:
            continue
        view = views[vid]
        left, top, right, bottom = record["box"]
        lower = record["lower"]
        side_ext = any(row["bbox"][3] >= bottom - 3 and row["bbox"][3] > record["face_bottom"] + 12
                       for row in record["extensions"])
        top_name = "underside of separate worktop" if lower else "top of cabinet shell"
        bottom_name = ("lower edge of owned side panel" if side_ext else "carcass bottom at plinth top"
                       if lower or record["basis"] == "tall_stack_candidate" else "bottom edge of upper cabinet")
        values = {
            "width": measure(view, "x", (left, right), "left edge of owned span", "right edge of owned span",
                             record["sources"]),
            "height": measure(view, "y", (top, bottom), top_name, bottom_name, record["sources"]),
            "depth": {"value_mm": None, "method": "unresolved",
                      "reason": "No separately bound depth footprint on the linked plan"},
        }
        if vid in routes and (depth := depth_geometry(plan_view, record, routes[vid], worktop)):
            axis, ends, ids, proxy = depth
            frontage_axis, start, ratio, origin, anchor_ids = routes[vid]
            binding = {
                "elevation_view_id": vid, "plan_frontage_axis": "xy"[frontage_axis],
                "mapped_frontage_px": sorted(round(start + ratio * (x - origin), 3) for x in (left, right)),
                "anchor_contour_ids": anchor_ids,
            }
            if proxy:
                measure_depth = measure(plan_view, "xy"[axis], ends, "rear wall line",
                                        "outer edge of shared worktop", ids)
                values["depth_proxy"] = {**measure_depth, "method": "shared_worktop_footprint_proxy",
                                         "projection_binding": binding}
            else:
                measure_depth = measure(plan_view, "xy"[axis], ends, "rear footprint edge", "outer footprint edge", ids)
                values["depth"] = {**measure_depth, "projection_binding": binding}
        result[bid] = values
    return result
