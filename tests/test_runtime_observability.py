from __future__ import annotations

from pathlib import Path
import re
import time

import pytest

from observability import runtime


ROOT = Path(__file__).parents[1]


def test_streamlit_and_cloudflare_build_versions_match():
    app_source = (ROOT / "app.py").read_text()
    wrapper = (ROOT / "cloudflare/index.html").read_text()

    app_version = re.search(r'build_version="([^"]+)"', app_source)
    wrapper_version = re.search(r'const BUILD_VERSION = "([^"]+)"', wrapper)

    assert app_version is not None
    assert wrapper_version is not None
    assert app_version.group(1) == wrapper_version.group(1)
    assert "COSTERLY_BUILD_VERSION" not in app_source


def test_wrapper_recovers_only_a_dropped_safe_header_target_after_deploy():
    wrapper = (ROOT / "cloudflare/index.html").read_text()

    assert 'screen === "upload"' in wrapper
    assert '["account", "admin", "projects"].includes(item.targetScreen)' in wrapper
    assert "!item.routeRecoveryAttempted" in wrapper
    assert 'mark("browser.transition_route_recovery"' in wrapper
    assert 'recoveryUrl.searchParams.set("screen", droppedHeaderTarget.targetScreen)' in wrapper
    assert "frame.src = recoveryUrl.toString();" in wrapper


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
            "refreshToken": "must-not-leak",
            "email_address": "must-not-leak",
            "file_name": "must-not-leak.pdf",
            "filename": "must-not-leak.pdf",
            "company_profile_import_ms": 1.25,
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
        "refreshToken": "[redacted]",
        "email_address": "[redacted]",
        "file_name": "[redacted]",
        "filename": "[redacted]",
        "company_profile_import_ms": 1.25,
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


def test_authenticated_upload_startup_keeps_phase_markers_for_the_cold_path():
    app_source = (ROOT / "app.py").read_text()
    auth_source = (ROOT / "state/company_auth.py").read_text()

    for marker in (
        "server.header_client_create",
        "server.platform_access_wait",
        "server.platform_access_query",
        "server.latest_estimate_wait",
        "server.latest_estimate_query",
    ):
        assert marker in app_source
    for marker in (
        "server.auth.rls_client_create",
        "server.auth.rls_membership_lookup",
        "server.auth.token_claim_parse",
        "server.auth.rls_access",
        "server.auth.fallback_client_create",
        "server.auth.session_refresh",
        "server.auth.get_user",
        "server.auth.membership_fallback_lookup",
    ):
        assert marker in auth_source


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


def test_completed_action_emits_safe_phase_durations(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "_enqueue", captured.append)
    state = {
        "_runtime_completed_action": {
            "action": "continue_to_objects",
            "status": "ok",
            "duration_ms": 321.4567,
            "phase_durations_ms": {
                "continue_seed_prepare_ms": 1.2,
                "continue_estimate_lookup_ms": 345.6789,
                "ignored": "not-a-number",
            },
        }
    }
    trace = runtime.RuntimeTrace(
        trace_id="10000000-0000-4000-8000-000000000001",
        session_id="10000000-0000-4000-8000-000000000002",
        run_id="10000000-0000-4000-8000-000000000003",
        screen="objects",
        started_at=time.perf_counter(),
    )

    runtime.emit_completed_action(state, trace)

    assert captured[0]["metadata"] == {
        "action": "continue_to_objects",
        "continue_seed_prepare_ms": 1.2,
        "continue_estimate_lookup_ms": 345.679,
    }
    assert trace.summary()["continue_estimate_lookup_ms"] == 345.679


def test_completed_action_emits_only_safe_provider_error_classification(monkeypatch):
    captured = []
    monkeypatch.setattr(runtime, "_enqueue", captured.append)
    state = {
        "_runtime_completed_action": {
            "action": "auth_password_updated",
            "status": "error",
            "duration_ms": 15,
            "error_type": "AuthApiError",
            "error_code": "weak_password",
            "password": "must-not-leak",
            "access_token": "must-not-leak",
        }
    }
    trace = runtime.RuntimeTrace(
        trace_id="10000000-0000-4000-8000-000000000001",
        session_id="10000000-0000-4000-8000-000000000002",
        run_id="10000000-0000-4000-8000-000000000003",
        screen="password_reset",
        started_at=time.perf_counter(),
    )

    runtime.emit_completed_action(state, trace)

    assert captured[0]["metadata"] == {
        "action": "auth_password_updated",
        "error_type": "AuthApiError",
        "error_code": "weak_password",
    }
    assert "must-not-leak" not in str(captured[0])


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

    assert 'data-src="https://core.costerly.ai/?embed=true"' in wrapper
    assert '"staging.costerly.ai": "https://core.costerly.ai/?embed=true"' in wrapper
    assert "const appOrigin = appUrl.origin" in wrapper
    assert 'appUrl.searchParams.set("obs_trace", traceId)' in wrapper
    assert 'const routeKeys = ["screen", "profile_tab", "run_id", "estimate_id", "object_id", "route_token"]' in wrapper
    assert "appUrl.searchParams.set(key, value)" in wrapper
    assert "function syncOuterRoute(route, renderedScreen)" in wrapper
    assert "window.history.pushState({costerlyRoute: true}" in wrapper
    assert 'window.addEventListener("popstate"' in wrapper
    assert "syncOuterRoute(event.data.route || {}, screen)" in wrapper
    assert 'const workflowPath = window.location.pathname.match(/^\\/([reo])\\/([A-Za-z0-9_-]{10,32})\\/?$/);' in wrapper
    assert 'nextUrl.pathname = `/${routePrefix}/${routeToken}`;' in wrapper
    assert "navigator.sendBeacon" in wrapper
    assert 'event.data.traceId === traceId' in wrapper
    assert "event.origin === appOrigin" in wrapper
    assert "visibility: hidden" not in wrapper
    assert "readyRunIds" in wrapper
    assert 'event.data.type === "costerly:transition-click"' in wrapper
    assert "sourceScreen: safeRouteValue(event.data.sourceScreen)" in wrapper
    assert "targetScreen: safeRouteValue(event.data.targetScreen)" in wrapper
    assert 'event.data.type === "costerly:transition-visible"' in wrapper
    assert 'event.data.type === "costerly:transition-stage"' in wrapper
    assert 'mark("browser.transition_visible"' in wrapper
    assert 'mark("browser.transition_ready"' in wrapper
    assert 'mark("browser.transition_timeout"' in wrapper
    assert 'concealInternalTransition(pendingTransition.name)' in wrapper
    assert '"upload_to_profile"' in wrapper
    assert '"profile_to_upload"' in wrapper
    assert '"upload_to_admin"' in wrapper
    assert '"profile_to_admin"' in wrapper
    assert '"admin_to_profile"' in wrapper
    assert '"admin_to_upload"' in wrapper
    assert '"profile_to_sign_out"' in wrapper
    assert '"upload_to_sign_out"' in wrapper
    assert '"processing_to_file_review"' in wrapper
    assert '"file_review_to_objects"' in wrapper
    assert '"objects_to_file_review"' in wrapper
    assert '"objects_to_object_detail"' in wrapper
    assert '"object_detail_to_objects"' in wrapper
    assert '"object_detail_approve_to_objects"' in wrapper
    assert '"upload_to_projects"' in wrapper
    assert '"projects_to_upload"' in wrapper
    assert '"back_to_upload"' in wrapper
    assert '"last_estimate"' in wrapper
    masked_transitions = wrapper.split("const maskedInternalTransitions = new Set([", 1)[1].split("]);", 1)[0]
    assert '"sign_in"' not in masked_transitions
    assert "maskedInternalTransitions.has(pendingTransition.name)" in wrapper
    assert "pendingTransition.readyReported = true" in wrapper
    assert "if (!maskedInternalTransitions.has(pendingTransition.name))" in wrapper
    assert "const loginTargetReady =" in wrapper
    assert "metadata.auth_css_ready === true" in wrapper
    assert 'source: "target_app_ready"' in wrapper
    assert 'mark("browser.internal_transition_timeout"' in wrapper
    internal_timeout_source = wrapper.split("function concealInternalTransition", 1)[1].split(
        "function revealInternalTransition", 1
    )[0]
    assert "10000" in internal_timeout_source
    assert 'window.setTimeout(() => mask.remove()' not in wrapper
    assert "iframe.is-transitioning" in wrapper
    assert ".app-loading-mask.is-transitioning" in wrapper
    assert "app-transition-status" not in wrapper
    assert "is-sign-in" not in wrapper
    assert 'metadata.completed_action === "auth_sign_in"' in wrapper
    assert 'metadata.completed_action_status === "error"' in wrapper
    assert 'status: failedSignIn ? "error" : "ok"' in wrapper
    assert 'event.data.type === "costerly:startup-phase"' in wrapper
    assert "startupPhases.has(event.data.phase)" in wrapper
    assert '"https://app.costerly.ai"' in function
    assert '"https://staging.costerly.ai"' in function
    assert 'allowedOrigins.has(request.headers.get("origin"))' in function
    assert "...(event.data.metrics || {})" in wrapper
    assert "event.data.buildVersion" in wrapper
    assert "event.data.metrics && event.data.metrics.server_build_version" in wrapper
    assert 'mark("browser.build_mismatch"' in wrapper
    assert 'window.sessionStorage.getItem(reloadGuardKey) !== mismatchPair' in wrapper
    assert "window.location.reload()" in wrapper
    assert "pythonRuns: 0" in wrapper
    assert "python_runs: pendingTransition.pythonRuns" in wrapper
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


def test_streamlit_ready_message_carries_server_build_version():
    source = (ROOT / "ui/js_guards.py").read_text()
    app_source = (ROOT / "app.py").read_text()

    assert "trace.annotate(server_build_version=trace.build_version)" in app_source
    assert "st.markdown(screen_transition_marker_html(screen), unsafe_allow_html=True)" in app_source
    assert "        build_version=trace.build_version,\n" not in app_source
    assert "build_version: str" not in source


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
    assert 'control.closest(".objects-pricing-review-button")' in ready_signal
    assert 'control.closest(".object-detail-footer-button--secondary")' in ready_signal
    assert 'control.closest(".st-key-header_last_estimate")' in ready_signal
    assert 'file_review_to_objects: "objects"' in ready_signal
    assert 'last_estimate: "file_review"' in ready_signal
    assert 'objects_to_file_review: "file_review"' in ready_signal
    assert "'upload_to_processing'" in ready_signal
    assert "'processing_to_file_review'" in ready_signal
    assert "type: 'costerly:transition-stage'" in ready_signal
    assert 'type: "costerly:transition-visible"' in ready_signal
    assert 'type: "costerly:transition-styled"' in ready_signal
    assert "new MutationObserver(reportIfVisible)" in ready_signal
    assert "const styledTargetReady = () =>" in ready_signal
    assert "function reportFileReviewStyled(transitionId)" in ready_signal
    assert "reportFileReviewStyled(transitionId);" in ready_signal
    assert 'transition === "upload_to_profile"' in ready_signal
    assert 'transition === "profile_to_upload"' in ready_signal
    assert 'transition === "upload_to_admin"' in ready_signal
    assert 'transition === "profile_to_admin"' in ready_signal
    assert 'transition === "admin_to_profile"' in ready_signal
    assert 'transition === "admin_to_upload"' in ready_signal
    assert 'parentDocument.querySelector(".platform-admin-heading")' in ready_signal
    assert 'parentDocument.querySelector(".platform-admin-table-card")' in ready_signal
    assert 'parentDocument.querySelector(".company-profile-heading")' in ready_signal
    assert 'headingStyle.minHeight === "56px"' in ready_signal
    assert 'parentDocument.querySelector(".upload-screen__hero")' in ready_signal
    assert "Number.parseFloat(heroStyle.fontSize) >= 20" in ready_signal
    assert "Number.parseFloat(dropzoneStyle.height) >= 180" in ready_signal
    assert "function releaseAuthShellWhenStable()" in ready_signal
    assert 'shell.dataset.costerlyStableRelease === "1"' in ready_signal
    assert "const stableForMs = 120;" in ready_signal
    assert "const failOpenMs = 450;" in ready_signal
    assert "observer.observe(targetApp, {" in ready_signal
    assert "quietForMs >= stableForMs" in ready_signal
    assert "parentWindow.requestAnimationFrame(releaseIfStable);" in ready_signal
    assert "parentWindow.setTimeout(removeOnce, failOpenMs);" in ready_signal
    assert "function authStylesReady()" in ready_signal
    assert 'parentWindow.getComputedStyle(form)' in ready_signal
    assert 'style.borderTopLeftRadius === "20px"' in ready_signal
    assert 'style.paddingTop === "30px"' in ready_signal
    assert "function announceWhenStyled()" in ready_signal
    assert "message.metrics.auth_css_ready = ready;" in ready_signal
    assert "message.metrics.auth_css_wait_ms" in ready_signal
    assert "announceWhenStyled();" in ready_signal
    post_ready_source = ready_signal.split("function postReady()", 1)[1].split(
        "installTransitionObserver();", 1
    )[0]
    assert "costerly-auth-sign-in-shell" not in post_ready_source
    assert 'parentDocument.addEventListener("click", handler, {' in ready_signal
    assert "capture: false" in ready_signal
    assert "passive: false" in ready_signal
    assert 'control.closest(".st-key-profile_to_upload")' in ready_signal
    assert 'label === "continue to upload" || label === "upload"' in ready_signal
    assert 'transition === "back_to_upload"' in ready_signal
    assert 'transition === "last_estimate"' in ready_signal
    assert 'return ".file-review-summary-card-marker"' in ready_signal
    assert 'cardStyle.borderTopLeftRadius === "16px"' in ready_signal
    assert 'const table = parentDocument.querySelector(".objects-pricing-table")' in ready_signal
    assert 'return ".object-detail-shell"' in ready_signal
    assert 'transition === "object_detail_to_objects"' in ready_signal
    assert 'parentWindow.scrollTo({ top: 0, left: 0, behavior: "auto" })' in ready_signal
    assert 'headerControls.querySelectorAll("button").length >= 2' in ready_signal
    observer_source = ready_signal.split("function installTransitionObserver()", 1)[1].split(
        "function postReady()", 1
    )[0]
    assert "if (bridgeButton) event.preventDefault();" in observer_source
    assert "if (bridgeButton) bridgeButton.click();" in observer_source
    assert 'String(control.dataset.streamlitBridgeKey || "")' in observer_source
    assert 'transition === "object_detail_to_objects"' in observer_source
    assert '=== "Back to Objects"' in observer_source
    assert "const resetScrollOnReady = __RESET_SCROLL__;" in ready_signal
    assert 'parentWindow.setTimeout(reset, 250);' in ready_signal
    object_detail_guard = ready_signal.split(
        "def install_object_detail_input_guard", 1
    )[1].split("def install_objects_live_progress", 1)[0]
    handle_input = object_detail_guard.split("function handleInput", 1)[1].split(
        "function handlePaste", 1
    )[0]
    handle_blur = object_detail_guard.split("function handleBlur", 1)[1].split(
        "function findApproveButton", 1
    )[0]
    assert 'updateRowCost(ctx.input.closest(".object-detail-table-row"))' in handle_input
    assert "updateSummaries" not in handle_input
    assert "updateCalculations" in handle_blur
    assert "parentWindow.location.search" not in handle_blur
    assert 'if (event.key === "Enter")' in object_detail_guard
    assert "ctx.input.blur()" in object_detail_guard
    assert "const edits = snapshotEdits();" in object_detail_guard
    assert "if (!edits.length) return;" in object_detail_guard
    assert "/rest/v1/rpc/save_rfq_object_detail_draft" in object_detail_guard
    assert 'field: "object_quantity"' in object_detail_guard
    assert "object-detail-discard-modal" in object_detail_guard
    assert "Are you sure you want to leave without saving?" in object_detail_guard
    assert "confirmDiscard" in object_detail_guard
    assert '"object_detail_approve_bridge"' in object_detail_guard
    telemetry_source = component.split("function startupPhase", 1)[1].split(
        "function storeResumeCookie", 1
    )[0]
    assert "access_token" not in telemetry_source
    assert "refresh_token" not in telemetry_source

    assert "route: __ROUTE__" in ready_signal
    assert '.replace("__ROUTE__", route_json)' in ready_signal

    wrapper = (ROOT / "cloudflare/index.html").read_text()
    assert 'searchParams.set("access_token"' not in wrapper
    assert 'searchParams.set("refresh_token"' not in wrapper
    assert 'event.data.type === "costerly:transition-styled"' in wrapper
    assert 'mark("browser.transition_styled"' in wrapper
    assert 'revealInternalTransition("target_styled")' in wrapper
    styled_handler = wrapper.split(
        'event.data.type === "costerly:transition-styled"', 1
    )[1].split(
        'event.data.type === "costerly:transition-visible"', 1
    )[0]
    assert "maskedInternalTransitions.has(pendingTransition.name)" in styled_handler


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
