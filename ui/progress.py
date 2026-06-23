from __future__ import annotations

import streamlit as st


def apply_progress_css() -> None:
    """Install the shared Costerly progress bar styling."""
    st.markdown(
        """
        <style>
        .custom-progress-track {
            width: 100%;
            height: var(--progress-height);
            border-radius: 999px;
            background: #D85A5A;
            overflow: hidden;
        }

        .custom-progress-fill {
            height: 100%;
            min-width: 0;
            border-radius: 999px;
            background: var(--color-progress-blue);
            transition: width 140ms linear;
        }

        .custom-progress-fill.is-running {
            background: linear-gradient(
                90deg,
                var(--color-progress-blue) 0%,
                #68A7FF 52%,
                var(--color-progress-blue) 100%
            );
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
