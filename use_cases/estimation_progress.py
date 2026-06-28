from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any


_LOCK = Lock()
_PROGRESS: dict[str, dict[str, Any]] = {}


def set_object_progress(
    *,
    estimate_id: str,
    object_id: str,
    percent: int,
    status: str = "running",
) -> None:
    """Track in-process estimation progress for the active Streamlit worker."""
    with _LOCK:
        _PROGRESS[estimate_id] = {
            "object_id": object_id,
            "percent": max(0, min(100, int(percent))),
            "status": status,
            "updated_at": datetime.now(UTC).isoformat(),
        }


def get_estimate_progress(estimate_id: str | None) -> dict[str, Any] | None:
    if not estimate_id:
        return None
    with _LOCK:
        current = _PROGRESS.get(estimate_id)
        return dict(current) if current else None


def clear_estimate_progress(estimate_id: str | None) -> None:
    if not estimate_id:
        return
    with _LOCK:
        _PROGRESS.pop(estimate_id, None)
