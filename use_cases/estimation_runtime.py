from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import json
import logging
from threading import RLock
from typing import Mapping

from use_cases.estimation import start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits, save_file_review_run_metadata
from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from db.repositories import (
    fetch_estimation_object_input,
    fetch_latest_ocr_result,
    fetch_rfq_estimate_material_plan,
    fetch_rfq_estimate_material_norm_overrides,
    fetch_rfq_estimate_material_purchase_overrides,
    fetch_rfq_object_estimates,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_totals,
    upsert_rfq_estimate_lines,
    upsert_rfq_estimate_material_plan,
)
from db.supabase_client import get_supabase_client
from use_cases.estimation_handoff import persist_estimation_inputs
from use_cases.estimation_originals import describe_estimation_original
from use_cases.estimation_parts_check_runtime import VERSION, load_parts_check, run_parts_check_for_estimate
from use_cases.estimation_cb_material_demand import calculate_cb_materials
from use_cases.material_engine_adapter import reprice_material_purchase_snapshot
from use_cases.estimation_material_context import build_estimation_material_context
from use_cases.estimation_assumption_fallbacks import persist_material_assumption_fallbacks
from db.repositories import update_rfq_object_estimate_progress
from use_cases.estimation_progress import set_object_progress


_LOG = logging.getLogger(__name__)
_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_MATERIAL_PLAN_LOCK = RLock()
_MATERIAL_PLAN_FUTURES: dict[str, Future] = {}
_MATERIAL_PLAN_PENDING_REQUESTS: dict[str, tuple[str, str, list[Future], bool]] = {}
_MATERIAL_PLAN_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="material-plan")


def _material_norm_overrides_by_requirement(rows: object) -> dict[tuple[str, str], dict[str, object]]:
    if rows is None or getattr(rows, "empty", True):
        return {}
    return {
        (str(row.get("object_id") or ""), str(row.get("material_requirement_id") or "")): dict(row)
        for _, row in rows.iterrows()
        if str(row.get("object_id") or "") and str(row.get("material_requirement_id") or "")
    }


def _material_purchase_overrides_by_selection_key(rows: object) -> dict[str, dict[str, object]]:
    if rows is None or getattr(rows, "empty", True):
        return {}
    return {str(row.get("selection_key") or ""): dict(row) for _, row in rows.iterrows() if str(row.get("selection_key") or "")}


def _publish_material_demand_lines(client, *, estimate_id, facts_by_object, replace_object_lines=True):
    for object_id, facts in facts_by_object.items():
        lines = []
        for index, demand in enumerate(facts["materials"], 1):
            quantity = demand.get("quantity")
            lines.append({
                "estimate_id": estimate_id, "object_id": object_id, "company_id": facts["company_id"],
                "line_id": f"{object_id}_material_{index:04d}", "section": "material",
                "group_name": "Supplier services" if demand.get("item_kind") == "operation_service" else "Materials",
                "item_name": demand["source_name"], "catalog_match_query": demand.get("family") or demand.get("operation_code"),
                "unit": demand.get("unit"), "quantity": None if quantity is None else quantity / facts["quantity"],
                "cost": None, "unit_cost": None, "source": "parts_check", "sort_order": index * 10,
                "needs_price": True, "needs_review": False, "quantity_basis": "per_finished_item",
                "raw_agent_json": {"facts": demand},
            })
        if replace_object_lines:
            replace_rfq_estimate_lines_for_object(client, estimate_id=estimate_id, object_id=object_id, lines=lines)
        else:
            upsert_rfq_estimate_lines(client, lines=lines)


def _build_and_persist_material_plan(*, client, estimate_id, company_id, parts_report, input_rows, rebuild=False):
    """Price the checked document through the shared estimate-wide engine."""
    catalog_context = build_estimation_material_context(client, company_id)
    norms = _material_norm_overrides_by_requirement(fetch_rfq_estimate_material_norm_overrides(client, estimate_id))
    purchases = _material_purchase_overrides_by_selection_key(fetch_rfq_estimate_material_purchase_overrides(client, estimate_id))
    calculation = calculate_cb_materials(
        parts_report=parts_report, input_rows=input_rows, catalog_context=catalog_context,
        material_norm_overrides=norms, material_purchase_overrides=purchases,
    )
    snapshot = calculation["material_plan"]
    facts_by_object = calculation["facts_by_object"]
    _publish_material_demand_lines(
        client, estimate_id=estimate_id, facts_by_object=facts_by_object, replace_object_lines=not rebuild,
    )

    from use_cases.estimation import apply_material_plan_allocations

    try:
        snapshot["assumption_job_sync"] = {
            "status": "synced",
            "count": persist_material_assumption_fallbacks(
                client=client, estimate_id=estimate_id, company_id=company_id,
                facts_by_object=facts_by_object, plan_snapshot=snapshot,
            ),
        }
    except Exception as exc:
        snapshot["assumption_job_sync"] = {"status": "failed", "error": type(exc).__name__}
        _LOG.warning("Assumption follow-up failed for estimate %s", estimate_id, exc_info=True)

    apply_material_plan_allocations(client, estimate_id=estimate_id, plan_snapshot=snapshot)
    upsert_rfq_estimate_material_plan(
        client, estimate_id=estimate_id, company_id=company_id, plan_payload=snapshot,
        plan_status=snapshot["status"], input_fingerprint=snapshot["input_fingerprint"],
    )
    return snapshot


def _mark_material_plan_failed(client, *, estimate_id, company_id, reason, preserve_snapshot=False):
    try:
        previous = {}
        if preserve_snapshot:
            rows = fetch_rfq_estimate_material_plan(client, estimate_id)
            if not rows.empty:
                previous = rows.iloc[0].get("plan_payload") or {}
        upsert_rfq_estimate_material_plan(
            client, estimate_id=estimate_id, company_id=company_id,
            plan_payload={**previous, "status": "failed", "reason_codes": [reason], "input_fingerprint": None},
            plan_status="failed",
        )
    except Exception:
        _LOG.exception("Could not publish the material plan failure for estimate %s", estimate_id)


def _recalculate_material_plan_job(*, estimate_id: str, run_id: str, company_id: str, purchase_only: bool = False) -> dict[str, object]:
    client = get_supabase_client()
    if purchase_only:
        rows = fetch_rfq_estimate_material_plan(client, estimate_id)
        saved = rows.iloc[0].get("plan_payload") if not rows.empty else None
        if saved and saved.get("status") in {"planned", "needs_review"}:
            overrides = _material_purchase_overrides_by_selection_key(
                fetch_rfq_estimate_material_purchase_overrides(client, estimate_id),
            )
            snapshot, changed = reprice_material_purchase_snapshot(saved, overrides)
            if changed:
                from use_cases.estimation import apply_material_plan_allocations

                apply_material_plan_allocations(client, estimate_id=estimate_id, plan_snapshot=snapshot,
                                                changed_requirements=changed)
                snapshot["input_fingerprint"] = None
                upsert_rfq_estimate_material_plan(client, estimate_id=estimate_id, company_id=company_id,
                                                 plan_payload=snapshot, plan_status=snapshot["status"])
            return snapshot
    try:
        return _recalculate_from_parts_check(client, estimate_id=estimate_id, run_id=run_id, company_id=company_id)
    except Exception:
        _mark_material_plan_failed(client, estimate_id=estimate_id, company_id=company_id,
                                   reason="material_plan_technical_failure", preserve_snapshot=True)
        raise


def _recalculate_from_parts_check(client, *, estimate_id, run_id, company_id):
    saved = load_parts_check(client=client, company_id=company_id, run_id=run_id, estimate_id=estimate_id)
    if saved["status"] != "ready" or not saved.get("input_ids"):
        raise RuntimeError("The estimate has no published Parts Check with immutable input references")
    report = json.loads(saved["payload"])
    objects = fetch_rfq_object_estimates(client, estimate_id)
    quantities = {str(row["object_id"]): row["quantity"] for _, row in objects.iterrows()}
    input_rows = []
    for input_id in saved["input_ids"]:
        row = fetch_estimation_object_input(client, input_id=input_id)
        if not row or row.get("company_id") != company_id or row.get("run_id") != run_id:
            raise ValueError("Parts Check input does not belong to this estimate")
        payload = row["input_payload"]
        obj = payload["object"]
        quantity = quantities[obj["object_id"]]
        input_rows.append({**row, "input_payload": {**payload, "object": {**obj, "quantity": float(quantity)}}})
    return _build_and_persist_material_plan(
        client=client, estimate_id=estimate_id, company_id=company_id, parts_report=report, input_rows=input_rows,
        rebuild=True,
    )


def _submit_pending_material_plan_recalculation(estimate_id: str) -> Future | None:
    """Submit the latest coalesced request. Caller holds the plan lock."""
    request = _MATERIAL_PLAN_PENDING_REQUESTS.pop(estimate_id, None)
    if request is None:
        return None
    run_id, company_id, receipts, purchase_only = request
    future = _MATERIAL_PLAN_EXECUTOR.submit(
        _recalculate_material_plan_job,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        purchase_only=purchase_only,
    )
    _MATERIAL_PLAN_FUTURES[estimate_id] = future

    def schedule_latest_if_changed(completed: Future) -> None:
        with _MATERIAL_PLAN_LOCK:
            if _submit_pending_material_plan_recalculation(estimate_id) is None:
                _MATERIAL_PLAN_FUTURES.pop(estimate_id, None)
        for receipt in receipts:
            if completed.cancelled():
                receipt.cancel()
            elif (error := completed.exception()) is not None:
                receipt.set_exception(error)
            else:
                receipt.set_result(completed.result())

    future.add_done_callback(schedule_latest_if_changed)
    return future


def queue_material_plan_recalculation(*, estimate_id: str, run_id: str, company_id: str,
                                      purchase_only: bool = False) -> Future:
    """Coalesce edits, but never lose a change that lands during a rebuild."""
    with _MATERIAL_PLAN_LOCK:
        receipt = Future()
        pending = _MATERIAL_PLAN_PENDING_REQUESTS.get(estimate_id)
        receipts = pending[2] if pending else []
        _MATERIAL_PLAN_PENDING_REQUESTS[estimate_id] = (
            run_id, company_id, [*receipts, receipt], purchase_only and (pending is None or pending[3]),
        )
        if estimate_id not in _MATERIAL_PLAN_FUTURES:
            _submit_pending_material_plan_recalculation(estimate_id)
        return receipt


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


def _set_object_technical_failure(
    client: object,
    *,
    estimate_id: str,
    object_id: str,
    label: str,
) -> None:
    """End a technical failure instead of leaving a running percentage behind."""
    set_object_progress(
        estimate_id=estimate_id,
        object_id=object_id,
        percent=100,
        status="failed",
    )
    update_rfq_object_estimate_progress(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        status="failed",
        progress_percent=100,
        progress_label=label,
    )


def _mark_handoff_failure(
    *,
    client: object,
    estimate_id: str,
    objects: list[Mapping[str, object]],
    ignored_object_ids: set[str],
) -> None:
    """End every known estimate row if immutable evidence handoff fails.

    A handoff happens before an Estimation input exists, so it has no input ID
    for the normal per-input failure trace. It still has reviewed object IDs.
    Those rows must become terminal failures rather than lingering at the
    optimistic geometry progress cap after the worker has exited.
    """
    for item in objects:
        object_id = str(item.get("object_id") or "")
        if not object_id or object_id in ignored_object_ids:
            continue
        try:
            _set_object_technical_failure(
                client,
                estimate_id=estimate_id,
                object_id=object_id,
                label="estimation_handoff_failed",
            )
        except Exception:
            # Preserve the original handoff error. The local progress state is
            # written before the durable update, so this session can still
            # leave the misleading running state.
            continue


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


def submit_prepared_estimation_job(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    object_edits: Mapping[str, Mapping[str, object]],
    metadata_values: Mapping[str, str],
    edits_changed: bool,
    ignored_object_ids: set[str],
    create_shell: bool,
) -> Future:
    """Queue the existing durable launch after Objects has painted its seed rows.

    The caller has already captured immutable File Review input.  Keeping all
    writes inside the worker is deliberate: a Streamlit button callback can
    switch to the seeded Objects screen without waiting on Supabase, while the
    same persistence and Estimation work still begins only after explicit user
    intent.
    """
    return _ESTIMATION_EXECUTOR.submit(
        _persist_prepared_launch_and_run,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
        object_edits={
            str(object_id): dict(edit)
            for object_id, edit in object_edits.items()
        },
        metadata_values={str(field): str(value) for field, value in metadata_values.items()},
        edits_changed=edits_changed,
        ignored_object_ids=set(ignored_object_ids),
        create_shell=create_shell,
    )


def _persist_prepared_launch_and_run(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    object_edits: dict[str, dict[str, object]],
    metadata_values: dict[str, str],
    edits_changed: bool,
    ignored_object_ids: set[str],
    create_shell: bool,
) -> dict[str, object]:
    """Persist an accepted launch snapshot, then run Estimation."""
    save_file_review_run_metadata(
        run_id=run_id,
        values=metadata_values,
        company_id=company_id,
    )
    if edits_changed:
        ignored_object_ids = apply_file_review_edits(
            run_id=run_id,
            company_id=company_id,
            object_edits=object_edits,
        )

    shell = None
    if create_shell:
        shell = start_estimation_for_run(
            run_id=run_id,
            company_id=company_id,
            ignored_object_ids=ignored_object_ids,
            estimate_id=estimate_id,
        )

    return _run_estimation_job(
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
    """Build the checked parts and price them from the immutable File Review handoff."""
    created_inputs: list[dict[str, object]] = []
    client = get_supabase_client()
    object_rows_data: list[dict[str, object]] = []
    try:
        run_rows = fetch_rfq_run(client, run_id)
        object_rows = fetch_rfq_detected_objects(client, run_id)
        object_rows_data = [row.to_dict() for _, row in object_rows.iterrows()]
        ocr = fetch_latest_ocr_result(client, run_id)
        if not run_rows.empty and ocr and ocr.get("ocr_event_id"):
            handoff = persist_estimation_inputs(
                client=client,
                run=run_rows.iloc[0].to_dict(),
                objects=object_rows_data,
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
        _mark_handoff_failure(
            client=client,
            estimate_id=estimate_id,
            objects=object_rows_data,
            ignored_object_ids=ignored_object_ids,
        )
        raise RuntimeError(f"Estimation handoff failed: {exc}") from exc

    if created_inputs:
        object_ids = [row["input_payload"]["object"]["object_id"] for row in created_inputs]
        stage = "parts_check"
        try:
            for object_id in object_ids:
                _set_object_progress(client, estimate_id=estimate_id, object_id=object_id,
                                     percent=15, label="building_parts_check")
            report = run_parts_check_for_estimate(
                client=client, estimate_id=estimate_id, run_id=run_id, company_id=company_id,
                file_name=file_name, file_bytes=file_bytes, inputs=created_inputs, ocr_package=ocr["ocr_result"],
            )
            if report is None:
                raise RuntimeError("Parts Check did not produce a checked report")
            stage = "material_plan"
            for object_id in object_ids:
                _set_object_progress(client, estimate_id=estimate_id, object_id=object_id,
                                     percent=70, label="building_project_material_plan")
            snapshot = _build_and_persist_material_plan(
                client=client, estimate_id=estimate_id, company_id=company_id,
                parts_report=report, input_rows=created_inputs,
            )
        except Exception:
            _LOG.exception("Estimation failed at %s for estimate %s", stage, estimate_id)
            _mark_material_plan_failed(client, estimate_id=estimate_id, company_id=company_id,
                                       reason=f"{stage}_technical_failure")
            for object_id in object_ids:
                update_rfq_object_estimate_totals(
                    client, estimate_id=estimate_id, object_id=object_id,
                    self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
                )
                _set_object_technical_failure(client, estimate_id=estimate_id, object_id=object_id,
                                              label=f"{stage}_technical_failure")
            return {
                "estimate_id": estimate_id, "run_id": run_id, "shell": shell,
                "estimation": {"status": "completed_with_failures", "estimated_objects": 0,
                               "failed_objects": {row["input_id"]: f"{stage}_technical_failure" for row in created_inputs}},
                "estimation_version": VERSION,
            }
        return {
            "estimate_id": estimate_id, "run_id": run_id, "shell": shell,
            "estimation": {"status": "completed" if snapshot["status"] == "planned" else "review_required",
                           "estimated_objects": len(created_inputs), "failed_objects": {}},
            "estimation_version": VERSION,
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
            "estimation_version": VERSION,
        }
    raise RuntimeError("Estimation input handoff produced no estimable objects.")
