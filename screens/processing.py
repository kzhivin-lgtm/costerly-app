from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import streamlit as st

from ui.js_guards import clear_upload_processing_shell
from ui.processing_forecast import estimate_file_review_seconds
from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from use_cases.rfq_processing import build_file_review_data, process_uploaded_rfq
from db.repositories import fetch_recent_rfq_processing_cycles
from db.supabase_client import get_supabase_client


def expected_file_review_seconds(
    page_count: int | None, *, history: list[dict] | None = None,
) -> float:
    """Return the current forecast to File Review, not only Detection time."""
    return float(estimate_file_review_seconds(history or [], page_count=page_count)["seconds"])


def _load_processing_history(company_id: str) -> list[dict]:
    """Best-effort same-company history, deliberately outside the RFQ critical path."""
    try:
        return fetch_recent_rfq_processing_cycles(
            get_supabase_client(), company_id=company_id,
        )
    except Exception as exc:
        print(f"[Processing Forecast] History unavailable: {exc}")
        return []


def render_processing_screen(company_id: str, *, trace=None) -> None:
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
        expected_file_review_seconds_value: float | None = None,
    ) -> None:
        stage_slot.markdown(
            processing_stage_html(
                marker_id=PROCESSING_MARKER_ID,
                progress_value=progress_value,
                elapsed_seconds=elapsed_seconds,
                complete=complete,
                processing_phase=processing_phase,
                expected_file_review_seconds=expected_file_review_seconds_value,
            ),
            unsafe_allow_html=True,
        )

    render_stage(
        0.04,
        processing_phase="ocr",
        expected_file_review_seconds_value=expected_file_review_seconds(None),
    )
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
        phase_state: dict[str, object] = {
            "value": "ocr", "page_count": None,
            "expected_file_review_seconds": expected_file_review_seconds(None),
        }
        phase_lock = Lock()

        if trace is not None:
            trace.event("server.rfq_processing_worker_started")

        def update_phase(label: str, page_count: int | None = None) -> None:
            with phase_lock:
                previous_phase = str(phase_state["value"])
            phase = {
                "OCR reading document": "ocr",
                "Preparing document pages": "ocr",
                "Fusion and route started": "fusion",
                "Discovery started": "discovery",
                "Membership review started": "review",
                "Registry assembly started": "registry",
                "Detection Agent": "detection",
                "Saving results": "saving",
            }.get(
                label,
                (
                    "discovery" if label.startswith("Discovery batch")
                    else previous_phase
                ),
            )
            with phase_lock:
                phase_state["value"] = phase
                if page_count is not None:
                    phase_state["page_count"] = page_count
            if trace is not None:
                trace.event(
                    "server.rfq_processing_stage",
                    metadata={"stage": label, "page_count": page_count},
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            history_future = executor.submit(_load_processing_history, company_id)
            future = executor.submit(
                process_uploaded_rfq,
                file_name=file_name,
                file_bytes=file_bytes,
                company_id=company_id,
                user_id=st.session_state.get("auth_user_id"),
                progress_callback=update_phase,
            )

            history: list[dict] | None = None
            rendered_signature: tuple[str, float] | None = None
            while not future.done():
                if history is None and history_future.done():
                    history = history_future.result()
                with phase_lock:
                    page_count = phase_state["page_count"]
                    active_phase = str(phase_state["value"])
                forecast = expected_file_review_seconds(page_count, history=history)
                with phase_lock:
                    phase_state["expected_file_review_seconds"] = forecast
                signature = (active_phase, forecast)
                if signature != rendered_signature:
                    render_stage(
                        0.04,
                        processing_phase=active_phase,
                        expected_file_review_seconds_value=forecast,
                    )
                    rendered_signature = signature
                time.sleep(0.15)

            result = future.result()
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        st.session_state.screen = "file_review"
        st.rerun()

    # This marker intentionally starts before cache seeding and the existing
    # transition handshake. It lets File Review record the complete server-side
    # handoff without making either deferred worker part of this path.
    file_review_handoff_started_at = time.perf_counter()

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
    st.session_state.current_document_identity_future = result.get("document_identity_future")
    st.session_state.file_review_deferred_work = {
        "run_id": run_id,
        "naming": result.get("naming_future") is not None,
        "preview": result.get("preview_future") is not None,
        "document_identity": result.get("document_identity_future") is not None,
    }
    st.session_state.current_naming_result = None
    st.session_state.processed_file_name = file_name
    st.session_state.file_review_handoff_timing = {
        "run_id": run_id,
        "started_at": file_review_handoff_started_at,
    }
    st.session_state.processing_error = None
    st.session_state.screen = "file_review"
    st.rerun()
