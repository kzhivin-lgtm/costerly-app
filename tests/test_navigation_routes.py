from __future__ import annotations

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


def test_profile_route_uses_bank_details_slug_and_accepts_legacy_slug():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Bank Details"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "bank-details",
    }
    assert app._PROFILE_TAB_ROUTES["company-details"] == "Bank Details"


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
