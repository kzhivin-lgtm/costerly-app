from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.ocr_contract import (
    OCR_PROFILE_BASIC,
    build_mistral_ocr_request,
)


DEFAULT_MISTRAL_OCR_MODEL = "mistral-ocr-4-0"
OCR_CONTRACT_VERSION = "ocr_v2"
_HTTP_CLIENT: Any | None = None
_HTTP_CLIENT_LOCK = threading.Lock()
_WARMUP_LOCK = threading.Lock()
_WARMUP_EVENT = threading.Event()
_WARMUP_STARTED = False


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


def get_mistral_http_client() -> Any:
    """Return one process-wide connection pool for all OCR requests."""
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT
    with _HTTP_CLIENT_LOCK:
        if _HTTP_CLIENT is None:
            import httpx

            _HTTP_CLIENT = httpx.Client(timeout=180)
    return _HTTP_CLIENT


def warm_mistral_http_client_async() -> None:
    """Warm DNS/TLS/HTTP keep-alive without blocking the upload screen."""
    global _WARMUP_STARTED
    api_key = get_secret("MISTRAL_API_KEY")
    if not api_key:
        _WARMUP_EVENT.set()
        return
    with _WARMUP_LOCK:
        if _WARMUP_STARTED:
            return
        _WARMUP_STARTED = True

    def warm() -> None:
        try:
            get_mistral_http_client().get(
                "https://api.mistral.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
        except Exception:
            # OCR itself remains the authoritative request and error surface.
            pass
        finally:
            _WARMUP_EVENT.set()

    threading.Thread(target=warm, name="mistral-http-warmup", daemon=True).start()


def wait_for_mistral_http_warmup(timeout: float = 10.0) -> None:
    _WARMUP_EVENT.wait(timeout=max(0.0, timeout))


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


def build_ocr_evidence(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a deterministic evidence index without semantic interpretation."""
    text_blocks: list[dict[str, Any]] = []
    literal_items: list[dict[str, Any]] = []
    item_index: dict[tuple[Any, ...], dict[str, Any]] = {}

    for page in pages:
        page_number = page["page_number"]
        for block in page.get("blocks") or []:
            content = str(block.get("content") or "").strip()
            if block.get("type") == "image" or not content:
                continue
            text_blocks.append(
                {
                    "page_number": page_number,
                    "block_type": block.get("type"),
                    "text": content,
                    "bbox": {
                        "top_left_x": block.get("top_left_x"),
                        "top_left_y": block.get("top_left_y"),
                        "bottom_right_x": block.get("bottom_right_x"),
                        "bottom_right_y": block.get("bottom_right_y"),
                    },
                }
            )

        for image_item in page.get("images") or []:
            annotation = _annotation_dict(image_item.get("image_annotation"))
            if not annotation:
                continue
            image_bbox = {
                "top_left_x": image_item.get("top_left_x"),
                "top_left_y": image_item.get("top_left_y"),
                "bottom_right_x": image_item.get("bottom_right_x"),
                "bottom_right_y": image_item.get("bottom_right_y"),
            }
            for raw_item in annotation.get("literal_items") or []:
                if not isinstance(raw_item, dict):
                    continue
                text = str(raw_item.get("text") or "").strip()
                if not text:
                    continue
                category = str(raw_item.get("category") or "other")
                region = str(raw_item.get("region") or "center")
                key = (page_number, image_item.get("id"), text, category, region)
                if key in item_index:
                    item_index[key]["occurrences"] += 1
                    continue
                item = {
                    "page_number": page_number,
                    "source_image_id": image_item.get("id"),
                    "text": text,
                    "category": category,
                    "region": region,
                    "source_image_bbox": image_bbox,
                    "occurrences": 1,
                }
                item_index[key] = item
                literal_items.append(item)

    return {
        "text_blocks": text_blocks,
        "literal_items": literal_items,
    }


def normalize_mistral_ocr_response(
    response: Any,
    *,
    file_name: str,
    file_bytes: bytes,
    model: str,
    elapsed_seconds: float,
    profile: str = OCR_PROFILE_BASIC,
    started_at: str | None = None,
    finished_at: str | None = None,
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

    result = {
        "contract_version": OCR_CONTRACT_VERSION,
        "provider": "mistral",
        "model": str(raw.get("model") or model),
        "profile": profile,
        "file_name": file_name,
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "mime_type": _mime_type(file_name),
        "page_count": len(pages),
        "processing_seconds": round(elapsed_seconds, 3),
        "started_at": started_at,
        "finished_at": finished_at,
        "pages": pages,
        "usage": _plain_json(raw.get("usage_info") or {}),
        # Preserve the exact provider payload for auditing and downstream agents.
        # Image base64 is disabled in the request, so this does not duplicate the
        # uploaded source file inside Supabase.
        "raw_response": _plain_json(raw),
    }
    result["evidence"] = build_ocr_evidence(pages)
    return result


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
    profile: str = OCR_PROFILE_BASIC,
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
        http_client = get_mistral_http_client()

    encoded = base64.standard_b64encode(file_bytes).decode("ascii")
    document_url = f"data:{_mime_type(file_name)};base64,{encoded}"
    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()

    try:
        response = http_client.post(
            "https://api.mistral.ai/v1/ocr",
            headers={
                "Authorization": f"Bearer {api_key or 'test-key'}",
                "Content-Type": "application/json",
            },
            json=build_mistral_ocr_request(
                model=selected_model,
                document_url=document_url,
                profile=profile,
            ),
        )
        response.raise_for_status()
        response_payload = response.json()
    except Exception as exc:
        _raise_ocr_error(exc)

    finished_at = datetime.now(UTC).isoformat()
    return normalize_mistral_ocr_response(
        response_payload,
        file_name=file_name,
        file_bytes=file_bytes,
        model=selected_model,
        elapsed_seconds=time.perf_counter() - started,
        profile=profile,
        started_at=started_at,
        finished_at=finished_at,
    )
