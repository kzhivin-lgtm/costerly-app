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
            margin: 42px 0 0 0;
            color: var(--color-text-strong);
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

        .objects-pricing-summary {
            display: grid;
            grid-template-columns: 1.25fr 1fr 1fr 1.1fr;
            column-gap: 46px;
            padding: 34px 0 38px 0;
            border-top: 1px solid rgba(42, 31, 44, 0.14);
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
            .objects-pricing-summary,
            .objects-pricing-actions {
                min-width: 900px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
