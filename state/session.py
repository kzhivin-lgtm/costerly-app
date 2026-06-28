from __future__ import annotations

from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


_APP_BOOT_ID = uuid4().hex


def get_secret(name: str, default: str) -> str:
    try:
        return str(st.secrets.get(name, default))
    except StreamlitSecretNotFoundError:
        return default


def get_company_id() -> str:
    return get_secret("COMPANY_ID", "001")


def init_state() -> None:
    if st.session_state.get("_app_boot_id") not in {None, _APP_BOOT_ID}:
        for key in list(st.session_state.keys()):
            del st.session_state[key]

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

    if "processed_file_name" not in st.session_state:
        st.session_state.processed_file_name = None

    if "processing_error" not in st.session_state:
        st.session_state.processing_error = None

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
