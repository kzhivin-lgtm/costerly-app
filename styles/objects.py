from __future__ import annotations

import streamlit as st


def apply_objects_css() -> None:
    """Install pricing objects screen styling."""
    st.markdown(
        """
        <style>
        .objects-estimation-header .workflow-title-mark {
            justify-content: flex-start;
            top: 0.61em;
        }
        .objects-estimation-header .workflow-title-mark img {
            width: auto;
        }
        .objects-estimation-header .workflow-title-primary {
            max-width: var(--objects-title-available-width, 100%);
            box-sizing: border-box;
        }
        .objects-estimation-header .workflow-title-text {
            display: inline-flex;
            flex-wrap: wrap;
            gap: 0 0.45em;
            max-width: 100%;
        }
        .objects-estimation-header .project-title-name {
            min-width: 0;
            overflow-wrap: anywhere;
        }
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
        .st-key-costerly_screen_header[data-stale="true"],
        .stApp:has(.objects-estimation-header)
        .st-key-costerly_screen_header [data-stale="true"],
        .stApp:has(.objects-estimation-header)
        .st-key-objects_actions[data-stale="true"],
        .stApp:has(.objects-estimation-header)
        .st-key-objects_actions [data-stale="true"],
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
            min-height: 133px;
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
        .objects-pricing-materials {
            min-height: 36px;
            text-transform: lowercase;
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

        .objects-pricing-price-input[aria-invalid="true"],
        .objects-pricing-quantity-input[aria-invalid="true"] {
            outline: 1px solid #b43b46;
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
            display: block;
            line-height: 40px;
            white-space: nowrap;
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
            width: 122px;
            -webkit-user-select: text;
            user-select: text;
        }

        .objects-pricing-row--project-cost {
            /* Prevent native click-to-caret from choosing the nearby editing
               host when the click is outside its visible border. */
            -webkit-user-select: none;
            user-select: none;
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

        .st-key-object_detail_navigation_bridges,
        .st-key-proposal_first_download_host {
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
        .st-key-final_approval_approved a {
            min-height: var(--button-height-lg) !important;
            width: 100%;
            box-sizing: border-box;
            border-radius: var(--button-radius) !important;
            font-family: var(--font-mono) !important;
            font-size: var(--button-font-size) !important;
            font-weight: var(--button-font-weight) !important;
            text-transform: uppercase !important;
            text-decoration: none !important;
        }
        .stApp:has(.objects-estimation-header) .st-key-final_approval_approved a:not([aria-disabled="true"]) {
            background: rgba(52, 168, 83, 0.12) !important;
            border-color: rgba(52, 168, 83, 0.32) !important;
            color: #2F8D48 !important;
        }
        .stApp:has(.objects-estimation-header) .st-key-final_approval_approved a:not([aria-disabled="true"]):hover {
            background: rgba(52, 168, 83, 0.18) !important;
            border-color: rgba(52, 168, 83, 0.48) !important;
            color: #26763B !important;
        }
        .stApp:has(.objects-estimation-header) .st-key-final_approval_approved a[aria-disabled="true"] {
            background: #f7f5f8 !important;
            border-color: #d4ced8 !important;
            color: #8c8492 !important;
            cursor: default;
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
            font-size: 30px;
            line-height: 1.2;
            font-weight: 400;
            color: #17131C;
        }

        .objects-pricing-summary-value--total {
            color: var(--color-accent);
            font-size: 30px;
            font-weight: 700;
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
        /* Objects V2.4 presentation. Keep input/row/summary geometry and all
           handlers; reclaim the old toolbar row with the approved body offset. */
        .st-key-costerly_screen_header:has(.objects-estimation-header) {
            position: relative;
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
        .st-key-objects_header_metrics { min-width: 0; max-width: 100%; }
        .st-key-objects_header_toolbar {
            position: absolute !important;
            top: 11px;
            right: 0;
            width: fit-content !important;
            max-width: calc(100% - var(--objects-title-min-width, 0px) - 24px);
            flex-direction: column !important;
            align-items: flex-end !important;
            gap: 8px !important;
        }
        .st-key-objects_header_stages {
            /* Reclaim30px toolbar height, add4px to the old42px stage inset. */
            padding-top: 46px;
        }
        .st-key-objects_live_pricing .objects-pricing-card {
            /* Two existing 16px block gaps plus 18px give 50px below stages. */
            margin-top: 18px;
        }
        .st-key-objects_header_metrics .objects-cycle-metrics {
            flex-wrap: nowrap;
            white-space: nowrap;
            font-size: 11px;
            gap: 16px;
            padding: 0;
            margin: 0;
            min-width: 0;
            max-width: calc(100% - 22px);
            overflow-x: auto;
            scrollbar-width: thin;
        }
        .st-key-objects_header_metrics .objects-cycle-metrics > span { flex: 0 0 auto; }
        .objects-workflow-stages {
            display: grid;
            grid-template-columns: max-content minmax(16px, 1fr) max-content minmax(16px, 1fr) max-content;
            align-items: start;
            min-height: 51px;
            padding: 0 !important;
            margin: 0 !important;
            list-style: none;
            gap: 24px;
        }
        .objects-workflow-stages li {
            display: contents;
        }
        .objects-stage-group {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 0;
            margin: 0;
            color: var(--color-text-strong);
        }
        .objects-stage-marker {
            flex: 0 0 30px;
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(42, 31, 44, 0.4);
            border-radius: 50%;
            font-family: var(--font-mono);
            font-size: 14px;
        }
        .objects-workflow-stages li:not(:last-child)::after {
            content: "";
            display: block;
            height: 1px;
            min-width: 16px;
            width: 100%;
            margin-top: 15px;
            background: rgba(42, 31, 44, 0.18);
        }
        .objects-workflow-stages strong {
            display: block;
            padding-top: 5px;
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
            font-size: 0;
        }
        .objects-workflow-stages [data-state="complete"] .objects-stage-marker::before {
            content: "";
            width: 6px;
            height: 10px;
            border-right: 2px solid currentColor;
            border-bottom: 2px solid currentColor;
            transform: translateY(-2px) rotate(45deg);
        }
        .stApp:has(.objects-workflow-stages [data-stage="2"][data-state="complete"]):not(:has(.objects-workflow-stages [data-stage="3"][data-state="complete"])) .st-key-objects_set_prices button {
            background: rgba(52, 168, 83, 0.10) !important;
            border-color: rgba(52, 168, 83, 0.34) !important;
            color: #2F8D48 !important;
        }
        .stApp:has(.objects-workflow-stages [data-stage="2"][data-state="complete"]):not(:has(.objects-workflow-stages [data-stage="3"][data-state="complete"])) .st-key-objects_set_prices button:hover {
            background: rgba(52, 168, 83, 0.16) !important;
            border-color: rgba(52, 168, 83, 0.48) !important;
            color: #26763B !important;
        }
        .stApp .st-key-objects_actions button {
            text-transform: none !important;
        }
        .st-key-objects_actions {
            padding-top: 0;
        }

        .objects-technical-metrics {
            position: relative;
            min-height: 30px;
            display: flex;
            align-items: center;
            width: max-content;
            max-width: 100%;
            padding-right: 22px;
        }
        .stApp .objects-metrics-toggle {
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            min-width: 20px;
            height: 30px;
            min-height: 30px;
            padding: 0;
            border: 0;
            border-radius: 0;
            background: transparent;
            color: rgba(42, 31, 44, 0.7);
            box-shadow: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .objects-metrics-chevron {
            width: 7px;
            height: 7px;
            border-right: 1.5px solid currentColor;
            border-bottom: 1.5px solid currentColor;
            transform: rotate(225deg);
        }
        .st-key-objects_header_metrics[data-metrics-collapsed="true"] .objects-cycle-metrics {
            /* Reserve the text width so the right-aligned arrow stays fixed. */
            visibility: hidden;
        }
        .st-key-objects_header_metrics[data-metrics-collapsed="true"] .objects-metrics-chevron {
            transform: rotate(45deg);
        }

        .objects-pricing-summary .objects-pricing-downloads {
            position: absolute;
            top: 34px;
            left: 0;
            display: flex;
            flex-direction: column;
            align-items: stretch;
            gap: 8px;
            width: calc((100% - 32px) / 6);
            min-width: 0;
            padding: 0;
            border: 0;
        }
        .objects-pricing-summary .objects-document-button {
            display: inline-flex;
            align-items: center;
            justify-content: flex-start;
            gap: 5px;
            flex: none;
            width: 100%;
            height: 34px;
            min-height: 34px;
            padding: 8px 12px;
            border: 1px solid #d4ced8;
            border-radius: 7px;
            background: #f7f5f8;
            color: #6f6578;
            opacity: 1;
            font-family: var(--font-sans);
            font-size: 11.5px;
            line-height: 1.3;
            white-space: nowrap;
            text-decoration: none;
        }
        .objects-document-icon {
            --document-icon-color: #817a80;
            color: var(--document-icon-color);
            position: relative;
            flex: none;
            width: 14px;
            height: 17px;
            border: 1px solid currentColor;
            border-radius: 2px;
            font: 12px/15px var(--font-mono);
            text-align: center;
        }
        .objects-document-icon--pdf {
            width: 18px;
            height: 21px;
            padding-top: 8px;
            font-size: 6px;
            line-height: 11px;
        }
        .objects-document-icon--excel {
            width: 18px;
            height: 21px;
        }
        .objects-document-button:not(:disabled):not([aria-disabled="true"]) .objects-document-icon--excel {
            --document-icon-color: #28794c;
        }
        .objects-document-button:not(:disabled):not([aria-disabled="true"]) .objects-document-icon--pdf {
            --document-icon-color: #b43b46;
        }
        .objects-document-icon--excel::before {
            content: "";
            position: absolute;
            inset: 5px 2px 3px 6px;
            background: repeating-linear-gradient(0deg, currentColor 0 1px, transparent 1px 4px),
                        repeating-linear-gradient(90deg, currentColor 0 1px, transparent 1px 4px);
            opacity: 0.5;
        }
        .objects-document-icon--excel span {
            position: absolute;
            left: -2px;
            top: 6px;
            width: 10px;
            height: 11px;
            border-radius: 1px;
            background: var(--document-icon-color);
            color: white;
            font: 700 8px/11px Arial, sans-serif;
        }
        .stApp .st-key-objects_actions [class*="st-key-objects_generate_proposal_"] button,
        .stApp .st-key-objects_actions .st-key-final_approval_approved button {
            text-transform: uppercase !important;
        }
        @media (max-width: 900px) {
            .st-key-objects_header_toolbar {
                position: static !important;
                width: 100% !important;
                max-width: 100%;
                align-items: flex-start !important;
            }
            .st-key-objects_header_metrics { max-width: 100%; }
            .st-key-objects_header_stages { padding-top: 42px; }
        }
        @media (max-width: 760px) {
            .st-key-objects_header_toolbar { flex-wrap: wrap !important; }
            .st-key-objects_header_metrics .objects-cycle-metrics { flex-wrap: nowrap; }
            .objects-workflow-stages { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
            .objects-stage-group { min-width: 0; }
            .objects-workflow-stages strong { font-size: 12px; }
            .objects-workflow-stages small { font-size: 11px; }
            .objects-workflow-stages li:not(:last-child)::after { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
