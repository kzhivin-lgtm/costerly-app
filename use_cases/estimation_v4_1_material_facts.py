"""Persist bounded Estimation V4.2 material facts for immutable V4 inputs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable, Mapping, Sequence

from agents.estimation_v4_1_material_facts_agent import (
    ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION,
    run_estimation_v4_1_material_facts_agent,
)
from db.repositories import (
    fetch_estimation_fact_result,
    fetch_estimation_object_input,
    fetch_estimation_resolver_material_families,
    insert_agent_usage_event_returning_id,
    insert_estimation_fact_result,
)
from use_cases.catalog_aliases import (
    canonicalize_estimation_pricing_key_values,
    load_estimation_alias_context,
)
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.estimation_v3_material_facts import _pricing_key_fields_by_resolver_family
from use_cases.estimation_material_context import build_estimation_material_context


def replay_estimation_v4_1_material_facts_input(
    *, client: Any, input_id: str,
) -> dict[str, Any]:
    """Run V4.1 over an already immutable package, without OCR or re-upload."""
    row = fetch_estimation_object_input(client, input_id=input_id)
    if row is None:
        raise ValueError("estimation input was not found")
    payload = row.get("input_payload")
    if not isinstance(payload, Mapping) or payload.get("contract_version") != "estimation_input_v4":
        raise ValueError("replay requires an immutable estimation_input_v4 package")
    company_id = str(payload.get("company_id") or "")
    if not company_id:
        raise ValueError("replay input has no company_id")
    return run_estimation_v4_1_material_facts_batch(
        client=client, inputs=[row], material_context=build_estimation_material_context(client, company_id),
    )


def run_estimation_v4_1_material_facts_batch(
    *, client: Any, inputs: Sequence[Mapping[str, Any]],
    on_object_start: Callable[[Mapping[str, Any]], None] | None = None,
    material_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    families = set((material_context or {}).get("families") or fetch_estimation_resolver_material_families(client))
    if not families:
        return {"created_result_ids": [], "reused_input_ids": [], "failed": {
            str(row.get("input_id") or "unknown"): "active_resolver_family_catalog_empty" for row in inputs
        }}
    created: list[str] = []
    reused: list[str] = []
    failed: dict[str, str] = {}
    pending: list[Mapping[str, Any]] = []
    for row in inputs:
        if on_object_start:
            on_object_start(row)
        input_id = str(row.get("input_id") or "").strip()
        if not input_id or not isinstance(row.get("input_payload"), Mapping):
            failed[input_id or "unknown"] = "invalid_estimation_input"
            continue
        if fetch_estimation_fact_result(
            client, input_id=input_id, agent_version=ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION,
        ):
            reused.append(input_id)
        else:
            pending.append(row)
    if not pending:
        return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}
    try:
        evidence_page_bytes_by_ref: dict[str, bytes] = {}
        for row in pending:
            for artifact in ((row["input_payload"].get("evidence") or {}).get("artifacts") or []):
                if not isinstance(artifact, Mapping) or artifact.get("artifact_kind") != "page":
                    continue
                storage_ref = str(artifact.get("storage_ref") or "")
                if storage_ref and storage_ref not in evidence_page_bytes_by_ref:
                    evidence_page_bytes_by_ref[storage_ref] = download_evidence_artifact(client=client, storage_ref=storage_ref)
        pricing_key_fields_by_family = _pricing_key_fields_by_resolver_family(
            families=families,
            material_families=tuple(((material_context or {}).get("catalogs") or {}).get("material_families") or ()),
            material_pricing_policies=tuple(((material_context or {}).get("catalogs") or {}).get("material_pricing_policies") or ()),
        )
        family_alias_context = load_estimation_alias_context(
            client, family_codes=families, pricing_key_fields_by_family=pricing_key_fields_by_family,
        )
        result = run_estimation_v4_1_material_facts_agent(
            inputs=pending, allowed_material_families=families,
            evidence_page_bytes_by_ref=evidence_page_bytes_by_ref,
            pricing_key_fields_by_family=pricing_key_fields_by_family,
            family_alias_context=family_alias_context,
        )
        usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
        failed.update(result["failed"])
        for row in pending:
            input_id = str(row["input_id"])
            facts = result["facts_by_input"].get(input_id)
            if facts is None:
                failed.setdefault(input_id, "material_fact_result_missing_object")
                continue
            facts = canonicalize_estimation_pricing_key_values(facts, family_alias_context=family_alias_context)
            created.append(insert_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION,
                facts_payload=facts, agent_usage_event_id=usage_id,
            ))
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
                    "object_id": str((payload.get("object") or {}).get("object_id") or ""),
                    "object_name": str((payload.get("object") or {}).get("object_name") or ""),
                    "agent_name": "estimation_v4_2_material_facts", "operation": "bounded_material_fact_extraction",
                    "model": "unrecorded_before_valid_result", "prompt_version": ESTIMATION_V4_2_MATERIAL_FACTS_AGENT_VERSION,
                    "input_tokens": 0, "output_tokens": 0, "input_cost_usd": None, "output_cost_usd": None,
                    "total_cost_usd": None, "currency": "USD", "status": "failed", "error_message": error_message[:1000],
                    "started_at": now, "finished_at": now, "raw_usage": {"input_id": input_id, "error_type": type(exc).__name__},
                })
            except Exception:
                pass
    return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}
