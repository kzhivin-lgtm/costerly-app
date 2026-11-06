"""Assembly-first visual BOM extraction, bounded to immutable evidence."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from use_cases.estimation_composition_scope import geometry_scope
from agents.estimation_visual_evidence import page_content
from use_cases.estimation_evidence_map import apply_evidence_measurements

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL, build_agent_usage_event, extract_text_from_claude_response,
    get_anthropic_client, get_secret,
)
from agents.estimation_v4_1_material_facts_agent import (
    MAX_OUTPUT_TOKENS, TIMEOUT_SECONDS, _create_message_with_hard_timeout, _json_object,
    build_v4_1_evidence_batches,
)


ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION = "estimation_calculation_v6_1_evidence_map_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_assembly_bom_prompt.md"
V6_PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_calculation_v6_prompt.md"
RECONCILIATION_PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_assembly_bom_reconciliation_prompt.md"


def _content(*, batch: Mapping[str, Any], payload: Mapping[str, Any], dimension_graph: Mapping[str, Any], dimension_scale_gate: Mapping[str, Any], allowed_material_families: Sequence[str], composition_scope: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    pages = []
    detail_budget = 12
    for page in batch["pages"]:
        visual, used = page_content(page_bytes=page["bytes"], storage_ref=page["storage_ref"], page_number=page["page_number"],
                                   payloads=[payload], views=dimension_graph.get("views") or [], detail_budget=detail_budget)
        content.extend(visual)
        detail_budget -= used
        pages.append({
            "page_number": page["page_number"], "source_evidence_ref": page["storage_ref"],
            "regions": [
                {"region_id": f"p{page['page_number']}-region-{index:03d}", **dict(region)}
                for index, region in enumerate(page["regions"], start=1)
                if isinstance(region, Mapping)
            ],
            "ocr_blocks": page["ocr_blocks"],
            "ocr_literal_items": page["ocr_literal_items"],
        })
    object_payload = payload.get("object") or {}
    content.append({"type": "text", "text": json.dumps({
        "batch_id": batch["batch_id"], "object": {
            "object_id": object_payload.get("object_id"), "object_name": object_payload.get("object_name"),
            "quantity": object_payload.get("quantity"),
        },
        "pages": pages, "dimension_graph": dimension_graph,
        "dimension_scale_gate": dimension_scale_gate,
        "composition_scope": geometry_scope(composition_scope),
        "allowed_material_families": sorted(allowed_material_families),
    }, ensure_ascii=False, separators=(",", ":"))})
    return content


def _validate_coverage(*, response: Mapping[str, Any], expected_region_ids: set[str]) -> list[dict[str, Any]]:
    """Preserve declared coverage for audit, without making it a model-output gate.

    A visual response can still form a bounded material estimate when it has
    not produced the optional coverage ledger.  The deterministic composer
    records completeness and invalid entries in ``coverage_audit`` instead.
    """
    coverage = response.get("coverage")
    if not isinstance(coverage, list):
        return []
    return [dict(item) for item in coverage if isinstance(item, Mapping)]


def _validate_response(*, response: Mapping[str, Any], batch: Mapping[str, Any]) -> dict[str, Any]:
    # Batch/page acknowledgements are optional response metadata. The request
    # already bounds the pixels supplied to this call, so their absence must
    # never discard usable assemblies and dimensions.
    document_unit = response.get("document_unit")
    assemblies = response.get("assemblies")
    if not isinstance(assemblies, list):
        raise ValueError("assembly BOM response requires assemblies")
    if not isinstance(document_unit, Mapping):
        raise ValueError("assembly BOM response requires document_unit")
    expected_region_ids = {
        f"p{page['page_number']}-region-{index:03d}"
        for page in batch["pages"]
        for index, region in enumerate(page.get("regions") or [], start=1)
        if isinstance(region, Mapping)
    }
    return {
        "document_unit": dict(document_unit),
        "assemblies": [dict(item) for item in assemblies if isinstance(item, Mapping)],
        "secondary_items": [dict(item) for item in response.get("secondary_items") or [] if isinstance(item, Mapping)],
        "omissions": [str(item) for item in response.get("omissions") or [] if str(item).strip()],
        "coverage": _validate_coverage(response=response, expected_region_ids=expected_region_ids),
        "view_interpretations": [dict(item) for item in response.get("view_interpretations") or [] if isinstance(item, Mapping)],
        "dimension_bindings": [dict(item) for item in response.get("dimension_bindings") or [] if isinstance(item, Mapping)],
    }


def _reconciliation_content(
    *, payload: Mapping[str, Any], dimension_graph: Mapping[str, Any], dimension_scale_gate: Mapping[str, Any], batch_extractions: Sequence[Mapping[str, Any]], composition_scope: Mapping[str, Any] | None,
    allowed_material_families: Sequence[str],
) -> list[dict[str, Any]]:
    """Reconcile bounded visual observations without re-uploading all pages.

    The first pass pays for pixels once per bounded batch.  This second pass
    sees only cited observations plus the immutable graph, so it can join a
    drawing spread without turning a 39-page PDF into one giant vision call.
    """
    object_payload = payload.get("object") or {}
    return [{"type": "text", "text": json.dumps({
        "object": {
            "object_id": object_payload.get("object_id"), "object_name": object_payload.get("object_name"),
            "quantity": object_payload.get("quantity"),
        },
        "dimension_graph": dimension_graph, "dimension_scale_gate": dimension_scale_gate,
        "composition_scope": geometry_scope(composition_scope),
        "batch_observations": list(batch_extractions),
        "allowed_material_families": sorted(allowed_material_families),
    }, ensure_ascii=False, separators=(",", ":"))}]


def _validate_reconciliation(*, response: Mapping[str, Any]) -> dict[str, Any]:
    document_unit = response.get("document_unit")
    assemblies = response.get("assemblies")
    if not isinstance(document_unit, Mapping) or not isinstance(assemblies, list):
        raise ValueError("assembly reconciliation requires assemblies")
    return {
        "document_unit": dict(document_unit),
        "assemblies": [dict(item) for item in assemblies if isinstance(item, Mapping)],
        "secondary_items": [dict(item) for item in response.get("secondary_items") or [] if isinstance(item, Mapping)],
        "omissions": [str(item) for item in response.get("omissions") or [] if str(item).strip()],
        "coverage": [dict(item) for item in response.get("coverage") or [] if isinstance(item, Mapping)],
        "view_interpretations": [dict(item) for item in response.get("view_interpretations") or [] if isinstance(item, Mapping)],
        "dimension_bindings": [dict(item) for item in response.get("dimension_bindings") or [] if isinstance(item, Mapping)],
    }


def run_estimation_assembly_bom_agent(*, input_row: Mapping[str, Any], evidence_page_bytes_by_ref: Mapping[str, bytes], dimension_graph: Mapping[str, Any], dimension_scale_gate: Mapping[str, Any], allowed_material_families: Sequence[str], composition_scope: Mapping[str, Any] | None = None, model: str | None = None, cb_parts_scope: Mapping[str, Any] | None = None, record=None) -> dict[str, Any]:
    if cb_parts_scope is not None:
        return _run_cb_parts(input_row=input_row, page_bytes=evidence_page_bytes_by_ref,
            dimension_graph=dimension_graph, dimension_scale_gate=dimension_scale_gate,
            scope=cb_parts_scope, allowed_material_families=allowed_material_families, model=model, record=record)
    payload = input_row.get("input_payload") or {}
    batches = build_v4_1_evidence_batches(payload)
    selected_model = model or get_secret("CLAUDE_ESTIMATION_ASSEMBLY_BOM_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    client = get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0)
    started_at = datetime.now(UTC).isoformat()
    prompt_path = V6_PROMPT_PATH if (composition_scope or {}).get("construction_version") else PROMPT_PATH
    responses: list[Any] = []
    observations: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for batch in batches:
        pages = []
        for page in batch["pages"]:
            page_bytes = evidence_page_bytes_by_ref.get(page["storage_ref"])
            if not page_bytes:
                raise ValueError(f"assembly BOM source page is missing: {page['storage_ref']}")
            pages.append({**page, "bytes": page_bytes})
        resolved_batch = {**batch, "pages": pages}
        response = _create_message_with_hard_timeout(
            client, timeout_seconds=TIMEOUT_SECONDS, model=selected_model, max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0, system=prompt_path.read_text(encoding="utf-8").strip(),
            messages=[{"role": "user", "content": _content(batch=resolved_batch, payload=payload, dimension_graph=dimension_graph, dimension_scale_gate=dimension_scale_gate, allowed_material_families=allowed_material_families, composition_scope=composition_scope)}],
        )
        responses.append(response)
        observations.append({"batch_id": batch["batch_id"], **_validate_response(
            response=_json_object(extract_text_from_claude_response(response)), batch=batch,
        )})
        diagnostics.append({
            "batch_id": batch["batch_id"], "topic": batch.get("topic"),
            "page_numbers": [page["page_number"] for page in batch["pages"]],
        })
    if len(observations) == 1:
        parsed = {
            "document_unit": observations[0]["document_unit"],
            "assemblies": observations[0]["assemblies"],
            "secondary_items": observations[0]["secondary_items"],
            "omissions": observations[0]["omissions"], "coverage": observations[0]["coverage"],
            "view_interpretations": observations[0]["view_interpretations"],
            "dimension_bindings": observations[0]["dimension_bindings"],
        }
    else:
        response = _create_message_with_hard_timeout(
            client, timeout_seconds=TIMEOUT_SECONDS, model=selected_model, max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0, system=RECONCILIATION_PROMPT_PATH.read_text(encoding="utf-8").strip(),
            messages=[{"role": "user", "content": _reconciliation_content(
                payload=payload, dimension_graph=dimension_graph, dimension_scale_gate=dimension_scale_gate, batch_extractions=observations, composition_scope=composition_scope,
                allowed_material_families=allowed_material_families,
            )}],
        )
        responses.append(response)
        parsed = _validate_reconciliation(response=_json_object(extract_text_from_claude_response(response)))
        diagnostics.append({"stage": "reconciliation", "batch_count": len(observations)})
    total_input = sum(int(getattr(getattr(item, "usage", None), "input_tokens", 0) or 0) for item in responses)
    total_output = sum(int(getattr(getattr(item, "usage", None), "output_tokens", 0) or 0) for item in responses)
    aggregate_response = SimpleNamespace(usage=SimpleNamespace(
        input_tokens=total_input, output_tokens=total_output,
        cache_creation_input_tokens=0, cache_read_input_tokens=0,
    ))
    usage = build_agent_usage_event(
        agent_name="estimation", operation="assembly_first_bom", company_id=str(payload.get("company_id") or ""),
        run_id=str(payload.get("run_id") or ""), file_name=str((payload.get("document") or {}).get("file_name") or ""),
        object_id=str((payload.get("object") or {}).get("object_id") or ""), object_name=str((payload.get("object") or {}).get("object_name") or ""),
        model=selected_model, prompt_version=ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION, response=aggregate_response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"batch_count": len(batches), "batches": diagnostics, "assembly_first": True,
                             "composition_scope": bool(composition_scope),
                             "dimension_scale_gate": dict(dimension_scale_gate)},
    )
    parsed = apply_evidence_measurements(parsed, scope=composition_scope or {})
    return {"extraction": parsed, "usage_event": usage}


def _run_cb_parts(*, input_row, page_bytes, dimension_graph, dimension_scale_gate,
                  scope, allowed_material_families, model=None, record=None):
    """Explicit V6.2 Calculate contract. One request, no batch/reconcile calls.

    The legacy route is unchanged. Saved diagnostic scopes retain their failed
    upstream status; a new Parts result never certifies the upstream chain.
    """
    from hashlib import sha256
    from agents.estimation_understanding_agent import (
        MODEL, CB_RULEBOOK, prepare_content, planner_front_ids, validate_assembly_plan,
    )
    from use_cases.estimation_cb_parts import DEFAULT_MATERIAL, compose_cb_parts, validate_cb_part_counts, compose_cb_sized_parts

    rule = CB_RULEBOOK["parts"]
    version = scope.get("parts_version", rule["version"])
    if version == rule["previous"]["version"]:
        rule = rule["previous"]
    elif version == rule["v2"]["version"]:
        rule = rule["v2"]
    elif version != rule["version"]:
        raise ValueError("unknown CB Parts version")
    count_only = version == "CB Parts V2"
    sized = version == "CB Parts V3"
    if scope.get("input_id") != input_row.get("input_id"):
        raise ValueError("CB Parts scope belongs to a different input")
    if model not in (None, MODEL):
        raise ValueError("CB Parts experiment requires the selected Haiku model")
    if not (count_only or sized) and "ldsp" not in allowed_material_families:
        raise ValueError("CB Parts requires the LDSP fallback family")
    content, manifests = prepare_content([input_row], page_bytes)
    known = {v["view_id"] for v in manifests[0]["known_views"]}
    front_ids = planner_front_ids(scope["front"], known)
    validate_assembly_plan(scope["planner"], known, front_ids)
    context = {"calculation_scope": scope}
    if not (count_only or sized):
        context.update(dimension_graph=dimension_graph, dimension_scale_gate=dimension_scale_gate,
            default_material=DEFAULT_MATERIAL, allowed_material_families=sorted(allowed_material_families))
    content.append({"type": "text", "text": json.dumps(context, ensure_ascii=False, separators=(",", ":"))})
    request = dict(model=MODEL, max_tokens=14000, output_config={"effort": "low"}, thinking={"type": "disabled"},
        system=rule["path"].read_text().strip(),
        messages=[{"role": "user", "content": content}])
    started = datetime.now(UTC).isoformat()
    if record:
        record("calculation_request", request, None)
    response = _create_message_with_hard_timeout(
        get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
    if record:
        record("calculation", request, response)
    if getattr(response, "stop_reason", None) != "end_turn":
        raise ValueError("CB Parts response did not finish normally")
    parsed = _json_object(extract_text_from_claude_response(response))
    if sized:
        result = {"parts_sized": compose_cb_sized_parts(parsed, scope=scope),
            "status": "cb_parts_sized_requires_review", "upstream_status": scope.get("upstream_status", {})}
    elif count_only:
        validate_cb_part_counts(parsed, scope=scope)
        result = {"parts_count": parsed, "status": "cb_parts_count_requires_review",
            "upstream_status": scope.get("upstream_status", {})}
    else:
        result = {"bom": compose_cb_parts(response=parsed, input_row=input_row, dimension_graph=dimension_graph,
            scope=scope, allowed_material_families=allowed_material_families)}
    payload = input_row["input_payload"]
    usage = build_agent_usage_event(agent_name="estimation", operation="cb_parts_calculation",
        company_id=str(payload.get("company_id") or ""), run_id=str(payload.get("run_id") or ""),
        file_name=str(payload.get("document", {}).get("file_name") or ""),
        object_id=str(payload.get("object", {}).get("object_id") or ""),
        object_name=str(payload.get("object", {}).get("object_name") or ""), model=MODEL,
        prompt_version=version, response=response, started_at=started, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"provider_calls": 1, "upstream_status": scope.get("upstream_status", {})})
    return {"extraction": parsed, **result, "usage_event": usage,
        "prompt_version": version, "prompt_sha256": sha256(request["system"].encode()).hexdigest()}
