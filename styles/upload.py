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

        html:has(.upload-screen-active),
        body:has(.upload-screen-active),
        .stApp:has(.upload-screen-active),
        .stApp:has(.upload-screen-active) [data-testid="stAppViewContainer"],
        .stApp:has(.upload-screen-active) [data-testid="stMain"] {
            height: 100vh !important;
            max-height: 100vh !important;
            overflow-y: hidden !important;
            overscroll-behavior-y: none !important;
        }
        
        .stApp:has(.upload-screen-active) .block-container {
            width: 100% !important;
            max-width: none !important;
            min-height: 100vh !important;
            padding: var(--app-content-top) var(--space-4) 72px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: flex-start !important;
            transform: none !important;
        }

        .upload-screen {
            width: 100%;
            margin-top: -9px;
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
            border: 0 !important;
            border-radius: 20px !important;
            background: #FFFFFF !important;
            box-shadow: 0 18px 48px rgba(59, 46, 72, 0.08) !important;
            outline: none !important;
            overflow: hidden !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: background-color 130ms ease, box-shadow 130ms ease !important;
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
            content: "" !important;
            position: absolute !important;
            left: 50% !important;
            top: calc(50% - 56px) !important;
            width: 46px !important;
            height: 46px !important;
            transform: translateX(-50%) !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 18 V82 M18 50 H82' stroke='%238049C6' stroke-width='9' stroke-linecap='round' fill='none'/%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: center center !important;
            background-size: contain !important;
            pointer-events: none !important;
            z-index: 2 !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::after {
            content: "Drop or upload\\A PDF/JPEG/PNG" !important;
            position: absolute !important;
            left: 0 !important;
            right: 0 !important;
            top: calc(50% + 4px) !important;
            display: block !important;
            color: rgba(42, 31, 44, 0.72) !important;
            font-family: var(--font-mono) !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            line-height: 1.55 !important;
            text-align: center !important;
            white-space: pre-line !important;
            pointer-events: none !important;
            z-index: 2 !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover {
            background: var(--color-upload-lilac) !important;
            border: 0 !important;
            box-shadow: 0 18px 48px rgba(89, 48, 137, 0.16) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover::before {
            content: "" !important;
            top: 50% !important;
            width: 88px !important;
            height: 88px !important;
            transform: translate(-50%, -50%) !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 16 V84 M16 50 H84' stroke='%238049C6' stroke-width='9' stroke-linecap='round' fill='none'/%3E%3C/svg%3E") !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover::after {
            content: "" !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
            background: #F5EFFC !important;
            border: 0 !important;
            box-shadow: 0 20px 52px rgba(89, 48, 137, 0.13) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover:hover {
            background: var(--color-upload-lilac) !important;
            border: 0 !important;
            box-shadow: 0 18px 48px rgba(89, 48, 137, 0.16) !important;
        }

        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *::before,
        div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *::after {
            box-shadow: none !important;
        }

        @media (max-width: 760px) {
            .upload-screen {
                margin-top: -7px;
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
                top: calc(50% - 50px) !important;
                width: 42px !important;
                height: 42px !important;
            }

            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::after {
                content: "Upload file\\A PDF/JPEG/PNG" !important;
                top: calc(50% + 2px) !important;
                font-size: 18px !important;
            }

            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"].costerly-upload-dragover::before {
                content: "" !important;
                top: 50% !important;
                width: 78px !important;
                height: 78px !important;
            }
        }

        @media (max-height: 760px) and (max-width: 760px) {
            .stApp:has(.upload-screen-active) .block-container {
                padding-top: 124px !important;
            }

            .upload-screen__hero {
                margin-bottom: 52px;
            }
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )
