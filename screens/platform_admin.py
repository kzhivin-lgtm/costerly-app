from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from db.supabase_client import get_supabase_client
from state.session import set_screen
from styles.platform_admin import apply_platform_admin_css
from use_cases.platform_admin import (
    PlatformAccess,
    company_operational_status,
    format_ai_cost,
    load_company_dashboard,
    normalize_dashboard_row,
    record_dashboard_view,
    require_platform_access,
)


PERIOD_LABELS = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "All time": 0,
}
STAGE_LABELS = ("All companies", "Test", "Pilot", "Paid")


def _brand_mark() -> str:
    try:
        return Path("assets/brand/costelry_mark_indigo.svg").read_text()
    except OSError:
        return ""


def _open_profile() -> None:
    set_screen("account")


def _open_estimate() -> None:
    set_screen("upload")


def _metric_cell(count: int, cost: str, *, label: str) -> str:
    return (
        f'<span class="platform-admin-metric-count">{count} {escape(label)}</span>'
        f'<span class="platform-admin-metric-cost">{escape(cost)}</span>'
    )


def _dashboard_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return (
            '<div class="platform-admin-table-card">'
            '<div class="platform-admin-empty">No companies match these filters</div>'
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
        body.append(
            "<tr>"
            f'<td><span class="platform-admin-company">{escape(str(row.get("company_name") or "Untitled company"))}</span></td>'
            f'<td><span class="platform-admin-stage platform-admin-stage--{escape(stage)}">{escape(stage)}</span></td>'
            f'<td>{row["users_count"]}</td>'
            f'<td>{row["active_days_7"]} ({row["active_days_30"]})</td>'
            f'<td>{row["files_uploaded"]}</td>'
            f'<td>{row["files_reuploaded"]}</td>'
            f'<td>{_metric_cell(row["detection_runs"], detection_cost, label="documents")}</td>'
            f'<td>{_metric_cell(row["estimation_calls"], estimation_cost, label="calls")}</td>'
            f'<td>{_metric_cell(row["price_source_runs"], price_source_cost, label="sources")}</td>'
            '<td><span class="platform-admin-metric-count">—</span></td>'
            f'<td><span class="platform-admin-metric-count">{escape(total_cost)}</span></td>'
            f'<td><span class="platform-admin-status platform-admin-status--{status_kind}">{escape(status)}</span></td>'
            "</tr>"
        )

    return (
        '<div class="platform-admin-table-card">'
        '<div class="platform-admin-table-scroll">'
        '<table class="platform-admin-table">'
        "<colgroup>"
        '<col style="width:180px"><col style="width:78px"><col style="width:60px">'
        '<col style="width:92px"><col style="width:68px"><col style="width:82px">'
        '<col style="width:128px"><col style="width:128px"><col style="width:128px">'
        '<col style="width:60px"><col style="width:112px"><col style="width:108px">'
        "</colgroup>"
        "<thead><tr>"
        "<th>Company</th><th>Stage</th><th>Users</th>"
        "<th>Active days<br>7d (30d)</th><th>Files</th><th>Reuploads</th>"
        "<th>Detection</th><th>Estimation</th><th>Price Lists</th>"
        "<th>PDFs</th><th>Total AI cost</th><th>Status</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table></div></div>"
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

    if not st.session_state.get("_platform_admin_dashboard_audited"):
        record_dashboard_view(client, platform_user_id=str(access.user_id))
        st.session_state._platform_admin_dashboard_audited = True

    with st.container(key="platform_admin_controls"):
        period_column, stage_column, spacer = st.columns([1, 1, 3])
        with period_column:
            period_label = st.selectbox(
                "Period",
                options=list(PERIOD_LABELS),
                index=1,
                key="platform_admin_period",
            )
        with stage_column:
            stage_filter = st.selectbox(
                "Company stage",
                options=STAGE_LABELS,
                key="platform_admin_stage",
            )

    rows = load_company_dashboard(
        client,
        requesting_user_id=str(access.user_id),
        days=PERIOD_LABELS[period_label],
    )
    if stage_filter != "All companies":
        expected_stage = stage_filter.lower()
        rows = [
            row
            for row in rows
            if str(row.get("account_stage") or "pilot").lower() == expected_stage
        ]
    st.markdown(_dashboard_table(rows), unsafe_allow_html=True)
