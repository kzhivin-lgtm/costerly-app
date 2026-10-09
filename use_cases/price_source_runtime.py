"""Background runtime for one company's Price Source extraction."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
import logging
from threading import Lock
import time
from typing import Any, Callable
from uuid import uuid4

from db.supabase_client import get_supabase_client
from use_cases.price_sources import (
    PriceSourceError,
    PriceSourceProcessResult,
    list_material_jobs,
    list_price_catalog,
    list_price_sources,
    list_unresolved_price_source_rows,
    process_price_source,
    purge_price_source,
    save_price_source_row,
)


logger = logging.getLogger(__name__)


_PRICE_SOURCE_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="price-source-extraction",
)
_PRICE_LISTS_READ_EXECUTOR = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="price-lists-read",
)
_LOCKS_GUARD = Lock()
_COMPANY_LOCKS: dict[str, Lock] = {}
_ACTIVE_JOBS_GUARD = Lock()


@dataclass(frozen=True)
class ActivePriceSourceJob:
    """One submitted extraction, retained while a browser session may reload."""

    future: Future
    job_id: str
    started_at: float
    started_at_epoch_ms: int


@dataclass(frozen=True)
class PriceSourceBatchProcessResult:
    """Terminal outcome for one user-submitted batch of independent files."""

    results: tuple[PriceSourceProcessResult, ...]
    failed_source_names: tuple[str, ...]

    @property
    def summary(self) -> dict[str, object]:
        numeric_keys = (
            "ready", "new", "updated", "unchanged", "merged", "unresolved",
            "excluded", "discarded_non_candidates", "discarded_consumables",
            "operation_services", "total", "agent_duration_seconds", "token_cost",
            "input_tokens", "output_tokens",
        )
        summary: dict[str, object] = {
            "source_count": len(self.results),
            "failed_source_count": len(self.failed_source_names),
            "failed_source_names": list(self.failed_source_names),
        }
        for key in numeric_keys:
            summary[key] = sum(
                float(result.summary.get(key) or 0)
                for result in self.results
            )
        for key in ("ready", "new", "updated", "unchanged", "merged", "unresolved", "excluded", "discarded_non_candidates", "discarded_consumables", "operation_services", "total", "input_tokens", "output_tokens"):
            summary[key] = int(summary[key])
        return summary


_COMPANY_ACTIVE_JOBS: dict[str, ActivePriceSourceJob] = {}


def _bounded_error_message(exc: BaseException, *, limit: int = 240) -> str:
    """Keep diagnostic events actionable without persisting unbounded input text."""
    return " ".join(str(exc).split())[:limit]


def _trace_event(
    trace: Any,
    name: str,
    *,
    status: str = "ok",
    duration_ms: float | None = None,
    **metadata: object,
) -> None:
    if trace is not None:
        trace.event(name, status=status, duration_ms=duration_ms, metadata=metadata)


def _company_lock(company_id: str) -> Lock:
    with _LOCKS_GUARD:
        return _COMPANY_LOCKS.setdefault(company_id, Lock())


def active_price_source_job(company_id: str) -> ActivePriceSourceJob | None:
    """Return a live company extraction so a reloaded UI can reattach to it."""
    with _ACTIVE_JOBS_GUARD:
        active = _COMPANY_ACTIVE_JOBS.get(str(company_id))
        if active is None or active.future.done():
            return None
        return active


def _clear_active_price_source_job(company_id: str, future: Future) -> None:
    with _ACTIVE_JOBS_GUARD:
        active = _COMPANY_ACTIVE_JOBS.get(company_id)
        if active is not None and active.future is future:
            _COMPANY_ACTIVE_JOBS.pop(company_id, None)


def submit_price_source_job(
    *,
    access,
    uploaded_file,
    source_url: str,
    trace=None,
) -> Future:
    """Queue one company-scoped extraction without holding the UI request open."""
    # A click must acknowledge quickly. Network I/O here delayed the Streamlit
    # callback by almost the browser watchdog window, which made a submitted
    # extraction look as though it never reached the server. Authorization is
    # still enforced by ``process_price_source`` in the worker before it can
    # create or change any company data.
    company_id = str(access.company_id)
    with _ACTIVE_JOBS_GUARD:
        previous = _COMPANY_ACTIVE_JOBS.get(company_id)
        if previous is not None and not previous.future.done():
            raise PriceSourceError(
                "Another price extraction is already running. Try again when it finishes."
            )
        job_id = str(uuid4())
        started_at = time.perf_counter()
        _trace_event(trace, "server.price_source_job_submitted", job_id=job_id)
        future = _PRICE_SOURCE_EXECUTOR.submit(
            _run_price_source_job,
            access=access,
            uploaded_file=uploaded_file,
            source_url=source_url,
            trace=trace,
            job_id=job_id,
            owner_authorized=False,
        )
        _COMPANY_ACTIVE_JOBS[company_id] = ActivePriceSourceJob(
            future=future,
            job_id=job_id,
            started_at=started_at,
            started_at_epoch_ms=int(time.time() * 1000),
        )
    future.add_done_callback(
        lambda completed: _clear_active_price_source_job(company_id, completed)
    )
    return future


def submit_price_source_batch_job(
    *,
    access,
    uploaded_files: list,
    trace=None,
) -> Future:
    """Queue several file inputs as one company-scoped batch.

    A batch remains serial inside one company lock.  This avoids the race in
    which two photos of the same invoice both decide that no aggregate source
    exists, then create two sources.  Different companies can still use the
    executor independently.
    """
    if not uploaded_files:
        raise PriceSourceError("Add at least one file.")
    company_id = str(access.company_id)
    with _ACTIVE_JOBS_GUARD:
        previous = _COMPANY_ACTIVE_JOBS.get(company_id)
        if previous is not None and not previous.future.done():
            raise PriceSourceError(
                "Another price extraction is already running. Try again when it finishes."
            )
        job_id = str(uuid4())
        started_at = time.perf_counter()
        _trace_event(
            trace,
            "server.price_source_batch_submitted",
            job_id=job_id,
            source_count=len(uploaded_files),
        )
        future = _PRICE_SOURCE_EXECUTOR.submit(
            _run_price_source_batch_job,
            access=access,
            uploaded_files=tuple(uploaded_files),
            trace=trace,
            job_id=job_id,
        )
        _COMPANY_ACTIVE_JOBS[company_id] = ActivePriceSourceJob(
            future=future,
            job_id=job_id,
            started_at=started_at,
            started_at_epoch_ms=int(time.time() * 1000),
        )
    future.add_done_callback(
        lambda completed: _clear_active_price_source_job(company_id, completed)
    )
    return future


def submit_price_source_purge_job(*, access, source_id: str, trace=None) -> Future:
    """Purge one source away from the Streamlit click callback.

    The UI can remove the source row immediately, while the server-owned
    deletion finishes without making the browser wait for database and storage
    round trips.
    """
    job_id = str(uuid4())
    _trace_event(
        trace,
        "server.price_source_purge_submitted",
        job_id=job_id,
        source_id=source_id,
    )
    return _PRICE_SOURCE_EXECUTOR.submit(
        _run_price_source_purge_job,
        access=access,
        source_id=source_id,
        trace=trace,
        job_id=job_id,
    )


def submit_price_source_row_save_job(
    *, access, source_id: str, row_id: str, values: dict,
) -> Future:
    """Persist a reviewed row after its UI action has completed optimistically."""
    return _PRICE_SOURCE_EXECUTOR.submit(
        save_price_source_row,
        access,
        source_id,
        row_id,
        values,
    )


def submit_price_lists_projection_jobs(
    *,
    access,
    loaders: dict[str, Callable] | None = None,
) -> dict[str, Future]:
    """Start independent Price Lists reads without delaying the upload control.

    These are read-only company-scoped projections. They intentionally use a
    separate executor from extraction and deletion, so a slow catalog read
    cannot delay an owner action or a source-processing worker.
    """
    resolved_loaders = loaders or {
        "sources": list_price_sources,
        "catalog": list_price_catalog,
        "review": list_unresolved_price_source_rows,
        "material_jobs": list_material_jobs,
    }
    return {
        name: _PRICE_LISTS_READ_EXECUTOR.submit(loader, access)
        for name, loader in resolved_loaders.items()
    }


def _run_price_source_job(
    *, access, uploaded_file, source_url: str, trace=None, job_id: str,
    owner_authorized: bool = False,
):
    started_at = time.perf_counter()
    company_id = str(access.company_id)
    lock = _company_lock(company_id)
    _trace_event(trace, "server.price_source_worker_started", job_id=job_id)
    if not lock.acquire(blocking=False):
        _trace_event(trace, "server.price_source_lock_rejected", status="error", job_id=job_id)
        raise PriceSourceError(
            "Another price extraction is already running. Try again when it finishes."
        )
    try:
        _trace_event(trace, "server.price_source_lock_acquired", job_id=job_id)
        result = process_price_source(
            access,
            department="",
            uploaded_file=uploaded_file,
            source_url=source_url,
            trace=trace,
            # Get a fresh client from the background-safe cached factory.
            client=get_supabase_client(),
            owner_authorized=owner_authorized,
        )
        _trace_event(
            trace,
            "server.price_source_worker_finished",
            job_id=job_id,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )
        return result
    except Exception as exc:
        _trace_event(
            trace,
            "server.price_source_worker_finished",
            status="error",
            job_id=job_id,
            error_type=type(exc).__name__,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )
        raise
    finally:
        lock.release()


def _run_price_source_batch_job(*, access, uploaded_files, trace=None, job_id: str):
    """Process each file separately while preserving invoice-page merge safety."""
    started_at = time.perf_counter()
    company_id = str(access.company_id)
    lock = _company_lock(company_id)
    _trace_event(
        trace,
        "server.price_source_batch_worker_started",
        job_id=job_id,
        source_count=len(uploaded_files),
    )
    if not lock.acquire(blocking=False):
        _trace_event(trace, "server.price_source_lock_rejected", status="error", job_id=job_id)
        raise PriceSourceError(
            "Another price extraction is already running. Try again when it finishes."
        )
    results: list[PriceSourceProcessResult] = []
    failed_source_names: list[str] = []
    try:
        _trace_event(trace, "server.price_source_lock_acquired", job_id=job_id)
        client = get_supabase_client()
        prior_batch_source_ids: set[str] = set()
        for index, uploaded_file in enumerate(uploaded_files, start=1):
            source_name = str(getattr(uploaded_file, "name", "source"))
            try:
                result = process_price_source(
                    access,
                    department="",
                    uploaded_file=uploaded_file,
                    source_url="",
                    trace=trace,
                    client=client,
                    owner_authorized=False,
                    batch_source_ids=prior_batch_source_ids,
                )
                results.append(result)
                prior_batch_source_ids.add(str(result.source_id))
                _trace_event(
                    trace,
                    "server.price_source_batch_source_finished",
                    job_id=job_id,
                    source_index=index,
                    source_name=source_name,
                )
            except Exception as exc:
                logger.exception("Price source batch input failed: %s", source_name)
                failed_source_names.append(source_name)
                _trace_event(
                    trace,
                    "server.price_source_batch_source_finished",
                    status="error",
                    job_id=job_id,
                    source_index=index,
                    source_name=source_name,
                    error_type=type(exc).__name__,
                    error_message=_bounded_error_message(exc),
                )
        if not results:
            raise PriceSourceError("No selected source could be processed.")
        return PriceSourceBatchProcessResult(
            results=tuple(results),
            failed_source_names=tuple(failed_source_names),
        )
    finally:
        _trace_event(
            trace,
            "server.price_source_batch_worker_finished",
            job_id=job_id,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
            processed_source_count=len(results),
            failed_source_count=len(failed_source_names),
        )
        lock.release()


def _run_price_source_purge_job(*, access, source_id: str, trace=None, job_id: str):
    started_at = time.perf_counter()
    _trace_event(
        trace,
        "server.price_source_purge_worker_started",
        job_id=job_id,
        source_id=source_id,
    )
    try:
        result = purge_price_source(access, source_id)
        _trace_event(
            trace,
            "server.price_source_purge_worker_finished",
            job_id=job_id,
            source_id=source_id,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )
        return result
    except Exception as exc:
        _trace_event(
            trace,
            "server.price_source_purge_worker_finished",
            status="error",
            job_id=job_id,
            source_id=source_id,
            error_type=type(exc).__name__,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )
        raise
