"""Deterministic pre-model categorization for Detection scenarios.

This classifier decides which Detection contract may inspect a document.  It
does not identify commercial objects, establish membership, or infer that two
views belong together.  Its output is deliberately auditable and always
falls back to the ordinary scenario when a special category is not evidenced.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any


DEFAULT_CLAUDE_DETECTION_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CLAUDE_DETECTION_BOUNDARY_MODEL = "claude-sonnet-4-6"

MIN_LARGE_DRAWING_SHARE = 0.08
MIN_REPEATED_MULTI_DRAWING_PAGES = 2
_SOURCE_CODE_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])(?:[A-Za-zА-Яа-яЁё]{1,5}[-/]\d{1,4}(?:[-/]\d{1,4})?|[A-Za-zА-Яа-яЁё]{1,5}\s+\d{1,4}[-/]\d{1,4})(?!\d)",
    re.IGNORECASE,
)
_DOCUMENT_IDENTIFIER_RE = re.compile(
    r"\b(?:order|project|job|заказ)\s*(?:no\.?|number|номер)?\s*[:#№-]?\s*"
    r"([A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9_/-]{1,})",
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


def _page_texts(ocr_package: dict[str, Any] | None) -> dict[int, str]:
    texts: dict[int, list[str]] = defaultdict(list)
    for index, page in enumerate((ocr_package or {}).get("pages") or [], start=1):
        if not isinstance(page, dict):
            continue
        page_number = page.get("page_number", index)
        if not isinstance(page_number, int) or page_number < 1:
            continue
        for key in ("markdown", "header", "footer"):
            value = str(page.get(key) or "").strip()
            if value:
                texts[page_number].append(value)
    evidence = (ocr_package or {}).get("evidence") or {}
    for kind in ("text_blocks", "literal_items"):
        for item in evidence.get(kind) or []:
            if not isinstance(item, dict):
                continue
            page_number = item.get("page_number")
            value = str(item.get("text") or "").strip()
            if isinstance(page_number, int) and page_number > 0 and value:
                texts[page_number].append(value)
    return {page: "\n".join(parts) for page, parts in texts.items()}


def _shared_document_identifiers(page_texts: dict[int, str]) -> dict[str, list[int]]:
    pages_by_identifier: dict[str, set[int]] = defaultdict(set)
    for page_number, text in page_texts.items():
        for match in _DOCUMENT_IDENTIFIER_RE.finditer(text):
            identifier = match.group(1).casefold()
            if len(identifier) >= 2:
                pages_by_identifier[identifier].add(page_number)
    return {
        identifier: sorted(pages)
        for identifier, pages in pages_by_identifier.items()
        if len(pages) >= 2
    }


def _strong_source_code_count(page_texts: dict[int, str]) -> int:
    codes = {
        match.group(0).strip().casefold()
        for text in page_texts.values()
        for match in _SOURCE_CODE_RE.finditer(text)
        if not match.group(0).strip().casefold().startswith(_PROVIDER_ARTIFACT_PREFIXES)
    }
    return len(codes)


def _technical_page_count(ocr_package: dict[str, Any] | None) -> int:
    profiles = ((ocr_package or {}).get("evidence") or {}).get("page_profiles") or []
    return sum(
        1
        for profile in profiles
        if isinstance(profile, dict)
        and str(profile.get("representation") or "") in {"vector", "mixed"}
    )


def _native_graphic_anchor_count(ocr_package: dict[str, Any] | None) -> int:
    evidence = (ocr_package or {}).get("evidence") or {}
    regions = evidence.get("graphic_regions") or []
    return sum(
        1
        for region in regions
        if isinstance(region, dict)
        and str(region.get("source") or "") == "native_pdf_image_xobject"
    )


def classify_detection_document(
    *,
    ocr_package: dict[str, Any] | None,
    source_capability: dict[str, Any],
    base_model: str = DEFAULT_CLAUDE_DETECTION_MODEL,
    boundary_model: str = DEFAULT_CLAUDE_DETECTION_BOUNDARY_MODEL,
    explicit_model: str | None = None,
) -> dict[str, Any]:
    """Choose an auditable Detection scenario before any Claude call.

    ``assembly_set`` is a processing category, not a claim that the complete
    document is one final commercial object.  It routes a coherent technical
    set to the ordinary Haiku Registry, where scope remains a separate
    evidence-backed observation.
    """
    pages = [
        page for page in (ocr_package or {}).get("pages") or []
        if isinstance(page, dict)
    ]
    page_texts = _page_texts(ocr_package)
    page_count = max(len(pages), int(source_capability.get("page_count") or 0))
    shared_identifiers = _shared_document_identifiers(page_texts)
    technical_page_count = _technical_page_count(ocr_package)

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
        maximum_large_drawings_on_page = max(maximum_large_drawings_on_page, large_on_page)
        if large_on_page >= 2:
            pages_with_multiple_large_drawings += 1

    signals = {
        "ocr_page_count": page_count,
        "technical_page_count": technical_page_count,
        "native_graphic_anchor_count": _native_graphic_anchor_count(ocr_package),
        "shared_document_identifiers": shared_identifiers,
        "large_drawing_count": large_drawing_count,
        "pages_with_multiple_large_drawings": pages_with_multiple_large_drawings,
        "maximum_large_drawings_on_page": maximum_large_drawings_on_page,
        "strong_source_code_count": _strong_source_code_count(page_texts),
        "source_capability": source_capability,
    }
    if explicit_model:
        return {
            "version": "detection_v6_12_document_category_v1",
            "category": "explicit_model_override",
            "decision": "explicit_model_override",
            "reasons": ["caller_supplied_model"],
            "registry_model": explicit_model,
            "evidence_model": explicit_model,
            "signals": signals,
        }
    if source_capability.get("route_eligible"):
        if signals["native_graphic_anchor_count"] >= 2:
            return {
                "version": "detection_v6_12_document_category_v1",
                "category": "page23_native_graphic_pack",
                "decision": "page23_native_graphic_pack",
                "reasons": [
                    "all_pages_lack_usable_coordinate_evidence",
                    "multiple_native_graphic_anchors",
                ],
                "registry_model": base_model,
                "evidence_model": base_model,
                "signals": signals,
            }
        return {
            "version": "detection_v6_12_document_category_v1",
            "category": "source_degraded_visual",
            "decision": "source_degraded_visual",
            "reasons": ["all_pages_lack_usable_coordinate_evidence"],
            "registry_model": base_model,
            "evidence_model": base_model,
            "signals": signals,
        }

    minimum_identifier_pages = max(3, math.ceil(page_count * 0.6))
    continuous_identifiers = {
        identifier: pages
        for identifier, pages in shared_identifiers.items()
        if len(pages) >= minimum_identifier_pages
    }
    if (
        page_count >= 3
        and technical_page_count >= 2
        and continuous_identifiers
    ):
        return {
            "version": "detection_v6_12_document_category_v1",
            "category": "assembly_set",
            "decision": "assembly_set_haiku",
            "reasons": [
                "continuous_document_identifier",
                "multiple_structured_technical_pages",
            ],
            "registry_model": base_model,
            "evidence_model": base_model,
            "signals": {**signals, "continuous_document_identifiers": continuous_identifiers},
        }

    repeated_multi_drawing_pages = (
        pages_with_multiple_large_drawings >= MIN_REPEATED_MULTI_DRAWING_PAGES
    )
    single_page_multi_drawing = len(pages) == 1 and maximum_large_drawings_on_page >= 2
    if signals["strong_source_code_count"] == 0 and (
        repeated_multi_drawing_pages or single_page_multi_drawing
    ):
        reasons = ["no_strong_source_object_code"]
        if repeated_multi_drawing_pages:
            reasons.append("repeated_multiple_large_drawing_regions")
        if single_page_multi_drawing:
            reasons.append("multiple_large_drawing_regions_on_single_page")
        return {
            "version": "detection_v6_12_document_category_v1",
            "category": "ada_sparse_multi_object",
            "decision": "ada_boundary_risk",
            "reasons": reasons,
            "registry_model": boundary_model,
            "evidence_model": base_model,
            "signals": signals,
        }
    return {
        "version": "detection_v6_12_document_category_v1",
        "category": "ordinary_object_set",
        "decision": "ordinary_haiku",
        "reasons": ["no_special_category_evidenced"],
        "registry_model": base_model,
        "evidence_model": base_model,
        "signals": signals,
    }
