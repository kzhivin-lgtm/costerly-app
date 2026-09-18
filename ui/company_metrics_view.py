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


def table_html(
    groups: tuple,
    monthly: dict,
    vat_percent: float,
    *,
    editable: bool,
) -> str:
    """Render Company Metrics with the exact Object Detail table primitives."""
    headers = "".join(
        f'<div class="object-detail-table-head">{_escape(label)}</div>'
        for label in ("Expense", "Monthly cost", "VAT", "Total")
    )
    body: list[str] = []
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
                f'<span data-company-metrics-total>{_money(net + vat)}</span>'
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


def save_action_html() -> str:
    return (
        '<a class="company-metrics-save" href="#" '
        'data-company-metrics-save="true">SAVE METRICS</a>'
    )
