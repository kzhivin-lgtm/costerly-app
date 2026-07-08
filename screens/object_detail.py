from __future__ import annotations

import html
import json

import streamlit as st

from styles.object_detail import apply_object_detail_css
from ui.js_guards import install_object_detail_input_guard
from use_cases.estimation import (
    apply_object_detail_line_edit,
    apply_object_detail_snapshot,
    approve_object_estimate,
    load_object_detail_data,
)


def _escape(value: object) -> str:
    """Return escaped text and a dash for missing table values."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


def _money(value: object) -> str:
    """Format monetary values for object detail tables."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float) and value != value:
        return "—"
    try:
        return f"₪{round(float(value)):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


def _quantity(value: object) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return _escape(value)


def _number_text(value: object) -> str:
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _slug(value: object) -> str:
    text = str(value or "").lower()
    return "".join(char if char.isalnum() else "_" for char in text).strip("_")


def _metric_html(label: str, value: object) -> str:
    """Render one compact section metric."""
    formatted = _money(value) if isinstance(value, int | float) else _escape(value)
    metric_key = _slug(label)
    return (
        f'<div class="object-detail-section-metric" data-metric="{_escape(metric_key)}">'
        f'<div class="object-detail-section-label">{_escape(label)}</div>'
        f'<div class="object-detail-section-value">{formatted}</div>'
        '</div>'
    )


def _input_html(value: object, kind: str = "text", field: str = "") -> str:
    """Render a visual editable field for future calculation wiring."""
    field_attr = f' data-field="{_escape(field)}"' if field else ""
    inputmode = "text" if kind == "text" else "decimal"
    return (
        f'<div class="object-detail-cell-input object-detail-cell-input--{kind}" '
        f'role="textbox" contenteditable="true" tabindex="0" inputmode="{inputmode}"'
        f'{field_attr}>{_escape(value)}</div>'
    )


def _row_values(section: dict[str, object], row: dict[str, object]) -> list[str]:
    """Map normalized estimate rows to visible table cells."""
    columns = section["columns"]
    if columns[0] == "Work":
        return [
            _escape(row.get("work")),
            _escape(row.get("role")),
            _input_html(_number_text(row.get("hours")), "number", "hours"),
            _input_html(_money(row.get("rate")), "money", "rate"),
            f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
        ]
    if len(columns) == 4:
        monthly_cost_display = row.get("monthly_cost_display")
        monthly_cost_value = (
            _escape(monthly_cost_display)
            if monthly_cost_display
            else _money(row.get("monthly_cost"))
        )
        monthly_cost_kind = "percent" if monthly_cost_display else "money"
        return [
            _escape(row.get("item")),
            _input_html(monthly_cost_value, monthly_cost_kind, "monthly_cost"),
            _input_html(row.get("allocation"), "text", "allocation_basis"),
            f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
        ]
    return [
        _escape(row.get("item")),
        _escape(row.get("unit")),
        _input_html(_money(row.get("unit_cost")), "money", "unit_cost"),
        _input_html(_number_text(row.get("qty")), "number", "quantity"),
        f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
    ]


def _group_summary_value(column: str, group_rows: list[dict[str, object]]) -> str:
    if column in {"Qty", "Hours"}:
        key = "qty" if column == "Qty" else "hours"
        return _number_text(sum(float(row.get(key) or 0) for row in group_rows))
    if column in {"Cost", "Monthly cost"}:
        key = "monthly_cost" if column == "Monthly cost" else "cost"
        return _money(sum(float(row.get(key) or 0) for row in group_rows))
    return ""


def _table_html(section: dict[str, object]) -> str:
    """Render a grouped cost table from normalized estimate rows."""
    columns = section["columns"]
    rows = section["rows"]
    column_count = len(columns)
    section_key = str(section.get("key") or _slug(section.get("title")))
    table_class = f"object-detail-table object-detail-table--cols-{column_count}"
    header = "".join(
        f'<div class="object-detail-table-head">{_escape(column)}</div>' for column in columns
    )

    body_parts: list[str] = []
    grouped_rows: dict[object, list[dict[str, object]]] = {}
    for row in rows:
        grouped_rows.setdefault(row.get("group"), []).append(row)

    for group, group_rows in grouped_rows.items():
        summary_cells = ['<span class="object-detail-group-title">' + _escape(group) + "</span>"]
        for column in columns[1:]:
            value = _group_summary_value(column, group_rows)
            summary_cells.append(
                f'<span class="object-detail-group-total">{value}</span>'
            )

        body_parts.append(
            '<details class="object-detail-group" open>'
            '<summary class="object-detail-group-summary">'
            + "".join(summary_cells)
            + "</summary>"
        )

        for row in group_rows:
            values = _row_values(section, row)
            body_parts.append(
                '<div class="object-detail-table-row" '
                f'data-line-id="{_escape(row.get("line_id"))}" '
                f'data-section="{_escape(section_key)}">'
                + "".join(f'<div class="object-detail-table-cell">{value}</div>' for value in values)
                + "</div>"
            )
        body_parts.append("</details>")

    return (
        f'<div class="{table_class}" data-section="{_escape(section_key)}">'
        f'<div class="object-detail-table-head-row">{header}</div>'
        f'{"".join(body_parts)}'
        '</div>'
    )


def _section_html(section: dict[str, object]) -> str:
    """Render one cost section with metrics and a grouped table."""
    metrics = "".join(_metric_html(label, value) for label, value in section["metrics"])
    column_count = len(section["columns"])
    metric_offset = ""
    if column_count == 5 and len(section["metrics"]) == 3:
        metric_offset = '<div class="object-detail-section-metric-spacer"></div>'

    return (
        f'<section class="object-detail-section object-detail-section--cols-{column_count}" '
        f'data-section="{_escape(section.get("key") or _slug(section["title"]))}">'
        '<div class="object-detail-section-header">'
        f'<div class="object-detail-section-title">{_escape(section["title"])}</div>'
        f'{metric_offset}{metrics}'
        '</div>'
        f'{_table_html(section)}'
        '</section>'
    )


def _final_html(data: dict[str, object]) -> str:
    """Render final self-cost block."""
    summary = data["self_cost"]
    return (
        '<div class="object-detail-final">'
        f'<div class="object-detail-final-title">{_escape(summary["title"])}</div>'
        '<div>'
        '<div class="object-detail-final-label">Excl. VAT</div>'
        f'<div class="object-detail-final-value" data-final="excl_vat">{_money(summary["excl_vat"])}</div>'
        '</div>'
        '<div>'
        '<div class="object-detail-final-label">VAT</div>'
        f'<div class="object-detail-final-value" data-final="vat">{_money(summary["vat"])}</div>'
        '</div>'
        '<div>'
        '<div class="object-detail-final-label">Total</div>'
        f'<div class="object-detail-final-value object-detail-final-total" data-final="total">{_money(summary["total"])}</div>'
        '</div>'
        '</div>'
    )


def _footer_html(run_id: object, estimate_id: object, object_id: object) -> str:
    back_params = (
        f"screen=objects&run_id={html.escape(str(run_id or ''))}"
        f"&estimate_id={html.escape(str(estimate_id or ''))}"
    )
    approve_params = (
        f"screen=object_detail&run_id={html.escape(str(run_id or ''))}"
        f"&estimate_id={html.escape(str(estimate_id or ''))}"
        f"&object_id={html.escape(str(object_id or ''))}"
        "&od_snapshot=[]&od_approve_after=1"
    )
    return (
        '<div class="object-detail-footer-actions">'
        f'<a class="object-detail-footer-button object-detail-footer-button--secondary" href="?{back_params}" target="_self">'
        'BACK TO OBJECTS'
        '</a>'
        f'<a class="object-detail-footer-button object-detail-footer-button--primary" href="?{approve_params}" '
        'target="_self" data-object-detail-approve="true">'
        'APPROVE ESTIMATE'
        '</a>'
        '</div>'
    )


def render_object_detail_screen(company_id: str) -> None:
    """Render one object estimate detail screen from persisted estimate data."""
    apply_object_detail_css()
    estimate_id = st.session_state.get("current_estimate_id")
    object_id = st.session_state.get("current_object_id")

    if not estimate_id or not object_id:
        st.error("No object estimate selected.")
        if st.button("BACK TO OBJECTS", type="secondary"):
            st.session_state.screen = "objects"
            st.rerun()
        return

    _consume_pending_object_detail_snapshot()
    _consume_pending_object_detail_edit()
    if st.session_state.pop("object_detail_approve_after_edit", False):
        _approve_current_object_and_return(
            estimate_id=str(estimate_id),
            object_id=str(object_id),
            recalculate=False,
        )
        st.rerun()

    try:
        data = load_object_detail_data(
            estimate_id=estimate_id,
            object_id=object_id,
        )
    except Exception as exc:
        st.error(f"Could not load Object Detail: {exc}")
        if st.button("BACK TO OBJECTS", type="secondary"):
            st.session_state.screen = "objects"
            st.rerun()
        return

    st.markdown(
        '<div class="post-upload-shell object-detail-shell">'
        '<div class="object-detail-hero">'
        '<div>'
        '<h1 class="post-upload-title object-detail-title">'
        '<span>Object:</span><br>'
        f'<span>{_escape(data["name"])}</span>'
        '</h1>'
        '<div class="object-detail-info-row">'
        '<span class="object-detail-info-label">QTY:</span>'
        f'<span class="object-detail-info-value">{_quantity(data["quantity"])}</span>'
        '<span>·</span>'
        '<span class="object-detail-info-label">AI confidence:</span>'
        f'<span class="object-detail-info-value">{_escape(data["confidence"])}</span>'
        '</div>'
        '</div>'
        f'<div class="object-detail-preview-placeholder">{_escape(data["preview_label"])}</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "".join(_section_html(section) for section in data["sections"])
        + _final_html(data)
        + _footer_html(
            run_id=st.session_state.get("current_run_id"),
            estimate_id=estimate_id,
            object_id=object_id,
        ),
        unsafe_allow_html=True,
    )

    install_object_detail_input_guard(
        run_id=str(st.session_state.get("current_run_id") or ""),
        estimate_id=str(estimate_id),
        object_id=str(object_id),
    )


def _consume_pending_object_detail_edit() -> bool:
    pending = st.session_state.pop("object_detail_pending_edit", None)
    if not pending:
        return False
    estimate_id = str(pending.get("estimate_id") or "")
    object_id = str(pending.get("object_id") or "")
    apply_object_detail_line_edit(
        estimate_id=estimate_id,
        object_id=object_id,
        line_id=str(pending.get("line_id") or ""),
        field=str(pending.get("field") or ""),
        value=str(pending.get("value") or ""),
    )
    _mark_objects_estimation_dirty(estimate_id)
    return True


def _consume_pending_object_detail_snapshot() -> bool:
    pending = st.session_state.pop("object_detail_pending_snapshot", None)
    if not pending:
        return False
    estimate_id = str(pending.get("estimate_id") or "")
    object_id = str(pending.get("object_id") or "")
    try:
        edits = json.loads(str(pending.get("snapshot") or "[]"))
    except json.JSONDecodeError:
        edits = []
    st.session_state.object_detail_last_snapshot_debug = {
        "received": True,
        "edits": len(edits) if isinstance(edits, list) else 0,
    }
    apply_object_detail_snapshot(
        estimate_id=estimate_id,
        object_id=object_id,
        edits=edits if isinstance(edits, list) else [],
    )
    _mark_objects_estimation_dirty(estimate_id)
    return bool(edits)


def _approve_current_object_and_return(
    *,
    estimate_id: str,
    object_id: str,
    object_key: str | None = None,
    recalculate: bool = True,
) -> None:
    approve_object_estimate(
        estimate_id=estimate_id,
        object_id=object_id,
        recalculate=recalculate,
    )
    _mark_objects_estimation_dirty(estimate_id)
    approved_object_keys = st.session_state.setdefault("approved_object_keys", set())
    approved_object_keys.add(object_key or object_id)
    st.session_state.screen = "objects"


def _mark_objects_estimation_dirty(estimate_id: str) -> None:
    if not estimate_id:
        return
    st.session_state.setdefault("objects_estimation_cache_dirty", set()).add(estimate_id)
