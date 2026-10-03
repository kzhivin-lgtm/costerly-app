from __future__ import annotations

import streamlit as st


def apply_projects_css() -> None:
    st.markdown(
        """
        <style>
        .projects-screen-active { display: none; }
        .stApp:has(.projects-screen-active) .costerly-app-header { display: none !important; }
        .stApp:has(.projects-screen-active) .block-container {
            width: min(1180px, calc(100vw - 48px));
            max-width: 1180px;
            padding-top: 42px !important;
            padding-bottom: 80px;
        }
        .projects-title {
            margin: 0 0 30px;
            color: var(--color-text-strong);
            font-family: var(--font-sans);
            font-size: clamp(34px, 4vw, 48px);
            line-height: 1.05;
            letter-spacing: -0.04em;
        }
        .projects-card {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            gap: 24px;
            min-height: 76px;
            padding: 18px 22px;
            margin-bottom: 12px;
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 14px;
        }
        .projects-card-title { font-size: 18px; font-weight: 750; color: var(--color-text-strong); }
        .projects-card-meta { margin-top: 5px; color: rgba(42, 31, 44, 0.58); font-size: 14px; }
        .projects-card-value { color: var(--color-text-strong); font-size: 15px; font-weight: 700; text-align: right; }
        .projects-empty {
            padding: 54px 28px;
            text-align: center;
            color: rgba(42, 31, 44, 0.58);
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 16px;
        }
        .projects-back { margin-bottom: 18px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
