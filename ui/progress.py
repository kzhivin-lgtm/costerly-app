from __future__ import annotations

import streamlit as st


def apply_progress_css() -> None:
    """Keep progress styling explicit while CSS lives in styles/base.py."""
    return None


def render_progress_bar(progress_value: float, *, running: bool = True) -> None:
    """Render a clamped progress bar using the shared post-upload classes."""
    value = max(0.0, min(1.0, float(progress_value)))
    width = round(value * 100, 1)
    running_class = " is-running" if running else ""

    st.markdown(
        f'<div class="custom-progress-track">'
        f'<div class="custom-progress-fill{running_class}" style="width:{width}%;"></div>'
        '</div>',
        unsafe_allow_html=True,
    )
