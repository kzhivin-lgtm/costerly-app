"""Assembly-first visual BOM extraction, bounded to immutable evidence."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL, build_agent_usage_event, extract_text_from_claude_response,
    get_anthropic_client, get_secret,
)
from agents.estimation_v4_1_material_facts_agent import (
    MAX_OUTPUT_TOKENS, TIMEOUT_SECONDS, _create_message_with_hard_timeout, _json_object,
    build_v4_1_evidence_batches,
)


ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION = "estimation_assembly_bom_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_assembly_bom_prompt.md"
RECONCILIATION_PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_assembly_bom_reconciliation_prompt.md"


def _content(*, batch: Mapping[str, Any], payload: Mapping[str, Any], dimension_graph: Mapping[str, Any], allowed_material_families: Sequence[str]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    pages = []
    for page in batch["pages"]:
        content.extend((
            {"type": "text", "text": json.dumps({"source_evidence_ref": page["storage_ref"], "page_number": page["page_number"]})},
            {"type": "image", "source": {"type": "base64", "media_type": "image/webp", "data": base64.b64encode(page["bytes"]).decode("ascii")}},
        ))
        pages.append({
            "page_number": page["page_number"], "source_evidence_ref": page["storage_ref"],
            "regions": page["regions"], "ocr_blocks": page["ocr_blocks"],
            "ocr_literal_items": page["ocr_literal_items"],
        })
    object_payload = payload.get("object") or {}
    content.append({"type": "text", "text": json.dumps({
        "batch_id": batch["batch_id"], "object": {
            "object_id": object_payload.get("object_id"), "object_name": object_payload.get("object_name"),
            "quantity": object_payload.get("quantity"),
        },
        "pages": pages, "dimension_graph": dimension_graph,
        "allowed_material_families": sorted(allowed_material_families),
    }, ensure_ascii=False, separators=(",", ":"))})
    return content


def _validate_response(*, response: Mapping[str, Any], batch: Mapping[str, Any]) -> dict[str, Any]:
    if response.get("batch_id") != batch["batch_id"]:
        raise ValueError("assembly BOM response batch_id does not match request")
    expected = {int(page["page_number"]) for page in batch["pages"]}
    pages = response.get("pages")
    actual = [int(page.get("page_number")) for page in pages or [] if isinstance(page, Mapping) and str(page.get("page_number") or "").isdigit()]
    if not isinstance(pages, list) or set(actual) != expected or len(actual) != len(pages):
        raise ValueError("assembly BOM response page coverage is incomplete or duplicated")
    assemblies = response.get("assemblies")
    if not isinstance(assemblies, list):
        raise ValueError("assembly BOM response requires assemblies")
    return {"assemblies": [dict(item) for item in assemblies if isinstance(item, Mapping)], "omissions": [str(item) for item in response.get("omissions") or [] if str(item).strip()]}


def _reconciliation_content(
    *, payload: Mapping[str, Any], dimension_graph: Mapping[str, Any], batch_extractions: Sequence[Mapping[str, Any]],
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
        "dimension_graph": dimension_graph,
        "batch_observations": list(batch_extractions),
        "allowed_material_families": sorted(allowed_material_families),
    }, ensure_ascii=False, separators=(",", ":"))}]


def _validate_reconciliation(*, response: Mapping[str, Any]) -> dict[str, Any]:
    assemblies = response.get("assemblies")
    if not isinstance(assemblies, list):
        raise ValueError("assembly reconciliation requires assemblies")
    return {
        "assemblies": [dict(item) for item in assemblies if isinstance(item, Mapping)],
        "omissions": [str(item) for item in response.get("omissions") or [] if str(item).strip()],
    }


def run_estimation_assembly_bom_agent(*, input_row: Mapping[str, Any], evidence_page_bytes_by_ref: Mapping[str, bytes], dimension_graph: Mapping[str, Any], allowed_material_families: Sequence[str], model: str | None = None) -> dict[str, Any]:
    payload = input_row.get("input_payload") or {}
    batches = build_v4_1_evidence_batches(payload)
    selected_model = model or get_secret("CLAUDE_ESTIMATION_ASSEMBLY_BOM_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    client = get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0)
    started_at = datetime.now(UTC).isoformat()
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
            temperature=0, system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
            messages=[{"role": "user", "content": _content(batch=resolved_batch, payload=payload, dimension_graph=dimension_graph, allowed_material_families=allowed_material_families)}],
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
        parsed = {"assemblies": observations[0]["assemblies"], "omissions": observations[0]["omissions"]}
    else:
        response = _create_message_with_hard_timeout(
            client, timeout_seconds=TIMEOUT_SECONDS, model=selected_model, max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0, system=RECONCILIATION_PROMPT_PATH.read_text(encoding="utf-8").strip(),
            messages=[{"role": "user", "content": _reconciliation_content(
                payload=payload, dimension_graph=dimension_graph, batch_extractions=observations,
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
        request_diagnostics={"batch_count": len(batches), "batches": diagnostics, "assembly_first": True},
    )
    return {"extraction": parsed, "usage_event": usage}
