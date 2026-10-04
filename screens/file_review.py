from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
import html
import time

import streamlit as st

from state.session import set_screen
from state.session import get_company_id
from styles.file_review import apply_file_review_css
from ui.js_guards import (
    install_workflow_header_alignment_guard,
)
from ui.layout import post_upload_header_html, render_post_upload_header
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
)
from use_cases.estimation import build_estimate_id
from use_cases.estimation_progress import set_object_progress
from use_cases.estimation_runtime import submit_estimation_job
from use_cases.latest_estimate import load_latest_estimate_route_for_run
from use_cases.rfq_processing import (
    load_file_review_data,
    load_file_review_naming_publication,
    load_file_review_preview_publication,
    save_file_review_object_name,
    save_file_review_run_metadata,
)
from use_cases.estimation_artifacts import evidence_signed_url
from db.supabase_client import get_supabase_client


_RUN_METADATA_LABELS = {
    "project_name": "Project name",
    "partner": "Partner",
    "client": "Client",
}


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
        ("Client", run.get("client")),
        ("File name", run.get("file_name")),
        ("Pages detected", run.get("pages_detected")),
        ("Author", run.get("author")),
        ("Document date", run.get("document_date")),
        ("File quality", run.get("file_quality")),
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


def _object_id(item: dict[str, object]) -> str:
    """Return the stable File Review object key used by edits and seed rows."""
    return str(item.get("object_id") or item.get("name") or "object")


def _default_object_edit(item: dict[str, object]) -> dict[str, object]:
    """Build the editable state shape for one detected object."""
    return {
        "name": item.get("name") or "",
        "quantity": item.get("quantity") or "1",
        "ignored": False,
    }


def _ensure_object_edit(object_id: str, item: dict[str, object]) -> dict[str, object]:
    """Return mutable edit state for a detected object in the current session."""
    edits = st.session_state.setdefault("file_review_object_edits", {})
    if object_id not in edits:
        edits[object_id] = _default_object_edit(item)
    return edits[object_id]


def _sync_run_metadata_state(run_id: str, run: dict[str, object]) -> None:
    """Keep editable project metadata scoped to one RFQ run."""
    if st.session_state.get("file_review_run_metadata_run_id") == run_id:
        return
    for field in _RUN_METADATA_LABELS:
        st.session_state.pop(f"file_review_run_metadata.{field}", None)
    st.session_state.file_review_run_metadata_run_id = run_id
    st.session_state.file_review_run_metadata = {
        field: str(run.get(field) or "unknown").strip() or "unknown"
        for field in _RUN_METADATA_LABELS
    }
    st.session_state.file_review_metadata_save_error = None


def _commit_run_metadata(run_id: str, field: str, widget_key: str) -> None:
    """Persist one Project, Partner, or Client edit on Enter or blur."""
    edits = st.session_state.setdefault("file_review_run_metadata", {})
    previous_value = str(edits.get(field) or "unknown")
    submitted_value = str(st.session_state.get(widget_key) or "").strip()
    if not submitted_value:
        st.session_state[widget_key] = previous_value
        st.session_state.file_review_metadata_save_error = None
        st.session_state.screen = "file_review"
        return

    try:
        saved = save_file_review_run_metadata(
            run_id=run_id,
            values={field: submitted_value},
        )
    except Exception as exc:
        st.session_state[widget_key] = previous_value
        st.session_state.file_review_metadata_save_error = str(exc)
    else:
        saved_value = saved[field]
        edits[field] = saved_value
        cache = st.session_state.setdefault("file_review_data_cache", {})
        data = cache.get(run_id)
        if isinstance(data, dict) and isinstance(data.get("run"), dict):
            data["run"][field] = saved_value
        st.session_state.file_review_metadata_save_error = None
    st.session_state.screen = "file_review"


def _run_metadata_snapshot() -> dict[str, str]:
    """Return the current File Review metadata draft for Continue."""
    edits = st.session_state.get("file_review_run_metadata") or {}
    return {
        field: str(
            st.session_state.get(f"file_review_run_metadata.{field}")
            or edits.get(field)
            or ""
        ).strip()
        for field in _RUN_METADATA_LABELS
    }


def _commit_object_name(run_id: str, object_id: str, widget_key: str) -> None:
    """Save a name committed with Enter or by leaving its input field."""
    edits = st.session_state.setdefault("file_review_object_edits", {})
    edit = edits.setdefault(object_id, {})
    previous_name = str(edit.get("name") or "")
    submitted_name = str(st.session_state.get(widget_key) or "").strip()

    # A Streamlit widget can briefly report an empty value while its previous
    # screen is unmounted. Empty is never a valid user edit, so retain the
    # canonical File Review value instead of sending a destructive save.
    if not submitted_name:
        st.session_state[widget_key] = previous_name
        st.session_state.file_review_name_save_error = None
        st.session_state.screen = "file_review"
        return

    try:
        saved_name = save_file_review_object_name(
            run_id=run_id,
            object_id=object_id,
            object_name=submitted_name,
        )
    except Exception as exc:
        st.session_state[widget_key] = previous_name
        st.session_state.file_review_name_save_error = str(exc)
    else:
        edit["name"] = saved_name
        cache = st.session_state.setdefault("file_review_data_cache", {})
        data = cache.get(run_id)
        if isinstance(data, dict):
            for item in data.get("objects") or []:
                if _object_id(item) == object_id:
                    item["name"] = saved_name
                    break
        st.session_state.file_review_name_save_error = None

    st.session_state.screen = "file_review"


def _timing_html(timings: dict[str, object] | None) -> str:
    if not timings:
        return ""

    def seconds(key: str) -> str:
        try:
            return f"{float(timings.get(key) or 0):.1f}s"
        except (TypeError, ValueError):
            return "—"

    naming_html = ""
    try:
        if float(timings.get("naming_seconds") or 0) > 0:
            naming_html = f'<span>Naming background <strong>{seconds("naming_seconds")}</strong></span>'
    except (TypeError, ValueError):
        pass

    return (
        '<div class="file-review-divider"></div>'
        '<div class="file-review-timing-row">'
        f'<span>OCR <strong>{seconds("ocr_seconds")}</strong></span>'
        f'<span>Detection <strong>{seconds("detection_seconds")}</strong></span>'
        f'{naming_html}'
        f'<span>Total lap <strong data-costerly-total-lap>{seconds("total_seconds")}</strong></span>'
        '</div>'
    )


def _merged_timings(
    in_session: object, persisted: object,
) -> dict[str, object] | None:
    """Prefer the live cycle values, but never hide completed async timing."""
    if not isinstance(in_session, dict) and not isinstance(persisted, dict):
        return None
    result = dict(persisted) if isinstance(persisted, dict) else {}
    if isinstance(in_session, dict):
        result.update(in_session)
    try:
        persisted_naming = float((persisted or {}).get("naming_seconds") or 0)
        session_naming = float((in_session or {}).get("naming_seconds") or 0)
        result["naming_seconds"] = max(persisted_naming, session_naming)
    except (AttributeError, TypeError, ValueError):
        pass
    return result


def _build_review_card_details_html(
    run: dict[str, object],
    timings: dict[str, object] | None = None,
) -> str:
    """Build the non-editable remainder of the File Review summary card."""
    missing_html = _list_html(
        run.get("missing_information", []),
        class_name="file-review-missing-list",
    )

    return (
        '<div class="file-review-summary-grid">'
        '<div class="file-review-label">File quality:</div>'
        f'<div class="file-review-value">{_escape(run.get("file_quality"))}</div>'
        '</div>'
        '<div class="file-review-divider"></div>'
        '<div class="file-review-section-title">Missing information:</div>'
        f'{missing_html}'
        f'{_timing_html(timings)}'
        '<div class="file-review-divider"></div>'
        '<details class="file-review-meta-details">'
        '<summary class="file-review-meta-summary">'
        '<span class="file-review-meta-title">Technical metadata:</span>'
        '</summary>'
        '<div class="file-review-meta-table">'
        f'{_metadata_rows_html(run)}'
        '</div>'
        '</details>'
    )


def _render_review_card(
    *,
    run_id: str,
    run: dict[str, object],
    timings: dict[str, object] | None,
) -> None:
    """Render editable project metadata inside the established summary card."""
    with st.container(border=True):
        st.markdown(
            '<span class="file-review-summary-card-marker" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
        for field, label in _RUN_METADATA_LABELS.items():
            label_col, input_col = st.columns(
                [1.8, 6.2], gap="small", vertical_alignment="center"
            )
            label_col.markdown(
                f'<div class="file-review-label">{_escape(label)}:</div>',
                unsafe_allow_html=True,
            )
            widget_key = f"file_review_run_metadata.{field}"
            canonical_value = str(
                st.session_state.file_review_run_metadata.get(field) or "unknown"
            )
            if widget_key not in st.session_state:
                st.session_state[widget_key] = canonical_value
            input_col.text_input(
                label,
                key=widget_key,
                max_chars=240,
                on_change=_commit_run_metadata,
                args=(run_id, field, widget_key),
                label_visibility="collapsed",
            )

        st.markdown(
            _build_review_card_details_html(run, timings),
            unsafe_allow_html=True,
        )


def _render_object_card(item: dict[str, object]) -> None:
    """Render one detected object card with real editable Streamlit controls."""
    object_id = _object_id(item)
    edit_key = f"file_review_object_edits.{object_id}"
    edit = _ensure_object_edit(object_id, item)

    with st.container(border=True):
        st.markdown(
            '<span class="file-review-object-card-marker" aria-hidden="true" '
            'style="display:none!important;width:0;height:0;overflow:hidden;">&#8203;</span>',
            unsafe_allow_html=True,
        )
        card_main, card_preview = st.columns([8, 1], gap="small", vertical_alignment="top")
        preview_ref = item.get("preview_ref")
        preview_html = '<div class="file-review-preview-placeholder"><span></span></div>'
        if isinstance(preview_ref, str):
            preview_url = evidence_signed_url(
                client=get_supabase_client(), storage_ref=preview_ref,
                company_id=get_company_id(),
            )
            if preview_url:
                preview_html = (
                    '<div class="file-review-preview-box">'
                    f'<img src="{html.escape(preview_url, quote=True)}" alt="Object preview">'
                    '</div>'
                )
        elif item.get("preview_pending"):
            preview_html = (
                '<div class="file-review-preview-placeholder" aria-label="Preview is preparing">'
                '<span class="file-review-preview-spinner"></span>'
                '</div>'
            )
        card_preview.markdown(preview_html, unsafe_allow_html=True)

        name_slot, _ = card_main.columns([7, 3], gap="small", vertical_alignment="top")
        name_slot.markdown(
            '<div class="file-review-top-label">Object name</div>',
            unsafe_allow_html=True,
        )

        name_widget_key = f"{edit_key}.name"
        canonical_name = str(edit.get("name") or "")
        current_widget_name = str(st.session_state.get(name_widget_key) or "")
        if name_widget_key not in st.session_state or (
            canonical_name and not current_widget_name.strip()
        ):
            st.session_state[name_widget_key] = canonical_name
        edit["name"] = name_slot.text_input(
            "Object name",
            key=name_widget_key,
            on_change=_commit_object_name,
            args=(
                str(st.session_state.get("current_run_id") or ""),
                object_id,
                name_widget_key,
            ),
            label_visibility="collapsed",
        )
        label_qty, label_conf, label_ignore = name_slot.columns(
            [1.3, 1.3, 1.7], gap="small", vertical_alignment="top",
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
        col_qty, col_conf, col_ignore = name_slot.columns(
            [1.3, 1.3, 1.7], gap="small", vertical_alignment="top",
        )
        edit["quantity"] = col_qty.text_input(
            "QTY",
            value=str(edit.get("quantity") or "1"),
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
            edit["ignored"] = not bool(edit.get("ignored"))

        if edit.get("ignored"):
            st.markdown(
                '<div class="file-review-native-ignored">THIS OBJECT WILL BE SKIPPED DURING ESTIMATION</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="file-review-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="file-review-object-detail-grid">'
            '<div class="file-review-label">Dimensions:</div>'
            f'<div class="file-review-value">{_escape(item.get("dimensions"))}</div>'
            '</div>'
            '<div class="file-review-divider"></div>'
            '<div class="file-review-section-title">Notes:</div>',
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
        st.session_state.file_review_initial_object_names = {}

    edits = st.session_state.setdefault("file_review_object_edits", {})
    initial_names = st.session_state.setdefault("file_review_initial_object_names", {})
    active_object_ids = {_object_id(item) for item in objects}

    for object_id in list(edits.keys()):
        if object_id not in active_object_ids:
            del edits[object_id]
            initial_names.pop(object_id, None)

    for item in objects:
        object_id = _object_id(item)
        initial_names.setdefault(object_id, str(item.get("name") or ""))


def _load_file_review_screen_data(run_id: str) -> dict[str, object]:
    """Load File Review data from session cache first, then Supabase."""
    cache = st.session_state.setdefault("file_review_data_cache", {})
    if run_id not in cache:
        cache[run_id] = load_file_review_data(run_id)
    return cache[run_id]


def _publish_persisted_naming(
    run_id: str, result: dict[str, object],
) -> bool:
    """Apply one durable Naming publication without reloading File Review."""
    status = str(result.get("status") or "pending")
    if status == "pending":
        return False

    published_key = f"file_review_naming_published.{run_id}"
    if st.session_state.get(published_key):
        return False
    st.session_state[published_key] = True

    if status != "succeeded":
        return True

    names = result.get("names") or {}
    if not isinstance(names, dict):
        return True
    cache = st.session_state.setdefault("file_review_data_cache", {})
    data = cache.get(run_id)
    if isinstance(data, dict):
        edits = st.session_state.setdefault("file_review_object_edits", {})
        initial_names = st.session_state.setdefault("file_review_initial_object_names", {})
        for item in data.get("objects") or []:
            object_id = _object_id(item)
            new_name = str(names.get(object_id) or "")
            if not new_name:
                continue
            initial_name = str(initial_names.get(object_id) or item.get("name") or "")
            edit = edits.get(object_id)
            if isinstance(edit, dict) and str(edit.get("name") or "") == initial_name:
                edit["name"] = new_name
                widget_key = f"file_review_object_edits.{object_id}.name"
                if st.session_state.get(widget_key) == initial_name:
                    st.session_state[widget_key] = new_name
            item["name"] = new_name

    timings = st.session_state.get("current_agent_timings")
    if isinstance(timings, dict):
        timings["naming_seconds"] = float(result.get("naming_seconds") or 0)
    return True


def _collect_completed_previews() -> dict[str, object] | None:
    future = st.session_state.get("current_preview_future")
    if not isinstance(future, Future) or not future.done():
        return None
    try:
        result = dict(future.result() or {})
        timings = st.session_state.get("current_agent_timings")
        if isinstance(timings, dict):
            timings["preview_seconds"] = float(result.get("duration_seconds") or 0)
    except Exception as exc:
        result = {"status": "failed", "error": type(exc).__name__}
    st.session_state.current_preview_future = None
    return result


def _mark_deferred_work_complete(run_id: str, work_type: str) -> None:
    work = st.session_state.get("file_review_deferred_work")
    if isinstance(work, dict) and work.get("run_id") == run_id:
        work[work_type] = False


def _has_deferred_work(run_id: str) -> bool:
    work = st.session_state.get("file_review_deferred_work")
    return bool(
        isinstance(work, dict)
        and work.get("run_id") == run_id
        and (work.get("naming") or work.get("preview"))
    )


def _publish_persisted_preview(run_id: str, result: dict[str, object]) -> bool:
    """Publish one durable Preview result and stop its File Review poll."""
    status = str(result.get("status") or "pending")
    if status == "pending":
        return False

    published_key = f"file_review_preview_published.{run_id}"
    if st.session_state.get(published_key):
        _mark_deferred_work_complete(run_id, "preview")
        return False
    st.session_state[published_key] = True
    _mark_deferred_work_complete(run_id, "preview")

    timings = st.session_state.get("current_agent_timings")
    if isinstance(timings, dict):
        timings["preview_seconds"] = float(result.get("preview_seconds") or result.get("duration_seconds") or 0)

    cache = st.session_state.setdefault("file_review_data_cache", {})
    cache.pop(run_id, None)
    if status != "succeeded":
        st.session_state[f"file_review_preview_terminal.{run_id}"] = status
    return True


def _publish_deferred_file_review_work(run_id: str) -> None:
    """Persist terminal Naming and Preview work without rerunning the app."""
    naming_result = load_file_review_naming_publication(run_id)
    naming_done = _publish_persisted_naming(run_id, naming_result)
    if naming_done:
        _mark_deferred_work_complete(run_id, "naming")
    local_preview_result = _collect_completed_previews()
    preview_result = local_preview_result or load_file_review_preview_publication(run_id)
    preview_done = _publish_persisted_preview(run_id, preview_result)
    # The enclosing fragment renders from the session cache on its next poll.
    # Do not issue an app rerun here: that briefly unmounts the global
    # navigation rail while Streamlit reconciles File Review.


@st.fragment(run_every=2.0)
def _render_file_review_dynamic_content(run_id: str) -> None:
    """Refresh only object cards while deferred artifacts become available."""
    # Naming updates a keyed text input. It must complete before this fragment
    # creates that input, otherwise Streamlit rejects the session-state write.
    # Preview publication also invalidates the cached object snapshot, so load
    # the cards only after either terminal artifact is published.
    if _has_deferred_work(run_id):
        _publish_deferred_file_review_work(run_id)

    try:
        data = _load_file_review_screen_data(run_id)
    except Exception as exc:
        st.error(f"Could not refresh File Review data: {exc}")
        return

    preview_terminal_status = st.session_state.get(f"file_review_preview_terminal.{run_id}")
    if preview_terminal_status:
        for item in data.get("objects") or []:
            if isinstance(item, dict) and not item.get("preview_ref"):
                item["preview_pending"] = False

    _sync_object_edit_state(run_id, data["objects"])

    name_save_error = st.session_state.get("file_review_name_save_error")
    if name_save_error:
        st.error(f"Could not save object name: {name_save_error}")
    metadata_save_error = st.session_state.get("file_review_metadata_save_error")
    if metadata_save_error:
        st.error(f"Could not save project details: {metadata_save_error}")

    st.markdown(
        (
            '<h1 class="file-review-detected-title">'
            f'Detected Objects: {len(data["objects"])}'
            "</h1>"
        ),
        unsafe_allow_html=True,
    )
    for item in data["objects"]:
        _render_object_card(item)
    _render_missing_object_search()


def _file_review_edits_changed(
    objects: list[dict[str, object]],
    object_edits: dict[str, dict[str, object]],
) -> bool:
    """Return whether File Review edits differ from the loaded object snapshot."""
    objects_by_id = {_object_id(item): item for item in objects}

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
        object_id = _object_id(item)
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


def _render_file_review_header_only() -> None:
    """Render File Review header when full review data is unavailable."""
    render_post_upload_header("File Review", marker_id=FILE_REVIEW_MARKER_ID)


def _back_to_upload_button(*, clear_processing_error: bool = False) -> None:
    """Render the shared Back to Upload action for non-review states."""
    from state.session import set_screen

    def return_to_upload() -> None:
        set_screen("upload")
        if clear_processing_error:
            st.session_state.processing_error = None

    st.button("BACK TO UPLOAD", type="secondary", on_click=return_to_upload)


def _back_to_upload_from_review() -> None:
    """Leave Upload with a route back to this exact File Review run."""
    run_id = str(st.session_state.get("current_run_id") or "").strip()
    if run_id:
        st.session_state.return_file_review_run_id = run_id
    set_screen("upload")


def _render_processing_error(message: object) -> None:
    """Render the File Review fallback when RFQ processing failed."""
    _render_file_review_header_only()
    st.error(f"RFQ processing failed: {message}")
    _back_to_upload_button(clear_processing_error=True)


def _render_load_error(message: object) -> None:
    """Render the File Review fallback when persisted RFQ data cannot load."""
    _render_file_review_header_only()
    st.error(f"Could not load RFQ run from Supabase: {message}")


def _render_missing_run_state() -> None:
    """Render the File Review fallback when there is no processed RFQ run."""
    _render_file_review_header_only()
    st.warning("No processed RFQ run found. Upload a file to start.")
    _back_to_upload_button()


def render_file_review_screen(company_id: str) -> None:
    """Render File Review from the persisted detection result when available."""
    apply_file_review_css()

    processing_error = st.session_state.get("processing_error")
    if processing_error:
        _render_processing_error(processing_error)
        return

    run_id = st.session_state.get("current_run_id")
    if not run_id:
        _render_missing_run_state()
        return

    try:
        data = _load_file_review_screen_data(run_id)
    except Exception as exc:
        _render_load_error(exc)
        return

    _sync_run_metadata_state(run_id, data["run"])
    with st.container():
        st.markdown(
            '<span class="file-review-title-card-shell-marker" aria-hidden="true"></span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            post_upload_header_html("File Review", marker_id=FILE_REVIEW_MARKER_ID),
            unsafe_allow_html=True,
        )
        _render_review_card(
            run_id=run_id,
            run=data["run"],
            timings=_merged_timings(st.session_state.get("current_agent_timings"), data.get("timings")),
        )
    install_workflow_header_alignment_guard()

    _render_file_review_dynamic_content(run_id)

    col_back, col_next = st.columns(2, gap="small")

    col_back.button(
        "BACK TO UPLOAD",
        type="secondary",
        use_container_width=True,
        on_click=_back_to_upload_from_review,
    )

    col_next.button(
        "CONTINUE TO OBJECTS ESTIMATION",
        type="primary",
        use_container_width=True,
        on_click=_continue_to_objects_estimation,
        kwargs={
            "company_id": company_id,
            "run_id": run_id,
            "objects": data["objects"],
        },
    )



def _object_edits_snapshot() -> dict[str, dict[str, object]]:
    """Copy current File Review edits so async estimation cannot see later mutations."""
    object_edits = st.session_state.get("file_review_object_edits", {})
    return {str(object_id): dict(edit) for object_id, edit in object_edits.items()}


def _ignored_object_ids(object_edits: dict[str, dict[str, object]]) -> set[str]:
    """Return object ids intentionally skipped by the user on File Review."""
    return {str(object_id) for object_id, edit in object_edits.items() if edit.get("ignored")}


def _current_estimate_matches_run(run_id: str) -> bool:
    """Return whether the current estimate belongs to this RFQ run.

    Older sessions may have an estimate id that encodes the run id but missed
    `current_estimate_run_id`; normalize that session state here.
    """
    current_estimate_id = st.session_state.get("current_estimate_id")
    current_estimate_run_id = st.session_state.get("current_estimate_run_id")

    if current_estimate_id and current_estimate_run_id == run_id:
        return True

    if (
        current_estimate_id
        and current_estimate_run_id != run_id
        and str(current_estimate_id).startswith(f"{run_id}_estimate_")
    ):
        st.session_state.current_estimate_run_id = run_id
        return True

    return False


def _prepare_objects_estimation_seed(
    *,
    objects: list[dict[str, object]],
    object_edits: dict[str, dict[str, object]],
    ignored_object_ids: set[str],
) -> None:
    """Store immediate Objects Estimation rows used before Supabase catches up."""
    st.session_state.file_review_ignored_object_ids = ignored_object_ids
    st.session_state.objects_estimation_seed_rows = _objects_estimation_seed_rows(
        objects,
        object_edits,
        ignored_object_ids,
    )


def _estimation_job_active() -> bool:
    """Return whether the background estimation worker is still running."""
    current_future = st.session_state.get("estimation_batch_future")
    return isinstance(current_future, Future) and not current_future.done()


def _mark_objects_estimation_cache_dirty(estimate_id: object) -> None:
    if estimate_id:
        st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(str(estimate_id))


def _submit_objects_estimation_job(
    *,
    company_id: str,
    run_id: str,
    object_edits: dict[str, dict[str, object]],
    edits_changed: bool,
    ignored_object_ids: set[str],
    create_shell: bool,
) -> bool:
    """Submit async estimation work; return False when upload bytes are missing."""
    file_name = st.session_state.get("uploaded_file_name")
    file_bytes = st.session_state.get("uploaded_file_bytes")
    if not file_name or not file_bytes:
        st.session_state.last_estimation_error = (
            "Uploaded file bytes are missing. Please upload the file again."
        )
        return False

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

    _mark_estimation_batch_started(estimate_id)
    try:
        st.session_state.estimation_batch_future = submit_estimation_job(
            estimate_id=estimate_id,
            run_id=run_id,
            company_id=company_id,
            file_name=file_name,
            file_bytes=file_bytes,
            object_edits=object_edits,
            edits_changed=edits_changed,
            ignored_object_ids=ignored_object_ids,
            create_shell=create_shell,
        )
    except Exception as exc:
        st.session_state.current_estimate_id = None
        st.session_state.current_estimate_run_id = None
        st.session_state.last_estimation_error = str(exc)
        return False
    _mark_objects_estimation_cache_dirty(estimate_id)
    return True


def _continue_to_objects_estimation(
    *,
    company_id: str,
    run_id: str,
    objects: list[dict[str, object]],
) -> None:
    """Prepare estimate state and move from File Review to Objects Estimation."""
    action_started_at = time.perf_counter()
    phase_durations_ms: dict[str, float] = {}
    action_status = "ok"
    action_error_code: str | None = None

    def record_action() -> None:
        payload: dict[str, object] = {
            "action": "continue_to_objects",
            "status": action_status,
            "duration_ms": (time.perf_counter() - action_started_at) * 1000,
            "phase_durations_ms": phase_durations_ms,
        }
        if action_error_code:
            payload["error_code"] = action_error_code
        st.session_state._runtime_completed_action = payload

    phase_started_at = time.perf_counter()
    try:
        saved_metadata = save_file_review_run_metadata(
            run_id=run_id,
            values=_run_metadata_snapshot(),
            company_id=company_id,
        )
    except Exception as exc:
        st.session_state.file_review_metadata_save_error = str(exc)
        action_status = "error"
        action_error_code = "metadata_save_failed"
        record_action()
        return
    st.session_state.file_review_run_metadata.update(saved_metadata)
    phase_durations_ms["continue_metadata_save_ms"] = (
        time.perf_counter() - phase_started_at
    ) * 1000

    phase_started_at = time.perf_counter()
    object_edits = _object_edits_snapshot()
    edits_changed = _file_review_edits_changed(objects, object_edits)
    ignored_object_ids = _ignored_object_ids(object_edits)
    _prepare_objects_estimation_seed(
        objects=objects,
        object_edits=object_edits,
        ignored_object_ids=ignored_object_ids,
    )
    phase_durations_ms["continue_seed_prepare_ms"] = (
        time.perf_counter() - phase_started_at
    ) * 1000

    current_estimate_matches_run = _current_estimate_matches_run(run_id)
    if not edits_changed and not current_estimate_matches_run:
        phase_started_at = time.perf_counter()
        try:
            from db.supabase_client import get_supabase_client

            persisted_route = load_latest_estimate_route_for_run(
                get_supabase_client(),
                company_id,
                run_id,
            )
        except Exception:
            persisted_route = None
        phase_durations_ms["continue_estimate_lookup_ms"] = (
            time.perf_counter() - phase_started_at
        ) * 1000
        if persisted_route:
            st.session_state.current_estimate_id = persisted_route["estimate_id"]
            st.session_state.current_estimate_run_id = persisted_route["run_id"]
            st.session_state.current_object_id = None
            current_estimate_matches_run = True
    create_shell = bool(edits_changed or not current_estimate_matches_run)
    should_submit_estimation = create_shell or (
        _estimation_job_active() and not current_estimate_matches_run
    )

    if should_submit_estimation:
        phase_started_at = time.perf_counter()
        submitted = _submit_objects_estimation_job(
            company_id=company_id,
            run_id=run_id,
            object_edits=object_edits,
            edits_changed=edits_changed,
            ignored_object_ids=ignored_object_ids,
            create_shell=create_shell,
        )
        phase_durations_ms["continue_estimation_submit_ms"] = (
            time.perf_counter() - phase_started_at
        ) * 1000
        if not submitted:
            action_status = "error"
            action_error_code = "estimation_submit_failed"
            record_action()
            return
    elif current_estimate_matches_run:
        _mark_objects_estimation_cache_dirty(st.session_state.get("current_estimate_id"))

    st.session_state.screen = "objects"
    record_action()


def _mark_estimation_batch_started(estimate_id: str) -> None:
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
