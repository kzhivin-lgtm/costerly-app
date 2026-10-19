"""Deterministic OCR-derived inspection regions for Detection V4.

These are not commercial objects and cannot establish a merge. They are a
complete, provider-derived list of graphical areas the Registry must inspect
before it makes its proof graph. The list deliberately retains only OCR image
blocks: text, tables and title blocks remain full page-level Evidence when the
page belongs to an object, but must not inflate the object search space.
"""

from __future__ import annotations

from typing import Any


_BBOX_KEYS = (
    "top_left_x",
    "top_left_y",
    "bottom_right_x",
    "bottom_right_y",
)


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        bbox = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    if (
        bbox["bottom_right_x"] <= bbox["top_left_x"]
        or bbox["bottom_right_y"] <= bbox["top_left_y"]
    ):
        return None
    return bbox


def build_detection_spatial_inventory(
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return ordered OCR image regions with usable page coordinates.

    Mistral OCR 4.1 exposes graphical page geometry as ``image`` blocks, not
    vector-line primitives. Keep their native order, which makes IDs stable
    across the same OCR response and suitable for strict response validation.
    """
    regions: list[dict[str, Any]] = []
    for raw_page in (ocr_package or {}).get("pages") or []:
        if not isinstance(raw_page, dict):
            continue
        try:
            page_number = int(raw_page.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number < 1:
            continue
        ordinal = 0
        for block in raw_page.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            bbox = _bbox(block)
            if bbox is None:
                continue
            ordinal += 1
            regions.append(
                {
                    "region_id": f"ocr-image-p{page_number:03d}-{ordinal:03d}",
                    "page_number": page_number,
                    "bbox": bbox,
                }
            )
    return regions


def spatial_inventory_context(regions: list[dict[str, Any]]) -> str:
    """Render compact, literal inspection coordinates for the Registry prompt."""
    if not regions:
        return "OCR GRAPHIC REGION INVENTORY: unavailable"
    lines = [
        "OCR GRAPHIC REGION INVENTORY (mandatory inspection coordinates, not object decisions):"
    ]
    for region in regions:
        bbox = region["bbox"]
        lines.append(
            f"{region['region_id']} P{region['page_number']} "
            f"B={bbox['top_left_x']},{bbox['top_left_y']},"
            f"{bbox['bottom_right_x']},{bbox['bottom_right_y']}"
        )
    return "\n".join(lines)
