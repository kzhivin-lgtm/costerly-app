"""Labor V1 comparison for the open Object Detail card."""

from html import escape
import json
import logging

import streamlit as st

from db.repositories import fetch_rfq_estimate_material_plan
from db.supabase_client import get_supabase_client
from use_cases.estimation_labor_v1 import (
    LAYOUT_VERSION, SPLIT_ROLES, build_sheet_layout, calculate_labor_v1, describe_layout_issues, sheet_layout_basis,
)
from use_cases.estimation_parts_check_runtime import load_parts_check
from use_cases.machinery import load_cnc_operator_wage


_LOG = logging.getLogger(__name__)


def _calculate(client, *, identity):
    company_id, run_id, estimate_id, object_id = identity
    params = {"client": client, "company_id": company_id, "run_id": run_id, "estimate_id": estimate_id}
    parts = load_parts_check(**params)
    if parts["status"] != "ready":
        return {"status": parts["status"]}
    rows = fetch_rfq_estimate_material_plan(client, estimate_id)
    if rows.empty:
        return {"status": "waiting_for_materials"}
    plan = rows.iloc[0].get("plan_payload") or {}
    if plan.get("status") not in {"planned", "needs_review"}:
        return {"status": "waiting_for_materials"}
    report = json.loads(parts["payload"])
    if object_id not in report["objects"]:
        return {"status": "unavailable"}
    source = plan.get("parts_check_source") or {}
    if not source or any(source.get(k) != report.get(k) for k in (
        "run_id", "estimate_id", "input_ids", "source_audit_sha256", "overlay_revision"
    )):
        return {"status": "different_revision"}
    layout = report.get("sheet_layout") or {}
    if layout.get("version") != LAYOUT_VERSION or layout.get("basis_sha256") != sheet_layout_basis(plan):
        layout = build_sheet_layout(report, plan)
    result = calculate_labor_v1(
        layout, plan, object_id=object_id, operator_gross_rate=load_cnc_operator_wage(client, company_id),
    )
    result["issues"] = describe_layout_issues(result["issues"], layout, report)
    return {"status": "ready", "result": result}


def _money(amount):
    return "—" if amount is None else f"₪{round(amount):,}"


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


def _cnc_section(body):
    return (
        '<details class="object-detail-elements object-detail-elements-section object-detail-cnc" open>'
        '<summary class="object-detail-section-title">CNC</summary>'
        f'{body}</details>'
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


def _comparison_html(result):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    preparation = result["file_preparation"]
    edge = result["edge_banding"]
    issues = result["issues"]
    if not rows and not issues:
        return _cnc_section('<p class="object-detail-cnc-caption">No sheet goods for CNC on this object.</p>')
    sheets = _sheets(work["sheet_count"])
    count_label = f"{sheets} {'sheet' if work['sheet_count'] == 1 else 'sheets'}"
    count_label += f" · {work['blank_count']} {'part' if work['blank_count'] == 1 else 'parts'}"
    operator = internal["operator_ex_vat"]
    has_work = bool(work["blank_count"])
    supplier_stock = external["bundle_ex_vat"] if has_work else None
    supplier_drilling = external["machining_ex_vat"] if has_work else None
    prep_minutes = preparation["minutes"]
    prep_cost = preparation["operator_ex_vat"]
    supplier_includes_prep = preparation["supplier_includes_preparation"]
    # Sum the rounded lines so the displayed whole-shekel totals reconcile.
    internal_labor = (round(operator) + round(prep_cost) + round(edge["in_house_ex_vat"])
                      if has_work or prep_minutes or edge["metres"] else None)
    sheet_amounts = [row["stock_ex_vat"] for row in rows if row["sheets"]]
    priced_sheet_amounts = [amount for amount in sheet_amounts if amount is not None]
    sheet_stock = sum(priced_sheet_amounts) if priced_sheet_amounts else None
    sheet_stock_complete = len(sheet_amounts) == len(priced_sheet_amounts)
    tape_stock = edge["tape_stock_ex_vat"]
    tape_stock_complete = edge["tape_stock_complete"]
    internal_total = (
        internal_labor + round(sheet_stock or 0) + round(tape_stock or 0)
        if internal_labor is not None else None
    )
    supplier_total = (round(supplier_stock or 0) + round(supplier_drilling or 0) + round(edge["supplier_ex_vat"])
                      if has_work or edge["metres"] else None)
    if prep_minutes and not supplier_includes_prep:
        supplier_total = (supplier_total or 0) + round(prep_cost)
    if edge["metres"] and not edge["supplier_includes_tape"]:
        supplier_total = (supplier_total or 0) + round(tape_stock or 0)
    layout_complete = not issues and not result["unplaced_blanks"]
    unpriced_sheets = external["unpriced_sheets"]
    supplier_stock_note = count_label
    if unpriced_sheets:
        supplier_stock_note += f" · {_sheets(unpriced_sheets)} need a quote"
    comparison_rows = [
        (("CNC workload", count_label, ""),
         ("Stock and cutting", _money(supplier_stock),
          supplier_stock_note)),
        (("Operator", _money(operator) if has_work else "—",
          f"{internal['operator_hours']} h"),
         ("Drilling allowance", _money(supplier_drilling), f"₪{external['drilling_rate']}/part")),
        (("Sheet stock", _estimate(sheet_stock, sheet_stock_complete),
          "" if sheet_stock_complete else "Some stock needs a quote") if sheet_amounts else None, None),
    ]
    if prep_minutes:
        duration = f"{prep_minutes:.2f}".rstrip("0").rstrip(".")
        comparison_rows.append((
            ("File preparation", _money(prep_cost), f"{duration} min"),
            ("File preparation", "Included", "") if supplier_includes_prep
            else ("File preparation", _money(prep_cost), "Our operator"),
        ))
    if edge["metres"]:
        metres = f"{edge['metres']:.1f} m"
        supplier_edge_note = metres
        if edge["supplier_includes_tape"]:
            supplier_edge_note += " · Tape included"
        if edge["supplier_unpriced_metres"]:
            supplier_edge_note += f" · {edge['supplier_unpriced_metres']:.1f} m need a quote"
        comparison_rows.append((
            ("Edge banding labor", _money(edge["in_house_ex_vat"]), f"{metres} · {edge['minutes']:.1f} min"),
            ("Edge banding", _estimate(edge["supplier_ex_vat"], not edge["supplier_unpriced_metres"]),
             supplier_edge_note),
        ))
        tape_row = ("Edge tape", _estimate(tape_stock, tape_stock_complete),
                    "" if tape_stock_complete else "Quote needed")
        comparison_rows.append((tape_row, None if edge["supplier_includes_tape"] else tape_row))
    comparison_rows += [
        (("Estimated labor", _estimate(internal_labor, layout_complete), ""),
         ("Estimated labor", "Included", "No separate labor rate") if supplier_total is not None
         else ("Estimated labor", "—", "Quote needed")),
        (("Estimated cost", _estimate(internal_total, layout_complete and sheet_stock_complete
                                      and tape_stock_complete), "Materials + labor"),
         ("Estimated cost", _estimate(supplier_total, layout_complete and not unpriced_sheets
                                      and not edge["supplier_unpriced_metres"]
                                      and (edge["supplier_includes_tape"] or tape_stock_complete)),
          "Materials + labor")),
    ]
    comparison = _comparison_table([row for row in comparison_rows if any(row)])
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
    details = (
        '<details class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">'
        '<summary>CNC time breakdown</summary>'
        '<table><thead><tr><th scope="col">Operation</th><th scope="col">Minutes</th></tr></thead>'
        f'<tbody>{minutes}</tbody><tfoot><tr><th scope="row">Total</th>'
        f'<td>{work["machine_minutes"]:.1f}</td></tr></tfoot></table>{joined}{excluded}</details>'
    )
    return _cnc_section(comparison + _supplier_stock_html(external["materials"]) + details)


def _estimate(value, complete):
    if value is None or complete:
        return _money(value)
    return f"{_money(value)} (subtotal)"


@st.fragment(parallel=True)
def render_labor_v1(*, company_id, run_id, estimate_id, object_id):
    identity = company_id, run_id, estimate_id, object_id
    cache = st.session_state.setdefault("labor_v1_comparisons", {})
    view = st.empty()
    if identity not in cache:
        view.markdown(_cnc_section('<p class="object-detail-cnc-caption">Preparing CNC…</p>'), unsafe_allow_html=True)
        try:
            state = _calculate(get_supabase_client(), identity=identity) if run_id else {"status": "unavailable"}
        except Exception:
            _LOG.exception("Could not calculate Labor V1 for estimate %s", estimate_id)
            state = {"status": "read_failed"}
        if state["status"] == "ready":
            cache[identity] = state["result"]
    if identity in cache:
        html = _comparison_html(cache[identity])
    else:
        messages = {
            "running": "CNC is waiting for Parts Check.",
            "waiting_for_materials": "CNC is waiting for the Material Plan.",
            "different_revision": "CNC is waiting for matching Parts Check and Materials.",
            "failed": "CNC is unavailable because Parts Check failed.",
            "unavailable": "Parts Check is unavailable for this object.",
            "read_failed": "CNC could not be loaded.",
        }
        html = _cnc_section(f'<p class="object-detail-cnc-caption">{messages[state["status"]]}</p>')
    view.markdown(html, unsafe_allow_html=True)
