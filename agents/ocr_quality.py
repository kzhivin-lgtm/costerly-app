from __future__ import annotations

import json
from typing import Any


def _annotation_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def image_annotations(ocr_package: dict[str, Any]) -> list[dict[str, Any]]:
    """Return parsed bbox annotations from every OCR page image."""
    annotations: list[dict[str, Any]] = []
    for page in ocr_package.get("pages") or []:
        for image in page.get("images") or []:
            annotation = _annotation_dict(image.get("image_annotation"))
            if annotation:
                annotations.append(
                    {
                        "page_number": page.get("page_number"),
                        "image_id": image.get("id"),
                        "annotation": annotation,
                    }
                )
    return annotations


def evaluate_ocr_result(ocr_package: dict[str, Any]) -> dict[str, Any]:
    """Measure whether OCR produced text evidence or mostly image placeholders."""
    markdown_text_chars = 0
    non_image_block_chars = 0
    image_blocks = 0
    page_count = int(ocr_package.get("page_count") or 0)

    for page in ocr_package.get("pages") or []:
        markdown = str(page.get("markdown") or "")
        markdown_without_images = "\n".join(
            line for line in markdown.splitlines() if not line.strip().startswith("![")
        ).strip()
        markdown_text_chars += len(markdown_without_images)
        for block in page.get("blocks") or []:
            if block.get("type") == "image":
                image_blocks += 1
            else:
                non_image_block_chars += len(str(block.get("content") or "").strip())

    annotations = image_annotations(ocr_package)
    annotation_chars = sum(
        len(json.dumps(item["annotation"], ensure_ascii=False))
        for item in annotations
    )
    needs_annotations = bool(
        image_blocks
        and markdown_text_chars < 80 * max(1, page_count)
        and not annotations
    )
    return {
        "page_count": page_count,
        "markdown_text_chars": markdown_text_chars,
        "non_image_block_chars": non_image_block_chars,
        "image_blocks": image_blocks,
        "annotation_count": len(annotations),
        "annotation_chars": annotation_chars,
        "needs_annotations": needs_annotations,
        "processing_seconds": float(ocr_package.get("processing_seconds") or 0),
    }


def score_expected_evidence(
    ocr_package: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Score literal expected evidence against the complete OCR JSON."""
    evidence_parts: list[str] = []
    for page in ocr_package.get("pages") or []:
        evidence_parts.extend(
            [
                str(page.get("header") or ""),
                str(page.get("footer") or ""),
                str(page.get("markdown") or ""),
            ]
        )
        for block in page.get("blocks") or []:
            if block.get("type") != "image":
                evidence_parts.append(str(block.get("content") or ""))
        for table in page.get("tables") or []:
            evidence_parts.append(json.dumps(table, ensure_ascii=False))
    for item in image_annotations(ocr_package):
        evidence_parts.append(json.dumps(item["annotation"], ensure_ascii=False))
    haystack = "\n".join(evidence_parts).casefold()
    checks: list[dict[str, Any]] = []
    for category, values in expected.items():
        if not isinstance(values, list):
            continue
        for value in values:
            literal = str(value)
            checks.append(
                {
                    "category": category,
                    "expected": literal,
                    "found": literal.casefold() in haystack,
                }
            )
    found = sum(1 for check in checks if check["found"])
    return {
        "found": found,
        "total": len(checks),
        "recall": round(found / len(checks), 3) if checks else None,
        "checks": checks,
    }
