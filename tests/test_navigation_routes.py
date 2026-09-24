from __future__ import annotations

import ast
from pathlib import Path

import streamlit as st

import app


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


def test_profile_route_is_restored_before_account_controls_render():
    source = Path("app.py").read_text()

    restore_position = source.index('if requested_screen == "account":')
    controls_position = source.index("render_account_control(access)")

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
