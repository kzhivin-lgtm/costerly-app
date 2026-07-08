from __future__ import annotations

import streamlit as st


def apply_object_detail_css() -> None:
    """Install object detail screen styling."""
    st.markdown(
        """
        <style>
        .object-detail-shell {
            margin-bottom: 44px;
        }

        .object-detail-hero {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 260px;
            column-gap: 42px;
            align-items: start;
        }

        .object-detail-title {
            max-width: 760px;
            margin-bottom: 28px !important;
            overflow-wrap: anywhere;
        }

        .object-detail-info-row {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin: 18px 0 8px 0;
            font-family: var(--font-sans);
            font-size: 22px;
            line-height: 1.12;
            font-weight: 800;
            letter-spacing: -0.035em;
            color: var(--color-text-strong);
        }

        .object-detail-info-label,
        .object-detail-section-label,
        .object-detail-table-head,
        .object-detail-final-label {
            color: rgba(42, 31, 44, 0.58);
            font-family: var(--font-mono);
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .object-detail-info-value,
        .object-detail-final-total {
            color: var(--color-accent);
        }

        .object-detail-preview-placeholder {
            width: 260px;
            min-height: 178px;
            border-radius: 12px;
            border: 1px solid rgba(42, 31, 44, 0.16);
            background: #FFFFFF;
            color: rgba(42, 31, 44, 0.44);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
        }

        .object-detail-section {
            --detail-grid: minmax(260px, 2.1fr) repeat(4, minmax(0, 1fr));
            margin: 0 0 48px 0;
        }

        .object-detail-section:last-of-type {
            margin-bottom: 20px;
        }

        .object-detail-section--cols-4 {
            --detail-grid: minmax(260px, 2.1fr) repeat(3, minmax(0, 1fr));
        }

        .object-detail-section-header {
            display: grid;
            grid-template-columns: var(--detail-grid);
            column-gap: 18px;
            align-items: end;
            margin: 0 0 12px 0;
        }

        .object-detail-section-title {
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 24px;
            line-height: 1.12;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .object-detail-section-metric {
            text-align: center;
        }

        .object-detail-section-metric-spacer {
            min-width: 0;
        }

        .object-detail-section-label {
            font-size: 11px;
            line-height: 1.1;
            margin: 0 0 5px 0;
        }

        .object-detail-section-value {
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 16px;
            font-weight: 700;
            line-height: 1.1;
        }

        .object-detail-section-metric:last-child .object-detail-section-value {
            color: var(--color-accent);
        }

        .object-detail-table {
            width: 100%;
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.045);
        }

        .object-detail-table--cols-5 {
            --detail-grid: minmax(260px, 2.1fr) repeat(4, minmax(0, 1fr));
        }

        .object-detail-table--cols-4 {
            --detail-grid: minmax(260px, 2.1fr) repeat(3, minmax(0, 1fr));
        }

        .object-detail-table-head-row,
        .object-detail-table-row {
            display: grid;
            grid-template-columns: var(--detail-grid);
            column-gap: 0;
        }

        .object-detail-table-head,
        .object-detail-table-cell {
            border-bottom: 1px solid rgba(42, 31, 44, 0.12);
            min-height: 42px;
            padding: 8px 12px;
            font-size: 13px;
            line-height: 1.24;
            color: var(--color-text-strong);
            display: flex;
            align-items: center;
        }

        .object-detail-table-head {
            background: rgba(42, 31, 44, 0.045);
        }

        .object-detail-table-head:not(:first-child),
        .object-detail-table-cell:not(:first-child) {
            justify-content: center;
        }

        .object-detail-group-summary {
            background: rgba(128, 73, 198, 0.075);
            color: rgba(42, 31, 44, 0.68);
            cursor: pointer;
            display: grid;
            grid-template-columns: var(--detail-grid);
            align-items: center;
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.04em;
            min-height: 40px;
            padding: 0 12px;
            text-transform: uppercase;
            user-select: none;
        }

        .object-detail-group-summary::marker,
        .object-detail-group-summary::-webkit-details-marker {
            display: none;
            content: "";
        }

        .object-detail-group-title {
            display: flex;
            align-items: center;
        }

        .object-detail-group-title::before {
            content: "▾";
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 22px;
            margin-right: 8px;
            font-size: 22px;
            line-height: 1;
            color: var(--color-accent);
        }

        .object-detail-group:not([open]) .object-detail-group-title::before {
            content: "▸";
        }

        .object-detail-group-total {
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--color-text-strong);
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            line-height: 1;
            visibility: hidden;
        }

        .object-detail-group:not([open]) .object-detail-group-total {
            visibility: visible;
        }

        .object-detail-cell-input {
            width: min(100%, 132px);
            min-height: 34px;
            border: 1px solid rgba(42, 31, 44, 0.16);
            border-radius: 8px;
            background: #FFFFFF;
            color: var(--color-text-strong);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            padding: 6px 10px;
            text-align: center;
            outline: none;
        }

        .object-detail-cell-input:focus {
            border-color: rgba(128, 73, 198, 0.58);
            box-shadow: 0 0 0 3px rgba(128, 73, 198, 0.14);
        }

        .object-detail-cell-input--text {
            width: min(100%, 190px);
            font-size: 12px;
        }

        .object-detail-final {
            display: grid;
            grid-template-columns: minmax(0, 1fr) repeat(3, max-content);
            column-gap: 42px;
            align-items: end;
            padding: 10px 0 24px 0;
            margin-top: 0;
        }

        .object-detail-final-title {
            font-family: var(--font-mono);
            font-size: 30px;
            line-height: 1.12;
            font-weight: 700;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            color: var(--color-text-strong);
        }

        .object-detail-final-label {
            font-size: 13px;
            margin: 0 0 8px 0;
        }

        .object-detail-final-value {
            font-family: var(--font-mono);
            font-size: 24px;
            font-weight: 700;
            color: var(--color-text-strong);
            text-align: center;
        }

        .object-detail-final-total {
            font-size: 30px;
            color: var(--color-accent);
        }

        .object-detail-footer-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-top: 34px;
        }

        .object-detail-footer-button {
            min-height: var(--button-height-lg);
            border-radius: var(--button-radius);
            border: 1px solid var(--button-secondary-border);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-mono);
            font-size: var(--button-font-size);
            font-weight: var(--button-font-weight);
            text-transform: uppercase;
            text-decoration: none;
            transition: background 140ms ease, border-color 140ms ease, color 140ms ease, opacity 140ms ease;
            cursor: pointer;
        }

        .object-detail-footer-button,
        .object-detail-footer-button:link,
        .object-detail-footer-button:visited,
        .object-detail-footer-button:hover,
        .object-detail-footer-button:focus,
        .object-detail-footer-button:active {
            text-decoration: none !important;
        }

        .object-detail-footer-button--secondary {
            background: var(--button-secondary-bg);
            color: var(--button-secondary-text);
        }

        .object-detail-footer-button--secondary:link,
        .object-detail-footer-button--secondary:visited,
        .object-detail-footer-button--secondary:hover,
        .object-detail-footer-button--secondary:focus,
        .object-detail-footer-button--secondary:active {
            color: var(--button-secondary-text) !important;
        }

        .object-detail-footer-button--secondary:hover {
            background: var(--button-secondary-bg-hover);
            border-color: var(--button-secondary-border);
        }

        .object-detail-footer-button--primary {
            background: var(--button-primary-bg);
            border-color: var(--button-primary-bg);
            color: var(--button-primary-text);
        }

        .object-detail-footer-button--primary:link,
        .object-detail-footer-button--primary:visited,
        .object-detail-footer-button--primary:hover,
        .object-detail-footer-button--primary:focus,
        .object-detail-footer-button--primary:active {
            color: var(--button-primary-text) !important;
        }

        .object-detail-footer-button--primary:hover {
            background: var(--button-primary-bg-hover);
            border-color: var(--button-primary-bg-hover);
            color: var(--button-primary-text);
        }

        @media (max-width: 760px) {
            .object-detail-hero,
            .object-detail-section-header,
            .object-detail-final,
            .object-detail-footer-actions {
                grid-template-columns: 1fr;
                row-gap: 14px;
            }

            .object-detail-preview-placeholder {
                width: 100%;
            }

            .object-detail-table {
                display: block;
                overflow-x: auto;
            }

            .object-detail-table-head-row,
            .object-detail-table-row {
                min-width: 760px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
