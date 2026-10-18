"""Deterministic V4.2 model routing for Detection object boundaries.

The router never proposes, splits, merges or counts commercial objects.  It
only selects the model that will make the existing Registry decision from
literal OCR layout signals.  This keeps the expensive model as an exception,
not a second source of object-boundary logic.
"""

from __future__ import annotations

import re
from typing import Any


DEFAULT_CLAUDE_DETECTION_V4_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CLAUDE_DETECTION_V4_BOUNDARY_MODEL = "claude-sonnet-4-6"

# An OCR drawing/image must occupy a material part of the physical page before
# it can contribute to the risk signal.  This deliberately ignores title
# blocks, logos and small embedded details.
MIN_LARGE_DRAWING_SHARE = 0.08
MIN_REPEATED_MULTI_DRAWING_PAGES = 2

# An author-issued index must contain a hyphen or slash.  This admits forms
# such as ``OM-2``, ``K-110`` and ``OM 15-1``, but rejects visual notes such as
# ``LED 3000`` and document metadata such as ``Sheet 1``. Provider image/table
# IDs are filtered below.
_SOURCE_CODE_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])(?:[A-Za-zА-Яа-яЁё]{1,5}[-/]\d{1,4}(?:[-/]\d{1,4})?|[A-Za-zА-Яа-яЁё]{1,5}\s+\d{1,4}[-/]\d{1,4})(?!\d)",
    re.IGNORECASE,
)
_PROVIDER_ARTIFACT_PREFIXES = ("img-", "tbl-", "image-", "table-")


def _number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _bbox_area(item: dict[str, Any]) -> float | None:
    left = _number(item.get("top_left_x"))
    top = _number(item.get("top_left_y"))
    right = _number(item.get("bottom_right_x"))
    bottom = _number(item.get("bottom_right_y"))
    if None in (left, top, right, bottom) or right <= left or bottom <= top:
        return None
    return (right - left) * (bottom - top)


def _page_area(page: dict[str, Any]) -> float | None:
    dimensions = page.get("dimensions")
    if not isinstance(dimensions, dict):
        return None
    width = _number(dimensions.get("width"))
    height = _number(dimensions.get("height"))
    if width is None or height is None or width == 0 or height == 0:
        return None
    return width * height


def _drawing_regions(page: dict[str, Any]) -> list[dict[str, Any]]:
    """Return raw OCR image regions, with block fallback for older OCR data."""
    images = page.get("images")
    if isinstance(images, list) and images:
        return [item for item in images if isinstance(item, dict)]
    blocks = page.get("blocks")
    if not isinstance(blocks, list):
        return []
    return [
        item for item in blocks
        if isinstance(item, dict) and str(item.get("type") or "").casefold() == "image"
    ]


def _source_text(ocr_package: dict[str, Any] | None) -> str:
    fragments: list[str] = []
    for page in (ocr_package or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        for key in ("markdown", "header", "footer"):
            fragments.append(str(page.get(key) or ""))
        for block in page.get("blocks") or []:
            if isinstance(block, dict):
                fragments.append(str(block.get("content") or ""))
        for image in page.get("images") or []:
            if isinstance(image, dict):
                fragments.append(str(image.get("image_annotation") or ""))
    return "\n".join(fragments)


def _strong_source_code_count(ocr_package: dict[str, Any] | None) -> int:
    codes = {
        match.group(0).strip().casefold()
        for match in _SOURCE_CODE_RE.finditer(_source_text(ocr_package))
        if not match.group(0).strip().casefold().startswith(_PROVIDER_ARTIFACT_PREFIXES)
    }
    return len(codes)


def detection_v42_model_route(
    *,
    ocr_package: dict[str, Any] | None,
    base_model: str = DEFAULT_CLAUDE_DETECTION_V4_MODEL,
    boundary_model: str = DEFAULT_CLAUDE_DETECTION_V4_BOUNDARY_MODEL,
    explicit_model: str | None = None,
) -> dict[str, Any]:
    """Select a Registry and Evidence model without interpreting a drawing.

    Sonnet is selected only when raw OCR shows an unlabelled document with
    repeated pages containing multiple independently large drawing regions.
    That is the observable Ada-style ambiguity: several visual assemblies but
    no author-issued object code that helps Haiku establish the boundary.
    """
    if explicit_model:
        return {
            "version": "detection_v4_2_risk_router",
            "decision": "explicit_model_override",
            "reasons": ["caller_supplied_model"],
            "registry_model": explicit_model,
            "evidence_model": explicit_model,
            "signals": {},
        }

    pages = [
        page for page in (ocr_package or {}).get("pages") or []
        if isinstance(page, dict)
    ]
    large_drawing_count = 0
    pages_with_multiple_large_drawings = 0
    maximum_large_drawings_on_page = 0
    for page in pages:
        page_area = _page_area(page)
        if page_area is None:
            continue
        large_on_page = sum(
            1
            for region in _drawing_regions(page)
            if (area := _bbox_area(region)) is not None
            and area / page_area >= MIN_LARGE_DRAWING_SHARE
        )
        large_drawing_count += large_on_page
        maximum_large_drawings_on_page = max(
            maximum_large_drawings_on_page, large_on_page
        )
        if large_on_page >= 2:
            pages_with_multiple_large_drawings += 1

    strong_source_code_count = _strong_source_code_count(ocr_package)
    signals = {
        "ocr_page_count": len(pages),
        "large_drawing_count": large_drawing_count,
        "pages_with_multiple_large_drawings": pages_with_multiple_large_drawings,
        "maximum_large_drawings_on_page": maximum_large_drawings_on_page,
        "strong_source_code_count": strong_source_code_count,
    }
    repeated_multi_drawing_pages = (
        pages_with_multiple_large_drawings >= MIN_REPEATED_MULTI_DRAWING_PAGES
    )
    single_page_multi_drawing = (
        len(pages) == 1 and maximum_large_drawings_on_page >= 2
    )
    if strong_source_code_count == 0 and (
        repeated_multi_drawing_pages or single_page_multi_drawing
    ):
        reasons = ["no_strong_source_object_code"]
        if repeated_multi_drawing_pages:
            reasons.append("repeated_multiple_large_drawing_regions")
        if single_page_multi_drawing:
            reasons.append("multiple_large_drawing_regions_on_single_page")
        return {
            "version": "detection_v4_2_risk_router",
            "decision": "sonnet_boundary_risk",
            "reasons": reasons,
            "registry_model": boundary_model,
            # The second call only prepares Evidence for objects locked by the
            # Registry.  It stays on the efficient base model.
            "evidence_model": base_model,
            "signals": signals,
        }

    return {
        "version": "detection_v4_2_risk_router",
        "decision": "haiku_default",
        "reasons": ["risk_threshold_not_met"],
        "registry_model": base_model,
        "evidence_model": base_model,
        "signals": signals,
    }
