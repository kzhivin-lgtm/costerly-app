"""Draw review overlays on the source PDF using the accepted analysis geometry."""

from collections import Counter
from itertools import combinations
from math import isfinite

import pymupdf

from use_cases.estimation_overlay_geometry import exterior_rings, separate_seams, volume_edges


_COLORS = ("#1D55A7", "#9D2D7D", "#11735D", "#A45313", "#633DB6", "#BF3A39",
           "#007495", "#675F14", "#AB4A86")
_FRONT_STYLES = {
    "hinged_door": ("Hinged doors", "#1254A5"),
    "drawer": ("Drawers", "#A22562"),
    "lift_up": ("Lift-up fronts", "#11735D"),
    "pull_out_shelf": ("Pull-out shelves", "#008071"),
    "mirror": ("Mirrors", "#6A40B3"),
    "fixed_open_shelf": ("Open shelves", "#B45309"),
    "support_leg": ("Legs", "#007495"),
}


def _polygon(points, view):
    if not isinstance(points, (list, tuple)) or len(points) < 3:
        return None
    if not all(isinstance(p, (list, tuple)) and len(p) == 2
               and all(type(x) in (int, float) and isfinite(x) for x in p) for p in points):
        return None
    return [(min(max(x, 0), view["width"]), min(max(y, 0), view["height"])) for x, y in points]


def _rectangle(box, view):
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return None
    left, top, right, bottom = box
    if not all(type(x) in (int, float) and isfinite(x) for x in box) or left >= right or top >= bottom:
        return None
    return _polygon([(left, top), (right, top), (right, bottom), (left, bottom)], view)


def _front_marks(obj, views):
    candidates = {vid: {row["id"]: row["polygon"] for row in view["candidates"]}
                  for vid, view in views.items()}
    front = obj["front"]
    support_views = front.get("support_appearance_counts_by_view") or {}
    counted_supports = front.get("instance_counts", {}).get("support_leg")
    full_support_views = {vid for vid, count in support_views.items() if vid in views and count == counted_supports}
    for row in front["faces"]:
        vid, role = row["view_id"], row["role"]
        view = views.get(vid)
        if view is None:
            continue
        if role == "support_leg" and full_support_views and vid not in full_support_views:
            # A linked partial appearance adds no leg to the known complete projection.
            continue
        native = _polygon(candidates[vid].get(row.get("candidate_id")), view)
        points = native or _rectangle(row.get("bbox_px"), view)
        if points:
            yield vid, [points], _FRONT_STYLES.get(role, (None, "#59636F"))[1], not native, role


def _block_marks(obj, views):
    for index, block in enumerate(obj["planner"]["blocks"]):
        envelopes = block.get("envelopes", {})
        color = _COLORS[index % len(_COLORS)]
        for vid, view in views.items():
            envelope = envelopes.get(vid, {})
            polygons = [_polygon(p, view) for p in envelope.get("polygons_px", ())]
            polygons = [p for p in polygons if p]
            approximate = "top_region_ids" in envelope
            if not polygons and isinstance(block["appearances"], list):
                for appearance in block["appearances"]:
                    if appearance["view_id"] != vid:
                        continue
                    # A native frame can trace around internal openings.
                    # The Planner's elevation bounds describe the whole block.
                    points = _rectangle(appearance.get("bbox"), view)
                    approximate = True
                    if points:
                        polygons.append(points)
            if polygons:
                yield vid, polygons, color, approximate, block["id"]


def _crop_frame(page, view):
    clip = pymupdf.Rect(*(n * (page.rect.width if i % 2 == 0 else page.rect.height)
                          for i, n in enumerate(view["bbox_normalized"])))
    scale = 1100 / clip.width
    return scale, (clip * pymupdf.Matrix(scale, scale)).irect


def _view_priority(view, projection, marks):
    reliable = sum(not mark[2] for mark in marks)
    return (bool(marks), projection == "Axonometric view" and bool(reliable),
            projection == "Front elevation", reliable, len(marks), -view.get("number", 0))


def _covering_views(views, projections, marks, *, layer):
    ordered = sorted(views, key=lambda vid: _view_priority(views[vid], projections.get(vid), marks[vid]),
                     reverse=True)
    if layer == "front":
        # Front localizes outlines by source view. Count and label them on that page only.
        return [vid for vid in ordered if marks[vid]] or ordered[:1]

    coverage = {vid: {mark[3] for mark in marks[vid]} for vid in ordered if marks[vid]}
    if not coverage:
        return ordered[:1]
    remaining = set().union(*coverage.values())
    for vid, blocks in coverage.items():
        if blocks == remaining:
            return [vid]
    for first, second in combinations(coverage, 2):
        if coverage[first] | coverage[second] == remaining:
            return [first, second]

    selected = set()
    while remaining:
        vid = max(coverage, key=lambda view_id: len(coverage[view_id] & remaining))
        selected.add(vid)
        remaining -= coverage[vid]
    return [vid for vid in ordered if vid in selected]


def _rgb(code):
    return tuple(int(code[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _source_lines(page, view):
    from tools.estimation_native_islands import extraction

    _, lines = extraction(page, page.get_drawings(), view["bbox_normalized"])
    return [(a, b) for a, b, width, color, _ in lines if width >= .65 and color == (0., 0., 0.)]


def _crop_extent(view, marks):
    bounds = pymupdf.Rect(0, 0, view["width"], view["height"])
    points = [point for polygons, *_ in marks for ring in polygons for point in ring]
    if not points:
        return bounds
    left, top = min(x for x, _ in points), min(y for _, y in points)
    right, bottom = max(x for x, _ in points), max(y for _, y in points)
    pad = max(16, .055 * (right - left))
    # Include context immediately around the assembly, while keeping the
    # original Island bounds that exclude adjacent objects.
    return bounds & pymupdf.Rect(left - pad, top - pad, right + pad, bottom + pad)


def _draw_ring(page, path, color, *, width, approximate=False, fill=False):
    page.draw_polyline([*path, path[0]], color=color, width=width, lineJoin=1, lineCap=1,
                       dashes="[6 4] 0" if approximate else None,
                       fill=color if fill else None, fill_opacity=.10 if fill else 0)


def _front_legend(marks):
    counts = Counter(mark[3] for mark in marks)
    rows = [(name, count, color) for role, (name, color) in _FRONT_STYLES.items() if (count := counts.pop(role, 0))]
    rows.extend((role.replace("_", " ").capitalize(), count, "#59636F") for role, count in sorted(counts.items()))
    return rows


def _legend_rows(marks):
    lines, offset = [], 0
    for name, count, color in _front_legend(marks):
        text = f"{name}  {count}"
        width = 46 + pymupdf.get_text_length(text, fontsize=12)
        if not lines or offset + width > 948:
            lines.append([])
            offset = 0
        lines[-1].append((offset, text, color))
        offset += width
    return lines


def _draw_blocks(page, point, marks, source_segments, zoom):
    shells = [(label, _rgb(color), approximate, exterior_rings(polygons))
              for polygons, color, approximate, label in marks]
    for label, color, approximate, rings in shells:
        neighbors = [ring for other, _, _, cluster in shells if other != label for ring in cluster]
        for ring in rings:
            outline = separate_seams(ring, neighbors, offset=5.5 / zoom)
            _draw_ring(page, [point(*p) for p in outline], color, width=4.6, approximate=approximate)
            if len(rings) == 1 and not approximate:
                for center, index, fraction in volume_edges(ring, source_segments):
                    a, b = outline[index], outline[(index + 1) % len(outline)]
                    end = tuple(x + fraction * (y - x) for x, y in zip(a, b))
                    page.draw_line(point(*center), point(*end), color=color, width=4.6, lineCap=1)
    used = []
    for label, color, _, rings in shells:
        if not rings:
            continue
        ring = max(rings, key=lambda ring: len(ring) and pymupdf.Rect(
            min(x for x, _ in ring), min(y for _, y in ring), max(x for x, _ in ring), max(y for _, y in ring)
        ).get_area())
        xs, ys = zip(*(point(*p) for p in ring))
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        label_width = max(36, 12 + pymupdf.get_text_length(label, fontname="hebo", fontsize=11))
        positions = [p for p in (pymupdf.Rect(x, y, x + label_width, y + 20)
                     for y in (top + 21, top + (bottom - top) * .55, bottom - 22)
                     for x in (left + 15, (left + right - label_width) / 2, right - label_width - 6))
                     if p in page.rect and not any(p.intersects(other) for other in used)]
        if not positions:
            continue
        box = positions[0]
        used.append(box)
        page.draw_rect(box, color=None, fill=color)
        page.insert_text((box.x0 + 6, box.y0 + 14), label, fontname="hebo", fontsize=11, color=(1, 1, 1))


def _write_page(output, source, view, projection, marks, *, layer, title, crop_marks,
                block_coverage, page_index, page_count):
    original = source[view["page"] - 1]
    original.remove_rotation()
    extent = _crop_extent(view, crop_marks)
    if page_count > 1 and extent.x1 >= .95 * view["width"]:
        extent.x1 = view["width"]
    scale, pixels = _crop_frame(original, view)
    clip = pymupdf.Rect((extent.x0 + pixels.x0) / scale, (extent.y0 + pixels.y0) / scale,
                        (extent.x1 + pixels.x0) / scale, (extent.y1 + pixels.y0) / scale)
    zoom = min(948 / extent.width, 630 / extent.height)
    left = (1000 - extent.width * zoom) / 2
    canvas = pymupdf.Rect(left, 75, left + extent.width * zoom, 75 + extent.height * zoom)
    ink, muted = _rgb("#18263D"), _rgb("#536176")
    legend = _legend_rows(marks) if layer == "front" else []
    displayed_blocks, total_blocks = block_coverage
    partial_blocks = layer == "block" and bool(marks) and len(marks) < total_blocks
    footer = 27 + (24 * len(legend) if marks else 28) + (24 if partial_blocks else 0)

    def point(x, y):
        return pymupdf.Point(canvas.x0 + (x - extent.x0) * zoom, canvas.y0 + (y - extent.y0) * zoom)

    page = output.new_page(width=1000, height=canvas.y1 + footer)
    if pymupdf.get_text_length(title, fontname="hebo", fontsize=23) > 820:
        while title and pymupdf.get_text_length(title + "...", fontname="hebo", fontsize=23) > 820:
            title = title[:-1]
        title += "..."
    page.insert_text((27, 35), title, fontname="hebo", fontsize=23, color=ink)
    view_id = view["view_id"].removeprefix("view-")
    view_label = f"V{int(view_id):02d}" if view_id.isdecimal() else view["view_id"]
    subtitle = f"{view_label}  /  {projection or 'Drawing view'}"
    if page_count > 1:
        subtitle += f"  /  View {page_index} of {page_count}"
    page.insert_text((28, 55), subtitle, fontsize=11, color=muted)
    label = layer.title()
    page.insert_text((974 - pymupdf.get_text_length(label, fontname="hebo", fontsize=22), 37),
                     label, fontname="hebo", fontsize=22, color=ink)
    page.draw_line((26, 64), (974, 64), color=_rgb("#DAE2EA"), width=1)
    page.show_pdf_page(canvas, source, view["page"] - 1, clip=clip)
    if layer == "front":
        for (ring,), color, approximate, _ in marks:
            _draw_ring(page, [point(*p) for p in ring], _rgb(color), width=2,
                       approximate=approximate, fill=True)
        for index, row in enumerate(legend):
            y = canvas.y1 + 26 + index * 24
            for offset, name, color in row:
                x, shade = 28 + offset, _rgb(color)
                page.draw_rect(pymupdf.Rect(x, y - 10, x + 11, y + 1), color=None, fill=shade)
                page.insert_text((x + 18, y), name, fontsize=12, color=ink)
    else:
        segments = _source_lines(original, view) if marks and projection == "Axonometric view" else []
        _draw_blocks(page, point, marks, segments, zoom)
    if not marks:
        page.insert_text((28, canvas.y1 + 28), "No localized elements on this view.", fontsize=12, color=muted)
    elif partial_blocks:
        message = f"{len(marks)} blocks on this view. {displayed_blocks} of {total_blocks} blocks shown in this PDF."
        page.insert_text((28, canvas.y1 + 28), message, fontsize=12, color=muted)


def build_overlay_pdfs(pdf_bytes, result, views, *, project_name=""):
    """Yield one Front PDF and one Block PDF per object, with one source crop per page."""
    projections = result.get("islands", {})
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as source:
        for object_id, obj in result["objects"].items():
            owned = {view["view_id"]: view for view in views if view["object_id"] == object_id}
            if not owned:
                continue
            name = result.get("understanding", {}).get(object_id, {}).get("name") or object_id
            title = f"{project_name} | {name}" if project_name else name
            blocks = {vid: [] for vid in owned}
            for vid, *mark in _block_marks(obj, owned):
                blocks[vid].append(mark)
            fronts = {vid: [] for vid in owned}
            for vid, *mark in _front_marks(obj, owned):
                fronts[vid].append(mark)
            total_blocks = len(obj["planner"]["blocks"])
            for layer, by_view in (("front", fronts), ("block", blocks)):
                selected = _covering_views(owned, projections, by_view, layer=layer)
                displayed = {mark[3] for vid in selected for mark in blocks[vid]} if layer == "block" else set()
                with pymupdf.open() as output:
                    for index, vid in enumerate(selected, start=1):
                        crop_marks = [*fronts[vid], *blocks[vid]] if layer == "front" else blocks[vid]
                        _write_page(output, source, owned[vid], projections.get(vid), by_view[vid],
                                    layer=layer, title=title, crop_marks=crop_marks,
                                    block_coverage=(len(displayed), total_blocks),
                                    page_index=index, page_count=len(selected))
                    output.set_metadata({"title": f"{title} | {layer.title()}"})
                    yield object_id, layer, output.tobytes(garbage=3, deflate=True)
