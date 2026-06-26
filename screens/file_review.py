from __future__ import annotations

import html

import streamlit as st

from styles.file_review import apply_file_review_css
from ui.js_guards import install_post_upload_transition_guard
from ui.layout import render_post_upload_header
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
    OBJECTS_MARKER_ID,
    post_upload_transition_shell_html,
)
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

        col_name, col_qty, col_conf, col_ignore = st.columns(
            [7.4, 1.2, 1.2, 1.5],
            gap="small",
            vertical_alignment="bottom",
        )

        edits[object_id]["name"] = col_name.text_input(
            "Object name",
            value=str(edits[object_id].get("name") or ""),
            key=f"{edit_key}.name",
        )
        edits[object_id]["quantity"] = col_qty.text_input(
            "QTY",
            value=str(edits[object_id].get("quantity") or "1"),
            key=f"{edit_key}.quantity",
        )
        col_conf.markdown(
            '<div class="file-review-native-conf-label">CONF</div>'
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

    edits = st.session_state.setdefault("file_review_object_edits", {})
    active_object_ids = {
        str(item.get("object_id") or item.get("name") or "object")
        for item in objects
    }

    for object_id in list(edits.keys()):
        if object_id not in active_object_ids:
            del edits[object_id]


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


def render_file_review_screen(company_id: str) -> None:
    """Render File Review from the persisted detection result when available."""
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
            data = load_file_review_data(run_id)
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

    _sync_object_edit_state(run_id, data["objects"])

    _render_review_card(data["run"])

    st.markdown(
        '<h1 class="file-review-detected-title">Detected objects</h1>',
        unsafe_allow_html=True,
    )

    for item in data["objects"]:
        _render_object_card(item)

    _render_missing_object_search()

    col_back, col_next = st.columns(2, gap="small")

    if col_back.button("BACK TO UPLOAD", type="secondary", use_container_width=True):
        st.session_state.screen = "upload"
        st.rerun()

    if col_next.button(
        "CONTINUE TO OBJECTS ESTIMATION",
        type="primary",
        use_container_width=True,
    ):
        object_edits = st.session_state.get("file_review_object_edits", {})
        st.session_state.pending_file_review_edits = {
            str(object_id): dict(edit)
            for object_id, edit in object_edits.items()
        }
        st.session_state.file_review_ignored_object_ids = {
            str(object_id)
            for object_id, edit in object_edits.items()
            if edit.get("ignored")
        }
        st.session_state.estimation_start_requested = True
        st.session_state.current_estimate_id = None
        st.session_state.current_object_id = None
        st.session_state.estimation_first_object_future = None
        st.session_state.estimation_first_object_requested = False
        st.session_state.approved_object_keys = set()
        st.session_state.last_estimation_result = None
        st.session_state.last_estimation_error = None
        st.session_state.screen = "objects"
        st.rerun()
