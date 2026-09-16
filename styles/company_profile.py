from __future__ import annotations

import streamlit as st


def apply_company_profile_css() -> None:
    """Apply the first production pass of the shared Costerly UI system."""
    st.markdown(
        """
        <style>
        .stApp:has(.company-profile-active),
        .stApp:has(.company-profile-active) [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
            background: var(--color-bg) !important;
            color: var(--color-text) !important;
        }

        .stApp:has(.company-profile-active) .block-container {
            width: min(1120px, calc(100vw - 48px));
            max-width: 1120px;
            padding-top: 48px;
            padding-bottom: 80px;
        }

        .company-profile-heading {
            display: flex;
            align-items: center;
            gap: 14px;
            min-height: 56px;
        }

        .company-profile-heading h1 {
            margin: 0;
            color: var(--color-text-strong);
            font-family: var(--font-sans);
            font-size: clamp(32px, 4vw, 46px);
            line-height: 1.05;
            letter-spacing: -0.045em;
        }

        .company-profile-mark,
        .company-profile-mark svg {
            display: block;
            width: 42px;
            height: 42px;
            flex: 0 0 42px;
        }

        .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading) {
            align-items: center;
            margin-bottom: 28px;
        }

        .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading)
        [data-testid="stButton"] {
            display: flex;
            justify-content: flex-end;
        }

        .stApp:has(.company-profile-active) button {
            min-height: var(--button-height-md);
            border-radius: var(--button-radius) !important;
            font-size: var(--button-font-size) !important;
            font-weight: var(--button-font-weight) !important;
            transition: background-color 120ms ease, border-color 120ms ease,
                        color 120ms ease, transform 80ms ease, box-shadow 120ms ease;
        }

        .stApp:has(.company-profile-active) button:active {
            transform: translateY(1px) scale(0.99);
        }

        .stApp:has(.company-profile-active) button:focus-visible,
        .stApp:has(.company-profile-active) input:focus-visible {
            outline: 3px solid var(--input-focus-ring) !important;
            outline-offset: 2px;
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab-list"] {
            gap: 4px;
            padding: 4px;
            margin-bottom: 24px;
            border: 1px solid var(--color-border-soft);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.64);
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab"] {
            min-height: 44px;
            padding: 0 16px;
            border-radius: 8px;
            color: var(--color-text-muted);
            font-weight: 700;
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab"][aria-selected="true"] {
            background: var(--color-surface);
            color: var(--color-text-strong);
            box-shadow: 0 1px 2px rgba(42, 31, 44, 0.08);
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab-highlight"],
        .stApp:has(.company-profile-active) [data-baseweb="tab-border"] {
            display: none;
        }

        .stApp:has(.company-profile-active) h2 {
            margin: 8px 0 18px;
            color: var(--color-text-strong) !important;
            font-size: 26px;
            letter-spacing: -0.025em;
        }

        .stApp:has(.company-profile-active) h3 {
            margin: 8px 0 12px;
            color: var(--color-text-strong) !important;
            font-size: 17px;
            letter-spacing: -0.01em;
        }

        .stApp:has(.company-profile-active) div[data-testid="stForm"] {
            padding: 24px;
            border: 1px solid var(--color-border-soft);
            border-radius: 16px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .stApp:has(.company-profile-active) label,
        .stApp:has(.company-profile-active) [data-testid="stWidgetLabel"] p {
            color: var(--color-text-strong) !important;
            font-weight: 700 !important;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"],
        .stApp:has(.company-profile-active) div[data-baseweb="input"] > div,
        .stApp:has(.company-profile-active) input,
        .stApp:has(.company-profile-active) textarea {
            color-scheme: light !important;
            background: var(--input-bg) !important;
            color: var(--input-text) !important;
            -webkit-text-fill-color: var(--input-text) !important;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"] {
            min-height: var(--input-height-md);
            border-color: var(--input-border) !important;
            border-radius: var(--input-radius) !important;
            transition: border-color 120ms ease, box-shadow 120ms ease;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"]:focus-within {
            border-color: var(--input-focus-border) !important;
            box-shadow: 0 0 0 3px var(--input-focus-ring) !important;
        }

        .stApp:has(.company-profile-active) input::placeholder {
            color: var(--input-placeholder) !important;
            -webkit-text-fill-color: var(--input-placeholder) !important;
        }

        .stApp:has(.company-profile-active) details {
            border: 1px solid var(--color-border-soft);
            border-radius: 10px;
            background: #FAF8FC;
        }

        .stApp:has(.company-profile-active) details summary {
            min-height: 46px;
            align-items: center;
            color: var(--color-text-strong);
            font-weight: 700;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] {
            display: flex;
            justify-content: flex-end;
            padding-top: 8px;
        }

        .stApp:has(.company-profile-active) [data-testid="stNotification"],
        .stApp:has(.company-profile-active) [data-testid="stAlert"] {
            color-scheme: light !important;
            border-radius: 10px;
        }

        .company-profile-readonly {
            margin-bottom: 16px;
            padding: 22px;
            border: 1px solid var(--color-border-soft);
            border-radius: 14px;
            background: var(--color-surface);
        }

        .company-profile-readonly-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px 28px;
        }

        .company-profile-readonly-item {
            display: grid;
            gap: 4px;
            min-width: 0;
        }

        .company-profile-readonly-item span {
            color: var(--color-text-muted);
            font-size: 13px;
            font-weight: 600;
        }

        .company-profile-readonly-item strong {
            overflow-wrap: anywhere;
            color: var(--color-text-strong);
            font-size: 15px;
        }

        .company-profile-users {
            width: 100%;
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 12px;
            background: var(--color-surface);
        }

        .company-profile-users table {
            width: 100%;
            border-collapse: collapse;
            color: var(--color-text);
            font-family: var(--font-sans);
            font-size: 15px;
        }

        .company-profile-users th,
        .company-profile-users td {
            padding: 14px 16px;
            border-bottom: 1px solid var(--color-border-soft);
            text-align: left;
        }

        .company-profile-users th {
            background: #FAF8FC;
            color: var(--color-text-strong);
            font-weight: 700;
        }

        .company-profile-users tr:last-child td {
            border-bottom: 0;
        }

        .stApp:has(.company-profile-active) [data-testid="stCode"] {
            color-scheme: light !important;
            border: 1px solid var(--color-border-soft);
            border-radius: 10px;
            background: var(--color-surface) !important;
        }

        @media (max-width: 760px) {
            .stApp:has(.company-profile-active) .block-container {
                width: min(100% - 28px, 1120px);
                padding-top: 28px;
                padding-bottom: 48px;
            }

            .company-profile-heading h1 { font-size: 32px; }
            .company-profile-mark,
            .company-profile-mark svg {
                width: 36px;
                height: 36px;
                flex-basis: 36px;
            }

            .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading) {
                flex-wrap: wrap;
                gap: 12px;
            }

            .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading) > div {
                width: 100% !important;
                flex: 1 0 100% !important;
            }

            .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading)
            [data-testid="stButton"],
            .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading) button {
                width: 100%;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab-list"] {
                overflow-x: auto;
                justify-content: flex-start;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab"] {
                flex: 0 0 auto;
                white-space: nowrap;
            }

            .stApp:has(.company-profile-active) div[data-testid="stForm"] { padding: 18px; }
            .company-profile-readonly-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
