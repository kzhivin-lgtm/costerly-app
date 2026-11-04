"""Whole-file Estimation Analyze pass producing locked object composition scopes."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL, build_agent_usage_event, extract_text_from_claude_response,
    get_anthropic_client, get_secret,
)
from agents.estimation_v4_1_material_facts_agent import (
    MAX_OUTPUT_TOKENS, TIMEOUT_SECONDS, _create_message_with_hard_timeout, _json_object,
)


ESTIMATION_COMPOSITION_ANALYZE_AGENT_VERSION = "estimation_analyze_v6_1"
COMPOSITION_SCOPE_V1 = "estimation_composition_scope_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_composition_analyze_prompt.md"


def _page_manifest(inputs: Sequence[Mapping[str, Any]], page_bytes_by_ref: Mapping[str, bytes]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return deduplicated document pages and object-owned regions.

    Estimation inputs intentionally retain full source pages.  The analyze
    pass receives every unique page once, plus the immutable object registry,
    so it can understand relationships without the Calculation call guessing
    from an isolated rectangle.
    """
    pages: dict[str, dict[str, Any]] = {}
    objects: list[dict[str, Any]] = []
    for row in inputs:
        payload = row.get("input_payload") or {}
        object_payload = payload.get("object") or {}
        input_id = str(row.get("input_id") or "")
        if not input_id:
            continue
        objects.append({
            "input_id": input_id,
            "object_id": str(object_payload.get("object_id") or ""),
            "object_name": str(object_payload.get("object_name") or ""),
            "quantity": object_payload.get("quantity"),
            "evidence_pages": list(object_payload.get("evidence_pages") or []),
        })
        artifacts = [artifact for container in ("evidence", "document_context") for artifact in (payload.get(container) or {}).get("artifacts") or []]
        for artifact in artifacts:
            if not isinstance(artifact, Mapping) or artifact.get("artifact_kind") != "page":
                continue
            storage_ref = str(artifact.get("storage_ref") or "")
            if not storage_ref:
                continue
            page_bytes = page_bytes_by_ref.get(storage_ref)
            if not page_bytes:
                raise ValueError(f"composition source page is missing: {storage_ref}")
            key = f"{artifact.get('page_number')}:{sha256(page_bytes).hexdigest()}"
            if key in pages:
                if storage_ref not in pages[key]["source_aliases"]:
                    pages[key]["source_aliases"].append(storage_ref)
                continue
            pages[key] = {
                "storage_ref": storage_ref,
                "source_aliases": [storage_ref],
                "page_number": artifact.get("page_number"),
                "bytes": page_bytes,
            }
    return list(pages.values()), objects


def _content(*, inputs: Sequence[Mapping[str, Any]], page_bytes_by_ref: Mapping[str, bytes], allowed_material_families: Sequence[str] = (), context_inputs: Sequence[Mapping[str, Any]] = ()) -> list[dict[str, Any]]:
    all_inputs = [*inputs, *context_inputs]
    pages, objects = _page_manifest(all_inputs, page_bytes_by_ref)
    requested = {str(row.get("input_id")) for row in inputs}
    content: list[dict[str, Any]] = []
    for page in pages:
        content.extend((
            {"type": "text", "text": json.dumps({"source_evidence_ref": page["storage_ref"], "source_aliases": page["source_aliases"], "page_number": page["page_number"]})},
            {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(page["bytes"]).decode("ascii")}},
        ))
    content.append({"type": "text", "text": json.dumps({
        "contract_version": COMPOSITION_SCOPE_V1,
        "objects": [obj for obj in objects if obj["input_id"] in requested],
        "accepted_context_objects": [{**obj, "construction_scope": next((row.get("accepted_construction_scope") for row in context_inputs if row.get("input_id") == obj["input_id"]), None)} for obj in objects if obj["input_id"] not in requested],
        "allowed_material_families": sorted(allowed_material_families),
        "source_text": list({str(item["block_ref"]): dict(item)
            for row in all_inputs for container in ("evidence", "document_context")
            for kind in ("ocr_blocks", "ocr_literal_items")
            for item in ((row.get("input_payload") or {}).get(container) or {}).get(kind) or []
            if isinstance(item, Mapping) and item.get("block_ref")}.values()),
    }, ensure_ascii=False, separators=(",", ":"))})
    return content


def _valid_scope(*, raw: Mapping[str, Any], input_ids: set[str]) -> dict[str, Any]:
    if str(raw.get("input_id") or "") not in input_ids:
        raise ValueError("composition scope input_id is unknown")
    zones = raw.get("zones")
    if not isinstance(zones, list) or not zones:
        raise ValueError("composition scope requires zones")
    return {
        "contract_version": COMPOSITION_SCOPE_V1,
        "status": "ready",
        "input_id": str(raw["input_id"]),
        "object_id": str(raw.get("object_id") or ""),
        "object_summary": str(raw.get("object_summary") or "").strip(),
        "zones": [dict(zone) for zone in zones if isinstance(zone, Mapping)],
        "assumptions": [str(item) for item in raw.get("assumptions") or [] if str(item).strip()],
    }


def run_estimation_composition_analyze_agent(*, inputs: Sequence[Mapping[str, Any]], page_bytes_by_ref: Mapping[str, bytes], allowed_material_families: Sequence[str] = (), context_inputs: Sequence[Mapping[str, Any]] = (), model: str | None = None) -> dict[str, Any]:
    if not inputs:
        return {"scopes_by_input": {}, "usage_event": {}}
    selected_model = model or get_secret("CLAUDE_ESTIMATION_ANALYZE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    client = get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0)
    started_at = datetime.now(UTC).isoformat()
    response = _create_message_with_hard_timeout(
        client, timeout_seconds=TIMEOUT_SECONDS, model=selected_model, max_tokens=min(24000, max(MAX_OUTPUT_TOKENS, len(inputs) * 2500)),
        temperature=0, system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{"role": "user", "content": _content(inputs=inputs, page_bytes_by_ref=page_bytes_by_ref, allowed_material_families=allowed_material_families, context_inputs=context_inputs)}],
    )
    parsed = _json_object(extract_text_from_claude_response(response))
    scopes = parsed.get("object_scopes")
    if not isinstance(scopes, list):
        raise ValueError("composition analyze response requires object_scopes")
    input_ids = {str(row.get("input_id") or "") for row in inputs}
    from use_cases.estimation_construction_plan import evidence_refs, normalize_palette, normalize_construction_scope
    allowed_refs = evidence_refs([*inputs, *context_inputs])
    palette = normalize_palette(parsed.get("material_palette"), allowed_refs=allowed_refs, families=allowed_material_families)
    scopes_by_input: dict[str, dict[str, Any]] = {}
    for raw in scopes:
        if not isinstance(raw, Mapping):
            continue
        scope = _valid_scope(raw=raw, input_ids=input_ids)
        owner = next(row for row in inputs if str(row.get("input_id")) == scope["input_id"])
        if scope["object_id"] != str(((owner.get("input_payload") or {}).get("object") or {}).get("object_id") or ""):
            raise ValueError("composition scope changed locked object identity")
        scope = normalize_construction_scope(scope, palette=palette, allowed_refs=allowed_refs)
        if scope["input_id"] in scopes_by_input:
            raise ValueError("composition analyze response has duplicate input_id")
        scopes_by_input[scope["input_id"]] = scope
    missing = sorted(input_ids - set(scopes_by_input))
    if missing:
        raise ValueError("composition analyze response omits an object scope")
    first_payload = inputs[0].get("input_payload") or {}
    usage = build_agent_usage_event(
        agent_name="estimation", operation="estimation_analyze", company_id=str(first_payload.get("company_id") or ""),
        run_id=str(first_payload.get("run_id") or ""), file_name=str((first_payload.get("document") or {}).get("file_name") or ""),
        object_id="", object_name="", model=selected_model,
        prompt_version=ESTIMATION_COMPOSITION_ANALYZE_AGENT_VERSION, response=response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"object_count": len(inputs), "context_object_count": len(context_inputs), "page_count": len(_page_manifest([*inputs, *context_inputs], page_bytes_by_ref)[0]), "whole_file": True},
    )
    return {"scopes_by_input": scopes_by_input, "usage_event": usage}
