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
            padding-top: 34px !important;
            padding-bottom: 80px;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMainBlockContainer"]
        > [data-testid="stVerticalBlock"]
        > [data-testid="stElementContainer"]:has(style),
        .stApp:has(.company-profile-active)
        [data-testid="stMainBlockContainer"]
        > [data-testid="stVerticalBlock"]
        > [data-testid="stElementContainer"]:has(.company-profile-active) {
            display: none !important;
        }

        .company-profile-heading {
            display: flex;
            align-items: center;
            gap: 8px;
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

        .company-profile-mark {
            transform: translateY(3px);
        }

        .stApp:has(.company-profile-active) div[data-testid="stHorizontalBlock"]:has(.company-profile-heading) {
            align-items: center;
            margin-bottom: 34px;
        }

        .st-key-company_profile_actions [data-testid="stHorizontalBlock"] {
            align-items: center;
            gap: 10px;
        }

        .st-key-company_profile_actions {
            transform: translateY(10px);
        }

        .st-key-company_profile_actions [data-testid="stButton"],
        .st-key-company_profile_actions [data-testid="stButton"] > div,
        .st-key-company_profile_actions button {
            width: 100%;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_profile_actions div[data-testid="stButton"] button {
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            padding: 0 10px !important;
            font-size: 12px !important;
            font-weight: 700 !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_profile_actions div[data-testid="stButton"] button p {
            font-size: 12px !important;
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

        .stApp:has(.company-profile-active)
        [data-testid="stElementContainer"]:has(.st-key-company_metrics_bridge_host),
        .st-key-company_metrics_bridge_host,
        .stApp:has(.company-profile-active)
        [data-testid="stElementContainer"]:has(.st-key-company_labor_bridge_host),
        .st-key-company_labor_bridge_host {
            display: none !important;
        }

        .st-key-company_profile_tab
        [role="tabpanel"]:has(.st-key-company_metrics_card)
        > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab-list"],
        .st-key-company_profile_tab [role="tablist"] {
            gap: 6px;
            padding: 6px;
            margin-bottom: 28px;
            border: 1px solid var(--color-border-soft);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.64);
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab"],
        .st-key-company_profile_tab [role="tab"] {
            min-height: 62px;
            padding: 0 26px;
            border-radius: 10px;
            color: var(--color-text-muted);
            font-size: 18px;
            font-weight: 500;
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab"][aria-selected="true"],
        .st-key-company_profile_tab [role="tab"][aria-selected="true"],
        .st-key-company_profile_tab [role="tab"][data-selected] {
            background: var(--color-surface);
            color: var(--color-text-strong);
            font-weight: 700 !important;
            box-shadow: 0 1px 2px rgba(42, 31, 44, 0.08);
        }

        .st-key-company_profile_tab [role="tab"][aria-selected="true"] p,
        .st-key-company_profile_tab [role="tab"][aria-selected="true"] span,
        .st-key-company_profile_tab [role="tab"][data-selected] p,
        .st-key-company_profile_tab [role="tab"][data-selected] span {
            font-weight: 700 !important;
        }

        .stApp:has(.company-profile-active) [data-baseweb="tab-highlight"],
        .stApp:has(.company-profile-active) [data-baseweb="tab-border"],
        .st-key-company_profile_tab [role="tablist"]::after,
        .st-key-company_profile_tab .react-aria-SelectionIndicator {
            display: none !important;
            content: none !important;
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
        .stApp:has(.company-profile-active) .st-key-company_metrics_card,
        .stApp:has(.company-profile-active) .st-key-company_labor_card,
        .stApp:has(.company-profile-active) [class*="st-key-company_machinery_group_"] {
            padding: 28px;
            border: 1px solid var(--color-border-soft);
            border-radius: 18px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .company-machinery-active {
            display: none;
        }

        .stApp:has(.company-machinery-active)
        [data-testid="stElementContainer"]:has(.company-machinery-active) {
            display: none;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-company_machinery_group_"] {
            margin-bottom: 24px;
            position: relative;
            gap: 0 !important;
        }

        .company-machinery-table-head {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(330px, 1fr) minmax(36px, 0.13fr);
            column-gap: 16px;
            min-height: 58px;
            padding: 0 16px;
            box-sizing: border-box;
            margin-bottom: 16px;
            align-items: center;
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 12px 12px 0 0;
            background: #FAF8FC;
            color: var(--color-text-strong);
            font-family: var(--font-mono) !important;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .company-machinery-table-head span {
            padding: 0;
        }

        .company-machinery-table-head span:nth-child(2) {
            width: min(100%, 304px);
            margin: 0 auto;
            padding: 0;
            box-sizing: border-box;
            transform: translateX(8px);
        }

        .machinery-availability-state,
        .stApp:has(.company-machinery-active)
        [data-testid="stElementContainer"]:has(.machinery-availability-state) {
            display: none !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"] {
            min-height: 70px;
            padding: 8px 16px;
            border: 1px solid var(--color-border-soft);
            border-top: 0;
            border-radius: 0;
            background: var(--color-surface);
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        > [data-testid="stVerticalBlock"] {
            justify-content: center;
            gap: 0 !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stHorizontalBlock"] {
            align-items: center;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
        > [data-testid="stVerticalBlock"] {
            align-items: center;
            justify-content: center;
        }

        .company-machinery-name {
            display: flex;
            min-height: 36px;
            align-items: center;
            color: var(--color-text-strong);
            font-size: 16px;
            font-weight: 500;
            line-height: 1.2;
        }

        .company-machinery-summary {
            margin-top: -4px;
            color: var(--color-text-muted);
            font-size: 12px;
            line-height: 1.25;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] {
            width: min(100%, 304px);
            margin: 0 auto;
            transform: translateY(8px);
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] > div {
            width: 100%;
            display: grid !important;
            grid-template-columns: 1.35fr 1fr 1fr;
            gap: 8px !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button {
            min-height: 36px;
            padding: 0 10px;
            width: 100%;
            min-width: 0;
            box-sizing: border-box;
            border-width: 1px !important;
            border-radius: 10px !important;
            font-size: 13px;
            font-weight: 400 !important;
            box-shadow: none !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button p,
        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button span {
            font-size: 13px !important;
            font-weight: inherit !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button:nth-of-type(1) {
            border-color: #F1E8C8 !important;
            background: #FFFDF5 !important;
            color: #847A59 !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button:nth-of-type(2) {
            border-color: #DCEBDF !important;
            background: #F7FBF8 !important;
            color: #66806D !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stButtonGroup"] button:nth-of-type(3) {
            border-color: #EFDEE1 !important;
            background: #FDF8F9 !important;
            color: #8A6D72 !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]:has(.machinery-selected-yes)
        [data-testid="stButtonGroup"] button:nth-child(2) {
            position: relative;
            z-index: 1;
            border-color: #33814A !important;
            background: #C5E9CF !important;
            color: #174D27 !important;
            font-weight: 700 !important;
            box-shadow: inset 0 0 0 2px #33814A !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]:has(.machinery-selected-no)
        [data-testid="stButtonGroup"] button:nth-child(3) {
            position: relative;
            z-index: 1;
            border-color: #A9384D !important;
            background: #F3C4CD !important;
            color: #6F1425 !important;
            font-weight: 700 !important;
            box-shadow: inset 0 0 0 2px #A9384D !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_row"]
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
        [data-testid="stButton"] button {
            width: 36px !important;
            min-width: 36px !important;
            height: 36px !important;
            min-height: 36px !important;
            padding: 0 !important;
            border: 1px solid var(--color-border-soft) !important;
            border-radius: 10px !important;
            background: #FAF8FC !important;
            color: var(--color-text-muted) !important;
            box-shadow: none !important;
            font-size: 18px !important;
            line-height: 1 !important;
            transform: translateY(8px) !important;
        }

        .stApp:has(.company-machinery-active)
        [data-testid="stButtonGroup"]:has(button[data-testid^="stBaseButton-pills"]) > div {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }

        .stApp:has(.company-machinery-active)
        button[data-testid^="stBaseButton-pills"] {
            min-height: 38px !important;
            padding: 7px 12px !important;
            border: 1px solid #D8D0DC !important;
            border-radius: 10px !important;
            background: #FFFFFF !important;
            color: var(--color-text-strong) !important;
            box-shadow: none !important;
            font-weight: 500 !important;
        }

        .stApp:has(.company-machinery-active)
        button[data-testid="stBaseButton-pillsActive"] {
            border-color: #4F8FCB !important;
            background: #E5F1FC !important;
            color: #174E7A !important;
            font-weight: 700 !important;
            box-shadow: inset 0 0 0 1px #4F8FCB !important;
        }

        .stApp:has(.company-machinery-active)
        button[data-testid="stBaseButton-pillsActive"] p,
        .stApp:has(.company-machinery-active)
        button[data-testid="stBaseButton-pillsActive"] span {
            color: #174E7A !important;
            font-weight: 700 !important;
        }

        /* Streamlit 1.64 uses React Aria state attributes for pills. */
        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        [data-testid="stButtonGroup"] button {
            min-height: 38px !important;
            padding: 7px 12px !important;
            border: 1px solid #D8D0DC !important;
            border-radius: 10px !important;
            background: #FFFFFF !important;
            color: var(--color-text-strong) !important;
            box-shadow: none !important;
            font-weight: 500 !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        [data-testid="stButtonGroup"] button[kind="primary"],
        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        [data-testid="stButtonGroup"] button[aria-pressed="true"],
        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        [data-testid="stButtonGroup"] button[data-selected="true"],
        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        [data-testid="stButtonGroup"] button[data-testid*="pills"][data-testid*="active" i] {
            border-color: #4F8FCB !important;
            background: #E5F1FC !important;
            color: #174E7A !important;
            font-weight: 700 !important;
            box-shadow: inset 0 0 0 1px #4F8FCB !important;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"] {
            padding: 22px 16px;
            gap: 18px !important;
            border-right: 1px solid var(--color-border-soft);
            border-bottom: 1px solid var(--color-border-soft);
            border-left: 1px solid var(--color-border-soft);
            background: #FBF9FD;
        }

        .stApp:has(.company-machinery-active)
        [class*="st-key-machinery_"][class*="_detail"]
        > [data-testid="stVerticalBlock"] {
            gap: 18px !important;
        }

        .stApp:has(.company-machinery-active) [data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--color-border-soft) !important;
            border-radius: 18px !important;
            background: var(--color-surface) !important;
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .stApp:has(.company-machinery-active) [data-testid="stExpander"] details > summary {
            min-height: 58px;
            padding: 0 22px;
        }

        .stApp:has(.company-machinery-active) [data-testid="stExpander"] details > div {
            padding: 0 22px 22px;
        }

        .stApp:has(.company-machinery-active) [class*="st-key-machinery_"][class*="_card"]
        > [data-testid="stVerticalBlock"] {
            gap: 18px !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_logo_card {
            margin-top: 12px;
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 12px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .company-logo-table-heading {
            padding: 14px 16px;
            border-bottom: 1px solid var(--color-border-soft);
            background: #FAF8FC;
            color: var(--color-text-strong);
            font-family: var(--font-mono) !important;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .stApp:has(.company-profile-active) .st-key-company_logo_body {
            padding: var(--profile-action-gap) 28px 28px;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body[data-testid="stVerticalBlock"],
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body > [data-testid="stVerticalBlock"] {
            gap: var(--profile-action-gap) !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stHorizontalBlock"] {
            width: 100%;
            max-width: 760px;
            margin: 0 auto;
            align-items: flex-start;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body
        [data-testid="stElementContainer"]:has(.company-logo-change-mode),
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body
        [data-testid="stElementContainer"]:has(.company-logo-pending) {
            display: none !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_logo_empty_upload {
            width: 100%;
            max-width: 360px;
            margin-left: auto;
            margin-right: auto;
        }

        .company-logo-preview {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 220px;
            margin: 0;
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 20px;
            background: #FFFFFF;
            color: rgba(42, 31, 44, 0.72);
            font-family: var(--font-mono);
            font-size: 20px;
            font-weight: 700;
        }

        .company-logo-preview img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .company-logo-preview:has(img) {
            border: 0;
            background: transparent;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] {
            width: 100%;
            height: 100%;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section {
            position: relative;
            width: 100%;
            height: 220px;
            min-height: 220px;
            padding: 0 !important;
            overflow: hidden;
            border: 1px dashed #BFAFD0 !important;
            border-radius: 20px !important;
            outline: 0 !important;
            background: #FBF9FD !important;
            box-shadow: none !important;
            cursor: pointer;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section > div,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section small,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section span,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section p,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section button {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section::before {
            content: "";
            position: absolute;
            left: 50%;
            top: calc(50% - 48px);
            z-index: 2;
            width: 46px;
            height: 46px;
            transform: translateX(-50%);
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cpath d='M50 18 V82 M18 50 H82' stroke='%238049C6' stroke-width='9' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: center;
            background-size: contain;
            pointer-events: none;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section::after {
            content: "Drop or Upload\\A PNG/SVG/PDF";
            position: absolute;
            left: 0;
            right: 0;
            top: calc(50% + 12px);
            z-index: 2;
            color: rgba(42, 31, 44, 0.72);
            font-family: var(--font-mono);
            font-size: 20px;
            font-weight: 700;
            line-height: 1.55;
            text-align: center;
            white-space: pre-line;
            pointer-events: none;
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section:hover,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section:focus-within,
        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stFileUploader"] section.costerly-upload-dragover {
            border-color: var(--color-accent) !important;
            outline: 0 !important;
            background: #F7F1FC !important;
            box-shadow: 0 0 0 3px rgba(128, 73, 198, 0.14) !important;
        }

        @keyframes company-logo-notice-dismiss {
            to {
                max-height: 0;
                margin: 0;
                padding: 0;
                opacity: 0;
                overflow: hidden;
                visibility: hidden;
            }
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_body [data-testid="stAlert"] {
            animation: company-logo-notice-dismiss 180ms ease 5s forwards;
        }

        .stApp:has(.company-profile-active) .st-key-price_source_add_card,
        .stApp:has(.company-profile-active) .st-key-price_source_list_card,
        .stApp:has(.company-profile-active) .st-key-price_source_detail_card {
            margin-top: 18px;
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 18px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .stApp:has(.company-profile-active) .st-key-price_source_add_card {
            margin-top: 0;
        }

        .stApp:has(.company-profile-active) .st-key-price_source_add_body {
            padding: 20px 24px 24px;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body[data-testid="stVerticalBlock"],
        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body > [data-testid="stVerticalBlock"] {
            gap: 16px !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body [data-testid="stHorizontalBlock"] {
            align-items: stretch !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
            gap: 12px !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body [data-testid="stFileUploader"] section {
            min-height: 198px;
            border: 1px dashed #BFAFD0 !important;
            border-radius: var(--input-radius) !important;
            background: #FBF9FD !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_add_body [data-testid="stButton"] button {
            min-height: 52px !important;
        }

        .stApp:has(.company-profile-active) .st-key-price_source_list_card {
            padding-bottom: 10px;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_list_card > [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_list_card [data-testid="stHorizontalBlock"] {
            min-height: 68px;
            padding: 10px 16px;
            border-bottom: 1px solid var(--color-border-soft);
        }

        .price-source-file {
            display: block;
            max-width: 360px;
            overflow: hidden;
            color: var(--color-text-muted);
            font-size: 12px;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .price-source-detail-heading {
            display: flex;
            justify-content: space-between;
            gap: 24px;
            padding: 20px 24px 8px;
        }

        .price-source-detail-heading > div {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .price-source-detail-heading > div:last-child {
            text-align: right;
        }

        .price-source-detail-heading span {
            color: var(--color-text-muted);
            font-size: 12px;
        }

        .st-key-price_source_detail_card [data-testid="stCaptionContainer"] {
            padding: 0 24px 14px;
        }

        .price-source-table {
            overflow-x: auto;
            border-top: 1px solid var(--color-border-soft);
        }

        .price-source-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .price-source-table th,
        .price-source-table td {
            padding: 14px 16px;
            border-right: 1px solid var(--color-border-soft);
            border-bottom: 1px solid var(--color-border-soft);
            text-align: left;
            vertical-align: middle;
        }

        .price-source-table th {
            background: #FAF8FC;
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 12px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .price-source-table td {
            font-size: 13px;
        }

        .stApp:has(.company-profile-active) .st-key-price_catalog_section {
            margin-top: 18px;
        }

        .stApp:has(.company-profile-active) .st-key-price_source_library_toggle {
            margin-top: 18px;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_source_library_toggle [data-testid="stButton"] button {
            min-height: 52px !important;
            border-radius: 14px !important;
        }

        .stApp:has(.company-profile-active)
        .st-key-price_catalog_section > [data-testid="stVerticalBlock"] {
            gap: 18px !important;
        }

        .price-catalog-card {
            overflow: hidden;
            border: 1px solid var(--color-border-soft);
            border-radius: 18px;
            background: var(--color-surface);
            box-shadow: 0 12px 34px rgba(42, 31, 44, 0.06);
        }

        .price-catalog-title,
        .price-catalog-department > summary,
        .price-catalog-type > summary {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
        }

        .price-catalog-title {
            min-height: 62px;
            padding: 0 22px;
            background: #FAF8FC;
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .price-catalog-title span:last-child,
        .price-catalog-department > summary span:last-child,
        .price-catalog-type > summary span:last-child {
            color: var(--color-text-muted);
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0;
            text-transform: none;
        }

        .price-catalog-department,
        .price-catalog-type {
            border-top: 1px solid var(--color-border-soft);
        }

        .price-catalog-department > summary,
        .price-catalog-type > summary {
            min-height: 54px;
            padding: 0 22px;
            cursor: pointer;
            list-style-position: inside;
        }

        .price-catalog-department > summary {
            background: #F7F3FA;
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.035em;
            text-transform: uppercase;
        }

        .price-catalog-type > summary {
            padding-left: 38px;
            background: #FCFBFD;
            color: var(--color-text-strong);
            font-size: 14px;
            font-weight: 700;
        }

        .price-catalog-table-wrap {
            overflow-x: auto;
        }

        .price-catalog-card table {
            width: 100%;
            min-width: 780px;
            border-collapse: collapse;
            table-layout: fixed;
        }

        .price-catalog-card th,
        .price-catalog-card td {
            padding: 13px 16px;
            border-top: 1px solid var(--color-border-soft);
            text-align: left;
            vertical-align: middle;
        }

        .price-catalog-card th {
            background: #FFFFFF;
            color: var(--color-text-muted);
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .price-catalog-card th:nth-child(1) { width: 31%; }
        .price-catalog-card th:nth-child(2) { width: 25%; }
        .price-catalog-card th:nth-child(3) { width: 19%; }
        .price-catalog-card th:nth-child(4) { width: 14%; }
        .price-catalog-card th:nth-child(5) { width: 11%; }

        .price-catalog-material strong,
        .price-catalog-supplier strong,
        .price-catalog-material span,
        .price-catalog-link {
            display: block;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .price-catalog-material strong,
        .price-catalog-supplier strong,
        .price-catalog-price strong {
            color: var(--color-text-strong);
            font-size: 14px;
        }

        .price-catalog-material span,
        .price-catalog-link {
            margin-top: 3px;
            color: var(--color-text-muted);
            font-size: 12px;
        }

        .price-catalog-link:hover,
        .price-catalog-source a:hover {
            color: var(--color-accent);
        }

        .price-catalog-price,
        .price-catalog-date,
        .price-catalog-source {
            white-space: nowrap;
        }

        .price-catalog-source a,
        .price-catalog-source span {
            color: var(--color-text-muted);
            font-family: var(--font-mono);
            font-size: 12px;
        }

        .price-catalog-empty-body {
            display: flex;
            min-height: 190px;
            padding: 32px;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 8px;
            text-align: center;
        }

        .price-catalog-empty-body strong {
            color: var(--color-text-strong);
            font-size: 18px;
        }

        .price-catalog-empty-body span {
            max-width: 460px;
            color: var(--color-text-muted);
            font-size: 14px;
            line-height: 1.45;
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
        .stApp:has(.company-profile-active) div[data-baseweb="base-input"],
        .stApp:has(.company-profile-active) div[data-baseweb="select"] > div {
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

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            display: flex !important;
            align-items: center !important;
            min-height: 52px !important;
            background: var(--input-bg) !important;
            border-color: #CEC5D1 !important;
            color: var(--input-text) !important;
            box-shadow: none !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div {
            display: flex !important;
            align-items: center !important;
            min-height: 50px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            color: var(--input-text) !important;
            font-family: var(--font-sans) !important;
            line-height: 1.2 !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"]:focus-within div[data-baseweb="select"] > div {
            border-color: var(--input-focus-border) !important;
            box-shadow: 0 0 0 3px var(--input-focus-ring) !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            display: flex !important;
            align-items: center !important;
            height: 52px !important;
            min-height: 52px !important;
            max-height: 52px !important;
            border: 1px solid #CEC5D1 !important;
            border-radius: var(--input-radius) !important;
            background: var(--input-bg) !important;
            box-shadow: none !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div {
            min-height: 50px !important;
            align-items: center !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"]:focus-within div[data-baseweb="select"] > div {
            border-color: #5B9BD5 !important;
            box-shadow: 0 0 0 3px rgba(91, 155, 213, 0.18) !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"]:has(span[data-baseweb="tag"])
        div[data-baseweb="select"] > div {
            border-color: #79AEE8 !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] span[data-baseweb="tag"],
        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] [role="button"][aria-label*="close by backspace"] {
            border: 1px solid #79AEE8 !important;
            background: #E8F3FF !important;
            color: #194E7A !important;
        }

        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] span[data-baseweb="tag"] span,
        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] span[data-baseweb="tag"] svg,
        .stApp:has(.company-profile-active)
        [data-testid="stMultiSelect"] span[data-baseweb="tag"] path {
            color: #194E7A !important;
            fill: #2F76B7 !important;
        }

        /* Streamlit 1.64 replaced the BaseWeb Select with React Aria ComboBox. */
        .stApp:has(.company-profile-active) [data-testid="stSelectbox"]
        .react-aria-ComboBox [role="group"] {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            height: 52px !important;
            min-height: 52px !important;
            overflow: hidden !important;
            border: 1px solid #CEC5D1 !important;
            border-radius: var(--input-radius) !important;
            background: var(--input-bg) !important;
            box-shadow: none !important;
            transition: border-color 120ms ease, box-shadow 120ms ease;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"]
        .react-aria-ComboBox [role="group"][data-focus-within="true"] {
            border-color: var(--input-focus-border) !important;
            box-shadow: 0 0 0 3px var(--input-focus-ring) !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"]
        .react-aria-ComboBox input[role="combobox"] {
            height: 50px !important;
            min-height: 50px !important;
            padding: 0 16px !important;
            border: 0 !important;
            outline: 0 !important;
            background: var(--input-bg) !important;
            box-shadow: none !important;
            color: var(--input-text) !important;
            -webkit-text-fill-color: var(--input-text) !important;
            font-family: var(--font-sans) !important;
            font-size: 16px !important;
            line-height: normal !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"]
        .react-aria-ComboBox button[aria-haspopup="listbox"] {
            align-self: stretch !important;
            width: 42px !important;
            min-width: 42px !important;
            height: 50px !important;
            min-height: 50px !important;
            padding: 0 12px 0 6px !important;
            border: 0 !important;
            border-radius: 0 !important;
            outline: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            color: var(--color-text-muted) !important;
            transform: none !important;
        }

        body:has(.company-profile-active) [data-st-overlay-root="true"]
        [role="option"][aria-selected="true"],
        body:has(.company-profile-active) [data-st-overlay-root="true"]
        [role="option"][aria-selected="true"] [data-item-hl] {
            background: rgba(128, 73, 198, 0.14) !important;
            color: var(--color-text-strong) !important;
        }

        body:has(.company-profile-active) [data-st-overlay-root="true"]
        [role="option"]:hover,
        body:has(.company-profile-active) [data-st-overlay-root="true"]
        [role="option"][data-focused="true"] [data-item-hl] {
            background: rgba(128, 73, 198, 0.09) !important;
            color: var(--color-text-strong) !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stSelectbox"] svg {
            fill: var(--color-text-muted) !important;
            color: var(--color-text-muted) !important;
        }

        div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
            background: rgba(128, 73, 198, 0.14) !important;
            color: var(--color-text-strong) !important;
        }

        div[data-baseweb="popover"] [role="option"]:hover {
            background: rgba(128, 73, 198, 0.09) !important;
            color: var(--color-text-strong) !important;
        }

        div[data-baseweb="popover"] [role="option"] svg {
            fill: var(--color-accent) !important;
            color: var(--color-accent) !important;
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
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button,
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"],
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] > div,
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] button,
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"],
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] > div,
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] button {
            width: 100% !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"],
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] button[kind="primary"],
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] button[kind="primary"] {
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
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"] p,
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] button[kind="primary"] p,
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] button[kind="primary"] p {
            color: #FFFFFF !important;
            font-family: var(--font-sans) !important;
            font-size: 19px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button:hover,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"]:hover,
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] button[kind="primary"]:hover,
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] button[kind="primary"]:hover {
            background: #6F3CB4 !important;
            border-color: #6F3CB4 !important;
            color: #FFFFFF !important;
            box-shadow: 0 12px 28px rgba(111, 60, 180, 0.34) !important;
            transform: translateY(-1px);
        }

        .stApp:has(.company-profile-active) [data-testid="stFormSubmitButton"] button:active,
        .stApp:has(.company-profile-active) .st-key-company_metrics_card [data-testid="stButton"] button[kind="primary"]:active,
        .stApp:has(.company-profile-active) .st-key-company_labor_card [data-testid="stButton"] button[kind="primary"]:active,
        .stApp:has(.company-profile-active) .st-key-company_logo_card [data-testid="stButton"] button[kind="primary"]:active {
            background: #6131A3 !important;
            border-color: #6131A3 !important;
            transform: translateY(0) scale(0.995);
        }

        .stApp:has(.company-profile-active)
        .st-key-company_logo_card [data-testid="stButton"] button[kind="primary"] {
            margin-top: 0 !important;
        }

        .company-metrics-table {
            margin-top: 0;
        }

        .company-metrics-group-summary {
            cursor: default;
        }

        .company-metrics-row--last .object-detail-table-cell {
            border-bottom: 0;
        }

        .company-metrics-row .object-detail-table-cell:nth-child(3),
        .company-metrics-row .object-detail-table-cell:nth-child(4) {
            font-family: var(--font-mono);
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }

        .stApp:has(.company-profile-active) .st-key-company_metrics_settings {
            margin-top: 34px;
        }

        .company-metrics-save {
            width: 100%;
            min-height: 60px;
            margin-top: 18px;
            border: 1px solid #8049C6;
            border-radius: var(--button-radius);
            background: #8049C6;
            box-shadow: 0 8px 22px rgba(128, 73, 198, 0.22);
            color: #FFFFFF !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-sans);
            font-size: 19px;
            font-weight: 700;
            text-decoration: none !important;
            text-transform: uppercase;
            transition: background 150ms ease, border-color 150ms ease,
                        transform 150ms ease, box-shadow 150ms ease;
        }

        .company-metrics-save:hover,
        .company-metrics-save:focus {
            border-color: #6F3CB4;
            background: #6F3CB4;
            box-shadow: 0 12px 28px rgba(111, 60, 180, 0.34);
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }

        .company-metrics-save:active {
            border-color: #6131A3;
            background: #6131A3;
            transform: translateY(0) scale(0.995);
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
            border-radius: 18px;
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
            font-family: var(--font-mono) !important;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .company-profile-users td,
        .company-profile-users td strong {
            font-family: var(--font-sans) !important;
        }

        .company-profile-users tr:last-child td {
            border-bottom: 0;
        }

        .company-profile-users .company-user-action-cell {
            width: 44px;
            padding-left: 8px;
            padding-right: 8px;
            text-align: center;
        }

        .company-user-delete {
            width: 28px;
            height: 28px;
            padding: 0;
            border: 0;
            border-radius: 7px;
            background: transparent;
            color: var(--color-text-muted);
            font-family: var(--font-sans) !important;
            font-size: 20px;
            line-height: 1;
            cursor: pointer;
        }

        .company-user-delete:hover,
        .company-user-delete:focus-visible {
            background: #F7ECEE;
            color: #B4233B;
            outline: none;
        }

        .company-profile-invite {
            margin-top: 12px;
        }

        .company-profile-invite-value {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }

        .company-profile-invite-text {
            display: block;
            min-width: 0;
            flex: 1 1 auto;
            overflow-wrap: anywhere;
            color: var(--color-text);
            font-family: var(--font-mono) !important;
        }

        .stApp:has(.company-profile-active) .company-invite-copy {
            width: 88px;
            min-width: 88px;
            min-height: 36px;
            padding: 0 14px;
            border: 1px solid var(--color-border-soft);
            border-radius: 8px !important;
            background: #FFFFFF;
            color: var(--color-text-strong);
            font-family: var(--font-sans);
            font-size: 14px !important;
            font-weight: 700;
            cursor: pointer;
        }

        .stApp:has(.company-profile-active) .company-invite-copy:hover,
        .stApp:has(.company-profile-active) .company-invite-copy:focus-visible {
            border-color: var(--color-accent);
            background: #F8F3FC;
            color: var(--color-accent);
            outline: none;
        }

        .company-labor-list {
            overflow-x: auto;
        }

        .company-labor-list table {
            width: 100%;
            min-width: 0;
            table-layout: fixed;
        }

        .company-labor-list th,
        .company-labor-list td {
            box-sizing: border-box;
            padding-left: 8px;
            padding-right: 8px;
        }

        .company-labor-col-actions {
            width: 38px;
        }

        .company-labor-col-worker {
            width: 20%;
        }

        .company-labor-col-department {
            width: 112px;
        }

        .company-labor-col-position {
            width: 170px;
        }

        .company-labor-col-pay-type {
            width: 82px;
        }

        .company-labor-col-details {
            width: 146px;
        }

        .company-labor-col-monthly {
            width: 106px;
        }

        .company-labor-total-row th {
            padding-top: 18px !important;
            padding-bottom: 18px !important;
            border-left: 0 !important;
            border-right: 0 !important;
            background: #FAF8FC !important;
            color: var(--color-text-strong) !important;
            font-family: var(--font-mono) !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            font-variant-numeric: tabular-nums;
        }

        .company-labor-total-row th:first-child {
            text-align: left !important;
        }

        .company-labor-total-row th:nth-child(2),
        .company-labor-total-row th:nth-child(3) {
            text-align: left !important;
        }

        .company-labor-list th:first-child,
        .company-labor-list td:first-child {
            width: 38px;
            min-width: 38px;
            padding-left: 8px;
            padding-right: 6px;
        }

        .company-labor-list th:nth-child(6),
        .company-labor-list td:nth-child(6) {
            width: 146px;
        }

        .company-labor-list th:nth-child(7),
        .company-labor-list td:nth-child(7) {
            width: 106px;
        }

        .company-labor-list td:nth-child(6),
        .company-labor-list td:nth-child(7) {
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        .company-labor-actions {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0;
        }

        .stApp:has(.company-profile-active) .company-labor-edit,
        .stApp:has(.company-profile-active) .company-labor-delete,
        .stApp:has(.company-profile-active) .company-labor-edit:hover,
        .stApp:has(.company-profile-active) .company-labor-delete:hover,
        .stApp:has(.company-profile-active) .company-labor-edit:focus,
        .stApp:has(.company-profile-active) .company-labor-delete:focus {
            width: 22px !important;
            min-width: 22px !important;
            height: 22px !important;
            min-height: 22px !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 5px !important;
            background: transparent !important;
            color: var(--color-text-muted) !important;
            font-family: var(--font-sans) !important;
            font-size: 16px !important;
            line-height: 1 !important;
            box-shadow: none !important;
            transform: none !important;
            cursor: pointer;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        .react-aria-ComboBox [role="group"] > button:not([aria-haspopup="listbox"]),
        .stApp:has(.company-profile-active) .st-key-company_labor_card
        .react-aria-ComboBox button[aria-label*="Clear"] {
            display: none !important;
        }

        .stApp:has(.company-profile-active) .company-labor-edit:hover,
        .stApp:has(.company-profile-active) .company-labor-edit:focus-visible,
        .stApp:has(.company-profile-active) .company-labor-delete:hover,
        .stApp:has(.company-profile-active) .company-labor-delete:focus-visible {
            background: rgba(128, 73, 198, 0.10) !important;
            color: var(--color-accent) !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card {
            margin-top: 0;
            border-radius: 18px !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        [data-testid="stHorizontalBlock"] {
            align-items: flex-end !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        [data-testid="stWidgetLabel"] {
            display: flex !important;
            align-items: center !important;
            height: 22px !important;
            min-height: 22px !important;
            margin-bottom: 6px !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        [data-testid="stWidgetLabel"] > div {
            display: flex !important;
            align-items: center !important;
            min-height: 22px !important;
        }

        div[role="tooltip"] p {
            margin: 0 0 4px !important;
            line-height: 1.2 !important;
        }

        div[role="tooltip"] ul {
            margin: 2px 0 6px !important;
            padding-left: 18px !important;
        }

        div[role="tooltip"] li {
            margin: 0 !important;
            line-height: 1.2 !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        [data-testid="stTextInput"] input:disabled {
            opacity: 1 !important;
            color: var(--color-text-strong) !important;
            -webkit-text-fill-color: var(--color-text-strong) !important;
            font-weight: 700 !important;
        }

        .stApp:has(.company-profile-active) .st-key-company_labor_card
        [data-testid="stHorizontalBlock"]:has(button[kind="primary"]) button {
            min-height: 60px !important;
            margin-top: 8px !important;
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
                width: calc((100% - 20px) / 3) !important;
                flex: 1 1 calc((100% - 20px) / 3) !important;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab-list"],
            .st-key-company_profile_tab [role="tablist"] {
                overflow-x: auto;
                justify-content: flex-start;
            }

            .stApp:has(.company-profile-active) [data-baseweb="tab"],
            .st-key-company_profile_tab [role="tab"] {
                flex: 0 0 auto;
                white-space: nowrap;
            }

            .stApp:has(.company-profile-active) div[data-testid="stForm"],
            .stApp:has(.company-profile-active) .st-key-company_metrics_card,
            .stApp:has(.company-profile-active) .st-key-company_labor_card,
            .stApp:has(.company-profile-active) [class*="st-key-company_machinery_group_"] { padding: 18px; }

            .company-machinery-table-head {
                grid-template-columns: minmax(0, 1fr) minmax(230px, 1.2fr);
            }
            .stApp:has(.company-profile-active) .st-key-company_logo_body { padding: 24px 18px 18px; }
            .company-logo-preview,
            .stApp:has(.company-profile-active)
            .st-key-company_logo_body [data-testid="stFileUploader"] section {
                height: 180px;
                min-height: 180px;
            }
            .company-profile-readonly-grid { grid-template-columns: 1fr; }

            .stApp:has(.company-profile-active)
            .st-key-price_source_add_body [data-testid="stFileUploader"] section {
                min-height: 150px;
            }

            .price-catalog-card {
                overflow: visible;
                border-radius: 18px;
            }

            .price-catalog-table-wrap {
                overflow: visible;
            }

            .price-catalog-card table,
            .price-catalog-card thead,
            .price-catalog-card tbody,
            .price-catalog-card tr,
            .price-catalog-card td {
                display: block;
                width: 100%;
                min-width: 0;
            }

            .price-catalog-card thead { display: none; }

            .price-catalog-card tr {
                padding: 14px 16px;
                border-top: 1px solid var(--color-border-soft);
            }

            .price-catalog-card td {
                padding: 4px 0;
                border: 0;
                white-space: normal;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
