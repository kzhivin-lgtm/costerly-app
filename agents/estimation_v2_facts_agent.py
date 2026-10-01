from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any, AbstractSet, Mapping

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_FALLBACK_MODEL,
    build_agent_usage_event,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
)
from agents.schemas.estimation_v2_facts_schema import (
    FEATURE_KEYS,
    MANUFACTURING_FLAG_KEYS,
    MANUFACTURING_MEASUREMENT_KEYS,
    PURCHASED_SPECIFICATION_KEYS,
    SPECIFICATION_KEYS,
    TRANSPORT_FIELDS,
)
from use_cases.estimation_v2_composition import (
    ESTIMATION_REASON_CODE_VALUES,
    LABOR_OPERATION_VALUES,
    OBJECT_FACTS_CONTRACT_VERSION,
    PROVENANCE_VALUES,
    validate_object_facts,
)
from use_cases.labor_engine import MACHINE_REQUIREMENTS


ESTIMATION_V2_FACTS_AGENT_VERSION = "estimation_object_facts_agent_v5"
ESTIMATION_V2_FACTS_MAX_OUTPUT_TOKENS = 16384
ESTIMATION_V2_FACTS_TIMEOUT_SECONDS = 180.0
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_v2_object_facts_prompt.md"


def _required_input(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = payload.get(name)
    if not isinstance(value, Mapping):
        raise ValueError(f"estimation_input_v2.{name} must be an object")
    return value


def _validate_input(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if payload.get("contract_version") != "estimation_input_v2":
        raise ValueError("Estimation v2 facts agent requires estimation_input_v2")
    object_payload = _required_input(payload, "object")
    evidence = _required_input(payload, "evidence")
    blocks = evidence.get("ocr_blocks")
    if not isinstance(blocks, list) or len(blocks) > 80:
        raise ValueError("estimation_input_v2 must contain at most 80 bounded OCR blocks")
    block_refs = [str(block.get("block_ref") or "") for block in blocks if isinstance(block, Mapping)]
    if len(block_refs) != len(blocks) or any(not ref for ref in block_refs) or len(block_refs) != len(set(block_refs)):
        raise ValueError("estimation_input_v2 OCR blocks require unique block_ref values")
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("estimation_input_v2.evidence.artifacts must be an array")
    preview = str(evidence.get("primary_preview_ref") or "")
    if not preview.startswith("storage://rfq-estimation-evidence/"):
        raise ValueError("estimation_input_v2 requires a private preview reference")
    return object_payload, evidence


def _provider_estimation_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Remove unverified Detection interpretations that can contaminate visual facts."""
    result = dict(payload)
    object_payload = dict(_required_input(payload, "object"))
    object_payload.pop("dimensions", None)
    object_payload.pop("notes", None)
    result["object"] = object_payload
    return result


def _assert_evidence_refs(result: Mapping[str, Any], evidence: Mapping[str, Any]) -> None:
    allowed = {
        str(block["block_ref"])
        for block in evidence.get("ocr_blocks") or []
        if isinstance(block, Mapping) and block.get("block_ref")
    }
    allowed.update(
        str(artifact["storage_ref"])
        for artifact in evidence.get("artifacts") or []
        if isinstance(artifact, Mapping) and artifact.get("storage_ref")
    )
    cited: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            refs = value.get("evidence_refs")
            if isinstance(refs, list):
                cited.update(str(ref) for ref in refs)
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(result)
    unknown = cited - allowed
    if unknown:
        raise ValueError(f"Estimation v2 facts agent invented evidence refs: {sorted(unknown)}")


def _number_text(value: Any, name: str, *, integer: bool = False) -> int | float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain a numeric string") from exc
    if integer:
        if not number.is_integer():
            raise ValueError(f"{name} must contain an integer string")
        return int(number)
    return number


def _confidence_number(value: Any, name: str) -> float:
    number = _number_text(value, name)
    if not 0 <= number <= 100:
        raise ValueError(f"{name} must be between 0 and 100")
    return float(number)


def _profile_section_number(value: Any, name: str) -> int | float:
    text = str(value or "").strip()
    match = re.fullmatch(
        r"([0-9]+(?:\.[0-9]+)?)\s*[xX×]\s*([0-9]+(?:\.[0-9]+)?)",
        text,
    )
    if match:
        first = float(match.group(1))
        second = float(match.group(2))
        if first != second:
            raise ValueError(f"{name} rectangular section requires an explicit weld face")
        return int(first) if first.is_integer() else first
    return _number_text(value, name)


def _key_values(
    items: Any,
    *,
    allowed: tuple[str, ...],
    name: str,
    ignored_unknown_keys: list[str] | None = None,
) -> dict[str, str]:
    if not isinstance(items, list):
        raise ValueError(f"{name} must be an array")
    result: dict[str, str] = {}
    for item in items:
        if not isinstance(item, Mapping) or set(item) != {"key", "value"}:
            raise ValueError(f"{name} entries must contain key and value")
        key = str(item["key"])
        if key not in allowed:
            if ignored_unknown_keys is not None:
                ignored_unknown_keys.append(f"{name}.{key}")
                continue
            raise ValueError(f"{name} contains unsupported key: {key}")
        if key in result:
            raise ValueError(f"{name} contains duplicate key: {key}")
        result[key] = str(item["value"])
    return result


def _provider_json_text(response_text: str) -> str:
    """Accept raw JSON or one exact Markdown JSON fence, never repair content."""
    text = str(response_text or "").strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip().lower() not in {"```", "```json"}:
        raise ValueError("Claude returned an unsupported Estimation v2 wrapper")
    if lines[-1].strip() != "```":
        raise ValueError("Claude returned an unterminated Estimation v2 JSON fence")
    return "\n".join(lines[1:-1]).strip()


def _normalize_provider_result(
    result: Mapping[str, Any],
    *,
    input_id: str,
    object_input_revision: int,
    estimation_input: Mapping[str, Any],
    production_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if set(result) != set(TRANSPORT_FIELDS):
        missing = set(TRANSPORT_FIELDS) - set(result)
        extra = set(result) - set(TRANSPORT_FIELDS)
        raise ValueError(f"facts transport fields are invalid, missing={sorted(missing)}, extra={sorted(extra)}")
    dimensions = result.get("dimensions_mm")
    if not isinstance(dimensions, list) or len(dimensions) != 3:
        raise ValueError("dimensions_mm transport must contain width, depth and height")
    numeric_specification = {
        "thickness_mm", "width_mm", "length_mm", "diameter_mm", "wall_thickness_mm"
    }
    materials = []
    for index, raw in enumerate(result.get("materials") or []):
        if not isinstance(raw, Mapping):
            raise ValueError(f"materials[{index}] must be an object")
        item = dict(raw)
        values = _key_values(
            item.pop("specification_items", []),
            allowed=SPECIFICATION_KEYS,
            name=f"materials[{index}].specification_items",
        )
        specification = {}
        for key, value in values.items():
            if value in {"", "unknown"}:
                continue
            specification[key] = (
                _number_text(value, f"materials[{index}].{key}")
                if key in numeric_specification else value
            )
        materials.append({
            **item,
            "quantity": None if item.get("quantity") == 0 else item.get("quantity"),
            "specification": specification,
        })

    raw_features = _key_values(result.get("features"), allowed=FEATURE_KEYS, name="features")
    boolean_features = {"toe_kick", "back_panel", "plumbing_cutout", "open_face"}
    count_features = {"shelf_count", "door_count", "drawer_count", "bend_count", "anchor_count"}
    features: dict[str, Any] = {}
    for key, value in raw_features.items():
        if value in {"", "unknown"}:
            continue
        if key in boolean_features:
            if value not in {"yes", "no"}:
                raise ValueError(f"features.{key} must be yes, no, or unknown")
            features[key] = value == "yes"
        elif key in count_features:
            parsed = _number_text(value, f"features.{key}", integer=True)
            if parsed != -1:
                features[key] = parsed
        elif key == "profile_section_mm":
            parsed = _profile_section_number(value, f"features.{key}")
            if parsed != 0:
                features[key] = parsed
        else:
            features[key] = value

    manufacturing = []
    ignored_manufacturing_keys: list[str] = []
    for index, raw in enumerate(result.get("manufacturing_features") or []):
        if not isinstance(raw, Mapping):
            raise ValueError(f"manufacturing_features[{index}] must be an object")
        item = dict(raw)
        measurement_values = _key_values(
            item.pop("measurement_items", []),
            allowed=MANUFACTURING_MEASUREMENT_KEYS,
            name=f"manufacturing_features[{index}].measurement_items",
            ignored_unknown_keys=ignored_manufacturing_keys,
        )
        flag_values = _key_values(
            item.pop("flag_items", []),
            allowed=MANUFACTURING_FLAG_KEYS,
            name=f"manufacturing_features[{index}].flag_items",
            ignored_unknown_keys=ignored_manufacturing_keys,
        )
        measurements = {key: None for key in MANUFACTURING_MEASUREMENT_KEYS}
        for key, value in measurement_values.items():
            parsed = _number_text(value, f"manufacturing_features[{index}].{key}")
            if parsed != -1:
                measurements[key] = parsed
        flags = {key: "unknown" for key in MANUFACTURING_FLAG_KEYS}
        for key, value in flag_values.items():
            if value not in {"yes", "no", "unknown"}:
                raise ValueError(
                    f"manufacturing_features[{index}].{key} must be yes, no, or unknown"
                )
            flags[key] = value
        manufacturing.append({
            **item,
            "measurements": measurements,
            "flags": flags,
        })

    purchased = []
    purchased_numeric = {"width_mm", "depth_mm", "height_mm", "thickness_mm"}
    for index, raw in enumerate(result.get("purchased_components") or []):
        if not isinstance(raw, Mapping):
            raise ValueError(f"purchased_components[{index}] must be an object")
        item = dict(raw)
        values = _key_values(
            item.pop("specification_items", []),
            allowed=PURCHASED_SPECIFICATION_KEYS,
            name=f"purchased_components[{index}].specification_items",
        )
        specification = {}
        for key, value in values.items():
            if value in {"", "unknown"}:
                continue
            if key in purchased_numeric:
                parsed = _number_text(value, f"purchased_components[{index}].{key}")
                if parsed != 0:
                    specification[key] = parsed
            elif key == "cutout_count":
                parsed = _number_text(value, f"purchased_components[{index}].{key}", integer=True)
                if parsed != -1:
                    specification[key] = parsed
            else:
                specification[key] = value
        purchased.append({
            **item,
            "quantity": None if item.get("quantity") == 0 else item.get("quantity"),
            "specification": specification,
        })

    available_machines = {
        str(row.get("machine_code") or "")
        for row in ((production_context or {}).get("machines") or [])
        if isinstance(row, Mapping)
        and row.get("availability_status") == "in_house"
        and row.get("machine_code")
    }
    labor_operations = []
    unavailable_operation_machines: list[tuple[int, str]] = []
    for index, raw in enumerate(result.get("labor_operations") or []):
        if not isinstance(raw, Mapping):
            raise ValueError(f"labor_operations[{index}] must be an object")
        item = dict(raw)
        material_ids = item.get("material_requirement_ids")
        if not isinstance(material_ids, list):
            raise ValueError(f"labor_operations[{index}].material_requirement_ids must be an array")
        operation_code = str(item.get("operation_code") or "")
        machine_code = MACHINE_REQUIREMENTS.get(operation_code)
        if machine_code and machine_code not in available_machines:
            unavailable_operation_machines.append((index, machine_code))
        labor_operations.append({
            **item,
            "route": "in_house_machine" if machine_code else "in_house_manual",
            "machine_code": machine_code,
            "quantity": _number_text(item.get("quantity"), f"labor_operations[{index}].quantity"),
            "confidence": _confidence_number(
                item.get("confidence"), f"labor_operations[{index}].confidence"
            ),
            "material_requirement_ids": [str(value) for value in material_ids],
        })
    object_payload = _required_input(estimation_input, "object")
    evidence = _required_input(estimation_input, "evidence")
    normalized_dimensions = {
        key: None if value == 0 else value
        for key, value in zip(("width", "depth", "height"), dimensions)
    }
    review_items = list(result.get("review_items") or [])
    if ignored_manufacturing_keys:
        review_items.append({
            "code": "manufacturing_feature_unsupported",
            "severity": "warning",
            "path": "manufacturing_features",
            "message": "Ignored unsupported optional manufacturing keys: "
            + ", ".join(sorted(set(ignored_manufacturing_keys))),
            "evidence_refs": [evidence.get("primary_preview_ref")],
        })
    blocking_review = any(
        isinstance(item, Mapping) and item.get("severity") == "blocking"
        for item in review_items
    )
    server_gaps: list[tuple[str, str, str]] = []
    if not materials:
        server_gaps.append(("material_requirement_missing", "materials", "Material requirements are missing"))
    for index, material in enumerate(materials):
        if material.get("quantity") is None:
            server_gaps.append(("material_quantity_missing", f"materials[{index}].quantity", "Material quantity is missing"))
    for index, component in enumerate(purchased):
        if component.get("quantity") is None:
            server_gaps.append(("material_quantity_missing", f"purchased_components[{index}].quantity", "Purchased component quantity is missing"))
    if not labor_operations:
        server_gaps.append(("labor_result_unavailable", "labor_operations", "Production operations are missing"))
    for index, machine_code in unavailable_operation_machines:
        server_gaps.append((
            "machinery_route_unresolved",
            f"labor_operations[{index}].machine_code",
            f"Required company machinery capability is unavailable: {machine_code}",
        ))
    required_gap = bool(server_gaps)
    normalized_status = result.get("status")
    if required_gap and not blocking_review:
        existing_paths = {
            str(item.get("path") or "") for item in review_items if isinstance(item, Mapping)
        }
        for code, path, message in server_gaps:
            if path not in existing_paths:
                review_items.append({
                    "code": code, "severity": "blocking", "path": path,
                    "message": message, "evidence_refs": [evidence.get("primary_preview_ref")],
                })
        blocking_review = True
    if blocking_review or required_gap:
        normalized_status = "review_required"
    elif normalized_status == "review_required":
        normalized_status = "ready"
    return {
        "contract_version": OBJECT_FACTS_CONTRACT_VERSION,
        "input_id": input_id,
        "object_input_revision": object_input_revision,
        "run_id": estimation_input.get("run_id"),
        "company_id": estimation_input.get("company_id"),
        "object_id": object_payload.get("object_id"),
        "object_name": object_payload.get("object_name"),
        "quantity": object_payload.get("quantity"),
        "status": normalized_status,
        "dimensions_mm": normalized_dimensions,
        "materials": materials,
        "features": features,
        "manufacturing_features": manufacturing,
        "purchased_components": purchased,
        "labor_operations": labor_operations,
        "source_facts": result.get("source_facts"),
        "review_items": review_items,
        "primary_preview_ref": evidence.get("primary_preview_ref"),
    }


def _assert_bound_identifiers(
    result: Mapping[str, Any],
    *,
    input_id: str,
    object_input_revision: int,
    estimation_input: Mapping[str, Any],
) -> None:
    object_payload = _required_input(estimation_input, "object")
    evidence = _required_input(estimation_input, "evidence")
    expected = {
        "input_id": input_id,
        "object_input_revision": object_input_revision,
        "run_id": estimation_input.get("run_id"),
        "company_id": estimation_input.get("company_id"),
        "object_id": object_payload.get("object_id"),
        "object_name": object_payload.get("object_name"),
        "quantity": object_payload.get("quantity"),
        "primary_preview_ref": evidence.get("primary_preview_ref"),
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(f"Estimation v2 facts agent changed bound field: {key}")


def run_estimation_v2_facts_agent(
    *,
    input_id: str,
    object_input_revision: int,
    estimation_input: Mapping[str, Any],
    allowed_material_families: AbstractSet[str],
    preview_bytes: bytes,
    production_context: Mapping[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Extract bounded facts from one frozen input and its persisted preview."""
    object_payload, evidence = _validate_input(estimation_input)
    resolved_input_id = str(input_id or "").strip()
    if not resolved_input_id:
        raise ValueError("input_id is required")
    if isinstance(object_input_revision, bool) or not isinstance(object_input_revision, int) or object_input_revision < 1:
        raise ValueError("object_input_revision must be a positive integer")
    if not isinstance(preview_bytes, (bytes, bytearray)) or not preview_bytes:
        raise ValueError("preview_bytes are required")
    if not {str(value).strip() for value in allowed_material_families if str(value).strip()}:
        raise ValueError("allowed_material_families must not be empty")
    selected_model = model or get_secret(
        "CLAUDE_ESTIMATION_V2_FACTS_MODEL", DEFAULT_CLAUDE_FALLBACK_MODEL
    )
    request = {
        "input_id": resolved_input_id,
        "object_input_revision": object_input_revision,
        "estimation_input": _provider_estimation_input(estimation_input),
        "allowed_material_families": sorted(allowed_material_families),
        "transport_contract": {
            "required_fields": sorted(TRANSPORT_FIELDS),
            "allowed_labor_operations": sorted(LABOR_OPERATION_VALUES),
            "allowed_reason_codes": sorted(ESTIMATION_REASON_CODE_VALUES),
            "allowed_provenance": sorted(PROVENANCE_VALUES),
            "allowed_review_severities": ["blocking", "warning"],
            "allowed_manufacturing_processes": ["cnc_router", "sheet_laser"],
            "allowed_tri_state_values": ["yes", "no", "unknown"],
            "specification_keys": list(SPECIFICATION_KEYS),
            "feature_keys": list(FEATURE_KEYS),
            "purchased_specification_keys": list(PURCHASED_SPECIFICATION_KEYS),
        },
        "transport_orders": {"dimensions_mm": ["width", "depth", "height"]},
        "transport_item_fields": {
            "material": [
                "requirement_id", "source_name", "family", "specification_items",
                "quantity", "unit", "evidence_refs",
            ],
            "specification_item": ["key", "value"],
            "feature": ["key", "value"],
            "manufacturing_feature": [
                "feature_id", "process", "material_requirement_id",
                "measurement_items", "flag_items", "evidence_refs",
            ],
            "purchased_component": [
                "component_id", "component_type", "quantity", "unit",
                "specification_items", "evidence_refs",
            ],
            "source_fact": ["path", "value", "provenance", "evidence_refs"],
            "review_item": ["code", "severity", "path", "message", "evidence_refs"],
            "labor_operation": [
                "operation_id", "operation_code", "quantity", "unit",
                "batch_key", "material_requirement_ids", "basis",
                "provenance", "evidence_refs", "confidence",
            ],
        },
    }
    started_at = datetime.now(UTC).isoformat()
    response = create_claude_message(
        get_anthropic_client().with_options(
            timeout=ESTIMATION_V2_FACTS_TIMEOUT_SECONDS,
            max_retries=0,
        ),
        model=selected_model,
        max_tokens=ESTIMATION_V2_FACTS_MAX_OUTPUT_TOKENS,
        temperature=0,
        system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{
            "role": "user",
            "content": [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/webp",
                    "data": base64.b64encode(bytes(preview_bytes)).decode("ascii"),
                },
            }, {
                "type": "text",
                "text": "The first content block is the persisted source preview. "
                "Extract one bounded object-facts result for the named object:\n"
                + json.dumps(request, ensure_ascii=False, separators=(",", ":")),
            }],
        }],
    )
    finished_at = datetime.now(UTC).isoformat()
    stop_reason = str(getattr(response, "stop_reason", "") or "unknown")
    response_text = extract_text_from_claude_response(response)
    if stop_reason == "max_tokens":
        raise RuntimeError(
            "Claude truncated Estimation v2 facts at the output token limit "
            f"({ESTIMATION_V2_FACTS_MAX_OUTPUT_TOKENS}); result was not published"
        )
    try:
        raw = json.loads(_provider_json_text(response_text))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Claude returned invalid Estimation v2 transport JSON "
            f"(stop_reason={stop_reason}, output_chars={len(response_text)}, "
            f"error_position={exc.pos})"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Estimation v2 facts transport must be an object")
    validated = validate_object_facts(
        _normalize_provider_result(
            raw,
            input_id=resolved_input_id,
            object_input_revision=object_input_revision,
            estimation_input=estimation_input,
            production_context=production_context,
        ),
        allowed_material_families=allowed_material_families,
    )
    _assert_bound_identifiers(
        validated,
        input_id=resolved_input_id,
        object_input_revision=object_input_revision,
        estimation_input=estimation_input,
    )
    _assert_evidence_refs(validated, evidence)
    usage_event = build_agent_usage_event(
        agent_name="estimation_v2_facts",
        operation="object_fact_extraction",
        company_id=str(estimation_input.get("company_id") or ""),
        run_id=str(estimation_input.get("run_id") or ""),
        file_name=str((estimation_input.get("document") or {}).get("file_name") or ""),
        object_id=str(object_payload.get("object_id") or ""),
        object_name=str(object_payload.get("object_name") or ""),
        model=selected_model,
        prompt_version=ESTIMATION_V2_FACTS_AGENT_VERSION,
        response=response,
        started_at=started_at,
        finished_at=finished_at,
        request_diagnostics={
            "input_contract_version": estimation_input.get("contract_version"),
            "object_input_revision": object_input_revision,
            "source_document_attached": False,
            "source_preview_attached": True,
            "ocr_rerun": False,
            "stop_reason": stop_reason,
            "max_output_tokens": ESTIMATION_V2_FACTS_MAX_OUTPUT_TOKENS,
        },
    )
    return {"facts": validated, "usage_event": usage_event}
