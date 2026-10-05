"""Background runtime for one company's Price Source extraction."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
import time
from typing import Any
from uuid import uuid4

from agents.anthropic_adapter import get_secret
from db.supabase_client import get_supabase_client
from use_cases.price_sources import PriceSourceError, process_price_source


_PRICE_SOURCE_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="price-source-extraction",
)
_LOCKS_GUARD = Lock()
_COMPANY_LOCKS: dict[str, Lock] = {}


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


def submit_price_source_job(
    *,
    access,
    uploaded_file,
    source_url: str,
    trace=None,
) -> Future:
    """Start one company-scoped extraction without holding the UI request open."""
    # Prime Streamlit-bound resources on the request thread. The worker then
    # reads cached credentials and uses the same safe Supabase-client pattern
    # as background Estimation.
    if not get_secret("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is missing.")
    get_supabase_client()
    job_id = str(uuid4())
    _trace_event(trace, "server.price_source_job_submitted", job_id=job_id)
    return _PRICE_SOURCE_EXECUTOR.submit(
        _run_price_source_job,
        access=access,
        uploaded_file=uploaded_file,
        source_url=source_url,
        trace=trace,
        job_id=job_id,
    )


def _run_price_source_job(
    *, access, uploaded_file, source_url: str, trace=None, job_id: str
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
