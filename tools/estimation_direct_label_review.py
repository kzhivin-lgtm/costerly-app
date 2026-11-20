"""Verify printed labels on source pixels owned by each native contour."""

from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from math import ceil, floor
import json

# The API permits at least100 images per request. Two reference images plus
#90 panel interiors stay within that limit; larger views are covered in batches.
# https://platform.claude.com/docs/en/build-with-claude/vision
PANELS_PER_REQUEST = 90
REVIEW = """Read direct printed component labels from the supplied native-panel
interiors. Each panel image is independently clipped to exactly one closed
source contour. White pixels outside that contour are not part of the panel.
The full drawing and neutral map are context only. For an ID, transcribe words
from THAT panel image only, never borrow text from another panel or the overview.
Record mirror only when a word naming a mirror is actually printed inside that
panel. An arrow or leader crossing a panel is not a direct printed label.
Inspect every supplied contour, including empty panels. Do not infer material,
function or quantities from shape. No expected number of labels is supplied.
Return JSON only:
{"reviewed_contour_ids":["Cxx"],
"direct_labels":[{"id":"Cxx","role":"mirror","source_text":"exact printed word"}],
"unresolved_contour_ids":[]}
List every supplied ID exactly once in reviewed_contour_ids. List an ID as
unresolved only when a real printed component word is visible but cannot be
read or owned confidently. A panel with no such words is simply empty, not
unresolved. An empty direct_labels list is valid. Do not add other IDs."""


def render_panel_tiles(page, view):
    """Keep original PDF pixels inside each polygon, at the existing3x zoom."""
    import pymupdf
    from PIL import Image, ImageDraw

    x0, y0, x1, y1 = view["bbox_normalized"]
    clip = pymupdf.Rect(x0 * page.rect.width, y0 * page.rect.height,
                        x1 * page.rect.width, y1 * page.rect.height)
    zoom = 1100 / clip.width
    low = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, alpha=False)
    high = page.get_pixmap(matrix=pymupdf.Matrix(zoom * 3, zoom * 3), clip=clip, alpha=False)
    source = Image.frombytes("RGB", (high.width, high.height), high.samples)
    tiles = []
    for face in view["candidates"]:
        polygon = [((x + low.x) * 3 - high.x, (y + low.y) * 3 - high.y) for x, y in face["polygon"]]
        left = max(0, floor(min(x for x, y in polygon)) - 1)
        top = max(0, floor(min(y for x, y in polygon)) - 1)
        right = min(high.width, ceil(max(x for x, y in polygon)) + 1)
        bottom = min(high.height, ceil(max(y for x, y in polygon)) + 1)
        if left >= right or top >= bottom:
            raise ValueError("Native contour has no source image interior")
        crop = source.crop((left, top, right, bottom))
        mask = Image.new("L", crop.size, 0)
        ImageDraw.Draw(mask).polygon([(x - left, y - top) for x, y in polygon], fill=255)
        crop = Image.composite(crop, Image.new("RGB", crop.size, "white"), mask)
        crop.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        buffer = BytesIO(); crop.save(buffer, format="PNG")
        image = buffer.getvalue()
        tiles.append({"id": face["id"], "png": image, "bbox_px": face["bbox"],
                      "polygon_px": face["polygon"], "image_sha256": sha256(image).hexdigest(),
                      "image_size": list(crop.size)})
    return tiles


def reconcile_direct_labels(invoke, request, initial, bind, *, view_id, findings, panel_tiles):
    """One independent ownership pass, with complete coverage and saved dissent."""
    if not panel_tiles:
        return initial
    all_ids = [tile["id"] for tile in panel_tiles]
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("Direct-label tiles require unique native IDs")
    responses = []
    for start in range(0, len(panel_tiles), PANELS_PER_REQUEST):
        batch = panel_tiles[start:start + PANELS_PER_REQUEST]
        expected = {tile["id"] for tile in batch}
        review_request = deepcopy(request)
        review_request["system"] = REVIEW
        review_request["max_tokens"] = max(2500, len(batch) * 24)
        content = review_request["messages"][0]["content"][:4]
        content.append({"type": "text", "text": json.dumps({"contour_ids": [t["id"] for t in batch]})})
        for tile in batch:
            content.extend([{"type": "text", "text": "Native panel interior " + tile["id"]},
                {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                "data": b64encode(tile["png"]).decode("ascii")}}])
        review_request["messages"][0]["content"] = content

        def validate(raw):
            seen, labels, unresolved = raw["reviewed_contour_ids"], raw["direct_labels"], raw["unresolved_contour_ids"]
            if (not isinstance(seen, list) or set(seen) != expected or len(seen) != len(expected)
                    or not isinstance(labels, list) or not isinstance(unresolved, list)
                    or len(set(unresolved)) != len(unresolved) or not set(unresolved) <= expected):
                raise ValueError("Direct-label review must cover every native panel")
            if any(row.get("id") not in expected or not isinstance(row.get("role"), str)
                   or not row["role"].strip() or not isinstance(row.get("source_text"), str)
                   or not row["source_text"].strip() for row in labels):
                raise ValueError("Direct labels require an owned contour and literal source text")
            bind({**initial["readings"], "direct_labels": [row for row in labels if row["role"] == "mirror"]})
            if {row["id"] for row in labels} & set(unresolved):
                raise ValueError("A direct label cannot also be unresolved")
            return raw

        responses.append(invoke(f"direct-label-review-{view_id}-{start // PANELS_PER_REQUEST + 1:03}",
                                review_request, validate))
    transcriptions = [row for response in responses for row in response["direct_labels"]]
    labels = [row for row in transcriptions if row["role"] == "mirror"]
    result = bind({**initial["readings"], "direct_labels": labels})
    attached = {row["candidate_id"] for row in result["items"] if row["role"] == "mirror"}
    pending = (any(response["unresolved_contour_ids"] for response in responses)
               or bool({row["id"] for row in labels} - attached))
    result["direct_label_review"] = {"status": "unresolved" if pending else "reviewed",
        "initial_readings": deepcopy(initial["readings"]), "reviews": responses,
        "source_findings": deepcopy([row for row in findings or () if row["source"].get("view_id") == view_id]),
        "other_transcriptions": [row for row in transcriptions if row["role"] != "mirror"],
        "contour_tiles": [{k: v for k, v in tile.items() if k != "png"} for tile in panel_tiles],
        "selection_basis": "independent_transcription_inside_each_native_contour"}
    if pending:
        result["issues"].append({"view_id": view_id, "role": "mirror", "reason": "front_role_review_pending"})
    return result
