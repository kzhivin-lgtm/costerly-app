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


def validate_detection_spatial_islands(
    islands: object,
    *,
    spatial_regions: list[dict[str, Any]],
    page_count: int,
) -> list[dict[str, Any]]:
    """Validate the model's independent visual-island pass.

    OCR image blocks are a recall aid, not a boundary oracle.  Therefore an
    island may be ``vision_only`` when the page rendering contains a bounded
    depiction that OCR did not emit as an image block.  Conversely, every OCR
    image block must be represented by at least one island, including generic
    plans and other non-object context.
    """
    if not isinstance(islands, list):
        raise ValueError("spatial islands are invalid")
    region_pages = {
        str(region.get("region_id")): region.get("page_number")
        for region in spatial_regions
        if isinstance(region, dict)
    }
    cited_region_ids: set[str] = set()
    for index, island in enumerate(islands, start=1):
        required = {
            "island_id", "page_number", "location_hint", "visual_description",
            "classification", "observation_basis", "source_region_ids",
        }
        if not isinstance(island, dict) or set(island) != required:
            raise ValueError("spatial island fields are invalid")
        if str(island["island_id"]) != f"island-{index:03d}":
            raise ValueError("spatial island IDs must be ordered")
        page_number = island["page_number"]
        if (
            not isinstance(page_number, int)
            or not 1 <= page_number <= page_count
            or island["classification"] not in {"object_candidate", "non_object_context"}
            or island["observation_basis"] not in {"ocr_supported", "vision_only"}
            or not all(str(island[key]).strip() for key in ("location_hint", "visual_description"))
            or not isinstance(island["source_region_ids"], list)
            or len(island["source_region_ids"]) != len(set(island["source_region_ids"]))
        ):
            raise ValueError("spatial island is invalid")
        source_region_ids = [str(region_id) for region_id in island["source_region_ids"]]
        if island["observation_basis"] == "ocr_supported" and not source_region_ids:
            raise ValueError("OCR-supported spatial island requires a source region")
        if island["observation_basis"] == "vision_only" and source_region_ids:
            raise ValueError("vision-only spatial island cannot cite an OCR region")
        if any(
            region_id not in region_pages or region_pages[region_id] != page_number
            for region_id in source_region_ids
        ):
            raise ValueError("spatial island source regions are invalid")
        cited_region_ids.update(source_region_ids)
    expected_region_ids = set(region_pages)
    if cited_region_ids != expected_region_ids:
        raise ValueError("spatial islands must account for every OCR graphic region")
    return islands
