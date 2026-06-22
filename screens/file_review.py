from __future__ import annotations

import streamlit as st


def render_file_review_screen(company_id: str) -> None:
    st.markdown("# File review")
    st.markdown("Clean architecture placeholder.")

    st.write(
        {
            "company_id": company_id,
            "uploaded_file_name": st.session_state.get("uploaded_file_name"),
            "bytes_loaded": bool(st.session_state.get("uploaded_file_bytes")),
        }
    )

    if st.button("Back to upload"):
        st.session_state.screen = "upload"
        st.rerun()
