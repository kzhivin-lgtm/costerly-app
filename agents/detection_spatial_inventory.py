"""Legacy V4 visual-map helper.

V5.2 Registry does not use this module. Its equivalent is part of Fusion in
``detection_fusion_candidate_regions``. Retained only for the older separate
visual-map route until that route is retired.
"""

from __future__ import annotations

from typing import Any


_BBOX_KEYS = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")


def _bbox(value: object) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        result = {key: int(value[key]) for key in _BBOX_KEYS}
    except (KeyError, TypeError, ValueError):
        return None
    return result if (
        result["bottom_right_x"] > result["top_left_x"]
        and result["bottom_right_y"] > result["top_left_y"]
    ) else None


def build_detection_spatial_inventory(ocr_package: dict[str, Any] | None) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        try:
            page_number = int(page.get("page_number"))
        except (TypeError, ValueError):
            continue
        ordinal = 0
        for block in page.get("blocks") or []:
            bbox = _bbox(block) if isinstance(block, dict) and block.get("type") == "image" else None
            if bbox is None:
                continue
            ordinal += 1
            inventory.append({"region_id": f"ocr-image-p{page_number:03d}-{ordinal:03d}", "page_number": page_number, "bbox": bbox})
    return inventory


def spatial_inventory_context(inventory: list[dict[str, Any]]) -> str:
    if not inventory:
        return "OCR GRAPHIC REGION INVENTORY: no usable provider graphic regions"
    lines = ["OCR GRAPHIC REGION INVENTORY (legacy visual-map cross-check):"]
    for region in inventory:
        bbox = region["bbox"]
        lines.append(f"{region['region_id']} P{region['page_number']} B={bbox['top_left_x']},{bbox['top_left_y']},{bbox['bottom_right_x']},{bbox['bottom_right_y']}")
    return "\n".join(lines)
