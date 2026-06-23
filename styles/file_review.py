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
            grid-template-columns: max-content minmax(0, 1fr);
            column-gap: 24px;
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
            padding: 32px 34px 26px 34px;
            box-sizing: border-box;
            color: var(--color-text-strong);
            margin: 0 0 var(--review-card-gap) 0;
        }

        .file-review-object-edit-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 74px 94px 104px;
            column-gap: 16px;
            align-items: end;
        }

        .file-review-object-edit-group {
            display: block;
            margin: 0;
        }

        .file-review-object-edit-label {
            display: block;
            font-size: 14px;
            line-height: 1.2;
            margin: 0 0 8px 0;
            color: rgba(42, 31, 44, 0.52);
        }

        .file-review-object-edit-label-center {
            text-align: center;
        }

        .file-review-object-name-input,
        .file-review-object-qty-input {
            width: 100%;
            min-height: var(--input-height-md);
            box-sizing: border-box;
            border: 1px solid var(--input-border);
            border-radius: var(--input-radius);
            background: var(--input-bg);
            color: var(--input-text);
            font-family: var(--font-sans);
            outline: none;
            transition: border-color 140ms ease, box-shadow 140ms ease;
        }

        .file-review-object-name-input {
            font-size: var(--input-strong-font-size);
            line-height: var(--input-line-height);
            font-weight: var(--input-strong-font-weight);
            letter-spacing: var(--input-strong-letter-spacing);
            padding: var(--input-padding-y) var(--input-padding-x);
        }

        .file-review-object-qty-input {
            font-size: var(--input-compact-font-size);
            line-height: 1.1;
            font-weight: var(--input-compact-font-weight);
            padding: 8px 10px;
            text-align: center;
        }

        .file-review-object-name-input:focus,
        .file-review-object-qty-input:focus {
            border-color: var(--input-focus-border);
            box-shadow: 0 0 0 3px var(--input-focus-ring);
        }

        .file-review-object-confidence {
            min-height: 46px;
        }

        .file-review-object-confidence-value {
            font-size: 22px;
            line-height: 46px;
            font-weight: 700;
            color: #17131C;
            text-align: center;
        }

        .file-review-object-ignore-button {
            min-height: var(--button-height-md);
            border: 1px solid rgba(42, 31, 44, 0.18);
            border-radius: var(--button-radius);
            background: var(--button-secondary-bg);
            color: rgba(42, 31, 44, 0.72);
            font-family: var(--font-sans);
            font-size: var(--button-font-size);
            font-weight: var(--button-font-weight);
            text-transform: uppercase;
            cursor: pointer;
            transition: border-color 140ms ease, color 140ms ease, background 140ms ease;
        }

        .file-review-object-ignore-button:hover {
            border-color: rgba(214, 69, 63, 0.48);
            background: var(--color-danger-bg);
            color: var(--color-danger);
        }

        .file-review-object-detail-grid {
            display: grid;
            grid-template-columns: max-content minmax(0, 1fr);
            column-gap: 24px;
            row-gap: 14px;
            align-items: baseline;
        }

        .file-review-object-notes-list li {
            font-size: 16px;
            line-height: 1.42;
            margin: 3px 0;
            padding-left: 2px;
        }

        .file-review-missing-card {
            width: 100%;
            border: 1px solid rgba(42, 31, 44, 0.12);
            border-radius: 16px;
            background: var(--color-surface);
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.055);
            padding: 26px 34px 24px 34px;
            margin: 0 0 var(--review-card-gap) 0;
        }

        .file-review-missing-toggle {
            display: none;
        }

        .file-review-missing-collapsed {
            display: flex;
            align-items: center;
            gap: 22px;
        }

        .file-review-missing-expanded {
            display: none;
        }

        .file-review-missing-toggle:checked
            ~ .file-review-missing-collapsed {
            display: none;
        }

        .file-review-missing-toggle:checked
            ~ .file-review-missing-expanded {
            display: block;
        }

        .file-review-missing-title {
            color: rgba(42, 31, 44, 0.58);
            font-size: 18px;
            line-height: 1.25;
            font-weight: 700;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }

        .file-review-search-label {
            color: rgba(42, 31, 44, 0.58);
            font-size: 18px;
            line-height: 1.25;
            font-weight: 700;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }

        .file-review-search-row {
            display: grid;
            grid-template-columns: max-content minmax(0, 1fr);
            column-gap: 22px;
            align-items: center;
            margin: 0 0 14px 0;
        }

        .file-review-search-label {
            min-width: 150px;
        }

        .file-review-search-input {
            width: 100%;
            min-height: var(--input-height-md);
            box-sizing: border-box;
            border: 1px solid var(--input-border);
            border-radius: var(--input-radius);
            background: var(--input-bg);
            color: var(--input-text);
            font-family: var(--font-sans);
            font-size: var(--input-font-size);
            line-height: var(--input-line-height);
            font-weight: var(--input-font-weight);
            padding: var(--input-padding-y) var(--input-padding-x);
            outline: none;
            transition: border-color 140ms ease, box-shadow 140ms ease;
        }

        .file-review-search-input::placeholder {
            color: var(--input-placeholder);
            opacity: 1;
        }

        .file-review-search-input:focus {
            border-color: var(--input-focus-border);
            box-shadow: 0 0 0 3px var(--input-focus-ring);
        }

        .file-review-search-actions {
            display: flex;
            gap: 16px;
            margin: 22px 0 0 172px;
        }

        .file-review-search-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 150px;
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
            cursor: pointer;
            text-decoration: none;
            transition: border-color 140ms ease, color 140ms ease, background 140ms ease;
        }

        .file-review-search-button:hover {
            background: var(--button-secondary-bg-hover);
            color: var(--color-accent);
            border-color: rgba(128, 73, 198, 0.42);
        }

        .file-review-search-button--cancel:hover {
            background: var(--button-danger-bg-hover);
            color: var(--button-danger-text-hover);
            border-color: var(--button-danger-border-hover);
        }

        @media (max-width: 760px) {
            .file-review-card,
            .file-review-object-card,
            .file-review-missing-card {
                padding: 26px 22px 24px 22px;
                border-radius: 14px;
            }

            .file-review-summary-grid,
            .file-review-meta-row,
            .file-review-object-edit-grid,
            .file-review-object-detail-grid,
            .file-review-search-row {
                grid-template-columns: 1fr;
                row-gap: 8px;
            }

            .file-review-search-actions {
                margin-left: 0;
            }

            .file-review-value {
                font-size: 17px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
