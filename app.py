from __future__ import annotations

import streamlit as st

from state.session import init_state, get_company_id
from styles.base import apply_base_css
from screens.upload import render_upload_screen
from screens.processing import render_processing_screen
from screens.file_review import render_file_review_screen


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
    screen = st.session_state.screen

    if screen == "upload":
        render_upload_screen(company_id)
    elif screen == "processing":
        render_processing_screen(company_id)
    elif screen == "file_review":
        render_file_review_screen(company_id)
    else:
        st.session_state.screen = "upload"
        st.rerun()


if __name__ == "__main__":
    main()
