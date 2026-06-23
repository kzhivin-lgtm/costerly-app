from __future__ import annotations

import html

import streamlit as st

from dev.fixtures.file_review import FILE_REVIEW_FIXTURE
from styles.file_review import apply_file_review_css
from ui.layout import render_post_upload_header


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
    """Render one detected object card."""
    notes_html = _list_html(
        item.get("notes", []),
        class_name="file-review-object-notes-list",
    )

    card_html = (
        '<div class="file-review-object-card">'
        '<div class="file-review-object-edit-grid">'
        '<label class="file-review-object-edit-group">'
        '<span class="file-review-object-edit-label">Object name</span>'
        f'<input class="file-review-object-name-input" type="text" value="{_escape(item.get("name"))}" />'
        '</label>'
        '<label class="file-review-object-edit-group file-review-object-qty-group">'
        '<span class="file-review-object-edit-label file-review-object-edit-label-center">QTY</span>'
        f'<input class="file-review-object-qty-input" type="number" min="0" value="{_escape(item.get("quantity"))}" />'
        '</label>'
        '<div class="file-review-object-confidence">'
        '<div class="file-review-object-edit-label file-review-object-edit-label-center">CONF</div>'
        f'<div class="file-review-object-confidence-value">{_escape(item.get("confidence"))}</div>'
        '</div>'
        '<button class="file-review-object-ignore-button" type="button">Ignore</button>'
        '</div>'
        '<div class="file-review-divider"></div>'
        '<div class="file-review-object-detail-grid">'
        '<div class="file-review-label">Dimensions:</div>'
        f'<div class="file-review-value">{_escape(item.get("dimensions"))}</div>'
        '<div class="file-review-label">Materials:</div>'
        f'<div class="file-review-value">{_escape(item.get("materials"))}</div>'
        '</div>'
        '<div class="file-review-divider"></div>'
        '<div class="file-review-section-title">Missing information:</div>'
        f'{notes_html}'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def _render_missing_object_search() -> None:
    """Render second-pass object search controls as app-owned HTML."""
    card_html = (
        '<div class="file-review-missing-card">'
        '<input class="file-review-missing-toggle" id="file-review-missing-toggle" type="checkbox" />'
        '<div class="file-review-missing-collapsed">'
        '<div class="file-review-missing-title">Missing objects:</div>'
        '<label class="file-review-search-button" for="file-review-missing-toggle">Search again</label>'
        '</div>'
        '<div class="file-review-missing-expanded">'
        '<div class="file-review-search-row">'
        '<div class="file-review-search-label">Object name:</div>'
        '<input class="file-review-search-input" type="text" '
        'placeholder="Example: wall shelf, reception desk, curtain rod system" />'
        '</div>'
        '<div class="file-review-search-row">'
        '<div class="file-review-search-label">Search hint:</div>'
        '<input class="file-review-search-input" type="text" '
        'placeholder="Example: check page 3, small metal bracket near ceiling detail." />'
        '</div>'
        '<div class="file-review-search-actions">'
        '<button class="file-review-search-button" type="button">Search again</button>'
        '<label class="file-review-search-button file-review-search-button--cancel" '
        'for="file-review-missing-toggle">Cancel</label>'
        '</div>'
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def render_file_review_screen(company_id: str) -> None:
    """Render File Review with temporary visual fixture data.

    The fixture is only for screen construction while the detection use case is
    not connected. Production data will later arrive as a DetectionResult.
    """
    apply_file_review_css()
    render_post_upload_header("File Review")

    data = FILE_REVIEW_FIXTURE
    _render_review_card(data["run"])

    st.markdown(
        '<h1 class="file-review-detected-title">Detected objects</h1>',
        unsafe_allow_html=True,
    )

    for item in data["objects"]:
        _render_object_card(item)

    _render_missing_object_search()

    col_back, col_next, col_gap = st.columns([1, 1, 3.5])

    if col_back.button("BACK TO UPLOAD", type="secondary", use_container_width=True):
        st.session_state.screen = "upload"
        st.rerun()

    if col_next.button(
        "CONTINUE TO OBJECTS",
        disabled=True,
        type="primary",
        use_container_width=True,
    ):
        st.session_state.screen = "objects"
        st.rerun()
