from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


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

    if "estimation_first_object_requested" not in st.session_state:
        st.session_state.estimation_first_object_requested = False

    if "last_estimation_error" not in st.session_state:
        st.session_state.last_estimation_error = None


def go_to(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()
