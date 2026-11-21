from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any


_LOCK = Lock()
_PROGRESS: dict[str, dict[str, Any]] = {}


@dataclass
class EstimationCycle:
    """One accepted launch and the first Objects render of each usable action."""

    started_at: float
    ready_seconds: dict[str, float] = field(default_factory=dict)
    total_seconds: float | None = None
    worker_finished: bool = False
    worker_failed: bool = False
    cost_usd: float | None = None

    def observe(self, now: float, *, ready_ids: list[str], all_terminal: bool) -> float:
        # A later render can show active work again. A historical ready frame
        # is not the current terminal state, so revoke its timing receipt.
        if not all_terminal and not self.worker_failed:
            self.total_seconds = None
        active_ready = set(ready_ids)
        self.ready_seconds = {key: value for key, value in self.ready_seconds.items() if key in active_ready}
        if self.total_seconds is not None:
            return self.total_seconds
        elapsed = max(0.0, now - self.started_at)
        for object_id in ready_ids:
            self.ready_seconds.setdefault(object_id, elapsed)
        if self.worker_finished and (all_terminal or self.worker_failed):
            self.total_seconds = elapsed
        return elapsed


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
