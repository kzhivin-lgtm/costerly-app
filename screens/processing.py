from __future__ import annotations

import streamlit as st

from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html


def render_processing_screen(company_id: str) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    For now this is the visual shell only. The real processing use case will
    later advance this screen automatically.
    """
    st.markdown(
        processing_stage_html(marker_id=PROCESSING_MARKER_ID),
        unsafe_allow_html=True,
    )
