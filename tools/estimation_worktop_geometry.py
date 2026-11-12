"""Recover an orthographic worktop outline from linked lower cabinet views."""

from collections import Counter, defaultdict
import re

from tools.estimation_orthographic_geometry import pixel_scale


def _edges(points):
    return zip(points, points[1:] + points[:1])


def _area(points):
    return abs(sum(x * v - u * y for (x, y), (u, v) in _edges(points))) / 2


def _outline(faces, depth):
    counts = Counter()
    for face in faces:
        points = [tuple(round(value, 3) for value in point) for point in face["polygon"]]
        counts.update(tuple(sorted((a, b))) for a, b in _edges(points) if a != b)
    if any(count > 2 for count in counts.values()):
        return None
    neighbors = defaultdict(set)
    for (a, b), count in counts.items():
        if count == 1:
            neighbors[a].add(b)
            neighbors[b].add(a)
    if not neighbors or any(len(edges) != 2 for edges in neighbors.values()):
        return None

    rings = []
    while neighbors:
        start = current = min(neighbors)
        previous = None
        ring = []
        while current in neighbors:
            ring.append(current)
            following = min(neighbors.pop(current) - {previous})
            previous, current = current, following
        if current != start or len(ring) < 3:
            return None
        rings.append(ring)
    outer, *internal = sorted(rings, key=_area, reverse=True)
    if any(min(max(p[i] for p in ring) - min(p[i] for p in ring) for i in (0, 1)) > .04 * depth
           or _area(ring) > .02 * _area(outer) for ring in internal):
        return None
    return outer


def _clip(points, axis, boundary, keep_lower):
    result = []
    for a, b in _edges(points):
        a_inside = (a[axis] <= boundary) if keep_lower else (a[axis] >= boundary)
        b_inside = (b[axis] <= boundary) if keep_lower else (b[axis] >= boundary)
        if a_inside:
            result.append(a)
        if a_inside != b_inside:
            ratio = (boundary - a[axis]) / (b[axis] - a[axis])
            point = tuple(x + ratio * (y - x) for x, y in zip(a, b))
            if point not in (a, b):
                result.append(point)
    return result


def _terminal_seam(outline, faces, starts, inner, ends):
    """Find a transverse seam immediately before the one beveled end."""
    options = []
    for axis in (0, 1):
        cross = 1 - axis
        depth = inner[cross] - starts[cross]
        bevels = [min(a[axis], b[axis]) for a, b in _edges(outline)
                  if abs(a[axis] - b[axis]) > 2 and abs(a[cross] - b[cross]) > 2
                  and abs(max(a[axis], b[axis]) - ends[axis]) < .1 * depth
                  and abs(max(a[cross], b[cross]) - inner[cross]) < .03 * depth]
        for bevel in bevels:
            seams = defaultdict(set)
            for face in faces:
                spans = defaultdict(list)
                for a, b in _edges(face["polygon"]):
                    if abs(a[axis] - b[axis]) < .02 and 0 < bevel - a[axis] <= .16 * depth:
                        spans[round(a[axis], 3)].append(sorted((a[cross], b[cross])))
                for at, intervals in spans.items():
                    end = inner[cross]
                    for low, high in sorted(intervals, reverse=True):
                        if abs(high - end) < .02:
                            end = low
                    if inner[cross] - end >= .5 * depth:
                        seams[at].add(face["id"])
            options.extend((axis, at, sorted(ids)) for at, ids in seams.items() if len(ids) == 2)
    return options[0] if len(options) == 1 else None


def _finish_evidence(understanding, views, projections):
    notes = understanding.get("characteristics") or ()
    contrasting = [note for note in notes if isinstance(note, str)
                   and re.search(r"worktop|countertop|столешниц", note, re.I)
                   and re.search(r"contrast|different (?:material|finish|colou?r)|контраст|другой (?:цвет|материал)", note, re.I)
                   and re.search(r"bevel|angled|chamfer|diagonal|45°|скошен", note, re.I)]
    if not contrasting:
        return None
    renders = [view["view_id"] for view in views.values()
               if projections.get(view["view_id"]) in {"Render", "Axonometric view"}]
    return {"view_id": renders[0] if len(renders) == 1 else None, "notes": contrasting}


def worktop_geometry(blocks, views, printed, understanding, projections):
    """Bind the footprint to both lower runs and keep source and scale evidence."""
    proxies = [block["measurements"]["depth_proxy"] for block in blocks
               if block["measurements"].get("depth_proxy", {}).get("value_mm")]
    view_ids = {row["view_id"] for row in proxies}
    if len(view_ids) != 1 or {row["axis"] for row in proxies} != {"x", "y"}:
        return None
    view = views[next(iter(view_ids))]
    if projections.get(view["view_id"]) != "Top view":
        return None
    shared = set.intersection(*(set(row["contour_ids"]) for row in proxies))
    if len(shared) != 1:
        return None
    linked = set().union(*(row["contour_ids"] for row in proxies))
    candidates = {face["id"]: face for face in view["candidates"]}
    if not linked <= candidates.keys():
        return None
    starts, inner, ends = [], [], []
    for axis, size in enumerate((view["width"], view["height"])):
        name = "xy"[axis]
        across = [row["bounds_1000"] for row in proxies if row["axis"] == name]
        near, lip = (min(row[i] for row in across) * size / 1000 for i in (0, 1))
        if lip <= near or any(abs(row[i] * size / 1000 - target) > 2
                              for row in across for i, target in enumerate((near, lip))):
            return None
        front_end = max(row["projection_binding"]["mapped_frontage_px"][1] for row in proxies
                        if row["projection_binding"]["plan_frontage_axis"] == name)
        edges = [candidates[ident]["bbox"][axis + 2] for ident in linked
                 if abs(candidates[ident]["bbox"][axis + 2] - front_end) <= .08 * (lip - near)]
        if not edges:
            return None
        starts.append(near)
        inner.append(lip)
        ends.append(max(edges))

    faces = [face for face in candidates.values() if all(
        all(starts[axis] - .02 <= point[axis] <= ends[axis] + .02 for axis in (0, 1))
        and any(point[axis] <= inner[axis] + .02 for axis in (0, 1)) for point in face["polygon"])]
    if not linked <= {face["id"] for face in faces}:
        return None
    depth = min(b - a for a, b in zip(starts, inner))
    outline = _outline(faces, depth)
    scales = [pixel_scale(view, axis, printed) for axis in "xy"]
    if not outline or not all(scales):
        return None
    view_id = view["view_id"]
    refs = [f"{view_id}:{face['id']}" for face in faces]
    refs.extend(scale[1]["source_id"] for scale in scales)

    def surface(ident, points, **evidence):
        polygon_mm = [[round((point[i] - starts[i]) * scales[i][0], 3) for i in (0, 1)] for point in points]
        return {"id": ident, "polygon_px": points, "polygon_mm": polygon_mm,
                "area_m2": round(_area(polygon_mm) / 1_000_000, 6), **evidence}

    result = {"view_id": view_id, "area_basis": "gross_plan_outline", "cutout_status": "unresolved",
              "source_refs": refs, "outer": surface("outer", outline), "surfaces": []}
    result["kitchen_worktop"] = bool(re.search(r"\bkitchen\b|кухн", understanding.get("name") or "", re.I))
    finish = _finish_evidence(understanding, views, projections)
    seam = _terminal_seam(outline, faces, starts, inner, ends)
    if not finish:
        result["surfaces"] = [{**result["outer"], "id": "main", "material_role": "main_worktop"}]
    elif seam and finish["view_id"]:
        axis, at, ids = seam
        result["surfaces"] = [
            surface("main", _clip(outline, axis, at, True), material_role="main_worktop"),
            surface("end", _clip(outline, axis, at, False), material_role="contrasting_end"),
        ]
        result["finish_evidence"] = finish
        result["seam_source_refs"] = [f"{view_id}:{ident}" for ident in ids]
    return result
