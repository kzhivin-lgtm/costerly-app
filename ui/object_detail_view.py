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


def _money(value: object, *, cents: bool = False) -> str:
    """Format monetary values for object detail tables."""
    if value is None or value == "":
        return "—"
    if isinstance(value, float) and value != value:
        return "—"
    try:
        amount = float(value)
        if not math.isfinite(amount):
            return "—"
        if cents:
            return f"₪{amount:,.2f}".replace(",", "\u202f")
        return f"₪{math.floor(amount + 0.5):,}".replace(",", "\u202f")
    except (TypeError, ValueError):
        return _escape(value)


_DISCRETE_MATERIAL_UNITS = {
    "ea", "piece", "pcs", "set", "pair", "pack", "sheet", "roll", "bar", "stock", "dozen",
}


def _material_quantity_decimals(unit: str, *, purchase_kind: str = "") -> int:
    if purchase_kind:
        return 0 if purchase_kind in {"sheet", "linear_stock", "piece"} else 1
    normalized = str(unit or "").lower().strip()
    return 0 if not normalized or normalized.split()[0] in _DISCRETE_MATERIAL_UNITS else 1


def _material_quantity_text(value: object, *, decimals: int) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(amount):
        return ""
    factor = 10 ** decimals
    rounded = math.floor(amount * factor + 0.5) / factor
    return f"{rounded:.{decimals}f}"


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


def _material_input_html(*, value: object, field: str, line_id: str, unit: str, decimals: int) -> str:
    has_unit = bool(str(unit or "").strip())
    modifier = " object-detail-material-input--required" if field == "required_material" else " object-detail-material-input--bare"
    unit_html = (
        f'<span class="object-detail-material-input-unit">{_escape(unit)}</span>'
        if has_unit else ""
    )
    display_value = _material_quantity_text(value, decimals=decimals)
    return (
        f'<span class="object-detail-material-input{modifier}" data-unit="{_escape(unit) if unit else ""}" '
        f'data-quantity-decimals="{decimals}">'
        + (_input_html(display_value, "number", field, line_id, original_value=value) if line_id else
           f'<span class="object-detail-cell-input object-detail-cell-input--number">{_escape(display_value)}</span>')
        + unit_html
        + "</span>"
    )


def _purchase_unit_html(value: object) -> str:
    """Keep a sheet type and its dimensions legible within a compact column."""
    text = str(value or "").strip()
    purchase_kind, separator, dimensions = text.partition(" ")
    if purchase_kind.lower() in {"sheet", "roll", "bar"} and separator and dimensions.strip():
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
    if section.get("readonly") and section.get("column_fields"):
        return [_escape(row.get(field)) for field in section["column_fields"]]
    if tuple(columns) == MATERIAL_PURCHASE_COLUMNS:
        if row.get("locked"):
            percent = _number_text(row.get("policy_percent"))
            basis = "coating materials" if row.get("policy_basis") == "coatings" else "primary materials"
            return [
                _escape(row.get("item")),
                _escape(row.get('policy_description') or (f"{percent}% of {basis}" if percent else "Formula")),
                _escape("Formula"),
                _escape("—"),
                _escape("—"),
                f'<span class="object-detail-row-cost">{_money(row.get("total"))}</span>',
            ]
        required_unit = str(row.get("required_material_unit") or "")
        required_value = row.get("required_material_value")
        purchase_unit = str(row.get("purchase_unit") or "")
        display_unit = "" if required_unit == purchase_unit and required_unit in {"piece", "set"} else required_unit
        name = row.get("item")
        reference_name = row.get("material_reference_name")
        title = f' title="{_escape(reference_name)}"' if reference_name and reference_name != name else ""
        if row.get("unit_price_display") == "Variable":
            pieces = (
                f'<span data-finished-quantity="pieces">{_escape(_quantity(required_value))}'
                f'&nbsp;{"piece" if required_value == 1 else "pieces"}</span>'
                if required_value is not None else "—"
            )
            return [
                _source_marker(row.get("price_source")) + f'<span class="object-detail-material-name">{_escape(name)}</span>',
                pieces,
                _escape(purchase_unit), '<span class="object-detail-unit-price">Variable</span>',
                f'<span data-finished-quantity="sets">{_escape(_quantity(row.get("purchase_quantity_value")))}</span>',
                f'<span class="object-detail-row-cost">{_money(row.get("total"))}</span>',
            ]
        return [
            _source_marker(row.get("price_source"))
            + f'<span class="object-detail-material-name"{title}>{_escape(name)}</span>',
            _material_input_html(value=required_value, field="required_material", line_id=str(row.get("required_material_line_id") or ""), unit=display_unit,
                                 decimals=_material_quantity_decimals(required_unit)),
            _purchase_unit_html(row.get("purchase_unit")),
            f'<span class="object-detail-unit-price">{_money(row.get("purchase_unit_cost"))}</span>',
            _material_input_html(value=row.get("purchase_quantity_value"), field="purchase_quantity",
                                 line_id=str(row.get("purchase_quantity_line_id") or ""), unit="",
                                 decimals=_material_quantity_decimals(row.get("purchase_quantity_unit") or purchase_unit,
                                                                      purchase_kind=row.get("purchase_kind") or "")),
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
        if section.get("readonly"):
            return [_escape(row.get("item")), monthly_cost_value,
                    _escape(row.get("allocation")),
                    f'<span class="object-detail-row-cost">{_money(row.get("cost"))}</span>']
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
    reserves = bool(group_rows) and all(row.get("reserve_percent") not in (None, "") for row in group_rows)
    if column == "Allocation":
        if reserves:
            return "Formula"
        values = list(dict.fromkeys(str(row.get("allocation") or "") for row in group_rows))
        return _escape(values[0]) if len(values) == 1 else "—"
    if column == "Monthly cost" and reserves:
        return "—"
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
        "purchase_is_manual", "prior_required", "prior_purchase_quantity", "purchase_unit_cost", "stock_coverage",
        "stock_cuts", "stock_kerf_mm",
        "unit_price_display", "pieces_per_set",
        "is_coating", "locked", "policy_percent", "policy_basis", "policy_description", "coating_recipe", "policy_rate", "item",
    ) if key in row}


def material_preview_rows(data: dict[str, object]) -> list[dict[str, object]]:
    return [_material_preview(row) for section in data["sections"] if section["key"] == "material"
            for row in section["rows"]]


def front_panels_html(groups) -> str:
    controls = []
    for group in groups or ():
        label = "Front panels"
        if len(groups) > 1:
            label += f" · {group.get('thickness_mm') or '—'} mm"
        options = group["options"] if group.get("source_choice") else [
            {"value": "source", "label": group["source_name"]}, *group["options"],
        ]
        option_html = "".join(
            f'<option value="{_escape(option["value"])}"'
            + (' selected' if option["value"] == group["choice"] else '')
            + f'>{_escape(option["label"])}</option>' for option in options
        )
        controls.append(
            '<label class="object-detail-front-panels-control">'
            f'<span>{_escape(label)}</span>'
            f'<select aria-label="{_escape(label)}" data-front-panels '
            f'data-field="front_material" data-line-id="__front_panels__:{_escape(group["id"])}" '
            f'data-original-value="{_escape(group["choice"])}">{option_html}</select></label>'
        )
    return '<div class="object-detail-front-panels">' + ''.join(controls) + '</div>' if controls else ''


def material_rows_html(rows) -> str:
    return table_rows_html({"columns": MATERIAL_PURCHASE_COLUMNS, "rows": rows})


def table_rows_html(section) -> str:
    """Shared server-authored rows for initial tables and their edit receipts."""
    material = tuple(section["columns"]) == MATERIAL_PURCHASE_COLUMNS
    def attributes(row):
        if material:
            return 'data-section="materials" ' + f'data-material-preview="{_escape(json.dumps(_material_preview(row)))}"'
        return f'data-section="{_escape(section["key"])}" data-row-key="{_escape(row["row_key"])}"'
    return ''.join(
        f'<div class="object-detail-table-row" {attributes(row)}>'
        + ''.join(f'<div class="object-detail-table-cell">{value}</div>' for value in _row_values(section, row))
        + '</div>' for row in section["rows"]
    )


def _table_html(section: dict[str, object], *, collapse_title: str | None = None) -> str:
    """Render a grouped cost table from normalized estimate rows."""
    columns = section["columns"]
    rows = section["rows"]
    column_count = len(columns)
    section_key = str(section.get("key") or _slug(section.get("title")))
    table_class = f"object-detail-table object-detail-table--cols-{column_count}"
    material_table = tuple(columns) == MATERIAL_PURCHASE_COLUMNS
    header_cells = []
    known_totals = [float(row['total']) for row in rows
                    if isinstance(row.get('total'), (int, float)) and math.isfinite(row['total'])]
    subtotal = sum(known_totals) if known_totals or not rows else None
    if section_key == 'overhead':
        subtotal = section['metrics'][0][1]
    for index, column in enumerate(columns):
        label = _escape(column)
        if collapse_title and index == 0:
            label = ''
        if material_table and column in {"Purchase unit", "Unit price"}:
            label = f'<span>{label.replace(" ", "<br> ", 1)}</span>'
        header_cells.append(f'<div class="object-detail-table-head">{label}</div>')
    header = "".join(header_cells)

    body_parts: list[str] = []
    if material_table or section.get("flat"):
        body_parts.append(table_rows_html(section))
        if collapse_title:
            return (
                f'<details class="{table_class} object-detail-cost-band object-detail-materials-band" '
                f'data-section="{_escape(section_key)}">'
                '<summary class="object-detail-table-head-row object-detail-cost-summary object-detail-band-summary">'
                f'<div class="object-detail-table-head object-detail-cost-title">{_escape(collapse_title)}</div>'
                '<div class="object-detail-table-head object-detail-cost-total">'
                f'<span class="object-detail-cost-value" data-material-section-total>{_money(subtotal)}</span></div></summary>'
                f'<div class="object-detail-cost-body">{front_panels_html(section.get("front_panels"))}'
                f'<div class="object-detail-table-head-row">{header}</div>'
                f'{"".join(body_parts)}</div></details>'
            )
        reference_attr = f' data-reference-table="{_escape(section_key)}"' if section.get("flat") else ''
        return (
            f'<div class="{table_class}" data-section="{_escape(section_key)}"{reference_attr}>'
            f'<div class="object-detail-table-head-row">{header}</div>'
            f'{"".join(body_parts)}'
            '</div>'
        )
    if collapse_title:
        body_parts.append(f'<div class="object-detail-table-head-row object-detail-overhead-column-headings">{header}</div>')
    grouped_rows: dict[object, list[dict[str, object]]] = {}
    for row in rows:
        grouped_rows.setdefault(row.get("group"), []).append(row)

    for group, group_rows in grouped_rows.items():
        summary_cells = ['<span class="object-detail-group-title">' + _escape(group) + "</span>"]
        for column in columns[1:]:
            value = _group_summary_value(column, group_rows)
            group_column = {'Monthly cost': 'monthly', 'Allocation': 'allocation', 'Cost': 'cost'}.get(column, '')
            summary_cells.append(f'<span class="object-detail-group-total" data-overhead-group-column="{group_column}">{value}</span>')

        body_parts.append(
            '<details class="object-detail-group">'
            '<summary class="object-detail-group-summary">'
            + "".join(summary_cells)
            + "</summary>"
        )
        for row in group_rows:
            values = _row_values(section, row)
            policy_percent = row.get("policy_percent") if row.get("locked") else ""
            policy_percent_attr = html.escape(str(policy_percent or ""), quote=True)
            overhead_attrs = (
                f' data-overhead-monthly="{html.escape(str(row.get("monthly_amount", "")), quote=True)}"'
                f' data-overhead-percent="{html.escape(str(row.get("reserve_percent", "")), quote=True)}"'
                if section_key == "overhead" else ""
            )
            body_parts.append(
                '<div class="object-detail-table-row" '
                f'data-line-id="{_escape(row.get("line_id"))}" '
                f'data-section="{_escape(section_key)}" '
                f'data-policy-percent="{policy_percent_attr}"{overhead_attrs}>'
                + "".join(f'<div class="object-detail-table-cell">{value}</div>' for value in values)
                + "</div>"
            )
        body_parts.append("</details>")

    body = "".join(body_parts)
    if collapse_title:
        return (
            f'<details class="{table_class} object-detail-cost-band object-detail-overhead-band" '
            f'data-section="{_escape(section_key)}">'
            '<summary class="object-detail-table-head-row object-detail-cost-summary object-detail-band-summary">'
            f'<div class="object-detail-table-head object-detail-cost-title">{_escape(collapse_title)}</div>'
            '<div class="object-detail-table-head object-detail-cost-total object-detail-section-metric" data-metric="cost">'
            f'<span class="object-detail-cost-value object-detail-section-value">{_money(subtotal)}</span></div></summary>'
            f'<div class="object-detail-cost-body">{body}</div></details>'
        )
    return (
        f'<div class="{table_class}" data-section="{_escape(section_key)}">'
        f'<div class="object-detail-table-head-row">{header}</div>'
        f'{body}'
        '</div>'
    )


def coating_table_section(audit) -> dict:
    return {"key": "coating", "readonly": True, "flat": True,
            "columns": ("Finish", "Coated area", "Time norm", "Hourly rate"),
            "column_fields": ("finish", "area", "norm", "rate"),
            "rows": [{"row_key": batch["finish"], "finish": batch["label"],
                      "area": f'{_number_text(round(batch["area_m2"], 2))} m²',
                      "norm": f'{_number_text(batch["minutes_per_m2"])} min/m²',
                      "rate": f'{_money((audit or {}).get("hourly_rate", 100))}/h'}
                     for batch in (audit or {}).get("batches", [])]}


def work_detail_rows_html(rows) -> str:
    return ''.join(f'<li data-row-key="{_escape(row["row_key"])}">{_escape(row["text"])}</li>' for row in rows)


def work_details_html(rows, *, key=None) -> str:
    if not rows and key is None:
        return ''
    attr = f' data-reference-list="{_escape(key)}"' if key else ''
    return f'<ul{attr}>' + work_detail_rows_html(rows) + '</ul>'


def coating_detail_rows(audit):
    return [{"row_key": row['row_key'], "text":
             f'{row["finish"]} · {row["area"]} · {row["norm"]} · {row["rate"]}'
             + (' · Batch preparation included' if batch.get('batch_m2') else '')}
            for row, batch in zip(coating_table_section(audit)['rows'], (audit or {}).get('batches', []))]


def coating_details_html(audit) -> str:
    return work_details_html(coating_detail_rows(audit), key='coating')


def _section_html(section: dict[str, object]) -> str:
    """Render one cost section with metrics and a grouped table."""
    if tuple(section['columns']) == MATERIAL_PURCHASE_COLUMNS:
        return (
            '<section class="object-detail-section object-detail-section--cols-6" data-section="material">'
            + _table_html(section, collapse_title=str(section['title'])) + '</section>'
        )
    if section.get('key') == 'overhead':
        return (
            '<section class="object-detail-section object-detail-section--cols-4" data-section="overhead">'
            + _table_html(section, collapse_title=str(section['title']))
            + '<div hidden>' + ''.join(_metric_html(label, value) for label, value in section['metrics'][1:])
            + '</div></section>'
        )
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
    quantity = float(data.get("quantity") or 1)
    net = summary.get("batch_excl_vat")
    if net is None and summary["excl_vat"] is not None:
        net = round(float(summary["excl_vat"]) * quantity, 2)
    vat = None if net is None else round(float(net) * float(summary.get("vat_percent", 18)) / 100, 2)
    total = None if net is None else round(float(net) + vat, 2)
    return (
        f'<div class="object-detail-final" data-vat-percent="{_escape(summary.get("vat_percent", 18))}" '
        f'data-full-cost="{str(data.get("cost_policy") == "object_costs_v3_1").lower()}" '
        f'data-base-cost="{_escape(summary["excl_vat"])}" data-base-batch-cost="{_escape(net)}">'
        '<div class="object-detail-final-title">Self Cost (SC)</div>'
        '<div class="object-detail-final-metric">'
        '<div class="object-detail-final-label">Excl. VAT</div>'
        f'<div class="object-detail-final-value" data-final="excl_vat">{_money(net)}</div>'
        '</div>'
        '<div class="object-detail-final-metric">'
        f'<div class="object-detail-final-label">VAT {_escape(_number_text(summary.get("vat_percent", 18)))}%</div>'
        f'<div class="object-detail-final-value" data-final="vat">{_money(vat)}</div>'
        '</div>'
        '<div class="object-detail-final-metric">'
        '<div class="object-detail-final-label">Total</div>'
        f'<div class="object-detail-final-value object-detail-final-total" data-final="total">{_money(total)}</div>'
        '</div>'
        '</div>'
    )


def overhead_section_html(result: dict[str, object]) -> str:
    """Restore the existing Overhead table, with Profile-owned inputs."""
    rows = []
    for line in result.get("lines", []):
        raw = line.get("raw_agent_json") or {}
        percent = raw.get("percent")
        rows.append({
            "group": line["group_name"], "line_id": line["line_id"],
            "item": line["item_name"], "monthly_cost": line["monthly_cost"],
            "monthly_cost_display": f"{_number_text(percent)}%" if percent is not None else None,
            "allocation": line["allocation_basis"], "cost": line["cost"],
            "monthly_amount": line["monthly_cost"] if percent is None else "",
            "reserve_percent": percent if percent is not None else "",
        })
    messages = {
        "loading": "Preparing Overhead…", "pending_labor": "Waiting for Labor hours",
        "missing_capacity": "Company production capacity is not configured",
        "invalid_basis": "Overhead needs valid labor and material amounts",
        "read_failed": "Overhead could not be loaded. Reopen this object to retry",
    }
    ready = result.get("status") == "ready"
    section = {
        "key": "overhead", "title": "Overhead", "readonly": True,
        "columns": ["Group", "Monthly cost", "Allocation", "Cost"], "rows": rows,
        "metrics": [("Cost", result.get("cost") if ready else "—"),
                    ("VAT", result.get("vat") if ready else "—"),
                    ("Total", result.get("total") if ready else "—")],
    }
    message = messages.get(result.get("status"))
    return (
        f'<div data-overhead-summary data-overhead-ready="{str(ready).lower()}"'
        f' data-overhead-status="{_escape(result.get("status", "loading"))}"'
        f' data-overhead-object-id="{_escape(result.get("object_id", ""))}"'
        f' data-overhead-estimate-id="{_escape(result.get("estimate_id", ""))}"'
        f' data-overhead-run-id="{_escape(result.get("run_id", ""))}"'
        f' data-overhead-capacity="{_escape(result.get("capacity_hours", ""))}"'
        f' data-overhead-labor-hours="{_escape(result.get("labor_hours", ""))}"'
        f' data-overhead-material-cost="{_escape(result.get("material_cost", ""))}"'
        f' data-overhead-vat="{_escape(result.get("vat_percent", 18))}">'
        + _section_html(section)
        + (f'<p class="object-detail-cnc-caption">{_escape(message)}</p>' if message else '') + '</div>'
    )


def _elements_table(rows, label, *, priced=False):
    if not rows:
        return '<p class="object-detail-elements-empty">No parts listed.</p>'
    body = []
    for row in rows:
        name = _escape(row.get("label"))
        size = _escape(row.get("size"))
        if "processing" in row:
            name = (f'<span class="object-detail-element-spec"><span>{name}</span>'
                    f'<small>{_escape(row.get("processing"))}</small></span>')
            thickness = _number_text(row.get("thickness_mm"))
            thickness_label = f"{thickness} mm" if thickness else "—"
            if thickness and row.get("thickness_estimated"):
                thickness_label += " (assumed)"
            size = (f'<span class="object-detail-element-spec"><span>{size}</span>'
                    f'<small>Thickness: {_escape(thickness_label)}</small></span>')
        cells = [name, size, _escape(_quantity(row.get("quantity")))]
        if priced:
            cells.extend(_money(row.get(key), cents=True) for key in ("unit_price", "total"))
        body.append(
            '<div class="object-detail-table-row" data-section="elements" role="row">'
            + "".join(f'<div class="object-detail-table-cell" role="cell">{cell}</div>' for cell in cells)
            + '</div>'
        )
    classes = "object-detail-table object-detail-elements-table" + (" object-detail-elements-table--priced" if priced else "")
    columns = ["Element", "Dimensions", "Quantity"] + (["Unit price", "Total"] if priced else [])
    headers = "".join(f'<div class="object-detail-table-head" role="columnheader">{column}</div>' for column in columns)
    return (
        f'<div class="{classes}" role="table" aria-label="{_escape(label)}">'
        f'<div class="object-detail-table-head-row" role="row">{headers}</div>'
        f'{"".join(body)}</div>'
    )


def _elements_html(groups: object, *, revision: object = None, object_id: object = None, assembly_details: str = "") -> str:
    """Show the part tables inside independent Elements and block disclosures."""
    if not isinstance(groups, list):
        groups = []
    if not groups and not revision and not assembly_details:
        return ""
    sections = []
    for group in groups:
        label = group["label"]
        table = _elements_table(group["rows"], label or "Elements", priced=group.get("priced", False))
        if label:
            sections.append(
                '<details class="object-detail-element-group">'
                '<summary class="object-detail-disclosure-summary">'
                f'<span class="object-detail-disclosure-title">{_escape(label)}</span></summary>{table}</details>'
            )
        else:
            sections.append(table)
    controls = (
        f'<div class="object-detail-overlay-actions" data-overlay-revision="{_escape(revision)}" '
        f'data-overlay-object="{_escape(object_id)}">'
        + "".join(f'<a class="object-detail-overlay-button" data-overlay-layer="{layer}" '
                  'role="link" aria-disabled="true" target="_blank" rel="noopener noreferrer" '
                  f'title="Preparing {layer.title()} PDF">{layer.title()}</a>'
                  for layer in ("front", "block"))
        + '</div>'
    ) if revision else ""
    return (
        '<div class="object-detail-elements-section">'
        '<details class="object-detail-elements">'
        '<summary class="object-detail-section-title object-detail-disclosure-summary">'
        '<span class="object-detail-disclosure-title">Elements</span></summary>'
        f'<div class="object-detail-element-groups">{"".join(sections)}{assembly_details}</div>'
        f'</details>{controls}</div>'
    )


def _footer_html(
    run_id: object,
    estimate_id: object,
    object_id: object,
    approved: bool = False,
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
        'Back to Project'
        '</a>'
        '<button type="button" class="object-detail-footer-button object-detail-footer-button--secondary '
        'object-detail-material-save" disabled>Save changes</button>'
        f'<a class="object-detail-footer-button object-detail-footer-button--primary'
        f'{" object-detail-approved" if approved else ""}" href="?{approve_params}" '
        'data-streamlit-bridge-key="object_detail_approve_bridge" '
        f'target="_self" data-object-detail-approve="true" data-approved="{str(approved).lower()}" '
        + ('aria-disabled="true"' if approved else "") + f'>{"APPROVED" if approved else "APPROVE"}</a>'
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


def detail_sections_html(data: dict[str, object]) -> str:
    return "".join(_section_html(section) for section in data["sections"])


def detail_elements_html(groups: object, *, revision: object, object_id: object, assembly_details: str = "") -> str:
    return _elements_html(groups, revision=revision, object_id=object_id, assembly_details=assembly_details)


def detail_summary_html(
    data: dict[str, object],
    *,
    run_id: object,
    estimate_id: object,
    object_id: object,
) -> str:
    """Render Object Detail totals and footer actions."""
    return (
        '<div class="object-detail-page-end">' + _final_html(data)
        + _footer_html(
            run_id=run_id,
            estimate_id=estimate_id,
            object_id=object_id,
            approved=bool(data.get("approved")),
        ) + "</div>"
    )
