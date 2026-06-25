from __future__ import annotations

import html

import streamlit as st

from styles.object_detail import apply_object_detail_css
from use_cases.estimation import load_object_detail_data


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
    if isinstance(value, str):
        return html.escape(value)
    if isinstance(value, float) and not value.is_integer():
        return f"₪{value:g}"
    return f"₪{int(value):,}".replace(",", " ")


def _metric_html(label: str, value: object) -> str:
    """Render one compact section metric."""
    formatted = _money(value) if isinstance(value, int | float) else _escape(value)
    return (
        '<div class="object-detail-section-metric">'
        f'<div class="object-detail-section-label">{_escape(label)}</div>'
        f'<div class="object-detail-section-value">{formatted}</div>'
        '</div>'
    )


def _input_html(value: object, kind: str = "text") -> str:
    """Render a visual editable field for future calculation wiring."""
    return (
        f'<input class="object-detail-cell-input object-detail-cell-input--{kind}" '
        f'value="{_escape(value)}" />'
    )


def _row_values(section: dict[str, object], row: dict[str, object]) -> list[str]:
    """Map normalized estimate rows to visible table cells."""
    columns = section["columns"]
    if columns[0] == "Work":
        return [
            _escape(row.get("work")),
            _escape(row.get("role")),
            _input_html(row.get("hours"), "number"),
            _input_html(_money(row.get("rate")), "money"),
            _money(row.get("cost")),
        ]
    if len(columns) == 4:
        return [
            _escape(row.get("item")),
            _input_html(_money(row.get("monthly_cost")), "money"),
            _input_html(row.get("allocation"), "text"),
            _money(row.get("cost")),
        ]
    return [
        _escape(row.get("item")),
        _escape(row.get("unit")),
        _input_html(_money(row.get("unit_cost")), "money"),
        _input_html(row.get("qty"), "number"),
        _money(row.get("cost")),
    ]


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

    has_qty_summary = "Qty" in columns and "Cost" in columns
    for group, group_rows in grouped_rows.items():
        summary_cells = ['<span class="object-detail-group-title">' + _escape(group) + "</span>"]
        for column in columns[1:]:
            value = ""
            if has_qty_summary and column == "Qty":
                value = _escape(sum(row.get("qty") or 0 for row in group_rows))
            elif has_qty_summary and column == "Cost":
                value = _money(sum(row.get("cost") or 0 for row in group_rows))
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
                '<div class="object-detail-table-row">'
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
        f'<span class="object-detail-info-value">{_escape(data["quantity"])}</span>'
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
        approved_object_keys = st.session_state.setdefault("approved_object_keys", set())
        approved_object_keys.add(data["object_key"])
        st.session_state.screen = "objects"
        st.rerun()
