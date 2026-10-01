from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Mapping

from use_cases.estimation import start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits
from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from db.repositories import fetch_latest_ocr_result, fetch_rfq_detected_objects, fetch_rfq_run
from db.supabase_client import get_supabase_client
from use_cases.estimation_handoff import persist_estimation_v2_inputs
from use_cases.estimation_originals import describe_estimation_original
from use_cases.estimation_v2_facts_shadow import run_estimation_v2_facts_batch
from use_cases.estimation_v2_publisher import (
    build_estimation_v2_context,
    publish_estimation_v2_object,
)
from db.repositories import update_rfq_object_estimate_progress
from use_cases.estimation_progress import set_object_progress


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)


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


def _run_estimation_v2_for_all_objects(
    *,
    client: object,
    estimate_id: str,
    created_inputs: list[dict[str, object]],
) -> dict[str, object]:
    """Extract, price and publish every object through Estimation v2."""
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
    shared_context = build_estimation_v2_context(client, company_id) if company_id else None

    for input_row in valid_inputs:
        object_id = str(input_row["object_id"])
        input_id = str(input_row["input_id"])
        mark_facts_start(input_row)
        facts_result = run_estimation_v2_facts_batch(
            client=client,
            inputs=[input_row],
        )
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
            published = publish_estimation_v2_object(
                client=client,
                estimate_id=estimate_id,
                input_row=input_row,
                context=shared_context,
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
                progress_label="v2_publisher_failed",
            )
    return {"processed_input_ids": completed_inputs, "failed": failed}


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
    """Persist the v2 handoff, then run queued object estimates."""
    created_v2_inputs: list[dict[str, object]] = []
    client = get_supabase_client()
    try:
        run_rows = fetch_rfq_run(client, run_id)
        object_rows = fetch_rfq_detected_objects(client, run_id)
        ocr = fetch_latest_ocr_result(client, run_id)
        if not run_rows.empty and ocr and ocr.get("ocr_event_id"):
            handoff = persist_estimation_v2_inputs(
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
            created_v2_inputs = handoff["created_inputs"]
    except Exception as exc:
        raise RuntimeError(f"Estimation v2 handoff failed: {exc}") from exc

    v2_inputs_available = bool(created_v2_inputs)
    if v2_inputs_available:
        estimation_result = _run_estimation_v2_for_all_objects(
                client=client,
                estimate_id=estimate_id,
                created_inputs=created_v2_inputs,
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
            "estimation_version": "v2",
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
            "estimation_version": "v2",
        }
    raise RuntimeError("Estimation v2 input handoff produced no estimable objects.")
