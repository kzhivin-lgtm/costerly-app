"""Draw review overlays on the source PDF using the accepted analysis geometry."""

from collections import defaultdict
from io import BytesIO
from math import isfinite

from PIL import Image, ImageChops, ImageDraw, ImageFilter
import pymupdf


LAYERS = ("front", "block")
_COLORS = ("#1D55A7", "#9D2D7D", "#11735D", "#A45313", "#633DB6", "#BF3A39",
           "#007495", "#675F14", "#AB4A86")
_FRONT_COLORS = dict(zip(
    ("hinged_door", "drawer", "lift_up", "pull_out_shelf", "mirror", "support_leg"),
    _COLORS, strict=False,
))


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
    for row in obj["front"]["faces"]:
        vid, role = row["view_id"], row["role"]
        view = views.get(vid)
        if view is None:
            continue
        native = _polygon(candidates[vid].get(row.get("candidate_id")), view)
        points = native or _rectangle(row.get("bbox_px"), view)
        if points:
            yield vid, [points], _FRONT_COLORS.get(role, "#59636F"), not native


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


def _exterior_image(polygons, color):
    """Stroke the union's outer edges. White gaps enclosed by the block stay clear."""
    left = int(min(x for ring in polygons for x, _ in ring)) - 4
    top = int(min(y for ring in polygons for _, y in ring)) - 4
    right = int(max(x for ring in polygons for x, _ in ring)) + 5
    bottom = int(max(y for ring in polygons for _, y in ring)) + 5
    mask = Image.new("L", (right - left, bottom - top))
    draw = ImageDraw.Draw(mask)
    for ring in polygons:
        draw.polygon([(x - left, y - top) for x, y in ring], fill=255)
    # Close single-pixel seams caused by rounding at a shared edge.
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    ImageDraw.floodfill(mask, (0, 0), 128)
    filled = mask.point([0 if value == 128 else 255 for value in range(256)])
    border = ImageChops.subtract(filled.filter(ImageFilter.MaxFilter(3)), filled.filter(ImageFilter.MinFilter(3)))
    image = Image.new("RGBA", mask.size, color)
    image.putalpha(border)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue(), (left, top, right, bottom)


def _crop_frame(page, view):
    clip = pymupdf.Rect(*(n * (page.rect.width if i % 2 == 0 else page.rect.height)
                          for i, n in enumerate(view["bbox_normalized"])))
    scale = 1100 / clip.width
    pixel_rect = (clip * pymupdf.Matrix(scale, scale)).irect
    return scale, pixel_rect


def _write_layer(source, views, page_marks, *, layer, object_id):
    with pymupdf.open() as output:
        for source_index in sorted({view["page"] - 1 for view in views.values()}):
            output.insert_pdf(source, from_page=source_index, to_page=source_index)
            page = output[-1]
            page.remove_rotation()
            for vid, polygons, color, approximate, label in page_marks[source_index]:
                scale, pixels = _crop_frame(page, views[vid])

                def point(x, y):
                    return pymupdf.Point((x + pixels.x0) / scale, (y + pixels.y0) / scale)

                if len(polygons) > 1:
                    png, (left, top, right, bottom) = _exterior_image(polygons, color)
                    page.insert_image(pymupdf.Rect(point(left, top), point(right, bottom)), stream=png)
                else:
                    ring, = polygons
                    path = [point(x, y) for x, y in ring]
                    rgb = tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
                    page.draw_polyline([*path, path[0]], color=rgb, width=max(.7, 2 / scale),
                                       dashes="[3 2] 0" if approximate else None)
                if label:
                    x, y = min((p for ring in polygons for p in ring), key=lambda p: (p[1], p[0]))
                    anchor = point(x, y)
                    width = pymupdf.get_text_length(label, fontsize=9)
                    anchor.x = min(max(anchor.x + 2, 3), page.rect.width - width - 4)
                    anchor.y = min(max(anchor.y + 11, 12), page.rect.height - 4)
                    page.draw_rect(pymupdf.Rect(anchor.x - 1, anchor.y - 8, anchor.x + width + 1, anchor.y + 2),
                                   color=None, fill=(1, 1, 1))
                    page.insert_text(anchor, label, fontsize=9, color=tuple(
                        int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)))
        output.set_metadata({"title": f"{layer.title()} overlay - {object_id}"})
        return output.tobytes(garbage=3, deflate=True)


def build_overlay_pdfs(pdf_bytes, result, views):
    """Yield one annotated PDF per object and layer that has localized evidence."""
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as source:
        for object_id, obj in result["objects"].items():
            owned = {view["view_id"]: view for view in views if view["object_id"] == object_id}
            for layer, marks in (
                ("front", ((*mark, None) for mark in _front_marks(obj, owned))),
                ("block", _block_marks(obj, owned)),
            ):
                pages = defaultdict(list)
                for mark in marks:
                    pages[owned[mark[0]]["page"] - 1].append(mark)
                if pages:
                    yield object_id, layer, _write_layer(source, owned, pages, layer=layer, object_id=object_id)
