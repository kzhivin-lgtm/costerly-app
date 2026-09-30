from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from use_cases.estimation import estimate_all_objects_for_run, start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits
from agents.anthropic_adapter import DETECTION_PROMPT_VERSION, get_secret
from db.repositories import fetch_latest_ocr_result, fetch_rfq_detected_objects, fetch_rfq_run
from db.supabase_client import get_supabase_client
from use_cases.estimation_handoff import persist_estimation_v2_shadow_inputs
from use_cases.estimation_originals import describe_estimation_original
from use_cases.estimation_v2_facts_shadow import run_estimation_v2_facts_shadow_batch


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_ESTIMATION_V2_FACTS_EXECUTOR = ThreadPoolExecutor(max_workers=1)


def _estimation_v2_facts_shadow_enabled() -> bool:
    value = str(get_secret("ESTIMATION_V2_FACTS_SHADOW_ENABLED", "false") or "false")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_estimation_v2_facts_shadow(created_inputs: list[dict[str, object]]) -> None:
    try:
        result = run_estimation_v2_facts_shadow_batch(
            client=get_supabase_client(),
            inputs=created_inputs,
        )
        if result["failed"]:
            print(f"[Estimation v2 facts shadow] Object failures: {result['failed']}")
    except Exception as exc:
        print(f"[Estimation v2 facts shadow] Batch failed: {exc}")


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
    """Queue estimation work without blocking the Streamlit click path."""
    return _ESTIMATION_EXECUTOR.submit(
        _run_estimation_job,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
        object_edits=object_edits,
        edits_changed=edits_changed,
        ignored_object_ids=ignored_object_ids,
        create_shell=create_shell,
    )


def _run_estimation_job(
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
) -> dict[str, object]:
    """Persist edits, ensure the shell exists, then run queued object estimates."""
    if edits_changed:
        ignored_object_ids = apply_file_review_edits(
            run_id=run_id,
            company_id=company_id,
            object_edits={
                str(object_id): dict(edit)
                for object_id, edit in object_edits.items()
            },
        )

    created_v2_inputs: list[dict[str, object]] = []
    try:
        client = get_supabase_client()
        run_rows = fetch_rfq_run(client, run_id)
        object_rows = fetch_rfq_detected_objects(client, run_id)
        ocr = fetch_latest_ocr_result(client, run_id)
        if not run_rows.empty and ocr and ocr.get("ocr_event_id"):
            handoff = persist_estimation_v2_shadow_inputs(
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
        print(f"[Estimation v2 shadow] Could not persist handoff: {exc}")

    shell = None
    if create_shell:
        shell = start_estimation_for_run(
            run_id=run_id,
            company_id=company_id,
            ignored_object_ids=ignored_object_ids,
            estimate_id=estimate_id,
        )
    estimation_result = estimate_all_objects_for_run(
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )
    facts_shadow_queued = bool(created_v2_inputs and _estimation_v2_facts_shadow_enabled())
    if facts_shadow_queued:
        _ESTIMATION_V2_FACTS_EXECUTOR.submit(
            _run_estimation_v2_facts_shadow,
            created_v2_inputs,
        )
    return {
        "estimate_id": estimate_id,
        "run_id": run_id,
        "shell": shell,
        "estimation": estimation_result,
        "v2_facts_shadow_queued": facts_shadow_queued,
    }
