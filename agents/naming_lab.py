from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_DETECTION_MODEL,
    build_uploaded_file_content_block,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
    strip_schema_for_claude,
)


NAMING_LAB_VERSION = "naming_lab_v1"
NAMING_PROMPT_PATH = Path(__file__).parent / "prompts" / "naming_agent_prompt.md"

NAMING_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["names"],
    "properties": {
        "names": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["object_id", "name_en", "name_original"],
                "properties": {
                    "object_id": {"type": "string"},
                    "name_en": {"type": "string"},
                    "name_original": {"type": "string"},
                },
            },
        }
    },
}


def load_naming_prompt() -> str:
    return NAMING_PROMPT_PATH.read_text(encoding="utf-8").strip()


def extract_object_index(object_name: Any) -> str:
    name = str(object_name or "").strip()
    if " — " in name:
        candidate = name.split(" — ", 1)[0].strip()
        if any(character.isdigit() for character in candidate):
            return candidate
    match = re.match(r"^([^\s—:]+\d[^\s—:]*)\s*(?:[—:])?", name)
    return match.group(1).strip() if match else ""


def _page_numbers(value: Any) -> set[int]:
    return {
        int(item)
        for item in re.findall(r"\d+", str(value or ""))
        if int(item) > 0
    }


def _ocr_items(ocr_result: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = ocr_result.get("evidence")
    if not isinstance(evidence, dict):
        return []
    items: list[dict[str, Any]] = []
    for key in ("text_blocks", "literal_items"):
        for item in evidence.get(key) or []:
            if isinstance(item, dict) and str(item.get("text") or "").strip():
                items.append(item)
    return items


def relevant_ocr_snippets(
    detected_object: dict[str, Any],
    ocr_result: dict[str, Any],
    *,
    max_items: int = 12,
    max_chars: int = 2400,
) -> list[str]:
    object_index = extract_object_index(detected_object.get("object_name"))
    pages = _page_numbers(detected_object.get("evidence_pages"))
    exact: list[str] = []
    page_fallback: list[str] = []

    for item in _ocr_items(ocr_result):
        text = " ".join(str(item.get("text") or "").split())
        page = item.get("page_number")
        if object_index and object_index.casefold() in text.casefold():
            exact.append(text)
        elif not object_index and page in pages:
            page_fallback.append(text)

    selected = exact or page_fallback
    unique: list[str] = []
    seen: set[str] = set()
    char_count = 0
    for text in selected:
        key = text.casefold()
        if key in seen:
            continue
        if char_count + len(text) > max_chars:
            break
        seen.add(key)
        unique.append(text)
        char_count += len(text)
        if len(unique) >= max_items:
            break
    return unique


def build_locked_naming_input(
    detected_objects: list[dict[str, Any]],
    ocr_result: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "object_id": str(item.get("object_id") or ""),
            "object_index": extract_object_index(item.get("object_name")),
            "current_name": str(item.get("object_name") or ""),
            "evidence_pages": str(item.get("evidence_pages") or ""),
            "materials": str(item.get("detected_materials") or ""),
            "dimensions": dict(item.get("dimensions_json") or {}),
            "notes": str(item.get("notes") or ""),
            "ocr_snippets": relevant_ocr_snippets(item, ocr_result),
        }
        for item in detected_objects
    ]


def ensure_unique_object_ids(detected_objects: list[dict[str, Any]]) -> None:
    """Assign position-locked transport IDs without changing objects or labels."""
    for position, item in enumerate(detected_objects, start=1):
        item["object_id"] = f"object-{position:03d}"


def _word_count(value: Any) -> int:
    return len(re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*", str(value or ""), re.UNICODE))


def validate_locked_name_mapping(
    locked_objects: list[dict[str, Any]],
    result: dict[str, Any],
) -> dict[str, Any]:
    expected_ids = [str(item.get("object_id") or "") for item in locked_objects]
    names = result.get("names")
    if not isinstance(names, list):
        raise ValueError("Naming result must contain a names array")
    actual_ids = [str(item.get("object_id") or "") for item in names if isinstance(item, dict)]
    if len(actual_ids) != len(names) or actual_ids != expected_ids:
        raise ValueError(
            f"Naming object_id sequence changed: expected {expected_ids}, got {actual_ids}"
        )

    violations: list[dict[str, Any]] = []
    for item in names:
        name_en_words = _word_count(item.get("name_en"))
        original_words = _word_count(item.get("name_original"))
        if name_en_words < 2 or name_en_words > 3:
            violations.append(
                {"object_id": item["object_id"], "field": "name_en", "words": name_en_words}
            )
        if original_words > 4:
            violations.append(
                {
                    "object_id": item["object_id"],
                    "field": "name_original",
                    "words": original_words,
                }
            )
    return {"accepted": not violations, "violations": violations}


def compose_name_preview(
    locked_objects: list[dict[str, Any]],
    result: dict[str, Any],
) -> list[dict[str, str]]:
    locked_by_id = {str(item.get("object_id") or ""): item for item in locked_objects}
    previews: list[dict[str, str]] = []
    for item in result["names"]:
        object_id = str(item["object_id"])
        object_index = str(locked_by_id[object_id].get("object_index") or "").strip()
        name_en = str(item.get("name_en") or "").strip()
        original = str(item.get("name_original") or "").strip()
        base = " — ".join(part for part in (object_index, name_en) if part)
        display_name = f'{base} ("{original}")' if original else base
        previews.append({"object_id": object_id, "display_name": display_name})
    return previews


def apply_name_mapping(
    detected_objects: list[dict[str, Any]],
    locked_objects: list[dict[str, Any]],
    result: dict[str, Any],
) -> None:
    """Apply validated display names without changing the locked object set."""
    validation = validate_locked_name_mapping(locked_objects, result)
    if not validation["accepted"]:
        raise ValueError(f"Naming word-limit violations: {validation['violations']}")
    previews = compose_name_preview(locked_objects, result)
    names_by_id = {item["object_id"]: item["display_name"] for item in previews}
    for detected_object in detected_objects:
        object_id = str(detected_object.get("object_id") or "")
        detected_object["object_name"] = names_by_id[object_id]


def run_naming_lab_call(
    locked_objects: list[dict[str, Any]],
    *,
    file_name: str | None = None,
    file_bytes: bytes | None = None,
) -> dict[str, Any]:
    model = str(
        get_secret("CLAUDE_NAMING_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
        or DEFAULT_CLAUDE_DETECTION_MODEL
    )
    client = get_anthropic_client()
    started = time.perf_counter()
    content: list[dict[str, Any]] = []
    if file_name and file_bytes:
        content.append(
            build_uploaded_file_content_block(
                file_name,
                file_bytes,
                cache_enabled=False,
            )
        )
    content.append(
        {
            "type": "text",
            "text": (
                "Name only these already locked objects. Use the attached document only "
                "to understand their product category and source-language label. Return "
                "only schema JSON:\n"
                + json.dumps(locked_objects, ensure_ascii=False, separators=(",", ":"))
            ),
        }
    )
    response = create_claude_message(
        client,
        model=model,
        max_tokens=2048,
        temperature=0,
        system=load_naming_prompt(),
        messages=[{"role": "user", "content": content}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": strip_schema_for_claude(NAMING_RESULT_SCHEMA),
            }
        },
    )
    duration_seconds = round(time.perf_counter() - started, 3)
    result = json.loads(extract_text_from_claude_response(response))
    validation = validate_locked_name_mapping(locked_objects, result)
    usage = getattr(response, "usage", None)
    return {
        "lab_version": NAMING_LAB_VERSION,
        "model": model,
        "duration_seconds": duration_seconds,
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "validation": validation,
        "names": result["names"],
        "preview": compose_name_preview(locked_objects, result),
    }
