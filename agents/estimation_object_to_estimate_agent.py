"""Bounded visual extraction of cited geometry for Object-to-Estimate V1."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_AGENT_MODEL, build_agent_usage_event, create_claude_message,
    extract_text_from_claude_response, get_anthropic_client, get_secret,
)
from agents.estimation_v4_1_material_facts_agent import (
    MAX_OUTPUT_TOKENS, TIMEOUT_SECONDS, _create_message_with_hard_timeout,
    _json_object, build_v4_1_evidence_batches,
)


ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION = "estimation_object_to_estimate_v1"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_object_to_estimate_prompt.md"


def _batch_content(*, batch: Mapping[str, Any], allowed_material_families: Sequence[str]) -> list[dict[str, Any]]:
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
    content.append({"type": "text", "text": json.dumps({
        "batch_id": batch["batch_id"], "pages": pages,
        "allowed_material_families": sorted(allowed_material_families),
    }, ensure_ascii=False, separators=(",", ":"))})
    return content


def _validate_batch_response(*, response: Mapping[str, Any], batch: Mapping[str, Any]) -> dict[str, Any]:
    if response.get("batch_id") != batch["batch_id"]:
        raise ValueError("object-to-estimate response batch_id does not match request")
    expected = {int(page["page_number"]) for page in batch["pages"]}
    pages = response.get("pages")
    actual = [int(page.get("page_number")) for page in pages or [] if isinstance(page, Mapping) and str(page.get("page_number") or "").isdigit()]
    if not isinstance(pages, list) or set(actual) != expected or len(actual) != len(pages):
        raise ValueError("object-to-estimate response page coverage is incomplete or duplicated")
    return {
        "object_kind": response.get("object_kind"),
        "dimensions": list(response.get("dimensions") or []),
        "counts": list(response.get("counts") or []),
        "material_roles": list(response.get("material_roles") or []),
    }


def run_estimation_object_to_estimate_agent(
    *, input_row: Mapping[str, Any], evidence_page_bytes_by_ref: Mapping[str, bytes],
    allowed_material_families: Sequence[str], model: str | None = None,
) -> dict[str, Any]:
    """Return source claims from every evidence page exactly once."""
    payload = input_row.get("input_payload") or {}
    batches = build_v4_1_evidence_batches(payload)
    selected_model = model or get_secret("CLAUDE_ESTIMATION_OBJECT_TO_ESTIMATE_MODEL", DEFAULT_CLAUDE_AGENT_MODEL)
    client = get_anthropic_client().with_options(timeout=TIMEOUT_SECONDS, max_retries=0)
    responses, claims, diagnostics = [], {"dimensions": [], "counts": [], "material_roles": []}, []
    object_kinds: list[str] = []
    started_at = datetime.now(UTC).isoformat()
    for batch in batches:
        pages = []
        for page in batch["pages"]:
            page_bytes = evidence_page_bytes_by_ref.get(page["storage_ref"])
            if not page_bytes:
                raise ValueError(f"object-to-estimate full source evidence is missing for {page['storage_ref']}")
            pages.append({**page, "bytes": page_bytes})
        resolved_batch = {**batch, "pages": pages}
        response = _create_message_with_hard_timeout(
            client, timeout_seconds=TIMEOUT_SECONDS, model=selected_model, max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0, system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
            messages=[{"role": "user", "content": _batch_content(batch=resolved_batch, allowed_material_families=allowed_material_families)}],
        )
        responses.append(response)
        parsed = _validate_batch_response(
            response=_json_object(extract_text_from_claude_response(response)), batch=batch,
        )
        if parsed["object_kind"] in {"wardrobe", "cabinet"}:
            object_kinds.append(parsed["object_kind"])
        for key in claims:
            claims[key].extend(item for item in parsed[key] if isinstance(item, Mapping))
        diagnostics.append({"batch_id": batch["batch_id"], "page_numbers": [page["page_number"] for page in batch["pages"]]})
    kind = max(set(object_kinds), key=lambda value: (object_kinds.count(value), value)) if object_kinds else "unknown"
    input_tokens = sum(int(getattr(getattr(response, "usage", None), "input_tokens", 0) or 0) for response in responses)
    output_tokens = sum(int(getattr(getattr(response, "usage", None), "output_tokens", 0) or 0) for response in responses)
    usage_response = type("UsageResponse", (), {"usage": type("Usage", (), {
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
    })()})()
    usage_event = build_agent_usage_event(
        agent_name="estimation_object_to_estimate", operation="bounded_geometry_extraction",
        company_id=str(payload.get("company_id") or ""), run_id=str(payload.get("run_id") or ""),
        file_name=str((payload.get("document") or {}).get("file_name") or ""),
        object_id=str((payload.get("object") or {}).get("object_id") or ""),
        object_name=str((payload.get("object") or {}).get("object_name") or ""), model=selected_model,
        prompt_version=ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION, response=usage_response,
        started_at=started_at, finished_at=datetime.now(UTC).isoformat(),
        request_diagnostics={"batch_count": len(responses), "batches": diagnostics, "geometry_only": True},
    )
    return {"extraction": {"object_kind": kind, **claims}, "usage_event": usage_event}
