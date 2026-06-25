from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import html
from urllib.parse import quote

import streamlit as st

from styles.objects import apply_objects_css
from ui.layout import render_post_upload_header
from use_cases.estimation import (
    estimate_first_object_for_run,
    load_objects_estimation_data,
    start_estimation_for_run,
)


_ESTIMATION_EXECUTOR = ThreadPoolExecutor(max_workers=1)


def _escape(value: object) -> str:
    """Return escaped text and a dash for unavailable estimate values."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _money(value: object) -> str:
    """Format temporary pricing fixture values for the pricing table."""
    if value is None or value == "":
        return "—"
    try:
        return f"₪{round(float(value)):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


def _row_html(
    row: dict[str, object],
    *,
    with_review: bool,
    show_sale_total: bool,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    """Render one pricing row. Buttons are visual until object detail exists."""
    if with_review:
        action_label = "Done" if row.get("reviewed") else "Review"
        action_class = " objects-pricing-review-button--done" if row.get("reviewed") else ""
        object_id = quote(str(row.get("object_key") or ""))
        estimate_param = quote(str(estimate_id or ""))
        run_param = quote(str(run_id or ""))
        review_html = (
            f'<a class="objects-pricing-review-button{action_class}" '
            f'href="?screen=object_detail&run_id={run_param}&estimate_id={estimate_param}&object_id={object_id}" '
            f'target="_self">{action_label}</a>'
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


def _empty_objects_data() -> dict[str, object]:
    """Return an empty real-data shape when no estimate exists yet."""
    return {
        "rows": [],
        "project_costs": [],
        "summary": {"project_price": None, "vat": None, "total": None},
    }


def _consume_estimation_future() -> None:
    """Store the background estimation result once the worker is done."""
    future = st.session_state.get("estimation_first_object_future")
    if not isinstance(future, Future) or not future.done():
        return

    try:
        st.session_state.last_estimation_result = future.result()
        st.session_state.last_estimation_error = None
    except Exception as exc:
        st.session_state.last_estimation_error = str(exc)
    finally:
        st.session_state.estimation_first_object_future = None


def _ensure_estimation_shell(*, run_id: str | None, company_id: str) -> None:
    """Create the estimate shell after navigation, not during File Review click."""
    if not run_id:
        return
    if not st.session_state.get("estimation_start_requested"):
        return

    try:
        estimate = start_estimation_for_run(
            run_id=run_id,
            company_id=company_id,
        )
        st.session_state.current_estimate_id = estimate["estimate_id"]
        st.session_state.estimation_first_object_requested = True
        st.session_state.last_estimation_error = None
    except Exception as exc:
        st.session_state.last_estimation_error = f"Could not start Objects Estimation: {exc}"
    finally:
        st.session_state.estimation_start_requested = False


def _start_first_object_estimation_if_requested(
    *,
    estimate_id: str | None,
    run_id: str | None,
    company_id: str,
) -> None:
    """Start the first object estimate in the background after the page renders."""
    if not estimate_id or not run_id:
        return
    if not st.session_state.get("estimation_first_object_requested"):
        return
    if isinstance(st.session_state.get("estimation_first_object_future"), Future):
        st.session_state.estimation_first_object_requested = False
        return

    file_name = st.session_state.get("uploaded_file_name")
    file_bytes = st.session_state.get("uploaded_file_bytes")
    if not file_name or not file_bytes:
        st.session_state.estimation_first_object_requested = False
        st.session_state.last_estimation_error = (
            "Uploaded file bytes are missing. Please upload the file again."
        )
        return

    st.session_state.estimation_first_object_future = _ESTIMATION_EXECUTOR.submit(
        estimate_first_object_for_run,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )
    st.session_state.estimation_first_object_requested = False
    st.session_state.last_estimation_error = None
    # Do not rerun here: Streamlit Cloud keeps the previous DOM dimmed while a
    # rerun is active, which creates duplicated screens during long estimates.


def render_objects_screen(company_id: str) -> None:
    """Render the object pricing review screen with temporary fixture data."""
    apply_objects_css()
    _consume_estimation_future()
    render_post_upload_header(
        "Objects Estimation",
        "Review objects → Set sale price → Generate proposal",
        class_name="objects-estimation-header",
    )

    estimate_id = st.session_state.get("current_estimate_id")
    run_id = st.session_state.get("current_run_id")
    _ensure_estimation_shell(run_id=run_id, company_id=company_id)
    estimate_id = st.session_state.get("current_estimate_id")

    if estimate_id:
        try:
            data = load_objects_estimation_data(estimate_id)
        except Exception as exc:
            st.error(f"Could not load Objects Estimation: {exc}")
            data = _empty_objects_data()
    else:
        st.warning("No active estimate. Return to File Review and start Objects Estimation.")
        data = _empty_objects_data()

    if st.session_state.get("last_estimation_error"):
        st.error(f"Estimation failed: {st.session_state.last_estimation_error}")

    approved_object_keys = st.session_state.get("approved_object_keys", set())
    object_rows = "".join(
        _row_html(
            {**row, "reviewed": row.get("object_key") in approved_object_keys},
            with_review=True,
            show_sale_total=True,
            estimate_id=estimate_id,
            run_id=run_id,
        )
        for row in data["rows"]
    )
    project_cost_rows = "".join(
        _row_html(
            row,
            with_review=False,
            show_sale_total=False,
            estimate_id=estimate_id,
            run_id=run_id,
        )
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

    _start_first_object_estimation_if_requested(
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
    )

    col_back, col_generate = st.columns(2, gap="small")

    if col_back.button("BACK TO FILE REVIEW", type="secondary", use_container_width=True):
        st.session_state.screen = "file_review"
        st.rerun()

    if col_generate.button("GENERATE PROPOSAL", type="primary", use_container_width=True):
        st.session_state.screen = "objects"
