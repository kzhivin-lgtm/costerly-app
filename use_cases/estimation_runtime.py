from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import RLock
from typing import Mapping

from use_cases.estimation import start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits
from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from db.repositories import (
    fetch_latest_estimation_facts_by_object,
    fetch_latest_ocr_result,
    fetch_rfq_estimate_material_norm_overrides,
    fetch_rfq_object_estimates,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    upsert_rfq_estimate_material_plan,
)
from db.supabase_client import get_supabase_client
from use_cases.estimation_handoff import persist_estimation_inputs
from use_cases.estimation_originals import describe_estimation_original
from use_cases.estimation_v3_material_facts import run_estimation_v3_material_facts_batch
from agents.estimation_v3_material_facts_agent import ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION
from use_cases.material_engine_adapter import (
    material_plan_input_fingerprint,
    material_plan_snapshot,
    build_material_plan,
)
from use_cases.estimation_material_context import build_estimation_material_context
from use_cases.estimation_v3_material_publisher import publish_estimation_v3_material_object
from db.repositories import update_rfq_object_estimate_progress
from use_cases.estimation_progress import set_object_progress


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_MATERIAL_PLAN_LOCK = RLock()
_MATERIAL_PLAN_FUTURES: dict[str, Future] = {}
_MATERIAL_PLAN_PENDING_REQUESTS: dict[str, tuple[str, str]] = {}


def _material_norm_overrides_by_requirement(rows: object) -> dict[tuple[str, str], dict[str, object]]:
    if rows is None or getattr(rows, "empty", True):
        return {}
    return {
        (str(row.get("object_id") or ""), str(row.get("material_requirement_id") or "")): dict(row)
        for _, row in rows.iterrows()
        if str(row.get("object_id") or "") and str(row.get("material_requirement_id") or "")
    }


def _build_and_persist_material_plan(
    *,
    client: object,
    estimate_id: str,
    run_id: str,
    company_id: str,
    catalogs: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Compute one estimate-wide plan from the latest facts and user norms."""
    shared_catalogs = catalogs or build_estimation_material_context(client, company_id)["catalogs"]
    facts_by_object = fetch_latest_estimation_facts_by_object(
        client, run_id=run_id, agent_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION,
    )
    override_rows = fetch_rfq_estimate_material_norm_overrides(client, estimate_id)
    overrides = _material_norm_overrides_by_requirement(override_rows)
    fingerprint = material_plan_input_fingerprint(
        facts_by_object=facts_by_object,
        material_norm_overrides=overrides,
        material_default_variants=shared_catalogs.get("material_default_variants") or (),
    )
    result = build_material_plan(
        facts_by_object=facts_by_object,
        catalogs=shared_catalogs,
        material_norm_overrides=overrides,
    )
    snapshot = material_plan_snapshot(result, input_fingerprint=fingerprint)
    plan = result.plan
    upsert_rfq_estimate_material_plan(
        client,
        estimate_id=estimate_id,
        company_id=company_id,
        plan_payload=snapshot,
        plan_status=plan.status if plan else "needs_review",
        input_fingerprint=fingerprint,
    )
    return snapshot


def _recalculate_material_plan_job(*, estimate_id: str, run_id: str, company_id: str) -> dict[str, object]:
    client = get_supabase_client()
    snapshot = _build_and_persist_material_plan(
        client=client,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
    )
    from use_cases.estimation import apply_material_plan_allocations

    apply_material_plan_allocations(
        client,
        estimate_id=estimate_id,
        plan_snapshot=snapshot,
    )
    return snapshot


def _submit_pending_material_plan_recalculation(estimate_id: str) -> Future | None:
    """Submit the latest coalesced request. Caller holds the plan lock."""
    request = _MATERIAL_PLAN_PENDING_REQUESTS.pop(estimate_id, None)
    if request is None:
        return None
    run_id, company_id = request
    future = _ESTIMATION_EXECUTOR.submit(
        _recalculate_material_plan_job,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
    )
    _MATERIAL_PLAN_FUTURES[estimate_id] = future

    def schedule_latest_if_changed(_completed: Future) -> None:
        with _MATERIAL_PLAN_LOCK:
            _submit_pending_material_plan_recalculation(estimate_id)

    future.add_done_callback(schedule_latest_if_changed)
    return future


def queue_material_plan_recalculation(*, estimate_id: str, run_id: str, company_id: str) -> Future:
    """Coalesce edits, but never lose a change that lands during a rebuild."""
    with _MATERIAL_PLAN_LOCK:
        _MATERIAL_PLAN_PENDING_REQUESTS[estimate_id] = (run_id, company_id)
        active = _MATERIAL_PLAN_FUTURES.get(estimate_id)
        if active is not None and not active.done():
            return active
        submitted = _submit_pending_material_plan_recalculation(estimate_id)
        if submitted is None:
            raise RuntimeError("Material-plan recalculation request was not queued")
        return submitted


def _set_object_progress(
    client: object,
    *,
    estimate_id: str,
    object_id: str,
    percent: int,
    label: str,
) -> None:
    """Write one object state for both the instant UI and Supabase polling."""
    set_object_progress(
        estimate_id=estimate_id,
        object_id=object_id,
        percent=percent,
        status="running",
    )
    update_rfq_object_estimate_progress(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        status="running",
        progress_percent=percent,
        progress_label=label,
    )


def _run_estimation_v3_for_all_objects(
    *,
    client: object,
    estimate_id: str,
    created_inputs: list[dict[str, object]],
) -> dict[str, object]:
    """Extract material facts, build one plan, then publish material rows."""
    failed: dict[str, str] = {}
    completed_inputs: list[str] = []
    total = len(created_inputs)
    valid_inputs: list[dict[str, object]] = []
    index_by_input = {}
    for index, input_row in enumerate(created_inputs, start=1):
        object_id = str(input_row.get("object_id") or "")
        input_id = str(input_row.get("input_id") or "")
        if not object_id or not input_id:
            failed[input_id or f"row-{index}"] = "invalid_estimation_input"
            continue
        valid_inputs.append(input_row)
        index_by_input[input_id] = index

    def mark_facts_start(input_row: Mapping[str, object]) -> None:
        input_id = str(input_row.get("input_id") or "")
        object_id = str(input_row.get("object_id") or "")
        _set_object_progress(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            percent=max(1, int((index_by_input[input_id] - 1) * 45 / max(total, 1))),
            label="extracting_object_facts",
        )

    first_payload = valid_inputs[0].get("input_payload") if valid_inputs else None
    company_id = str(first_payload.get("company_id") or "") if isinstance(first_payload, Mapping) else ""
    shared_context = build_estimation_material_context(client, company_id) if company_id else None

    for input_row in valid_inputs:
        mark_facts_start(input_row)
    facts_result = run_estimation_v3_material_facts_batch(
        client=client,
        inputs=valid_inputs,
        material_context=shared_context,
    )

    material_plan_summary: dict[str, object] = {"status": "not_run"}
    material_plan_snapshot_data: dict[str, object] | None = None
    if shared_context and valid_inputs:
        first_payload = valid_inputs[0].get("input_payload")
        run_id = str(first_payload.get("run_id") or "") if isinstance(first_payload, Mapping) else ""
        if run_id:
            try:
                snapshot = _build_and_persist_material_plan(
                    client=client,
                    estimate_id=estimate_id,
                    run_id=run_id,
                    company_id=company_id,
                    catalogs=shared_context["catalogs"],
                )
                material_plan_snapshot_data = snapshot
                material_plan_summary = {
                    "status": snapshot["status"],
                    "demand_count": snapshot["demand_count"],
                    "candidate_count": snapshot["candidate_count"],
                    "planned_line_count": len(snapshot["lines"]),
                    "planned_material_cost_ex_vat": sum(
                        line["total_cost"] for line in snapshot["lines"]
                    ),
                    "unresolved_requirement_ids": snapshot["unresolved_requirement_ids"],
                    "assumption_fallback_count": len(snapshot.get("assumption_fallbacks") or ()),
                    "reason_codes": snapshot["reason_codes"],
                }
            except Exception as exc:
                # Facts extraction and object publishing must stay usable if
                # purchase planning encounters malformed catalog data.
                material_plan_summary = {
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }

    for input_row in valid_inputs:
        object_id = str(input_row["object_id"])
        input_id = str(input_row["input_id"])
        error = facts_result["failed"].get(input_id)
        if error:
            failed[input_id] = error
            update_rfq_object_estimate_progress(
                client,
                estimate_id=estimate_id,
                object_id=object_id,
                status="failed",
                progress_percent=100,
                progress_label="object_facts_failed",
            )
            continue
        _set_object_progress(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            percent=55,
            label="object_facts_ready_for_costing",
        )
        try:
            published = publish_estimation_v3_material_object(
                client=client,
                estimate_id=estimate_id,
                input_row=input_row,
                allowed_material_families=set(shared_context["families"]),
            )
            completed_inputs.append(input_id)
            if published.get("status") not in {"complete", "review_required"}:
                failed[input_id] = f"unexpected_publisher_status:{published.get('status')}"
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
            update_rfq_object_estimate_progress(
                client,
                estimate_id=estimate_id,
                object_id=object_id,
                status="failed",
                progress_percent=100,
                progress_label="v3_material_publisher_failed",
            )
    if material_plan_snapshot_data:
        from use_cases.estimation import apply_material_plan_allocations

        apply_material_plan_allocations(
            client,
            estimate_id=estimate_id,
            plan_snapshot=material_plan_snapshot_data,
        )
    return {
        "processed_input_ids": completed_inputs,
        "failed": failed,
        "material_engine_plan": material_plan_summary,
    }


def submit_estimation_job(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    object_edits: dict[str, dict[str, object]],
    edits_changed: bool,
    ignored_object_ids: set[str],
    create_shell: bool,
) -> Future:
    """Create the access-controlled shell, then queue the expensive agent work."""
    if edits_changed:
        ignored_object_ids = apply_file_review_edits(
            run_id=run_id,
            company_id=company_id,
            object_edits={
                str(object_id): dict(edit)
                for object_id, edit in object_edits.items()
            },
        )

    shell = None
    if create_shell:
        shell = start_estimation_for_run(
            run_id=run_id,
            company_id=company_id,
            ignored_object_ids=ignored_object_ids,
            estimate_id=estimate_id,
        )

    return _ESTIMATION_EXECUTOR.submit(
        _run_estimation_job,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
        ignored_object_ids=ignored_object_ids,
        shell=shell,
    )


def _run_estimation_job(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    ignored_object_ids: set[str],
    shell: dict[str, object] | None,
) -> dict[str, object]:
    """Persist the V3 handoff, then run queued material estimates."""
    created_inputs: list[dict[str, object]] = []
    client = get_supabase_client()
    try:
        run_rows = fetch_rfq_run(client, run_id)
        object_rows = fetch_rfq_detected_objects(client, run_id)
        ocr = fetch_latest_ocr_result(client, run_id)
        if not run_rows.empty and ocr and ocr.get("ocr_event_id"):
            handoff = persist_estimation_inputs(
                client=client,
                run=run_rows.iloc[0].to_dict(),
                objects=[row.to_dict() for _, row in object_rows.iterrows()],
                ignored_object_ids=ignored_object_ids,
                file_name=file_name,
                file_bytes=file_bytes,
                ocr_event_id=str(ocr["ocr_event_id"]),
                ocr_package=ocr["ocr_result"],
                original=describe_estimation_original(
                    company_id=company_id, file_name=file_name, file_bytes=file_bytes
                ),
                versions={"detection": DETECTION_PROMPT_VERSION},
            )
            created_inputs = handoff["created_inputs"]
    except Exception as exc:
        raise RuntimeError(f"Estimation V3 handoff failed: {exc}") from exc

    inputs_available = bool(created_inputs)
    if inputs_available:
        estimation_result = _run_estimation_v3_for_all_objects(
                client=client,
                estimate_id=estimate_id,
                created_inputs=created_inputs,
        )
        return {
            "estimate_id": estimate_id,
            "run_id": run_id,
            "shell": shell,
            "estimation": {
                "status": "completed" if not estimation_result["failed"] else "completed_with_failures",
                "estimated_objects": len(estimation_result["processed_input_ids"]),
                "failed_objects": estimation_result["failed"],
            },
            "estimation_version": "v3_materials",
        }
    if shell and int(shell.get("object_count") or 0) == 0:
        return {
            "estimate_id": estimate_id,
            "run_id": run_id,
            "shell": shell,
            "estimation": {
                "status": "no_objects",
                "estimated_objects": 0,
                "failed_objects": {},
            },
            "estimation_version": "v3_materials",
        }
    raise RuntimeError("Estimation V3 input handoff produced no estimable objects.")
