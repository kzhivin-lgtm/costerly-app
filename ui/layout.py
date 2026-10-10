from __future__ import annotations

import html
import base64
from functools import lru_cache
from pathlib import Path
from typing import Callable

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
    return (
        post_upload_title_html(title, class_name=class_name, marker_id=marker_id)
        + post_upload_subtitle_html(subtitle, class_name=class_name)
    )


def post_upload_title_html(
    title: str,
    *,
    class_name: str | None = None,
    marker_id: str | None = None,
) -> str:
    """Return the title-only half of a server-rendered workflow header."""
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
        '</div>'
    )


def post_upload_subtitle_html(subtitle: str | None, *, class_name: str | None = None) -> str:
    """Return a separately laid-out workflow subtitle, when one exists."""
    if not subtitle:
        return ""
    shell_class = "post-upload-shell post-upload-screen-shell"
    if class_name:
        shell_class = f"{shell_class} {html.escape(class_name)}"
    return (
        f'<div class="{shell_class}">'
        f'<div class="post-upload-subtitle">{html.escape(subtitle)}</div>'
        '</div>'
    )


def render_post_upload_header(
    title: str,
    subtitle: str | None = None,
    *,
    class_name: str | None = None,
    marker_id: str | None = None,
    render_header_controls: Callable[[], None] | None = None,
) -> None:
    """Render the fixed-origin header used after the Upload screen.

    Processing, File Review, and future detail screens should use this helper
    instead of raw markdown headings so their title starts at the same pixel.
    """
    apply_post_upload_css()

    def render_title() -> None:
        st.markdown(
            post_upload_title_html(
                title,
                class_name=class_name,
                marker_id=marker_id,
            ),
            unsafe_allow_html=True,
        )

    render_screen_header(
        render_title,
        render_header_controls,
        render_below_title=(
            (lambda: st.markdown(post_upload_subtitle_html(subtitle, class_name=class_name), unsafe_allow_html=True))
            if subtitle
            else None
        ),
    )


def render_screen_header(
    render_title: Callable[[], None],
    render_header_controls: Callable[[], None] | None = None,
    *,
    render_below_title: Callable[[], None] | None = None,
    render_below_controls: Callable[[], None] | None = None,
) -> None:
    """Render the one native header grid used by authenticated screens.

    The rail must be a sibling of the screen title in Streamlit's server tree.
    CSS positioning cannot make a root-level widget reliably participate in a
    screen header's document flow after Streamlit reconciliation. Optional
    second-row slots preserve the identical left/right axes for screen-specific
    detail content, such as Object Detail's preview.
    """
    if render_header_controls is None:
        render_title()
        if render_below_title is not None:
            render_below_title()
        if render_below_controls is not None:
            render_below_controls()
        return

    title_column, actions_column = st.columns([3, 2], gap="small", vertical_alignment="center")
    with title_column:
        render_title()
    with actions_column:
        render_header_controls()

    if render_below_controls is None and render_below_title is not None:
        render_below_title()
        return

    if render_below_title is not None or render_below_controls is not None:
        details_column, preview_column = st.columns([3, 2], gap="small", vertical_alignment="top")
        with details_column:
            if render_below_title is not None:
                render_below_title()
        with preview_column:
            if render_below_controls is not None:
                render_below_controls()
