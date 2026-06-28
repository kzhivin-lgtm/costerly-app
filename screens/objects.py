from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import html
from urllib.parse import quote

import streamlit as st

from styles.objects import apply_objects_css
from ui.js_guards import install_post_upload_transition_guard
from ui.layout import render_post_upload_header
from ui.perf_debug import mark_python_perf, measure_python_perf
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
    OBJECTS_MARKER_ID,
    post_upload_transition_shell_html,
)
from use_cases.estimation import (
    estimate_first_object_for_run,
    load_objects_estimation_data,
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
        mark_python_perf("estimation future pending", pending=isinstance(future, Future))
        return

    with measure_python_perf("consume estimation future"):
        try:
            st.session_state.last_estimation_result = future.result()
            st.session_state.last_estimation_error = None
            estimate_id = st.session_state.get("current_estimate_id")
            if estimate_id:
                st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
        except Exception as exc:
            st.session_state.last_estimation_error = str(exc)
        finally:
            st.session_state.estimation_first_object_future = None


def _load_objects_screen_data(estimate_id: str) -> tuple[dict[str, object], str | None]:
    """Load Objects data from session cache first, then Supabase when needed."""
    cache = st.session_state.setdefault("objects_estimation_data_cache", {})
    dirty_estimates = st.session_state.setdefault("objects_estimation_cache_dirty", set())

    if estimate_id in cache and estimate_id not in dirty_estimates:
        mark_python_perf("objects cache hit", estimate_id=estimate_id)
        return cache[estimate_id], None

    mark_python_perf(
        "objects cache miss",
        estimate_id=estimate_id,
        dirty=estimate_id in dirty_estimates,
    )
    try:
        with measure_python_perf("load objects estimation data", estimate_id=estimate_id):
            data = load_objects_estimation_data(estimate_id)
    except Exception as exc:
        cached = cache.get(estimate_id)
        if cached is not None:
            return (
                cached,
                f"Could not refresh Objects Estimation from Supabase. Showing last available data. ({exc})",
            )
        raise

    cache[estimate_id] = data
    dirty_estimates.discard(estimate_id)
    return data, None


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
    mark_python_perf("first object estimation submitted", estimate_id=estimate_id)
    st.session_state.estimation_first_object_requested = False
    st.session_state.last_estimation_error = None
    # Do not rerun here: Streamlit Cloud keeps the previous DOM dimmed while a
    # rerun is active, which creates duplicated screens during long estimates.


def render_objects_screen(company_id: str) -> None:
    """Render the object pricing review screen with temporary fixture data."""
    with measure_python_perf("apply objects css"):
        apply_objects_css()
    _consume_estimation_future()

    estimate_id = st.session_state.get("current_estimate_id")
    run_id = st.session_state.get("current_run_id")

    data_error = None
    cache_warning = None
    if estimate_id:
        try:
            with measure_python_perf("objects data section", estimate_id=estimate_id):
                data, cache_warning = _load_objects_screen_data(estimate_id)
        except Exception as exc:
            data_error = f"Could not load Objects Estimation: {exc}"
            data = _empty_objects_data()
    else:
        data = _empty_objects_data()

    with measure_python_perf("objects header + guard"):
        render_post_upload_header(
            "Objects Estimation",
            "Review objects → Set sale price → Generate proposal",
            class_name="objects-estimation-header",
            marker_id=OBJECTS_MARKER_ID,
        )
        install_post_upload_transition_guard(
            [
                {
                    "label": "BACK TO FILE REVIEW",
                    "targetMarkerId": FILE_REVIEW_MARKER_ID,
                    "shellHtml": post_upload_transition_shell_html(title="File Review"),
                }
            ],
            current_marker_id=OBJECTS_MARKER_ID,
        )

    if not estimate_id:
        st.warning("No active estimate. Return to File Review and start Objects Estimation.")

    if data_error:
        st.error(data_error)

    if cache_warning:
        st.warning(cache_warning)

    if st.session_state.get("last_estimation_error"):
        st.error(f"Estimation failed: {st.session_state.last_estimation_error}")

    approved_object_keys = st.session_state.get("approved_object_keys", set())
    with measure_python_perf(
        "build objects table html",
        object_rows=len(data["rows"]),
        project_cost_rows=len(data["project_costs"]),
    ):
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

    with measure_python_perf("render objects table markdown"):
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
