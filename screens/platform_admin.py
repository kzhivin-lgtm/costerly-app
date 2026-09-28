from __future__ import annotations

from html import escape
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st

from db.supabase_client import get_supabase_client
from state.session import set_screen
from styles.platform_admin import apply_platform_admin_css
from use_cases.platform_admin import (
    PlatformAccess,
    company_operational_status,
    format_ai_cost,
    load_company_dashboard,
    load_manufacturing_parameter_library,
    normalize_dashboard_row,
    record_dashboard_view,
    require_platform_access,
)
from use_cases.manufacturing_parameters import MANUFACTURING_PARAMETER_DEFINITIONS

LOGGER = logging.getLogger(__name__)

ADMIN_VIEWS = {"companies", "cnc_laser"}
MANUFACTURING_SECTIONS = (
    (
        "CNC Router",
        "In-house",
        "cnc_router_in_house",
        "Internal machining time and cost from routing, drilling, setup, machine capacity and attendance",
    ),
    (
        "CNC Router",
        "Subcontractor",
        "cnc_router_subcontractor",
        "Supplier charges, included work, minimum order, delivery and rush conditions",
    ),
    (
        "Sheet Laser",
        "In-house",
        "sheet_laser_in_house",
        "Internal cutting time and cost from speed, piercing, gas, energy, setup and attendance",
    ),
    (
        "Sheet Laser",
        "Subcontractor",
        "sheet_laser_subcontractor",
        "Named provider model, setup, cutting basis, included material, minimum order and delivery",
    ),
)


def _brand_mark() -> str:
    try:
        return Path("assets/brand/costelry_mark_indigo.svg").read_text()
    except OSError:
        return ""


def _open_profile() -> None:
    set_screen("account")


def _open_estimate() -> None:
    set_screen("upload")


def _set_admin_view(view: str) -> None:
    st.session_state.platform_admin_view = view if view in ADMIN_VIEWS else "companies"


def _metric_cell(count: int, cost: str, *, label: str) -> str:
    displayed_cost = cost if cost == "—" else f"${cost}"
    return (
        f'<span class="platform-admin-metric-count">{count} {escape(label)}</span>'
        f'<span class="platform-admin-metric-cost">{escape(displayed_cost)}</span>'
    )


def _dashboard_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return (
            '<div class="platform-admin-table-card">'
            '<div class="platform-admin-empty">No companies yet</div>'
            "</div>"
        )

    body = []
    for raw_row in rows:
        row = normalize_dashboard_row(raw_row)
        stage = row["account_stage"]
        status, status_kind = company_operational_status(row)
        detection_cost = format_ai_cost(
            row.get("detection_cost_usd"),
            unpriced_events=row["detection_unpriced_events"],
        )
        estimation_cost = format_ai_cost(
            row.get("estimation_cost_usd"),
            unpriced_events=row["estimation_unpriced_events"],
        )
        price_source_cost = format_ai_cost(
            row.get("price_source_cost_usd"),
            unpriced_events=row["price_source_unpriced_events"],
        )
        total_cost = format_ai_cost(
            row.get("total_ai_cost_usd"),
            unpriced_events=row["total_unpriced_events"],
        )
        displayed_total_cost = total_cost if total_cost == "—" else f"${total_cost}"
        body.append(
            "<tr>"
            f'<td><span class="platform-admin-company">{escape(str(row.get("company_name") or "Untitled company"))}</span></td>'
            f'<td><span class="platform-admin-stage platform-admin-stage--{escape(stage)}">{escape(stage)}</span></td>'
            f'<td>{row["users_count"]}</td>'
            f'<td>{row["active_days_7"]} ({row["active_days_30"]})</td>'
            f'<td>{row["files_uploaded"]}</td>'
            f'<td>{row["files_reuploaded"]}</td>'
            f'<td>{_metric_cell(row["detection_runs"], detection_cost, label="doc")}</td>'
            f'<td>{_metric_cell(row["estimation_calls"], estimation_cost, label="calls")}</td>'
            f'<td>{_metric_cell(row["price_source_runs"], price_source_cost, label="sources")}</td>'
            '<td><span class="platform-admin-metric-count">—</span></td>'
            f'<td><span class="platform-admin-metric-count">{escape(displayed_total_cost)}</span></td>'
            f'<td><span class="platform-admin-status platform-admin-status--{status_kind}">{escape(status)}</span></td>'
            "</tr>"
        )

    return (
        '<div class="platform-admin-table-card">'
        '<div class="platform-admin-table-scroll">'
        '<table class="platform-admin-table">'
        "<colgroup>"
        '<col style="width:174px"><col style="width:66px"><col style="width:52px">'
        '<col style="width:82px"><col style="width:54px"><col style="width:72px">'
        '<col style="width:92px"><col style="width:92px"><col style="width:92px">'
        '<col style="width:50px"><col style="width:76px"><col style="width:116px">'
        "</colgroup>"
        "<thead><tr>"
        "<th>Company</th><th>Stage</th><th>Users</th>"
        "<th>Sessions<br>7d (30d)</th><th>Files</th><th>Repeat files</th>"
        "<th>Detection</th><th>Estimation</th><th>Price Lists</th>"
        "<th>PDFs</th><th>AI cost</th><th>Status</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table></div></div>"
    )


def _display_decimal(value: Any) -> str:
    if value in (None, ""):
        return "—"
    text = str(value)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _parameter_scope(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, label in (
        ("region", "Region"),
        ("material_family", "Material"),
        ("machine_class", "Machine"),
        ("object_family", "Object"),
    ):
        value = str(row.get(key) or "").strip()
        if value:
            parts.append(f"{label}: {value}")
    thickness_min = row.get("thickness_min_mm")
    thickness_max = row.get("thickness_max_mm")
    if thickness_min is not None or thickness_max is not None:
        low = _display_decimal(thickness_min)
        high = _display_decimal(thickness_max)
        parts.append(f"Thickness: {low} to {high} mm")
    qualifiers = row.get("qualifiers") or {}
    if isinstance(qualifiers, dict):
        for key, value in sorted(qualifiers.items()):
            if value not in (None, "", [], {}):
                parts.append(f"{str(key).replace('_', ' ').title()}: {value}")
    return "; ".join(parts) or "All supported scope"


def _source_markup(row: dict[str, Any]) -> str:
    name = escape(str(row.get("source_name") or "Source"))
    url = str(row.get("source_url") or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return (
            f'<a class="platform-admin-source-link" href="{escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">{name}</a>'
        )
    return name


def _manufacturing_parameter_table(rows: list[dict[str, Any]]) -> str:
    rendered_rows: list[str] = []
    for row in rows:
        placeholder = bool(row.get("_placeholder"))
        parameter_name = str(row.get("_label") or row.get("parameter_key") or "")
        raw_code = str(row.get("parameter_key") or "")
        parameter_markup = (
            f'<span class="platform-admin-parameter-name">{escape(parameter_name)}</span>'
            f'<span class="platform-admin-parameter-code">{escape(raw_code)}</span>'
        )
        if placeholder:
            rendered_rows.append(
                '<tr class="platform-admin-parameter-placeholder">'
                f"<td>{parameter_markup}</td>"
                f'<td>{escape(str(row.get("_scope_hint") or "Required parameter"))}</td>'
                "<td>—</td><td>—</td><td>—</td>"
                f'<td>{escape(str(row.get("unit") or "—"))}</td>'
                "<td>—</td><td>—</td><td>—</td>"
                '<td><span class="platform-admin-parameter-missing">Not configured</span></td>'
                "<td>—</td>"
                "</tr>"
            )
            continue
        rendered_rows.append(
            "<tr>"
            f"<td>{parameter_markup}</td>"
            f'<td>{escape(_parameter_scope(row))}</td>'
            f'<td>{escape(_display_decimal(row.get("value_low")))}</td>'
            f'<td>{escape(_display_decimal(row.get("value_typical")))}</td>'
            f'<td>{escape(_display_decimal(row.get("value_high")))}</td>'
            f'<td>{escape(str(row.get("unit") or "—"))}</td>'
            f'<td>{_source_markup(row)}</td>'
            f'<td>{escape(str(row.get("source_date") or "—"))}</td>'
            f'<td>{escape(_display_decimal(row.get("confidence")))}</td>'
            f'<td>{escape(str(row.get("status") or "—").title())}</td>'
            f'<td>{escape(str(row.get("version") or "—"))}</td>'
            "</tr>"
        )
    body = "".join(rendered_rows)
    return (
        '<div class="platform-admin-table-card platform-admin-parameter-card">'
        '<div class="platform-admin-table-scroll">'
        '<table class="platform-admin-table platform-admin-parameter-table">'
        "<colgroup>"
        '<col style="width:240px"><col style="width:280px">'
        '<col style="width:78px"><col style="width:78px"><col style="width:78px">'
        '<col style="width:92px"><col style="width:150px"><col style="width:108px">'
        '<col style="width:88px"><col style="width:118px"><col style="width:70px">'
        "</colgroup>"
        "<thead><tr>"
        "<th>Parameter</th><th>Scope</th><th>Low</th><th>Typical</th><th>High</th>"
        "<th>Unit</th><th>Source</th><th>Source date</th><th>Confidence</th>"
        "<th>Status</th><th>Version</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div></div>"
    )


def _parameter_rows_for_route(
    calculator: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    definitions = MANUFACTURING_PARAMETER_DEFINITIONS[calculator]
    definition_by_key = {definition.key: definition for definition in definitions}
    actual_by_key: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        actual_by_key.setdefault(str(row.get("parameter_key") or ""), []).append(row)
    rendered: list[dict[str, Any]] = []
    for definition in definitions:
        matches = actual_by_key.pop(definition.key, [])
        if matches:
            rendered.extend({**row, "_label": definition.label} for row in matches)
        else:
            rendered.append(
                {
                    "_placeholder": True,
                    "_label": definition.label,
                    "_scope_hint": definition.scope_hint,
                    "parameter_key": definition.key,
                    "unit": definition.unit,
                }
            )
    for key in sorted(actual_by_key):
        rendered.extend(actual_by_key[key])
    return rendered


def _render_manufacturing_library(client, access, platform_access: PlatformAccess) -> None:
    st.subheader("CNC / Laser")
    st.caption("Four independent cost models. Missing values remain visible and are never guessed")
    try:
        rows = load_manufacturing_parameter_library(
            client,
            requesting_user_id=str(access.user_id),
            include_history=True,
        )
    except Exception:
        LOGGER.exception("CNC / Laser parameter library failed to load")
        st.error("CNC / Laser parameters are temporarily unavailable. Try again in a moment")
        return
    by_calculator: dict[str, list[dict[str, Any]]] = {
        calculator: []
        for _process, _route, calculator, _description in MANUFACTURING_SECTIONS
    }
    archived_by_calculator: dict[str, list[dict[str, Any]]] = {
        calculator: []
        for _process, _route, calculator, _description in MANUFACTURING_SECTIONS
    }
    for row in rows:
        calculator = str(row.get("calculator") or "")
        if calculator in by_calculator:
            target = (
                archived_by_calculator
                if str(row.get("status") or "") == "archived"
                else by_calculator
            )
            target[calculator].append(row)
    current_process = ""
    for process, route, calculator, description in MANUFACTURING_SECTIONS:
        if process != current_process:
            st.markdown(f'<h2 class="platform-admin-process-title">{escape(process)}</h2>', unsafe_allow_html=True)
            current_process = process
        st.markdown(f'<h3 class="platform-admin-route-title">{escape(route)}</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<p class="platform-admin-route-description">{escape(description)}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            _manufacturing_parameter_table(
                _parameter_rows_for_route(calculator, by_calculator[calculator])
            ),
            unsafe_allow_html=True,
        )
        archived = archived_by_calculator[calculator]
        if archived:
            with st.expander(f"Previous versions ({len(archived)})"):
                st.markdown(
                    _manufacturing_parameter_table(
                        _parameter_rows_for_route(calculator, archived)
                    ),
                    unsafe_allow_html=True,
                )


def render_platform_admin_screen(access, platform_access: PlatformAccess) -> None:
    """Render the read-only cross-company overview."""
    apply_platform_admin_css()
    st.markdown(
        '<div class="platform-admin-active" style="display:none"></div>',
        unsafe_allow_html=True,
    )
    client = get_supabase_client()
    fresh = require_platform_access(client, str(access.user_id))
    if fresh != platform_access:
        raise PermissionError("Platform Admin access changed. Please refresh.")

    header_left, header_right = st.columns([3.6, 2])
    with header_left:
        st.markdown(
            f'<div class="platform-admin-heading"><div class="platform-admin-mark">{_brand_mark()}</div>'
            "<h1>Admin</h1></div>",
            unsafe_allow_html=True,
        )
    with header_right:
        with st.container(key="platform_admin_actions"):
            profile, estimate, sign_out_control = st.columns(3)
            with profile:
                st.button(
                    "Profile",
                    key="admin_to_profile",
                    use_container_width=True,
                    on_click=_open_profile,
                )
            with estimate:
                st.button(
                    "New Estimate",
                    key="admin_to_upload",
                    use_container_width=True,
                    on_click=_open_estimate,
                )
            with sign_out_control:
                from state.company_auth import sign_out

                st.button(
                    "Sign out",
                    key="company_sign_out",
                    use_container_width=True,
                    on_click=sign_out,
                )

    current_view = str(st.session_state.get("platform_admin_view") or "companies")
    if current_view not in ADMIN_VIEWS:
        current_view = "companies"
    with st.container(key="platform_admin_sections"):
        companies_column, manufacturing_column, spacer = st.columns([1, 1, 5])
        with companies_column:
            st.button(
                "Companies",
                key="platform_admin_companies_view",
                type="primary" if current_view == "companies" else "secondary",
                use_container_width=True,
                on_click=_set_admin_view,
                args=("companies",),
            )
        with manufacturing_column:
            st.button(
                "CNC / Laser",
                key="platform_admin_cnc_laser_view",
                type="primary" if current_view == "cnc_laser" else "secondary",
                use_container_width=True,
                on_click=_set_admin_view,
                args=("cnc_laser",),
            )

    if current_view == "cnc_laser":
        _render_manufacturing_library(client, access, platform_access)
        return

    if not st.session_state.get("_platform_admin_dashboard_audited"):
        record_dashboard_view(client, platform_user_id=str(access.user_id))
        st.session_state._platform_admin_dashboard_audited = True

    try:
        rows = load_company_dashboard(
            client,
            requesting_user_id=str(access.user_id),
            days=0,
        )
    except Exception:
        LOGGER.exception("Platform Admin company dashboard failed to load")
        st.error("Admin data is temporarily unavailable. Try again in a moment")
        return
    st.markdown(_dashboard_table(rows), unsafe_allow_html=True)
