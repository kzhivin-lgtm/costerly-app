from __future__ import annotations

import ast
from concurrent.futures import Future
from pathlib import Path

import streamlit as st

import app
from screens import objects


def test_profile_route_preserves_selected_tab():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Contacts"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "contacts",
    }


def test_profile_route_preserves_machinery_tab_in_app_and_wrapper():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Machinery"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "machinery",
    }
    wrapper = (Path(__file__).parents[1] / "cloudflare" / "index.html").read_text()
    assert '"machinery"' in wrapper


def test_profile_route_uses_bank_details_slug_and_accepts_legacy_slug():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Bank Details"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "bank-details",
    }
    assert app._PROFILE_TAB_ROUTES["company-details"] == "Bank Details"
    wrapper = (Path(__file__).parents[1] / "cloudflare" / "index.html").read_text()
    assert '"bank-details"' in wrapper
    assert '"company-details"' in wrapper


def test_file_review_route_preserves_run_context():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"

    assert app._browser_route("file_review") == {
        "screen": "file_review",
        "run_id": "run-123",
    }


def test_workflow_route_uses_a_short_token_when_company_context_is_available(monkeypatch):
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"
    monkeypatch.setattr(app, "_workflow_route_token", lambda **_kwargs: "short-route-1")

    assert app._browser_route("file_review", company_id="company-1") == {
        "screen": "file_review",
        "route_token": "short-route-1",
    }
    assert app._browser_route("objects", company_id="company-1") == {
        "screen": "objects",
        "route_token": "short-route-1",
    }


def test_file_review_route_keeps_the_active_estimate_for_refresh_recovery():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"

    assert app._browser_route("file_review") == {
        "screen": "file_review",
        "run_id": "run-123",
        "estimate_id": "estimate-456",
    }


def test_object_detail_route_preserves_complete_context():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"
    st.session_state.current_object_id = "object-789"

    assert app._browser_route("object_detail") == {
        "screen": "object_detail",
        "run_id": "run-123",
        "estimate_id": "estimate-456",
        "object_id": "object-789",
    }


def test_processing_refresh_fails_safe_to_upload():
    st.session_state.clear()

    assert app._browser_route("processing") == {"screen": "upload"}


def test_workflow_routes_do_not_render_the_central_logo_in_auth_disabled_mode():
    source = Path("app.py").read_text()

    assert 'if current_screen == "upload":' in source


def test_profile_route_is_restored_before_account_controls_render():
    source = Path("app.py").read_text()

    restore_position = source.index('if requested_screen == "account":')
    controls_position = source.index(
        "render_account_control(access, platform_access=platform_access)"
    )

    assert restore_position < controls_position


def test_widget_navigation_never_adds_a_second_explicit_rerun():
    """A widget click already reruns Streamlit; navigation must use on_click."""
    root = Path(__file__).parents[1]
    violations = []

    for path in root.rglob("*.py"):
        if any(part in {"tests", "tmp", ".venv"} for part in path.parts):
            continue
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Call):
                continue
            function = node.test.func
            if not isinstance(function, ast.Attribute) or function.attr not in {
                "button",
                "form_submit_button",
            }:
                continue
            block = ast.get_source_segment(source, node) or ""
            changes_screen = "session_state.screen" in block or "session_state[\"screen\"]" in block
            if changes_screen and "st.rerun()" in block:
                violations.append(f"{path.relative_to(root)}:{node.lineno}")

    assert violations == []


def test_file_review_navigation_uses_widget_callbacks_not_a_second_rerun():
    source = Path("screens/file_review.py").read_text()
    continue_source = source.split("def _continue_to_objects_estimation", 1)[1].split(
        "def _mark_estimation_batch_started", 1
    )[0]

    assert "on_click=_continue_to_objects_estimation" in source
    assert "on_click=set_screen" in source
    assert "st.rerun()" not in continue_source


def test_active_estimation_opens_seeded_objects_without_waiting_for_supabase(monkeypatch):
    st.session_state.clear()
    st.session_state.estimation_batch_future = Future()
    st.session_state.objects_estimation_seed_rows = [
        {
            "object_key": "object-1",
            "name": "Cabinet",
            "quantity": 1,
            "status": "running",
            "self_cost_unit": "1%",
            "sale_price_unit": None,
            "sale_price_total": None,
            "suggestion": "suggested: SC + 30%",
            "reviewed": False,
        }
    ]
    monkeypatch.setattr(
        objects,
        "_load_objects_screen_data",
        lambda _estimate_id: (_ for _ in ()).throw(AssertionError("must not load")),
    )

    state = objects._current_objects_state("estimate-1")

    assert state.data_error is None
    assert state.data["rows"][0]["object_key"] == "object-1"


def test_workflow_screens_do_not_install_react_mutating_transition_shells():
    assert "install_post_upload_transition_guard" not in Path("screens/file_review.py").read_text()
    assert "install_post_upload_transition_guard" not in Path("screens/objects.py").read_text()


def test_objects_runtime_stops_dom_writers_before_workflow_navigation():
    source = Path("ui/js_guards.py").read_text()

    assert 'const NAVIGATION_CLEANUP_KEY = "__costerlyObjectsNavigationCleanup"' in source
    assert 'parentDoc.addEventListener("pointerdown", stopForWorkflowNavigation, true)' in source
    assert 'parentWindow[PRICE_INPUT_CLEANUP_KEY]();' in source
    assert 'observer.observe(parentDoc.documentElement, { childList: true, subtree: true })' in source
