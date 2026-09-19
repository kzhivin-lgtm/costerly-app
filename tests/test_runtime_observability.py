from __future__ import annotations

from pathlib import Path
import time

import pytest

from observability import runtime


ROOT = Path(__file__).parents[1]


def test_runtime_event_has_trace_boundaries_and_redacts_sensitive_metadata(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "_enqueue", captured.append)
    trace = runtime.RuntimeTrace(
        trace_id="11111111-1111-4111-8111-111111111111",
        session_id="22222222-2222-4222-8222-222222222222",
        run_id="33333333-3333-4333-8333-333333333333",
        screen="upload",
        started_at=time.perf_counter(),
    )

    trace.event(
        "server.test",
        duration_ms=12.3456,
        metadata={
            "route": "upload",
            "access_token": "must-not-leak",
            "email_address": "must-not-leak",
            "dom_content_loaded_ms": 123.4,
        },
    )

    assert len(captured) == 1
    event = captured[0]
    assert event["trace_id"] == trace.trace_id
    assert event["session_id"] == trace.session_id
    assert event["run_id"] == trace.run_id
    assert event["duration_ms"] == 12.346
    assert event["metadata"] == {
        "route": "upload",
        "access_token": "[redacted]",
        "email_address": "[redacted]",
        "dom_content_loaded_ms": 123.4,
    }


def test_runtime_span_records_error_type_without_error_message(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "_enqueue", captured.append)
    trace = runtime.RuntimeTrace(
        trace_id="11111111-1111-4111-8111-111111111111",
        session_id="22222222-2222-4222-8222-222222222222",
        run_id="33333333-3333-4333-8333-333333333333",
        screen="login",
        started_at=time.perf_counter(),
    )

    with pytest.raises(RuntimeError, match="private detail"):
        with trace.span("server.failure"):
            raise RuntimeError("private detail")

    assert captured[0]["status"] == "error"
    assert captured[0]["metadata"] == {"error_type": "RuntimeError"}
    assert "private detail" not in str(captured[0])


def test_runtime_summary_relays_safe_phase_metrics(monkeypatch):
    monkeypatch.setattr(runtime, "_enqueue", lambda _event: None)
    trace = runtime.RuntimeTrace(
        trace_id="11111111-1111-4111-8111-111111111111",
        session_id="22222222-2222-4222-8222-222222222222",
        run_id="33333333-3333-4333-8333-333333333333",
        screen="upload",
        started_at=time.perf_counter(),
    )
    trace.annotate(run_sequence=2, fast_resume="restored", access_token="hidden")
    trace.event("server.auth.access_lookup", duration_ms=12.3456)

    summary = trace.summary()
    assert summary["run_sequence"] == 2
    assert summary["fast_resume"] == "restored"
    assert summary["access_token"] == "[redacted]"
    assert summary["auth_access_lookup_ms"] == 12.346
    assert isinstance(summary["server_elapsed_ms"], float)


def test_completed_action_is_emitted_once_without_sensitive_values(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "_enqueue", captured.append)
    state = {
        "_runtime_completed_action": {
            "action": "auth_sign_in",
            "status": "ok",
            "duration_ms": 321.4567,
        }
    }
    trace = runtime.RuntimeTrace(
        trace_id="10000000-0000-4000-8000-000000000001",
        session_id="10000000-0000-4000-8000-000000000002",
        run_id="10000000-0000-4000-8000-000000000003",
        screen="login",
        started_at=time.perf_counter(),
    )

    runtime.emit_completed_action(state, trace)
    runtime.emit_completed_action(state, trace)

    assert "_runtime_completed_action" not in state
    assert len(captured) == 1
    assert captured[0]["event_name"] == "server.action_completed"
    assert captured[0]["duration_ms"] == 321.457
    assert captured[0]["metadata"] == {"action": "auth_sign_in"}
    assert trace.summary()["completed_action"] == "auth_sign_in"
    assert trace.summary()["completed_action_status"] == "ok"


def test_runtime_persistence_retries_transient_failure(monkeypatch):
    attempts = []

    class Response:
        def raise_for_status(self):
            if len(attempts) < 3:
                raise RuntimeError("transient private detail")

    def post(*_args, **_kwargs):
        attempts.append(1)
        return Response()

    monkeypatch.setattr(runtime.httpx, "post", post)
    monkeypatch.setattr(runtime.time, "sleep", lambda _seconds: None)

    runtime._post_batch_with_retry(
        "https://example.invalid/rest/v1/app_runtime_events",
        "private-key",
        [{"event_name": "server.test"}],
    )

    assert len(attempts) == 3


def test_observability_sql_is_service_role_only_and_indexed():
    sql = (ROOT / "db/sql/2026_09_19_app_runtime_events.sql").read_text().lower()
    assert "create table if not exists public.app_runtime_events" in sql
    assert "enable row level security" in sql
    assert "app_runtime_events_trace_idx" in sql
    assert "create policy" not in sql
    assert "grant " not in sql


def test_cloudflare_wrapper_emits_non_blocking_correlated_timeline():
    wrapper = (ROOT / "cloudflare/index.html").read_text()
    function = (ROOT / "cloudflare/functions/api/runtime-events.js").read_text()
    routes = (ROOT / "cloudflare/_routes.json").read_text()

    assert 'data-src="https://costerly-app.streamlit.app/?embed=true"' in wrapper
    assert 'appUrl.searchParams.set("obs_trace", traceId)' in wrapper
    assert "navigator.sendBeacon" in wrapper
    assert 'event.data.traceId === traceId' in wrapper
    assert 'event.origin === "https://costerly-app.streamlit.app"' in wrapper
    assert "visibility: hidden" not in wrapper
    assert "readyRunIds" in wrapper
    assert 'event.data.type === "costerly:transition-click"' in wrapper
    assert 'event.data.type === "costerly:transition-visible"' in wrapper
    assert 'mark("browser.transition_visible"' in wrapper
    assert 'mark("browser.transition_ready"' in wrapper
    assert 'metadata.completed_action === "auth_sign_in"' in wrapper
    assert 'metadata.completed_action_status === "error"' in wrapper
    assert 'status: failedSignIn ? "error" : "ok"' in wrapper
    assert 'event.data.type === "costerly:startup-phase"' in wrapper
    assert "startupPhases.has(event.data.phase)" in wrapper
    assert "...(event.data.metrics || {})" in wrapper
    assert 'startupProbe === "anonymous"' in wrapper
    assert 'appUrl.searchParams.set("startup_probe", "anonymous")' in wrapper
    assert 'key.toLowerCase() !== "dom_content_loaded_ms"' in function
    assert "SUPABASE_SERVICE_ROLE_KEY" in function
    assert 'request.headers.get("origin")' in function
    assert 'request.method !== "POST"' in function
    assert "new TextEncoder().encode(body).byteLength" in function
    assert "onRequestPost" not in function
    assert '"include": ["/api/*"]' in routes
    assert "must-not-leak" not in wrapper + function


def test_auth_component_reports_safe_iframe_startup_phases():
    component = (
        ROOT / "ui/browser_session_component/index.html"
    ).read_text()

    assert 'window.parent.performance.getEntriesByType("navigation")' in component
    assert 'type: "costerly:startup-phase"' in component
    assert 'startupPhase(args, "auth_component_script"' in component
    assert 'startupPhase(args, "auth_component_render"' in component
    assert 'startupPhase(args, "auth_storage_read"' in component
    assert 'startupPhase(args, "auth_value_sent"' in component
    assert "preventDefault" not in component

    ready_signal = (ROOT / "ui/js_guards.py").read_text()
    assert 'type: "costerly:transition-click"' in ready_signal
    assert 'type: "costerly:transition-visible"' in ready_signal
    assert "new MutationObserver(reportIfVisible)" in ready_signal
    assert 'parentDocument.addEventListener("click", handler, {' in ready_signal
    assert "capture: false" in ready_signal
    assert "passive: true" in ready_signal
    observer_source = ready_signal.split("function installTransitionObserver()", 1)[1].split(
        "function postReady()", 1
    )[0]
    assert "preventDefault" not in observer_source
    assert "access_token" not in component
    assert "refresh_token" not in component


def test_scroll_reset_component_stays_out_of_main_layout(monkeypatch):
    from ui import js_guards

    class Sidebar:
        active = False

        def __enter__(self):
            self.active = True

        def __exit__(self, *_args):
            self.active = False

    sidebar = Sidebar()
    calls = []

    def render_component(*_args, **kwargs):
        assert sidebar.active is True
        calls.append(kwargs)

    monkeypatch.setattr(js_guards.st, "sidebar", sidebar)
    monkeypatch.setattr(js_guards.components, "html", render_component)

    js_guards.scroll_parent_to_top()

    assert calls == [{"height": 0, "width": 0}]
