from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agents.ocr_contract import (
    OCR_PROFILE_BASIC,
    build_mistral_ocr_request,
)


DEFAULT_MISTRAL_OCR_MODEL = "mistral-ocr-4-1"
RETIRED_MISTRAL_OCR_MODELS = {"mistral-ocr-4-0"}
OCR_CONTRACT_VERSION = "ocr_v8_native_coordinate_blocks"
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

            # OCR normally returns in seconds.  A bounded timeout makes a
            # provider or network stall actionable instead of holding the
            # company extraction lock for several minutes.
            _HTTP_CLIENT = httpx.Client(timeout=45)
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


def _compact_literal_text(value: Any) -> str:
    """Remove only pathological OCR vertical gaps from derived evidence.

    Ordinary line breaks and a single blank paragraph may distinguish labels,
    dimensions, and drawing groups. Image annotations can also contain dozens
    of empty lines between tokens, which adds no readable structure. Keep the
    former intact and collapse only four or more blank lines to one blank
    paragraph. The original provider payload remains unmodified.
    """
    return re.sub(r"(?:\r?\n[ \t]*){5,}", "\n\n", str(value or "")).strip()


def _annotation_bbox_to_page_bbox(
    value: object, *, source_image_bbox: dict[str, Any],
) -> dict[str, int] | None:
    """Map Mistral's image-local 0..1000 annotation bbox to page pixels."""
    if not isinstance(value, dict):
        return None
    required = ("x1", "y1", "x2", "y2")
    if (
        set(value) != set(required)
        or not all(isinstance(value[key], int) and 0 <= value[key] <= 1000 for key in required)
    ):
        return None
    if value["x2"] <= value["x1"] or value["y2"] <= value["y1"]:
        return None
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    if not all(isinstance(source_image_bbox.get(key), (int, float)) for key in keys):
        return None
    left, top = source_image_bbox["top_left_x"], source_image_bbox["top_left_y"]
    width = source_image_bbox["bottom_right_x"] - left
    height = source_image_bbox["bottom_right_y"] - top
    if width <= 0 or height <= 0:
        return None
    return {
        "top_left_x": round(left + width * value["x1"] / 1000),
        "top_left_y": round(top + height * value["y1"] / 1000),
        "bottom_right_x": round(left + width * value["x2"] / 1000),
        "bottom_right_y": round(top + height * value["y2"] / 1000),
    }


_DECLARED_DIMENSION_PATTERNS = (
    re.compile(
        r"(?<![A-Z0-9])(?P<symbol>THK|H|W|D|L|T)\s*(?:=|:)\s*"
        r"(?P<value>\d+(?:[.,]\d+)?)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?P<symbol>[Ø⌀R])\s*(?P<value>\d+(?:[.,]\d+)?)\b",
        flags=re.IGNORECASE,
    ),
)


def _extract_declared_dimension_literals(
    *,
    page_number: int,
    source_kind: str,
    source_id: str | None,
    source_bbox: dict[str, Any],
    text: str,
) -> list[dict[str, Any]]:
    """Extract only literal symbol-value declarations from OCR text.

    This deliberately does not interpret a dimension line, infer an axis, or
    associate the fact with a commercial object.  Detection remains the only
    vision stage permitted to make those geometric decisions.
    """
    results: list[dict[str, Any]] = []
    for pattern in _DECLARED_DIMENSION_PATTERNS:
        for match in pattern.finditer(text):
            symbol = match.group("symbol").upper().replace("⌀", "Ø")
            value = match.group("value")
            results.append({
                "page_number": page_number,
                "source_kind": source_kind,
                "source_id": source_id,
                "source_bbox": source_bbox,
                "symbol": symbol,
                "value": value,
                "raw": match.group(0),
            })
    return results


def build_ocr_evidence(
    pages: list[dict[str, Any]],
    *,
    native_text_blocks: list[dict[str, Any]] | None = None,
    native_graphic_regions: list[dict[str, Any]] | None = None,
    page_profiles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a deterministic evidence index without semantic interpretation."""
    text_blocks: list[dict[str, Any]] = []
    literal_items: list[dict[str, Any]] = []
    declared_dimension_literals: list[dict[str, Any]] = []
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
                    "source": "mistral_ocr",
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
            raw_items = annotation.get("literal_items") or []
            if not raw_items and str(annotation.get("text") or "").strip():
                raw_items = [
                    {
                        "text": annotation["text"],
                        "category": "other",
                        "region": "center",
                    }
                ]
            for raw_item in raw_items:
                if not isinstance(raw_item, dict):
                    continue
                # Image annotations can contain hundreds of blank lines
                # between adjacent OCR tokens. Keep meaningful line structure
                # and the image bbox, reducing only pathological empty gaps in
                # the derived evidence index. The provider payload remains
                # unmodified in ``raw_response``.
                text = _compact_literal_text(raw_item.get("text"))
                if not text:
                    continue
                category = str(raw_item.get("category") or "other")
                region = str(raw_item.get("region") or "center")
                item_bbox = _annotation_bbox_to_page_bbox(
                    raw_item.get("bbox_1000"), source_image_bbox=image_bbox,
                )
                coordinate_basis = (
                    "mistral_annotation_bbox_1000" if item_bbox is not None
                    else "source_image_bbox_legacy"
                )
                item_bbox = item_bbox or image_bbox
                key = (
                    page_number, image_item.get("id"), text, category, region,
                    tuple(item_bbox.get(key) for key in (
                        "top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y",
                    )),
                )
                if key in item_index:
                    item_index[key]["occurrences"] += 1
                    continue
                item = {
                    "page_number": page_number,
                    "source": "mistral_ocr",
                    "source_image_id": image_item.get("id"),
                    "text": text,
                    "category": category,
                    "region": region,
                    "bbox": item_bbox,
                    "coordinate_basis": coordinate_basis,
                    "source_image_bbox": image_bbox,
                    "occurrences": 1,
                }
                item_index[key] = item
                literal_items.append(item)

    # Native PDF text is a separate literal source.  It is extracted before
    # Mistral OCR, but merged here so Detection consumes one evidence package
    # with explicit provenance for every fragment.
    for block in native_text_blocks or []:
        if not isinstance(block, dict):
            continue
        text = str(block.get("text") or "").strip()
        if not text:
            continue
        try:
            page_number = int(block.get("page_number"))
        except (TypeError, ValueError):
            continue
        if page_number < 1:
            continue
        bbox = block.get("bbox") if isinstance(block.get("bbox"), dict) else {}
        text_blocks.append(
            {
                "page_number": page_number,
                "block_type": "native_pdf_text",
                "source": "native_pdf_text",
                "text": text,
                "bbox": {
                    "top_left_x": bbox.get("top_left_x"),
                    "top_left_y": bbox.get("top_left_y"),
                    "bottom_right_x": bbox.get("bottom_right_x"),
                    "bottom_right_y": bbox.get("bottom_right_y"),
                },
            }
        )

    for block in text_blocks:
        declared_dimension_literals.extend(_extract_declared_dimension_literals(
            page_number=block["page_number"],
            source_kind="text_block",
            source_id=None,
            source_bbox=block["bbox"],
            text=str(block["text"]),
        ))
    for item in literal_items:
        declared_dimension_literals.extend(_extract_declared_dimension_literals(
            page_number=item["page_number"],
            source_kind="image_annotation",
            source_id=str(item.get("source_image_id") or "") or None,
            source_bbox=item.get("bbox") or item.get("source_image_bbox") or {},
            text=str(item["text"]),
        ))
    deduplicated_literals: list[dict[str, Any]] = []
    seen_literal_keys: set[tuple[Any, ...]] = set()
    for literal in declared_dimension_literals:
        key = (
            literal["page_number"], literal["source_kind"], literal["source_id"],
            literal["symbol"], literal["value"], literal["raw"],
        )
        if key in seen_literal_keys:
            continue
        seen_literal_keys.add(key)
        literal["literal_id"] = f"DL{len(deduplicated_literals) + 1}"
        deduplicated_literals.append(literal)

    graphic_regions: list[dict[str, Any]] = []
    for region in native_graphic_regions or []:
        if not isinstance(region, dict):
            continue
        try:
            page_number = int(region.get("page_number"))
        except (TypeError, ValueError):
            continue
        bbox = region.get("bbox") if isinstance(region.get("bbox"), dict) else {}
        try:
            left = int(bbox["top_left_x"])
            top = int(bbox["top_left_y"])
            right = int(bbox["bottom_right_x"])
            bottom = int(bbox["bottom_right_y"])
        except (KeyError, TypeError, ValueError):
            continue
        if page_number < 1 or right <= left or bottom <= top:
            continue
        graphic_id = str(region.get("graphic_id") or "").strip()
        if not graphic_id:
            continue
        graphic_regions.append({
            "graphic_id": graphic_id,
            "page_number": page_number,
            "source": "native_pdf_image_xobject",
            "bbox": {
                "top_left_x": left,
                "top_left_y": top,
                "bottom_right_x": right,
                "bottom_right_y": bottom,
            },
            "source_page_width_points": region.get("source_page_width_points"),
            "source_page_height_points": region.get("source_page_height_points"),
            "source_bbox_points": region.get("source_bbox_points"),
            "image_width": region.get("image_width"),
            "image_height": region.get("image_height"),
        })

    return {
        "text_blocks": text_blocks,
        "literal_items": literal_items,
        "declared_dimension_literals": deduplicated_literals,
        "graphic_regions": graphic_regions,
        # Passive V6.1 document inspection. These profiles are deliberately
        # distinct from source facts: Form XObjects and vector paths do not
        # become text evidence or object claims.
        "page_profiles": [
            dict(profile)
            for profile in page_profiles or []
            if isinstance(profile, dict) and isinstance(profile.get("page_number"), int)
        ],
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
    if selected_model in RETIRED_MISTRAL_OCR_MODELS:
        selected_model = DEFAULT_MISTRAL_OCR_MODEL
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
