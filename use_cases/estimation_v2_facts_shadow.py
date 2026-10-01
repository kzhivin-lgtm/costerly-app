"""Fail-isolated Estimation v2 Object Facts coordinator."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from agents.estimation_v2_facts_agent import (
    ESTIMATION_V2_FACTS_AGENT_VERSION,
    run_estimation_v2_facts_agent,
)
from db.repositories import (
    fetch_active_israel_material_families,
    fetch_estimation_v2_fact_result,
    insert_agent_usage_event_returning_id,
    insert_estimation_v2_fact_result,
)
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.machinery import build_company_production_context


def run_estimation_v2_facts_batch(
    *,
    client: Any,
    inputs: Sequence[Mapping[str, Any]],
    on_object_start: Callable[[Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Extract and persist facts without affecting the active estimate workflow."""
    families = fetch_active_israel_material_families(client)
    if not families:
        return {
            "created_result_ids": [],
            "reused_input_ids": [],
            "failed": {
                str(row.get("input_id") or "unknown"): "active_israel_material_family_catalog_empty"
                for row in inputs
            },
        }

    created: list[str] = []
    reused: list[str] = []
    failed: dict[str, str] = {}
    production_context_by_company: dict[str, dict[str, Any]] = {}
    for row in inputs:
        if on_object_start is not None:
            on_object_start(row)
        input_id = str(row.get("input_id") or "").strip()
        payload = row.get("input_payload")
        revision = row.get("object_input_revision", 1)
        if not input_id or not isinstance(payload, Mapping):
            failed[input_id or "unknown"] = "invalid_estimation_input"
            continue
        try:
            existing = fetch_estimation_v2_fact_result(
                client,
                input_id=input_id,
                agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION,
            )
            if existing:
                reused.append(input_id)
                continue
            company_id = str(payload.get("company_id") or "")
            if company_id not in production_context_by_company:
                production_context_by_company[company_id] = (
                    build_company_production_context(company_id, client=client)
                    if company_id else {}
                )
            result = run_estimation_v2_facts_agent(
                input_id=input_id,
                object_input_revision=int(revision),
                estimation_input=payload,
                allowed_material_families=families,
                preview_bytes=download_evidence_artifact(
                    client=client,
                    storage_ref=str((payload.get("evidence") or {}).get("primary_preview_ref") or ""),
                ),
                production_context=production_context_by_company[company_id],
            )
            usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
            created.append(insert_estimation_v2_fact_result(
                client,
                input_id=input_id,
                agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION,
                facts_payload=result["facts"],
                agent_usage_event_id=usage_id,
            ))
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    return {
        "created_result_ids": created,
        "reused_input_ids": reused,
        "failed": failed,
    }
