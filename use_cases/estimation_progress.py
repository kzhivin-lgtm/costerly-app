from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4
import logging


_LOCK = Lock()
_PROGRESS: dict[str, dict[str, Any]] = {}

# Completed work, shared by the worker and the existing display interpolator.
# No elapsed-time interpolation may reach the next unconfirmed milestone.
ESTIMATION_STAGES = {
    "inputs_ready": 15, "geometry_ready": 20, "understanding_ready": 45,
    "locators_ready": 60, "inventory_ready": 75, "block_geometry_ready": 80,
    "parts_ready": 85, "materials_ready": 88, "parts_check_ready": 90,
    "demand_published": 94, "assumptions_checked": 96,
    "allocations_published": 98, "plan_published": 99,
}


def report_estimation_stage(callback, stage: str) -> None:
    """Progress is best effort and must never fail an otherwise valid calculation."""
    if callback is not None:
        try:
            callback(stage)
        except Exception:
            logging.getLogger(__name__).exception("Could not report estimation stage %s", stage)


def begin_estimate_progress(estimate_id: str, object_ids: list[str]) -> str:
    """Own one worker generation, rejecting late receipts from an older launch."""
    token = uuid4().hex
    with _LOCK:
        _PROGRESS[estimate_id] = {"token": token, "active": True, "objects": {
            oid: {"object_id": oid, "percent": 15, "status": "running",
                  "updated_at": datetime.now(UTC).isoformat()} for oid in object_ids
        }}
    return token


def set_estimate_stage(estimate_id: str, token: str, stage: str) -> None:
    """Update the whole active batch in memory, without additional durable I/O."""
    percent = ESTIMATION_STAGES[stage]
    with _LOCK:
        current = _PROGRESS.get(estimate_id)
        if not current or current.get("token") != token or not current.get("active"):
            return
        for row in current["objects"].values():
            if row["status"] == "running" and percent > row["percent"]:
                row.update(percent=percent, updated_at=datetime.now(UTC).isoformat())


def finish_estimate_progress(estimate_id: str, token: str) -> None:
    with _LOCK:
        current = _PROGRESS.get(estimate_id)
        if current and current.get("token") == token:
            current["active"] = False


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
        current = _PROGRESS.setdefault(estimate_id, {"objects": {}})
        previous = current["objects"].get(object_id)
        percent = max(0, min(99 if status == "running" else 100, int(percent)))
        if previous and (previous["status"] != "running" or (
                status == "running" and percent <= previous["percent"])):
            return
        current["objects"][object_id] = {
            "object_id": object_id,
            "percent": percent,
            "status": status,
            "updated_at": datetime.now(UTC).isoformat(),
        }


def get_estimate_progress(estimate_id: str | None) -> dict[str, Any] | None:
    if not estimate_id:
        return None
    with _LOCK:
        current = _PROGRESS.get(estimate_id)
        if not current:
            return None
        rows = {oid: dict(row) for oid, row in current["objects"].items()}
        # Keep the legacy single-object projection for existing consumers.
        return {**next(reversed(rows.values()), {}), "objects": rows, "active": current.get("active", False)}


def clear_estimate_progress(estimate_id: str | None) -> None:
    if not estimate_id:
        return
    with _LOCK:
        _PROGRESS.pop(estimate_id, None)
