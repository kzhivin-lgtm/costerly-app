"""Render the shop assembly total and its breakdown in Elements."""

from html import escape
from ui.object_detail_view import _money


_OPERATIONS = {
    "kit_handling": "Stage parts and hardware", "carcass": "Assemble carcass", "back": "Fit back",
    "fixed_panel_or_shelf": "Fit fixed panel or shelf", "drawer_box": "Assemble drawer box",
    "drawer_runner_installation": "Install drawer slide pair", "drawer_runner_adjustment": "Adjust drawer",
    "drawer_front": "Fit drawer front", "shelf_runner_installation": "Install pull-out shelf and slides",
    "shelf_runner_check": "Check shelf travel", "hinge_and_plate": "Install hinge and plate",
    "door_fitting": "Hang and align door", "lift_kit": "Install lift kit",
    "lift_front_fitting": "Fit lift-up front", "push_latch": "Install push latch",
    "bench_setup": "Set up workbench",
}


def _caption(text):
    return f'<p class="object-detail-cnc-caption">{escape(text)}</p>'


def _summary_row(block, label, *, total=False, quantity=1, payroll_share=None):
    from decimal import Decimal, ROUND_HALF_UP
    multiplier = Decimal(str(quantity))
    pay = ((Decimal(str(block['planned_minutes'])) * multiplier * 50 / 60)
           if payroll_share is not None else Decimal(str(block['base_labor_ils'])) * multiplier
           ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    values = [label, f'{block["active_minutes"] * multiplier:g}', f'{block["planned_minutes"] * multiplier:.2f}', _money(pay)]
    if payroll_share is not None:
        taxes = (pay * payroll_share).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        values += [_money(taxes), _money(pay + taxes)]
    if not total and not block["operations"]:
        values = [label] + ['—'] * (len(values) - 1)
    css = " object-detail-assembly-total" if total else ""
    return (
        f'<div class="object-detail-table-row{css}" role="row">'
        + "".join(f'<div class="object-detail-table-cell" role="cell">{escape(value)}</div>' for value in values)
        + '</div>'
    )


def _details(block, *, quantity=1):
    lines = [
        f'<li>{escape(_OPERATIONS[op["operation"]])} · {op["quantity"] * quantity:g} × {op["minutes_per_unit"]} min '
        f'= {op["active_minutes"] * quantity:g} min</li>' for op in block["operations"]
    ]
    lines.extend(f'<li>{escape(issue)}</li>' for issue in block["issues"])
    if not lines:
        return ""
    return (
        '<details class="object-detail-table object-detail-cnc-breakdown">'
        f'<summary>{escape(block["block_id"])} · Assembly details</summary>'
        f'<ul>{"".join(lines)}</ul></details>'
    )


def block_assembly_html(result=None, *, message="Block Assembly is unavailable."):
    if result is None or not result["blocks"]:
        body = _caption(message if result is None else "No assembly blocks in Parts Check.")
    else:
        hours = result["planned_minutes"] / 60
        label = "Subtotal" if _partial(result) else "Base labor"
        body = (
            '<div class="object-detail-assembly-metrics">'
            f'<span>{hours:.2f} h</span>'
            f'<span>{label} · ₪{result["base_labor_ils"]:,.2f}</span></div>'
        )
    return (
        '<section class="object-detail-elements-section" aria-label="Block Assembly">'
        f'<div class="object-detail-section-title">Block Assembly</div>{body}</section>'
    )


def _partial(result):
    return bool(result["common_roles_for_review"] or any(block["issues"] for block in result["blocks"]))


def assembly_breakdown_html(result, *, quantity=1, payroll_share=None, inline=False):
    if not result or not result["blocks"]:
        return ""
    headers = "".join(
        f'<div class="object-detail-table-head" role="columnheader">{label}</div>'
        for label in (("Block", "Active min", "Planned min", "Labor pay", "Taxes & social", "Total")
                      if payroll_share is not None else ("Block", "Active min", "Planned min", "Base labor"))
    )
    rows = "".join(
        _summary_row(block, block["block_id"] + (" · review" if block["issues"] else ""), quantity=quantity, payroll_share=payroll_share)
        for block in result["blocks"]
    )
    table = (
        '<div class="object-detail-table object-detail-assembly-table" role="table" aria-label="Block Assembly estimate">'
        f'<div class="object-detail-table-head-row" role="row">{headers}</div>{rows}'
        + _summary_row(result, "Subtotal" if _partial(result) else "Total", total=True, quantity=quantity, payroll_share=payroll_share) + '</div>'
    )
    captions = (_caption(f'For {quantity:g} finished items') if quantity != 1 else '') if payroll_share is not None else _caption(
        f'Per finished item · ₪{result["hourly_base_ils"]:g}/h base wage · payroll costs excluded')
    details = "".join(_details(block, quantity=quantity) for block in result["blocks"])
    if inline:
        return captions + table + details
    return (
        '<details class="object-detail-element-group">'
        f'<summary>Assembly breakdown</summary>{captions}{table}{details}</details>'
    )
