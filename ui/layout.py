from __future__ import annotations

import html
import base64
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import streamlit as st

from styles.post_upload import apply_post_upload_css


@lru_cache(maxsize=1)
def _workflow_mark_src() -> str:
    """Return the brand mark without adding a network request to a header."""
    mark = Path("assets/brand/costelry_mark_indigo.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(mark).decode("ascii")


def _workflow_title_html(title: str) -> str:
    """Place the workflow mark before the full, established title text."""
    return (
        '<span class="workflow-title-primary">'
        '<span class="workflow-title-mark" aria-hidden="true">'
        f'<img src="{_workflow_mark_src()}" alt="">'
        '</span>'
        f'<span class="workflow-title-text">{html.escape(title)}</span>'
        '</span>'
    )


def post_upload_header_html(
    title: str,
    subtitle: str | None = None,
    *,
    class_name: str | None = None,
    marker_id: str | None = None,
) -> str:
    """Return the shared post-upload header HTML."""
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="post-upload-subtitle">{html.escape(subtitle)}</div>'

    marker_html = ""
    if marker_id:
        marker_html = f'<div id="{html.escape(marker_id)}" style="display:none"></div>'

    shell_class = "post-upload-shell post-upload-screen-shell"
    if class_name:
        shell_class = f"{shell_class} {html.escape(class_name)}"

    return (
        f'<div class="{shell_class}">'
        f'{marker_html}'
        '<h1 class="post-upload-title workflow-title">'
        f'{_workflow_title_html(title)}'
        '</h1>'
        f'{subtitle_html}'
        '</div>'
    )


def render_post_upload_header(
    title: str,
    subtitle: str | None = None,
    *,
    class_name: str | None = None,
    marker_id: str | None = None,
) -> None:
    """Render the fixed-origin header used after the Upload screen.

    Processing, File Review, and future detail screens should use this helper
    instead of raw markdown headings so their title starts at the same pixel.
    """
    apply_post_upload_css()

    st.markdown(
        post_upload_header_html(
            title,
            subtitle,
            class_name=class_name,
            marker_id=marker_id,
        ),
        unsafe_allow_html=True,
    )


def render_workflow_header(
    title: str,
    subtitle: str | None = None,
    *,
    class_name: str | None = None,
    marker_id: str | None = None,
    render_actions: Callable[[], None] | None = None,
) -> None:
    """Render a workflow title and its actions in one vertically aligned row."""
    if render_actions is None:
        render_post_upload_header(
            title,
            subtitle,
            class_name=class_name,
            marker_id=marker_id,
        )
        return

    apply_post_upload_css()
    with st.container(key="workflow_header_row"):
        title_column, actions_column = st.columns(
            (1, 1), gap="small", vertical_alignment="center"
        )
        with title_column:
            st.markdown(
                post_upload_header_html(
                    title,
                    subtitle,
                    class_name=class_name,
                    marker_id=marker_id,
                ),
                unsafe_allow_html=True,
            )
        with actions_column:
            render_actions()
