from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")

_TRANSIENT_ERROR_MARKERS = (
    "resource temporarily unavailable",
    "temporarily unavailable",
    "timed out",
    "timeout",
    "connection reset",
    "connection aborted",
    "connection refused",
    "bad gateway",
    "service unavailable",
    "gateway timeout",
    "errno 11",
    "502",
    "503",
    "504",
)


def is_transient_error(exc: Exception) -> bool:
    """Return whether an exception looks like a temporary network/backend issue."""
    message = str(exc).lower()
    return any(marker in message for marker in _TRANSIENT_ERROR_MARKERS)


def read_with_retry(operation: Callable[[], T], *, attempts: int = 3) -> T:
    """Retry transient read failures without hiding persistent data errors."""
    last_error: Exception | None = None
    delays = (0.2, 0.5)

    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            if not is_transient_error(exc) or attempt >= attempts - 1:
                raise
            last_error = exc
            time.sleep(delays[min(attempt, len(delays) - 1)])

    if last_error:
        raise last_error
    raise RuntimeError("Retry operation failed without an exception.")
