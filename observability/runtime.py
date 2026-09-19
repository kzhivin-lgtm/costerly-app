from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
import json
import logging
import queue
import re
import threading
import time
from typing import Any
from uuid import UUID, uuid4

import httpx


logger = logging.getLogger("costerly.runtime")
logger.setLevel(logging.INFO)

OBSERVABILITY_SCHEMA_VERSION = "runtime_v1"
DEFAULT_BUILD_VERSION = "3.1.1"
_QUEUE: queue.Queue[dict[str, object]] = queue.Queue(maxsize=1000)
_SINK_LOCK = threading.Lock()
_SINK_URL: str | None = None
_SINK_KEY: str | None = None
_WORKER_THREAD: threading.Thread | None = None
_BLOCKED_KEY_PARTS = ("token", "password", "secret", "email", "file", "content")
_SAFE_TECHNICAL_KEYS = {"dom_content_loaded_ms"}
_SAFE_NAME = re.compile(r"^[a-z0-9_.:-]{1,80}$")


def configure_runtime_sink(url: str | None, service_role_key: str | None) -> None:
    """Configure the durable sink once without making the render path wait on it."""
    global _SINK_URL, _SINK_KEY
    if not url or not service_role_key:
        return
    with _SINK_LOCK:
        _SINK_URL = url.rstrip("/") + "/rest/v1/app_runtime_events"
        _SINK_KEY = service_role_key
        _start_worker_locked()


def valid_trace_id(value: object) -> str | None:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def _safe_name(value: object, fallback: str) -> str:
    text = str(value or "").strip().lower()
    return text if _SAFE_NAME.fullmatch(text) else fallback


def _safe_metadata(metadata: Mapping[str, object] | None) -> dict[str, object]:
    safe: dict[str, object] = {}
    for raw_key, value in (metadata or {}).items():
        key = str(raw_key)[:80]
        if key.lower() not in _SAFE_TECHNICAL_KEYS and any(
            part in key.lower() for part in _BLOCKED_KEY_PARTS
        ):
            safe[key] = "[redacted]"
        elif value is None or isinstance(value, (bool, int, float)):
            safe[key] = value
        elif isinstance(value, str):
            safe[key] = value[:300]
        else:
            safe[key] = str(value)[:300]
    return safe


def _start_worker_locked() -> None:
    global _WORKER_THREAD
    if _WORKER_THREAD is not None and _WORKER_THREAD.is_alive():
        return
    _WORKER_THREAD = threading.Thread(
        target=_runtime_worker,
        name="costerly-runtime-events",
        daemon=True,
    )
    _WORKER_THREAD.start()


def _enqueue(event: dict[str, object]) -> None:
    logger.info("runtime_event %s", json.dumps(event, separators=(",", ":"), sort_keys=True))
    with _SINK_LOCK:
        sink_configured = bool(_SINK_URL and _SINK_KEY)
    if not sink_configured:
        return
    try:
        _QUEUE.put_nowait(event)
    except queue.Full:
        logger.warning("runtime_event_dropped reason=queue_full")


def _persist_next_batch() -> None:
    first = _QUEUE.get()
    batch = [first]
    deadline = time.monotonic() + 0.15
    while len(batch) < 50:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            batch.append(_QUEUE.get(timeout=remaining))
        except queue.Empty:
            break

    try:
        with _SINK_LOCK:
            sink_url = _SINK_URL
            sink_key = _SINK_KEY
        if sink_url and sink_key:
            try:
                httpx.post(
                    sink_url,
                    headers={
                        "apikey": sink_key,
                        "authorization": f"Bearer {sink_key}",
                        "content-type": "application/json",
                        "prefer": "return=minimal",
                    },
                    json=batch,
                    timeout=2.0,
                ).raise_for_status()
            except Exception as exc:
                logger.warning("runtime_event_persist_failed count=%s error=%s", len(batch), exc)
    finally:
        for _event in batch:
            _QUEUE.task_done()


def _runtime_worker() -> None:
    while True:
        try:
            _persist_next_batch()
        except Exception:
            logger.exception("runtime_event_worker_recovered")
            time.sleep(0.1)


class RuntimeTrace:
    def __init__(
        self,
        *,
        trace_id: str,
        session_id: str,
        run_id: str,
        screen: str,
        started_at: float,
        build_version: str = DEFAULT_BUILD_VERSION,
    ) -> None:
        self.trace_id = trace_id
        self.session_id = session_id
        self.run_id = run_id
        self.screen = screen
        self.started_at = started_at
        self.build_version = build_version

    def set_screen(self, screen: str) -> None:
        self.screen = _safe_name(screen, "unknown")

    def event(
        self,
        name: str,
        *,
        status: str = "ok",
        duration_ms: float | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        event: dict[str, object] = {
            "occurred_at": datetime.now(UTC).isoformat(),
            "schema_version": OBSERVABILITY_SCHEMA_VERSION,
            "build_version": self.build_version,
            "source": "server",
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "event_name": _safe_name(name, "invalid_event"),
            "screen": self.screen,
            "status": _safe_name(status, "unknown"),
            "elapsed_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
            "metadata": _safe_metadata(metadata),
        }
        if duration_ms is not None:
            event["duration_ms"] = round(max(0.0, float(duration_ms)), 3)
        _enqueue(event)

    @contextmanager
    def span(self, name: str, **metadata: object) -> Iterator[None]:
        started_at = time.perf_counter()
        try:
            yield
        except Exception as exc:
            self.event(
                name,
                status="error",
                duration_ms=(time.perf_counter() - started_at) * 1000,
                metadata={**metadata, "error_type": type(exc).__name__},
            )
            raise
        else:
            self.event(
                name,
                duration_ms=(time.perf_counter() - started_at) * 1000,
                metadata=metadata,
            )


def new_runtime_trace(
    *,
    session_state: Any,
    requested_trace_id: object,
    screen: str,
    started_at: float,
    build_version: str = DEFAULT_BUILD_VERSION,
) -> RuntimeTrace:
    trace_id = valid_trace_id(requested_trace_id)
    if trace_id is None:
        trace_id = valid_trace_id(session_state.get("_runtime_trace_id")) or str(uuid4())
    session_state._runtime_trace_id = trace_id
    session_id = valid_trace_id(session_state.get("_runtime_session_id")) or str(uuid4())
    session_state._runtime_session_id = session_id
    return RuntimeTrace(
        trace_id=trace_id,
        session_id=session_id,
        run_id=str(uuid4()),
        screen=_safe_name(screen, "unknown"),
        started_at=started_at,
        build_version=build_version,
    )
