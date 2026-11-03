from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from use_cases.estimation import load_object_detail_data


# Detail prefetching is deliberately separate from the single estimation worker.
# It is read-only, bounded, and must never delay estimation or a user click.
_OBJECT_DETAIL_PREFETCH_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="object-detail-prefetch",
)


def submit_object_detail_prefetch(
    *, estimate_id: str, object_id: str, company_id: str,
) -> Future:
    """Prepare one completed Object Detail snapshot without touching session state."""
    return _OBJECT_DETAIL_PREFETCH_EXECUTOR.submit(
        load_object_detail_data,
        estimate_id=estimate_id,
        object_id=object_id,
        company_id=company_id,
    )
