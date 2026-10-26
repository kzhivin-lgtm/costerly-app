from __future__ import annotations

import base64
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_DETECTION_MODEL,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
    strip_schema_for_claude,
)


DOCUMENT_IDENTITY_VERSION = "document_identity_v1_title_block_only"
DOCUMENT_IDENTITY_PROMPT_PATH = Path(__file__).parent / "prompts" / "document_identity_prompt.md"
_FIELDS = ("project_name", "client", "design_partner", "author", "document_date")
_CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")

DOCUMENT_IDENTITY_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": list(_FIELDS),
    "properties": {
        field: {
            "type": "object",
            "additionalProperties": False,
            "required": ["value", "source_page", "source_corner", "source_label"],
            "properties": {
                "value": {"type": "string"},
                "source_page": {"type": "integer", "minimum": 0},
                "source_corner": {"type": "string"},
                "source_label": {"type": "string"},
            },
        }
        for field in _FIELDS
    },
}


def load_document_identity_prompt() -> str:
    return DOCUMENT_IDENTITY_PROMPT_PATH.read_text(encoding="utf-8").strip()


def unknown_document_identity() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "value": "unknown", "source_page": 0,
            "source_corner": "", "source_label": "",
        }
        for field in _FIELDS
    }


def _sample_page_numbers(page_count: int) -> list[int]:
    if page_count <= 0:
        return []
    selected = set(range(1, min(page_count, 3) + 1))
    selected.add(page_count)
    return sorted(selected)


def build_document_identity_title_block_crops(
    page_images: list[bytes],
    *,
    max_side: int = 1200,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return bounded corner crops for a title-block-only metadata pass.

    This intentionally samples document administration, not object Islands. It
    runs after Detection is persisted and has no authority over objects.
    """
    try:
        from PIL import Image
    except ImportError:
        return [], [{"reason": "Pillow unavailable"}]

    crops: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for page_number in _sample_page_numbers(len(page_images)):
        try:
            with Image.open(BytesIO(page_images[page_number - 1])) as image:
                width, height = image.size
                crop_width, crop_height = max(1, round(width * 0.32)), max(1, round(height * 0.36))
                for corner in _CORNERS:
                    left = 0 if "left" in corner else width - crop_width
                    top = 0 if "top" in corner else height - crop_height
                    crop = image.crop((left, top, left + crop_width, top + crop_height))
                    crop.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                    output = BytesIO()
                    crop.save(output, format="JPEG", quality=85)
                    crops.append({
                        "page_number": page_number,
                        "corner": corner,
                        "bytes": output.getvalue(),
                    })
                    audit.append({
                        "page_number": page_number,
                        "corner": corner,
                        "source_dimensions": {"width": width, "height": height},
                        "crop_dimensions": {"width": crop.width, "height": crop.height},
                    })
        except Exception as exc:
            audit.append({"page_number": page_number, "reason": type(exc).__name__})
    return crops, audit


def validate_document_identity(
    result: object,
    *,
    allowed_pages: set[int],
    allowed_corners: set[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(result, dict) or set(result) != set(_FIELDS):
        raise ValueError("Document identity result is invalid")
    normalized: dict[str, dict[str, Any]] = {}
    for field in _FIELDS:
        item = result.get(field)
        if not isinstance(item, dict) or set(item) != {
            "value", "source_page", "source_corner", "source_label",
        }:
            raise ValueError("Document identity field is invalid")
        value = " ".join(str(item.get("value") or "").split())
        source_label = " ".join(str(item.get("source_label") or "").split())
        source_corner = str(item.get("source_corner") or "")
        try:
            source_page = int(item.get("source_page"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Document identity source page is invalid") from exc
        if not value or len(value) > 160:
            raise ValueError("Document identity value is invalid")
        if value.casefold() == "unknown":
            if source_page != 0 or source_corner or source_label:
                raise ValueError("Unknown document identity cannot cite a source")
            normalized[field] = unknown_document_identity()[field]
            continue
        if source_page not in allowed_pages or source_corner not in allowed_corners or not source_label:
            raise ValueError("Document identity populated value needs visible title-block evidence")
        non_identity_labels = ("file name", "drawing name", "sheet no", "revision")
        if any(marker in source_label.casefold() for marker in non_identity_labels):
            raise ValueError("Document identity value cites a non-identity title-block label")
        normalized[field] = {
            "value": value,
            "source_page": source_page,
            "source_corner": source_corner,
            "source_label": source_label,
        }
    return normalized


def run_document_identity_call(*, page_images: list[bytes]) -> dict[str, Any]:
    """Extract document-level roles after object boundaries are locked."""
    crops, crop_audit = build_document_identity_title_block_crops(page_images)
    if not crops:
        return {
            "model": "deterministic", "duration_seconds": 0.0,
            "input_tokens": 0, "output_tokens": 0,
            "identity": unknown_document_identity(), "crop_audit": crop_audit,
        }
    model = str(
        get_secret("CLAUDE_DOCUMENT_IDENTITY_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
        or DEFAULT_CLAUDE_DETECTION_MODEL
    )
    content: list[dict[str, Any]] = [{
        "type": "text",
        "text": "Return only schema JSON for document-level identity. The supplied images are title-block candidate crops.",
    }]
    for crop in crops:
        content.extend([
            {"type": "text", "text": json.dumps({
                "title_block_crop": {"page_number": crop["page_number"], "corner": crop["corner"]},
            })},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": base64.b64encode(crop["bytes"]).decode("ascii"),
            }},
        ])
    started = time.perf_counter()
    response = create_claude_message(
        get_anthropic_client(), model=model, max_tokens=1024, temperature=0,
        system=load_document_identity_prompt(),
        messages=[{"role": "user", "content": content}],
        output_config={"format": {"type": "json_schema", "schema": strip_schema_for_claude(DOCUMENT_IDENTITY_RESULT_SCHEMA)}},
    )
    raw = json.loads(extract_text_from_claude_response(response))
    identity = validate_document_identity(
        raw,
        allowed_pages={int(crop["page_number"]) for crop in crops},
        allowed_corners={str(crop["corner"]) for crop in crops},
    )
    usage = getattr(response, "usage", None)
    return {
        "model": model,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "identity": identity,
        "crop_audit": crop_audit,
    }
