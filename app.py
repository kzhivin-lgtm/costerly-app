from __future__ import annotations

import streamlit as st

from state.session import init_state, get_company_id
from styles.base import apply_base_css
from ui.js_guards import scroll_parent_to_top, signal_app_ready_to_embed


st.set_page_config(
    page_title="costerly.ai",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _render_screen(screen: str, company_id: str) -> None:
    if screen == "upload":
        from screens.upload import render_upload_screen

        render_upload_screen(company_id)
    elif screen == "processing":
        from screens.processing import render_processing_screen

        render_processing_screen(company_id)
    elif screen == "file_review":
        from screens.file_review import render_file_review_screen

        render_file_review_screen(company_id)
    elif screen == "objects":
        from screens.objects import render_objects_screen

        render_objects_screen(company_id)
    elif screen == "object_detail":
        from screens.object_detail import render_object_detail_screen

        render_object_detail_screen(company_id)
    else:
        st.session_state.screen = "upload"
        st.rerun()


def main() -> None:
    init_state()

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
    apply_base_css()
    company_id = get_company_id()
    last_screen_for_scroll = st.session_state.get("_last_screen_for_scroll")
    if last_screen_for_scroll != screen:
        is_initial_upload_render = last_screen_for_scroll is None and screen == "upload"
        if not is_initial_upload_render:
            scroll_parent_to_top()
        st.session_state._last_screen_for_scroll = screen

    _render_screen(screen, company_id)

    signal_app_ready_to_embed(screen)


if __name__ == "__main__":
    main()
