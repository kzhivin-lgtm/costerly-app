from __future__ import annotations

import streamlit as st

from state.estimation_runs import get_estimate_for_run, remember_estimate_for_run
from state.uploaded_files import get_rfq_file
from use_cases.estimation import build_estimate_id
from use_cases.estimation_runtime import get_estimation_future, submit_estimation_start_command


def queue_estimation_start_from_state(*, run_id: str, company_id: str) -> None:
    """Start or restore an Objects Estimation cycle from Streamlit session state."""
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
