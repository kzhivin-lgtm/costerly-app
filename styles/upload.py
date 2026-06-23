from __future__ import annotations

import streamlit as st


def apply_upload_css() -> None:
    """Style the first upload screen and the native Streamlit file uploader.

    Called only by screens/upload.py. The native file uploader remains the real
    input; this CSS replaces its visual layer with the Costerly upload block.
    Dragover uses ui/js_guards.py to toggle stable class names on Streamlit's
    native dropzone.
    """
    st.markdown(
        """
        <style>
        
        .stApp:has(.upload-screen-active) .block-container {
            width: 100% !important;
            max-width: none !important;
            min-height: 100vh !important;
            padding: 0 var(--space-4) !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            transform: translateY(32px);
        }

        .upload-screen {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .upload-screen__stack {
            width: min(100%, 1040px);
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }

        .upload-screen__logo {
            width: 323px;
            max-width: 70vw;
            height: auto;
            display: block;
            margin: 0 0 38px 0;
        }

        .upload-screen__hero {
            margin: 0 0 58px 0;
            color: var(--color-purple, var(--primitive-purple-900));
            font-family: var(--font-hero);
            font-size: 46px;
            font-weight: 400;
            font-synthesis: none;
            letter-spacing: -0.045em;
            line-height: 1.18;
            text-align: center;
            -webkit-font-smoothing: antialiased;
            text-rendering: geometricPrecision;
        }

        div[data-testid="stFileUploader"] {
            width: var(--upload-width) !important;
            max-width: var(--upload-width) !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        div[data-testid="stFileUploader"] > label,
        div[data-testid="stFileUploader"] label {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
            position: relative !important;
            width: 100% !important;
            height: var(--upload-height) !important;
            min-height: var(--upload-height) !important;
            padding: 0 !important;
            margin: 0 !important;
            border: 2px solid var(--color-purple, var(--primitive-purple-900)) !important;
            border-radius: var(--radius-lg) !important;
            background: var(--color-surface) !important;
            box-shadow: none !important;
            outline: none !important;
            overflow: hidden !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: background-color 130ms ease, border-color 130ms ease !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] > div,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] button {
            opacity: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::before {
            content: "📎 Drop or upload" !important;
            position: absolute !important;
            inset: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: var(--color-purple, var(--primitive-purple-900)) !important;
            font-family: "Garet", var(--font-brand) !important;
            font-size: 28px !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            letter-spacing: -0.01em !important;
            text-align: center !important;
            pointer-events: none !important;
            z-index: 2 !important;
            background: transparent !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover {
            background: var(--color-upload-lilac) !important;
            border-color: var(--color-accent) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover::before {
            content: "" !important;
            width: 94px !important;
            height: 94px !important;
            margin: auto !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 21 V79 M21 50 H79' stroke='white' stroke-width='8' stroke-linecap='round' fill='none'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-size: contain !important;
            transform: none !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
            background: var(--color-upload-peach) !important;
            border-color: var(--color-upload-orange) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover:hover {
            background: var(--color-upload-lilac) !important;
            border-color: var(--color-accent) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *::before,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *::after {
            box-shadow: none !important;
        }

        @media (max-width: 760px) {
            .stApp:has(.upload-screen-active) .block-container {
                transform: translateY(24px);
            }

            .upload-screen__logo {
                width: min(248px, 72vw);
                margin-bottom: 38px;
            }

            .upload-screen__hero {
                font-size: clamp(30px, 9vw, 40px);
                line-height: 1.12;
                letter-spacing: -0.045em;
                margin-bottom: 58px;
            }

            div[data-testid="stFileUploader"] {
                width: min(100%, var(--upload-width)) !important;
                max-width: min(100%, var(--upload-width)) !important;
            }

            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::before {
                content: "📎 Upload file" !important;
                font-size: 22px !important;
            }

            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover::before {
                content: "" !important;
                width: 82px !important;
                height: 82px !important;
            }
        }

        @media (max-height: 760px) and (max-width: 760px) {
            .stApp:has(.upload-screen-active) .block-container {
                transform: translateY(16px);
            }

            .upload-screen__logo {
                margin-bottom: 34px;
            }

            .upload-screen__hero {
                margin-bottom: 52px;
            }
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )
