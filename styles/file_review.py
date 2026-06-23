from __future__ import annotations

import streamlit as st


def apply_file_review_css() -> None:
    """Install File Review-specific card and object list styling."""
    st.markdown(
        """
        <style>
        .file-review-card {
            width: 100%;
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 16px;
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.055);
            padding: 32px 34px 26px 34px;
            box-sizing: border-box;
            color: var(--color-text-strong);
            margin: var(--post-upload-heading-gap) 0 0 0;
        }

        .file-review-summary-grid {
            display: grid;
            grid-template-columns: 200px minmax(0, 1fr);
            column-gap: 28px;
            row-gap: 14px;
            align-items: baseline;
        }

        .file-review-label,
        .file-review-section-title,
        .file-review-meta-title {
            font-size: 18px;
            line-height: 1.25;
            font-weight: 700;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            color: rgba(42, 31, 44, 0.58);
        }

        .file-review-label {
            letter-spacing: 0.12em;
            color: rgba(42, 31, 44, 0.54);
        }

        .file-review-value {
            font-size: 18px;
            line-height: 1.28;
            font-weight: 700;
            letter-spacing: -0.015em;
            color: var(--color-text-strong);
        }

        .file-review-divider {
            height: 1px;
            background: rgba(42, 31, 44, 0.14);
            margin: 24px 0 20px 0;
        }

        .file-review-section-title {
            margin: 0 0 10px 0;
        }

        .file-review-missing-list,
        .file-review-object-notes-list {
            margin: 0 0 0 22px;
            padding: 0;
            color: var(--color-text-strong);
        }

        .file-review-missing-list li {
            font-size: 16px;
            line-height: 1.42;
            margin: 3px 0;
            padding-left: 2px;
        }

        .file-review-meta-summary {
            list-style: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
            padding: 0;
            user-select: none;
        }

        .file-review-meta-summary::-webkit-details-marker {
            display: none;
        }

        .file-review-meta-summary::before {
            content: "▾";
            font-size: 28px;
            line-height: 1;
            color: rgba(42, 31, 44, 0.60);
            transform: translateY(-1px);
        }

        .file-review-meta-details:not([open]) .file-review-meta-summary::before {
            content: "▸";
        }

        .file-review-meta-table {
            margin-top: 12px;
            border-top: 1px solid rgba(42, 31, 44, 0.10);
        }

        .file-review-meta-row {
            display: grid;
            grid-template-columns: 190px minmax(0, 1fr);
            column-gap: 14px;
            min-height: 27px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(42, 31, 44, 0.08);
            align-items: center;
        }

        .file-review-meta-key {
            font-size: 14px;
            line-height: 1.2;
            color: rgba(42, 31, 44, 0.52);
        }

        .file-review-meta-value {
            font-size: 14px;
            line-height: 1.2;
            color: var(--color-text-strong);
            font-weight: 500;
            overflow-wrap: anywhere;
        }

        .file-review-detected-title {
            font-family: var(--font-mono) !important;
            color: var(--color-accent) !important;
            font-size: var(--post-upload-title-size) !important;
            line-height: var(--post-upload-title-line-height) !important;
            font-weight: 500 !important;
            letter-spacing: -0.02em !important;
            margin: 48px 0 var(--post-upload-heading-gap) 0 !important;
            padding: 0 !important;
        }

        .file-review-object-card {
            width: 100%;
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 16px;
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.055);
            padding: 28px 34px 26px 34px;
            box-sizing: border-box;
            color: var(--color-text-strong);
            margin: 0 0 20px 0;
        }

        .file-review-object-top {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 110px 130px;
            column-gap: 34px;
            align-items: start;
            margin-bottom: 28px;
        }

        .file-review-object-name {
            font-size: 28px;
            line-height: 1.18;
            font-weight: 800;
            letter-spacing: -0.035em;
            color: #17131C;
        }

        .file-review-object-metric-label,
        .file-review-object-field-label,
        .file-review-object-notes-title {
            font-size: 14px;
            line-height: 1.2;
            color: rgba(42, 31, 44, 0.52);
        }

        .file-review-object-metric-label {
            font-size: 13px;
            margin-bottom: 6px;
        }

        .file-review-object-metric-value {
            font-size: 34px;
            line-height: 1;
            font-weight: 500;
            color: #111111;
        }

        .file-review-object-grid {
            display: grid;
            grid-template-columns: 1fr 1.45fr;
            column-gap: 44px;
            row-gap: 20px;
            margin-bottom: 18px;
        }

        .file-review-object-field-label {
            margin-bottom: 12px;
        }

        .file-review-object-field-value {
            font-size: 16px;
            line-height: 1.42;
            color: var(--color-text-strong);
        }

        .file-review-object-notes-title {
            margin: 18px 0 10px 0;
        }

        .file-review-object-notes-list li {
            font-size: 16px;
            line-height: 1.45;
            margin: 8px 0;
        }

        @media (max-width: 760px) {
            .file-review-card,
            .file-review-object-card {
                padding: 26px 22px 24px 22px;
                border-radius: 14px;
            }

            .file-review-summary-grid,
            .file-review-meta-row,
            .file-review-object-top,
            .file-review-object-grid {
                grid-template-columns: 1fr;
                row-gap: 8px;
            }

            .file-review-value {
                font-size: 17px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
