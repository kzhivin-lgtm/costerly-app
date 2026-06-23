from __future__ import annotations

import html

import streamlit as st

from styles.post_upload import apply_post_upload_css


def render_post_upload_header(title: str, subtitle: str | None = None) -> None:
    """Render the fixed-origin header used after the Upload screen.

    Processing, File Review, and future detail screens should use this helper
    instead of raw markdown headings so their title starts at the same pixel.
    """
    apply_post_upload_css()

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="post-upload-subtitle">{html.escape(subtitle)}</div>'

    st.markdown(
        '<div class="post-upload-shell">'
        f'<h1 class="post-upload-title">{html.escape(title)}</h1>'
        f'{subtitle_html}'
        '</div>',
        unsafe_allow_html=True,
    )
