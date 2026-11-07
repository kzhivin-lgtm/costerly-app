"""Coordinate-aware presentation of existing immutable evidence, no new detection."""
from __future__ import annotations

import base64
from io import BytesIO
import json
import math
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont
from use_cases.estimation_dimension_graph import source_coordinate_frame as _source_frame


def page_content(*, page_bytes: bytes, storage_ref: str, page_number: int,
                 payloads: Sequence[Mapping[str, Any]], views: Sequence[Mapping[str, Any]] | None = None,
                 detail_budget: int = 6, include_single_detail: bool = False) -> tuple[list[dict[str, Any]], int]:
    """Full page plus bounded view details, mapped from documented render scale.

    One synchronous preparation per existing provider request. No network,
    polling or model call. Unknown coordinate frames never authorize a crop.
    Details are alternate views of the SAME evidence, never new objects.
    """
    content = [{"type": "text", "text": json.dumps({"source_evidence_ref": storage_ref, "page_number": page_number})},
               {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(page_bytes).decode("ascii")}}]
    try:
        source = Image.open(BytesIO(page_bytes))
    except (OSError, ValueError):
        return content, 0  # Existing provider validation owns invalid image input.
    regions = []
    seen = set()
    for payload in payloads:
        frame = _source_frame(payload, page_number)
        if not frame:
            continue
        candidates = views if views is not None else [
            {"view_id": f"p{page_number}-view-{index:03d}", "bbox": region, "page_number": page_number}
            for page in (payload.get("object") or {}).get("evidence_pages") or [] if page.get("page_number") == page_number
            for index, region in enumerate(page.get("regions") or [], 1)
        ]
        for view in candidates:
            if view.get("page_number") != page_number:
                continue
            if view.get("object_id", (payload.get("object") or {}).get("object_id")) != (payload.get("object") or {}).get("object_id"):
                continue
            box = view.get("bbox") or {}
            view_frame = view.get("coordinate_frame_pixels", frame)
            try:
                coords = [float(box[key]) / float(view_frame[index % 2]) for index, key in enumerate(
                    ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y"))]
            except (KeyError, TypeError, ValueError):
                continue
            if not all(math.isfinite(value) and 0 <= value <= 1.01 for value in coords) or coords[2] <= coords[0] or coords[3] <= coords[1]:
                continue
            signature = tuple(round(value, 5) for value in coords)
            if signature in seen:
                continue
            seen.add(signature)
            regions.append({"view_id": view["view_id"], "object_id": (payload.get("object") or {}).get("object_id"),
                            "bbox_normalized": coords, "coordinate_frame_pixels": list(view_frame)})
    metadata = {"page_number": page_number, "source_evidence_ref": storage_ref,
                "displayed_image_pixels": list(source.size), "view_regions": regions,
                "coordinate_note": "OCR and view bboxes use coordinate_frame_pixels, not displayed_image_pixels. Normalized boxes locate the same source regions."}
    content.insert(0, {"type": "text", "text": json.dumps(metadata, separators=(",", ":"))})
    used = 0
    if len(regions) > 1 or (include_single_detail and regions):
        for region in regions[:max(0, detail_budget)]:
            x1, y1, x2, y2 = region["bbox_normalized"]
            # Small context margin retains nearby dimension endpoints.
            box = (max(0, int((x1 - .015) * source.width)), max(0, int((y1 - .015) * source.height)),
                   min(source.width, math.ceil((x2 + .015) * source.width)), min(source.height, math.ceil((y2 + .015) * source.height)))
            crop = source.crop(box)
            # Keep the generated view identity attached to its pixels. The
            # source crop is unchanged below this explicitly non-source header.
            label = f"VIEW {region['view_id']} | GENERATED LABEL"
            font = ImageFont.load_default(size=14)
            label_width = ImageDraw.Draw(crop).textbbox((0, 0), label, font=font)[2] + 12
            labelled = Image.new("RGB", (max(crop.width, label_width), crop.height + 32), "white")
            labelled.paste(crop, (0, 32))
            ImageDraw.Draw(labelled).text((6, 8), label, fill="black", font=font)
            buffer = BytesIO()
            labelled.save(buffer, format="WEBP", quality=95)
            content.extend([
                {"type": "text", "text": json.dumps({"detail_of_existing_view": region, "source_evidence_ref": storage_ref,
                    "generated_header_height_px": 32,
                    "note": "Enlarged view context from the SAME page/object. Top header is a generated locator, not drawing evidence. Do not count another object or duplicate components."})},
                {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(buffer.getvalue()).decode("ascii")}},
            ])
            used += 1
    return content, used
