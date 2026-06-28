from __future__ import annotations

import math
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from state.uploaded_files import remember_rfq_file
from ui.js_guards import clear_upload_processing_shell
from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from use_cases.rfq_processing import process_uploaded_rfq


def render_processing_screen(company_id: str) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    The screen stays visual-only: it delegates the actual agent/Supabase work to
    process_uploaded_rfq().
    """
    stage_slot = st.empty()

    def render_stage(progress_value: float) -> None:
        stage_slot.markdown(
            processing_stage_html(
                marker_id=PROCESSING_MARKER_ID,
                progress_value=progress_value,
            ),
            unsafe_allow_html=True,
        )

    render_stage(0.04)
    clear_upload_processing_shell()

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
        render_stage(0.12)

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                process_uploaded_rfq,
                file_name=file_name,
                file_bytes=file_bytes,
                company_id=company_id,
            )

            while not future.done():
                elapsed = time.time() - start_time
                soft_value = 0.12 + 0.76 * (1 - math.exp(-elapsed / 18))
                render_stage(min(soft_value, 0.88))
                time.sleep(0.15)

            result = future.result()

        render_stage(0.94)
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        st.session_state.screen = "file_review"
        st.rerun()

    st.session_state.current_run_id = result["run_id"]
    remember_rfq_file(
        run_id=result["run_id"],
        file_name=file_name,
        file_bytes=file_bytes,
    )
    st.session_state.processed_file_name = file_name
    st.session_state.processing_error = None
    st.session_state.screen = "file_review"
    st.rerun()
