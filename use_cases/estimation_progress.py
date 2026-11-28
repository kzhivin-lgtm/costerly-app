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
    "inputs_ready": 5, "geometry_ready": 8, "understanding_ready": 40,
    "locators_ready": 50, "inventory_ready": 65, "block_geometry_ready": 66,
    "parts_ready": 67, "material_context_ready": 74, "material_plan_ready": 82,
    "materials_ready": 88, "parts_check_ready": 90,
    "demand_published": 94, "assumptions_checked": 96,
    "allocations_published": 98, "plan_published": 99,
}


def progress_display_curve(base: int) -> tuple[int, float]:
    cap = next((mark - 1 for mark in ESTIMATION_STAGES.values() if mark > base), 99)
    return cap, 6.0 if base >= 98 else 3.0 if base >= 90 else 1.0


def progress_display_value(base: int, elapsed: float, display_from: int | None = None) -> int:
    """Catch up to real receipts at two points/second, then interpolate their band.

    The existing fragment drives this pure function. Completion never waits
    for animation, and elapsed time cannot confirm an unfinished milestone.
    """
    base = max(0, min(99, base))
    cap, seconds = progress_display_curve(base)
    start = base if display_from is None else max(0, min(base, display_from))
    catchup = (base - start) * .5
    elapsed = max(0.0, elapsed)
    if elapsed < catchup:
        return min(base, start + int(elapsed / .5))
    pending_age = elapsed - catchup
    if 67 <= base < 90:
        # Catalog reads, material selection and nesting have variable duration.
        # Approach the next real receipt gradually instead of spending their
        # short band in a few seconds and sitting at its last integer.
        band = cap - base + 1
        return min(cap, base + int(band * pending_age / (pending_age + 6.0)))
    return min(cap, base + int(pending_age / seconds))


def _advance_progress(row: dict[str, Any], percent: int, now: datetime) -> None:
    previous_age = max(0.0, (now - datetime.fromisoformat(row["updated_at"])).total_seconds())
    visible = progress_display_value(row["percent"], previous_age, row.get("display_from"))
    row.update(percent=percent, display_from=visible, updated_at=now.isoformat())


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
            oid: {"object_id": oid, "percent": ESTIMATION_STAGES["inputs_ready"], "status": "running",
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
                _advance_progress(row, percent, datetime.now(UTC))


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
        if previous and status == "running":
            _advance_progress(previous, percent, datetime.now(UTC))
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
