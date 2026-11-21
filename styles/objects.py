from __future__ import annotations

import streamlit as st


def apply_objects_css() -> None:
    """Install pricing objects screen styling."""
    st.markdown(
        """
        <style>
        .objects-estimation-header .post-upload-subtitle {
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

        .objects-pricing-card {
            --objects-row-main-offset: 12px;
            width: 100%;
            margin: var(--post-upload-heading-gap) 0 0 0;
            color: var(--color-text-strong);
        }

        .objects-cycle-metrics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px 24px;
            padding: 12px 0;
            margin-bottom: 16px;
            color: rgba(42, 31, 44, 0.7);
            font-family: var(--font-mono);
            font-size: 13px;
            font-variant-numeric: tabular-nums;
            overflow-wrap: anywhere;
        }

        .objects-cycle-metrics strong {
            color: var(--color-text);
        }

        div[data-testid="stElementContainer"]:has(.objects-estimation-header),
        div[data-testid="stElementContainer"]:has(.objects-pricing-card) {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        .stApp:has(.objects-estimation-header)
        .st-key-objects_live_pricing[data-stale="true"],
        .stApp:has(.objects-estimation-header)
        .st-key-objects_live_pricing [data-testid="stElementContainer"][data-stale="true"] {
            opacity: 1 !important;
            transition: none !important;
        }

        .objects-pricing-table {
            width: 100%;
            border-top: 1px solid rgba(42, 31, 44, 0.14);
        }

        .objects-pricing-header,
        .objects-pricing-row {
            display: grid;
            grid-template-columns: minmax(250px, 1.35fr) 58px 116px 162px 128px 122px;
            column-gap: 18px;
            align-items: start;
        }

        .objects-pricing-header {
            padding: 0 0 14px 0;
            border-top: 0;
        }

        .objects-pricing-head {
            color: rgba(42, 31, 44, 0.54);
            font-family: var(--font-mono);
            font-size: 14px;
            line-height: 1.15;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .objects-pricing-head:not(:first-child) {
            text-align: center;
        }

        .objects-pricing-row {
            min-height: 112px;
            padding: 18px 0;
            border-top: 1px solid rgba(42, 31, 44, 0.14);
        }

        .objects-pricing-name {
            font-size: 22px;
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #17131C;
            min-height: 54px;
            margin: 0 0 6px 0;
            display: flex;
            align-items: center;
            padding-top: var(--objects-row-main-offset);
        }

        .objects-pricing-materials,
        .objects-pricing-suggestion,
        .objects-pricing-summary-note {
            color: rgba(42, 31, 44, 0.58);
            font-size: 15px;
            line-height: 1.2;
            font-weight: 500;
        }

        .objects-pricing-suggestion {
            font-size: 11px;
            white-space: nowrap;
            text-align: center;
        }

        .objects-pricing-number,
        .objects-pricing-price {
            font-family: var(--font-mono);
            font-size: 18px;
            line-height: 1.2;
            font-weight: 700;
            text-align: center;
            color: var(--color-text-strong);
            min-height: 54px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: var(--objects-row-main-offset);
        }

        .objects-pricing-quantity-input {
            width: 54px;
            min-width: 54px;
            height: 42px;
            min-height: 42px;
            box-sizing: border-box;
            padding: 0;
            line-height: 40px;
            text-align: center;
            margin: calc(var(--objects-row-main-offset) + 6px) auto 0 auto;
            border: 1px solid rgba(42, 31, 44, 0.16);
            border-radius: 8px;
            background: #FFFFFF;
            outline: none;
        }

        .objects-pricing-quantity-input:focus {
            border-color: rgba(128, 73, 198, 0.72);
            box-shadow: 0 0 0 2px rgba(128, 73, 198, 0.10);
        }

        .objects-quantity-saving-overlay {
            position: fixed;
            inset: 0;
            z-index: 2147483000;
            pointer-events: none;
            background: rgba(244, 242, 244, 0.42);
            opacity: 0;
            transition: opacity 80ms linear;
        }

        .objects-quantity-saving-overlay.is-visible {
            opacity: 1;
            pointer-events: auto;
        }

        .objects-progress-status {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            min-width: 58px;
            white-space: nowrap;
        }

        .objects-progress-spinner {
            width: 15px;
            height: 15px;
            box-sizing: border-box;
            border: 3px solid rgba(40, 153, 221, 0.22);
            border-top-color: #2899DD;
            border-radius: 999px;
            animation: objects-progress-spin 500ms linear infinite;
            flex: 0 0 auto;
        }

        .objects-progress-percent {
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        @keyframes objects-progress-spin {
            to {
                transform: rotate(360deg);
            }
        }

        .objects-pricing-price-input {
            width: 100%;
            min-height: 42px;
            box-sizing: border-box;
            border: 1px solid var(--input-border);
            border-radius: var(--input-radius);
            background: var(--input-bg);
            color: var(--input-text);
            font-family: var(--font-mono);
            font-size: 16px;
            font-weight: 700;
            text-align: center;
            outline: none;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: border-color 140ms ease, box-shadow 140ms ease;
        }

        .objects-pricing-price-input:focus {
            border-color: var(--input-focus-border);
            box-shadow: 0 0 0 3px var(--input-focus-ring);
        }

        .objects-pricing-sale-cell {
            display: flex;
            flex-direction: column;
            gap: 5px;
            padding-top: calc(var(--objects-row-main-offset) + 6px);
        }

        .objects-pricing-row--project-cost .objects-pricing-project-cost-cell {
            grid-column: 2 / 5;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;
            gap: 5px;
            padding-top: calc(var(--objects-row-main-offset) + 6px);
        }

        .objects-pricing-row--project-cost .objects-pricing-price-input {
            width: 162px;
        }

        .objects-pricing-row--project-cost .objects-pricing-suggestion {
            width: 162px;
            text-align: center;
        }

        .objects-pricing-review-button,
        .objects-pricing-review-button:link,
        .objects-pricing-review-button:visited,
        .objects-pricing-review-button:active,
        .objects-pricing-download-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: var(--button-height-md);
            box-sizing: border-box;
            border: 1px solid var(--button-secondary-border);
            border-radius: var(--button-radius);
            background: var(--button-secondary-bg);
            color: var(--button-secondary-text);
            font-family: var(--font-mono);
            font-size: var(--button-font-size);
            font-weight: var(--button-font-weight);
            text-transform: uppercase;
            text-decoration: none;
        }

        .objects-pricing-review-button {
            width: 100%;
            min-height: 46px;
            font-size: 16px;
        }

        .objects-pricing-review-button:hover {
            background: var(--button-secondary-bg-hover);
            color: var(--color-accent);
            border-color: rgba(128, 73, 198, 0.42);
            text-decoration: none;
        }

        .objects-pricing-review-button--disabled,
        .objects-pricing-review-button--disabled:hover {
            pointer-events: none;
            cursor: default;
            background: rgba(42, 31, 44, 0.06);
            border-color: rgba(42, 31, 44, 0.14);
            color: rgba(42, 31, 44, 0.44);
            text-decoration: none;
        }

        .objects-pricing-review-button--done,
        .objects-pricing-review-button--done:link,
        .objects-pricing-review-button--done:visited,
        .objects-pricing-review-button--done:active {
            background: rgba(52, 168, 83, 0.10);
            border-color: rgba(52, 168, 83, 0.34);
            color: #2F8D48;
        }

        .objects-pricing-review-button--done:hover {
            background: rgba(52, 168, 83, 0.16);
            border-color: rgba(52, 168, 83, 0.48);
            color: #26763B;
        }

        .objects-pricing-action-cell {
            padding-top: calc(var(--objects-row-main-offset) + 4px);
        }

        .st-key-object_detail_navigation_bridges {
            display: none !important;
        }

        .objects-pricing-download-button {
            min-height: 36px;
            border: 0;
            background: transparent;
            padding: 0;
            justify-content: flex-start;
        }

        .objects-pricing-download-button:hover {
            color: var(--color-accent);
        }

        .objects-pricing-download-button--disabled,
        .objects-pricing-download-button--disabled:hover {
            pointer-events: none;
            color: rgba(42, 31, 44, 0.40);
        }

        .objects-pricing-download-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: auto;
            height: 26px;
            padding: 0 10px;
            border-radius: 7px;
            background: rgba(42, 31, 44, 0.12);
            color: rgba(42, 31, 44, 0.72);
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }

        .objects-pricing-downloads {
            display: grid;
            grid-template-columns: minmax(250px, 1.35fr) 58px 116px 162px 128px 122px;
            column-gap: 18px;
            padding: 26px 0;
            border-top: 1px solid rgba(42, 31, 44, 0.14);
        }

        .objects-pricing-download-block {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;
            gap: 10px;
        }

        .objects-pricing-download-block--proposal {
            grid-column: 1;
        }

        .objects-pricing-download-block--summary {
            grid-column: 2 / 5;
            width: 162px;
        }

        .objects-pricing-download-title {
            font-size: 20px;
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #17131C;
        }

        .stApp:has(.objects-estimation-header)
        .st-key-final_approval_approved button:disabled {
            opacity: 1 !important;
            background: rgba(52, 168, 83, 0.12) !important;
            border-color: rgba(52, 168, 83, 0.32) !important;
            color: #2F8D48 !important;
        }

        .objects-pricing-summary {
            --objects-summary-price-axis: calc(100% - 658px);
            --objects-summary-total-axis: calc(74.712644% + 34.896552px);
            display: grid;
            grid-template-columns: 1.25fr 1fr 1fr 1.1fr;
            column-gap: 46px;
            position: relative;
            padding: 34px 0 38px 0;
            border-top: 1px solid rgba(42, 31, 44, 0.14);
        }

        .objects-pricing-summary-price {
            position: absolute;
            top: 34px;
            left: var(--objects-summary-price-axis);
            width: 162px;
        }

        .objects-pricing-summary-vat {
            position: absolute;
            top: 34px;
            left: calc(87.356322% - 311.551724px);
            z-index: 1;
        }

        .objects-pricing-summary-total {
            grid-column: 4;
            grid-row: 1;
        }

        .objects-pricing-summary-title {
            font-size: 20px;
            line-height: 1.2;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #17131C;
            margin: 0 0 16px 0;
        }

        .objects-pricing-summary-value {
            font-family: var(--font-mono);
            font-size: 18px;
            line-height: 1.2;
            font-weight: 700;
            color: var(--color-text-strong);
        }

        .objects-pricing-summary-value--total {
            color: var(--color-accent);
            font-size: 30px;
        }

        .objects-pricing-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin: 28px 0 0 0;
        }

        @media (max-width: 920px) {
            .objects-pricing-card {
                overflow-x: auto;
            }

            .objects-pricing-table,
            .objects-pricing-downloads,
            .objects-pricing-summary,
            .objects-pricing-actions {
                min-width: 900px;
            }
        }
        /* Objects V2: only the header rail, stage strip and footer actions.
           Pricing rows, fields, project allocations and totals above are unchanged. */
        .st-key-costerly_screen_header:has(.objects-estimation-header) {
            gap: 8px !important;
        }
        .st-key-objects_header_controls [class*="st-key-costerly_header_controls"] {
            position: static !important;
            top: auto !important;
            right: auto !important;
            transform: none !important;
            opacity: 1 !important;
            max-width: none !important;
        }
        .st-key-objects_header_controls,
        .st-key-objects_header_metrics {
            flex: 0 0 auto !important;
        }
        .st-key-objects_header_toolbar {
            align-items: center !important;
            gap: 24px !important;
        }
        .st-key-objects_header_stages {
            /* Keep the original pricing table's document Y after moving metrics. */
            padding-bottom: 16.1875px;
        }
        .st-key-objects_header_metrics .objects-cycle-metrics {
            flex-wrap: nowrap;
            white-space: nowrap;
            font-size: 11px;
            gap: 16px;
            padding: 0;
            margin: 0;
        }
        .objects-workflow-stages {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            align-items: center;
            min-height: 51px;
            padding: 0 !important;
            margin: 0 !important;
            list-style: none;
            gap: 24px;
        }
        .objects-workflow-stages li {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0;
            margin: 0;
            color: rgba(42, 31, 44, 0.58);
        }
        .objects-stage-marker {
            flex: 0 0 30px;
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(42, 31, 44, 0.18);
            border-radius: 50%;
            font-family: var(--font-mono);
            font-size: 14px;
        }
        .objects-workflow-stages li:not(:last-child)::after {
            content: "";
            height: 1px;
            min-width: 16px;
            flex: 1;
            background: rgba(42, 31, 44, 0.18);
        }
        .objects-workflow-stages strong {
            display: block;
            font-size: 15px;
            font-weight: 600;
            line-height: 1.3;
        }
        .objects-workflow-stages small {
            display: block;
            margin-top: 4px;
            font-size: 12px;
            line-height: 1.3;
        }
        .objects-workflow-stages [data-state="current"] {
            color: var(--color-text-strong);
        }
        .objects-workflow-stages [data-state="current"] .objects-stage-marker {
            background: var(--color-accent);
            border-color: var(--color-accent);
            color: white;
        }
        .objects-workflow-stages [data-state="complete"] .objects-stage-marker {
            color: #2F8D48;
            border-color: #2F8D48;
        }
        .stApp .st-key-objects_actions button {
            text-transform: none !important;
        }
        .st-key-objects_actions {
            /* Retain the original bottom action row after removing Parts Check. */
            padding-top: 72px;
        }
        .stApp .st-key-objects_actions [class*="st-key-objects_generate_proposal_"] button,
        .stApp .st-key-objects_actions .st-key-final_approval_approved button {
            text-transform: uppercase !important;
        }
        @media (max-width: 760px) {
            .st-key-objects_header_toolbar { flex-wrap: wrap !important; }
            .st-key-objects_header_metrics .objects-cycle-metrics { flex-wrap: wrap; }
            .objects-workflow-stages { gap: 8px; }
            .objects-workflow-stages strong { font-size: 12px; }
            .objects-workflow-stages small { font-size: 11px; }
            .objects-workflow-stages li:not(:last-child)::after { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
