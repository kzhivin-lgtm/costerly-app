from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ui.js_guards import clear_upload_processing_shell
from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from use_cases.rfq_processing import process_uploaded_rfq


def render_processing_screen(company_id: str) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    The screen stays visual-only: it delegates the actual agent/Supabase work to
    process_uploaded_rfq().
    """
    stage_slot = st.empty()

    def render_stage(
        progress_value: float,
        *,
        elapsed_seconds: float = 0,
        complete: bool = False,
        processing_phase: str = "ocr",
    ) -> None:
        stage_slot.markdown(
            processing_stage_html(
                marker_id=PROCESSING_MARKER_ID,
                progress_value=progress_value,
                elapsed_seconds=elapsed_seconds,
                complete=complete,
                processing_phase=processing_phase,
            ),
            unsafe_allow_html=True,
        )

    render_stage(0.08, processing_phase="ocr")
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
        phase_state = {"value": "ocr"}

        def update_phase(label: str) -> None:
            phase_state["value"] = {
                "OCR reading document": "ocr",
                "Detection Agent": "detection",
                "Saving results": "saving",
            }.get(label, phase_state["value"])

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                process_uploaded_rfq,
                file_name=file_name,
                file_bytes=file_bytes,
                company_id=company_id,
                progress_callback=update_phase,
            )

            rendered_phase = "ocr"
            while not future.done():
                active_phase = phase_state["value"]
                if active_phase != rendered_phase:
                    render_stage(
                        {"ocr": 0.08, "detection": 0.32, "saving": 0.92}[active_phase],
                        processing_phase=active_phase,
                    )
                    rendered_phase = active_phase
                time.sleep(0.15)

            result = future.result()
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        st.session_state.screen = "file_review"
        st.rerun()

    # Let the user see a genuine completed lap before the review screen replaces
    # the processing stage. The browser-owned timer remains authoritative.
    render_stage(1.0, complete=True, processing_phase="complete")
    time.sleep(0.25)

    st.session_state.current_run_id = result["run_id"]
    st.session_state.current_ocr_package = result.get("ocr_package")
    st.session_state.current_agent_timings = result.get("timings")
    st.session_state.processed_file_name = file_name
    st.session_state.processing_error = None
    st.session_state.screen = "file_review"
    st.rerun()
