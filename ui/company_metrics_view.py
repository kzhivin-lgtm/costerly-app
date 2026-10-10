from __future__ import annotations

import html


def _escape(value: object) -> str:
    return html.escape(str(value or ""))


def _amount(value: object) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _money(value: object) -> str:
    return f"₪{round(_amount(value)):,}".replace(",", "\u202f")


def _percent(value: object) -> str:
    amount = min(100.0, _amount(value))
    if amount.is_integer():
        return f"{int(amount)}%"
    return f"{amount:.2f}".rstrip("0").rstrip(".") + "%"


def table_html(
    groups: tuple,
    monthly: dict,
    vat_percent: float,
    *,
    editable: bool,
) -> str:
    """Render Overhead Expenses with the exact Object Detail table primitives."""
    headers = "".join(
        f'<div class="object-detail-table-head">{_escape(label)}</div>'
        for label in ("Overhead Expense", "Monthly cost", "VAT", "Total")
    )
    body: list[str] = []
    gross_total = 0
    for group_name, rows in groups:
        body.append(
            '<div class="object-detail-group-summary company-metrics-group-summary">'
            f'<span>{_escape(group_name)}</span><span></span><span></span><span></span>'
            '</div>'
        )
        for row_index, (field, label) in enumerate(rows):
            net = round(_amount(monthly.get(field)))
            vat_exempt = field == "arnona_facilities_cost"
            vat = 0 if vat_exempt else round(net * vat_percent / 100)
            gross = net + vat
            gross_total += gross
            editable_attrs = (
                ' role="textbox" contenteditable="true" tabindex="0" inputmode="decimal"'
                if editable
                else ""
            )
            last_class = " company-metrics-row--last" if row_index == len(rows) - 1 else ""
            vat_text = "—" if vat_exempt else _money(vat)
            body.append(
                f'<div class="object-detail-table-row company-metrics-row{last_class}" '
                f'data-metric-field="{_escape(field)}" '
                f'data-vat-exempt="{str(vat_exempt).lower()}">'
                f'<div class="object-detail-table-cell">{_escape(label)}</div>'
                '<div class="object-detail-table-cell">'
                '<div class="object-detail-cell-input object-detail-cell-input--money '
                'company-metrics-monthly-input" '
                f'data-field="{_escape(field)}"{editable_attrs}>{_money(net)}</div>'
                '</div>'
                '<div class="object-detail-table-cell">'
                f'<span data-company-metrics-vat>{vat_text}</span>'
                '</div>'
                '<div class="object-detail-table-cell">'
                '<div class="object-detail-cell-input object-detail-cell-input--money '
                'company-metrics-total-input" '
                f'data-company-metrics-total{editable_attrs}>{_money(gross)}</div>'
                '</div>'
                '</div>'
            )

    body.append(
        '<div class="object-detail-table-row company-metrics-total-summary">'
        '<div class="object-detail-table-cell">Total monthly overhead expenses</div>'
        '<div class="object-detail-table-cell"></div>'
        '<div class="object-detail-table-cell"></div>'
        '<div class="object-detail-table-cell">'
        f'<span data-company-metrics-grand-total>{_money(gross_total)}</span>'
        '</div>'
        '</div>'
    )

    return (
        '<div class="object-detail-table object-detail-table--cols-4 '
        'company-metrics-table" data-company-metrics-table '
        f'data-vat-percent="{float(vat_percent)}">'
        f'<div class="object-detail-table-head-row">{headers}</div>'
        f'{"".join(body)}'
        '</div>'
    )


PRICING_GROUPS = (
    ((
        "Project pricing",
        (
            ("delivery_percent", "Delivery", 3, "Percent of the objects sale subtotal."),
            ("installation_percent", "Installation", 10, "Percent of the objects sale subtotal."),
            ("consumables_percent", "Consumables", 5, "Percent of primary materials."),
            ("paint_consumables_percent", "Paint consumables", 10, "Percent of coating materials."),
            ("packaging_percent", "Packaging", 1, "Percent of primary materials."),
        ),
    ),),
    ((
        "Company policy",
        (
            ("management_buffer_percent", "Management buffer", 5, "Reserve applied by the overhead engine."),
            ("warranty_reserve_percent", "Warranty reserve", 5, "Reserve applied by the overhead engine."),
            ("sale_price_markup_percent", "Default sale markup", 30, "Default markup for suggested sale prices."),
            ("vat_percent", "Ma'am / VAT rate", 18, "VAT rate used for company pricing totals."),
        ),
    ),),
)


def pricing_table_html(settings: dict, *, editable: bool) -> str:
    """Render the accepted intermediate compact Pricing Cost surface."""
    editable_attrs = (
        ' role="textbox" contenteditable="true" tabindex="0" inputmode="decimal"'
        if editable else ""
    )
    body: list[str] = []
    for group_index, group in enumerate(PRICING_GROUPS):
        _group_name, fields = group[0]
        if group_index:
            body.append('<div class="company-pricing-divider" aria-hidden="true"></div>')
        for start in range(0, len(fields), 2):
            cells: list[str] = []
            for field, label, default, help_text in fields[start:start + 2]:
                cells.extend((
                    '<div class="object-detail-table-cell company-pricing-label">'
                    f'{_escape(label)}<span class="company-pricing-help" '
                    f'title="{_escape(help_text)}" aria-label="{_escape(help_text)}">?</span></div>',
                    '<div class="object-detail-table-cell"><div class="object-detail-cell-input '
                    f'company-pricing-input" data-field="{_escape(field)}"{editable_attrs}>'
                    f'{_percent(settings.get(field, default))}</div></div>',
                ))
            while len(cells) < 4:
                cells.append('<div class="object-detail-table-cell company-pricing-empty"></div>')
            body.append('<div class="object-detail-table-row company-pricing-row">' + "".join(cells) + '</div>')
    return '<div class="object-detail-table company-pricing-table" data-company-pricing-table>' + "".join(body) + '</div>'


def save_action_html(*, label: str = "SAVE OVERHEAD EXPENSES", action: str = "metrics") -> str:
    return (
        '<button class="company-metrics-save" type="button" '
        f'data-company-settings-save="{_escape(action)}" '
        f'data-company-metrics-save="{str(action == "metrics").lower()}">'
        f'{_escape(label)}</button>'
    )
