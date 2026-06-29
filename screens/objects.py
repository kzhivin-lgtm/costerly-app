from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime
import html
import math
from urllib.parse import quote

import streamlit as st

from config import get_optional_secret
from styles.objects import apply_objects_css
from ui.js_guards import (
    install_objects_progress_sync,
    install_post_upload_transition_guard,
)
from ui.layout import render_post_upload_header
from ui.perf_debug import mark_python_perf, measure_python_perf
from ui.screen_transition import (
    FILE_REVIEW_MARKER_ID,
    OBJECTS_MARKER_ID,
    post_upload_transition_shell_html,
)
from use_cases.estimation import load_objects_estimation_data
from use_cases.estimation_progress import get_estimate_progress


def _escape(value: object) -> str:
    """Return escaped text and a dash for unavailable estimate values."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _money(value: object) -> str:
    """Format temporary pricing fixture values for the pricing table."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float) and value != value:
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
    """Render one pricing row."""
    if with_review:
        review_html = _review_action_html(row, estimate_id=estimate_id, run_id=run_id)
    else:
        review_html = ""
    sale_total_html = _money(row.get("sale_price_total")) if show_sale_total else ""
    self_cost_html = _self_cost_unit_html(row)
    object_key = _escape(row.get("object_key"))
    estimate_key = _escape(estimate_id or "")
    run_key = _escape(run_id or "")

    return (
        '<div class="objects-pricing-row" '
        f'data-object-key="{object_key}" '
        f'data-estimate-id="{estimate_key}" '
        f'data-run-id="{run_key}">'
        '<div>'
        f'<div class="objects-pricing-name">{_escape(row.get("name"))}</div>'
        f'{_row_materials_html(row.get("materials"))}'
        '</div>'
        f'<div class="objects-pricing-number">{_escape(row.get("quantity"))}</div>'
        f'<div class="objects-pricing-price objects-pricing-self-cost-cell">{self_cost_html}</div>'
        '<div class="objects-pricing-sale-cell">'
        f'<input class="objects-pricing-price-input" type="text" value="{_money(row.get("sale_price_unit"))}" />'
        f'<div class="objects-pricing-suggestion">{_escape(row.get("suggestion"))}</div>'
        '</div>'
        f'<div class="objects-pricing-price objects-pricing-sale-total-cell">{sale_total_html}</div>'
        f'<div class="objects-pricing-action-cell" data-action-cell="true">{review_html}</div>'
        '</div>'
    )


def _review_action_html(
    row: dict[str, object],
    *,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    status = str(row.get("status") or "pending").lower()
    if status == "completed":
        action_label = "Done" if row.get("reviewed") else "Review"
        action_class = " objects-pricing-review-button--done" if row.get("reviewed") else ""
        object_id = quote(str(row.get("object_key") or ""))
        estimate_param = quote(str(estimate_id or ""))
        run_param = quote(str(run_id or ""))
        return (
            f'<a class="objects-pricing-review-button{action_class}" '
            f'href="?screen=object_detail&run_id={run_param}&estimate_id={estimate_param}&object_id={object_id}" '
            f'target="_self">{action_label}</a>'
        )

    action_label = "Estimating" if status == "running" else "Pending"
    return (
        '<span class="objects-pricing-review-button objects-pricing-review-button--disabled" '
        'aria-disabled="true">'
        f'{action_label}'
        '</span>'
    )


def _row_materials_html(value: object) -> str:
    if value is None or value == "":
        return ""
    return f'<div class="objects-pricing-materials">{_escape(value)}</div>'


def _self_cost_unit_html(row: dict[str, object]) -> str:
    if str(row.get("status") or "").lower() != "running":
        return _money(row.get("self_cost_unit"))

    updated_at = _parse_datetime(row.get("progress_updated_at"))
    if updated_at is None:
        return _escape(row.get("self_cost_unit"))

    base = _safe_int(row.get("progress_percent"), default=25)
    cap, seconds_per_percent = _smooth_progress_curve(base)
    current = _smooth_progress_percent(row)
    return (
        '<span class="objects-progress-percent" '
        f'data-start="{base}" '
        f'data-cap="{cap}" '
        f'data-step-ms="{int(seconds_per_percent * 1000)}" '
        f'data-updated-at="{_escape(updated_at.isoformat())}">'
        f'{current}%'
        '</span>'
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
        f'<div class="objects-pricing-summary-value" data-summary-field="project_price">{_money(summary.get("project_price"))}</div>'
        '</div>'
        '<div>'
        '<div class="objects-pricing-summary-title">VAT 18%</div>'
        f'<div class="objects-pricing-summary-value" data-summary-field="vat">{_money(summary.get("vat"))}</div>'
        '</div>'
        '<div>'
        '<div class="objects-pricing-summary-title">Project Total</div>'
        f'<div class="objects-pricing-summary-value objects-pricing-summary-value--total" data-summary-field="total">{_money(summary.get("total"))}</div>'
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


def _objects_progress_sync_config() -> tuple[str | None, str | None]:
    return (
        get_optional_secret("SUPABASE_URL"),
        get_optional_secret("SUPABASE_ANON_KEY"),
    )


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


def _data_with_progress(data: dict[str, object], estimate_id: str | None) -> dict[str, object]:
    """Show File Review objects immediately until the estimate shell reaches Supabase."""
    rows_source = data.get("rows") or st.session_state.get("objects_estimation_seed_rows") or []
    if not rows_source:
        return data

    progress = get_estimate_progress(estimate_id)
    rows = [dict(row) for row in rows_source]
    if progress:
        active_object_id = str(progress.get("object_id") or "")
        for row in rows:
            if str(row.get("object_key") or "") == active_object_id:
                row["status"] = str(progress.get("status") or "running")
                row["progress_percent"] = progress.get("percent")
                row["progress_updated_at"] = progress.get("updated_at")
                break

    for row in rows:
        status = str(row.get("status") or "pending").lower()
        if status == "running":
            row["self_cost_unit"] = f"{_smooth_progress_percent(row)}%"

    return {**data, "rows": rows}


def _smooth_progress_percent(row: dict[str, object]) -> int:
    base = _safe_int(row.get("progress_percent"), default=25)
    updated_at = _parse_datetime(row.get("progress_updated_at"))
    if updated_at is None:
        return base

    elapsed_seconds = max(0, (datetime.now(UTC) - updated_at).total_seconds())
    cap, seconds_per_percent = _smooth_progress_curve(base)
    smoothed = base + math.floor(elapsed_seconds / seconds_per_percent)
    return max(1, min(cap, smoothed))


def _smooth_progress_curve(base: int) -> tuple[int, float]:
    if base < 25:
        return 24, 0.4
    if base < 65:
        return 64, 0.5
    if base < 78:
        return 77, 0.3
    if base < 88:
        return 87, 0.25
    if base < 96:
        return 95, 0.2
    return 99, 0.2


def _safe_int(value: object, *, default: int) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, float) and value != value:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not value:
        return None
    try:
        raw = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def render_objects_screen(company_id: str) -> None:
    """Render the object pricing review screen with temporary fixture data."""
    with measure_python_perf("apply objects css"):
        apply_objects_css()
    _consume_estimation_future()

    estimate_id = st.session_state.get("current_estimate_id")
    run_id = st.session_state.get("current_run_id")
    estimation_running = isinstance(st.session_state.get("estimation_first_object_future"), Future)
    if estimation_running and estimate_id:
        st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)

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
        supabase_url, supabase_anon_key = _objects_progress_sync_config()
        if estimate_id and supabase_url and supabase_anon_key:
            install_objects_progress_sync(
                supabase_url=supabase_url,
                supabase_anon_key=supabase_anon_key,
                estimate_id=str(estimate_id),
                interval_ms=1500,
            )

    if not estimate_id:
        st.warning("No active estimate. Return to File Review and start Objects Estimation.")

    if data_error:
        st.error(data_error)

    if cache_warning:
        st.warning(cache_warning)

    if st.session_state.get("last_estimation_error"):
        st.error(f"Estimation failed: {st.session_state.last_estimation_error}")

    data = _data_with_progress(data, estimate_id)

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

    col_back, col_generate = st.columns(2, gap="small")

    if col_back.button("BACK TO FILE REVIEW", type="secondary", use_container_width=True):
        st.session_state.screen = "file_review"
        st.rerun()

    if col_generate.button("GENERATE PROPOSAL", type="primary", use_container_width=True):
        st.session_state.screen = "objects"
