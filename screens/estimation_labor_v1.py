"""Labor V1 comparison for the open Object Detail card."""

from html import escape
from itertools import zip_longest
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


def _material(row):
    return f"{row['material']} · {row['thickness_mm']:g} mm"


def _format(row):
    return " × ".join(f"{d:g}" for d in row["size_mm"])


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


def _stock_label(row):
    return f"{_material(row)} · {_format(row)} mm"


def _show_comparison(result):
    work = result["work"]
    internal = result["in_house"]
    rows = internal["materials"]
    external = result["subcontractor"]
    issues = result["issues"]
    if not rows and not external and not issues:
        _comparison_table(())
        st.info("No sheet goods for CNC on this object.")
        return
    st.caption("Cutting and drilling · Costs before VAT · Shared sheets allocated by area")
    if issues:
        st.warning(f"{len(issues)} layout item(s) need review. The calculated scope is partial.")
    priced_stock = [row["stock_ex_vat"] for row in rows if row["stock_ex_vat"] is not None]
    machine = internal["machine_ex_vat"]
    operator = internal["operator_ex_vat"]
    priced = [row for row in external if row["bundle_ex_vat"] is not None]
    supplier_stock = sum(row["bundle_ex_vat"] for row in priced) if priced else None
    supplier_drilling = sum(row["machining_ex_vat"] for row in priced) if priced else None
    internal_total = operator + sum(priced_stock) + (machine or 0) if work["blank_count"] else None
    supplier_total = supplier_stock + supplier_drilling if priced else None
    internal_complete = not issues and len(priced_stock) == len(rows) and machine is not None
    supplier_complete = not issues and len(priced) == len(external)
    _comparison_table([
        (("Sheet share", _sheets(work["sheet_count"])),
         ("Sheet share", _sheets(sum(row["sheets"] for row in priced)) if priced else "—")),
        (("Parts with drilling", str(work["drilled_part_count"])),
         ("Parts with drilling", str(sum(row["drilled_parts"] for row in priced)) if priced else "—")),
        (("Machine time", f"{work['machine_minutes']:.1f} min"), None),
        (("Sheet stock", _money(sum(priced_stock) if priced_stock else None)),
         ("Stock and cutting", _money(supplier_stock))),
        (("Operator", _money(operator) if work["blank_count"] else "—"),
         ("Drilling allowance", _money(supplier_drilling))),
        (("Machine", _money(machine) if machine is not None else "Rate needed"), None),
        (("Estimated cost", _estimate(internal_total, internal_complete)),
         ("Estimated cost", _estimate(supplier_total, supplier_complete))),
    ])
    if len(priced) < len(external):
        st.write(f"Subcontractor quote needed for {len(external) - len(priced)} stock group(s).")
    with st.expander("Material and machining details"):
        if rows or external:
            shop_details = [
                (_stock_label(row), f"{_sheets(row['sheets'])} sheets · {row['cut_m']:.1f} m cut"
                 f" · {row['path_m']:.1f} m toolpath · {_money(row['stock_ex_vat'])}"
                 + (" (allowance)" if row["stock_is_assumed"] else ""))
                for row in rows
            ]
            vendor_details = [
                (_stock_label(row), f"{_sheets(row['sheets'])} sheets · {_money(row['bundle_ex_vat'])} stock and cutting"
                 f" · {_money(row['machining_ex_vat'])} drilling · {row['status']}")
                for row in external
            ]
            _comparison_table(zip_longest(shop_details, vendor_details))
        if issues:
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
