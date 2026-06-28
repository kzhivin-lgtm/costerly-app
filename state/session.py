from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from state.estimation_runs import clear_estimation_runs
from state.uploaded_files import clear_uploaded_files


def get_secret(name: str, default: str) -> str:
    try:
        return str(st.secrets.get(name, default))
    except StreamlitSecretNotFoundError:
        return default


def get_company_id() -> str:
    return get_secret("COMPANY_ID", "001")


def init_state() -> None:
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

    if "processed_file_name" not in st.session_state:
        st.session_state.processed_file_name = None

    if "processing_error" not in st.session_state:
        st.session_state.processing_error = None

    if "estimation_cycle_future" not in st.session_state:
        st.session_state.estimation_cycle_future = None

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


def go_to(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()


def reset_post_upload_flow_state() -> None:
    """Clear RFQ and estimate state when the current upload flow is discarded."""
    st.session_state.current_run_id = None
    st.session_state.current_estimate_id = None
    st.session_state.current_estimate_run_id = None
    st.session_state.current_object_id = None
    st.session_state.uploaded_file_name = None
    st.session_state.uploaded_file_bytes = None
    st.session_state.processed_file_name = None
    st.session_state.processing_error = None
    st.session_state.estimation_cycle_future = None
    st.session_state.last_estimation_error = None
    st.session_state.file_review_object_edits = {}
    st.session_state.file_review_object_edits_run_id = None
    st.session_state.file_review_ignored_object_ids = set()
    st.session_state.file_review_saved_ignored_object_ids = set()
    st.session_state.file_review_data_cache = {}
    st.session_state.objects_estimation_data_cache = {}
    st.session_state.objects_estimation_cache_dirty = set()
    st.session_state.last_estimation_result = None
    st.session_state.approved_object_keys = set()
    clear_estimation_runs()
    clear_uploaded_files()
