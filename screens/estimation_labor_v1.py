"""Labor V1 comparison on the Objects screen."""

import json
import logging

import streamlit as st

from db.repositories import fetch_rfq_estimate_material_plan
from db.supabase_client import get_supabase_client
from use_cases.estimation_labor_v1 import (
    LABOR_VERSION, LAYOUT_VERSION, build_sheet_layout, calculate_labor_v1, sheet_layout_basis,
)
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
    company_id, run_id, estimate_id = identity
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
    source = plan.get("parts_check_source") or {}
    if not source or any(source.get(k) != report.get(k) for k in (
        "run_id", "estimate_id", "input_ids", "source_audit_sha256", "overlay_revision"
    )):
        return {"status": "different_revision"}
    layout = report.get("sheet_layout") or {}
    if layout.get("version") != LAYOUT_VERSION or layout.get("basis_sha256") != sheet_layout_basis(plan):
        layout = build_sheet_layout(report, plan)
        save_parts_sheet_layout(**params, report=report, layout=layout)
    return {"status": "ready", "result": calculate_labor_v1(layout, plan, machine_rate=_machine_rate(client, company_id))}


def _money(amount):
    return "—" if amount is None else f"₪{amount:,.2f}"


def _material(row):
    return f"{row['material']} · {row['thickness_mm']:g} mm"


def _format(row):
    return " × ".join(f"{d:g}" for d in row["size_mm"])


def _show_comparison(result):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    issues = result["issues"]
    if not rows and not issues:
        st.info("No sheet goods for CNC in this estimate.")
        return
    st.caption("Sheet goods · Cutting and drilling · Costs before VAT")
    if issues:
        st.warning(f"{len(issues)} layout item(s) need review. The calculated scope is partial.")
    left, right = st.columns(2)
    with left:
        st.markdown("**In-house CNC**")
        st.write(f"{work['sheet_count']} sheets · {work['blank_count']} blanks · {work['machine_minutes']:.1f} min")
        st.write(f"Operator {_money(internal['operator_ex_vat'])}")
        machine = internal["machine_ex_vat"]
        st.write(f"Machine {_money(machine)}" if machine is not None else "Machine rate needed in Company Profile.")
        stock = sum(row["stock_ex_vat"] or 0 for row in rows)
        st.write(f"Priced sheet stock {_money(stock)}")
        if rows and not issues and all(row["stock_ex_vat"] is not None for row in rows) and machine is not None:
            st.write(f"**Estimated CNC scope {_money(stock + internal['operator_ex_vat'] + machine)}**")
    with right:
        st.markdown("**CNC subcontractor**")
        priced = [row for row in external if row["bundle_ex_vat"] is not None]
        if priced:
            bundle = sum(row["bundle_ex_vat"] for row in priced)
            machining = sum(row["machining_ex_vat"] for row in priced)
            st.write(f"{sum(row['sheets'] for row in priced)} priced sheets · "
                     f"{sum(row['drilled_parts'] for row in priced)} parts with drilling allowance")
            st.write(f"Stock and cutting {_money(bundle)}")
            st.write(f"Drilling allowance {_money(machining)}")
            label = "Estimated CNC scope" if len(priced) == len(external) and not issues else "Priced subtotal"
            st.write(f"**{label} {_money(bundle + machining)}**")
        if len(priced) < len(external):
            st.write(f"Quote needed for {len(external) - len(priced)} stock group(s).")
    with st.expander("Material and machining details"):
        if rows:
            st.table([{"In-house stock": _material(row), "Format (mm)": _format(row), "Sheets": row["sheets"],
                       "Cut (m)": round(row["cut_m"], 1), "Toolpath (m)": round(row["path_m"], 1),
                       "Stock cost": _money(row["stock_ex_vat"]) + (" (allowance)" if row["stock_is_assumed"] else "")}
                      for row in rows])
            st.table([{"Supplier stock": _material(row), "Format (mm)": _format(row),
                       "Sheets": str(row["sheets"]) if row["sheets"] is not None else "—",
                       "Stock and cutting": _money(row["bundle_ex_vat"]),
                       "Drilling": _money(row["machining_ex_vat"]), "Basis": row["status"]} for row in external])
        if issues:
            st.table([{"Reference": row["reference"], "Needs review": row["issue"]} for row in issues])


def render_labor_v1(*, company_id, run_id, estimate_id):
    if not estimate_id or not run_id:
        return
    identity = company_id, run_id, estimate_id
    if st.button(f"Calculate {LABOR_VERSION}", key=f"labor-v1-{estimate_id}"):
        with st.spinner("Calculating sheet CNC"):
            try:
                state = _calculate(get_supabase_client(), identity=identity)
            except Exception:
                _LOG.exception("Could not calculate Labor V1 for estimate %s", estimate_id)
                state = {"status": "read_failed"}
        st.session_state.labor_v1_result = (identity, state)
    active, state = st.session_state.get("labor_v1_result", (None, {}))
    if active != identity:
        return
    st.markdown(f"#### Calculation · {LABOR_VERSION}")
    if state["status"] == "ready":
        _show_comparison(state["result"])
    else:
        messages = {
            "running": "Parts Check is running. Calculate again when it finishes.",
            "waiting_for_materials": "The Material Plan is not ready. Calculate again when it finishes.",
            "different_revision": "Parts Check and the Material Plan are on different revisions. Refresh the estimate and try again.",
            "failed": "Parts Check could not finish for this upload.",
            "unavailable": "Parts Check is not available for this upload.",
            "read_failed": "Labor V1 could not be calculated. Try again.",
        }
        st.info(messages[state["status"]])
