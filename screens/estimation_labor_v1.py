"""Sheet Processing comparison for the open Object Detail card."""

from html import escape
from decimal import Decimal
import json
import logging

import streamlit as st

from db.repositories import (
    fetch_company_overhead_settings, fetch_company_overhead_monthly,
    fetch_rfq_estimate_material_plan,
)
from db.supabase_client import get_supabase_client
from observability.runtime import report_runtime_failure
from screens.block_assembly import assembly_breakdown_html
from ui.object_detail_view import detail_elements_html, overhead_section_html, _money as display_money
from use_cases.overhead_engine import estimate_object_overhead, with_production_capacity, format_labor_hours
from use_cases.block_assembly import calculate_block_assembly
from use_cases.estimation_labor_v1 import (
    LAYOUT_VERSION, SPLIT_ROLES, build_sheet_layout, describe_layout_issues, sheet_layout_basis,
    labor_pay_metrics, sheet_pay_metrics, object_labor_metrics, load_object_labor,
    DISPLAY_HOURLY_RATE, DISPLAY_PAYROLL_SHARE,
    preparation_pay_metrics, labor_work_metrics,
)
from use_cases.estimation_parts_check_runtime import load_parts_check
from use_cases.machinery import load_sheet_processing_machinery
from use_cases.sheet_processing import calculate_sheet_processing


_LOG = logging.getLogger(__name__)


def _calculate(client, *, identity):
    return load_object_labor(client, identity=identity, parts_loader=load_parts_check,
                             plan_loader=fetch_rfq_estimate_material_plan,
                             machinery_loader=load_sheet_processing_machinery)





def _money(amount):
    return display_money(amount)


def _sheets(quantity):
    return "—" if quantity is None else f"{quantity:.2f}".rstrip("0").rstrip(".")


def _comparison_table(rows):
    """Use the same table styling as the other Object Detail sections."""
    def cell(item):
        content = ""
        if item is not None:
            label, value, rate = item
            rate_html = f'<span class="object-detail-cnc-rate">{escape(rate)}</span>' if rate else ""
            content = (
                f'<span class="object-detail-cnc-label">{escape(label)}{rate_html}</span>'
                f'<span class="object-detail-cnc-value">{escape(value)}</span>'
            )
        return f'<div class="object-detail-table-cell" role="cell">{content}</div>'

    body = "".join(
        f'<div class="object-detail-table-row" role="row">{cell(inside)}{cell(outside)}</div>'
        for inside, outside in rows
    )
    return (
        '<div class="object-detail-table object-detail-table--cols-2" data-section="cnc" role="table">'
        '<div class="object-detail-table-head-row" role="row">'
        '<div class="object-detail-table-head" role="columnheader">In-house</div>'
        '<div class="object-detail-table-head" role="columnheader">Subcontractor</div>'
        '</div>' + body + '</div>'
    )


def _sheet_section(body, *, count_label="", metrics=None):
    counts = f'<span class="object-detail-cnc-count">{escape(count_label)}</span>' if count_label else ""
    return _cost_band('Sheet Processing', counts + body, metrics, key='sheet-processing')


_pay_metrics = labor_pay_metrics


_sheet_pay_metrics = sheet_pay_metrics


def _cost_band(title, body, metrics=None, *, key, open_by_default=False, editable=True, fixed_leaf=False, aggregate=False, cost_quantity=1, explicit_keys=()):
    is_row = key != 'labor'

    def metric(label, value, column, *, total=False):
        value = '—' if value is None else value
        css = 'object-detail-cost-total' if total else 'object-detail-cost-metric'
        cell = 'object-detail-table-cell' if is_row else 'object-detail-table-head'
        content = (f'<span class="object-detail-cost-value">{escape(str(value))}</span>' if is_row else
                   f'<span class="object-detail-cost-label">{label}</span>')
        if is_row and column == 'hours' and editable:
            original = f' data-original-value="{metrics["hours"]}"' if metrics is not None else ''
            displayed = value
            content = (
                '<div class="object-detail-material-input" data-quantity-decimals="1">'
                '<div class="object-detail-cell-input object-detail-cell-input--number"'
                ' role="textbox" contenteditable="true" tabindex="0" inputmode="decimal"'
                f' aria-label="{escape(title)} hours" data-field="labor_hours" data-line-id="{key}"'
                f'{original} data-placeholder="—">{displayed}</div></div>'
            )
        return f'<div class="{cell} {css}" data-labor-column="{column}">{content}</div>'

    value = metrics or {}
    fields = metric('Hours', format_labor_hours(value['hours']) if metrics else None, 'hours')
    fields += '<div class="object-detail-labor-money-pair">'
    fields += metric('Labor<br>Pay', _money(value.get('pay')), 'pay')
    fields += metric('Taxes &amp;<br>Social +25%', _money(value.get('taxes')), 'taxes') + '</div>'
    fields += metric('Total', _money(value.get('total')), 'total', total=True)
    classes = 'object-detail-work-row' if is_row else 'object-detail-table object-detail-cost-band object-detail-labor-table'
    cell = 'object-detail-table-cell' if is_row else 'object-detail-table-head'
    row = 'object-detail-table-row' if is_row else 'object-detail-table-head-row'
    body_class = 'object-detail-work-body' if is_row else 'object-detail-labor-body'
    if not is_row:
        return (
            f'<details class="{classes}" data-cost-band="{key}"'
            f' data-cost-unknown="{str(metrics is None).lower()}"'
            f' data-cost-partial="{str(bool(value.get("partial"))).lower()}"'
            f' data-labor-total-hours="{value.get("hours", "")}"'
            f' data-labor-cost-quantity="{cost_quantity}"'
            f' data-labor-explicit-keys="{escape(json.dumps(list(explicit_keys)), quote=True)}"'
            f' data-labor-base-hours="{value.get("hours", "")}" data-labor-base-total="{value.get("total", "")}"'
            + (' open' if open_by_default else '') + '>'
            '<summary class="object-detail-table-head-row object-detail-cost-summary object-detail-band-summary">'
            f'<div class="{cell} object-detail-cost-title">{escape(title)}</div>'
            '<div class="object-detail-table-head object-detail-cost-hours" data-labor-column="hours">'
            '<span class="object-detail-labor-hours-value">'
            + (f'{format_labor_hours(value["hours"])} h' if metrics else '—')
            + '</span></div>'
            '<div class="object-detail-table-head object-detail-cost-total" data-labor-column="total">'
            f'<span class="object-detail-cost-value">{_money(value.get("total"))}</span></div></summary>'
            f'<div class="{body_class}">'
            '<div class="object-detail-table-head-row object-detail-cost-summary object-detail-cost-column-headings">'
            f'<div class="object-detail-table-head"></div>{fields}</div>{body}</div></details>'
        )
    return (
        f'<details class="{classes}" data-cost-band="{key}"'
        + (' data-labor-aggregate="true"' if aggregate else '')
        + (f' data-labor-fixed-hours="{value["hours"]}"' if fixed_leaf and metrics else '')
        + f' data-cost-unknown="{str(metrics is None).lower()}"'
        f' data-cost-partial="{str(bool(value.get("partial"))).lower()}"'
        + (' open' if open_by_default else '') + '>'
        f'<summary class="{row} object-detail-cost-summary">'
        f'<div class="{cell} object-detail-cost-title">{escape(title)}</div>{fields}</summary>'
        f'<div class="{body_class}">{body}</div></details>'
    )


def _joined_parts_html(joins):
    labels = {"carcass_side": "cabinet side"}
    entries = []
    for join in joins:
        _, block, role, _ = join["part_id"].rsplit(":", 3)
        if role in SPLIT_ROLES:
            continue
        name = f"{block} {labels.get(role, role.replace('_', ' '))}"
        quantity = join["part_count"]
        count = f"{quantity} × " if quantity > 1 else ""
        entries.append(f"<li>{count}{escape(name)}</li>")
    if not entries:
        return ""
    return "<p><strong>Visible parts with a joint</strong></p><ul>" + "".join(entries) + "</ul>"


def _supplier_stock_html(rows):
    if not rows:
        return ""
    entries = []
    for row in rows:
        length, width = row["size_mm"]
        stock = f"{row['material']} · {length:g} × {width:g} mm"
        rate = row["rate_ex_vat"]
        quantity = _sheets(row["sheets"])
        detail = f"{quantity} sheets · Quote needed"
        if rate is not None:
            detail = f"{quantity} × {_money(rate)}"
            if row["basis"] in {"stock_plus_straight_cut", "thickness_estimate", "format_estimate", "veneer_estimate"}:
                detail += " · Estimate"
        entries.append(
            f"<tr><td>{escape(stock)}</td><td>{escape(detail)}</td>"
            f"<td>{_money(row['bundle_ex_vat'])}</td></tr>"
        )
    return (
        '<details class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">'
        '<summary>Subcontractor sheet rates</summary>'
        '<table><thead><tr><th scope="col">Stock</th><th scope="col">Sheets and rate</th>'
        '<th scope="col">Amount</th></tr></thead>'
        f"<tbody>{''.join(entries)}</tbody></table></details>"
    )


def _panel_saw_breakdown(panel_saw, *, tape_stock, tape_stock_complete, layout_complete):
    if not panel_saw:
        return ""
    edge = panel_saw["edging"]
    minutes = [("Layout preparation", panel_saw["preparation_minutes"]),
               ("Panel saw", sum(panel_saw["saw"].values())),
               ("Manual drilling", sum(panel_saw["drilling"].values())), (edge["method"], edge["minutes"])]
    rows = "".join(f"<tr><td>{escape(label)}</td><td>{value:.1f}</td></tr>" for label, value in minutes)
    notes = [edge["note"]] if edge["note"] else []
    if panel_saw["unplaced"]:
        notes.append(f"{panel_saw['unplaced']} blanks need a different sheet format")
    if panel_saw["geometry_review"]:
        notes.append("Review contours and cutouts before using the panel saw route")
    note_html = "".join(f'<p class="object-detail-cnc-caption">{escape(note)}</p>' for note in notes)
    stock = panel_saw["materials"]
    shares = sum(row["sheets"] for row in stock)
    labor = sum(round(cost) for cost in (panel_saw["preparation_cost"], panel_saw["operator_cost"], edge["cost"]))
    stock_cost = sum(row["stock_ex_vat"] or 0 for row in stock)
    total = labor + round(stock_cost) + round(tape_stock or 0)
    complete = (layout_complete and tape_stock_complete and not panel_saw["geometry_review"]
                and not panel_saw["unplaced"] and not edge.get("unestimated")
                and all(row["stock_ex_vat"] is not None for row in stock))
    return (
        '<details class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">'
        '<summary>Panel saw and manual work</summary>'
        f'<p class="object-detail-cnc-caption">{_sheets(shares)} sheets · Labor {_money(labor)}'
        f' · Estimated cost {_estimate(total, complete)}</p>'
        '<table><thead><tr><th scope="col">Operation</th><th scope="col">Minutes</th></tr></thead>'
        f'<tbody>{rows}</tbody><tfoot><tr><th scope="row">Total</th>'
        f'<td>{panel_saw["minutes"]:.1f}</td></tr></tfoot></table>{note_html}</details>'
    )


def _cnc_time_breakdown(result, *, inline=False):
    work, issues = result['work'], result['issues']
    breakdown = (
        ("Setup", "setup_minutes"), ("Load sheets", "load_minutes"),
        ("Unload parts and scrap", "unload_minutes"), ("Clean table", "cleanup_minutes"),
        ("Cutting", "cut_minutes"), ("Moves", "move_minutes"), ("Drilling", "drilling_minutes"),
        ("Tool changes", "tool_change_minutes"),
    )
    minutes = "".join(
        f'<tr><td>{label}</td><td>{work[key]:.1f}</td></tr>' for label, key in breakdown
    )
    excluded = (
        '<p><strong>Excluded from this calculation</strong></p><ul>'
        + "".join(f"<li>{escape(row['description'])}</li>" for row in issues)
        + "</ul>"
    ) if issues else ""
    joined = _joined_parts_html(result["joined_parts"])
    body = (
        '<table><thead><tr><th scope="col">Operation</th><th scope="col">Minutes</th></tr></thead>'
        f'<tbody>{minutes}</tbody><tfoot><tr><th scope="row">Total</th>'
        f'<td>{work["machine_minutes"]:.1f}</td></tr></tfoot></table>{joined}{excluded}'
    )
    if inline:
        return '<div class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">' + body + '</div>'
    return ('<details class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">'
            '<summary>CNC time breakdown</summary>' + body + '</details>')


def _cnc_sheet_html(result, *, elements_html, work):
    operations = (
        _cost_band('Operator', _cnc_time_breakdown(result, inline=True), work['cnc-operator'], key='cnc-operator')
        + _cost_band('File Preparation', '', work['file-preparation'], key='file-preparation')
        + _cost_band('Edge Banding', '', work['edge-banding'], key='edge-banding')
    )
    body = '<div class="object-detail-cnc-elements">' + elements_html + '</div>'
    body += ('<details class="object-detail-cnc-work" data-labor-detail="cnc">'
             '<summary>CNC time breakdown</summary><div class="object-detail-cnc-work-body">'
             + operations + '</div></details>')
    return _cost_band('Sheet Processing', body, work['sheet-processing'], key='sheet-processing',
                      editable=False, aggregate=True)


def _comparison_html(result, *, elements_html='', metrics=None):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    preparation = result["file_preparation"]
    edge = result["edge_banding"]
    issues = result["issues"]
    route = result.get("in_house_route", "cnc")
    panel_saw = result.get("panel_saw")
    if not rows and not issues:
        return _sheet_section(elements_html + '<p class="object-detail-cnc-caption">No sheet processing for this object.</p>',
                              metrics=metrics if metrics is not None else _sheet_pay_metrics(result))
    in_house_rows = panel_saw["materials"] if route == "panel_saw" else rows
    sheet_count = sum(row["sheets"] for row in in_house_rows)
    count_label = f"{_sheets(sheet_count)} {'sheet' if sheet_count == 1 else 'sheets'}"
    if route == "panel_saw" and abs(sheet_count - work["sheet_count"]) > 0.005:
        count_label = f"{_sheets(sheet_count)} in-house / {_sheets(work['sheet_count'])} subcontractor sheets"
    count_label += f", {work['blank_count']} {'part' if work['blank_count'] == 1 else 'parts'}"
    operator = internal["operator_ex_vat"]
    has_work = bool(work["blank_count"])
    supplier_stock = external["bundle_ex_vat"] if has_work else None
    supplier_drilling = external["machining_ex_vat"] if has_work else None
    prep_minutes = preparation["minutes"]
    prep_cost = preparation["operator_ex_vat"]
    supplier_includes_prep = preparation["supplier_includes_preparation"]
    inside_prep_minutes, inside_prep_cost = prep_minutes, prep_cost
    inside_edge = result.get("cnc_edging", {"method": "Edge bander", "minutes": edge["minutes"],
                                            "cost": edge["in_house_ex_vat"]})
    inside_operator_note = f"CNC · {internal['operator_hours']} h" if has_work else ""
    inside_prep_label = "File preparation"
    if route == "panel_saw":
        inside_prep_minutes = panel_saw["preparation_minutes"]
        inside_prep_cost = panel_saw["preparation_cost"]
        inside_prep_label = "Layout preparation"
        operator = panel_saw["operator_cost"]
        inside_operator_note = "Panel saw and manual drilling"
        inside_edge = panel_saw["edging"]
    # Sum the rounded lines so the displayed whole-shekel totals reconcile.
    internal_labor = round(operator) + round(inside_prep_cost) + round(inside_edge["cost"])
    sheet_amounts = [row["stock_ex_vat"] for row in in_house_rows if row["sheets"]]
    priced_sheet_amounts = [amount for amount in sheet_amounts if amount is not None]
    sheet_stock = sum(priced_sheet_amounts) if priced_sheet_amounts else None
    sheet_stock_complete = len(sheet_amounts) == len(priced_sheet_amounts)
    tape_stock = edge["tape_stock_ex_vat"]
    tape_stock_complete = edge["tape_stock_complete"]
    materials_complete = sheet_stock_complete and tape_stock_complete
    material_cost = round(sheet_stock or 0) + round(tape_stock or 0)
    material_amount = material_cost if sheet_stock is not None or (edge["metres"] and tape_stock is not None) else None
    material_notes = []
    if sheet_amounts:
        material_notes.append(f"Sheets {_money(sheet_stock)}")
    if edge["metres"]:
        material_notes.append(f"Edge tape {_money(tape_stock)}")
    if not materials_complete:
        material_notes.append("Quote needed")
    internal_total = internal_labor + material_cost if has_work or prep_minutes or edge["metres"] else None

    supplier_edge = round(edge["supplier_ex_vat"])
    supplier_edge_complete = not edge["supplier_unpriced_metres"]
    supplier_edge_notes = []
    metres = f"{edge['metres']:.1f} m"
    if edge["metres"]:
        supplier_edge_notes.append(metres)
        if edge["supplier_includes_tape"]:
            supplier_edge_notes.append("Tape included")
        else:
            supplier_edge += round(tape_stock or 0)
            supplier_edge_complete = supplier_edge_complete and tape_stock_complete
            supplier_edge_notes.append(f"Edge tape {_money(tape_stock)}")
        if not supplier_edge_complete:
            supplier_edge_notes.append("Quote needed")

    supplier_total = (round(supplier_stock or 0) + round(supplier_drilling or 0) + supplier_edge
                      if has_work or edge["metres"] else None)
    if prep_minutes and not supplier_includes_prep:
        supplier_total = (supplier_total or 0) + round(prep_cost)
    layout_complete = not issues and not result["unplaced_blanks"]
    unpriced_sheets = external["unpriced_sheets"]
    supplier_stock_note = f"{_sheets(unpriced_sheets)} need a quote" if unpriced_sheets else ""
    duration = f"{inside_prep_minutes:.2f}".rstrip("0").rstrip(".")
    edging_note = (f"{metres} · {inside_edge['minutes']:.1f} min" if edge["metres"] else "")
    if edging_note and inside_edge["method"] == "Iron-on":
        edging_note = " · ".join(("Iron-on", edging_note, inside_edge["note"]))
    inside_complete = layout_complete and materials_complete and not inside_edge.get("unestimated")
    comparison_rows = [
        ((inside_prep_label, _money(inside_prep_cost) if inside_prep_minutes else "—",
          f"{duration} min" if inside_prep_minutes else ""),
         ("File preparation", "Included", "") if prep_minutes and supplier_includes_prep else
         ("File preparation", _money(prep_cost) if prep_minutes else "—", "Our operator" if prep_minutes else "")),
        (("Operator", _money(operator) if has_work else "—", inside_operator_note),
         ("Stock and cutting", _estimate(supplier_stock, not unpriced_sheets), supplier_stock_note)),
        (("Edge banding labor", _estimate(inside_edge["cost"] if edge["metres"] else None,
                                         not inside_edge.get("unestimated")), edging_note),
         ("Edge banding", _estimate(supplier_edge if edge["metres"] else None, supplier_edge_complete),
          " · ".join(supplier_edge_notes))),
        (("Materials", _estimate(material_amount, materials_complete), " · ".join(material_notes)),
         ("Drilling allowance", _money(supplier_drilling), f"₪{external['drilling_rate']}/part")),
        (("Estimated cost", _estimate(internal_total, inside_complete), "Materials + labor"),
         ("Estimated cost", _estimate(supplier_total, layout_complete and not unpriced_sheets
                                      and supplier_edge_complete), "Materials + labor")),
    ]
    if route is None:
        comparison_rows = [(None, outside) for _, outside in comparison_rows]
        comparison_rows[1] = (("In-house route unavailable", "—", "See Machinery settings"), comparison_rows[1][1])
    comparison = _comparison_table(comparison_rows)
    details = _cnc_time_breakdown(result)
    saw_details = _panel_saw_breakdown(panel_saw, tape_stock=tape_stock, tape_stock_complete=tape_stock_complete,
                                      layout_complete=layout_complete)
    return _sheet_section(elements_html + comparison + _supplier_stock_html(external["materials"])
                          + (details if route == "cnc" else "") + saw_details, count_label=count_label,
                          metrics=metrics if metrics is not None else _sheet_pay_metrics(result))


def _estimate(value, complete):
    return _money(value)


_labor_pay_metrics = object_labor_metrics


def _preparation_html(state, *, quantity=1, overrides=None):
    checking, packing, total = preparation_pay_metrics(state, quantity=quantity, overrides=overrides)
    result = state.get('preparation') or {}
    interfaces = result.get('interfaces', ())
    checking_body = '<ul>' + ''.join(
        '<li>' + escape(' ↔ '.join(row['unit_ids'])) +
        f' · {row["quantity"] if row["quantity"] is not None else "—"} × 30 min</li>' for row in interfaces) + '</ul>' if interfaces else ''
    packing_body = '<ul>' + ''.join(
        '<li>' + escape(row['id']) + f' · {row["size"] or "—"} · '
        + escape(str(row['quantity'])) + f' × {row["minutes_per_unit"] if row["minutes_per_unit"] is not None else "—"} min</li>'
        for row in result.get('packing_units', ())) + '</ul>' if result.get('packing_units') else ''
    body = _cost_band('Trial Fit and Separation', checking_body, checking, key='trial-fit')
    body += _cost_band('Packing', packing_body, packing, key='packing')
    return _cost_band('Preparation and Packing', body, total, key='preparation-packing', editable=False, aggregate=True)


def _labor_html(state, *, elements=None, overlay_revision=None, object_id=None, quantity=1, overrides=None):
    work = labor_work_metrics(state, quantity=quantity, overrides=overrides)
    sheet_metrics, assembly_metrics, total = (work[key] for key in ('sheet-processing', 'assembly', 'labor'))
    elements_html = detail_elements_html(elements, revision=overlay_revision, object_id=object_id)
    if state['status'] == 'ready':
        sheet = (_cnc_sheet_html(state['result'], elements_html=elements_html, work=work)
                 if state['result'].get('in_house_route', 'cnc') == 'cnc' else
                 _comparison_html(state['result'], elements_html=elements_html, metrics=sheet_metrics))
    else:
        messages = {
            'preparing': 'Preparing Sheet Processing…', 'running': 'Waiting for Parts Check.',
            'waiting_for_materials': 'Waiting for the Material Plan.',
            'different_revision': 'Waiting for matching Parts Check and Materials.',
            'failed': 'Parts Check failed.', 'unavailable': 'Parts Check is unavailable for this object.',
            'read_failed': 'Sheet Processing could not be loaded.',
        }
        sheet = _sheet_section(elements_html + f'<p class="object-detail-cnc-caption">{messages[state["status"]]}</p>',
                               metrics=sheet_metrics)
    assembly = state.get('assembly')
    if assembly is not None:
        assembly_body = assembly_breakdown_html(assembly, quantity=quantity, payroll_share=DISPLAY_PAYROLL_SHARE, inline=True)
        if not assembly['blocks']:
            assembly_body = '<p class="object-detail-cnc-caption">No assembly blocks in Parts Check.</p>'
    else:
        message = 'Preparing Assembly…' if state['status'] == 'preparing' else 'Assembly is unavailable.'
        assembly_body = f'<p class="object-detail-cnc-caption">{message}</p>'
    block_assembly = _cost_band('Block Assembly', assembly_body, assembly_metrics, key='assembly')
    additional = _cost_band('Additional Assembly', '', work['additional-assembly'], key='additional-assembly')
    body = (
        _cost_band('Part Production', sheet, sheet_metrics, key='part-production', editable=False, aggregate=True)
        + _cost_band('Part Coating', '', work['part-coating'], key='part-coating')
        + _cost_band('Assembly', block_assembly + additional, work['assembly-stage'],
                     key='assembly-stage', editable=False, aggregate=True)
        + _preparation_html(state, quantity=quantity, overrides=overrides)
    )
    return '<div class="object-detail-labor-band">' + _cost_band('Labor', body, total, key='labor', cost_quantity=quantity, explicit_keys=(overrides or {}).keys()) + '</div>'


def _overhead_html(state, *, identity, material_cost, material_partial=False, quantity=1, overrides=None):
    company_id, run_id, estimate_id, object_id = identity
    context = state.get("overhead_context", {"status": "read_failed"})
    overhead = {"status": context["status"], "object_id": object_id}
    if context["status"] == "ready":
        _, _, total = _labor_pay_metrics(state, quantity=quantity, overrides=overrides)
        overhead = estimate_object_overhead(
            company_id=company_id, estimate_id=estimate_id, object_id=object_id,
            settings=context["settings"], overhead_monthly=context["monthly"],
            labor_hours=total["hours"] if total else None,
            labor_cost=total["total"] if total else None, material_cost=material_cost,
            partial=material_partial or bool(total and total["partial"]),
        )
    return overhead_section_html({**overhead, "estimate_id": estimate_id, "run_id": run_id})


def _load_overhead_context(client, company_id):
    """Read the existing company inputs within the existing parallel fragment."""
    settings = fetch_company_overhead_settings(client, company_id)
    monthly = fetch_company_overhead_monthly(client, company_id)
    return {"status": "ready", "settings": with_production_capacity(client, company_id, settings.iloc[0].to_dict() if not settings.empty else {}),
            "monthly": monthly.iloc[0].to_dict() if not monthly.empty else {}}


@st.fragment(parallel=True)
def render_labor_v1(*, company_id, run_id, estimate_id, object_id, elements=None, overlay_revision=None,
                    quantity=1, overrides=None, material_cost=0, material_partial=False):
    identity = company_id, run_id, estimate_id, object_id
    cache = st.session_state.setdefault("labor_v1_comparisons", {})
    view = st.empty()
    overhead_view = st.empty()
    overhead_view.markdown(overhead_section_html({"status": "loading", "object_id": object_id}), unsafe_allow_html=True)
    state = cache.get(identity)
    if not state or "assembly" not in state or "preparation" not in state:
        view.markdown(
            _labor_html({'status': 'preparing'}, elements=elements, overlay_revision=overlay_revision,
                        object_id=object_id, quantity=quantity, overrides=overrides), unsafe_allow_html=True,
        )
        try:
            state = _calculate(get_supabase_client(), identity=identity) if run_id else {"status": "unavailable"}
        except Exception as exc:
            report_runtime_failure("cnc.calculate", exc, rfq_run_id=run_id, estimate_id=estimate_id, object_id=object_id)
            _LOG.exception("Could not calculate Labor V1 for estimate %s", estimate_id)
            state = {"status": "read_failed"}
        if state["status"] == "ready":
            cache[identity] = state
    # Labor is visible before the separate company read. Loading Overhead must
    # not replace its input nodes or wait in the Materials/navigation path.
    view.markdown(_labor_html(state, elements=elements, overlay_revision=overlay_revision,
                             object_id=object_id, quantity=quantity, overrides=overrides), unsafe_allow_html=True)
    if "overhead_context" not in state:
        try:
            state["overhead_context"] = _load_overhead_context(get_supabase_client(), company_id)
        except Exception as exc:
            report_runtime_failure("overhead.load", exc, rfq_run_id=run_id,
                                   estimate_id=estimate_id, object_id=object_id)
            _LOG.exception("Could not load Overhead for estimate %s", estimate_id)
    overhead_view.markdown(_overhead_html(state, identity=identity, material_cost=material_cost,
                                         material_partial=material_partial, quantity=quantity,
                                         overrides=overrides), unsafe_allow_html=True)
