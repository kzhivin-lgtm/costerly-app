from __future__ import annotations

import streamlit as st

from state.session import init_state, get_company_id
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
    if requested_screen in {"objects", "object_detail", "file_review"}:
        st.session_state.screen = requested_screen
        requested_run_id = st.query_params.get("run_id")
        requested_estimate_id = st.query_params.get("estimate_id")
        requested_object_id = st.query_params.get("object_id")
        object_detail_edit_line = st.query_params.get("od_edit_line")
        object_detail_edit_field = st.query_params.get("od_edit_field")
        object_detail_edit_value = st.query_params.get("od_edit_value")
        object_detail_approve_after = st.query_params.get("od_approve_after")
        object_detail_snapshot = st.query_params.get("od_snapshot")
        if requested_run_id:
            st.session_state.current_run_id = requested_run_id
        if requested_estimate_id:
            st.session_state.current_estimate_id = requested_estimate_id
            if requested_run_id:
                st.session_state.current_estimate_run_id = requested_run_id
        if requested_object_id:
            st.session_state.current_object_id = requested_object_id
        if (
            requested_screen == "object_detail"
            and requested_estimate_id
            and requested_object_id
            and object_detail_snapshot
        ):
            st.session_state.object_detail_last_snapshot_debug = {
                "received": True,
                "chars": len(object_detail_snapshot),
            }
            st.session_state.object_detail_pending_snapshot = {
                "estimate_id": requested_estimate_id,
                "object_id": requested_object_id,
                "snapshot": object_detail_snapshot,
            }
            if object_detail_approve_after == "1":
                st.session_state.object_detail_approve_after_edit = True
        elif (
            requested_screen == "object_detail"
            and requested_estimate_id
            and requested_object_id
            and object_detail_edit_line
            and object_detail_edit_field
            and object_detail_edit_value is not None
        ):
            st.session_state.object_detail_pending_edit = {
                "estimate_id": requested_estimate_id,
                "object_id": requested_object_id,
                "line_id": object_detail_edit_line,
                "field": object_detail_edit_field,
                "value": object_detail_edit_value,
            }
            if object_detail_approve_after == "1":
                st.session_state.object_detail_approve_after_edit = True
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
