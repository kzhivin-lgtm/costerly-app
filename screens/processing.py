from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import streamlit as st

from ui.processing_forecast import (
    build_stage_progress_plan,
    estimate_file_review_seconds,
    stage_progress_floor,
)
from ui.processing_stage import PROCESSING_MARKER_ID, processing_stage_html
from ui.js_guards import clear_upload_processing_shell
from use_cases.rfq_processing import build_file_review_data, process_uploaded_rfq
from db.repositories import fetch_recent_rfq_processing_cycles
from db.supabase_client import get_supabase_client


def _initial_pdf_page_count(file_name: str, file_bytes: bytes) -> int | None:
    """Read the PDF page count before OCR, without rendering a page or calling AI."""
    if not file_name.lower().endswith(".pdf") or not file_bytes:
        return None
    try:
        import pymupdf

        document = pymupdf.open(stream=file_bytes, filetype="pdf")
        try:
            page_count = len(document)
        finally:
            document.close()
        return page_count if page_count > 0 else None
    except Exception as exc:
        print(f"[Processing Progress] Initial PDF page count unavailable: {exc}")
        return None


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


def _render_terminal_processing_error(stage_slot, message: object) -> None:
    """End the active Processing view in place after a terminal failure.

    A failure has no File Review run or detected-object card. Rerunning into
    File Review therefore leaves the browser transition waiting for a DOM that
    cannot exist. Rendering the explicit failure in this completed server pass
    releases the Processing shell without an auth/session round trip.
    """
    from state.session import reset_new_estimate_session, set_screen

    stage_slot.empty()
    clear_upload_processing_shell()
    st.error(f"RFQ processing failed: {message}")
    if st.button("BACK TO UPLOAD", type="secondary"):
        reset_new_estimate_session(clear_upload_widget=True)
        set_screen("upload")
        st.rerun()


def render_processing_screen(company_id: str, *, trace=None) -> None:
    """Render the processing screen while the uploaded RFQ is analyzed.

    The screen stays visual-only: it delegates the actual agent/Supabase work to
    process_uploaded_rfq().
    """
    stage_slot = st.empty()
    screen_started = time.perf_counter()
    screen_started_at_ms = int(time.time() * 1000)

    def render_stage(
        progress_value: float,
        *,
        elapsed_seconds: float = 0,
        complete: bool = False,
        processing_phase: str = "ocr",
        expected_file_review_seconds_value: float | None = None,
        processing_plan: dict | None = None,
        processing_stage_id: str | None = None,
        processing_stage_started_at_ms: int | None = None,
        processing_page_count: int | None = None,
        processing_result_run_id: str | None = None,
    ) -> None:
        stage_slot.markdown(
            processing_stage_html(
                marker_id=PROCESSING_MARKER_ID,
                progress_value=progress_value,
                elapsed_seconds=elapsed_seconds,
                complete=complete,
                processing_phase=processing_phase,
                expected_file_review_seconds=expected_file_review_seconds_value,
                processing_plan=processing_plan,
                processing_stage_id=processing_stage_id,
                processing_stage_started_at_ms=processing_stage_started_at_ms,
                processing_run_token=str(screen_started_at_ms),
                processing_page_count=processing_page_count,
                processing_result_run_id=processing_result_run_id,
            ),
            unsafe_allow_html=True,
        )

    file_name = st.session_state.get("uploaded_file_name")
    file_bytes = st.session_state.get("uploaded_file_bytes")

    if not file_name or not file_bytes:
        st.session_state.processing_error = "No uploaded RFQ file found."
        st.session_state.screen = "upload"
        st.rerun()

    if processing_error := st.session_state.get("processing_error"):
        _render_terminal_processing_error(stage_slot, processing_error)
        return

    # Page count is cheap and deterministic. It lets the one visible bar begin
    # at zero and make bounded, file-shaped progress before Fusion exists.
    initial_page_count = _initial_pdf_page_count(file_name, file_bytes)
    render_stage(
        0.0,
        processing_phase="ocr",
        processing_stage_id="pre_fusion",
        processing_page_count=initial_page_count,
    )
    if (
        st.session_state.get("current_run_id")
        and st.session_state.get("processed_file_name") == file_name
    ):
        st.session_state.screen = "file_review"
        st.rerun()

    try:
        phase_state: dict[str, object] = {
            "value": "ocr", "page_count": initial_page_count,
            "label": "OCR reading document",
            "stage_id": "pre_fusion",
            "stage_started_at_ms": screen_started_at_ms,
            "forecast_requested": False,
            "plan_input": None,
            "progress_plan": None,
        }
        phase_lock = Lock()

        if trace is not None:
            trace.event("server.rfq_processing_worker_started")

        def _stage_id(label: str, metadata: dict | None = None) -> str:
            if label.startswith("Discovery batch "):
                try:
                    return f"discovery_{int(label.split()[2])}"
                except (IndexError, ValueError):
                    return "discovery_1"
            if label.startswith("Discovery"):
                return "discovery_1"
            return {
                "Membership review started": "membership_review",
                "Membership review retry 1": "membership_review",
                "Registry assembly started": "registry_assembly",
                "Saving results": "saving",
            }.get(label, "pre_fusion")

        def update_phase(
            label: str,
            page_count: int | None = None,
            metadata: dict | None = None,
        ) -> None:
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
                phase_state["label"] = label
                phase_state["stage_id"] = _stage_id(label, metadata)
                phase_state["stage_started_at_ms"] = int(time.time() * 1000)
                if page_count is not None:
                    phase_state["page_count"] = page_count
                if label == "Fusion and route started":
                    # A visible F begins as soon as Fusion has given us a
                    # concrete page count. The exact batch-shaped plan follows
                    # immediately before the first Discovery model call.
                    phase_state["forecast_requested"] = True
                if label == "Processing plan prepared" and isinstance(metadata, dict):
                    phase_state["plan_input"] = dict(metadata)
            if trace is not None:
                trace.event(
                    "server.rfq_processing_stage",
                    metadata={"stage": label, "page_count": page_count},
                )

        # Forecast history is optional. A terminal Detection error must never
        # wait for this unrelated read before the user sees the failure.
        executor = ThreadPoolExecutor(max_workers=2)
        try:
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
            rendered_signature: tuple | None = None
            while not future.done():
                if history is None and history_future.done():
                    history = history_future.result()
                with phase_lock:
                    page_count = phase_state["page_count"]
                    active_phase = str(phase_state["value"])
                    label = str(phase_state["label"])
                    stage_id = str(phase_state["stage_id"])
                    stage_started_at_ms = int(phase_state["stage_started_at_ms"])
                    plan_input = phase_state["plan_input"]
                    progress_plan = phase_state["progress_plan"]
                    forecast_requested = bool(phase_state["forecast_requested"])
                if progress_plan is None and isinstance(plan_input, dict):
                    progress_plan = build_stage_progress_plan(
                        page_count=page_count if isinstance(page_count, int) else None,
                        elapsed_seconds=time.perf_counter() - screen_started,
                        plan_input=plan_input,
                        history=history,
                    )
                    with phase_lock:
                        phase_state["progress_plan"] = progress_plan
                forecast = (
                    float(progress_plan["forecast_seconds"])
                    if isinstance(progress_plan, dict)
                    else (
                        expected_file_review_seconds(
                            page_count if isinstance(page_count, int) else None,
                            history=history,
                        )
                        if forecast_requested else None
                    )
                )
                signature = (
                    label,
                    stage_id,
                    stage_started_at_ms,
                    forecast,
                    page_count,
                )
                if signature != rendered_signature:
                    render_stage(
                        stage_progress_floor(progress_plan, stage_id),
                        processing_phase=active_phase,
                        expected_file_review_seconds_value=forecast,
                        processing_plan=progress_plan,
                        processing_stage_id=stage_id,
                        processing_stage_started_at_ms=stage_started_at_ms,
                        processing_page_count=(
                            page_count if isinstance(page_count, int) else None
                        ),
                    )
                    rendered_signature = signature
                time.sleep(0.15)

            result = future.result()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    except Exception as exc:
        st.session_state.processing_error = str(exc)
        _render_terminal_processing_error(stage_slot, exc)
        return

    processing_plan = phase_state.get("progress_plan")
    if isinstance(processing_plan, dict):
        result.setdefault("timings", {})["forecast_seconds"] = int(
            processing_plan["forecast_seconds"]
        )

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

    # The one visible shell receives completion only after File Review's first
    # payload is ready. Its CSS transition reaches 100% immediately before the
    # rerun, rather than leaving a gray gap after a false early finish.
    render_stage(
        1.0,
        complete=True,
        processing_phase="complete",
        expected_file_review_seconds_value=(
            float(processing_plan["forecast_seconds"])
            if isinstance(processing_plan, dict) else None
        ),
        processing_plan=processing_plan if isinstance(processing_plan, dict) else None,
        processing_stage_id="complete",
        processing_result_run_id=run_id,
    )
    time.sleep(0.22)

    st.session_state.current_run_id = run_id
    # `Last Estimate` is File Review, not necessarily an estimate shell. Keep
    # its exact completed run ready for the header after the user starts a new
    # upload, so the action can use the session cache above before any query.
    st.session_state[f"_latest_estimate_route:{company_id}"] = {
        "run_id": run_id,
        "estimate_id": "",
    }
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
