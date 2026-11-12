"""Read one lateral swing symbol per native contour from PDF strokes."""

from math import dist

import pymupdf


def thin_strokes(page, view):
    width, height = page.rect.width, page.rect.height
    x0, y0, x1, y1 = view["bbox_normalized"]
    clip = pymupdf.Rect(x0 * width, y0 * height, x1 * width, y1 * height)
    zoom = 1100 / clip.width
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
    rotation = page.rotation_matrix

    def point(raw):
        p = raw * rotation
        return (p.x * zoom - pixmap.x, p.y * zoom - pixmap.y)

    strokes = {}
    for path in page.get_drawings():
        if path["type"] != "s" or not path["width"] < 0.4 or path["color"] != (0., 0., 0.):
            continue
        for index, (kind, *points) in enumerate(path["items"]):
            if kind == "l":
                strokes[(path["seqno"], index)] = tuple(map(point, points))
    return pixmap, strokes


def mark_on_face(face, strokes):
    """Require a pair from the opposite corners to one lateral edge of this face."""
    x0, y0, x1, y1 = face["bbox"]
    tolerance = min(5.0, 0.08 * min(x1 - x0, y1 - y0))
    if tolerance <= 0:
        return None

    def corners(x):
        side = [p for p in face["polygon"] if abs(p[0] - x) <= tolerance]
        return min(side, key=lambda p: p[1]), max(side, key=lambda p: p[1])

    matches = []
    for side, apex_x, base_x in (("left", x0, x1), ("right", x1, x0)):
        top, bottom = corners(base_x)
        edge_top, edge_bottom = corners(apex_x)
        edge_height = edge_bottom[1] - edge_top[1]
        if edge_height <= 0 or dist(top, bottom) <= 2 * tolerance:
            continue

        def rays_from(corner):
            for stroke_id, (a, b) in strokes.items():
                for base, apex in ((a, b), (b, a)):
                    fraction = (apex[1] - edge_top[1]) / edge_height
                    if (dist(base, corner) <= tolerance and abs(apex[0] - apex_x) <= tolerance
                            and 0.25 <= fraction <= 0.75):
                        yield stroke_id, base, apex

        lower_rays = list(rays_from(bottom))
        for upper_id, upper_base, upper_apex in rays_from(top):
            for lower_id, lower_base, lower_apex in lower_rays:
                if upper_id == lower_id or dist(upper_apex, lower_apex) > 1.25:
                    continue
                matches.append({
                    "candidate_id": face["id"],
                    "role": "hinged_door",
                    "apex_side_on_view": side,
                    "source_strokes": [upper_id, lower_id],
                    "rays_px": [[upper_base, upper_apex], [lower_base, lower_apex]],
                })
    return matches[0] if len(matches) == 1 else None
