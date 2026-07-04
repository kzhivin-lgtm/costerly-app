from __future__ import annotations

import html

import streamlit as st

from styles.object_detail import apply_object_detail_css
from ui.js_guards import install_object_detail_input_guard
from use_cases.estimation import (
    apply_object_detail_line_edit,
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


def _metric_html(label: str, value: object) -> str:
    """Render one compact section metric."""
    formatted = _money(value) if isinstance(value, int | float) else _escape(value)
    return (
        '<div class="object-detail-section-metric">'
        f'<div class="object-detail-section-label">{_escape(label)}</div>'
        f'<div class="object-detail-section-value">{formatted}</div>'
        '</div>'
    )


def _input_html(value: object, kind: str = "text", field: str = "") -> str:
    """Render a visual editable field for future calculation wiring."""
    field_attr = f' data-field="{_escape(field)}"' if field else ""
    return (
        f'<input class="object-detail-cell-input object-detail-cell-input--{kind}" '
        f'value="{_escape(value)}"{field_attr} />'
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
            _money(row.get("cost")),
        ]
    if len(columns) == 4:
        monthly_cost_display = row.get("monthly_cost_display")
        monthly_cost_value = (
            _escape(monthly_cost_display)
            if monthly_cost_display
            else _money(row.get("monthly_cost"))
        )
        return [
            _escape(row.get("item")),
            _input_html(monthly_cost_value, "money", "monthly_cost"),
            _input_html(row.get("allocation"), "text", "allocation_basis"),
            _money(row.get("cost")),
        ]
    return [
        _escape(row.get("item")),
        _escape(row.get("unit")),
        _input_html(_money(row.get("unit_cost")), "money", "unit_cost"),
        _input_html(_number_text(row.get("qty")), "number", "quantity"),
        _money(row.get("cost")),
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
                f'data-line-id="{_escape(row.get("line_id"))}">'
                + "".join(f'<div class="object-detail-table-cell">{value}</div>' for value in values)
                + "</div>"
            )
        body_parts.append("</details>")

    return (
        f'<div class="{table_class}">'
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
        f'<section class="object-detail-section object-detail-section--cols-{column_count}">'
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
        f'<div class="object-detail-final-value">{_money(summary["excl_vat"])}</div>'
        '</div>'
        '<div>'
        '<div class="object-detail-final-label">VAT</div>'
        f'<div class="object-detail-final-value">{_money(summary["vat"])}</div>'
        '</div>'
        '<div>'
        '<div class="object-detail-final-label">Total</div>'
        f'<div class="object-detail-final-value object-detail-final-total">{_money(summary["total"])}</div>'
        '</div>'
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

    _consume_pending_object_detail_edit()

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
        + _final_html(data),
        unsafe_allow_html=True,
    )

    col_back, col_approve = st.columns(2, gap="small")
    if col_back.button("BACK TO OBJECTS", type="secondary", use_container_width=True):
        st.session_state.screen = "objects"
        st.rerun()

    if col_approve.button("APPROVE ESTIMATE", type="primary", use_container_width=True):
        approve_object_estimate(
            estimate_id=str(estimate_id),
            object_id=str(object_id),
        )
        approved_object_keys = st.session_state.setdefault("approved_object_keys", set())
        approved_object_keys.add(data["object_key"])
        st.session_state.screen = "objects"
        st.rerun()

    install_object_detail_input_guard(
        run_id=str(st.session_state.get("current_run_id") or ""),
        estimate_id=str(estimate_id),
        object_id=str(object_id),
    )


def _consume_pending_object_detail_edit() -> None:
    pending = st.session_state.pop("object_detail_pending_edit", None)
    if not pending:
        return
    apply_object_detail_line_edit(
        estimate_id=str(pending.get("estimate_id") or ""),
        object_id=str(pending.get("object_id") or ""),
        line_id=str(pending.get("line_id") or ""),
        field=str(pending.get("field") or ""),
        value=str(pending.get("value") or ""),
    )
