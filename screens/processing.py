from __future__ import annotations

import streamlit as st


def render_processing_screen(company_id: str) -> None:
    st.markdown("# Processing file")
    st.markdown(st.session_state.get("uploaded_file_name") or "Uploaded file")

    st.progress(20, text="Reading file...")

    if st.button("Go to file review"):
        st.session_state.screen = "file_review"
        st.rerun()
