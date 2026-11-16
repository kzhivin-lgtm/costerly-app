from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
import json
import logging
import queue
import re
import threading
import time
from pathlib import Path
from traceback import walk_tb
from typing import Any
from uuid import UUID, uuid4

import httpx


logger = logging.getLogger("costerly.runtime")
logger.setLevel(logging.INFO)

OBSERVABILITY_SCHEMA_VERSION = "runtime_v1"
DEFAULT_BUILD_VERSION = "3.2.3"
_ROOT = Path(__file__).resolve().parents[1]
_ACTIVE_TRACE: ContextVar[RuntimeTrace | None] = ContextVar("costerly_runtime_trace", default=None)
_QUEUE: queue.Queue[dict[str, object]] = queue.Queue(maxsize=1000)
_SINK_LOCK = threading.Lock()
_SINK_URL: str | None = None
_SINK_KEY: str | None = None
_WORKER_THREAD: threading.Thread | None = None
_APPLICATION_LOG_HANDLER: logging.Handler | None = None
_SERVICE_BUILD_VERSION = DEFAULT_BUILD_VERSION
_BLOCKED_KEY_WORDS = {"token", "password", "secret", "email", "file", "filename", "content"}
_SAFE_TECHNICAL_KEYS = {"dom_content_loaded_ms"}
_SAFE_NAME = re.compile(r"^[a-z0-9_.:-]{1,80}$")
_WORKFLOW_ID = re.compile(r"^[A-Za-z0-9_-]{1,160}$")
_SERVICE_ERROR_CODE = re.compile(r"^(?:[0-9A-Z]{5}|PGRST[0-9]{3})$")
_EVENT_STATUSES = {"ok", "error", "timeout", "dropped", "unknown"}
_PERSIST_ATTEMPTS = 3


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
        normalized_key = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key).lower()
        key_words = set(re.findall(r"[a-z0-9]+", normalized_key))
        if key.lower() not in _SAFE_TECHNICAL_KEYS and key_words & _BLOCKED_KEY_WORDS:
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
    level = logging.ERROR if event["status"] == "error" else logging.INFO
    logger.log(level, "runtime_event %s", json.dumps(event, separators=(",", ":"), sort_keys=True))
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
            _post_batch_with_retry(sink_url, sink_key, batch)
    finally:
        for _event in batch:
            _QUEUE.task_done()


def _post_batch_with_retry(
    sink_url: str, sink_key: str, batch: list[dict[str, object]]
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, _PERSIST_ATTEMPTS + 1):
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
            if attempt > 1:
                logger.info(
                    "runtime_event_persist_recovered count=%s attempt=%s",
                    len(batch),
                    attempt,
                )
            return
        except Exception as exc:
            last_error = exc
            if isinstance(exc, httpx.HTTPStatusError) and 400 <= exc.response.status_code < 500:
                if exc.response.status_code not in {408, 429}:
                    break
            if attempt < _PERSIST_ATTEMPTS:
                time.sleep(0.1 * attempt)
    logger.warning(
        "runtime_event_persist_failed count=%s attempts=%s error_type=%s http_status=%s",
        len(batch),
        attempt,
        type(last_error).__name__ if last_error else "Unknown",
        last_error.response.status_code if isinstance(last_error, httpx.HTTPStatusError) else None,
    )


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
        session_id: str | None,
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
        self._summary: dict[str, object] = {}
        self._workflow: dict[str, str] = {}
        self._last_failures: dict[str, float] = {}

    def set_screen(self, screen: str) -> None:
        self.screen = _safe_name(screen, "unknown")

    def set_workflow(self, state: Any) -> None:
        self._workflow = _workflow_ids(
            rfq_run_id=state.get("current_run_id"),
            estimate_id=state.get("current_estimate_id"),
            object_id=state.get("current_object_id"),
        )

    def annotate(self, **metadata: object) -> None:
        self._summary.update(_safe_metadata(metadata))

    def summary(self) -> dict[str, object]:
        return {
            **self._summary,
            "server_elapsed_ms": round(
                (time.perf_counter() - self.started_at) * 1000,
                3,
            ),
        }

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
            "status": status if status in _EVENT_STATUSES else "unknown",
            "elapsed_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
            "duration_ms": None,
            "metadata": {**self._workflow, **_safe_metadata(metadata)},
        }
        if duration_ms is not None:
            rounded_duration = round(max(0.0, float(duration_ms)), 3)
            event["duration_ms"] = rounded_duration
            summary_key = name.removeprefix("server.").replace(".", "_") + "_ms"
            self._summary[_safe_name(summary_key, "phase_ms")] = rounded_duration
        _enqueue(event)

    def failure(
        self, event: str, error: Exception | None = None, *,
        stage: str, duration_ms: float | None = None, repeat_window: float = 0,
        **workflow: object,
    ) -> None:
        details = {"stage": _safe_name(stage, "unknown"), **_exception_details(error), **_workflow_ids(**workflow)}
        if repeat_window:
            key = json.dumps([event, details], sort_keys=True)
            now = time.monotonic()
            if now - self._last_failures.get(key, float("-inf")) < repeat_window:
                return
            self._last_failures = {k: ts for k, ts in self._last_failures.items() if now - ts < repeat_window}
            self._last_failures[key] = now
        self.event(event, status="error", duration_ms=duration_ms, metadata=details)

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
                metadata={**metadata, **_exception_details(exc)},
            )
            raise
        else:
            self.event(
                name,
                duration_ms=(time.perf_counter() - started_at) * 1000,
                metadata=metadata,
            )


def _workflow_ids(**values: object) -> dict[str, str]:
    return {key: value for key, value in values.items() if key in {"rfq_run_id", "estimate_id", "object_id"}
            and isinstance(value, str) and _WORKFLOW_ID.fullmatch(value)}


def _exception_details(error: Exception | None) -> dict[str, object]:
    """Retain the type and application call sites without exception text or locals."""
    if error is None:
        return {}
    result = {"error_type": type(error).__name__}
    locations = []
    seen = set()
    current: BaseException | None = error
    for _ in range(4):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        for frame, line in walk_tb(current.__traceback__):
            path = Path(frame.f_code.co_filename)
            if path.is_relative_to(_ROOT):
                relative = path.relative_to(_ROOT)
                if relative.parts and relative.parts[0] not in {".venv", "venv"}:
                    locations.append(f"{relative.as_posix()}:{line}:{frame.f_code.co_name}")
        code = getattr(current, "code", None)
        if isinstance(code, str) and _SERVICE_ERROR_CODE.fullmatch(code):
            result["error_code"] = code
        status = getattr(current, "status_code", None)
        if isinstance(current, httpx.HTTPStatusError):
            status = current.response.status_code
        if isinstance(status, int) and 100 <= status <= 599:
            result["http_status"] = status
        if current is not error:
            result["cause_type"] = type(current).__name__
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    if locations:
        result["error_at"] = " > ".join(list(dict.fromkeys(locations))[-3:])
    return result


@contextmanager
def runtime_trace_scope(trace: RuntimeTrace | None) -> Iterator[None]:
    token = _ACTIVE_TRACE.set(trace)
    try:
        yield
    finally:
        _ACTIVE_TRACE.reset(token)


def current_runtime_trace(state: Any = None) -> RuntimeTrace | None:
    trace = _ACTIVE_TRACE.get()
    return trace if trace is not None or state is None else state.get("_runtime_error_trace")


def _background_trace() -> RuntimeTrace:
    return RuntimeTrace(trace_id=str(uuid4()), session_id=None, run_id=str(uuid4()), screen="background",
                        started_at=time.perf_counter(), build_version=_SERVICE_BUILD_VERSION)


class _ApplicationErrorLog(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Exclude our own sink logger and third-party library logs.
        if not record.name.startswith(("screens.", "use_cases.", "db.", "state.", "agents.")):
            return
        try:
            self._record_error(record)
        except Exception:
            # Telemetry must never replace the original application error.
            return

    def _record_error(self, record: logging.LogRecord) -> None:
        trace = current_runtime_trace() or _background_trace()
        parsed = record.exc_info[1] if record.exc_info else None
        error = parsed if isinstance(parsed, Exception) else None
        metadata = {"stage": _safe_name(record.name, "application"), **_exception_details(error)}
        if "error_at" not in metadata:
            path = Path(record.pathname)
            if path.is_relative_to(_ROOT):
                metadata["error_at"] = f"{path.relative_to(_ROOT).as_posix()}:{record.lineno}:{record.funcName}"
        trace.event("server.application_error", status="error", metadata=metadata)


def install_application_error_logging(build_version: str) -> None:
    """Mirror existing errors to runtime events without storing raw log messages."""
    global _APPLICATION_LOG_HANDLER, _SERVICE_BUILD_VERSION
    with _SINK_LOCK:
        _SERVICE_BUILD_VERSION = build_version
        if _APPLICATION_LOG_HANDLER is None:
            _APPLICATION_LOG_HANDLER = _ApplicationErrorLog(level=logging.ERROR)
            logging.getLogger().addHandler(_APPLICATION_LOG_HANDLER)


def report_runtime_failure(stage: str, error: Exception | None = None, *,
                           trace: RuntimeTrace | None = None, **context: Any) -> None:
    trace = trace or current_runtime_trace() or _background_trace()
    trace.failure("server.operation_failed", error, stage=stage, **context)


def submit_observed(executor, stage: str, callback, /, *args, **kwargs):
    """Observe a real worker failure even if the user closes the tab."""
    trace = current_runtime_trace() or _background_trace()
    ids = _workflow_ids(rfq_run_id=kwargs.get("run_id"), estimate_id=kwargs.get("estimate_id"),
                        object_id=kwargs.get("object_id"))

    @wraps(callback)
    def run(*work_args, **work_kwargs):
        with runtime_trace_scope(trace):
            try:
                return callback(*work_args, **work_kwargs)
            except Exception as error:
                report_runtime_failure(stage, error, **ids)
                raise

    return executor.submit(run, *args, **kwargs)


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


def emit_completed_action(session_state: Any, trace: RuntimeTrace) -> None:
    """Attach a completed action from the preceding rerun to the new trace."""
    completed = session_state.pop("_runtime_completed_action", None)
    if not isinstance(completed, dict):
        return
    action = str(completed.get("action") or "unknown")
    status = str(completed.get("status") or "unknown")
    metadata = {"action": action}
    for key in ("error_type", "error_code"):
        value = completed.get(key)
        if value:
            metadata[key] = str(value)[:120]
    phase_durations = completed.get("phase_durations_ms")
    if isinstance(phase_durations, Mapping):
        safe_durations = {
            _safe_name(key, "phase_ms"): round(max(0.0, float(value)), 3)
            for key, value in phase_durations.items()
            if isinstance(value, (int, float))
        }
        metadata.update(safe_durations)
        trace.annotate(**safe_durations)
    trace.annotate(completed_action=action, completed_action_status=status)
    trace.event(
        "server.action_completed",
        status=status,
        duration_ms=float(completed.get("duration_ms") or 0),
        metadata=metadata,
    )
