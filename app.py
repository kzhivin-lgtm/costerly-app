from __future__ import annotations

import streamlit as st

from state.estimation_runs import get_estimate_for_run, remember_estimate_for_run
from state.session import init_state, get_company_id
from state.uploaded_files import get_rfq_file
from styles.base import apply_base_css
from ui.js_guards import scroll_parent_to_top
from ui.perf_debug import (
    mark_python_perf,
    measure_python_perf,
    render_python_perf_panel,
    start_python_perf_run,
)
from screens.upload import render_upload_screen
from screens.processing import render_processing_screen
from screens.file_review import render_file_review_screen
from screens.objects import render_objects_screen
from screens.object_detail import render_object_detail_screen
from use_cases.estimation import build_estimate_id
from use_cases.estimation_runtime import get_estimation_future, submit_estimation_start_command


def _queue_estimation_start_from_query(*, run_id: str, company_id: str) -> None:
    """Queue estimate setup from an HTML action link without importing screen helpers."""
    current_estimate_matches_run = (
        st.session_state.get("current_estimate_id")
        and st.session_state.get("current_estimate_run_id") == run_id
    )
    if current_estimate_matches_run:
        return

    existing_estimate_id = get_estimate_for_run(run_id)
    if existing_estimate_id:
        st.session_state.current_estimate_id = existing_estimate_id
        st.session_state.current_estimate_run_id = run_id
        active_future = get_estimation_future(existing_estimate_id)
        if active_future:
            st.session_state.estimation_cycle_future = active_future
        return

    file_name = st.session_state.get("uploaded_file_name")
    file_bytes = st.session_state.get("uploaded_file_bytes")
    if (not file_name or not file_bytes) and run_id:
        cached_file = get_rfq_file(run_id)
        if cached_file:
            file_name, file_bytes = cached_file
            st.session_state.uploaded_file_name = file_name
            st.session_state.uploaded_file_bytes = file_bytes

    if not file_name or not file_bytes:
        st.session_state.last_estimation_error = (
            "Uploaded file bytes are missing. Please upload the file again."
        )
        return

    object_edits = {
        str(object_id): dict(edit)
        for object_id, edit in st.session_state.get("file_review_object_edits", {}).items()
    }
    ignored_object_ids = {
        str(object_id)
        for object_id, edit in object_edits.items()
        if edit.get("ignored")
    }
    st.session_state.file_review_ignored_object_ids = ignored_object_ids

    estimate_id = build_estimate_id(run_id)
    remember_estimate_for_run(run_id=run_id, estimate_id=estimate_id)
    st.session_state.current_estimate_id = estimate_id
    st.session_state.current_estimate_run_id = run_id
    st.session_state.current_object_id = None
    st.session_state.approved_object_keys = set()
    st.session_state.last_estimation_result = None
    st.session_state.last_estimation_error = None
    st.session_state.estimation_cycle_future = submit_estimation_start_command(
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
        object_edits=object_edits,
        edits_changed=True,
        ignored_object_ids=ignored_object_ids,
    )
    st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)


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
    requested_screen = st.query_params.get("screen")
    if requested_screen in {"upload", "objects", "object_detail", "file_review"}:
        st.session_state.screen = requested_screen
        requested_run_id = st.query_params.get("run_id")
        requested_estimate_id = st.query_params.get("estimate_id")
        requested_object_id = st.query_params.get("object_id")
        requested_action = st.query_params.get("action")
        if requested_run_id:
            st.session_state.current_run_id = requested_run_id
        if requested_estimate_id:
            st.session_state.current_estimate_id = requested_estimate_id
            if requested_run_id:
                remember_estimate_for_run(
                    run_id=requested_run_id,
                    estimate_id=requested_estimate_id,
                )
            active_future = get_estimation_future(requested_estimate_id)
            if active_future:
                st.session_state.estimation_cycle_future = active_future
        if requested_object_id:
            st.session_state.current_object_id = requested_object_id
        if requested_action == "start_estimation" and requested_run_id:
            try:
                _queue_estimation_start_from_query(
                    run_id=requested_run_id,
                    company_id=company_id,
                )
            except Exception as exc:
                st.session_state.last_estimation_error = (
                    f"Could not start Objects Estimation: {exc}"
                )
        st.query_params.clear()

    screen = st.session_state.screen
    start_python_perf_run(screen)
    if st.session_state.get("_last_screen_for_scroll") != screen:
        scroll_parent_to_top()
        st.session_state._last_screen_for_scroll = screen
        mark_python_perf("scroll reset requested")

    with measure_python_perf("route render", screen=screen):
        if screen == "upload":
            render_upload_screen(company_id)
        elif screen == "processing":
            render_processing_screen(company_id)
        elif screen == "file_review":
            render_file_review_screen(company_id)
        elif screen == "objects":
            render_objects_screen(company_id)
        elif screen == "object_detail":
            render_object_detail_screen(company_id)
        else:
            st.session_state.screen = "upload"
            st.rerun()

    mark_python_perf("python render end", screen=screen)
    render_python_perf_panel(screen)


if __name__ == "__main__":
    main()
