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

    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None

    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.uploaded_file_bytes = None


def go_to(screen: str) -> None:
    st.session_state.screen = screen
    st.rerun()
