"""Background runtime for one company's Price Source extraction."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock

from agents.anthropic_adapter import get_secret
from db.supabase_client import get_supabase_client
from use_cases.price_sources import PriceSourceError, process_price_source


_PRICE_SOURCE_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="price-source-extraction",
)
_LOCKS_GUARD = Lock()
_COMPANY_LOCKS: dict[str, Lock] = {}


def _company_lock(company_id: str) -> Lock:
    with _LOCKS_GUARD:
        return _COMPANY_LOCKS.setdefault(company_id, Lock())


def submit_price_source_job(
    *,
    access,
    uploaded_file,
    source_url: str,
) -> Future:
    """Start one company-scoped extraction without holding the UI request open."""
    # Prime Streamlit-bound resources on the request thread. The worker then
    # reads cached credentials and uses the same safe Supabase-client pattern
    # as background Estimation.
    if not get_secret("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is missing.")
    get_supabase_client()
    return _PRICE_SOURCE_EXECUTOR.submit(
        _run_price_source_job,
        access=access,
        uploaded_file=uploaded_file,
        source_url=source_url,
    )


def _run_price_source_job(*, access, uploaded_file, source_url: str):
    company_id = str(access.company_id)
    lock = _company_lock(company_id)
    if not lock.acquire(blocking=False):
        raise PriceSourceError("Another price extraction is already running. Try again when it finishes.")
    try:
        return process_price_source(
            access,
            department="",
            uploaded_file=uploaded_file,
            source_url=source_url,
            trace=None,
            # Get a fresh client from the background-safe cached factory.
            client=get_supabase_client(),
        )
    finally:
        lock.release()
