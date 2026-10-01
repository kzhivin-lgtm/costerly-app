from __future__ import annotations

import streamlit as st


def apply_platform_admin_css() -> None:
    st.markdown(
        """
        <style>
        .stApp:has(.platform-admin-active),
        .stApp:has(.platform-admin-active) [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
            background: var(--color-bg) !important;
            color: var(--color-text) !important;
        }

        .stApp:has(.platform-admin-active) .costerly-app-header,
        .stApp:has(.platform-admin-active) [data-testid="stElementContainer"]:has(.costerly-app-header) {
            display: none !important;
        }

        /* Streamlit may retain the previous Upload tree for one reconciliation
           frame. Admin owns the frame as soon as its marker exists. */
        .stApp:has(.platform-admin-active) .upload-screen,
        .stApp:has(.platform-admin-active) [data-testid="stFileUploader"],
        .stApp:has(.platform-admin-active)
        [data-testid="stElementContainer"]:has([data-testid="stFileUploader"]) {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        .stApp:has(.platform-admin-active) .block-container {
            width: min(1540px, calc(100vw - 48px));
            max-width: 1540px;
            padding-top: 34px !important;
            padding-bottom: 80px;
        }

        .platform-admin-heading {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 56px;
        }

        .platform-admin-heading h1 {
            margin: 0;
            color: var(--color-text-strong);
            font-family: var(--font-sans);
            font-size: clamp(32px, 4vw, 46px);
            line-height: 1.05;
            letter-spacing: -0.045em;
        }

        .platform-admin-mark,
        .platform-admin-mark svg {
            display: block;
            width: 42px;
            height: 42px;
            flex: 0 0 42px;
        }

        .platform-admin-mark { transform: translateY(3px); }

        .stApp:has(.platform-admin-active)
        div[data-testid="stHorizontalBlock"]:has(.platform-admin-heading) {
            align-items: center;
            margin-bottom: 34px;
        }

        .st-key-platform_admin_actions {
            transform: translateY(10px);
        }

        .st-key-platform_admin_actions [data-testid="stHorizontalBlock"] {
            gap: 10px;
        }

        .st-key-platform_admin_actions [data-testid="stButton"],
        .st-key-platform_admin_actions [data-testid="stButton"] > div,
        .st-key-platform_admin_actions button {
            width: 100%;
        }

        .stApp:has(.platform-admin-active)
        .st-key-platform_admin_actions div[data-testid="stButton"] button {
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            padding: 0 10px !important;
            font-size: 12px !important;
            font-weight: 700 !important;
        }

        .stApp:has(.platform-admin-active)
        .st-key-platform_admin_actions div[data-testid="stButton"] button p {
            font-size: 12px !important;
            white-space: nowrap !important;
        }

        .st-key-platform_admin_sections {
            margin-bottom: 24px;
        }

        .st-key-platform_admin_sections [data-testid="stHorizontalBlock"] {
            gap: 10px;
        }

        .st-key-platform_admin_sections [data-testid="stButton"],
        .st-key-platform_admin_sections [data-testid="stButton"] > div,
        .st-key-platform_admin_sections button {
            width: 100%;
        }

        .platform-admin-table-card {
            overflow: hidden;
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 12px;
            background: var(--color-surface);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.045);
        }

        .platform-admin-table-scroll {
            overflow-x: auto;
            overscroll-behavior-inline: contain;
        }

        .platform-admin-table {
            width: 100%;
            min-width: 1210px;
            border-collapse: collapse;
            table-layout: fixed;
            font-family: var(--font-sans);
        }

        .platform-admin-table th {
            min-height: 42px;
            padding: 8px 12px;
            border-bottom: 1px solid rgba(42, 31, 44, 0.12);
            color: var(--color-text-strong);
            background: rgba(42, 31, 44, 0.045);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            line-height: 1.24;
            text-align: left;
            vertical-align: middle;
        }

        .platform-admin-table td {
            min-height: 42px;
            padding: 8px 12px;
            border-bottom: 1px solid rgba(42, 31, 44, 0.12);
            color: var(--color-text-strong);
            font-size: 13px;
            font-weight: 500;
            line-height: 1.24;
            vertical-align: middle;
        }

        .platform-admin-table tr:last-child td { border-bottom: 0; }

        .platform-admin-company {
            color: var(--color-text-strong);
            font-size: 14px;
            font-weight: 700;
            overflow-wrap: anywhere;
        }

        .platform-admin-stage,
        .platform-admin-status {
            display: inline-flex;
            align-items: center;
            min-height: 26px;
            padding: 3px 8px;
            border-radius: 999px;
            background: #F1EDF6;
            color: var(--color-accent-dark);
            font-size: 11px;
            font-weight: 700;
            text-transform: capitalize;
            white-space: nowrap;
        }

        .platform-admin-stage--paid,
        .platform-admin-status--ok {
            background: var(--color-success-bg);
            color: var(--color-success);
        }

        .platform-admin-stage--test,
        .platform-admin-status--neutral {
            background: #F0F1F2;
            color: var(--color-text-muted);
        }

        .platform-admin-status--attention {
            background: var(--color-danger-bg);
            color: var(--color-danger);
        }

        .platform-admin-metric-count {
            display: block;
            color: var(--color-text-strong);
            font-weight: 700;
            white-space: nowrap;
        }

        .platform-admin-metric-cost {
            display: block;
            margin-top: 4px;
            color: var(--color-text-muted);
            font-size: 11px;
            white-space: nowrap;
        }

        .platform-admin-empty {
            padding: 40px 24px;
            color: var(--color-text-muted);
            font-size: 14px;
            text-align: center;
        }

        .platform-admin-process-title {
            margin: 30px 0 12px;
            color: var(--color-text-strong);
            font-size: 22px;
            line-height: 1.2;
        }

        .platform-admin-route-title {
            margin: 18px 0 4px;
            color: var(--color-text-strong);
            font-size: 15px;
            line-height: 1.2;
        }

        .platform-admin-route-description {
            margin: 0 0 10px;
            color: var(--color-text-muted);
            font-size: 13px;
            line-height: 1.35;
        }

        .platform-admin-parameter-card {
            margin-bottom: 18px;
        }

        .platform-admin-parameter-table {
            min-width: 1380px;
        }

        .platform-admin-parameter-name {
            display: block;
            color: var(--color-text-strong);
            font-weight: 700;
            overflow-wrap: anywhere;
        }

        .platform-admin-parameter-code {
            display: block;
            margin-top: 3px;
            color: var(--color-text-muted);
            font-family: var(--font-mono);
            font-size: 10px;
            overflow-wrap: anywhere;
        }

        .platform-admin-parameter-empty {
            height: 56px;
            color: var(--color-text-muted) !important;
            text-align: center !important;
            vertical-align: middle !important;
        }

        .platform-admin-parameter-placeholder td {
            background: rgba(42, 31, 44, 0.018);
        }

        .platform-admin-parameter-missing {
            color: var(--color-text-muted);
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
        }

        .platform-admin-source-link {
            color: var(--color-accent-dark);
            font-weight: 700;
            text-decoration: none;
        }

        .platform-admin-source-link:hover {
            text-decoration: underline;
        }

        @media (max-width: 760px) {
            .stApp:has(.platform-admin-active) .block-container {
                width: calc(100vw - 24px);
                padding-top: 20px !important;
            }

            .platform-admin-heading h1 { font-size: 34px; }
            .platform-admin-table-card { border-radius: 12px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
