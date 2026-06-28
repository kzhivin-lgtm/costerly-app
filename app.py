from __future__ import annotations

import streamlit as st

from state.estimation_runs import remember_estimate_for_run
from state.session import init_state, get_company_id, reset_post_upload_flow_state
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
from use_cases.estimation_runtime import get_estimation_future


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
        if requested_screen == "upload":
            reset_post_upload_flow_state()
        requested_run_id = st.query_params.get("run_id")
        requested_estimate_id = st.query_params.get("estimate_id")
        requested_object_id = st.query_params.get("object_id")
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
        st.query_params.clear()
    elif st.session_state.get("screen") == "upload":
        reset_post_upload_flow_state()

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
