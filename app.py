from __future__ import annotations

import streamlit as st

from state.session import init_state, get_company_id
from styles.base import apply_base_css
from screens.upload import render_upload_screen
from screens.processing import render_processing_screen
from screens.file_review import render_file_review_screen
from screens.objects import render_objects_screen
from screens.object_detail import render_object_detail_screen


st.set_page_config(
    page_title="costerly.ai",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    init_state()
    apply_base_css()

    company_id = get_company_id()
    requested_screen = st.query_params.get("screen")
    if requested_screen in {"objects", "object_detail", "file_review"}:
        st.session_state.screen = requested_screen
        requested_run_id = st.query_params.get("run_id")
        requested_estimate_id = st.query_params.get("estimate_id")
        requested_object_id = st.query_params.get("object_id")
        if requested_run_id:
            st.session_state.current_run_id = requested_run_id
        if requested_estimate_id:
            st.session_state.current_estimate_id = requested_estimate_id
        if requested_object_id:
            st.session_state.current_object_id = requested_object_id
        st.query_params.clear()

    screen = st.session_state.screen

    if screen == "upload":
        render_upload_screen(company_id)
    elif screen == "processing":
        render_processing_screen(company_id)
    elif screen == "file_review":
        render_file_review_screen(company_id)
    elif screen == "objects":
        render_objects_screen(company_id)
    elif screen == "object_detail":
        render_object_detail_screen(company_id)
    else:
        st.session_state.screen = "upload"
        st.rerun()


if __name__ == "__main__":
    main()
