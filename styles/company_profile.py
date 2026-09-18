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

        .stApp:has(.company-profile-active) .costerly-app-header,
        .stApp:has(.company-profile-active) [data-testid="stElementContainer"]:has(.costerly-app-header),
        .stApp:has(.company-profile-active) .st-key-costerly_header_controls {
            display: none !important;
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
            margin-bottom: 34px;
        }

        .st-key-company_profile_actions [data-testid="stHorizontalBlock"] {
            align-items: center;
            gap: 10px;
        }

        .st-key-company_profile_actions [data-testid="stButton"],
        .st-key-company_profile_actions [data-testid="stButton"] > div,
        .st-key-company_profile_actions button {
            width: 100%;
        }

        .st-key-company_profile_actions button {
            height: 40px !important;
            min-height: 40px !important;
            max-height: 40px !important;
            padding: 0 12px !important;
            font-size: 13px !important;
            font-weight: 700 !important;
        }

        .st-key-company_profile_actions button p {
            font-size: 13px !important;
            white-space: nowrap !important;
        }

        .st-key-company_profile_actions [data-testid="stColumn"]:last-child button p::before {
            content: "";
            display: inline-block;
            width: 16px;
            height: 16px;
            margin-right: 7px;
            vertical-align: -3px;
            background: currentColor;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H5.8A1.8 1.8 0 0 0 4 5.8v12.4A1.8 1.8 0 0 0 5.8 20H10'/%3E%3Cpath d='M14 8l4 4-4 4'/%3E%3Cpath d='M8 12h10'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H5.8A1.8 1.8 0 0 0 4 5.8v12.4A1.8 1.8 0 0 0 5.8 20H10'/%3E%3Cpath d='M14 8l4 4-4 4'/%3E%3Cpath d='M8 12h10'/%3E%3C/svg%3E") center / contain no-repeat;
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
            gap: 6px;
            padding: 6px;
            margin-bottom: 28px;
            border: 1px solid var(--color-border-soft);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.64);
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab"] {
            min-height: 62px;
            padding: 0 26px;
            border-radius: 10px;
            color: var(--color-text-muted);
            font-size: 18px;
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

        .stApp:has(.company-profile-active) div[data-testid="stForm"],
        .stApp:has(.company-profile-active) .st-key-company_metrics_card {
            padding: 28px;
            border: 1px solid var(--color-border-soft);
            border-radius: 18px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .stApp:has(.company-profile-active) label,
        .stApp:has(.company-profile-active) [data-testid="stWidgetLabel"] p {
            color: var(--color-text-strong) !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            line-height: 1.35 !important;
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

        .stApp:has(.company-profile-active) [data-testid="stTextInputRootElement"],
        .stApp:has(.company-profile-active) div[data-baseweb="input"],
        .stApp:has(.company-profile-active) div[data-baseweb="base-input"] {
            min-height: 52px !important;
            border: 1px solid #CEC5D1 !important;
            border-radius: var(--input-radius) !important;
            box-shadow: none !important;
            transition: border-color 120ms ease, box-shadow 120ms ease;
        }

        .stApp:has(.company-profile-active) [data-testid="stTextInput"]:focus-within [data-testid="stTextInputRootElement"],
        .stApp:has(.company-profile-active) [data-testid="stTextInput"]:focus-within div[data-baseweb="input"],
        .stApp:has(.company-profile-active) [data-testid="stTextInput"]:focus-within div[data-baseweb="base-input"] {
            border-color: var(--input-focus-border) !important;
            box-shadow: 0 0 0 3px var(--input-focus-ring) !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stTextInputRootElement"] > div,
        .stApp:has(.company-profile-active) div[data-baseweb="input"] > div {
            border: 0 !important;
            outline: 0 !important;
            box-shadow: none !important;
        }

        .stApp:has(.company-profile-active) input {
            min-height: 50px !important;
            padding: 0 16px !important;
            caret-color: #8049C6 !important;
            font-size: 16px !important;
        }

        .stApp:has(.company-profile-active) [data-testid="InputInstructions"],
        .stApp:has(.company-profile-active) [data-testid="stInputInstructions"],
        .stApp:has(.company-profile-active) [class*="InputInstructions"] {
            display: none !important;
        }

        .stApp:has(.company-profile-active) input::placeholder {
            color: var(--input-placeholder) !important;
            -webkit-text-fill-color: var(--input-placeholder) !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] {
            padding-top: 8px;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"],
        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] > div,
        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"],
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] > div,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button {
            width: 100% !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"] {
            min-height: 60px !important;
            margin-top: 8px !important;
            background: #8049C6 !important;
            border: 1px solid #8049C6 !important;
            color: #FFFFFF !important;
            font-family: var(--font-sans) !important;
            font-size: 19px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            box-shadow: 0 8px 22px rgba(128, 73, 198, 0.22) !important;
            transition: background 150ms ease, border-color 150ms ease,
                        transform 150ms ease, box-shadow 150ms ease !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button p,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"] p {
            color: #FFFFFF !important;
            font-family: var(--font-sans) !important;
            font-size: 19px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button:hover,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"]:hover {
            background: #6F3CB4 !important;
            border-color: #6F3CB4 !important;
            color: #FFFFFF !important;
            box-shadow: 0 12px 28px rgba(111, 60, 180, 0.34) !important;
            transform: translateY(-1px);
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button:active,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"]:active {
            background: #6131A3 !important;
            border-color: #6131A3 !important;
            transform: translateY(0) scale(0.995);
        }

        .company-metric-group {
            min-height: 50px;
            display: flex;
            align-items: center;
            margin: 10px 0 0 !important;
            padding: 0 12px;
            background: rgba(128, 73, 198, 0.075);
            color: rgba(42, 31, 44, 0.68);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .st-key-company_metrics_header {
            margin-top: 18px;
            padding: 0;
        }

        .st-key-company_metrics_header [data-testid="stHorizontalBlock"],
        [class*="st-key-company_metric_row_"] [data-testid="stHorizontalBlock"] {
            display: grid !important;
            grid-template-columns: minmax(260px, 2.1fr) repeat(3, minmax(0, 1fr));
            gap: 0 !important;
            align-items: stretch !important;
        }

        .st-key-company_metrics_header [data-testid="stColumn"],
        [class*="st-key-company_metric_row_"] [data-testid="stColumn"] {
            width: auto !important;
            min-width: 0 !important;
            flex: none !important;
            display: flex;
            align-items: center;
        }

        .st-key-company_metrics_header [data-testid="stColumn"] {
            min-height: 42px;
            padding: 8px 12px;
        }

        [class*="st-key-company_metric_row_"] [data-testid="stColumn"] {
            min-height: 36px;
            padding: 4px 12px;
        }

        .st-key-company_metrics_header [data-testid="stColumn"]:not(:first-child),
        [class*="st-key-company_metric_row_"] [data-testid="stColumn"]:not(:first-child) {
            justify-content: center;
        }

        .st-key-company_metrics_header [data-testid="stColumn"] > div,
        [class*="st-key-company_metric_row_"] [data-testid="stColumn"] > div {
            width: 100%;
        }

        .st-key-company_metrics_header p {
            margin: 0 !important;
            color: var(--color-text-strong) !important;
            font-family: var(--font-mono) !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        [class*="st-key-company_metric_row_"] {
            padding: 0;
            border-bottom: 1px solid rgba(42, 31, 44, 0.10);
        }

        [class*="st-key-company_metric_row_"] > [data-testid="stVerticalBlock"],
        [class*="st-key-company_metric_row_"] [data-testid="stVerticalBlockBorderWrapper"] > div {
            gap: 0 !important;
        }

        [class*="st-key-company_metric_row_"][class*="_last"] {
            border-bottom: 0;
        }

        [class*="st-key-company_metric_row_"] [data-testid="stTextInput"] {
            width: min(100%, 132px);
            margin: 0 auto;
        }

        [class*="st-key-company_metric_row_"] [data-testid="stTextInputRootElement"],
        [class*="st-key-company_metric_row_"] div[data-baseweb="input"],
        [class*="st-key-company_metric_row_"] div[data-baseweb="base-input"] {
            min-height: 28px !important;
            border-color: rgba(42, 31, 44, 0.18) !important;
            border-radius: 8px !important;
        }

        [class*="st-key-company_metric_row_"] input {
            min-height: 26px !important;
            padding: 0 8px !important;
            font-family: var(--font-mono) !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            text-align: center;
        }

        .company-metric-name,
        .company-metric-readonly {
            display: flex;
            min-height: 28px;
            align-items: center;
            line-height: 1.24;
        }

        .company-metric-name {
            color: var(--color-text-strong);
            font-size: 13px;
            font-weight: 500;
        }

        .company-metric-readonly {
            justify-content: center;
            padding: 0;
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
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

            .st-key-company_profile_actions [data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important;
            }

            .st-key-company_profile_actions [data-testid="stColumn"] {
                width: calc(50% - 5px) !important;
                flex: 1 1 calc(50% - 5px) !important;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab-list"] {
                overflow-x: auto;
                justify-content: flex-start;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab"] {
                flex: 0 0 auto;
                white-space: nowrap;
            }

            .stApp:has(.company-profile-active) div[data-testid="stForm"],
            .stApp:has(.company-profile-active) .st-key-company_metrics_card { padding: 18px; }
            .company-profile-readonly-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
