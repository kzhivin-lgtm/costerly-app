from __future__ import annotations

import streamlit as st


def render_upload_screen(company_id: str) -> None:
    st.markdown("# costerly.ai")
    st.markdown("Upload an RFQ, drawing, PDF, sketch or technical file.")

    uploaded_file = st.file_uploader(
        "Upload file",
        type=["pdf", "png", "jpg", "jpeg", "webp", "csv", "xlsx"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_bytes = uploaded_file.getvalue()
        st.session_state.screen = "processing"
        st.rerun()
