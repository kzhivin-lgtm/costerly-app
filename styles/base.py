from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

FONT_DIR = Path("assets/fonts")


@lru_cache(maxsize=None)
def _font_data_uri(file_name: str) -> str:
    font_bytes = (FONT_DIR / file_name).read_bytes()
    encoded = base64.b64encode(font_bytes).decode("ascii")
    return f"data:font/woff2;base64,{encoded}"

def apply_base_css() -> None:
    """Install global Costerly design tokens and Streamlit base overrides.

    Called once from app.py before routing to a screen. Screen-specific CSS
    belongs in styles/upload.py, styles/post_upload.py, or screen modules.
    """

    garet_book_src = _font_data_uri("Garet-Book.woff2")
    garet_heavy_src = _font_data_uri("Garet-Heavy.woff2")

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        @font-face {
            font-family: "Garet";
            src: url("__GARET_BOOK_SRC__") format("woff2");
            font-weight: 400 600;
            font-style: normal;
            font-display: swap;
        }

        @font-face {
            font-family: "Garet";
            src: url("__GARET_HEAVY_SRC__") format("woff2");
            font-weight: 700 900;
            font-style: normal;
            font-display: swap;
        }

        :root {
            /* Primitive brand palette */
            --primitive-warm-bg: #F1EFEF;
            --primitive-purple-500: #8049C6;
            --primitive-purple-900: #3B2E48;
            --primitive-dark-900: #2A1F2C;
            --primitive-white: #FFFFFF;

            /* Primitive neutral palette */
            --primitive-ink-900: #17191C;
            --primitive-ink-700: #3D4046;
            --primitive-ink-500: #6B6F76;
            --primitive-ink-400: #9AA0A6;
            --primitive-line-300: #D9DCE0;
            --primitive-line-200: #E8EAED;

            /* Primitive feedback palette */
            --primitive-success-100: #E4F3EC;
            --primitive-success-500: #1F8A5B;
            --primitive-danger-100: #FBE9E8;
            --primitive-danger-500: #D6453F;

            /* Primitive upload interaction palette */
            --primitive-upload-lilac: #E8D9FF;
            --primitive-upload-peach: #FFE1D2;
            --primitive-upload-orange: #FF8A3D;
            --primitive-progress-blue: #2F80ED;

            /* Typography */
            --font-hero: var(--font-mono);
            --font-brand: "Space Grotesk", Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            --font-sans: "Space Grotesk", Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            --font-mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

            /* Spacing scale */
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-5: 24px;
            --space-6: 32px;
            --space-8: 48px;

            /* Radius scale */
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;

            /* Shared layout tokens */
            --upload-width: 600px;
            --upload-height: 200px;
            --post-upload-width: min(960px, calc(100vw - 56px));
            --post-upload-top: 73px;
            --post-upload-screen-top: 26px;
            --processing-stage-top: var(--post-upload-top);
            --post-upload-bottom: 72px;
            --post-upload-title-size: 40px;
            --post-upload-title-line-height: 1.1;
            --post-upload-title-margin-bottom: var(--space-5);
            --post-upload-heading-gap: 28px;
            --post-upload-subtitle-margin-top: calc(-1 * var(--space-3));
            --post-upload-subtitle-margin-bottom: var(--space-3);
            --post-upload-subtitle-width: 760px;
            --progress-height: 12px;

            /* Shared button tokens */
            --button-height-md: 44px;
            --button-height-lg: 56px;
            --button-radius: 10px;
            --button-font-size: 16px;
            --button-font-weight: 700;
            --button-primary-bg: var(--color-accent);
            --button-primary-bg-hover: #6F3CB4;
            --button-primary-text: #FFFFFF;
            --button-secondary-bg: #FFFFFF;
            --button-secondary-bg-hover: #FAF8FC;
            --button-secondary-text: rgba(42, 31, 44, 0.74);
            --button-secondary-border: rgba(42, 31, 44, 0.18);
            --button-danger-bg-hover: var(--color-danger-bg);
            --button-danger-text-hover: var(--color-danger);
            --button-danger-border-hover: rgba(214, 69, 63, 0.48);

            /* Shared input tokens */
            --input-height-md: 46px;
            --input-radius: 10px;
            --input-bg: #FFFFFF;
            --input-border: rgba(42, 31, 44, 0.18);
            --input-text: #17131C;
            --input-placeholder: rgba(42, 31, 44, 0.42);
            --input-focus-border: rgba(128, 73, 198, 0.72);
            --input-focus-ring: rgba(128, 73, 198, 0.14);
            --input-font-size: 18px;
            --input-font-weight: 500;
            --input-line-height: 1.2;
            --input-padding-y: 8px;
            --input-padding-x: 12px;
            --input-strong-font-size: 24px;
            --input-strong-font-weight: 800;
            --input-strong-letter-spacing: -0.035em;
            --input-compact-font-size: 22px;
            --input-compact-font-weight: 700;

            /* Shared review card rhythm */
            --review-card-gap: 20px;
        }

        :root,
        [data-costerly-theme="light"] {
            --color-bg: var(--primitive-warm-bg);
            --color-surface: var(--primitive-white);
            --color-text: var(--primitive-ink-900);
            --color-text-strong: var(--primitive-dark-900);
            --color-text-muted: var(--primitive-ink-500);
            --color-text-soft: var(--primitive-ink-400);
            --color-border: var(--primitive-line-300);
            --color-border-soft: var(--primitive-line-200);
            --color-accent: var(--primitive-purple-500);
            --color-accent-dark: var(--primitive-purple-900);
            --color-success-bg: var(--primitive-success-100);
            --color-success: var(--primitive-success-500);
            --color-danger-bg: var(--primitive-danger-100);
            --color-danger: var(--primitive-danger-500);
            --color-upload-lilac: var(--primitive-upload-lilac);
            --color-upload-peach: var(--primitive-upload-peach);
            --color-upload-orange: var(--primitive-upload-orange);
            --color-progress-blue: var(--primitive-progress-blue);
        }

        [data-costerly-theme="dark"] {
            /* Reserved for future dark theme. Values intentionally match light. */
            --color-bg: var(--primitive-warm-bg);
            --color-surface: var(--primitive-white);
            --color-text: var(--primitive-ink-900);
            --color-text-strong: var(--primitive-dark-900);
            --color-text-muted: var(--primitive-ink-500);
            --color-text-soft: var(--primitive-ink-400);
            --color-border: var(--primitive-line-300);
            --color-border-soft: var(--primitive-line-200);
            --color-accent: var(--primitive-purple-500);
            --color-accent-dark: var(--primitive-purple-900);
            --color-success-bg: var(--primitive-success-100);
            --color-success: var(--primitive-success-500);
            --color-danger-bg: var(--primitive-danger-100);
            --color-danger: var(--primitive-danger-500);
            --color-upload-lilac: var(--primitive-upload-lilac);
            --color-upload-peach: var(--primitive-upload-peach);
            --color-upload-orange: var(--primitive-upload-orange);
            --color-progress-blue: var(--primitive-progress-blue);
        }

        :root {
            /* Backward-compatible aliases while old CSS is migrated. */
            --bg: var(--color-bg);
            --surface: var(--color-surface);
            --accent-500: var(--color-accent);
            --ink-900: var(--color-text);
            --ink-700: var(--primitive-ink-700);
            --ink-500: var(--color-text-muted);
            --ink-400: var(--color-text-soft);
            --line-300: var(--color-border);
            --line-200: var(--color-border-soft);
            --mono: var(--font-mono);
            --sans: var(--font-sans);
            --orange: var(--color-accent);
            --s1: var(--space-1);
            --s2: var(--space-2);
            --s3: var(--space-3);
            --s4: var(--space-4);
            --s5: var(--space-5);
            --s6: var(--space-6);
            --s8: var(--space-8);
            --r-sm: var(--radius-sm);
            --r-md: var(--radius-md);
            --r-lg: var(--radius-lg);
        }

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {
            background: var(--color-bg) !important;
            color: var(--color-text) !important;
            font-family: var(--font-sans) !important;
        }

        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stDeployButton"],
        #GithubIcon,
        .viewerBadge_container__1QSob,
        .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK,
        .styles_viewerBadge__1yB5_ {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
        }

        button[title="View fullscreen"],
        button[title="Fullscreen"],
        button[aria-label="View fullscreen"],
        button[aria-label="Fullscreen"],
        div[data-testid="stImage"] button {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stSidebar"] {
            display: none;
        }

        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 960px;
            padding-top: 56px;
            padding-bottom: 56px;
        }

        .stApp:not(:has(.upload-screen-active)) .block-container,
        .stApp:not(:has(.upload-screen-active)) [data-testid="stMainBlockContainer"] {
            width: var(--post-upload-width) !important;
            max-width: none !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: var(--post-upload-screen-top) !important;
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

        .post-upload-stage {
            position: fixed;
            inset: 0;
            z-index: 2147482500;
            background: var(--color-bg);
            color: var(--color-text-strong);
            box-sizing: border-box;
            overflow: auto;
        }

        .post-upload-stage__inner {
            width: var(--post-upload-width);
            max-width: none;
            margin-left: auto;
            margin-right: auto;
            padding-top: var(--processing-stage-top);
            padding-left: 0;
            padding-right: 0;
            padding-bottom: var(--post-upload-bottom);
            box-sizing: border-box;
            background: var(--color-bg);
        }

        .post-upload-stage__slow {
            display: none;
            margin-top: var(--space-5);
            color: rgba(42, 31, 44, 0.62);
            font-size: 14px;
            line-height: 1.45;
        }

        .post-upload-stage__timer {
            margin-top: var(--space-3);
            color: rgba(42, 31, 44, 0.68);
            font-family: var(--font-mono);
            font-size: 14px;
            font-variant-numeric: tabular-nums;
        }

        .post-upload-stage[data-slow="true"] .post-upload-stage__slow {
            display: block;
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

        .post-upload-shell:not(:has(.post-upload-subtitle)) .post-upload-title {
            margin-bottom: 0 !important;
        }

        .post-upload-subtitle {
            color: var(--color-text-muted) !important;
            font-family: var(--font-sans) !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            margin: var(--post-upload-subtitle-margin-top) 0 var(--post-upload-subtitle-margin-bottom) 0 !important;
            max-width: var(--post-upload-subtitle-width) !important;
        }

        .post-upload-stage .post-upload-subtitle {
            color: rgba(42, 31, 44, 0.58) !important;
            font-family: var(--font-mono) !important;
            font-size: 22px !important;
            line-height: 1.2 !important;
            font-weight: 700 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            margin-top: 14px !important;
            max-width: none !important;
            white-space: nowrap !important;
        }

        .post-upload-stage .custom-progress-track {
            margin-top: var(--post-upload-heading-gap);
        }

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

        button,
        input,
        textarea,
        select {
            font-family: var(--font-sans) !important;
        }

        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {
            min-height: var(--button-height-lg) !important;
            border-radius: var(--button-radius) !important;
            font-family: var(--font-mono) !important;
            font-size: var(--button-font-size) !important;
            font-weight: var(--button-font-weight) !important;
            text-transform: uppercase !important;
            border: 1px solid var(--button-secondary-border) !important;
            transition: background 140ms ease, border-color 140ms ease, color 140ms ease, opacity 140ms ease !important;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            background: var(--button-primary-bg) !important;
            color: var(--button-primary-text) !important;
            border-color: var(--button-primary-bg) !important;
        }

        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: var(--button-primary-bg-hover) !important;
            border-color: var(--button-primary-bg-hover) !important;
            color: var(--button-primary-text) !important;
        }

        div[data-testid="stButton"] button[kind="secondary"],
        div[data-testid="stFormSubmitButton"] button {
            background: var(--button-secondary-bg) !important;
            color: var(--button-secondary-text) !important;
            border-color: var(--button-secondary-border) !important;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            background: var(--button-secondary-bg-hover) !important;
            color: var(--color-text-strong) !important;
            border-color: rgba(128, 73, 198, 0.34) !important;
        }

        div[data-testid="stButton"] button:disabled,
        div[data-testid="stButton"] button[disabled],
        div[data-testid="stFormSubmitButton"] button:disabled,
        div[data-testid="stFormSubmitButton"] button[disabled] {
            opacity: 0.56 !important;
            cursor: not-allowed !important;
        }

        @media (max-width: 760px) {
            :root {
                --upload-width: min(92vw, 600px);
                --upload-height: 180px;
                --post-upload-width: calc(100vw - 32px);
                --post-upload-top: 56px;
                --post-upload-title-size: clamp(30px, 9vw, 40px);
            }

            .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: 100% !important;
                padding-left: var(--space-4) !important;
                padding-right: var(--space-4) !important;
            }
        }
        </style>
        """

        .replace("__GARET_BOOK_SRC__", garet_book_src)
        .replace("__GARET_HEAVY_SRC__", garet_heavy_src),
        unsafe_allow_html=True,
    )
