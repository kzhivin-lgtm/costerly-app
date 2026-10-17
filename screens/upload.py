from __future__ import annotations

import streamlit as st

from agents.ocr_adapter import warm_mistral_http_client_async
from state.session import reset_new_estimate_session
from styles.upload import apply_upload_css
from ui.js_guards import install_upload_interaction_guards
from ui.processing_stage import processing_stage_html


def _render_upload_hero() -> None:
    """Render the upload value proposition below the shared app header."""
    html = (
        '<div class="upload-screen-active" style="display:none"></div>'
        '<div class="upload-screen">'
        '<div class="upload-screen__stack">'
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
    reset_new_estimate_session(clear_upload_widget=False)


def render_upload_screen(company_id: str, *, trace=None) -> None:
    """Render the first screen and move to processing after a file is accepted.

    This screen owns only UI state and the Streamlit upload action. Processing
    will later move into a use case outside the Streamlit screen layer.
    """
    apply_upload_css()
    warm_mistral_http_client_async()
    _render_upload_hero()

    uploaded_file = st.file_uploader(
        "📎 Drop or upload",
        type=["pdf", "png", "jpg", "jpeg"],
        key="rfq_upload_input",
        label_visibility="collapsed",
    )
    install_upload_interaction_guards(processing_stage_html(elapsed_seconds=0))

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        same_upload_as_session = (
            st.session_state.get("uploaded_file_name") == uploaded_file.name
            and st.session_state.get("uploaded_file_bytes") == file_bytes
        )
        if not same_upload_as_session:
            _reset_post_upload_flow_state()
        if trace is not None:
            trace.event(
                "server.rfq_upload_accepted",
                metadata={"same_upload_as_session": same_upload_as_session},
            )
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_bytes = file_bytes
        st.session_state.screen = "processing"
        if trace is not None:
            trace.event("server.rfq_processing_queued")
        st.rerun()
