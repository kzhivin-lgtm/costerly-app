from __future__ import annotations

import streamlit as st

from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from use_cases.rfq_processing import process_uploaded_rfq


def render_processing_screen(company_id: str) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    The screen stays visual-only: it delegates the actual agent/Supabase work to
    process_uploaded_rfq().
    """
    st.markdown(
        processing_stage_html(marker_id=PROCESSING_MARKER_ID),
        unsafe_allow_html=True,
    )

    file_name = st.session_state.get("uploaded_file_name")
    file_bytes = st.session_state.get("uploaded_file_bytes")

    if not file_name or not file_bytes:
        st.session_state.processing_error = "No uploaded RFQ file found."
        st.session_state.screen = "upload"
        st.rerun()

    if (
        st.session_state.get("current_run_id")
        and st.session_state.get("processed_file_name") == file_name
    ):
        st.session_state.screen = "file_review"
        st.rerun()

    try:
        result = process_uploaded_rfq(
            file_name=file_name,
            file_bytes=file_bytes,
            company_id=company_id,
        )
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        st.session_state.screen = "file_review"
        st.rerun()

    st.session_state.current_run_id = result["run_id"]
    st.session_state.processed_file_name = file_name
    st.session_state.processing_error = None
    st.session_state.screen = "file_review"
    st.rerun()
