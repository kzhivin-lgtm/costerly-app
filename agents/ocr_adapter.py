from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


DEFAULT_MISTRAL_OCR_MODEL = "mistral-ocr-4-0"
OCR_CONTRACT_VERSION = "ocr_v1"


def get_secret(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def _mime_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    mime_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    try:
        return mime_types[suffix]
    except KeyError as exc:
        raise ValueError("Unsupported OCR file type. Upload PDF, JPEG, or PNG.") from exc


def _response_to_dict(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "model_dump_json"):
        return json.loads(response.model_dump_json())
    raise RuntimeError("Mistral OCR returned an unsupported response object")


def _plain_json(value: Any) -> Any:
    """Convert SDK models nested inside OCR pages to JSON-compatible values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_json(item) for item in value]
    return value


def normalize_mistral_ocr_response(
    response: Any,
    *,
    file_name: str,
    file_bytes: bytes,
    model: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    raw = _response_to_dict(response)
    raw_pages = raw.get("pages") or []
    pages: list[dict[str, Any]] = []

    for position, raw_page in enumerate(raw_pages):
        page = _plain_json(raw_page)
        source_index = int(page.get("index", position))
        confidence_scores = page.get("confidence_scores") or {}
        pages.append(
            {
                "page_number": source_index + 1,
                "source_page_index": source_index,
                "markdown": str(page.get("markdown") or ""),
                "header": str(page.get("header") or ""),
                "footer": str(page.get("footer") or ""),
                "dimensions": _plain_json(page.get("dimensions") or {}),
                "blocks": _plain_json(page.get("blocks") or []),
                "tables": _plain_json(page.get("tables") or []),
                "images": _plain_json(page.get("images") or []),
                "hyperlinks": _plain_json(page.get("hyperlinks") or []),
                "confidence": confidence_scores.get(
                    "average_page_confidence_score"
                ),
            }
        )

    return {
        "contract_version": OCR_CONTRACT_VERSION,
        "provider": "mistral",
        "model": str(raw.get("model") or model),
        "file_name": file_name,
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "mime_type": _mime_type(file_name),
        "page_count": len(pages),
        "processing_seconds": round(elapsed_seconds, 3),
        "pages": pages,
        "usage": _plain_json(raw.get("usage_info") or {}),
    }


def _raise_ocr_error(exc: Exception) -> None:
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    if status_code == 401:
        message = "Mistral OCR rejected the API key. Check MISTRAL_API_KEY."
    elif status_code == 402:
        message = "Mistral OCR requires billing for this request or model."
    elif status_code in {403, 404}:
        message = (
            "Mistral OCR model is not available for this workspace. "
            "Check Free-plan model access or enable Scale billing."
        )
    elif status_code == 429:
        message = "Mistral OCR Free-plan rate limit reached. Try again later."
    else:
        message = f"Mistral OCR request failed: {exc}"
    raise RuntimeError(message) from exc


def run_mistral_ocr(
    *,
    file_name: str,
    file_bytes: bytes,
    model: str | None = None,
    http_client: Any | None = None,
) -> dict[str, Any]:
    """Run OCR once and return a provider-neutral page package."""
    if not file_bytes:
        raise ValueError("Mistral OCR requires uploaded file bytes.")

    selected_model = model or get_secret(
        "MISTRAL_OCR_MODEL",
        DEFAULT_MISTRAL_OCR_MODEL,
    )
    api_key = get_secret("MISTRAL_API_KEY")

    if not api_key and http_client is None:
        raise RuntimeError(
            "MISTRAL_API_KEY is missing. Add it to Streamlit secrets."
        )

    if http_client is None:
        import httpx

        http_client = httpx.Client(timeout=180)

    encoded = base64.standard_b64encode(file_bytes).decode("ascii")
    document_url = f"data:{_mime_type(file_name)};base64,{encoded}"
    started = time.perf_counter()

    try:
        response = http_client.post(
            "https://api.mistral.ai/v1/ocr",
            headers={
                "Authorization": f"Bearer {api_key or 'test-key'}",
                "Content-Type": "application/json",
            },
            json={
                "model": selected_model,
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
            },
        )
        response.raise_for_status()
        response_payload = response.json()
    except Exception as exc:
        _raise_ocr_error(exc)

    return normalize_mistral_ocr_response(
        response_payload,
        file_name=file_name,
        file_bytes=file_bytes,
        model=selected_model,
        elapsed_seconds=time.perf_counter() - started,
    )
