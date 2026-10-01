from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, AbstractSet, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL,
    build_agent_usage_event,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
)
from agents.estimation_v2_facts_agent import _provider_json_text
from agents.schemas.estimation_v2_facts_schema import (
    FEATURE_KEYS, MANUFACTURING_FLAG_KEYS, MANUFACTURING_MEASUREMENT_KEYS,
    PURCHASED_SPECIFICATION_KEYS, SPECIFICATION_KEYS,
)
from use_cases.estimation_v2_composition import (
    LABOR_OPERATION_VALUES, OBJECT_FACTS_CONTRACT_VERSION, validate_object_facts,
)
from use_cases.labor_engine import BASELINES, MACHINE_REQUIREMENTS


ESTIMATION_V2_FACTS_AGENT_VERSION = "estimation_page_facts_agent_v12_per_object_previews"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_v2_page_facts_prompt.md"
MAX_OUTPUT_TOKENS = 12000
TIMEOUT_SECONDS = 180.0


def _number(value: Any, *, positive: bool = False) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if positive and result <= 0:
        return None
    return result


def _sparse(value: Any, allowed: Sequence[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): child for key, child in value.items() if key in allowed and child not in (None, "", "unknown")}


def _features(value: Any) -> dict[str, Any]:
    values = _sparse(value, FEATURE_KEYS)
    boolean_keys = {"toe_kick", "back_panel", "plumbing_cutout", "open_face"}
    count_keys = {"shelf_count", "door_count", "drawer_count", "bend_count", "anchor_count"}
    result: dict[str, Any] = {}
    for key, raw in values.items():
        if key in boolean_keys:
            if raw in {True, "yes", "true", 1}:
                result[key] = True
            elif raw in {False, "no", "false", 0}:
                result[key] = False
        elif key in count_keys:
            number = _number(raw)
            if number is not None and number >= 0:
                result[key] = int(number)
        elif key == "profile_section_mm":
            number = _number(raw, positive=True)
            if number is not None:
                result[key] = number
        else:
            result[key] = str(raw)
    return result


def _expand_object(
    compact: Mapping[str, Any], row: Mapping[str, Any], families: AbstractSet[str],
) -> dict[str, Any]:
    payload = row["input_payload"]
    object_payload = payload["object"]
    evidence = payload["evidence"]
    preview = str(evidence["primary_preview_ref"])
    materials = []
    material_ids: set[str] = set()
    for index, raw in enumerate(compact.get("m") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        requirement_id = str(raw.get("id") or f"m{index}")
        family = str(raw.get("f") or "")
        quantity = _number(raw.get("q"), positive=True)
        if family not in families or quantity is None:
            continue
        material_ids.add(requirement_id)
        materials.append({
            "requirement_id": requirement_id,
            "source_name": str(raw.get("n") or family), "family": family,
            "specification": _sparse(raw.get("s"), SPECIFICATION_KEYS),
            "quantity": quantity, "unit": str(raw.get("u") or "ea"),
            "evidence_refs": [preview],
        })
    operations = []
    for index, raw in enumerate(compact.get("op") or [], start=1):
        if not isinstance(raw, Mapping):
            continue
        code = str(raw.get("c") or "")
        quantity = _number(raw.get("q"), positive=True)
        if code not in LABOR_OPERATION_VALUES or code not in BASELINES or quantity is None:
            continue
        affected = [str(value) for value in raw.get("m") or [] if str(value) in material_ids]
        machine_code = MACHINE_REQUIREMENTS.get(code)
        operations.append({
            "operation_id": str(raw.get("id") or f"op{index}"),
            "operation_code": code,
            "route": "in_house_machine" if machine_code else "in_house_manual",
            "quantity": quantity, "unit": str(raw.get("u") or "unit"),
            "batch_key": f"{code}:{','.join(affected) or 'object'}",
            "machine_code": machine_code, "material_requirement_ids": affected,
            "basis": f"Compact planner physical driver: {quantity:g} {str(raw.get('u') or 'unit')}",
            "provenance": "estimated", "evidence_refs": [preview],
            "confidence": 50,
        })
    manufacturing = []
    for index, raw in enumerate(compact.get("mf") or [], start=1):
        if not isinstance(raw, Mapping) or raw.get("p") not in {"cnc_router", "sheet_laser"}:
            continue
        measurements = {key: None for key in MANUFACTURING_MEASUREMENT_KEYS}
        measurements.update({key: _number(value) for key, value in _sparse(raw.get("v"), MANUFACTURING_MEASUREMENT_KEYS).items()})
        flags = {key: "unknown" for key in MANUFACTURING_FLAG_KEYS}
        flags.update({key: value for key, value in _sparse(raw.get("g"), MANUFACTURING_FLAG_KEYS).items() if value in {"yes", "no", "unknown"}})
        manufacturing.append({
            "feature_id": str(raw.get("id") or f"mf{index}"), "process": raw["p"],
            "material_requirement_id": str(raw.get("m") or ""),
            "measurements": measurements, "flags": flags, "evidence_refs": [preview],
        })
    purchased = []
    for index, raw in enumerate(compact.get("pc") or [], start=1):
        if not isinstance(raw, Mapping) or _number(raw.get("q"), positive=True) is None:
            continue
        purchased.append({
            "component_id": str(raw.get("id") or f"pc{index}"),
            "component_type": str(raw.get("t") or "purchased_component"),
            "quantity": _number(raw.get("q"), positive=True), "unit": str(raw.get("u") or "ea"),
            "specification": _sparse(raw.get("s"), PURCHASED_SPECIFICATION_KEYS),
            "evidence_refs": [preview],
        })
    dimensions = list(compact.get("d") or [])
    dimensions += [0] * (3 - len(dimensions))
    review_items = []
    if not materials:
        review_items.append({"code": "material_requirement_missing", "severity": "blocking", "path": "materials", "message": "Compact planner returned no valid material", "evidence_refs": [preview]})
    if not operations:
        review_items.append({"code": "labor_result_unavailable", "severity": "blocking", "path": "labor_operations", "message": "Compact planner returned no valid operation", "evidence_refs": [preview]})
    facts = {
        "contract_version": OBJECT_FACTS_CONTRACT_VERSION,
        "input_id": str(row["input_id"]), "object_input_revision": int(row.get("object_input_revision") or 1),
        "run_id": payload["run_id"], "company_id": payload["company_id"],
        "object_id": object_payload["object_id"], "object_name": object_payload["object_name"],
        "quantity": object_payload.get("quantity") or 1,
        "status": "review_required" if review_items else "ready",
        "dimensions_mm": {key: (_number(value, positive=True) if value else None) for key, value in zip(("width", "depth", "height"), dimensions[:3])},
        "materials": materials, "features": _features(compact.get("x")),
        "manufacturing_features": manufacturing, "purchased_components": purchased,
        "labor_operations": operations, "source_facts": [], "review_items": review_items,
        "primary_preview_ref": preview,
    }
    return validate_object_facts(facts, allowed_material_families=families)


def run_estimation_v2_page_facts_agent(
    *, inputs: Sequence[Mapping[str, Any]], allowed_material_families: AbstractSet[str],
    preview_bytes_by_input: Mapping[str, bytes], model: str | None = None,
) -> dict[str, Any]:
    if not inputs:
        raise ValueError("inputs are required")
    selected_model = model or get_secret("CLAUDE_ESTIMATION_V2_PAGE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    targets = []
    for row in inputs:
        object_payload = row["input_payload"]["object"]
        targets.append({
            "id": object_payload["object_id"], "name": object_payload["object_name"],
            "quantity": object_payload.get("quantity") or 1,
            "locator_hints_only": {
                "dimensions": object_payload.get("dimensions"),
                "description": object_payload.get("notes"),
                "detected_materials": object_payload.get("detected_materials"),
            },
        })
    request = {
        "targets": targets, "allowed_material_families": sorted(allowed_material_families),
        "allowed_operation_codes": sorted(LABOR_OPERATION_VALUES),
        "specification_keys": list(SPECIFICATION_KEYS), "feature_keys": list(FEATURE_KEYS),
        "manufacturing_measurement_keys": list(MANUFACTURING_MEASUREMENT_KEYS),
        "manufacturing_flag_keys": list(MANUFACTURING_FLAG_KEYS),
        "purchased_specification_keys": list(PURCHASED_SPECIFICATION_KEYS),
    }
    started_at = datetime.now(UTC).isoformat()
    content: list[dict[str, Any]] = []
    for row in inputs:
        input_id = str(row["input_id"])
        object_payload = row["input_payload"]["object"]
        preview_bytes = preview_bytes_by_input.get(input_id)
        if not preview_bytes:
            raise ValueError(f"source preview is missing for input {input_id}")
        content.extend([
            {"type": "text", "text": json.dumps({
                "source_preview_for_object_id": object_payload["object_id"],
                "source_preview_for_input_id": input_id,
            }, ensure_ascii=False, separators=(",", ":"))},
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/webp",
                "data": base64.b64encode(preview_bytes).decode("ascii"),
            }},
        ])
    content.append({"type": "text", "text": json.dumps(request, ensure_ascii=False, separators=(",", ":"))})
    response = create_claude_message(
        get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0),
        model=selected_model, max_tokens=MAX_OUTPUT_TOKENS, temperature=0,
        system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{"role": "user", "content": content}],
    )
    finished_at = datetime.now(UTC).isoformat()
    raw = json.loads(_provider_json_text(extract_text_from_claude_response(response)))
    objects = raw.get("objects") if isinstance(raw, Mapping) else None
    if not isinstance(objects, list):
        raise ValueError("compact page result must contain objects")
    compact_by_id = {str(item.get("id") or ""): item for item in objects if isinstance(item, Mapping)}
    facts_by_input = {}
    failed = {}
    object_diagnostics = []
    for row in inputs:
        input_id = str(row["input_id"])
        object_id = str(row["input_payload"]["object"]["object_id"])
        try:
            facts_by_input[input_id] = _expand_object(compact_by_id[object_id], row, allowed_material_families)
            facts = facts_by_input[input_id]
            object_diagnostics.append({
                "input_id": input_id, "object_id": object_id, "status": "validated",
                "material_count": len(facts["materials"]),
                "operation_count": len(facts["labor_operations"]),
                "manufacturing_count": len(facts["manufacturing_features"]),
                "purchased_component_count": len(facts["purchased_components"]),
            })
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
            object_diagnostics.append({
                "input_id": input_id, "object_id": object_id, "status": "failed_validation",
                "error_type": type(exc).__name__, "error_message": str(exc)[:2000],
                "compact_payload": compact_by_id.get(object_id),
            })
    first = inputs[0]["input_payload"]
    usage = build_agent_usage_event(
        agent_name="estimation_v2_facts", operation="page_fact_extraction",
        company_id=str(first.get("company_id") or ""), run_id=str(first.get("run_id") or ""),
        file_name=str((first.get("document") or {}).get("file_name") or ""),
        object_id="page-batch", object_name=f"{len(inputs)} objects", model=selected_model,
        prompt_version=ESTIMATION_V2_FACTS_AGENT_VERSION, response=response,
        started_at=started_at, finished_at=finished_at,
        request_diagnostics={
            "object_count": len(inputs), "source_preview_count": len(preview_bytes_by_input),
            "per_object_source_previews": True, "compact_transport": True,
        },
    )
    usage["raw_usage"] = {
        **dict(usage.get("raw_usage") or {}),
        "object_diagnostics": object_diagnostics,
        "returned_object_ids": sorted(compact_by_id),
        "missing_object_ids": sorted(
            str(row["input_payload"]["object"]["object_id"])
            for row in inputs
            if str(row["input_payload"]["object"]["object_id"]) not in compact_by_id
        ),
    }
    return {
        "facts_by_input": facts_by_input, "failed": failed, "usage_event": usage,
        "compact_objects": compact_by_id,
    }
