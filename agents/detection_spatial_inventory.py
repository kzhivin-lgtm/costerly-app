"""Passive OCR graphic-region audit for Detection V4.23.

Mistral ``image`` blocks are layout hints. They are intentionally not an
object-boundary contract and never validate or alter the Registry response.
"""

from __future__ import annotations

from typing import Any


_BBOX_KEYS = (
    "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
)


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        result = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    if (
        result["bottom_right_x"] <= result["top_left_x"]
        or result["bottom_right_y"] <= result["top_left_y"]
    ):
        return None
    return result


def build_detection_spatial_inventory(
    ocr_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return ordered provider graphic regions for audit and visual re-check."""
    inventory: list[dict[str, Any]] = []
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number < 1:
            continue
        ordinal = 0
        for block in page.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "image":
                continue
            bbox = _bbox(block)
            if bbox is None:
                continue
            ordinal += 1
            inventory.append({
                "region_id": f"ocr-image-p{page_number:03d}-{ordinal:03d}",
                "page_number": page_number,
                "bbox": bbox,
            })
    return inventory


def spatial_inventory_context(inventory: list[dict[str, Any]]) -> str:
    """Render the compact passive reference appended after ordinary OCR text."""
    if not inventory:
        return "OCR GRAPHIC REGION INVENTORY: no usable provider graphic regions"
    lines = [
        "OCR GRAPHIC REGION INVENTORY (passive post-visual cross-check only):"
    ]
    for region in inventory:
        bbox = region["bbox"]
        lines.append(
            f"{region['region_id']} P{region['page_number']} "
            f"B={bbox['top_left_x']},{bbox['top_left_y']},"
            f"{bbox['bottom_right_x']},{bbox['bottom_right_y']}"
        )
    return "\n".join(lines)
