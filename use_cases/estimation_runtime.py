from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from use_cases.estimation import estimate_pending_objects_for_run, start_estimation_for_run
from use_cases.rfq_processing import apply_file_review_edits


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_ESTIMATION_FUTURES: dict[str, Future] = {}


def submit_estimation_start_command(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    object_edits: dict[str, dict[str, object]],
    edits_changed: bool,
    ignored_object_ids: set[str],
) -> Future:
    """Start estimate setup and the object cycle outside the Streamlit click path."""
    future = _ESTIMATION_EXECUTOR.submit(
        _run_estimation_start_command,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
        object_edits=object_edits,
        edits_changed=edits_changed,
        ignored_object_ids=ignored_object_ids,
    )
    _ESTIMATION_FUTURES[estimate_id] = future
    return future


def get_estimation_future(estimate_id: str) -> Future | None:
    future = _ESTIMATION_FUTURES.get(estimate_id)
    if future and not future.done():
        return future
    return None


def _run_estimation_start_command(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
    object_edits: dict[str, dict[str, object]],
    edits_changed: bool,
    ignored_object_ids: set[str],
) -> dict[str, object]:
    """Persist File Review changes, create the estimate shell, then run agents."""
    if edits_changed:
        ignored_object_ids = apply_file_review_edits(
            run_id=run_id,
            object_edits={
                str(object_id): dict(edit)
                for object_id, edit in object_edits.items()
            },
        )

    shell = start_estimation_for_run(
        run_id=run_id,
        company_id=company_id,
        ignored_object_ids=ignored_object_ids,
        estimate_id=estimate_id,
    )
    cycle = estimate_pending_objects_for_run(
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
        "cycle": cycle,
    }
