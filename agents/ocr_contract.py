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
        "literal_items": {
            "type": "array",
            "description": (
                "Transcribe every legible text occurrence in the image exactly as "
                "printed. Include dimensions, labels, notes, material and finish "
                "callouts. Never infer missing text, summarize content, identify "
                "products, count products, name products, or group drawing views."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Exact visible text preserving language, spelling, numbers, and units.",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["dimension", "material", "finish", "hardware", "note", "title", "other"],
                    },
                    "region": {
                        "type": "string",
                        "enum": [
                            "top-left",
                            "top-center",
                            "top-right",
                            "center-left",
                            "center",
                            "center-right",
                            "bottom-left",
                            "bottom-center",
                            "bottom-right",
                        ],
                        "description": "Approximate location of this exact text occurrence inside the image.",
                    },
                },
                "required": ["text", "category", "region"],
            },
        }
    },
    "required": ["literal_items"],
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

    payload: dict[str, Any] = {
        "model": model,
        "document": {
            "type": "document_url",
            "document_url": document_url,
        },
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
