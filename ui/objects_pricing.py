from __future__ import annotations

from datetime import UTC, datetime
import html
import math
from urllib.parse import quote


def _escape(value: object) -> str:
    """Return escaped text and a dash for unavailable estimate values."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _money(value: object) -> str:
    """Format pricing values for the objects estimate table."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float) and value != value:
        return "—"
    try:
        return f"₪{max(0, math.floor(float(value))):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


def _number(value: object, default: float = 0) -> float:
    """Convert pricing values for lightweight UI calculations."""
    if value is None or value == "":
        return default
    if isinstance(value, float) and value != value:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _input_money(value: object) -> str:
    """Format editable pricing input values with a stable currency prefix."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float) and value != value:
        return "—"
    try:
        return f"₪{max(0, math.floor(float(value))):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


def _sale_input_html(value: object, *, overridden: bool = False) -> str:
    input_value = _input_money(value)
    editable_attr = '' if input_value == "—" else ' contenteditable="true" tabindex="0"'
    disabled_attr = ' aria-disabled="true"' if input_value == "—" else ' aria-disabled="false"'
    overridden_attr = ' data-pricing-overridden="true"' if overridden else ''
    return (
        '<div class="objects-pricing-price-input" role="textbox" inputmode="numeric" '
        f'{editable_attr}{disabled_attr}{overridden_attr}>{input_value}</div>'
    )


def _quantity(value: object) -> str:
    """Format quantities as whole units in the pricing table."""
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _escape(value)
    if number != number:
        return "—"
    return str(int(round(number)))


def _object_key(row: dict[str, object]) -> str:
    """Return the stable Objects Estimation row key."""
    return str(row.get("object_key") or "")


def _estimate_key(estimate_id: str | None) -> str:
    """Return the HTML-safe estimate id attribute value."""
    return _escape(estimate_id or "")


def _run_key(run_id: str | None) -> str:
    """Return the HTML-safe run id attribute value."""
    return _escape(run_id or "")


def _data_number(value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float) and value != value:
        return ""
    return _escape(value)


def _suggestion_html(row: dict[str, object]) -> str:
    warning = _escape(row.get("sale_price_manual_warning"))
    if warning == "—":
        warning = ""
    text = warning or _escape(row.get("suggestion"))
    warning_class = " objects-pricing-suggestion--warning" if warning else ""
    return f'<div class="objects-pricing-suggestion{warning_class}">{text}</div>'


def _row_status(row: dict[str, object]) -> str:
    """Return normalized row status."""
    return str(row.get("status") or "pending").lower()


def _is_project_cost_row(row: dict[str, object]) -> bool:
    return _object_key(row).lower() in {"delivery", "installation"}


def _row_html(
    row: dict[str, object],
    *,
    with_review: bool,
    show_sale_total: bool,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    """Render one pricing row."""
    is_project_cost = _is_project_cost_row(row)
    if is_project_cost:
        return _project_cost_row_html(row, estimate_id=estimate_id, run_id=run_id)

    if with_review and not is_project_cost:
        review_html = _review_action_html(row, estimate_id=estimate_id, run_id=run_id)
    else:
        review_html = ""
    sale_total_html = _money(row.get("sale_price_total")) if show_sale_total else ""
    self_cost_html = _self_cost_unit_html(row)
    object_key = _escape(_object_key(row))
    estimate_key = _estimate_key(estimate_id)
    run_key = _run_key(run_id)
    source_self_cost = _data_number(row.get("manual_source_self_cost"))
    suggested_sale_price = _data_number(row.get("manual_source_suggested_sale_price"))

    return (
        '<div class="objects-pricing-row" '
        f'data-object-key="{object_key}" '
        f'data-estimate-id="{estimate_key}" '
        f'data-run-id="{run_key}" '
        f'data-source-self-cost="{source_self_cost}" '
        f'data-suggested-sale-price="{suggested_sale_price}">'
        '<div>'
        f'<div class="objects-pricing-name">{_escape(row.get("name"))}</div>'
        f'{_row_materials_html(row.get("materials"))}'
        '</div>'
        f'<div class="objects-pricing-number">{_quantity(row.get("quantity"))}</div>'
        f'<div class="objects-pricing-price objects-pricing-self-cost-cell">{self_cost_html}</div>'
        '<div class="objects-pricing-sale-cell">'
        f'{_sale_input_html(row.get("sale_price_unit"), overridden=bool(row.get("sale_price_overridden")))}'
        f'{_suggestion_html(row)}'
        '</div>'
        f'<div class="objects-pricing-price objects-pricing-sale-total-cell">{sale_total_html}</div>'
        '<div class="objects-pricing-action-cell"'
        f'{" data-action-cell=\"true\"" if with_review and not is_project_cost else ""}>{review_html}</div>'
        '</div>'
    )


def _project_cost_row_html(
    row: dict[str, object],
    *,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    object_key = _escape(_object_key(row))
    estimate_key = _estimate_key(estimate_id)
    run_key = _run_key(run_id)

    return (
        '<div class="objects-pricing-row objects-pricing-row--project-cost" '
        f'data-object-key="{object_key}" '
        f'data-estimate-id="{estimate_key}" '
        f'data-run-id="{run_key}">'
        '<div>'
        f'<div class="objects-pricing-name">{_escape(row.get("name"))}</div>'
        f'{_row_materials_html(row.get("materials"))}'
        '</div>'
        '<div class="objects-pricing-project-cost-cell">'
        f'{_sale_input_html(row.get("sale_price_unit"), overridden=bool(row.get("sale_price_overridden")))}'
        f'{_suggestion_html(row)}'
        '</div>'
        '</div>'
    )


def _review_action_html(
    row: dict[str, object],
    *,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    status = _row_status(row)
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


def _safe_int(value: object, *, default: int = 0) -> int:
    """Return a bounded integer for progress display."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, number))


def _parse_datetime(value: object) -> datetime | None:
    """Parse Supabase timestamps used by the smooth progress display."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _smooth_progress_curve(base: int) -> tuple[int, float]:
    """Return the display cap and seconds per visual progress point."""
    if base >= 95:
        return 99, 6.0
    if base >= 70:
        return 95, 3.0
    if base >= 35:
        return 85, 1.8
    return 70, 1.2


def _smooth_progress_percent(row: dict[str, object]) -> int:
    """Smooth a running estimate percent between backend updates."""
    base = _safe_int(row.get("progress_percent"), default=25)
    updated_at = _parse_datetime(row.get("progress_updated_at"))
    if updated_at is None:
        return base

    cap, seconds_per_percent = _smooth_progress_curve(base)
    elapsed = max(0.0, (datetime.now(UTC) - updated_at).total_seconds())
    visual_increment = int(elapsed / seconds_per_percent)
    return max(base, min(cap, base + visual_increment))


def _self_cost_unit_html(row: dict[str, object]) -> str:
    if _row_status(row) != "running":
        return _money(row.get("self_cost_unit"))

    updated_at = _parse_datetime(row.get("progress_updated_at"))
    if updated_at is None:
        percent = _escape(row.get("self_cost_unit") or f'{_safe_int(row.get("progress_percent"), default=25)}%')
        return (
            '<span class="objects-progress-status" aria-label="Estimating self cost">'
            '<span class="objects-progress-spinner" aria-hidden="true"></span>'
            f'<span class="objects-progress-percent">{percent}</span>'
            '</span>'
        )

    base = _safe_int(row.get("progress_percent"), default=25)
    cap, seconds_per_percent = _smooth_progress_curve(base)
    current = _smooth_progress_percent(row)
    return (
        '<span class="objects-progress-status" aria-label="Estimating self cost">'
        '<span class="objects-progress-spinner" aria-hidden="true"></span>'
        '<span class="objects-progress-percent" '
        f'data-start="{base}" '
        f'data-cap="{cap}" '
        f'data-step-ms="{int(seconds_per_percent * 1000)}" '
        f'data-updated-at="{_escape(updated_at.isoformat())}">'
        f'{current}%'
        '</span>'
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


def _pricing_table_header_html() -> str:
    """Render Objects Estimation table column headers."""
    return (
        '<div class="objects-pricing-header">'
        '<div class="objects-pricing-head">Project objects</div>'
        '<div class="objects-pricing-head">QTY</div>'
        '<div class="objects-pricing-head">Self cost<br>per unit</div>'
        '<div class="objects-pricing-head">Sale price<br>per unit</div>'
        '<div class="objects-pricing-head">Sale price<br>total</div>'
        '<div></div>'
        '</div>'
    )


def _rows_html(
    rows: list[dict[str, object]],
    *,
    with_review: bool,
    show_sale_total: bool,
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    """Render a list of pricing rows with consistent table options."""
    return "".join(
        _row_html(
            row,
            with_review=with_review,
            show_sale_total=show_sale_total,
            estimate_id=estimate_id,
            run_id=run_id,
        )
        for row in rows
    )


def _pricing_table_html(
    *,
    rows: list[dict[str, object]],
    project_costs: list[dict[str, object]],
    summary: dict[str, object],
    estimate_id: str | None,
    run_id: str | None,
) -> str:
    """Build the complete Objects Estimation pricing table HTML."""
    object_rows = _rows_html(
        rows,
        with_review=True,
        show_sale_total=True,
        estimate_id=estimate_id,
        run_id=run_id,
    )
    project_cost_rows = _rows_html(
        project_costs,
        with_review=False,
        show_sale_total=False,
        estimate_id=estimate_id,
        run_id=run_id,
    )

    return (
        '<div class="objects-pricing-card">'
        f'{_pricing_table_header_html()}'
        '<div class="objects-pricing-table">'
        f'{object_rows}'
        f'{project_cost_rows}'
        f'{_summary_html(summary)}'
        '</div>'
        '</div>'
    )




# Public module surface used by screens.objects.
number = _number
row_status = _row_status
smooth_progress_percent = _smooth_progress_percent
pricing_table_html = _pricing_table_html
