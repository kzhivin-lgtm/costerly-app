from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from use_cases.estimation import estimate_pending_objects_for_run


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)


def submit_pending_object_estimation(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
) -> Future:
    """Run pending object estimation work in a shared background worker."""
    return _ESTIMATION_EXECUTOR.submit(
        estimate_pending_objects_for_run,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )
