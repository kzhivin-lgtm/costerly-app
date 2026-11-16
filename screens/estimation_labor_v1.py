"""Labor V1 comparison for the open Object Detail card."""

from html import escape
import json
import logging

import streamlit as st

from db.repositories import fetch_rfq_estimate_material_plan
from db.supabase_client import get_supabase_client
from use_cases.estimation_labor_v1 import LAYOUT_VERSION, build_sheet_layout, calculate_labor_v1, sheet_layout_basis
from use_cases.estimation_parts_check_runtime import load_parts_check, save_parts_sheet_layout


_LOG = logging.getLogger(__name__)


def _machine_rate(client, company_id):
    rows = (client.table("company_machinery").select("pricing")
            .eq("company_id", company_id).eq("machine_code", "wood_cnc_router")
            .eq("active", True).eq("availability_status", "in_house")
            .eq("pricing_method", "hourly").limit(1).execute().data or [])
    rate = (rows[0].get("pricing") or {}).get("rate") if rows else None
    if isinstance(rate, (int, float)) and not isinstance(rate, bool) and rate > 0:
        return rate
    return None


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
        save_parts_sheet_layout(**params, report=report, layout=layout)
    return {"status": "ready", "result": calculate_labor_v1(
        layout, plan, object_id=object_id, machine_rate=_machine_rate(client, company_id),
    )}


def _money(amount):
    return "—" if amount is None else f"₪{amount:,.2f}"


def _sheets(quantity):
    return "—" if quantity is None else f"{quantity:.2f}".rstrip("0").rstrip(".")


def _comparison_table(rows):
    """Use the same table styling as the other Object Detail sections."""
    def cell(item):
        content = ""
        if item is not None:
            label, value = item
            content = (
                f'<span class="object-detail-section-label">{escape(label)}</span>'
                f'<span class="object-detail-cnc-value">{escape(value)}</span>'
            )
        return f'<div class="object-detail-table-cell" role="cell">{content}</div>'

    body = "".join(
        f'<div class="object-detail-table-row" role="row">{cell(inside)}{cell(outside)}</div>'
        for inside, outside in rows
    )
    st.markdown(
        '<div class="object-detail-table object-detail-table--cols-2" data-section="cnc" role="table">'
        '<div class="object-detail-table-head-row" role="row">'
        '<div class="object-detail-table-head" role="columnheader">In-house</div>'
        '<div class="object-detail-table-head" role="columnheader">Subcontractor</div>'
        '</div>' + body + '</div>',
        unsafe_allow_html=True,
    )


def _show_comparison(result):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    issues = result["issues"]
    if not rows and not issues:
        _comparison_table(())
        st.info("No sheet goods for CNC on this object.")
        return
    st.caption(
        f"{_sheets(work['sheet_count'])} CNC sheets · {work['blank_count']} blanks · "
        f"{work['drilled_part_count']} parts with estimated drilling · "
        f"{work['cut_m']:.1f} m cut · {work['machine_minutes']:.1f} min CNC"
    )
    if result["unplaced_blanks"]:
        st.warning(f'{result["unplaced_blanks"]} blanks did not fit. Both estimates are partial.')
    elif issues:
        st.warning("Some CNC parts need review. Both estimates are partial.")
    priced_stock = [row["stock_ex_vat"] for row in rows if row["stock_ex_vat"] is not None]
    machine = internal["machine_ex_vat"]
    operator = internal["operator_ex_vat"]
    has_work = bool(work["blank_count"])
    supplier_stock = external["bundle_ex_vat"] if has_work else None
    supplier_drilling = external["machining_ex_vat"] if has_work else None
    internal_total = operator + sum(priced_stock) + (machine or 0) if has_work else None
    supplier_total = supplier_stock + supplier_drilling if has_work else None
    layout_complete = not issues and not result["unplaced_blanks"]
    internal_complete = layout_complete and len(priced_stock) == len(rows) and machine is not None
    machine_label = "Machine" if machine is None else f"Machine · {_money(internal['machine_rate'])}/h"

    _comparison_table([
        (("Sheet stock", _money(sum(priced_stock) if priced_stock else None)),
         (f"Stock and cutting · ₪{external['sheet_rate']}/sheet", _money(supplier_stock))),
        ((f"Operator · {internal['operator_hours']} h × {_money(internal['operator_rate'])}",
          _money(operator) if has_work else "—"),
         (f"Drilling allowance · ₪{external['drilling_rate']}/part", _money(supplier_drilling))),
        ((machine_label, _money(machine) if machine is not None else "Rate needed"), None),
        (("Estimated cost", _estimate(internal_total, internal_complete)),
         ("Estimated cost", _estimate(supplier_total, layout_complete))),
    ])
    st.caption("Costs before VAT. Subcontractor pricing is a budget allowance.")
    missing_stock = sorted({
        f"{row['material']} ({row['thickness_mm']:g} mm)"
        for row in rows if row["sheets"] and row["stock_ex_vat"] is None
    })
    if missing_stock:
        st.warning(f"In-house subtotal needs sheet prices for {', '.join(missing_stock)}.")
    with st.expander("CNC time breakdown"):
        st.markdown(
            "| Operation | Minutes |\n| :--- | ---: |\n"
            + "\n".join(f"| {label} | {work[key]:.1f} |" for label, key in (
                ("Setup", "setup_minutes"), ("Load sheets", "load_minutes"),
                ("Unload parts and scrap", "unload_minutes"), ("Clean table", "cleanup_minutes"),
                ("Cutting", "cut_minutes"), ("Moves", "move_minutes"), ("Drilling", "drilling_minutes"),
                ("Tool changes", "tool_change_minutes"),
            ))
        )
    if issues:
        with st.expander("Layout issues"):
            for row in issues:
                st.text(f"{row['reference']}: {row['issue']}")


def _estimate(value, complete):
    if value is None or complete:
        return _money(value)
    return f"{_money(value)} (subtotal)"


@st.fragment
def render_labor_v1(*, company_id, run_id, estimate_id, object_id):
    st.markdown('<div class="object-detail-section-title">CNC</div>', unsafe_allow_html=True)
    if not run_id:
        _comparison_table(())
        st.info("Parts Check is not available for this object.")
        return
    identity = company_id, run_id, estimate_id, object_id
    if st.button("Calculate CNC", key=f"labor-v1-{estimate_id}-{object_id}"):
        with st.spinner("Calculating sheet CNC"):
            try:
                state = _calculate(get_supabase_client(), identity=identity)
            except Exception:
                _LOG.exception("Could not calculate Labor V1 for estimate %s", estimate_id)
                state = {"status": "read_failed"}
        st.session_state.labor_v1_result = (identity, state)
    active, state = st.session_state.get("labor_v1_result", (None, {}))
    if active != identity:
        _comparison_table(())
        return
    if state["status"] == "ready":
        _show_comparison(state["result"])
    else:
        _comparison_table(())
        messages = {
            "running": "Parts Check is running. Calculate again when it finishes.",
            "waiting_for_materials": "The Material Plan is not ready. Calculate again when it finishes.",
            "different_revision": "Parts Check and the Material Plan are on different revisions. Refresh the estimate and try again.",
            "failed": "Parts Check could not finish for this upload.",
            "unavailable": "Parts Check is not available for this object.",
            "read_failed": "CNC could not be calculated. Try again.",
        }
        st.info(messages[state["status"]])
