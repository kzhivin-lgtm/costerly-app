from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from ui.js_guards import clear_upload_processing_shell
from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from use_cases.rfq_processing import build_file_review_data, process_uploaded_rfq


def expected_detection_seconds(page_count: int | None) -> float:
    """Return a conservative Detection pacing bucket from OCR page count."""
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        return 28.0
    if page_count <= 2:
        return 14.0
    if page_count <= 6:
        return 18.0
    if page_count <= 12:
        return 28.0
    if page_count <= 20:
        return 45.0
    return 60.0


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
        expected_detection_seconds_value: float | None = None,
    ) -> None:
        stage_slot.markdown(
            processing_stage_html(
                marker_id=PROCESSING_MARKER_ID,
                progress_value=progress_value,
                elapsed_seconds=elapsed_seconds,
                complete=complete,
                processing_phase=processing_phase,
                expected_detection_seconds=expected_detection_seconds_value,
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
        phase_state: dict[str, object] = {"value": "ocr", "page_count": None}

        def update_phase(label: str, page_count: int | None = None) -> None:
            phase_state["value"] = {
                "OCR reading document": "ocr",
                "Preparing document pages": "ocr",
                "Detection Agent": "detection",
                "Saving results": "saving",
            }.get(label, phase_state["value"])
            if page_count is not None:
                phase_state["page_count"] = page_count

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                process_uploaded_rfq,
                file_name=file_name,
                file_bytes=file_bytes,
                company_id=company_id,
                user_id=st.session_state.get("auth_user_id"),
                progress_callback=update_phase,
            )

            rendered_phase = "ocr"
            while not future.done():
                active_phase = phase_state["value"]
                if active_phase != rendered_phase:
                    render_stage(
                        {"ocr": 0.08, "detection": 0.13, "saving": 0.96}[active_phase],
                        processing_phase=active_phase,
                        expected_detection_seconds_value=(
                            expected_detection_seconds(phase_state.get("page_count"))
                            if active_phase == "detection"
                            else None
                        ),
                    )
                    rendered_phase = active_phase
                time.sleep(0.15)

            result = future.result()
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        st.session_state.screen = "file_review"
        st.rerun()

    # Seed the first File Review from the exact validated payload that Processing
    # has just persisted. Refresh and restored sessions still reload Supabase.
    run_id = result["run_id"]
    st.session_state.setdefault("file_review_data_cache", {})[run_id] = (
        build_file_review_data(
            result["detection_result"],
            timings=result.get("timings"),
        )
    )

    # Give the existing 80 ms browser watcher one bounded handshake window to
    # observe the complete marker and install transition masking before rerun.
    # The former 250 ms delay was unnecessarily visible; 120 ms preserves the
    # no-fragment contract while the cached File Review keeps the handoff fast.
    render_stage(1.0, complete=True, processing_phase="complete")
    time.sleep(0.12)

    st.session_state.current_run_id = run_id
    st.session_state.current_ocr_package = result.get("ocr_package")
    st.session_state.current_agent_timings = result.get("timings")
    st.session_state.current_naming_future = result.get("naming_future")
    st.session_state.current_preview_future = result.get("preview_future")
    st.session_state.file_review_deferred_work = {
        "run_id": run_id,
        "naming": result.get("naming_future") is not None,
        "preview": result.get("preview_future") is not None,
    }
    st.session_state.current_naming_result = None
    st.session_state.processed_file_name = file_name
    st.session_state.processing_error = None
    st.session_state.screen = "file_review"
    st.rerun()
