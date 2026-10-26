from __future__ import annotations

import json
import base64
import re
import time
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


NAMING_LAB_VERSION = "naming_lab_v11_decision_audit"
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
                "required": ["object_id", "name_en", "name_original", "name_basis"],
                "properties": {
                    "object_id": {"type": "string"},
                    "name_en": {"type": "string"},
                    "name_original": {"type": "string"},
                    "name_basis": {"type": "string"},
                },
            },
        }
    },
}


def load_naming_prompt() -> str:
    return NAMING_PROMPT_PATH.read_text(encoding="utf-8").strip()


def extract_object_index(object_name: Any) -> str:
    name = str(object_name or "").strip()
    # Transport labels identify a Registry position, never a source-authored
    # object code. Reject the complete placeholder before looking for a code
    # within a longer provisional display name as well.
    if re.fullmatch(r"(?:object|item|unknown)\s*\d+(?:\s*[—-]\s*.*)?", name, re.IGNORECASE):
        return ""
    if " — " in name:
        candidate = name.split(" — ", 1)[0].strip()
        if _is_source_identifier(candidate):
            return candidate
    if _is_source_identifier(name):
        return name
    # Registry transport is source-derived, but a model can occasionally add
    # a descriptive word around one literal code, for example "Kitchen N56".
    # Retain that one unambiguous code rather than dropping it in Naming. Do
    # not guess when a label contains multiple possible identifiers.
    candidates = {match.group(0).strip() for match in _SOURCE_IDENTIFIER_RE.finditer(name)}
    return next(iter(candidates)) if len(candidates) == 1 else ""


_SOURCE_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё0-9])(?:[A-Za-zА-Яа-яЁё]{1,4}\s*[- ]?\s*\d+(?:[-./][A-Za-zА-Яа-яЁё0-9]+){0,3}|\d{1,3}[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*(?:[-./][A-Za-zА-Яа-яЁё0-9]+){0,3})(?![A-Za-zА-Яа-яЁё0-9])"
)


def _is_source_identifier(value: Any) -> bool:
    candidate = str(value or "").strip()
    if re.fullmatch(r"(?:object|item|unknown)\s*\d+", candidate.casefold()):
        return False
    return bool(_SOURCE_IDENTIFIER_RE.fullmatch(candidate))


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


def _bbox_contains_centre(region: dict[str, Any], bbox: object) -> bool:
    """Keep OCR local when Detection has a locked object View bbox."""
    if not isinstance(bbox, dict):
        return False
    keys = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
    try:
        left, top, right, bottom = (float(bbox[key]) for key in keys)
        region_left, region_top, region_right, region_bottom = (
            float(region[key]) for key in keys
        )
    except (KeyError, TypeError, ValueError):
        return False
    if right <= left or bottom <= top or region_right <= region_left or region_bottom <= region_top:
        return False
    centre_x, centre_y = (left + right) / 2, (top + bottom) / 2
    return region_left <= centre_x <= region_right and region_top <= centre_y <= region_bottom


def _object_regions_by_page(detected_object: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    regions_by_page: dict[int, list[dict[str, Any]]] = {}
    for ref in detected_object.get("evidence_page_refs") or []:
        if not isinstance(ref, dict):
            continue
        try:
            page_number = int(ref.get("page_number"))
        except (TypeError, ValueError):
            continue
        regions = [region for region in ref.get("regions") or [] if isinstance(region, dict)]
        if page_number > 0 and regions:
            regions_by_page[page_number] = regions
    return regions_by_page


def relevant_ocr_snippets(
    detected_object: dict[str, Any],
    ocr_result: dict[str, Any],
    *,
    max_items: int = 6,
    max_chars: int = 1000,
) -> list[str]:
    object_index = extract_object_index(detected_object.get("object_name"))
    pages = _page_numbers(detected_object.get("evidence_pages"))
    regions_by_page = _object_regions_by_page(detected_object)
    exact: list[str] = []
    local: list[str] = []
    page_fallback: list[str] = []

    for item in _ocr_items(ocr_result):
        text = " ".join(str(item.get("text") or "").split())
        try:
            page = int(item.get("page_number"))
        except (TypeError, ValueError):
            continue
        item_bbox = item.get("bbox") or item.get("source_image_bbox")
        is_local = any(
            _bbox_contains_centre(region, item_bbox)
            for region in regions_by_page.get(page, [])
        )
        if regions_by_page and not is_local:
            continue
        if object_index and object_index.casefold() in text.casefold():
            exact.append(text)
        elif regions_by_page and is_local:
            local.append(text)
        elif not object_index and page in pages:
            page_fallback.append(text)

    selected = exact or local or page_fallback
    unique: list[str] = []
    seen: set[str] = set()
    char_count = 0
    for text in selected:
        key = text.casefold()
        if key in seen:
            continue
        remaining = max_chars - char_count
        if remaining <= 0:
            break
        text = text[:remaining].rstrip()
        if not text:
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
    locked: list[dict[str, Any]] = []
    for item in detected_objects:
        evidence_regions = []
        for ref in item.get("evidence_page_refs") or []:
            if not isinstance(ref, dict) or not str(ref.get("page_number") or "").isdigit():
                continue
            evidence_regions.append({
                "page_number": int(ref["page_number"]),
                "regions": [dict(region) for region in ref.get("regions") or [] if isinstance(region, dict)],
            })
        locked.append({
            "object_id": str(item.get("object_id") or ""),
            "object_index": extract_object_index(item.get("object_name")),
            "current_name": str(item.get("object_name") or ""),
            "evidence_pages": [ref["page_number"] for ref in evidence_regions],
            # These are retrieval pointers for the supplied full pages.  They
            # make the multimodal naming pass object-specific without passing
            # the UI-only presentation crop.
            "evidence_regions": evidence_regions,
            "ocr_snippets": relevant_ocr_snippets(item, ocr_result),
        })
    return locked


def ensure_unique_object_ids(detected_objects: list[dict[str, Any]]) -> None:
    """Assign position-locked transport IDs without changing objects or labels."""
    for position, item in enumerate(detected_objects, start=1):
        item["object_id"] = f"object-{position:03d}"


def _word_count(value: Any) -> int:
    return len(re.findall(r"[^\W_]+(?:[-’'][^\W_]+)*", str(value or ""), re.UNICODE))


def _is_transport_placeholder(value: Any) -> bool:
    normalized = " ".join(str(value or "").casefold().split())
    return bool(re.fullmatch(r"(?:object|item|unknown)(?: \d+)?", normalized))


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
        if name_en_words < 1 or name_en_words > 3:
            violations.append(
                {"object_id": item["object_id"], "field": "name_en", "words": name_en_words}
            )
        elif _is_transport_placeholder(item.get("name_en")):
            violations.append(
                {"object_id": item["object_id"], "field": "name_en", "reason": "transport_placeholder"}
            )
        if original_words > 4:
            violations.append(
                {
                    "object_id": item["object_id"],
                    "field": "name_original",
                    "words": original_words,
                }
            )
        elif original_words:
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
        base = " ".join(part for part in (object_index, name_en) if part)
        previews.append({"object_id": object_id, "display_name": base})
    return previews


def build_naming_decision_audit(
    locked_objects: list[dict[str, Any]],
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return short, inspectable Naming grounds beside the final names.

    The source code and evidence pages come from the locked Detection input,
    while the model supplies only a concise category-selection basis.  It is
    audit data, never input to object-boundary or Estimation decisions.
    """
    locked_by_id = {
        str(item.get("object_id") or ""): item
        for item in locked_objects
        if isinstance(item, dict)
    }
    decisions: list[dict[str, Any]] = []
    for item in result.get("names") or []:
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("object_id") or "")
        locked = locked_by_id.get(object_id, {})
        decisions.append({
            "object_id": object_id,
            "source_identifier": str(locked.get("object_index") or ""),
            "evidence_pages": list(locked.get("evidence_pages") or []),
            "selected_name": str(item.get("name_en") or ""),
            "name_basis": str(item.get("name_basis") or ""),
        })
    return decisions


def apply_name_mapping(
    detected_objects: list[dict[str, Any]],
    locked_objects: list[dict[str, Any]],
    result: dict[str, Any],
) -> None:
    """Apply valid names and preserve placeholders for isolated invalid rows."""
    validation = validate_locked_name_mapping(locked_objects, result)
    invalid_ids = {
        str(item.get("object_id") or "")
        for item in validation["violations"]
    }
    previews = compose_name_preview(locked_objects, result)
    names_by_id = {item["object_id"]: item["display_name"] for item in previews}
    current_names = {
        str(item.get("object_id") or ""): str(item.get("current_name") or "")
        for item in locked_objects
    }
    for detected_object in detected_objects:
        object_id = str(detected_object.get("object_id") or "")
        detected_object["object_name"] = (
            current_names[object_id]
            if object_id in invalid_ids
            else names_by_id[object_id]
        )


def run_naming_lab_call(
    locked_objects: list[dict[str, Any]],
    visual_pages_by_number: dict[int, bytes] | None = None,
    object_crops_by_id: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    model = str(
        get_secret("CLAUDE_NAMING_MODEL", DEFAULT_CLAUDE_DETECTION_MODEL)
        or DEFAULT_CLAUDE_DETECTION_MODEL
    )
    client = get_anthropic_client()
    started = time.perf_counter()
    content = [
        {
            "type": "text",
            "text": (
                "Name only these already locked objects. Treat an object index or a model/name "
                "as incomplete until you identify its product category from the Detection context "
                "and local OCR. Source pages are labelled by physical page number. "
                "Return only schema JSON:\n"
                + json.dumps(locked_objects, ensure_ascii=False, separators=(",", ":"))
            ),
        }
    ]
    if object_crops_by_id is not None:
        for locked in locked_objects:
            object_id = str(locked.get("object_id") or "")
            for crop in object_crops_by_id.get(object_id) or []:
                if not isinstance(crop, dict) or not isinstance(crop.get("bytes"), bytes):
                    continue
                content.extend([
                    {"type": "text", "text": json.dumps({
                        "object_bound_crop": {
                            "object_id": object_id,
                            "page_number": crop.get("page_number"),
                            "group_id": crop.get("group_id"),
                        },
                    })},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/jpeg",
                        "data": base64.b64encode(crop["bytes"]).decode("ascii"),
                    }},
                ])
    else:
        for page_number, page_bytes in sorted((visual_pages_by_number or {}).items()):
            content.extend([
                {"type": "text", "text": json.dumps({"source_evidence_page": page_number})},
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(page_bytes).decode("ascii")}},
            ])
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
        "naming_decision_audit": build_naming_decision_audit(locked_objects, result),
        "preview": compose_name_preview(locked_objects, result),
    }
