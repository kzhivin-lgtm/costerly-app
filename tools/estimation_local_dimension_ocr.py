"""Recover source-only numeric labels when Detection has no dimension inventory."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import subprocess

from PIL import Image
import pymupdf


ROTATIONS = {
    0: (None, lambda x, y: (x, y)),
    90: (Image.Transpose.ROTATE_90, lambda x, y: (1 - y, x)),
    180: (Image.Transpose.ROTATE_180, lambda x, y: (1 - x, 1 - y)),
    270: (Image.Transpose.ROTATE_270, lambda x, y: (y, 1 - x)),
}


def read_dimension_labels(pdf, views, reader, unit):
    """Render PDF crops and map confident local OCR boxes back into source coordinates."""
    factors = {"mm": 1, "cm": 10}
    factor = factors[unit]
    with TemporaryDirectory(prefix="estimation-local-dimensions-") as directory:
        sources = {}
        for vid, view in views.items():
            page = pdf[view["page"] - 1]
            x0, y0, x1, y1 = view["bbox_normalized"]
            clip = pymupdf.Rect(x0 * page.rect.width, y0 * page.rect.height,
                               x1 * page.rect.width, y1 * page.rect.height)
            zoom = 2200 / clip.width
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            for angle, (rotation, _) in ROTATIONS.items():
                output = str(Path(directory) / f"{view['page']}-{len(sources):03}.png")
                oriented = image.transpose(rotation) if rotation else image
                oriented.save(output)
                sources[output] = (vid, angle, None)
            # CAD glyphs can be easier to read at the standard page render scale.
            standard = page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), clip=clip, alpha=False)
            output = str(Path(directory) / f"{view['page']}-{len(sources):03}.png")
            standard.save(output)
            sources[output] = (vid, 0, "crop_200dpi")
        if not sources:
            return {}
        response = subprocess.run([str(reader), *sources], capture_output=True, text=True,
                                  check=True, timeout=120)
        results = json.loads(response.stdout)
    labels = {vid: [] for vid in views}
    for name, (vid, angle, render_basis) in sources.items():
        rows = results[name]
        view = views[vid]
        _, restore = ROTATIONS[angle]
        for reading in rows:
            literal = reading["text"].strip()
            if not re.fullmatch(r"[1-9]\d{1,4}", literal) or reading["confidence"] < .8:
                continue
            x0, y0, x1, y1 = reading["bbox_norm"]
            a, b = restore(x0, y0), restore(x1, y1)
            left, right = sorted((a[0], b[0]))
            top, bottom = sorted((a[1], b[1]))
            width, height = (right - left) * view["width"], (bottom - top) * view["height"]
            if min(width, height) <= 0 or max(width, height) < 1.15 * min(width, height):
                continue
            axis = "x" if width > height else "y"
            if render_basis and any(
                row["original_text"] == literal and row["label_axis"] == axis
                and abs(row["normalized_bbox"]["top_left_x"] + row["normalized_bbox"]["bottom_right_x"]
                        - left - right) <= .03
                and abs(row["normalized_bbox"]["top_left_y"] + row["normalized_bbox"]["bottom_right_y"]
                        - top - bottom) <= .03
                for row in labels[vid]
            ):
                continue
            ident = f"{vid}-local-{len(labels[vid]) + 1:02}"
            labels[vid].append({
                "occurrence_id": ident, "original_text": literal, "value_mm": int(literal) * factor,
                "normalized_bbox": {"top_left_x": left, "top_left_y": top,
                                    "bottom_right_x": right, "bottom_right_y": bottom},
                "label_axis": axis, "confidence": reading["confidence"],
                "unit_basis": f"{unit}_caller_assumption", "source_refs": [f"local_ocr:{ident}"],
                **({"render_basis": render_basis} if render_basis else {}),
            })
    return labels
