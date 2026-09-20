from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
import platform
import time

_SCRIPT_STARTED_AT = time.perf_counter()

import streamlit as st

from config import get_optional_secret
from observability.runtime import (
    configure_runtime_sink,
    emit_completed_action,
    new_runtime_trace,
)
from state.session import init_state, get_company_id
from state.company_auth import (
    company_auth_enabled,
    current_company_access,
    invitation_from_url,
    render_account_control,
    render_company_account,
    render_company_setup,
    render_login_or_signup,
    sync_browser_auth_session,
)
from db.company_access import assert_estimate_owned, assert_run_owned
from db.supabase_client import get_supabase_client
from styles.base import apply_base_css
from ui.js_guards import scroll_parent_to_top, signal_app_ready_to_embed
from ui.app_header import render_app_header


def _installed_version(distribution: str) -> str:
    try:
        return package_version(distribution)
    except PackageNotFoundError:
        return "unknown"


_RUNTIME_VERSIONS = {
    "python_version": platform.python_version(),
    "streamlit_version": st.__version__,
    "supabase_version": _installed_version("supabase"),
}


st.set_page_config(
    page_title="costerly.ai",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


_PROFILE_TAB_ROUTES = {
    "overhead-expenses": "Overhead Expenses",
    "labor-costs": "Labor Costs",
    "contacts": "Contacts",
    "bank-details": "Bank Details",
    "company-details": "Bank Details",
    "users": "Users",
    "price-lists": "Price Lists",
}


def _browser_route(screen: str) -> dict[str, str]:
    """Return the safe, durable browser route for the rendered screen."""
    if screen == "account":
        selected_tab = str(
            st.session_state.get("company_profile_tab") or "Overhead Expenses"
        )
        tab_route = next(
            (
                route
                for route, label in _PROFILE_TAB_ROUTES.items()
                if label == selected_tab
            ),
            "overhead-expenses",
        )
        return {"screen": "account", "profile_tab": tab_route}

    if screen == "file_review":
        run_id = str(st.session_state.get("current_run_id") or "")
        return {"screen": screen, "run_id": run_id} if run_id else {"screen": "upload"}

    if screen in {"objects", "object_detail"}:
        run_id = str(st.session_state.get("current_run_id") or "")
        estimate_id = str(st.session_state.get("current_estimate_id") or "")
        if not run_id or not estimate_id:
            return {"screen": "upload"}
        route = {"screen": screen, "run_id": run_id, "estimate_id": estimate_id}
        if screen == "object_detail":
            object_id = str(st.session_state.get("current_object_id") or "")
            if not object_id:
                return {"screen": "objects", "run_id": run_id, "estimate_id": estimate_id}
            route["object_id"] = object_id
        return route

    # Processing cannot survive a destroyed Python session yet. Auth,
    # registration, and company setup are derived from verified auth/invite state.
    return {"screen": "upload"}


def _signal_ready(trace, screen: str) -> None:
    trace.set_screen(screen)
    trace.event("server.app_ready_component_enqueued")
    signal_app_ready_to_embed(
        screen,
        build_version=trace.build_version,
        trace_id=trace.trace_id,
        run_id=trace.run_id,
        metrics=trace.summary(),
        route=_browser_route(screen),
    )
    trace.event("server.run_complete")


def _render_screen(screen: str, company_id: str, *, access=None, trace=None) -> None:
    if screen == "upload":
        from screens.upload import render_upload_screen

        render_upload_screen(company_id)
    elif screen == "processing":
        from screens.processing import render_processing_screen

        render_processing_screen(company_id)
    elif screen == "file_review":
        from screens.file_review import render_file_review_screen

        render_file_review_screen(company_id)
    elif screen == "objects":
        from screens.objects import render_objects_screen

        render_objects_screen(company_id)
    elif screen == "object_detail":
        from screens.object_detail import render_object_detail_screen

        render_object_detail_screen(company_id)
    elif screen == "account":
        if access is None or access.company_id != company_id:
            raise PermissionError("Company access changed. Please sign in again.")
        render_company_account(access, trace=trace)
    else:
        st.session_state.screen = "upload"
        st.rerun()


def main() -> None:
    init_started_at = time.perf_counter()
    init_state()
    st.session_state._runtime_run_sequence = (
        int(st.session_state.get("_runtime_run_sequence") or 0) + 1
    )
    configure_runtime_sink(
        get_optional_secret("SUPABASE_URL"),
        get_optional_secret("SUPABASE_SERVICE_ROLE_KEY"),
    )
    trace = new_runtime_trace(
        session_state=st.session_state,
        requested_trace_id=st.query_params.get("obs_trace"),
        screen=str(st.session_state.get("screen") or "upload"),
        started_at=_SCRIPT_STARTED_AT,
        build_version="3.5.6",
    )
    trace.annotate(
        run_sequence=st.session_state._runtime_run_sequence,
        python_imports_ms=round((init_started_at - _SCRIPT_STARTED_AT) * 1000, 3),
        **_RUNTIME_VERSIONS,
    )
    emit_completed_action(st.session_state, trace)
    trace.event(
        "server.run_start",
        duration_ms=(time.perf_counter() - init_started_at) * 1000,
        metadata={"phase": "init_state"},
    )
    with trace.span("server.base_css"):
        apply_base_css()

    auth_enabled = company_auth_enabled()
    access = None
    if auth_enabled:
        startup_probe = str(st.query_params.get("startup_probe") or "")
        if startup_probe == "anonymous":
            trace.annotate(
                auth_outcome="anonymous_probe",
                fast_resume="bypassed_for_probe",
            )
            with trace.span("server.app_header_render"):
                render_app_header()
            trace.set_screen("login")
            with trace.span("server.login_render"):
                render_login_or_signup(None)
            _signal_ready(trace, "login")
            return
        with trace.span("server.auth.browser_session_sync"):
            browser_session_ready = sync_browser_auth_session(
                trace_id=trace.trace_id,
                run_id=trace.run_id,
                run_sequence=st.session_state._runtime_run_sequence,
                server_elapsed_before_component_ms=trace.summary()["server_elapsed_ms"],
            )
        trace.event(
            "server.auth.browser_session_sync_result",
            metadata={
                "ready": browser_session_ready,
                "outcome": str(
                    st.session_state.get("_browser_auth_sync_outcome") or "unknown"
                ),
                "fast_resume": str(
                    st.session_state.get("_fast_resume_outcome") or "unknown"
                ),
            },
        )
        trace.annotate(
            auth_outcome=str(
                st.session_state.get("_browser_auth_sync_outcome") or "unknown"
            ),
            fast_resume=str(
                st.session_state.get("_fast_resume_outcome") or "unknown"
            ),
        )
        if not browser_session_ready:
            trace.event("server.auth.browser_session_wait", status="unknown")
            st.stop()
        try:
            with trace.span("server.auth.access_lookup"):
                access = current_company_access()
                invitation = invitation_from_url()
        except Exception as exc:
            trace.event(
                "server.auth.access_error",
                status="error",
                metadata={"error_type": type(exc).__name__},
            )
            st.error(f"Company access is unavailable: {exc}")
            _signal_ready(trace, "company_access_error")
            return
        with trace.span("server.app_header_render"):
            render_app_header()
        if access is None:
            trace.set_screen("login")
            with trace.span("server.login_render"):
                render_login_or_signup(invitation)
            _signal_ready(trace, "login")
            return
        if access.company_id is None:
            trace.set_screen("company_setup")
            with trace.span("server.company_setup_render"):
                render_company_setup(access, invitation)
            _signal_ready(trace, "company_setup")
            return
        st.session_state.auth_company_id = access.company_id
        st.session_state.auth_access_token = access.access_token
        requested_screen = st.query_params.get("screen")
        if requested_screen == "account":
            st.session_state.screen = "account"
            requested_profile_tab = str(st.query_params.get("profile_tab") or "")
            if requested_profile_tab in _PROFILE_TAB_ROUTES:
                st.session_state.company_profile_tab = _PROFILE_TAB_ROUTES[requested_profile_tab]
            for route_key in ("screen", "profile_tab"):
                if route_key in st.query_params:
                    del st.query_params[route_key]
        with trace.span("server.account_controls_render"):
            render_account_control(access)
    else:
        with trace.span("server.app_header_render"):
            render_app_header()

    with trace.span("server.company_id_resolve"):
        company_id = get_company_id()

    requested_screen = st.query_params.get("screen")
    if requested_screen in {"objects", "object_detail", "file_review"}:
        st.session_state.screen = requested_screen
        requested_run_id = st.query_params.get("run_id")
        requested_estimate_id = st.query_params.get("estimate_id")
        requested_object_id = st.query_params.get("object_id")
        if auth_enabled:
            try:
                client = get_supabase_client()
                if requested_run_id:
                    assert_run_owned(client, requested_run_id, company_id)
                if requested_estimate_id:
                    assert_estimate_owned(client, requested_estimate_id, company_id)
            except PermissionError:
                st.query_params.clear()
                st.error("This RFQ or estimate is not available to your company.")
                _signal_ready(trace, "company_access_error")
                return
        object_detail_edit_line = st.query_params.get("od_edit_line")
        object_detail_edit_field = st.query_params.get("od_edit_field")
        object_detail_edit_value = st.query_params.get("od_edit_value")
        object_detail_approve_after = st.query_params.get("od_approve_after")
        object_detail_snapshot = st.query_params.get("od_snapshot")
        if requested_run_id:
            st.session_state.current_run_id = requested_run_id
        if requested_estimate_id:
            st.session_state.current_estimate_id = requested_estimate_id
            if requested_run_id:
                st.session_state.current_estimate_run_id = requested_run_id
        if requested_object_id:
            st.session_state.current_object_id = requested_object_id
        if (
            requested_screen == "object_detail"
            and requested_estimate_id
            and requested_object_id
            and object_detail_snapshot
        ):
            st.session_state.object_detail_pending_snapshot = {
                "estimate_id": requested_estimate_id,
                "object_id": requested_object_id,
                "snapshot": object_detail_snapshot,
            }
            if object_detail_approve_after == "1":
                st.session_state.object_detail_approve_after_edit = True
        elif (
            requested_screen == "object_detail"
            and requested_estimate_id
            and requested_object_id
            and object_detail_edit_line
            and object_detail_edit_field
            and object_detail_edit_value is not None
        ):
            st.session_state.object_detail_pending_edit = {
                "estimate_id": requested_estimate_id,
                "object_id": requested_object_id,
                "line_id": object_detail_edit_line,
                "field": object_detail_edit_field,
                "value": object_detail_edit_value,
            }
            if object_detail_approve_after == "1":
                st.session_state.object_detail_approve_after_edit = True
        st.query_params.clear()

    screen = st.session_state.screen
    if auth_enabled:
        try:
            client = get_supabase_client()
            run_id = st.session_state.get("current_run_id")
            estimate_id = st.session_state.get("current_estimate_id")
            if screen in {"file_review", "objects", "object_detail"} and run_id:
                assert_run_owned(client, str(run_id), company_id)
            if screen in {"objects", "object_detail"} and estimate_id:
                assert_estimate_owned(client, str(estimate_id), company_id)
        except PermissionError:
            st.session_state.current_run_id = None
            st.session_state.current_estimate_id = None
            st.session_state.current_object_id = None
            st.session_state.screen = "upload"
            st.error("The selected RFQ or estimate is not available to your company.")
            _signal_ready(trace, "company_access_error")
            return
    last_screen_for_scroll = st.session_state.get("_last_screen_for_scroll")
    if last_screen_for_scroll != screen:
        is_initial_upload_render = last_screen_for_scroll is None and screen == "upload"
        if not is_initial_upload_render:
            scroll_parent_to_top()
        st.session_state._last_screen_for_scroll = screen

    trace.set_screen(screen)
    with trace.span("server.screen_render", route=screen):
        _render_screen(screen, company_id, access=access, trace=trace)

    _signal_ready(trace, screen)


if __name__ == "__main__":
    main()
