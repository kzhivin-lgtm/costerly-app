from __future__ import annotations

import streamlit as st

from ui.layout import render_post_upload_header
from ui.progress import apply_progress_css, render_progress_bar


PROCESSING_TITLE = "Reading your RFQ package"
PROCESSING_SUBTITLE = "AI Detection is analyzing the uploaded file and detecting estimate-scope objects"


def render_processing_screen(company_id: str) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    For now this is the visual shell only. The real processing use case will
    later advance this screen automatically.
    """
    render_post_upload_header(PROCESSING_TITLE, PROCESSING_SUBTITLE)
    apply_progress_css()
    render_progress_bar(0.04)
