from __future__ import annotations

from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


_APP_BOOT_ID = uuid4().hex

# A Streamlit widget callback runs before this script body. When a deployment
# replaces the Python process, the first header click can therefore set a new
# destination and then immediately lose it to the stale-session reset below.
# Preserve only destinations that do not depend on a transient workflow ID.
_DEPLOY_SAFE_NAVIGATION_SCREENS = frozenset({"upload", "account", "admin", "projects"})


def get_secret(name: str, default: str) -> str:
    try:
        return str(st.secrets.get(name, default))
    except StreamlitSecretNotFoundError:
        return default


def get_company_id() -> str:
    from state.company_auth import company_auth_enabled

    if company_auth_enabled():
        company_id = st.session_state.get("auth_company_id")
        if not company_id:
            raise PermissionError("Sign in to a company before using Costerly AI.")
        return str(company_id)
    return get_secret("COMPANY_ID", "001")


def init_state() -> None:
    if st.session_state.get("_app_boot_id") not in {None, _APP_BOOT_ID}:
        pending_screen = str(st.session_state.get("screen") or "")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        if pending_screen in _DEPLOY_SAFE_NAVIGATION_SCREENS:
            st.session_state.screen = pending_screen

    st.session_state._app_boot_id = _APP_BOOT_ID

    if "screen" not in st.session_state:
        st.session_state.screen = "upload"

    if "current_run_id" not in st.session_state:
        st.session_state.current_run_id = None

    if "current_estimate_id" not in st.session_state:
        st.session_state.current_estimate_id = None

    if "current_estimate_run_id" not in st.session_state:
        st.session_state.current_estimate_run_id = None

    if "current_object_id" not in st.session_state:
        st.session_state.current_object_id = None

    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None

    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.uploaded_file_bytes = None

    if "rfq_upload_widget_generation" not in st.session_state:
        st.session_state.rfq_upload_widget_generation = 0

    if "processed_file_name" not in st.session_state:
        st.session_state.processed_file_name = None

    if "processing_error" not in st.session_state:
        st.session_state.processing_error = None

    if "current_agent_timings" not in st.session_state:
        st.session_state.current_agent_timings = None

    if "current_naming_future" not in st.session_state:
        st.session_state.current_naming_future = None

    if "current_naming_result" not in st.session_state:
        st.session_state.current_naming_result = None

    if "current_preview_future" not in st.session_state:
        st.session_state.current_preview_future = None

    if "file_review_deferred_work" not in st.session_state:
        st.session_state.file_review_deferred_work = None

    if "last_estimation_error" not in st.session_state:
        st.session_state.last_estimation_error = None

    if "file_review_data_cache" not in st.session_state:
        st.session_state.file_review_data_cache = {}

    if "file_review_saved_ignored_object_ids" not in st.session_state:
        st.session_state.file_review_saved_ignored_object_ids = set()

    if "objects_estimation_data_cache" not in st.session_state:
        st.session_state.objects_estimation_data_cache = {}

    if "objects_estimation_cache_dirty" not in st.session_state:
        st.session_state.objects_estimation_cache_dirty = set()


def reset_new_estimate_session(*, clear_upload_widget: bool) -> None:
    """Remove every estimate-scoped session value before a new upload cycle.

    A new estimate is a new run even when its bytes and filename match a
    previous upload. Background work for the old run may finish independently,
    but it must no longer have a session-visible destination.
    """
    none_fields = (
        "return_file_review_run_id",
        "current_run_id",
        "current_estimate_id",
        "current_estimate_run_id",
        "current_object_id",
        "current_ocr_package",
        "current_agent_timings",
        "current_naming_future",
        "current_naming_result",
        "current_preview_future",
        "file_review_deferred_work",
        "processed_file_name",
        "processing_error",
        "estimation_batch_future",
        "last_estimation_result",
        "last_estimation_error",
        "file_review_object_edits_run_id",
        "file_review_run_metadata_run_id",
        "file_review_name_save_error",
        "file_review_metadata_save_error",
        "objects_live_poll_estimate_id",
        "final_approval_error",
        "object_detail_approval_error",
        "object_detail_pending_edit",
        "object_detail_pending_snapshot",
        "object_detail_approve_after_edit",
    )
    for key in none_fields:
        st.session_state[key] = None

    for key in (
        "objects_estimation_seed_rows",
        "file_review_object_edits",
        "file_review_initial_object_names",
        "file_review_ignored_object_ids",
        "file_review_saved_ignored_object_ids",
        "file_review_run_metadata",
        "approved_object_keys",
        "workflow_route_tokens",
        "proposal_pdf_urls_by_estimate",
    ):
        st.session_state.pop(key, None)

    st.session_state.uploaded_file_name = None
    st.session_state.uploaded_file_bytes = None
    st.session_state.file_review_data_cache = {}
    st.session_state.objects_estimation_data_cache = {}
    st.session_state.objects_estimation_cache_dirty = set()

    for key in list(st.session_state):
        if str(key).startswith((
            "file_review_naming_published.",
            "file_review_naming_cache_synced.",
            "file_review_preview_published.",
            "file_review_preview_terminal.",
            "file_review_terminal_publication.",
        )):
            st.session_state.pop(key, None)
    if clear_upload_widget:
        # A native file input does not reliably emit a new Streamlit value when
        # the same PDF is selected again. A new widget identity makes every
        # New Estimate or retry an actual upload cycle rather than a client-only
        # Processing shell.
        st.session_state.rfq_upload_widget_generation = (
            int(st.session_state.get("rfq_upload_widget_generation", 0)) + 1
        )
        st.session_state.pop("rfq_upload_input", None)


def set_screen(screen: str) -> None:
    """Change the active screen from a widget callback before the next render."""
    st.session_state.screen = screen


def go_to(screen: str) -> None:
    """Change screens from non-widget control flow and rerun immediately."""
    set_screen(screen)
    st.rerun()
