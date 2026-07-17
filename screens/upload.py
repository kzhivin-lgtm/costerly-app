from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

from styles.upload import apply_upload_css
from ui.js_guards import install_upload_interaction_guards
from ui.processing_stage import processing_stage_html


LOGO_PATH = Path("assets/brand/costelry_logo_full_cropped.svg")

@lru_cache(maxsize=1)
def _read_logo_data_uri() -> str:
    """Return the brand logo as an inline image source for the upload screen.

    Called during upload screen rendering. Keeping the SVG inline avoids layout
    differences from Streamlit's image wrapper.
    """
    svg_bytes = LOGO_PATH.read_bytes()
    encoded = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"

def _render_upload_hero() -> None:
    """Render the static brand and hero block above the uploader."""
    logo_src = _read_logo_data_uri()

    html = (
        '<div class="upload-screen-active" style="display:none"></div>'
        '<div class="upload-screen">'
        '<div class="upload-screen__stack">'
        f'<img class="upload-screen__logo" src="{logo_src}" alt="costerly.ai" />'
        '<div class="upload-screen__hero">'
        'AI estimating<br>'
        'Quote request to proposal<br>'
        'In minutes, not days'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _reset_post_upload_flow_state() -> None:
    """Clear RFQ/estimate state when a new upload starts."""
    st.session_state.current_run_id = None
    st.session_state.current_estimate_id = None
    st.session_state.current_estimate_run_id = None
    st.session_state.current_object_id = None
    st.session_state.current_ocr_package = None
    st.session_state.current_agent_timings = None
    st.session_state.processed_file_name = None
    st.session_state.processing_error = None
    st.session_state.estimation_first_object_future = None
    st.session_state.last_estimation_result = None
    st.session_state.last_estimation_error = None
    st.session_state.objects_estimation_seed_rows = []
    st.session_state.file_review_object_edits = {}
    st.session_state.file_review_object_edits_run_id = None
    st.session_state.file_review_ignored_object_ids = set()
    st.session_state.file_review_saved_ignored_object_ids = set()
    st.session_state.file_review_data_cache = {}
    st.session_state.objects_estimation_data_cache = {}
    st.session_state.objects_estimation_cache_dirty = set()


def render_upload_screen(company_id: str) -> None:
    """Render the first screen and move to processing after a file is accepted.

    This screen owns only UI state and the Streamlit upload action. Processing
    will later move into a use case outside the Streamlit screen layer.
    """
    apply_upload_css()
    _render_upload_hero()

    uploaded_file = st.file_uploader(
        "📎 Drop or upload",
        type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )
    install_upload_interaction_guards(processing_stage_html())

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        if (
            st.session_state.get("uploaded_file_name") != uploaded_file.name
            or st.session_state.get("uploaded_file_bytes") != file_bytes
        ):
            _reset_post_upload_flow_state()
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_bytes = file_bytes
        st.session_state.screen = "processing"
        st.rerun()
