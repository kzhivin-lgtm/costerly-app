from __future__ import annotations

from pathlib import Path

import pytest

from screens.platform_admin import _dashboard_table
from use_cases.platform_admin import (
    PlatformAccess,
    company_file_fingerprint,
    company_operational_status,
    format_ai_cost,
    load_company_dashboard,
    load_platform_access,
    normalize_dashboard_row,
    record_authenticated_session,
    record_rfq_upload,
    require_platform_access,
)


ROOT = Path(__file__).resolve().parents[1]


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, data):
        self.data = data

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        return _Response(self.data)


class _RpcQuery:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return _Response(self.data)


class _Client:
    def __init__(self, *, staff=None, rpc_data=None):
        self.staff = staff or []
        self.rpc_data = rpc_data or []
        self.rpc_calls = []

    def table(self, name):
        assert name == "platform_staff"
        return _Query(self.staff)

    def rpc(self, name, params):
        self.rpc_calls.append((name, params))
        return _RpcQuery(self.rpc_data)


def _admin_client(*, rpc_data=None):
    return _Client(
        staff=[
            {
                "user_id": "user-1",
                "role": "platform_admin",
                "active": True,
            }
        ],
        rpc_data=rpc_data,
    )


def test_platform_access_requires_an_explicit_active_platform_role():
    assert load_platform_access(_Client(), "user-1") is None
    assert (
        load_platform_access(
            _Client(staff=[{"user_id": "user-1", "role": "owner", "active": True}]),
            "user-1",
        )
        is None
    )
    access = load_platform_access(_admin_client(), "user-1")
    assert access == PlatformAccess(user_id="user-1", role="platform_admin")


def test_platform_access_denial_is_server_side():
    with pytest.raises(PermissionError, match="Platform Admin"):
        require_platform_access(_Client(), "user-1")


def test_dashboard_uses_guarded_v2_rpc_and_validates_period():
    rows = [{"company_id": "company-a"}]
    client = _admin_client(rpc_data=rows)

    assert load_company_dashboard(
        client,
        requesting_user_id="user-1",
        days=30,
    ) == rows
    assert client.rpc_calls == [
        (
            "platform_admin_company_dashboard_v2",
            {"p_requesting_user_id": "user-1", "p_days": 30},
        )
    ]
    with pytest.raises(ValueError, match="period"):
        load_company_dashboard(client, requesting_user_id="user-1", days=31)


@pytest.mark.parametrize(
    ("value", "unpriced", "expected"),
    [
        ("0", 0, "0.00"),
        ("0.071", 0, "0.07"),
        ("1.25", 0, "1.25"),
        ("0", 2, "—"),
        ("0.071", 2, "0.07"),
    ],
)
def test_ai_cost_format_is_honest_about_unpriced_events(value, unpriced, expected):
    assert format_ai_cost(value, unpriced_events=unpriced) == expected


def test_file_fingerprint_is_stable_but_company_scoped():
    first = company_file_fingerprint("company-a", b"same file")
    assert first == company_file_fingerprint("company-a", b"same file")
    assert first != company_file_fingerprint("company-b", b"same file")
    assert "same file" not in first


def test_rfq_upload_returns_repeat_result_without_sending_file_content():
    client = _Client(rpc_data=[{"event_id": "event-1", "is_repeat": True}])

    assert record_rfq_upload(
        client,
        company_id="company-a",
        user_id="user-1",
        file_bytes=b"sensitive document",
    )
    name, params = client.rpc_calls[0]
    assert name == "record_product_usage_event"
    assert params["p_event_name"] == "rfq_uploaded"
    assert params["p_entity_fingerprint"] != "sensitive document"
    assert params["p_metadata"] == {}


def test_authenticated_session_is_company_scoped_and_content_free():
    client = _Client(rpc_data=[])

    record_authenticated_session(
        client,
        company_id="company-a",
        user_id="user-1",
        session_id="session-1",
    )
    name, params = client.rpc_calls[0]
    assert name == "record_product_usage_event"
    assert params["p_event_name"] == "authenticated_session_started"
    assert params["p_entity_fingerprint"] != "session-1"
    assert params["p_metadata"] == {}


def test_dashboard_escapes_company_name_and_omits_customer_content():
    markup = _dashboard_table(
        [
            {
                "company_name": '<script>alert("x")</script>',
                "account_stage": "paid",
                "users_count": 2,
                "active_days_7": 3,
                "active_days_30": 8,
                "files_uploaded": 4,
                "files_reuploaded": 1,
                "detection_runs": 4,
                "detection_cost_usd": "0.12",
                "detection_unpriced_events": 1,
                "estimation_calls": 10,
                "estimation_cost_usd": "1.40",
                "estimation_unpriced_events": 0,
                "price_source_runs": 3,
                "price_source_cost_usd": "0.03",
                "price_source_unpriced_events": 0,
                "pdfs_generated": 99,
                "total_ai_cost_usd": "1.55",
                "total_unpriced_events": 1,
                "failed_agent_events": 0,
                "file_name": "must-not-render.pdf",
                "source_content": "must-not-render",
            }
        ]
    )

    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup
    assert "must-not-render" not in markup
    assert "4 doc" in markup
    assert "0.12" in markup
    assert "10 calls" in markup
    assert "1.40" in markup
    assert "<td><span class=\"platform-admin-metric-count\">—</span></td>" in markup


def test_admin_screen_is_an_unfiltered_all_time_company_matrix():
    screen_source = (ROOT / "screens/platform_admin.py").read_text()

    assert "PERIOD_LABELS" not in screen_source
    assert "STAGE_LABELS" not in screen_source
    assert 'st.selectbox("Period"' not in screen_source
    assert '"Company stage"' not in screen_source
    assert "days=0" in screen_source
    assert "Admin data is temporarily unavailable" in screen_source


def test_admin_matrix_reuses_overhead_expenses_table_geometry():
    admin_styles = (ROOT / "styles/platform_admin.py").read_text()
    detail_styles = (ROOT / "styles/object_detail.py").read_text()

    for declaration in (
        "border: 1px solid rgba(42, 31, 44, 0.14);",
        "border-radius: 12px;",
        "box-shadow: 0 12px 24px rgba(0, 0, 0, 0.045);",
        "min-height: 42px;",
        "padding: 8px 12px;",
    ):
        assert declaration in detail_styles
        assert declaration in admin_styles
    assert ".platform-admin-table tbody tr:hover" not in admin_styles


def test_normalization_and_status_do_not_infer_customer_sentiment():
    row = normalize_dashboard_row({"account_stage": "unknown", "files_uploaded": 2})
    assert row["account_stage"] == "pilot"
    assert company_operational_status(row) == ("OK", "ok")
    assert company_operational_status({"failed_agent_events": 2}) == (
        "2 agent failures",
        "attention",
    )
    assert company_operational_status({}) == ("No activity", "neutral")
    assert company_operational_status({"price_source_runs": 1}) == ("OK", "ok")


def test_admin_migration_is_private_and_rpc_rechecks_platform_access():
    migration = (
        ROOT / "db/sql/2026_09_27_platform_admin_dashboard.sql"
    ).read_text()

    for table in (
        "platform_staff",
        "platform_company_accounts",
        "product_usage_events",
        "platform_admin_audit_events",
    ):
        assert f"create table if not exists public.{table}" in migration
        assert f"alter table public.{table} enable row level security" in migration
        assert f"revoke all on public.{table} from public, anon, authenticated" in migration
    assert "product_usage_events_daily_activity_idx" in migration
    assert "legacy_files_uploaded" in migration
    assert "e.event_name = 'rfq_uploaded'" in migration
    assert "rfq_runs_normalized as (" in migration
    assert "r.created_at::timestamptz" in migration
    assert "else null" in migration
    assert "security definer" in migration
    assert "Platform Admin access is required" in migration
    assert "Unsupported Admin dashboard period" in migration
    assert "with metric_window as (" in migration
    assert "with window as (" not in migration
    assert "grant execute on function public.platform_admin_company_dashboard" in migration
    assert "to service_role" in migration


def test_admin_session_migration_has_rolling_session_counts_and_private_rpc():
    migration = (
        ROOT / "db/sql/2026_09_27_platform_admin_sessions.sql"
    ).read_text()

    assert "authenticated_session_started" in migration
    assert "product_usage_events_session_idx" in migration
    assert "platform_admin_company_dashboard_v2" in migration
    assert "interval '7 days'" in migration
    assert "interval '30 days'" in migration
    assert "from public, anon, authenticated" in migration
    assert "to service_role" in migration


def test_admin_route_is_hidden_and_guarded_in_application_source():
    app_source = (ROOT / "app.py").read_text()
    auth_source = (ROOT / "state/company_auth.py").read_text()
    header_source = (ROOT / "ui/app_header.py").read_text()

    assert 'requested_screen == "admin"' in app_source
    assert 'screen == "admin" and platform_access is None' in app_source
    assert 'st.session_state.get("_platform_access_user_id")' in app_source
    assert "st.session_state._platform_access = platform_access" in app_source
    assert 'show_admin=platform_access is not None' in auth_source
    assert "if show_projects and show_admin" in header_source
    assert "elif show_admin:" in header_source


def test_company_admin_display_role_remains_non_removable():
    profile_source = (ROOT / "screens/company_profile.py").read_text()

    assert '"Company Admin" if row["role"] == "owner" else "Team Member"' in profile_source
    assert 'member.get("Role") != "Company Admin"' in profile_source


def test_platform_access_bootstrap_requires_an_existing_auth_user():
    tool_source = (ROOT / "tools/grant_platform_access.py").read_text()

    assert 'add_mutually_exclusive_group(required=True)' in tool_source
    assert 'choices=("platform_admin", "platform_viewer")' in tool_source
    assert 'SUPABASE_SERVICE_ROLE_KEY is required' in tool_source
    assert 'client.table("platform_staff").upsert' in tool_source


def test_company_stage_is_managed_from_a_trusted_tool():
    tool_source = (ROOT / "tools/set_company_stage.py").read_text()

    assert 'choices=("test", "pilot", "paid")' in tool_source
    assert 'SUPABASE_SERVICE_ROLE_KEY is required' in tool_source
    assert 'table("platform_company_accounts").upsert' in tool_source
