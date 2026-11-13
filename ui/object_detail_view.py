from __future__ import annotations

import html
import json
import math

from ui.layout import _workflow_title_html


MATERIAL_PURCHASE_COLUMNS = (
    "Material", "Required material", "Purchase unit", "Unit price", "Purchase quantity", "Total",
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
        amount = float(value)
        if not math.isfinite(amount):
            return "—"
        return f"₪{math.floor(amount + 0.5):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


def _material_quantity_text(value: object, *, unit: str = "", is_purchase: bool = False) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(amount):
        return ""
    if unit in {"m²", "m2"}:
        return f"{math.floor(amount * 10 + 0.5) / 10:.1f}"
    if unit in {"m", "m³"} or is_purchase:
        return _number_text(amount, decimals=4)
    rounded = math.floor(amount + 0.5)
    return "<1" if 0 < amount < 0.5 else str(rounded)


def _quantity(value: object) -> str:
    return _number_text(value, decimals=3) or "—"


def _number_text(value: object, *, decimals: int = 2) -> str:
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return ""
    if number == int(number):
        return str(int(number))
    return f"{number:.{decimals}f}".rstrip("0").rstrip(".")


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


def _input_html(value: object, kind: str = "text", field: str = "", line_id: str = "",
                original_value: object = None) -> str:
    """Render an editable visual field wired by the Object Detail input guard."""
    field_attr = f' data-field="{_escape(field)}"' if field else ""
    line_id_attr = f' data-line-id="{_escape(line_id)}"' if line_id else ""
    original_attr = f' data-original-value="{_escape(original_value)}"' if original_value is not None else ""
    inputmode = "text" if kind == "text" else "decimal"
    return (
        f'<div class="object-detail-cell-input object-detail-cell-input--{kind}" '
        f'role="textbox" contenteditable="true" tabindex="0" inputmode="{inputmode}"'
        f'{field_attr}{line_id_attr}{original_attr}>{_escape(value)}</div>'
    )


def _material_input_html(*, value: object, field: str, line_id: str, unit: str) -> str:
    has_unit = bool(str(unit or "").strip())
    modifier = " object-detail-material-input--required" if field == "required_material" else " object-detail-material-input--bare"
    unit_html = (
        f'<span class="object-detail-material-input-unit">{_escape(unit)}</span>'
        if has_unit else ""
    )
    display_value = _material_quantity_text(value, unit=unit, is_purchase=field == "purchase_quantity")
    return (
        f'<span class="object-detail-material-input{modifier}" data-unit="{_escape(unit) if unit else ""}">'
        + (_input_html(display_value, "number", field, line_id, original_value=value) if line_id else
           f'<span class="object-detail-cell-input object-detail-cell-input--number">{_escape(display_value)}</span>')
        + unit_html
        + "</span>"
    )


def _purchase_unit_html(value: object) -> str:
    """Keep a sheet type and its dimensions legible within a compact column."""
    text = str(value or "").strip()
    purchase_kind, separator, dimensions = text.partition(" ")
    if purchase_kind.lower() == "sheet" and separator and dimensions.strip():
        return (
            '<span class="object-detail-purchase-unit">'
            f'<span class="object-detail-purchase-unit-kind">{_escape(purchase_kind)}</span>'
            f'<span class="object-detail-purchase-unit-dimensions">{_escape(dimensions.strip())}</span>'
            "</span>"
        )
    return _escape(value)


def _source_marker(value: object) -> str:
    source = str(value or "").upper()
    return (
        f'<span class="object-detail-material-source" data-source="{_escape(source)}">{_escape(source)}</span>'
        if source in {"C", "I", "A"} else ""
    )


def _row_values(section: dict[str, object], row: dict[str, object]) -> list[str]:
    """Map normalized estimate rows to visible table cells."""
    columns = section["columns"]
    if tuple(columns) == MATERIAL_PURCHASE_COLUMNS:
        if row.get("locked"):
            percent = _number_text(row.get("policy_percent"))
            basis = "coating materials" if row.get("policy_basis") == "coatings" else "primary materials"
            return [
                _escape(row.get("item")),
                _escape(f"{percent}% of {basis}" if percent else "Formula"),
                _escape("Formula"),
                _escape("—"),
                _escape("—"),
                f'<span class="object-detail-row-cost">{_money(row.get("total"))}</span>',
            ]
        required_unit = str(row.get("required_material_unit") or "")
        required_value = row.get("required_material_value")
        purchase_unit = str(row.get("purchase_unit") or "")
        display_unit = "" if required_unit.casefold() == purchase_unit.casefold() == "piece" else required_unit
        return [
            _source_marker(row.get("price_source")) + f'<span class="object-detail-material-name">{_escape(row.get("item"))}</span>',
            _material_input_html(value=required_value, field="required_material", line_id=str(row.get("required_material_line_id") or ""), unit=display_unit),
            _purchase_unit_html(row.get("purchase_unit")),
            f'<span class="object-detail-unit-price">{_money(row.get("purchase_unit_cost"))}</span>',
            _material_input_html(value=row.get("purchase_quantity_value"), field="purchase_quantity",
                                 line_id=str(row.get("purchase_quantity_line_id") or ""), unit=""),
            f'<span class="object-detail-row-cost">{_money(row.get("total"))}</span>',
        ]
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
    if row.get("locked"):
        percent = _number_text(row.get("policy_percent"))
        return [
            _escape(row.get("item")),
            _escape(row.get("unit")),
            _escape("—"),
            _escape(f"{percent}%" if percent else ""),
            f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
        ]
    source_marker = _source_marker(row.get("price_source"))
    allocation = row.get("material_plan_allocation")
    if isinstance(allocation, dict):
        purchase = f"{_number_text(allocation.get('purchase_quantity'))} {allocation.get('purchase_unit') or 'purchase unit'}"
        return [
            _escape(row.get("item")),
            _escape("Project allocation"),
            _escape(purchase),
            _escape(_money(allocation.get("price_per_purchase_unit"))) + source_marker,
            f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
        ]
    unit_cost = _input_html(_money(row.get("unit_cost")), "money", "unit_cost") + source_marker
    return [
        _escape(row.get("item")),
        _escape(row.get("unit")),
        _input_html(_number_text(row.get("qty")), "number", "quantity"),
        unit_cost,
        f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>',
    ]


def _group_summary_value(column: str, group_rows: list[dict[str, object]]) -> str:
    if column in {"Qty", "Hours"}:
        key = "qty" if column == "Qty" else "hours"
        values = []
        for row in group_rows:
            try:
                number = float(row.get(key) or 0)
            except (TypeError, ValueError):
                number = 0
            values.append(number if math.isfinite(number) else 0)
        return _number_text(sum(values))
    if column in {"Cost", "Monthly cost"}:
        key = "monthly_cost" if column == "Monthly cost" else "cost"
        values = []
        for row in group_rows:
            try:
                number = float(row.get(key) or 0)
            except (TypeError, ValueError):
                number = 0
            values.append(number if math.isfinite(number) else 0)
        return _money(sum(values))
    return ""


def _material_preview(row: dict[str, object]) -> dict[str, object]:
    return {key: row[key] for key in (
        "total", "required_material_value", "required_material_unit", "required_material_line_id",
        "purchase_quantity_value", "purchase_quantity_line_id", "purchase_kind",
        "purchase_is_manual", "project_required", "purchase_unit_cost", "stock_coverage",
        "is_coating", "locked", "policy_percent", "policy_basis", "item",
    ) if key in row}


def material_preview_rows(data: dict[str, object]) -> list[dict[str, object]]:
    return [_material_preview(row) for section in data["sections"] if section["key"] == "material"
            for row in section["rows"]]


def _table_html(section: dict[str, object]) -> str:
    """Render a grouped cost table from normalized estimate rows."""
    columns = section["columns"]
    rows = section["rows"]
    column_count = len(columns)
    section_key = str(section.get("key") or _slug(section.get("title")))
    table_class = f"object-detail-table object-detail-table--cols-{column_count}"
    material_table = tuple(columns) == MATERIAL_PURCHASE_COLUMNS
    header_cells = []
    for column in columns:
        label = _escape(column)
        if material_table and column in {"Purchase unit", "Unit price"}:
            label = f'<span>{label.replace(" ", "<br> ", 1)}</span>'
        header_cells.append(f'<div class="object-detail-table-head">{label}</div>')
    header = "".join(header_cells)

    body_parts: list[str] = []
    if material_table:
        for row in rows:
            values = _row_values(section, row)
            preview = _material_preview(row)
            body_parts.append(
                f'<div class="object-detail-table-row" data-section="materials" data-material-preview="{_escape(json.dumps(preview))}">'
                + "".join(f'<div class="object-detail-table-cell">{value}</div>' for value in values)
                + "</div>"
            )
        return (
            f'<div class="{table_class}" data-section="{_escape(section_key)}">'
            f'<div class="object-detail-table-head-row">{header}</div>'
            f'{"".join(body_parts)}'
            '</div>'
        )
    grouped_rows: dict[object, list[dict[str, object]]] = {}
    for row in rows:
        grouped_rows.setdefault(row.get("group"), []).append(row)

    for group, group_rows in grouped_rows.items():
        summary_cells = ['<span class="object-detail-group-title">' + _escape(group) + "</span>"]
        for column in columns[1:]:
            value = _group_summary_value(column, group_rows)
            summary_cells.append(f'<span class="object-detail-group-total">{value}</span>')

        body_parts.append(
            '<details class="object-detail-group" open>'
            '<summary class="object-detail-group-summary">'
            + "".join(summary_cells)
            + "</summary>"
        )

        for row in group_rows:
            values = _row_values(section, row)
            policy_percent = row.get("policy_percent") if row.get("locked") else ""
            policy_percent_attr = html.escape(str(policy_percent or ""), quote=True)
            body_parts.append(
                '<div class="object-detail-table-row" '
                f'data-line-id="{_escape(row.get("line_id"))}" '
                f'data-section="{_escape(section_key)}" '
                f'data-policy-percent="{policy_percent_attr}">'
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
        f'<div class="object-detail-final" data-vat-percent="{_escape(summary.get("vat_percent", 18))}" '
        f'data-base-cost="{_escape(summary["excl_vat"])}">'
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


def _elements_html(rows: object) -> str:
    """Show the grouped part list using the Materials table styling."""
    if not isinstance(rows, list) or not rows:
        return ""
    body = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        body.append(
            '<div class="object-detail-table-row" data-section="elements" role="row">'
            f'<div class="object-detail-table-cell" role="cell">{_escape(row.get("label"))}</div>'
            f'<div class="object-detail-table-cell" role="cell">{_escape(row.get("size"))}</div>'
            f'<div class="object-detail-table-cell" role="cell">{_escape(_number_text(row.get("quantity")))}</div>'
            '</div>'
        )
    if not body:
        return ""
    return (
        '<details class="object-detail-elements">'
        '<summary class="object-detail-section-title">Elements</summary>'
        '<div class="object-detail-table object-detail-elements-table" role="table" aria-label="Elements">'
        '<div class="object-detail-table-head-row" role="row">'
        '<div class="object-detail-table-head" role="columnheader">Element</div>'
        '<div class="object-detail-table-head" role="columnheader">Dimensions</div>'
        '<div class="object-detail-table-head" role="columnheader">Quantity</div>'
        '</div>'
        f'{"".join(body)}</div>'
        '</details>'
    )


def _footer_html(
    run_id: object,
    estimate_id: object,
    object_id: object,
) -> str:
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
        f'<a class="object-detail-footer-button object-detail-footer-button--secondary" '
        'data-streamlit-bridge-key="object_detail_back_bridge" '
        f'href="?{back_params}" target="_self">'
        'Back to Objects'
        '</a>'
        '<button type="button" class="object-detail-footer-button object-detail-footer-button--secondary '
        'object-detail-material-save" hidden disabled>Save changes</button>'
        f'<a class="object-detail-footer-button object-detail-footer-button--primary" href="?{approve_params}" '
        'data-streamlit-bridge-key="object_detail_approve_bridge" '
        'target="_self" data-object-detail-approve="true">Approve</a>'
        '</div>'
        '<p class="object-detail-material-edit-status" role="status" aria-live="polite"></p>'
    )


def hero_heading_html(data: dict[str, object]) -> str:
    """Render the Object Detail title and object facts without its preview."""
    return (
        '<div class="post-upload-shell object-detail-shell">'
        '<h1 class="post-upload-title object-detail-title workflow-title">'
        f'{_workflow_title_html("Object:")}'
        '<br>'
        f'<span class="object-detail-object-name">{_escape(data["name"])}</span>'
        '</h1>'
        '<div class="object-detail-info-row" '
        f'data-run-id="{_escape(data.get("run_id") or "")}" '
        f'data-estimate-id="{_escape(data.get("estimate_id") or "")}" '
        f'data-object-key="{_escape(data.get("object_key") or "")}">'
        '<span class="object-detail-info-label">QTY:</span>'
        '<span class="object-detail-info-value object-detail-quantity-input" '
        'data-object-quantity-input="true" contenteditable="true" inputmode="decimal" '
        f'tabindex="0">{_escape(data["quantity"])}</span>'
        '<span>·</span>'
        '<span class="object-detail-info-label">AI confidence:</span>'
        f'<span class="object-detail-info-value">{_escape(data["confidence"])}</span>'
        '</div>'
        '</div>'
    )


def hero_label_html() -> str:
    """Render the stable first-line Object label for the shared header row."""
    return (
        '<div class="post-upload-shell object-detail-shell">'
        '<h1 class="post-upload-title object-detail-title workflow-title">'
        f'{_workflow_title_html("Object:")}'
        '</h1>'
        '</div>'
    )


def hero_details_html(data: dict[str, object]) -> str:
    """Render the object-specific heading details below the shared header row."""
    return (
        '<div class="post-upload-shell object-detail-details">'
        '<h1 class="post-upload-title object-detail-title object-detail-title--name">'
        f'<span class="object-detail-object-name">{_escape(data["name"])}</span>'
        '</h1>'
        '<div class="object-detail-info-row" '
        f'data-run-id="{_escape(data.get("run_id") or "")}" '
        f'data-estimate-id="{_escape(data.get("estimate_id") or "")}" '
        f'data-object-key="{_escape(data.get("object_key") or "")}">'
        '<span class="object-detail-info-label">QTY:</span>'
        '<span class="object-detail-info-value object-detail-quantity-input" '
        'data-object-quantity-input="true" contenteditable="true" inputmode="decimal" '
        f'tabindex="0">{_escape(_quantity(data["quantity"]))}</span>'
        '<span>·</span>'
        '<span class="object-detail-info-label">AI confidence:</span>'
        f'<span class="object-detail-info-value">{_escape(data["confidence"])}</span>'
        '</div>'
        '</div>'
    )


def hero_preview_html(data: dict[str, object]) -> str:
    """Render the Object Detail source preview for the header row."""
    preview_url = str(data.get("preview_url") or "")
    return (
        '<div class="object-detail-preview-placeholder">'
        f'<img class="object-detail-preview-image" src="{_escape(preview_url)}" alt="Source preview">'
        '</div>'
        if preview_url
        else f'<div class="object-detail-preview-placeholder">{_escape(data["preview_label"])}</div>'
    )


def hero_html(data: dict[str, object]) -> str:
    """Render the legacy combined Object Detail hero/header block."""
    return (
        '<div class="post-upload-shell object-detail-shell">'
        '<div class="object-detail-hero">'
        f'<div>{hero_heading_html(data)}</div>'
        f'{hero_preview_html(data)}'
        '</div>'
        '</div>'
    )


def detail_html(
    data: dict[str, object],
    *,
    run_id: object,
    estimate_id: object,
    object_id: object,
) -> str:
    """Render Object Detail sections, totals, and footer actions."""
    return (
        "".join(_section_html(section) for section in data["sections"])
        + _elements_html(data.get("elements"))
        + _final_html(data)
        + _footer_html(
            run_id=run_id,
            estimate_id=estimate_id,
            object_id=object_id,
        )
    )
