from __future__ import annotations

OCR_PROFILE_BASIC = "basic"
OCR_PROFILE_EVIDENCE = "evidence"
OCR_PROFILES = {
    OCR_PROFILE_BASIC,
    OCR_PROFILE_EVIDENCE,
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
        # Native OCR blocks contain both content and page-pixel bbox.  They are
        # the coordinate contract consumed by Fusion.  A custom per-item bbox
        # annotation caused P04/P08 provider timeouts on HSL and is excluded.
        "confidence_scores_granularity": "block",
    }
    return payload
