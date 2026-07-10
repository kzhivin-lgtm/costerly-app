from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
import html

import streamlit as st

from styles.file_review import apply_file_review_css
from ui.js_guards import install_post_upload_transition_guard
from ui.layout import post_upload_header_html, render_post_upload_header
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
    OBJECTS_MARKER_ID,
    post_upload_transition_shell_html,
)
from use_cases.estimation import build_estimate_id
from use_cases.estimation_progress import set_object_progress
from use_cases.estimation_runtime import submit_estimation_job
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


def _build_review_card_html(run: dict[str, object]) -> str:
    """Build the top File Review summary card HTML."""
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

    return card_html


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
                '<div class="file-review-native-ignored">THIS OBJECT WILL BE SKIPPED DURING ESTIMATION</div>',
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
        return cache[run_id], None

    data = load_file_review_data(run_id)
    cache[run_id] = data
    return data, None


def _file_review_edits_changed(
    objects: list[dict[str, object]],
    object_edits: dict[str, dict[str, object]],
) -> bool:
    """Return whether File Review edits differ from the loaded object snapshot."""
    objects_by_id = {
        str(item.get("object_id") or item.get("name") or "object"): item
        for item in objects
    }

    for object_id, edit in object_edits.items():
        item = objects_by_id.get(str(object_id))
        if item is None:
            return True

        original_name = str(item.get("name") or "").strip()
        original_quantity = str(item.get("quantity") or "1").strip()
        edited_name = str(edit.get("name") or "").strip()
        edited_quantity = str(edit.get("quantity") or "1").strip()

        if edited_name != original_name:
            return True
        if edited_quantity != original_quantity:
            return True
        saved_ignored_ids = st.session_state.get("file_review_saved_ignored_object_ids", set())
        if bool(edit.get("ignored")) != (str(object_id) in saved_ignored_ids):
            return True

    return False


def _objects_estimation_seed_rows(
    objects: list[dict[str, object]],
    object_edits: dict[str, dict[str, object]],
    ignored_object_ids: set[str],
) -> list[dict[str, object]]:
    """Build the immediate Objects screen rows from the reviewed object snapshot."""
    rows = []
    for item in objects:
        object_id = str(item.get("object_id") or item.get("name") or "object")
        if object_id in ignored_object_ids:
            continue

        edit = object_edits.get(object_id, {})
        rows.append(
            {
                "object_key": object_id,
                "name": str(edit.get("name") or item.get("name") or "Untitled object"),
                "materials": "",
                "quantity": str(edit.get("quantity") or item.get("quantity") or "1"),
                "self_cost_unit": "pending",
                "status": "pending",
                "progress_percent": 0,
                "progress_updated_at": None,
                "sale_price_unit": None,
                "sale_price_total": None,
                "suggestion": "suggested: SC + 30%",
                "reviewed": False,
            }
        )

    return rows


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
    def install_continue_transition_guard() -> None:
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

    st.markdown(
        (
            '<div class="file-review-title-card-shell">'
            + post_upload_header_html("File Review", marker_id=FILE_REVIEW_MARKER_ID)
            + _build_review_card_html(data["run"])
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
    install_continue_transition_guard()

    _sync_object_edit_state(run_id, data["objects"])

    if cache_warning:
        st.warning(cache_warning)

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
        edits_changed = _file_review_edits_changed(data["objects"], object_edits)
        object_edits_snapshot = {
            str(object_id): dict(edit)
            for object_id, edit in object_edits.items()
        }
        ignored_object_ids = {
            str(object_id)
            for object_id, edit in object_edits_snapshot.items()
            if edit.get("ignored")
        }
        st.session_state.file_review_ignored_object_ids = ignored_object_ids
        st.session_state.objects_estimation_seed_rows = _objects_estimation_seed_rows(
            data["objects"],
            object_edits_snapshot,
            ignored_object_ids,
        )
        current_estimate_matches_run = (
            st.session_state.get("current_estimate_id")
            and st.session_state.get("current_estimate_run_id") == run_id
        )
        current_estimate_id = st.session_state.get("current_estimate_id")
        current_estimate_run_id = st.session_state.get("current_estimate_run_id")
        if (
            current_estimate_id
            and current_estimate_run_id != run_id
            and str(current_estimate_id).startswith(f"{run_id}_estimate_")
        ):
            st.session_state.current_estimate_run_id = run_id
            current_estimate_matches_run = True
        create_shell = bool(edits_changed or not current_estimate_matches_run)
        current_future = st.session_state.get("estimation_first_object_future")
        estimation_job_active = isinstance(current_future, Future) and not current_future.done()
        should_submit_estimation = create_shell or (
            estimation_job_active and not current_estimate_matches_run
        )
        if should_submit_estimation:
            file_name = st.session_state.get("uploaded_file_name")
            file_bytes = st.session_state.get("uploaded_file_bytes")
            if not file_name or not file_bytes:
                st.session_state.last_estimation_error = (
                    "Uploaded file bytes are missing. Please upload the file again."
                )
                st.rerun()
                return

            estimate_id = (
                build_estimate_id(run_id)
                if create_shell
                else str(st.session_state.get("current_estimate_id"))
            )
            if create_shell:
                st.session_state.current_estimate_id = estimate_id
                st.session_state.current_estimate_run_id = run_id
                st.session_state.current_object_id = None
                st.session_state.approved_object_keys = set()
                st.session_state.last_estimation_result = None
                st.session_state.last_estimation_error = None
            _mark_first_object_estimation_started(estimate_id)
            st.session_state.estimation_first_object_future = submit_estimation_job(
                estimate_id=estimate_id,
                run_id=run_id,
                company_id=company_id,
                file_name=file_name,
                file_bytes=file_bytes,
                object_edits=object_edits_snapshot,
                edits_changed=edits_changed,
                ignored_object_ids=ignored_object_ids,
                create_shell=create_shell,
            )
            st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
        elif current_estimate_matches_run:
            st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(
                str(st.session_state.get("current_estimate_id"))
            )

        st.session_state.screen = "objects"
        st.rerun()


def _mark_first_object_estimation_started(estimate_id: str) -> None:
    """Seed the first visible row so the next screen does not flash all pending."""
    seed_rows = st.session_state.get("objects_estimation_seed_rows")
    if not seed_rows:
        return

    first_row = seed_rows[0]
    object_id = str(first_row.get("object_key") or "")
    if not object_id:
        return

    now = datetime.now(UTC).isoformat()
    first_row["status"] = "running"
    first_row["self_cost_unit"] = "1%"
    first_row["progress_percent"] = 1
    first_row["progress_updated_at"] = now
    set_object_progress(
        estimate_id=estimate_id,
        object_id=object_id,
        percent=1,
        status="running",
    )
