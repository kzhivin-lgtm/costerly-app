from __future__ import annotations

from typing import Any


OCR_PROFILE_BASIC = "basic"
OCR_PROFILE_EVIDENCE = "evidence"
OCR_PROFILES = {
    OCR_PROFILE_BASIC,
    OCR_PROFILE_EVIDENCE,
}

OCR_EVIDENCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "text": {
            "type": "string",
            "description": (
                "Transcribe all legible text inside this image exactly as printed. "
                "Preserve language, spelling, numbers, units, and line breaks. "
                "Include dimensions, labels, notes, material and finish callouts. "
                "Never infer missing text, summarize content, identify products, "
                "count products, or group drawing views."
            ),
        }
    },
    "required": ["text"],
}


def build_mistral_ocr_request(
    *,
    model: str,
    document_url: str,
    profile: str = OCR_PROFILE_BASIC,
) -> dict[str, Any]:
    """Build one versioned Mistral OCR request without performing I/O."""
    if profile not in OCR_PROFILES:
        raise ValueError(f"Unknown OCR profile: {profile}")

    is_image = document_url.startswith("data:image/")
    document = (
        {"type": "image_url", "image_url": document_url}
        if is_image
        else {"type": "document_url", "document_url": document_url}
    )
    payload: dict[str, Any] = {
        "model": model,
        "document": document,
        "table_format": "html",
        "extract_header": True,
        "extract_footer": True,
        "include_blocks": True,
        "include_image_base64": False,
        "confidence_scores_granularity": "page",
    }
    if profile == OCR_PROFILE_EVIDENCE:
        payload["bbox_annotation_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": profile,
                "strict": True,
                "schema": OCR_EVIDENCE_SCHEMA,
            },
        }
    return payload
