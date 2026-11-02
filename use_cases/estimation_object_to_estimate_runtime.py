"""Persist Object-to-Estimate geometry and deterministic BOM results."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from agents.estimation_assembly_bom_agent import (
    ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
    run_estimation_assembly_bom_agent,
)
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
from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1, build_assembly_bom
from use_cases.estimation_dimension_graph import DIMENSION_GRAPH_V1, build_dimension_graph
from use_cases.estimation_object_to_estimate import build_object_to_estimate_brief


ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION = "estimation_approximate_bom_v1"
ESTIMATION_DIMENSION_GRAPH_AGENT_VERSION = DIMENSION_GRAPH_V1
ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION = ASSEMBLY_BOM_V1
ESTIMATION_ACTIVE_BOM_AGENT_VERSION = ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION


def _dimension_graph_usage(*, payload: Mapping[str, Any], graph: Mapping[str, Any]) -> dict[str, Any]:
    """Persist deterministic graph provenance beside the LLM provenance."""
    object_payload = payload.get("object") or {}
    return {
        "company_id": str(payload.get("company_id") or ""), "run_id": str(payload.get("run_id") or ""),
        "file_name": str((payload.get("document") or {}).get("file_name") or ""),
        "object_id": str(object_payload.get("object_id") or ""),
        "object_name": str(object_payload.get("object_name") or ""),
        "agent_name": "estimation", "operation": "dimension_graph", "model": "deterministic",
        "prompt_version": ESTIMATION_DIMENSION_GRAPH_AGENT_VERSION,
        "input_tokens": 0, "output_tokens": 0,
        "input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None,
        "status": "succeeded", "duration_seconds": 0.0,
        "started_at": datetime.now(UTC).isoformat(), "finished_at": datetime.now(UTC).isoformat(),
        "raw_usage": {
            "dimension_count": len(graph.get("dimension_numbers") or ()),
            "view_count": len(graph.get("views") or ()),
            "relation_count": len(graph.get("relations") or ()),
            "dimension_graph": True,
        },
    }


def run_assembly_first_bom_batch(
    *, client: Any, inputs: Sequence[Mapping[str, Any]], allowed_material_families: Sequence[str],
) -> dict[str, Any]:
    """Create the V4.12 graph and assembly-first BOM for immutable inputs.

    Unlike the V4.11 path below, this function has no product-kind recipe.
    Every visual request is bounded by source-page batches, then reconciled by
    cited observations when an object spans more than one batch.
    """
    created, reused, failed = [], [], {}
    for row in inputs:
        input_id = str(row.get("input_id") or "")
        if not input_id:
            failed["unknown"] = "invalid_estimation_input"
            continue
        existing = fetch_estimation_fact_result(
            client, input_id=input_id, agent_version=ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
        )
        if existing:
            reused.append(input_id)
            continue
        try:
            graph_existing = fetch_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_DIMENSION_GRAPH_AGENT_VERSION,
            )
            if graph_existing:
                graph = dict(graph_existing.get("facts_payload") or {})
            else:
                graph = build_dimension_graph(input_row=row)
                graph_usage_id = insert_agent_usage_event_returning_id(
                    client, _dimension_graph_usage(payload=dict(row.get("input_payload") or {}), graph=graph),
                )
                created.append(insert_estimation_fact_result(
                    client, input_id=input_id, agent_version=ESTIMATION_DIMENSION_GRAPH_AGENT_VERSION,
                    facts_payload=graph, agent_usage_event_id=graph_usage_id,
                ))
            payload = row.get("input_payload") or {}
            page_bytes = {}
            for artifact in ((payload.get("evidence") or {}).get("artifacts") or []):
                if not isinstance(artifact, Mapping) or artifact.get("artifact_kind") != "page":
                    continue
                storage_ref = str(artifact.get("storage_ref") or "")
                if storage_ref:
                    page_bytes[storage_ref] = download_evidence_artifact(client=client, storage_ref=storage_ref)
            result = run_estimation_assembly_bom_agent(
                input_row=row, evidence_page_bytes_by_ref=page_bytes, dimension_graph=graph,
                allowed_material_families=allowed_material_families,
            )
            bom = build_assembly_bom(
                input_row=row, dimension_graph=graph, extraction=result["extraction"],
                allowed_material_families=allowed_material_families,
            )
            usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
            created.append(insert_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
                facts_payload=bom, agent_usage_event_id=usage_id,
            ))
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    return {"created_result_ids": created, "reused_input_ids": reused, "failed": failed}


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
