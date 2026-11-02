"""Persist Object-to-Estimate geometry and deterministic BOM results."""

from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any, Mapping, Sequence

from agents.estimation_assembly_bom_agent import (
    ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION as STRUCTURAL_BOM_AGENT_VERSION,
    run_estimation_assembly_bom_agent,
)
from agents.estimation_object_to_estimate_agent import (
    ESTIMATION_OBJECT_TO_ESTIMATE_AGENT_VERSION,
    run_estimation_object_to_estimate_agent,
)
from db.repositories import (
    fetch_estimation_fact_result, insert_agent_usage_event, insert_agent_usage_event_returning_id,
    insert_estimation_fact_result, insert_estimation_failure_trace,
)
from use_cases.estimation_approximate_bom import APPROXIMATE_BOM_V1, compose_approximate_bom_v1
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.estimation_structural_bom import build_structural_assembly_bom
from use_cases.estimation_dimension_graph import DIMENSION_GRAPH_V1, build_dimension_graph
from use_cases.estimation_dimension_scale import build_dimension_scale_gate
from use_cases.estimation_object_to_estimate import build_object_to_estimate_brief


ESTIMATION_APPROXIMATE_BOM_AGENT_VERSION = "estimation_approximate_bom_v1"
ESTIMATION_DIMENSION_GRAPH_AGENT_VERSION = DIMENSION_GRAPH_V1
ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION = STRUCTURAL_BOM_AGENT_VERSION
ESTIMATION_ACTIVE_BOM_AGENT_VERSION = ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION


_SAFE_FAILURE_PREFIXES = (
    "assembly BOM response ", "assembly reconciliation ", "structural BOM ",
    "document_unit", "material role ", "no material families are available",
    "persisted object-to-estimate brief ", "Estimation Object Facts ",
)


def _structural_failure_code(message: str) -> str | None:
    """Return a bounded diagnostic code, never a model response fragment."""
    normalized = " ".join(message.split())
    patterns = (
        (r"^structural BOM has no material demand$", "no_material_demand"),
        (r"^assembly requires unique id and supported structural role$", "invalid_assembly_identity_or_role"),
        (r"^[^ ]+\.dimensions must be an object$", "assembly_dimensions_not_an_object"),
        (r"^[^ ]+ lacks dimensions required by [a-z_]+$", "assembly_missing_required_dimensions"),
        (r"^[^ ]+\.counts must be an object$", "assembly_counts_not_an_object"),
        (r"^secondary item requires a unique id$", "invalid_secondary_item_identity"),
        (r"^secondary item role is unsupported$", "unsupported_secondary_item_role"),
        (r"^secondary item requires material$", "secondary_item_missing_material"),
        (r"^document_unit.*$", "invalid_document_unit"),
        (r"^material role .*$", "invalid_material_role"),
        (r"^[^ ]+\.dimensions\.[^. ]+.*$", "invalid_assembly_dimension"),
        (r"^[^ ]+\.counts\.[^. ]+.*$", "invalid_assembly_count"),
        (r"^secondary_items\.[^. ]+\.quantity.*$", "invalid_secondary_item_quantity"),
        (r"^.* must contain immutable evidence references$", "invalid_evidence_references"),
    )
    return next((code for pattern, code in patterns if re.match(pattern, normalized)), None)


def _safe_failure_message(exc: Exception) -> str:
    """Keep the diagnostic actionable without storing provider output or secrets."""
    message = " ".join(str(exc).split())
    if code := _structural_failure_code(message):
        return code
    if message.startswith(_SAFE_FAILURE_PREFIXES):
        return message[:400]
    return "Unexpected technical failure. Raw provider responses and exception details are not retained."


def _record_failure_trace(
    *, client: Any, input_id: str, stage: str, exc: Exception,
) -> None:
    """Tracing must never mask the original technical failure."""
    try:
        structural_validation = stage == "structural_composition" and isinstance(exc, ValueError)
        safe_message = (
            _structural_failure_code(str(exc)) or "structural_validation_failed"
            if structural_validation else _safe_failure_message(exc)
        )
        insert_estimation_failure_trace(
            client, input_id=input_id, agent_version=ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
            stage=stage,
            error_type=("StructuralValidationError" if structural_validation else type(exc).__name__),
            error_message=safe_message,
        )
    except Exception:
        pass


def _record_stage_event(
    *, client: Any, input_row: Mapping[str, Any], stage: str, status: str,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Persist a bounded marker for every completed or failed V4 stage.

    This is an operational trace, not model output. It contains identifiers,
    counts and normalized reason codes only, so a failure remains diagnosable
    without retaining prompt, response, chain-of-thought or credentials.
    """
    try:
        payload = input_row.get("input_payload") or {}
        object_payload = payload.get("object") or {}
        now = datetime.now(UTC).isoformat()
        insert_agent_usage_event(client, {
            "company_id": str(payload.get("company_id") or ""),
            "run_id": str(payload.get("run_id") or ""),
            "file_name": str((payload.get("document") or {}).get("file_name") or ""),
            "object_id": str(object_payload.get("object_id") or ""),
            "object_name": str(object_payload.get("object_name") or ""),
            "agent_name": "estimation", "operation": "estimation_stage",
            "model": "deterministic", "prompt_version": ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
            "input_tokens": 0, "output_tokens": 0,
            "input_cost_usd": None, "output_cost_usd": None, "total_cost_usd": None,
            "status": status, "started_at": now, "finished_at": now,
            "error_message": (str((details or {}).get("reason_code") or "")[:400] or None),
            "raw_usage": {
                "estimation_stage": stage,
                "input_id": str(input_row.get("input_id") or ""),
                **{str(key): value for key, value in (details or {}).items()
                   if key in {"reason_code", "page_count", "assembly_count", "part_count", "material_count", "normalization_count", "fact_result_id"}},
            },
        })
    except Exception:
        # Observability must never change the outcome of an estimate.
        pass


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
        stage = "dimension_graph"
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
            _record_stage_event(
                client=client, input_row=row, stage="dimension_graph", status="succeeded",
                details={"reason_code": "reused" if graph_existing else "built",
                         "page_count": len(graph.get("views") or ()), "normalization_count": 0},
            )
            dimension_scale_gate = build_dimension_scale_gate(dimension_graph=graph)
            payload = row.get("input_payload") or {}
            stage = "evidence_artifact"
            page_bytes = {}
            for artifact in ((payload.get("evidence") or {}).get("artifacts") or []):
                if not isinstance(artifact, Mapping) or artifact.get("artifact_kind") != "page":
                    continue
                storage_ref = str(artifact.get("storage_ref") or "")
                if storage_ref:
                    page_bytes[storage_ref] = download_evidence_artifact(client=client, storage_ref=storage_ref)
            _record_stage_event(
                client=client, input_row=row, stage="evidence_artifacts", status="succeeded",
                details={"reason_code": "loaded", "page_count": len(page_bytes)},
            )
            stage = "assembly_agent"
            result = run_estimation_assembly_bom_agent(
                input_row=row, evidence_page_bytes_by_ref=page_bytes, dimension_graph=graph,
                dimension_scale_gate=dimension_scale_gate,
                allowed_material_families=allowed_material_families,
            )
            usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
            _record_stage_event(
                client=client, input_row=row, stage="assembly_agent", status="succeeded",
                details={"reason_code": "response_validated"},
            )
            stage = "structural_composition"
            bom = build_structural_assembly_bom(
                input_row=row, dimension_graph=graph, extraction=result["extraction"],
                dimension_scale_gate=dimension_scale_gate,
                allowed_material_families=allowed_material_families,
            )
            _record_stage_event(
                client=client, input_row=row, stage="structural_composition", status="succeeded",
                details={
                    "reason_code": "bom_ready", "assembly_count": len(bom.get("assemblies") or ()),
                    "part_count": len(bom.get("parts") or ()), "material_count": len(bom.get("materials") or ()),
                    "normalization_count": len(bom.get("normalizations") or ()),
                },
            )
            stage = "bom_persistence"
            fact_result_id = insert_estimation_fact_result(
                client, input_id=input_id, agent_version=ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
                facts_payload=bom, agent_usage_event_id=usage_id,
            )
            created.append(fact_result_id)
            _record_stage_event(
                client=client, input_row=row, stage="bom_persistence", status="succeeded",
                details={"reason_code": "persisted", "fact_result_id": fact_result_id},
            )
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
            _record_failure_trace(client=client, input_id=input_id, stage=stage, exc=exc)
            _record_stage_event(
                client=client, input_row=row, stage=stage, status="failed",
                details={"reason_code": _safe_failure_message(exc)},
            )
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
