"""Persist one compact page extraction as independently publishable object facts."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any, Callable, Mapping, Sequence
from agents.estimation_v2_page_facts_agent import ESTIMATION_V2_FACTS_AGENT_VERSION, run_estimation_v2_page_facts_agent
from db.repositories import fetch_active_israel_material_families, fetch_estimation_v2_fact_result, insert_agent_usage_event_returning_id, insert_estimation_v2_fact_result
from use_cases.estimation_artifacts import download_evidence_artifact


def run_estimation_v2_facts_batch(*, client: Any, inputs: Sequence[Mapping[str, Any]], on_object_start: Callable[[Mapping[str, Any]], None] | None = None) -> dict[str, Any]:
    families = fetch_active_israel_material_families(client)
    if not families:
        return {"created_result_ids": [], "reused_input_ids": [], "failed": {str(row.get("input_id") or "unknown"): "active_israel_material_family_catalog_empty" for row in inputs}}
    created: list[str] = []
    reused: list[str] = []
    failed: dict[str, str] = {}
    pending: list[Mapping[str, Any]] = []
    for row in inputs:
        if on_object_start:
            on_object_start(row)
        input_id = str(row.get("input_id") or "").strip()
        payload = row.get("input_payload")
        if not input_id or not isinstance(payload, Mapping):
            failed[input_id or "unknown"] = "invalid_estimation_input"
            continue
        existing = fetch_estimation_v2_fact_result(client, input_id=input_id, agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION)
        if existing:
            reused.append(input_id)
        else:
            pending.append(row)
    if not pending:
        return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}
    first_payload = pending[0]["input_payload"]
    try:
        result = run_estimation_v2_page_facts_agent(
            inputs=pending, allowed_material_families=families,
            preview_bytes=download_evidence_artifact(client=client, storage_ref=str((first_payload.get("evidence") or {}).get("primary_preview_ref") or "")),
        )
        usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
        failed.update(result["failed"])
        for row in pending:
            input_id = str(row["input_id"])
            facts = result["facts_by_input"].get(input_id)
            if facts is None:
                failed.setdefault(input_id, "compact_page_result_missing_object")
                continue
            created.append(insert_estimation_v2_fact_result(client, input_id=input_id, agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION, facts_payload=facts, agent_usage_event_id=usage_id))
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        for row in pending:
            input_id = str(row.get("input_id") or "")
            payload = row.get("input_payload") or {}
            failed[input_id] = error_message
            try:
                now = datetime.now(UTC).isoformat()
                insert_agent_usage_event_returning_id(client, {
                    "company_id": str(payload.get("company_id") or ""), "run_id": str(payload.get("run_id") or ""),
                    "file_name": str((payload.get("document") or {}).get("file_name") or ""),
                    "object_id": str((payload.get("object") or {}).get("object_id") or ""), "object_name": str((payload.get("object") or {}).get("object_name") or ""),
                    "agent_name": "estimation_v2_facts", "operation": "page_fact_extraction", "model": "unrecorded_before_valid_result",
                    "prompt_version": ESTIMATION_V2_FACTS_AGENT_VERSION, "input_tokens": 0, "output_tokens": 0,
                    "input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None, "currency": "USD",
                    "status": "failed", "error_message": error_message[:1000], "started_at": now, "finished_at": now,
                    "raw_usage": {"input_id": input_id, "error_type": type(exc).__name__},
                })
            except Exception:
                pass
    return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}
