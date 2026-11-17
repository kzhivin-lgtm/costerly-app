"""Render the shop assembly estimate alongside Sheet Processing."""

from html import escape


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


def _section(body):
    return (
        '<details class="object-detail-elements object-detail-elements-section">'
        f'<summary class="object-detail-section-title">Block Assembly</summary>{body}</details>'
    )


def _caption(text):
    return f'<p class="object-detail-cnc-caption">{escape(text)}</p>'


def _summary_row(block, label, *, total=False):
    values = [label, str(block["active_minutes"]), f'{block["planned_minutes"]:.2f}', f'₪{block["base_labor_ils"]:,.2f}']
    if not total and not block["operations"]:
        values = [label, "—", "—", "—"]
    css = " object-detail-assembly-total" if total else ""
    return (
        f'<div class="object-detail-table-row{css}" role="row">'
        + "".join(f'<div class="object-detail-table-cell" role="cell">{escape(value)}</div>' for value in values)
        + '</div>'
    )


def _details(block):
    lines = [
        f'<li>{escape(_OPERATIONS[op["operation"]])} · {op["quantity"]} × {op["minutes_per_unit"]} min '
        f'= {op["active_minutes"]} min</li>' for op in block["operations"]
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
    if result is None:
        return _section(_caption(message))
    if not result["blocks"]:
        return _section(_caption("No assembly blocks in Parts Check."))
    headers = "".join(
        f'<div class="object-detail-table-head" role="columnheader">{label}</div>'
        for label in ("Block", "Active min", "Planned min", "Base labor")
    )
    rows = "".join(
        _summary_row(block, block["block_id"] + (" · review" if block["issues"] else ""))
        for block in result["blocks"]
    )
    partial = bool(result["common_roles_for_review"] or any(block["issues"] for block in result["blocks"]))
    table = (
        '<div class="object-detail-table object-detail-assembly-table" role="table" aria-label="Block Assembly estimate">'
        f'<div class="object-detail-table-head-row" role="row">{headers}</div>{rows}'
        + _summary_row(result, "Subtotal" if partial else "Total", total=True) + '</div>'
    )
    captions = _caption(f'Per finished item · ₪{result["hourly_base_ils"]:g}/h base wage · payroll costs excluded')
    if result["common_roles_for_review"]:
        captions += _caption("Some assembly parts have no block assignment and need review.")
    captions += _caption("Glass, mirrors, lighting, split-panel joining and site work are outside this estimate.")
    details = "".join(_details(block) for block in result["blocks"])
    return _section(captions + table + details)
