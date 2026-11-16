"""Labor V1 comparison for the open Object Detail card."""

from html import escape
import json
import logging

import streamlit as st

from db.repositories import fetch_rfq_estimate_material_plan
from db.supabase_client import get_supabase_client
from use_cases.estimation_labor_v1 import (
    LAYOUT_VERSION, build_sheet_layout, calculate_labor_v1, describe_layout_issues, sheet_layout_basis,
)
from use_cases.estimation_parts_check_runtime import load_parts_check


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
    result = calculate_labor_v1(layout, plan, object_id=object_id)
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
    if not joins:
        return ""
    labels = {"carcass_side": "cabinet side", "carcass_back": "back panel", "frame_backing": "back panel"}
    entries = []
    for join in joins:
        _, block, role, _ = join["part_id"].rsplit(":", 3)
        if role.startswith("plinth_"):
            name = "Plinth"
        else:
            name = f"{block} {labels.get(role, role.replace('_', ' '))}"
        quantity = join["part_count"]
        count = f"{quantity} × " if quantity > 1 else ""
        length, width = join["length_mm"], join["width_mm"]
        finished_length = length * join["length_sections"]
        finished_width = width * join["width_sections"]
        entries.append(
            f"<li>{count}{escape(name)} ({finished_length:g} × {finished_width:g} mm): "
            f"{join['pieces_per_part']} pieces each, {length:g} × {width:g} mm</li>"
        )
    return "<p><strong>Parts made in sections</strong></p><ul>" + "".join(entries) + "</ul>"


def _comparison_html(result):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    issues = result["issues"]
    if not rows and not issues:
        return _cnc_section('<p class="object-detail-cnc-caption">No sheet goods for CNC on this object.</p>')
    sheets = _sheets(work["sheet_count"])
    parts = f"{work['blank_count']} parts"
    priced_stock = [row["stock_ex_vat"] for row in rows if row["stock_ex_vat"] is not None]
    stock_cost = sum(priced_stock) if priced_stock else None
    operator = internal["operator_ex_vat"]
    has_work = bool(work["blank_count"])
    supplier_stock = external["bundle_ex_vat"] if has_work else None
    supplier_drilling = external["machining_ex_vat"] if has_work else None
    # Sum the rounded lines so the displayed whole-shekel totals reconcile.
    internal_total = round(operator) + round(stock_cost or 0) if has_work else None
    supplier_total = round(supplier_stock) + round(supplier_drilling) if has_work else None
    layout_complete = not issues and not result["unplaced_blanks"]
    internal_complete = layout_complete and len(priced_stock) == len(rows)
    missing_stock = sorted({
        f"{row['material']} ({row['thickness_mm']:g} mm)"
        for row in rows if row["sheets"] and row["stock_ex_vat"] is None
    })
    in_house_stock = f"{sheets} sheets"
    if missing_stock:
        in_house_stock += f" · Price needed for {', '.join(missing_stock)}"
    comparison = _comparison_table([
        ((f"Sheet stock · {parts}", _money(stock_cost), in_house_stock),
         (f"Stock and cutting · {parts}", _money(supplier_stock),
          f"{sheets} sheets × {_money(external['sheet_rate'])}")),
        (("Operator", _money(operator) if has_work else "—",
          f"{internal['operator_hours']} h"),
         ("Drilling allowance", _money(supplier_drilling), f"₪{external['drilling_rate']}/part")),
        (("Estimated cost", _estimate(internal_total, internal_complete), ""),
         ("Estimated cost", _estimate(supplier_total, layout_complete), "")),
    ])
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
    estimated_stock = ""
    for row in rows:
        if row["stock_price_is_estimated"] and row["sheets"]:
            length, width = row["size_mm"]
            estimated_stock += (
                f"<p>{length:g} × {width:g} mm sheet stock: {_money(row['stock_ex_vat'])} "
                "(reference estimate). Subcontractor pricing for this format needs a quote.</p>"
            )
    details = (
        '<details class="object-detail-table object-detail-cnc-breakdown" data-section="cnc">'
        '<summary>CNC time breakdown</summary>'
        '<table><thead><tr><th scope="col">Operation</th><th scope="col">Minutes</th></tr></thead>'
        f'<tbody>{minutes}</tbody><tfoot><tr><th scope="row">Total</th>'
        f'<td>{work["machine_minutes"]:.1f}</td></tr></tfoot></table>{estimated_stock}{joined}{excluded}</details>'
    )
    return _cnc_section(comparison + details)


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
