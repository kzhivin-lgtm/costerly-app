"""Render one verified OCR region as a bounded source-derived preview."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping

from PIL import Image


def crop_ocr_region_to_webp(
    *,
    page_image: bytes,
    page_dimensions: Mapping[str, Any],
    bbox: Mapping[str, Any],
    padding_ratio: float = 0.06,
) -> bytes:
    """Crop pixel-coordinate OCR bbox with bounded padding, never resize source geometry."""
    if not 0 <= padding_ratio <= 0.2:
        raise ValueError("padding_ratio must be between 0 and 0.2")
    try:
        source_width = float(page_dimensions["width"])
        source_height = float(page_dimensions["height"])
        left = float(bbox["top_left_x"])
        top = float(bbox["top_left_y"])
        right = float(bbox["bottom_right_x"])
        bottom = float(bbox["bottom_right_y"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("page dimensions and bbox must be numeric") from exc
    # Vision output can express preview coordinates as 0..1 fractions even
    # though OCR page geometry is measured in pixels.
    if all(0 <= value <= 1 for value in (left, top, right, bottom)):
        left, right = left * source_width, right * source_width
        top, bottom = top * source_height, bottom * source_height
    if source_width <= 0 or source_height <= 0 or not (0 <= left < right <= source_width and 0 <= top < bottom <= source_height):
        raise ValueError("bbox must be inside the OCR page dimensions")
    with Image.open(BytesIO(page_image)) as source:
        image = source.convert("RGB")
        scale_x = image.width / source_width
        scale_y = image.height / source_height
        pad_x = (right - left) * padding_ratio
        pad_y = (bottom - top) * padding_ratio
        crop = image.crop((
            max(0, int((left - pad_x) * scale_x)),
            max(0, int((top - pad_y) * scale_y)),
            min(image.width, int((right + pad_x) * scale_x)),
            min(image.height, int((bottom + pad_y) * scale_y)),
        ))
        if crop.width < 1 or crop.height < 1:
            raise ValueError("bbox produced an empty crop")
        result = BytesIO()
        crop.save(result, format="WEBP", quality=82, method=6)
        return result.getvalue()
