from __future__ import annotations

import html

import streamlit as st

from dev.fixtures.objects import OBJECTS_FIXTURE
from styles.objects import apply_objects_css
from ui.layout import render_post_upload_header


def _escape(value: object) -> str:
    """Return escaped text and a dash for unavailable estimate values."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _money(value: object) -> str:
    """Format temporary pricing fixture values for the pricing table."""
    if value is None or value == "":
        return "—"
    return f"₪{int(value):,}".replace(",", " ")


def _row_html(
    row: dict[str, object],
    *,
    with_review: bool,
    show_sale_total: bool,
) -> str:
    """Render one pricing row. Buttons are visual until object detail exists."""
    if with_review:
        action_label = "Done" if row.get("reviewed") else "Review"
        action_class = " objects-pricing-review-button--done" if row.get("reviewed") else ""
        review_html = (
            f'<a class="objects-pricing-review-button{action_class}" '
            f'href="?screen=object_detail" target="_self">{action_label}</a>'
        )
    else:
        review_html = ""
    sale_total_html = _money(row.get("sale_price_total")) if show_sale_total else ""

    return (
        '<div class="objects-pricing-row">'
        '<div>'
        f'<div class="objects-pricing-name">{_escape(row.get("name"))}</div>'
        f'<div class="objects-pricing-materials">{_escape(row.get("materials"))}</div>'
        '</div>'
        f'<div class="objects-pricing-number">{_escape(row.get("quantity"))}</div>'
        f'<div class="objects-pricing-price">{_money(row.get("self_cost_unit"))}</div>'
        '<div class="objects-pricing-sale-cell">'
        f'<input class="objects-pricing-price-input" type="text" value="{_money(row.get("sale_price_unit"))}" />'
        f'<div class="objects-pricing-suggestion">{_escape(row.get("suggestion"))}</div>'
        '</div>'
        f'<div class="objects-pricing-price">{sale_total_html}</div>'
        f'<div class="objects-pricing-action-cell">{review_html}</div>'
        '</div>'
    )


def _summary_html(summary: dict[str, object]) -> str:
    """Render project-level price summary."""
    return (
        '<div class="objects-pricing-summary">'
        '<div>'
        '<div class="objects-pricing-summary-title">Project Summary</div>'
        '<button class="objects-pricing-download-button" type="button">'
        '<span class="objects-pricing-download-pill">Download XLS</span>'
        '</button>'
        '</div>'
        '<div>'
        '<div class="objects-pricing-summary-title">Project Price</div>'
        f'<div class="objects-pricing-summary-value">{_money(summary.get("project_price"))}</div>'
        '</div>'
        '<div>'
        '<div class="objects-pricing-summary-title">VAT 18%</div>'
        f'<div class="objects-pricing-summary-value">{_money(summary.get("vat"))}</div>'
        '</div>'
        '<div>'
        '<div class="objects-pricing-summary-title">Project Total</div>'
        f'<div class="objects-pricing-summary-value objects-pricing-summary-value--total">{_money(summary.get("total"))}</div>'
        '</div>'
        '</div>'
    )


def render_objects_screen(company_id: str) -> None:
    """Render the object pricing review screen with temporary fixture data."""
    apply_objects_css()
    render_post_upload_header(
        "Objects Estimation",
        "Review objects -> Set sale price -> Generate proposal",
        class_name="objects-estimation-header",
    )

    data = OBJECTS_FIXTURE
    approved_object_keys = st.session_state.get("approved_object_keys", set())
    object_rows = "".join(
        _row_html(
            {**row, "reviewed": row.get("object_key") in approved_object_keys},
            with_review=True,
            show_sale_total=True,
        )
        for row in data["rows"]
    )
    project_cost_rows = "".join(
        _row_html(row, with_review=False, show_sale_total=False)
        for row in data["project_costs"]
    )

    st.markdown(
        '<div class="objects-pricing-card">'
        '<div class="objects-pricing-header">'
        '<div class="objects-pricing-head">Project objects</div>'
        '<div class="objects-pricing-head">QTY</div>'
        '<div class="objects-pricing-head">Self cost<br>per unit</div>'
        '<div class="objects-pricing-head">Sale price<br>per unit</div>'
        '<div class="objects-pricing-head">Sale price<br>total</div>'
        '<div></div>'
        '</div>'
        '<div class="objects-pricing-table">'
        f'{object_rows}'
        f'{project_cost_rows}'
        f'{_summary_html(data["summary"])}'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_back, col_generate = st.columns(2, gap="small")

    if col_back.button("BACK TO FILE REVIEW", type="secondary", use_container_width=True):
        st.session_state.screen = "file_review"
        st.rerun()

    if col_generate.button("GENERATE PROPOSAL", type="primary", use_container_width=True):
        st.session_state.screen = "objects"
