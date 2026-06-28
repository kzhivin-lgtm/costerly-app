from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from use_cases.estimation import estimate_all_objects_for_run, start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)


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
    estimation_result = estimate_all_objects_for_run(
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )
    return {
        "estimate_id": estimate_id,
        "run_id": run_id,
        "shell": shell,
        "estimation": estimation_result,
    }
