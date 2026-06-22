from __future__ import annotations

import streamlit as st


def apply_base_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --costerly-bg: #F1EFEF;
            --costerly-accent: #8049C6;
            --costerly-purple: #3B2E48;
            --costerly-dark: #2A1F2C;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--costerly-bg);
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container {
            max-width: 960px;
            padding-top: 56px;
            padding-bottom: 56px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
