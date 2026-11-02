"""Persist Object-to-Estimate geometry and deterministic BOM results."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from agents.estimation_object_to_estimate_agent import (
    ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION,
    run_estimation_object_to_estimate_agent,
)
from db.repositories import (
    fetch_estimation_fact_result, insert_agent_usage_event_returning_id,
    insert_estimation_fact_result,
)
from use_cases.estimation_approximate_bom import APPROXIMATE_BOM_V1, compose_approximate_bom_v1
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.estimation_object_to_estimate import build_object_to_estimate_brief


ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION = "estimation_approximate_bom_v1"


def run_object_to_estimate_bom_batch(
    *, client: Any, inputs: Sequence[Mapping[str, Any]], allowed_material_families: Sequence[str],
) -> dict[str, Any]:
    """Create or reuse one evidence brief and one BOM for each immutable input."""
    created, reused, failed = [], [], {}
    for row in inputs:
        input_id = str(row.get("input_id") or "")
        if not input_id:
            failed["unknown"] = "invalid_estimation_input"
            continue
        bom_existing = fetch_estimation_fact_result(
            client, input_id=input_id, agent_version=ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION,
        )
        if bom_existing:
            reused.append(input_id)
            continue
        try:
            brief_existing = fetch_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION,
            )
            if brief_existing:
                brief = dict(brief_existing.get("facts_payload") or {})
                usage_id = str(brief_existing.get("agent_usage_event_id") or "")
                if not usage_id:
                    raise RuntimeError("persisted object-to-estimate brief has no usage event")
            else:
                payload = row.get("input_payload") or {}
                page_bytes = {}
                for artifact in ((payload.get("evidence") or {}).get("artifacts") or []):
                    if not isinstance(artifact, Mapping) or artifact.get("artifact_kind") != "page":
                        continue
                    storage_ref = str(artifact.get("storage_ref") or "")
                    if storage_ref:
                        page_bytes[storage_ref] = download_evidence_artifact(client=client, storage_ref=storage_ref)
                result = run_estimation_object_to_estimate_agent(
                    input_row=row, evidence_page_bytes_by_ref=page_bytes,
                    allowed_material_families=allowed_material_families,
                )
                brief = build_object_to_estimate_brief(input_row=row, extraction=result["extraction"])
                usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
                created.append(insert_estimation_fact_result(
                    client, input_id=input_id, agent_version=ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION,
                    facts_payload=brief, agent_usage_event_id=usage_id,
                ))
            bom = compose_approximate_bom_v1(brief)
            created.append(insert_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION,
                facts_payload=bom, agent_usage_event_id=usage_id,
            ))
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}
