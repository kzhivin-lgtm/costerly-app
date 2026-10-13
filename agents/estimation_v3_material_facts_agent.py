"""V3 material-only Object Facts extraction.

This is the active extraction boundary for the Material Resolver and Material
Engine. It deliberately has no labor, machinery, price or overhead behavior.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any, AbstractSet, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL,
    build_agent_usage_event,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
)
from use_cases.estimation_v3_material_contract import (
    COMPACT_PART_KEYS,
    MATERIAL_FACTS_V3_VERSION,
    SPECIFICATION_KEYS,
    validate_material_facts_v3,
)


# The unit and purchasable quantity belong to the selected supply candidate,
# not to the vision model.  Bump the extraction version so cached facts that
# contained model-guessed units can never feed the current Material Engine.
ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION = "estimation_material_facts_v3_2"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_v3_material_facts_prompt.md"
MAX_OUTPUT_TOKENS = 8_000
TIMEOUT_SECONDS = 180.0


def _number(value: Any, *, positive: bool = False) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if not positive or result > 0 else None


def _identifier(value: Any, default: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9_.:-]+", "_", str(value or "").strip().casefold()).strip("_") or default
    result, suffix = base, 2
    while result in used:
        result, suffix = f"{base}_{suffix}", suffix + 1
    used.add(result)
    return result


def _sparse(value: Any) -> dict[str, Any]:
    return {
        str(key): child for key, child in value.items()
        if key in SPECIFICATION_KEYS and child not in (None, "", "unknown")
    } if isinstance(value, Mapping) else {}


def _json_object(text: str) -> Mapping[str, Any]:
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise ValueError("V3 material facts returned an invalid JSON fence")
        value = "\n".join(lines[1:-1]).strip()
    parsed = json.loads(value)
    if not isinstance(parsed, Mapping):
        raise ValueError("V3 material facts must be a JSON object")
    return parsed


def _expand(
    compact: Mapping[str, Any], row: Mapping[str, Any], families: AbstractSet[str],
) -> dict[str, Any]:
    payload = row["input_payload"]
    object_payload = payload["object"]
    preview = str((payload.get("evidence") or {}).get("primary_preview_ref") or "")
    materials, reviews, material_ids = [], [], set()
    for index, raw in enumerate(compact.get("m") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        family = str(raw.get("f") or "")
        if family not in families:
            continue
        requirement_id = _identifier(raw.get("id"), f"m{index}", material_ids)
        materials.append({
            "requirement_id": requirement_id,
            "source_name": str(raw.get("n") or family),
            "family": family,
            "specification": _sparse(raw.get("s")),
            # The extractor establishes material identity, evidence-backed
            # direct counts and geometry only.
            # Resolver supplies the concrete purchasable form and Engine owns
            # its unit and conversion.  Keeping them null here prevents a
            # guessed "piece" from becoming a false purchase demand.
            "quantity": _number(raw.get("q"), positive=True),
            "unit": None,
            "evidence_refs": [preview],
        })
    parts, part_ids = [], set()
    for index, raw in enumerate(compact.get("p") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        material_id = str(raw.get("m") or "")
        quantity = _number(raw.get("q"), positive=True)
        length, width = _number(raw.get("l"), positive=True), _number(raw.get("w"), positive=True)
        if material_id not in material_ids or quantity is None or length is None or width is None:
            continue
        parts.append({
            "part_id": _identifier(raw.get("id"), f"p{index}", part_ids),
            "material_requirement_id": material_id,
            "quantity": quantity,
            "length_mm": length,
            "width_mm": width,
            "rotation_allowed": str(raw.get("r") or "yes").casefold() != "no",
            "evidence_refs": [preview],
        })
    if not materials:
        reviews.append({
            "code": "material_requirement_missing", "severity": "blocking",
            "path": "materials", "message": "No valid material demand was extracted",
            "evidence_refs": [preview],
        })
    dimensions = list(compact.get("d") or []) + [0, 0, 0]
    facts = {
        "contract_version": MATERIAL_FACTS_V3_VERSION,
        "input_id": str(row["input_id"]),
        "object_input_revision": int(row.get("object_input_revision") or 1),
        "run_id": payload["run_id"], "company_id": payload["company_id"],
        "object_id": object_payload["object_id"], "object_name": object_payload["object_name"],
        "quantity": object_payload.get("quantity") or 1,
        "status": "review_required" if reviews else "ready",
        "dimensions_mm": {
            key: _number(value, positive=True) if value else None
            for key, value in zip(("width", "depth", "height"), dimensions[:3])
        },
        "materials": materials,
        "parts": parts,
        "review_items": reviews,
        "primary_preview_ref": preview,
    }
    return validate_material_facts_v3(facts, allowed_material_families=families)


def run_estimation_v3_material_facts_agent(
    *, inputs: Sequence[Mapping[str, Any]], allowed_material_families: AbstractSet[str],
    preview_bytes_by_input: Mapping[str, bytes],
    pricing_key_fields_by_family: Mapping[str, Sequence[str]] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    if not inputs:
        raise ValueError("inputs are required")
    selected_model = model or get_secret("CLAUDE_ESTIMATION_V3_PAGE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    targets = [{
        "id": row["input_payload"]["object"]["object_id"],
        "name": row["input_payload"]["object"]["object_name"],
        "quantity": row["input_payload"]["object"].get("quantity") or 1,
        "locator_hints_only": {
            "dimensions": row["input_payload"]["object"].get("dimensions"),
            "description": row["input_payload"]["object"].get("notes"),
            "detected_materials": row["input_payload"]["object"].get("detected_materials"),
        },
    } for row in inputs]
    request = {
        "targets": targets, "allowed_material_families": sorted(allowed_material_families),
        "specification_keys": list(SPECIFICATION_KEYS), "part_keys": list(COMPACT_PART_KEYS),
        "pricing_key_fields_by_family": {
            str(family): list(fields)
            for family, fields in sorted((pricing_key_fields_by_family or {}).items())
        },
    }
    content: list[dict[str, Any]] = []
    for row in inputs:
        input_id = str(row["input_id"])
        preview = preview_bytes_by_input.get(input_id)
        if not preview:
            raise ValueError(f"source preview is missing for input {input_id}")
        content.extend([
            {"type": "text", "text": json.dumps({"source_preview_for_object_id": row["input_payload"]["object"]["object_id"]})},
            {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(preview).decode("ascii")}},
        ])
    content.append({"type": "text", "text": json.dumps(request, ensure_ascii=False, separators=(",", ":"))})
    started_at = datetime.now(UTC).isoformat()
    response = create_claude_message(
        get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0),
        model=selected_model, max_tokens=MAX_OUTPUT_TOKENS, temperature=0,
        system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{"role": "user", "content": content}],
    )
    compact = _json_object(extract_text_from_claude_response(response))
    by_object = {str(item.get("id") or ""): item for item in compact.get("objects") or [] if isinstance(item, Mapping)}
    facts_by_input, failed = {}, {}
    for row in inputs:
        input_id, object_id = str(row["input_id"]), str(row["input_payload"]["object"]["object_id"])
        try:
            facts_by_input[input_id] = _expand(by_object.get(object_id) or {}, row, allowed_material_families)
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    first = inputs[0]["input_payload"]
    usage = build_agent_usage_event(
        agent_name="estimation_v3_material_facts", operation="material_fact_extraction",
        company_id=str(first.get("company_id") or ""), run_id=str(first.get("run_id") or ""),
        file_name=str((first.get("document") or {}).get("file_name") or ""),
        object_id="page-batch", object_name=f"{len(inputs)} objects", model=selected_model,
        prompt_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION, response=response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"object_count": len(inputs), "material_only": True},
    )
    return {"facts_by_input": facts_by_input, "failed": failed, "usage_event": usage}
