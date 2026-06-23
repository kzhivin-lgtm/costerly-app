from __future__ import annotations

import streamlit as st


def apply_post_upload_css() -> None:
    """Install the shared layout contract for every screen after Upload.

    Called by ui/layout.py. The same CSS class names are also reused by the
    instant upload shell so the temporary and real Processing screens align.
    """
    st.markdown(
        """
        <style>
        .stApp:not(:has(.upload-screen-active)) .block-container {
            width: var(--post-upload-width) !important;
            max-width: none !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: var(--post-upload-top) !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-bottom: var(--post-upload-bottom) !important;
            background: var(--color-bg) !important;
        }

        .post-upload-shell {
            width: 100%;
            margin: 0;
            padding: 0;
            background: var(--color-bg);
        }

        .post-upload-title {
            font-family: var(--font-mono) !important;
            color: var(--color-accent) !important;
            font-size: var(--post-upload-title-size) !important;
            line-height: var(--post-upload-title-line-height) !important;
            font-weight: 500 !important;
            letter-spacing: -0.02em !important;
            margin: 0 0 var(--post-upload-title-margin-bottom) 0 !important;
            padding: 0 !important;
        }

        .post-upload-subtitle {
            color: var(--color-text-muted) !important;
            font-family: var(--font-sans) !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            margin: var(--post-upload-subtitle-margin-top) 0 var(--post-upload-subtitle-margin-bottom) 0 !important;
            max-width: var(--post-upload-subtitle-width) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
