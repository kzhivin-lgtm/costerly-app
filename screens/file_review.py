from __future__ import annotations

import html

import streamlit as st

from state.session import reset_post_upload_flow_state
from styles.file_review import apply_file_review_css
from ui.js_guards import install_post_upload_transition_guard
from ui.layout import render_post_upload_header
from ui.perf_debug import mark_python_perf, measure_python_perf
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
    OBJECTS_MARKER_ID,
    post_upload_transition_shell_html,
)
from use_cases.estimation_start import queue_estimation_start_from_state
from use_cases.rfq_processing import load_file_review_data


def _escape(value: object) -> str:
    """Return escaped text for compact HTML card rendering."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _list_html(items: list[str], *, class_name: str) -> str:
    """Render a plain bullet list for review-card text sections."""
    if not items:
        return f'<div class="{class_name}">No major missing information detected.</div>'

    list_items = "".join(f"<li>{_escape(item)}</li>" for item in items)
    return f'<ul class="{class_name}">{list_items}</ul>'


def _metadata_rows_html(run: dict[str, object]) -> str:
    """Render the compact technical metadata rows."""
    rows = [
        ("Project name", run.get("project_name")),
        ("Partner", run.get("partner")),
        ("File name", run.get("file_name")),
        ("Pages detected", run.get("pages_detected")),
        ("Source type", run.get("source_type")),
        ("Author", run.get("author")),
        ("Document date", run.get("document_date")),
        ("Language", run.get("language")),
        ("File quality confidence", run.get("file_quality_confidence")),
        ("Run ID", run.get("run_id")),
        ("Status", run.get("status")),
    ]

    return "".join(
        '<div class="file-review-meta-row">'
        f'<div class="file-review-meta-key">{_escape(key)}</div>'
        f'<div class="file-review-meta-value">{_escape(value)}</div>'
        '</div>'
        for key, value in rows
    )


def _render_review_card(run: dict[str, object]) -> None:
    """Render the top File Review summary card."""
    missing_html = _list_html(
        run.get("missing_information", []),
        class_name="file-review-missing-list",
    )

    card_html = (
        '<div class="file-review-card">'
        '<div class="file-review-summary-grid">'
        '<div class="file-review-label">Project name:</div>'
        f'<div class="file-review-value">{_escape(run.get("project_name"))}</div>'
        '<div class="file-review-label">Partner:</div>'
        f'<div class="file-review-value">{_escape(run.get("partner"))}</div>'
        '<div class="file-review-label">File quality:</div>'
        f'<div class="file-review-value">{_escape(run.get("file_quality"))}</div>'
        '</div>'
        '<div class="file-review-divider"></div>'
        '<div class="file-review-section-title">Missing information:</div>'
        f'{missing_html}'
        '<div class="file-review-divider"></div>'
        '<details class="file-review-meta-details">'
        '<summary class="file-review-meta-summary">'
        '<span class="file-review-meta-title">Technical metadata:</span>'
        '</summary>'
        '<div class="file-review-meta-table">'
        f'{_metadata_rows_html(run)}'
        '</div>'
        '</details>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def _render_object_card(item: dict[str, object]) -> None:
    """Render one detected object card with real editable Streamlit controls."""
    object_id = str(item.get("object_id") or item.get("name") or "object")
    edit_key = f"file_review_object_edits.{object_id}"
    edits = st.session_state.setdefault("file_review_object_edits", {})
    if object_id not in edits:
        edits[object_id] = {
            "name": item.get("name") or "",
            "quantity": item.get("quantity") or "1",
            "ignored": False,
        }

    with st.container(border=True):
        st.markdown(
            '<span class="file-review-object-card-marker" aria-hidden="true" '
            'style="display:none!important;width:0;height:0;overflow:hidden;">&#8203;</span>',
            unsafe_allow_html=True,
        )

        label_name, label_qty, label_conf, label_ignore = st.columns(
            [7.4, 1.2, 1.2, 1.5],
            gap="small",
            vertical_alignment="top",
        )
        label_name.markdown(
            '<div class="file-review-top-label">Object name</div>',
            unsafe_allow_html=True,
        )
        label_qty.markdown(
            '<div class="file-review-top-label file-review-top-label-center">QTY</div>',
            unsafe_allow_html=True,
        )
        label_conf.markdown(
            '<div class="file-review-top-label file-review-top-label-center">CONF</div>',
            unsafe_allow_html=True,
        )
        label_ignore.markdown(
            '<div class="file-review-top-label file-review-top-label-empty" aria-hidden="true">&nbsp;</div>',
            unsafe_allow_html=True,
        )

        col_name, col_qty, col_conf, col_ignore = st.columns(
            [7.4, 1.2, 1.2, 1.5],
            gap="small",
            vertical_alignment="top",
        )

        edits[object_id]["name"] = col_name.text_input(
            "Object name",
            value=str(edits[object_id].get("name") or ""),
            key=f"{edit_key}.name",
            label_visibility="collapsed",
        )
        edits[object_id]["quantity"] = col_qty.text_input(
            "QTY",
            value=str(edits[object_id].get("quantity") or "1"),
            key=f"{edit_key}.quantity",
            label_visibility="collapsed",
        )
        col_conf.markdown(
            f'<div class="file-review-native-conf-value">{_escape(item.get("confidence"))}</div>',
            unsafe_allow_html=True,
        )
        ignore_clicked = col_ignore.button(
            "IGNORE",
            key=f"{edit_key}.ignore",
            use_container_width=True,
            type="secondary",
        )
        if ignore_clicked:
            edits[object_id]["ignored"] = not bool(edits[object_id].get("ignored"))

        if edits[object_id].get("ignored"):
            st.markdown(
                '<div class="file-review-native-ignored">This object will be skipped during estimation.</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="file-review-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="file-review-object-detail-grid">'
            '<div class="file-review-label">Dimensions:</div>'
            f'<div class="file-review-value">{_escape(item.get("dimensions"))}</div>'
            '<div class="file-review-label">Materials:</div>'
            f'<div class="file-review-value">{_escape(item.get("materials"))}</div>'
            '</div>'
            '<div class="file-review-divider"></div>'
            '<div class="file-review-section-title">Missing information:</div>',
            unsafe_allow_html=True,
        )
        notes_html = _list_html(
            item.get("notes", []),
            class_name="file-review-object-notes-list",
        )
        st.markdown(notes_html, unsafe_allow_html=True)


def _sync_object_edit_state(run_id: str, objects: list[dict[str, object]]) -> None:
    """Keep File Review edits scoped to the current RFQ run."""
    if st.session_state.get("file_review_object_edits_run_id") != run_id:
        st.session_state.file_review_object_edits = {}
        st.session_state.file_review_object_edits_run_id = run_id
        st.session_state.file_review_saved_ignored_object_ids = set()

    edits = st.session_state.setdefault("file_review_object_edits", {})
    active_object_ids = {
        str(item.get("object_id") or item.get("name") or "object")
        for item in objects
    }

    for object_id in list(edits.keys()):
        if object_id not in active_object_ids:
            del edits[object_id]


def _load_file_review_screen_data(run_id: str) -> tuple[dict[str, object], str | None]:
    """Load File Review data from session cache first, then Supabase."""
    cache = st.session_state.setdefault("file_review_data_cache", {})
    if run_id in cache:
        mark_python_perf("file review cache hit", run_id=run_id)
        return cache[run_id], None

    mark_python_perf("file review cache miss", run_id=run_id)
    with measure_python_perf("load file review data", run_id=run_id):
        data = load_file_review_data(run_id)
    cache[run_id] = data
    return data, None


def _render_missing_object_search() -> None:
    """Render a static second-pass search placeholder until the flow is wired."""
    card_html = (
        '<div class="file-review-missing-card">'
        '<div class="file-review-missing-collapsed">'
        '<div class="file-review-missing-title">Missing objects:</div>'
        '<div class="file-review-search-button">Search again</div>'
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def _render_action_buttons(*, run_id: str, company_id: str) -> None:
    """Render bottom File Review actions through Streamlit session routing."""
    back_col, continue_col = st.columns(2, gap="large")
    if back_col.button("BACK TO UPLOAD", type="secondary", use_container_width=True):
        reset_post_upload_flow_state()
        st.session_state.screen = "upload"
        st.rerun()

    if continue_col.button(
        "CONTINUE TO OBJECTS ESTIMATION",
        type="primary",
        use_container_width=True,
    ):
        queue_estimation_start_from_state(run_id=run_id, company_id=company_id)
        st.session_state.screen = "objects"
        st.rerun()


def render_file_review_screen(company_id: str) -> None:
    """Render File Review from the persisted detection result when available."""
    with measure_python_perf("apply file review css"):
        apply_file_review_css()

    processing_error = st.session_state.get("processing_error")
    if processing_error:
        render_post_upload_header("File Review", marker_id=FILE_REVIEW_MARKER_ID)
        install_post_upload_transition_guard([], current_marker_id=FILE_REVIEW_MARKER_ID)
        st.error(f"RFQ processing failed: {processing_error}")
        if st.button("BACK TO UPLOAD", type="secondary"):
            st.session_state.screen = "upload"
            st.session_state.processing_error = None
            st.rerun()
        return

    run_id = st.session_state.get("current_run_id")
    if run_id:
        try:
            with measure_python_perf("file review data section", run_id=run_id):
                data, cache_warning = _load_file_review_screen_data(run_id)
        except Exception as exc:
            render_post_upload_header("File Review", marker_id=FILE_REVIEW_MARKER_ID)
            install_post_upload_transition_guard([], current_marker_id=FILE_REVIEW_MARKER_ID)
            st.error(f"Could not load RFQ run from Supabase: {exc}")
            return
    else:
        render_post_upload_header("File Review", marker_id=FILE_REVIEW_MARKER_ID)
        install_post_upload_transition_guard([], current_marker_id=FILE_REVIEW_MARKER_ID)
        st.warning("No processed RFQ run found. Upload a file to start.")
        if st.button("BACK TO UPLOAD", type="secondary"):
            st.session_state.screen = "upload"
            st.rerun()
        return

    with measure_python_perf("file review header + guard"):
        render_post_upload_header("File Review", marker_id=FILE_REVIEW_MARKER_ID)
        install_post_upload_transition_guard(
            [
                {
                    "label": "CONTINUE TO OBJECTS ESTIMATION",
                    "targetMarkerId": OBJECTS_MARKER_ID,
                    "shellHtml": post_upload_transition_shell_html(
                        title="Objects Estimation",
                        subtitle="Review objects → Set sale price → Generate proposal",
                    ),
                }
            ],
            current_marker_id=FILE_REVIEW_MARKER_ID,
        )

    with measure_python_perf("sync file review edits", object_count=len(data["objects"])):
        _sync_object_edit_state(run_id, data["objects"])

    if cache_warning:
        st.warning(cache_warning)

    with measure_python_perf("render file review card"):
        _render_review_card(data["run"])

    st.markdown(
        '<h1 class="file-review-detected-title">Detected objects</h1>',
        unsafe_allow_html=True,
    )

    with measure_python_perf("render detected object cards", object_count=len(data["objects"])):
        for item in data["objects"]:
            _render_object_card(item)

    _render_missing_object_search()

    _render_action_buttons(run_id=run_id, company_id=company_id)
