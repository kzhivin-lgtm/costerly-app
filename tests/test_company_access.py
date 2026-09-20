from __future__ import annotations

import base64
from contextlib import contextmanager
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from postgrest.exceptions import APIError
from streamlit.testing.v1 import AppTest

from db.company_access import assert_company_owner, assert_estimate_owned, assert_run_owned
from state import company_auth
from screens import company_profile
from ui import company_metrics_view
from use_cases import pricing
from use_cases.invite_links import (
    DEFAULT_PUBLIC_APP_URL,
    create_one_company_link,
    invite_token_hash,
    invite_url,
    new_invite_token,
    public_app_url,
)
from use_cases.email_addresses import is_valid_email_address
from use_cases.rfq_processing import assign_server_run_id


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def execute(self):
        return type("Response", (), {"data": self.rows})()


class _Client:
    def __init__(self, rows):
        self.rows = rows
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return _Query(self.rows)


@pytest.mark.parametrize("guard,table", [
    (assert_run_owned, "rfq_runs"),
    (assert_estimate_owned, "rfq_estimates"),
])
def test_company_record_guard_accepts_only_own_company(guard, table):
    client = _Client([{"company_id": "company-a"}])
    guard(client, "record-1", "company-a")
    assert client.table_name == table
    with pytest.raises(PermissionError):
        guard(client, "record-1", "company-b")
    with pytest.raises(PermissionError):
        guard(_Client([]), "missing", "company-a")


def test_company_auth_is_opt_in_until_database_switch(monkeypatch):
    monkeypatch.setattr(company_auth, "get_optional_secret", lambda name, default=None: default)
    assert company_auth.company_auth_enabled() is False
    monkeypatch.setattr(company_auth, "get_optional_secret", lambda name, default=None: "true")
    assert company_auth.company_auth_enabled() is True


def test_browser_session_restores_and_persists_tab_tokens(monkeypatch):
    st = company_auth.st
    st.session_state.clear()
    st.session_state._browser_auth_read_request = "read-1"
    monkeypatch.setattr(
        company_auth,
        "browser_session_exchange",
        lambda **_kwargs: {
            "status": "ready",
            "requestId": "read-1",
            "session": {
                "access_token": "access-1",
                "refresh_token": "refresh-1",
                "expires_at": 123,
            },
        },
    )
    promoted = []
    monkeypatch.setattr(company_auth, "write_fast_resume_cookie", promoted.append)
    monkeypatch.setattr(company_auth, "seal_resume_session", lambda **_kwargs: "sealed")

    assert company_auth.sync_browser_auth_session() is True
    assert st.session_state.auth_access_token == "access-1"
    assert st.session_state.auth_refresh_token == "refresh-1"
    assert st.session_state.auth_expires_at == 123
    assert st.session_state._browser_auth_initialized is True
    assert st.session_state._browser_auth_sync_outcome == "browser_session_restored"
    assert st.session_state._fast_resume_outcome == "promoted_from_browser"
    assert promoted == ["sealed"]

    class Session:
        access_token = "access-2"
        refresh_token = "refresh-2"
        expires_at = 456

    company_auth._store_auth_session(Session())
    pending = st.session_state._browser_auth_pending
    assert pending["action"] == "store"
    assert pending["session"] == {
        "access_token": "access-2",
        "refresh_token": "refresh-2",
        "expires_at": 456,
    }


def test_browser_session_does_not_render_component_after_bootstrap(monkeypatch):
    st = company_auth.st
    st.session_state.clear()
    st.session_state._browser_auth_initialized = True

    def unexpected_exchange(**_kwargs):
        raise AssertionError("Initialized sessions must not render the browser component")

    monkeypatch.setattr(company_auth, "browser_session_exchange", unexpected_exchange)

    assert company_auth.sync_browser_auth_session() is True


@pytest.mark.parametrize("action", ["store", "clear"])
def test_browser_session_write_commands_do_not_wait_for_callback(monkeypatch, action):
    st = company_auth.st
    st.session_state.clear()
    st.session_state._browser_auth_pending = {
        "action": action,
        "request_id": f"{action}-1",
        "session": {"access_token": "a", "refresh_token": "r"}
        if action == "store"
        else None,
    }
    calls = []
    monkeypatch.setattr(
        company_auth,
        "browser_session_exchange",
        lambda **kwargs: calls.append(kwargs),
    )

    assert company_auth.sync_browser_auth_session() is True
    assert calls[0]["action"] == action
    assert "_browser_auth_pending" not in st.session_state
    assert st.session_state._browser_auth_initialized is True


def test_browser_session_uses_session_storage_and_hidden_sidebar_transport():
    root = Path(__file__).parents[1]
    component_html = (root / "ui/browser_session_component/index.html").read_text()

    assert "window.sessionStorage" in component_html
    assert "window.localStorage" not in component_html
    assert 'if (args.action === "read")' in component_html
    assert "__Host-costerly-resume-v1" in component_html
    assert "SameSite=None; Partitioned" in component_html
    assert "Max-Age=0" in component_html


def test_fast_resume_skips_browser_component(monkeypatch):
    st = company_auth.st
    st.session_state.clear()
    monkeypatch.setattr(
        company_auth,
        "restore_resume_session",
        lambda _cookies: (
            "restored",
            {
                "access_token": "access-fast",
                "refresh_token": "refresh-fast",
                "expires_at": 789,
            },
        ),
    )
    monkeypatch.setattr(
        company_auth,
        "browser_session_exchange",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("Fast Resume must skip the browser component")
        ),
    )

    assert company_auth.sync_browser_auth_session() is True
    assert st.session_state.auth_access_token == "access-fast"
    assert st.session_state.auth_refresh_token == "refresh-fast"
    assert st.session_state._browser_auth_initialized is True
    assert st.session_state._browser_auth_sync_outcome == "fast_resume_restored"
    assert st.session_state._fast_resume_outcome == "restored"


def test_browser_session_component_executes_inside_sidebar(monkeypatch):
    from ui import browser_session

    class Sidebar:
        active = False

        def __enter__(self):
            self.active = True

        def __exit__(self, *_args):
            self.active = False

    sidebar = Sidebar()

    def component(**_kwargs):
        assert sidebar.active is True
        return '{"status":"ready","requestId":"read-1","session":null}'

    monkeypatch.setattr(browser_session.st, "sidebar", sidebar)
    monkeypatch.setattr(browser_session, "_SESSION_COMPONENT", component)

    result = browser_session.browser_session_exchange(
        action="read", request_id="read-1"
    )
    assert result == {
        "status": "ready",
        "requestId": "read-1",
        "session": None,
    }


def _render_login_test():
    from state import company_auth

    company_auth.render_login_or_signup(None)


def test_sign_in_submit_uses_native_pre_render_callback(monkeypatch):
    calls = []
    monkeypatch.setattr(
        company_auth,
        "sign_in",
        lambda email, password: calls.append((email, password)),
    )

    app = AppTest.from_function(_render_login_test).run()
    app.text_input(key="login_email").set_value("owner@example.com")
    app.text_input(key="login_password").set_value("Password123")
    next(button for button in app.button if button.label == "Sign in").click().run()

    assert calls == [("owner@example.com", "Password123")]
    assert not app.exception


def test_sign_in_callback_returns_failure_to_login_form(monkeypatch):
    monkeypatch.setattr(
        company_auth,
        "sign_in",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("unavailable")),
    )

    app = AppTest.from_function(_render_login_test).run()
    app.text_input(key="login_email").set_value("owner@example.com")
    app.text_input(key="login_password").set_value("wrong")
    next(button for button in app.button if button.label == "Sign in").click().run()

    assert [error.value for error in app.error] == [
        "Could not sign in. Check your email and password."
    ]
    assert not app.exception


def test_browser_policy_migration_removes_anonymous_cost_access():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_15_company_access_foundation.sql").read_text()
    assert "drop policy if exists rfq_estimate_pricing_overrides_anon_update" in sql
    assert "revoke all on public.rfq_estimate_pricing_overrides from anon" in sql
    assert "with (security_invoker = true)" in sql
    assert "revoke all on public.rfq_object_estimate_progress_public from anon" in sql
    assert "create table if not exists public.company_creation_invites" in sql
    assert "create table if not exists public.company_join_links" in sql
    assert "where token_hash = p_token_hash and used_at is null" in sql
    assert "for update" in sql  # One-use creation is atomic.
    assert "where l.join_token = p_join_token" in sql  # Company link is reusable.
    assert "expires_at" not in sql
    assert "p_email" not in sql
    assert "insert into public.companies(company_id, company_name)" in sql
    assert "insert into public.companies(company_id, display_name)" not in sql
    assert "company_members_one_owner_idx" in sql
    assert "where role = 'owner'" in sql
    assert "values (p_user_id, p_company_id, 'owner')" in sql
    assert "values (p_user_id, v_company_id, 'member')" in sql


def test_first_sql_stage_only_adds_isolated_objects():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_15_company_access_stage1_strict_additive.sql").read_text().lower()
    assert "create table public.company_members" in sql
    assert "create table public.company_creation_invites" in sql
    assert "create table public.company_join_links" in sql
    assert "to_regclass('public.company_members') is not null" in sql
    assert "alter table public.companies" not in sql
    assert "public.rfq_" not in sql
    for operation in ("drop ", "revoke ", "create or replace", "delete ", "cascade"):
        assert operation not in sql


def test_second_sql_stage_creates_locked_down_invite_functions_only():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_15_company_access_stage2_invite_rpcs.sql").read_text().lower()
    assert "to_regprocedure('public.create_company_from_invite(text,uuid,text,text)')" in sql
    assert "to_regprocedure('public.join_company_by_link(text,uuid)')" in sql
    assert "security invoker" in sql
    assert "where token_hash = p_token_hash and used_at is null" in sql
    assert "for update" in sql
    assert "values (p_user_id, p_company_id, 'owner')" in sql
    assert "values (p_user_id, v_company_id, 'member')" in sql
    assert "grant execute on function public.join_company_by_link" in sql
    assert "create or replace" not in sql
    assert "alter table public.rfq_" not in sql


def test_only_creator_role_can_edit_company_wide_settings():
    assert_company_owner(_Client([{"company_id": "company-a", "role": "owner"}]), "user-1", "company-a")
    with pytest.raises(PermissionError):
        assert_company_owner(_Client([{"company_id": "company-a", "role": "member"}]), "user-2", "company-a")
    with pytest.raises(PermissionError):
        assert_company_owner(_Client([{"company_id": "company-b", "role": "owner"}]), "user-3", "company-a")


def test_company_creation_uses_three_digit_ids_and_retries_unique_collision(monkeypatch):
    access = company_auth.CompanyAccess("user-1", "owner@example.com", None, None, "token")
    monkeypatch.setattr(company_auth, "current_company_access", lambda: access)
    generated = iter([0, 1])
    monkeypatch.setattr(company_auth.secrets, "randbelow", lambda _n: next(generated))
    sent = []

    class Query:
        def __init__(self, values):
            sent.append(values)

        def execute(self):
            if len(sent) == 1:
                raise APIError({"code": "23505", "message": "duplicate key value violates unique constraint companies_pkey"})
            return type("Response", (), {"data": sent[-1]["p_company_id"]})()

    class Client:
        def rpc(self, name, values):
            assert name == "create_company_from_invite"
            return Query(values)

    monkeypatch.setattr(company_auth, "_server_client", lambda: Client())
    result = company_auth.create_company_for_user(access, "Workshop", new_invite_token())
    assert result == "002"
    assert [values["p_company_id"] for values in sent] == ["001", "002"]
    assert all(len(values["p_company_id"]) == 3 for values in sent)


def test_company_creation_does_not_retry_noncollision_database_error(monkeypatch):
    access = company_auth.CompanyAccess("user-1", "owner@example.com", None, None, "token")
    monkeypatch.setattr(company_auth, "current_company_access", lambda: access)

    class Query:
        def execute(self):
            raise APIError({"code": "23514", "message": "unexpected check constraint"})

    class Client:
        def rpc(self, *_args):
            return Query()

    monkeypatch.setattr(company_auth, "_server_client", lambda: Client())
    with pytest.raises(APIError):
        company_auth.create_company_for_user(access, "Workshop", new_invite_token())


def test_profile_contacts_save_only_for_owner(monkeypatch):
    access = company_auth.CompanyAccess("user-1", "owner@example.com", "company-a", "owner", "token")
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = []
    stored_role = ["owner"]

    class Query:
        def __init__(self, table):
            self.table = table

        def select(self, *_args):
            return self

        def eq(self, *_args):
            return self

        def limit(self, *_args):
            return self

        def update(self, values):
            writes.append((self.table, values))
            return self

        def execute(self):
            rows = ([{"company_id": "company-a", "role": stored_role[0]}]
                    if self.table == "company_members" else [{"company_id": "company-a"}])
            return type("Response", (), {"data": rows})()

    class Client:
        def table(self, name):
            return Query(name)

    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: Client())
    company_profile.save_company_contacts(access, " Workshop ", " hello@example.com ", " +1 555 ")
    assert writes == [("companies", {"company_name": "Workshop", "public_email": "hello@example.com", "public_phone": "+1 555"})]

    stored_role[0] = "member"
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: company_auth.CompanyAccess("user-1", "owner@example.com", "company-a", "member", "token"))
    with pytest.raises(PermissionError):
        company_profile.save_company_contacts(access, "Changed", "", "")
    assert len(writes) == 1


def test_member_cannot_get_company_join_link():
    member = company_auth.CompanyAccess("user-2", "member@example.com", "company-a", "member", "token")
    with pytest.raises(PermissionError):
        company_auth.company_join_url(member)


def test_company_account_traces_lazy_profile_import_and_render(monkeypatch):
    events = []

    class Trace:
        @contextmanager
        def span(self, name):
            events.append(("start", name))
            yield
            events.append(("end", name))

    rendered = []
    monkeypatch.setattr(
        company_profile,
        "render_company_profile",
        lambda access, *, trace=None: rendered.append((access, trace)),
    )
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    trace = Trace()

    company_auth.render_company_account(access, trace=trace)

    assert events == [
        ("start", "server.company_profile_import"),
        ("end", "server.company_profile_import"),
        ("start", "server.company_profile_render"),
        ("end", "server.company_profile_render"),
    ]
    assert rendered == [(access, trace)]


def test_owner_join_link_uses_public_application_not_localhost(monkeypatch):
    owner = company_auth.CompanyAccess("user-1", "owner@example.com", "002", "owner", "token")
    join_token = new_invite_token()
    monkeypatch.setattr(company_auth, "current_company_access", lambda: owner)
    monkeypatch.setattr(company_auth, "_server_client", lambda: _Client([{"join_token": join_token}]))
    monkeypatch.setattr(company_auth, "get_optional_secret", lambda *_args: None)
    url = company_auth.company_join_url(owner)
    assert url.startswith(f"{DEFAULT_PUBLIC_APP_URL}join/")
    assert "localhost" not in url and "127.0.0.1" not in url


def _render_profile_test():
    import streamlit as st
    from screens.company_profile import render_company_profile
    from state.company_auth import CompanyAccess

    role = st.session_state["test_profile_role"]
    render_company_profile(CompanyAccess("user-1", "owner@example.com", "company-a", role, "token"))


def _render_upload_header_controls_test():
    import streamlit as st

    from ui.app_header import render_account_header_controls

    def open_profile():
        st.session_state["header_profile_opened"] = True

    render_account_header_controls(
        on_profile=open_profile,
        on_sign_out=lambda: None,
        show_projects=True,
    )


def test_upload_dashboard_has_compact_centered_navigation_and_preserves_logo():
    app = AppTest.from_function(_render_upload_header_controls_test).run()

    assert not app.exception
    assert [button.label for button in app.button] == ["Projects", "Profile", "Sign out"]
    assert app.button[0].disabled is True

    app.button[1].click().run()
    assert app.session_state["header_profile_opened"] is True

    css = (Path(__file__).parents[1] / "styles/upload.py").read_text()
    assert "top: calc(var(--app-header-top) - var(--app-content-top) - 16px);" in css
    assert "order: 10 !important;" in css
    assert "order: 20 !important;" in css
    assert "order: 30 !important;" in css
    assert "width: 340px !important;" in css
    assert "margin: 48px auto 32px !important;" in css
    assert "margin-top: 23px;" in css
    assert "height: 36px !important;" in css
    assert "padding: 0 10px !important;" in css
    assert '[data-testid="stVerticalBlock"]:has(> [data-testid="stLayoutWrapper"] .st-key-costerly_header_controls)' in css
    assert "gap: 0 !important;" in css
    assert "font-size: 24px;" in css


def test_upload_to_profile_navigation_runs_before_render_without_explicit_rerun():
    header_source = Path("ui/app_header.py").read_text()
    auth_source = Path("state/company_auth.py").read_text()
    button_source = header_source.split('"Profile"', 1)[1].split(")", 1)[0]
    control_source = auth_source.split("def render_account_control", 1)[1].split(
        "def render_company_account", 1
    )[0]

    assert "on_click=on_profile" in button_source
    assert "on_profile=_open_company_account" in control_source
    assert "st.rerun" not in control_source


@pytest.mark.parametrize("role", ["owner", "member"])
def test_company_profile_has_six_tabs_and_owner_only_controls(monkeypatch, role):
    calls = {"profile": 0, "members": 0, "metrics": 0, "employees": 0}

    def load_profile(_access):
        calls["profile"] += 1
        return {"company_name": "Workshop", "public_email": "", "public_phone": ""}

    def load_members(_access):
        calls["members"] += 1
        return [{"Email": "owner@example.com", "Role": "Owner"}]

    def load_metrics(_access):
        calls["metrics"] += 1
        return {"vat_percent": 18}, {}

    def load_employees(_access):
        calls["employees"] += 1
        return []

    monkeypatch.setattr(company_profile, "load_company_profile", load_profile)
    monkeypatch.setattr(company_profile, "load_company_members", load_members)
    monkeypatch.setattr(
        company_profile,
        "load_company_metrics",
        load_metrics,
    )
    monkeypatch.setattr(company_profile, "load_company_employees", load_employees)
    monkeypatch.setattr(company_auth, "company_join_url", lambda _access: "https://example.com/join/token")
    app = AppTest.from_function(_render_profile_test)
    app.session_state["test_profile_role"] = role
    app.run()
    assert not app.exception
    assert [tab.label for tab in app.get("tab")] == [
        "Overhead Expenses", "Labor Costs", "Price Lists", "Contacts", "Bank Details", "Users",
    ]
    assert any(button.label == "Projects" and button.disabled for button in app.button)
    assert any(button.label == "New Estimate" for button in app.button)
    assert any(button.label == "Sign out" for button in app.button)
    assert not any(
        button.label in {"Save Contacts", "Save Bank Details"}
        for button in app.button
    )
    assert calls == {"profile": 0, "members": 0, "metrics": 1, "employees": 0}
    metrics_markup = "".join(item.value for item in app.markdown)
    assert ('data-company-metrics-save="true"' in metrics_markup) is (role == "owner")
    assert "Project Reserves" not in metrics_markup
    if role == "owner":
        labels = [field.label for field in app.text_input]
        assert labels[:3] == [
            "Ma'am / VAT rate",
            "Warranty reserve",
            "Management buffer",
        ]
    else:
        assert all(field.disabled for field in app.text_input)

    app.session_state["company_profile_tab"] = "Labor Costs"
    app.run()
    if role == "owner":
        assert calls["employees"] == 1
        assert any(button.label == "Add Worker" for button in app.button)
        assert [item.label for item in app.selectbox] == [
            "Department", "Position", "Pay type",
        ]
    else:
        assert calls["employees"] == 0
        assert not any(button.label == "Add Worker" for button in app.button)
        assert "available only to the company owner" in " ".join(
            item.value for item in app.info
        )

    app.session_state["company_profile_tab"] = "Contacts"
    app.run()
    assert calls == {
        "profile": 1,
        "members": 0,
        "metrics": 1,
        "employees": 1 if role == "owner" else 0,
    }
    if role == "owner":
        labels = [field.label for field in app.text_input]
        assert any(button.label == "Save Contacts" for button in app.button)
        assert "House Number" in labels
        assert "Number" not in labels
        assert labels.index("Facebook") < labels.index("LinkedIn") < labels.index("Instagram")

    app.session_state["company_profile_tab"] = "Bank Details"
    app.run()
    assert calls == {
        "profile": 2,
        "members": 0,
        "metrics": 1,
        "employees": 1 if role == "owner" else 0,
    }
    if role == "owner":
        labels = [field.label for field in app.text_input]
        assert any(button.label == "Save Bank Details" for button in app.button)
        assert labels[:4] == [
            "Company name",
            "Company registration number",
            "Company legal name (Hebrew)",
            "Company legal name (English)",
        ]
        assert labels.count("Company legal name (Hebrew)") == 1
        assert labels.count("Company legal name (English)") == 1
        assert "BIC" in labels
        assert "SWIFT / BIC" not in labels
    assert "VAT file number" not in [field.label for field in app.text_input]
    assert "Country" not in [field.label for field in app.text_input]

    app.session_state["company_profile_tab"] = "Users"
    app.run()
    assert calls == {
        "profile": 2,
        "members": 1,
        "metrics": 1,
        "employees": 1 if role == "owner" else 0,
    }
    assert not app.subheader
    assert not app.code
    users_markup = "".join(item.value for item in app.markdown)
    assert ('class="company-profile-users company-profile-invite"' in users_markup) is (
        role == "owner"
    )
    assert ("Team Invitation Link" in users_markup) is (role == "owner")
    assert ("https://example.com/join/token" in users_markup) is (role == "owner")


def test_company_metrics_reuses_object_detail_table_contract():
    html = company_metrics_view.table_html(
        (("Facility / Rent / Arnona", (
            ("rent_facilities_cost", "Rent"),
            ("arnona_facilities_cost", "Arnona"),
        )),),
        {"rent_facilities_cost": 1000, "arnona_facilities_cost": 500},
        18,
        editable=True,
    )
    assert "object-detail-table object-detail-table--cols-4 company-metrics-table" in html
    assert "object-detail-table-head-row" in html
    assert "object-detail-group-summary company-metrics-group-summary" in html
    assert html.count('contenteditable="true"') == 2
    assert html.count("company-metrics-monthly-input") == 2
    assert 'data-company-metrics-vat>—</span>' in html
    assert 'data-company-metrics-total>₪500</span>' in html


def test_labor_position_list_uses_compact_labels_and_keeps_legacy_display():
    assert company_profile.LABOR_DEPARTMENTS == {
        "management": "Management",
        "office": "Office",
        "production": "Production",
    }
    assert ("general_worker", "Worker") in company_profile.LABOR_POSITIONS["production"]
    assert ("painter_finisher", "Painter") in company_profile.LABOR_POSITIONS["production"]
    assert ("designer_draftsperson", "Designer") in company_profile.LABOR_POSITIONS["office"]
    assert not any(
        code == "cabinetmaker_joiner"
        for code, _label in company_profile.LABOR_POSITIONS["production"]
    )
    assert not any(
        code == "purchasing_manager"
        for code, _label in company_profile.LABOR_POSITIONS["office"]
    )
    assert company_profile._labor_position_label("cabinetmaker_joiner") == "Carpenter"
    assert company_profile._labor_position_label("purchasing_manager") == "Purchasing Manager"


@pytest.mark.parametrize(
    ("pay_type", "pay_values", "expected"),
    [
        (
            "monthly_salary",
            {"gross_monthly_salary": 12_000},
            {
                "gross_monthly_salary": 12_000.0,
                "gross_hourly_rate": None,
                "monthly_hours": None,
                "employment_factor": 1.25,
                "total_hourly_cost": None,
                "total_monthly_cost": 15_000.0,
            },
        ),
        (
            "hourly_rate",
            {"gross_hourly_rate": 65, "monthly_hours": 160},
            {
                "gross_monthly_salary": None,
                "gross_hourly_rate": 65,
                "monthly_hours": 160.0,
                "employment_factor": 1.25,
                "total_hourly_cost": 81.25,
                "total_monthly_cost": 13_000.0,
            },
        ),
    ],
)
def test_add_company_employee_writes_only_selected_pay_model(
    monkeypatch, pay_type, pay_values, expected
):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    inserted = []

    class Query:
        def insert(self, values):
            inserted.append(values)
            return self

        def execute(self):
            return type("Result", (), {"data": [inserted[-1]]})()

    class Client:
        def table(self, name):
            assert name == "company_employees"
            return Query()

    client = Client()
    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: client)
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    company_profile.add_company_employee(
        access,
        worker_name=" Guy ",
        department="production",
        position_code="general_worker",
        pay_type=pay_type,
        **pay_values,
    )

    assert inserted == [{
        "company_id": "company-a",
        "worker_name": "Guy",
        "department": "production",
        "position_code": "general_worker",
        "pay_type": pay_type,
        **expected,
    }]


def test_labor_pay_values_are_whole_and_factor_uses_two_decimals():
    payload = company_profile._company_employee_payload(
        worker_name="Worker",
        department="production",
        position_code="general_worker",
        pay_type="hourly_rate",
        gross_hourly_rate=50,
        monthly_hours=160,
        employment_factor=1.256,
    )
    assert payload["gross_hourly_rate"] == 50
    assert payload["monthly_hours"] == 160
    assert payload["employment_factor"] == 1.26
    assert payload["total_hourly_cost"] == 63.0
    assert payload["total_monthly_cost"] == 10_080.0
    with pytest.raises(ValueError, match="Hourly rate must be a whole number"):
        company_profile._company_employee_payload(
            worker_name="Worker",
            department="production",
            position_code="general_worker",
            pay_type="hourly_rate",
            gross_hourly_rate=50.5,
            monthly_hours=160,
        )
    with pytest.raises(ValueError, match="whole number"):
        company_profile._company_employee_payload(
            worker_name="Worker",
            department="production",
            position_code="general_worker",
            pay_type="hourly_rate",
            gross_hourly_rate=50,
            monthly_hours=160.5,
        )


def test_update_company_employee_is_scoped_to_company_and_worker(monkeypatch):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = []
    filters = []

    class Query:
        def update(self, values):
            writes.append(values)
            return self

        def eq(self, field, value):
            filters.append((field, value))
            return self

        def execute(self):
            return type("Result", (), {"data": [{
                "company_id": "company-a",
                "employee_id": "employee-1",
                **writes[-1],
            }]})()

    class Client:
        def table(self, name):
            assert name == "company_employees"
            return Query()

    monkeypatch.setattr(company_profile, "get_supabase_client", Client)
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    company_profile.update_company_employee(
        access,
        "employee-1",
        worker_name="Guy",
        department="production",
        position_code="general_worker",
        pay_type="monthly_salary",
        gross_monthly_salary=9_000,
    )

    assert filters == [
        ("company_id", "company-a"),
        ("employee_id", "employee-1"),
    ]
    assert writes[-1]["gross_monthly_salary"] == 9_000


def test_archive_company_employee_retains_row_and_scopes_update(monkeypatch):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = []
    filters = []

    class Query:
        def update(self, values):
            writes.append(values)
            return self

        def eq(self, field, value):
            filters.append(("eq", field, value))
            return self

        def is_(self, field, value):
            filters.append(("is", field, value))
            return self

        def execute(self):
            return type("Result", (), {"data": [{
                "company_id": "company-a",
                "employee_id": "employee-1",
                **writes[-1],
            }]})()

    class Client:
        def table(self, name):
            assert name == "company_employees"
            return Query()

    monkeypatch.setattr(company_profile, "get_supabase_client", Client)
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    archived = company_profile.archive_company_employee(access, "employee-1")

    assert set(writes[-1]) == {"deleted_at"}
    assert archived["deleted_at"].endswith("+00:00")
    assert filters == [
        ("eq", "company_id", "company-a"),
        ("eq", "employee_id", "employee-1"),
        ("is", "deleted_at", "null"),
    ]


def test_labor_costs_apply_factor_and_hours_only_to_hourly_workers():
    hourly = {
        "pay_type": "hourly_rate",
        "gross_hourly_rate": 50,
        "monthly_hours": 160,
        "employment_factor": 1.25,
    }
    monthly = {
        "pay_type": "monthly_salary",
        "gross_monthly_salary": 12_000,
        "employment_factor": 1.25,
    }

    assert company_profile._labor_hourly_cost(hourly) == 62.5
    assert company_profile._labor_hourly_cost(monthly) is None
    assert company_profile._labor_monthly_cost(hourly) == 10_000
    assert company_profile._labor_monthly_cost(monthly) == 15_000

    overridden = company_profile._company_employee_payload(
        worker_name="Worker",
        department="production",
        position_code="general_worker",
        pay_type="hourly_rate",
        gross_hourly_rate=50,
        monthly_hours=160,
        employment_factor=1.25,
        total_hourly_cost=70,
        total_monthly_cost=11_000,
    )
    assert overridden["total_hourly_cost"] == 70
    assert overridden["total_monthly_cost"] == 11_000


def test_labor_input_change_synchronizes_editable_totals():
    company_profile.st.session_state.clear()
    company_profile.st.session_state.update({
        "labor_test_gross_hourly_rate": "50",
        "labor_test_monthly_hours": "160",
        "labor_test_employment_factor": "1.25",
    })

    company_profile._sync_labor_totals("labor_test", "hourly_rate")

    assert company_profile.st.session_state["labor_test_total_hourly_cost"] == "₪62.50"
    assert company_profile.st.session_state["labor_test_total_monthly_cost"] == "₪10\u202f000"


def test_labor_form_reset_rotates_widget_keys_and_clears_edit_mode():
    company_profile.st.session_state.clear()
    company_profile.st.session_state.update({
        "_labor_form_reset_pending": True,
        "_labor_form_version": 4,
        "_labor_edit_employee_id": "employee-1",
        "labor_form_4_new_worker_name": "Guy",
    })
    company_profile._apply_labor_form_reset()
    assert company_profile.st.session_state["_labor_form_version"] == 5
    assert company_profile.st.session_state["_labor_edit_employee_id"] == ""
    assert "labor_form_4_new_worker_name" not in company_profile.st.session_state


def test_labor_list_renders_before_editor_and_uses_profile_fonts():
    source = (Path(__file__).parents[1] / "screens/company_profile.py").read_text()
    render_source = source.split("def _render_labor_costs", 1)[1].split(
        "def _open_upload_screen", 1
    )[0]
    assert render_source.index("_render_employee_list(employees)") < render_source.index(
        'with st.container(key="company_labor_card"'
    )
    css = (Path(__file__).parents[1] / "styles/company_profile.py").read_text()
    assert ".company-profile-users th" in css
    assert "font-family: var(--font-mono) !important" in css
    assert ".company-profile-users td strong" in css
    assert ".company-profile-mark {" in css
    assert "transform: translateY(3px);" in css
    assert ".st-key-company_profile_actions {" in css
    assert "transform: translateY(10px);" in css
    assert '.st-key-company_profile_actions div[data-testid="stButton"] button {' in css
    assert "min-height: 36px !important;" in css
    assert "font-family: var(--font-sans) !important" in css


def test_company_logo_card_uses_profile_table_header_and_two_square_panels():
    screen_source = (
        Path(__file__).parents[1] / "screens/company_profile.py"
    ).read_text()
    logo_source = screen_source.split("def _render_company_logo_card", 1)[1].split(
        "def _render_owner_bank_details", 1
    )[0]
    css = (Path(__file__).parents[1] / "styles/company_profile.py").read_text()

    assert '<div class="company-logo-table-heading">Company Logo</div>' in logo_source
    assert '<h3>Company Logo</h3>' not in logo_source
    assert "converted to a standard square PNG" not in logo_source
    assert "upload_column, preview_column = st.columns(" in logo_source
    assert 'type=["png", "svg", "pdf"]' in logo_source
    assert 'body = "<span>Logo</span>"' in screen_source
    assert "else current_logo" in logo_source
    assert 'button_label = "Change Logo" if reference else "Save Logo"' in logo_source
    assert "disabled=pending_logo is None" in logo_source
    assert ".company-logo-table-heading {" in css
    assert ".st-key-company_logo_body" in css
    assert (
        ".st-key-company_logo_body {\n"
        "            padding: var(--profile-action-gap) 28px 28px;"
    ) in css
    assert "max-width: 760px;" in css
    assert "height: 220px;" in css
    assert 'content: "Drop or Upload\\\\A PNG/SVG/PDF";' in css
    assert "gap: var(--profile-action-gap) !important;" in css
    assert "margin-top: 0 !important;" in css
    assert 'button_label = "Change Logo" if reference else "Save Logo"' in logo_source
    assert "install_company_logo_picker_guard()" in logo_source
    assert "disabled=pending_logo is None and not reference" in logo_source
    base_css = (Path(__file__).parents[1] / "styles/base.py").read_text()
    assert "--profile-action-gap: var(--space-6);" in base_css
    assert "company-logo-notice-dismiss 180ms ease 5s forwards" in css


def test_labor_existing_worker_opens_prefilled_edit_form(monkeypatch):
    monkeypatch.setattr(company_profile, "load_company_employees", lambda _access: [{
        "employee_id": "employee-1",
        "company_id": "company-a",
        "worker_name": "Guy",
        "department": "production",
        "position_code": "general_worker",
        "pay_type": "hourly_rate",
        "gross_monthly_salary": None,
        "gross_hourly_rate": 50,
        "monthly_hours": 160,
        "employment_factor": 1.25,
    }])
    app = AppTest.from_function(_render_profile_test)
    app.session_state["test_profile_role"] = "owner"
    app.session_state["company_profile_tab"] = "Labor Costs"
    app.session_state["_labor_edit_employee_id"] = "employee-1"
    app.run()

    assert not app.exception
    fields = {field.label: field for field in app.text_input}
    assert fields["Worker name"].value == "Guy"
    assert fields["Hourly Rate"].value == "50"
    assert fields["Average Hours per Month"].value == "160"
    assert fields["Employment Factor"].value == "1.25"
    assert fields["Total Hourly Cost"].value == "₪62.50"
    assert fields["Total Monthly Cost"].value == "₪10\u202f000"
    assert fields["Total Hourly Cost"].disabled is False
    assert fields["Total Monthly Cost"].disabled is False
    assert any(button.label == "Save Worker" for button in app.button)
    assert any(button.label == "Cancel Edit" for button in app.button)


def test_labor_edit_request_is_consumed_once_and_rejects_invalid_payloads():
    company_profile.st.session_state.clear()

    request = '{"employeeId":"employee-1","nonce":"request-1"}'
    assert company_profile._consume_labor_edit_request(request) == "employee-1"
    assert company_profile._consume_labor_edit_request(request) is None
    assert company_profile._consume_labor_edit_request("not-json") is None
    assert company_profile._consume_labor_edit_request(
        '{"employeeId":"","nonce":"request-2"}'
    ) is None


def test_labor_worker_table_uses_pencil_bridge_without_edit_selectbox():
    root = Path(__file__).parents[1]
    source = (root / "screens/company_profile.py").read_text()
    render_source = source.split("def _render_labor_costs", 1)[1].split(
        "def _open_upload_screen", 1
    )[0]
    component = (root / "ui/company_labor_bridge_component/index.html").read_text()
    css = (root / "styles/company_profile.py").read_text()

    assert "data-company-labor-edit" in source
    assert "data-company-labor-delete" in source
    assert 'aria-label="Edit worker"' in source
    assert 'aria-label="Remove worker"' in source
    assert 'st.selectbox(\n            "Edit worker"' not in render_source
    assert '[data-company-labor-edit], [data-company-labor-delete]' in component
    assert 'send("streamlit:setComponentValue"' in component
    assert ".company-labor-edit" in css
    assert ".company-labor-delete" in css
    assert ".st-key-company_labor_bridge_host" in css


def test_labor_table_keeps_compact_columns_and_aligned_totals():
    root = Path(__file__).parents[1]
    source = (root / "screens/company_profile.py").read_text()
    css = (root / "styles/company_profile.py").read_text()

    assert '<th colspan="5">Total Monthly</th>' in source
    assert '<th>Pay Details</th><th>Monthly</th>' in source
    assert 'class="company-labor-col-actions"' in source
    assert 'class="company-labor-col-worker"' in source
    assert 'class="company-labor-col-department"' in source
    assert 'class="company-labor-col-position"' in source
    assert 'class="company-labor-col-pay-type"' in source
    assert 'class="company-labor-col-details"' in source
    assert ".company-labor-col-actions" in css
    assert "width: 38px;" in css
    assert "flex-direction: column;" in css
    assert ".company-labor-col-details" in css
    assert "width: 146px;" in css
    assert "min-width: 0;" in css
    assert 'button:not([aria-haspopup="listbox"])' in css
    assert "box-sizing: border-box;" in css
    assert "border-left: 0 !important;" in css
    assert "border-right: 0 !important;" in css
    assert "align-items: flex-end !important;" in css
    assert '[data-testid="stWidgetLabel"]' in css


def test_labor_table_uses_short_pay_types_and_omits_employment_factor():
    hourly = {
        "pay_type": "hourly_rate",
        "gross_hourly_rate": 50,
        "monthly_hours": 160,
        "employment_factor": 1.25,
    }
    monthly = {
        "pay_type": "monthly_salary",
        "gross_monthly_salary": 12_000,
        "employment_factor": 1.25,
    }

    assert company_profile._labor_table_pay_type("hourly_rate") == "Hourly"
    assert company_profile._labor_table_pay_type("monthly_salary") == "Monthly"
    assert company_profile._labor_pay_details(hourly) == "₪50/h · 160h"
    assert company_profile._labor_pay_details(monthly) == "₪12\u202f000"
    assert "1.25" not in company_profile._labor_pay_details(hourly)


def test_labor_empty_amounts_use_zero_placeholders_and_structured_factor_help():
    root = Path(__file__).parents[1]
    source = (root / "screens/company_profile.py").read_text()

    assert source.count('placeholder="0"') >= 3
    assert 'if editing else "0"' not in source
    assert '"**Includes:**\\n"' in source
    assert "Planning multiplier for employer costs" not in source
    assert '"- Employer pension\\n"' in source
    assert '"**Excludes:**\\n"' in source
    assert '"- Overtime\\n"' in source


def test_company_employee_access_is_owner_only(monkeypatch):
    member = company_auth.CompanyAccess(
        "user-2", "member@example.com", "company-a", "member", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: member)
    monkeypatch.setattr(
        company_profile,
        "get_supabase_client",
        lambda: pytest.fail("member access must stop before opening a database client"),
    )
    with pytest.raises(PermissionError):
        company_profile.load_company_employees(member)


def test_company_employees_migration_keeps_salary_data_owner_only():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_19_company_employees.sql").read_text()
    assert "create table if not exists public.company_employees" in sql
    assert "worker_name text not null" in sql
    assert "first_name" not in sql and "last_name" not in sql
    assert sql.count("and m.role = 'owner'") == 5
    assert "revoke all on public.company_employees from anon" in sql


def test_company_employee_factor_soft_delete_migration_is_non_destructive():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_20_company_employee_cost_factor_soft_delete.sql"
    ).read_text().lower()
    assert "add column if not exists employment_factor" in sql
    assert "add column if not exists deleted_at" in sql
    assert "default 1.25" in sql
    assert "where deleted_at is null" in sql
    assert "drop table" not in sql
    assert "drop column" not in sql
    assert "truncate" not in sql
    assert "delete from" not in sql


def test_company_employee_manual_totals_migration_retains_rows():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_20_company_employee_manual_totals.sql"
    ).read_text().lower()
    assert "add column if not exists total_hourly_cost" in sql
    assert "add column if not exists total_monthly_cost" in sql
    assert "where total_monthly_cost is null" in sql
    assert "drop table" not in sql
    assert "drop column" not in sql
    assert "truncate" not in sql
    assert "delete from" not in sql


def test_company_metrics_member_table_has_no_editable_cells_or_save_action():
    html = company_metrics_view.table_html(
        (("Utilities / Safety", (("electricity_cost", "Electricity"),)),),
        {"electricity_cost": 200},
        18,
        editable=False,
    )
    assert "contenteditable" not in html
    assert 'data-company-metrics-total>₪236</span>' in html


def test_other_spendings_flows_from_company_metrics_to_object_detail_pricing():
    assert company_profile.METRIC_GROUPS[-1] == (
        "Other Spendings",
        (("other_spendings_cost", "Other spendings"),),
    )
    assert pricing._monthly_overhead_map()[-1] == (
        "other_spendings_cost",
        "Other spendings",
        "Other spendings",
    )
    save_html = company_metrics_view.save_action_html()
    assert "SAVE OVERHEAD EXPENSES" in save_html
    assert "<button" in save_html
    assert "href=" not in save_html


def test_company_metrics_uses_overhead_expenses_copy_everywhere(monkeypatch):
    table = company_metrics_view.table_html(
        (("Utilities / Safety", (("electricity_cost", "Electricity"),)),),
        {"electricity_cost": 200},
        18,
        editable=True,
    )
    assert "Overhead Expense" in table
    assert ">Expense<" not in table
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "save_company_metrics", lambda *_args: None)
    company_profile.st.session_state.clear()
    snapshot = json.dumps({"nonce": "copy-test", "settings": {}, "monthly": {}})
    assert (
        company_profile._consume_company_metrics_snapshot(access, snapshot)
        == "Overhead expenses saved"
    )


def test_company_profile_tabs_support_stateful_streamlit_dom():
    css = (Path(__file__).parents[1] / "styles/company_profile.py").read_text()
    assert '.st-key-company_profile_tab [role="tablist"]' in css
    assert '.st-key-company_profile_tab [role="tab"]' in css
    assert '[role="tab"][data-selected]' in css
    assert ".react-aria-SelectionIndicator" in css
    assert '[role="tablist"]::after' in css
    assert ".st-key-company_metrics_bridge_host" in css
    assert ':has(.st-key-company_metrics_bridge_host)' in css
    assert '[role="tab"][data-selected] p' in css
    assert '[role="tabpanel"]:has(.st-key-company_metrics_card)' in css
    assert '> [data-testid="stVerticalBlock"]' in css


def test_company_metrics_bridge_does_not_navigate_parent_page():
    source = Path("ui/company_metrics_bridge_component/index.html").read_text()
    assert "streamlit:setComponentValue" in source
    assert "data-company-metrics-save" in source
    assert "location.search" not in source
    assert "location.href" not in source


def test_only_company_metrics_save_bridge_is_fragment_scoped():
    source = Path("screens/company_profile.py").read_text()
    assert "@st.fragment\ndef _render_metrics_save" in source
    assert "@st.fragment\ndef _render_metrics(" not in source


def test_profile_to_upload_navigation_runs_before_render():
    source = Path("screens/company_profile.py").read_text()
    button_source = source.split('"New Estimate"', 1)[1].split(")", 1)[0]

    assert 'key="profile_to_upload"' in button_source
    assert "on_click=_open_upload_screen" in button_source
    assert "st.rerun" not in button_source


def test_company_details_saves_identity_and_bank_fields_together(monkeypatch):
    profile = {
        "company_name": "Workshop",
        "legal_name_hebrew": "חברה",
        "legal_name": "Workshop Ltd",
        "bank_name": "Bank",
        "bank_number": "10",
        "branch_number": "20",
        "account_number": "30",
        "iban": "IL00",
        "swift": "TESTILIT",
    }
    writes = []
    monkeypatch.setattr(company_profile, "load_company_profile", lambda _access: profile)
    monkeypatch.setattr(
        company_profile,
        "save_company_profile",
        lambda _access, values: writes.append(values) or {"company_id": "company-a"},
    )
    monkeypatch.setattr(company_profile, "load_company_members", lambda _access: [])
    monkeypatch.setattr(
        company_profile,
        "load_company_metrics",
        lambda _access: ({"vat_percent": 18}, {}),
    )
    monkeypatch.setattr(company_auth, "company_join_url", lambda _access: "https://example.com/join/token")

    app = AppTest.from_function(_render_profile_test)
    app.session_state["test_profile_role"] = "owner"
    app.session_state["company_profile_tab"] = "Bank Details"
    app.run()
    next(button for button in app.button if button.label == "Save Bank Details").click()
    app.run()

    assert app.session_state["company_profile_tab"] == "Bank Details"
    assert any(button.label == "Save Bank Details" for button in app.button)
    assert writes[-1]["company_name"] == "Workshop"
    assert writes[-1]["legal_name_hebrew"] == "חברה"
    assert writes[-1]["legal_name"] == "Workshop Ltd"
    assert writes[-1]["iban"] == "IL00"
    assert writes[-1]["swift"] == "TESTILIT"


def test_save_company_metrics_updates_only_visible_metric_fields(monkeypatch):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = {}

    class Query:
        def __init__(self, table):
            self.table = table

        def update(self, values):
            writes[self.table] = values
            return self

        def eq(self, *_args):
            return self

        def execute(self):
            return type("Result", (), {"data": [{"company_id": "company-a"}]})()

    class Client:
        def table(self, name):
            return Query(name)

    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: Client())
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    monthly = {field: index for index, field in enumerate(company_profile.METRIC_MONTHLY_FIELDS)}
    company_profile.save_company_metrics(
        access,
        {
            "vat_percent": 18,
            "warranty_reserve_percent": 2.5,
            "management_buffer_percent": 4,
        },
        monthly,
    )

    assert set(writes["overhead_settings"]) == {
        "vat_percent",
        "warranty_reserve_percent",
        "management_buffer_percent",
    }
    assert "delivery_percent" not in writes["overhead_settings"]
    assert set(writes["overhead_monthly"]) == {
        *company_profile.METRIC_MONTHLY_FIELDS,
    }


def test_new_company_metrics_row_includes_required_legacy_defaults(monkeypatch):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-new", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = []

    class Query:
        def __init__(self, table):
            self.table = table

        def update(self, values):
            writes.append(("update", self.table, values))
            return self

        def insert(self, values):
            writes.append(("insert", self.table, values))
            return self

        def eq(self, *_args):
            return self

        def execute(self):
            return type("Result", (), {"data": []})()

    class Client:
        def table(self, name):
            return Query(name)

    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: Client())
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    company_profile.save_company_metrics(
        access,
        {
            "vat_percent": 18,
            "warranty_reserve_percent": 7,
            "management_buffer_percent": 6,
        },
        {field: 0 for field in company_profile.METRIC_MONTHLY_FIELDS},
    )

    settings_insert = next(
        values for operation, table, values in writes
        if operation == "insert" and table == "overhead_settings"
    )
    assert settings_insert == {
        "company_id": "company-new",
        **company_profile.METRIC_SETTING_INSERT_DEFAULTS,
        "vat_percent": 18,
        "warranty_reserve_percent": 7,
        "management_buffer_percent": 6,
    }


def test_company_metrics_format_whole_shekels_and_exempt_arnona_from_vat():
    assert company_profile._metric_money(10_000.49) == "₪10\u202f000"
    assert company_profile._metric_money(" ₪2,500.80 ") == "₪2\u202f501"
    assert company_profile._metric_vat("rent_facilities_cost", 10_000, 18) == 1_800
    assert company_profile._metric_vat("arnona_facilities_cost", 2_500, 18) == 0
    assert company_profile._metric_percent_text(18) == "18%"
    assert company_profile._metric_percent_text(2.5) == "2.5%"


@pytest.mark.parametrize(("raw", "formatted"), [
    ("0534000000", "+972 53 400 0000"),
    ("+972534000000", "+972 53 400 0000"),
    ("972 53 400 0000", "+972 53 400 0000"),
    ("0", "0"),
    ("", ""),
])
def test_company_profile_formats_israeli_phone(raw, formatted):
    assert company_profile._format_israeli_phone(raw) == formatted


def test_company_metrics_save_monthly_costs_as_whole_shekels(monkeypatch):
    access = company_auth.CompanyAccess(
        "user-1", "owner@example.com", "company-a", "owner", "token"
    )
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = {}

    class Query:
        def __init__(self, table):
            self.table = table

        def update(self, values):
            writes[self.table] = values
            return self

        def eq(self, *_args):
            return self

        def execute(self):
            return type("Result", (), {"data": [{"company_id": "company-a"}]})()

    class Client:
        def table(self, name):
            return Query(name)

    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: Client())
    monkeypatch.setattr(company_profile, "assert_company_owner", lambda *_args: None)

    company_profile.save_company_metrics(
        access,
        {field: 0 for field in company_profile.METRIC_SETTING_FIELDS},
        {field: 1234.6 for field in company_profile.METRIC_MONTHLY_FIELDS},
    )

    assert set(writes["overhead_monthly"].values()) == {1235}


def test_profile_partial_update_preserves_hidden_vat_and_country(monkeypatch):
    access = company_auth.CompanyAccess("user-1", "owner@example.com", "company-a", "owner", "token")
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    writes = []

    class Query:
        def __init__(self, table):
            self.table = table

        def select(self, *_args):
            return self

        def eq(self, *_args):
            return self

        def limit(self, *_args):
            return self

        def update(self, values):
            writes.append(values)
            return self

        def execute(self):
            if self.table == "company_members":
                return type("Response", (), {"data": [{"company_id": "company-a", "role": "owner"}]})()
            return type("Response", (), {"data": [{"company_id": "company-a"}]})()

    class Client:
        def table(self, name):
            return Query(name)

    monkeypatch.setattr(company_profile, "get_supabase_client", lambda: Client())
    company_profile.save_company_profile(access, {
        "company_name": " Workshop ",
        "legal_name": "Workshop Ltd",
    })
    assert writes == [{"company_name": "Workshop", "legal_name": "Workshop Ltd"}]
    assert "vat_file_number" not in writes[0]
    assert "address_country" not in writes[0]


def test_company_profile_reuses_auth_input_contract():
    css = (Path(__file__).parents[1] / "styles/company_profile.py").read_text()
    assert '[data-testid="InputInstructions"]' in css
    assert '[data-testid="stTextInputRootElement"]' in css
    assert '[data-testid="stTextInput"]:focus-within' in css
    assert "border: 1px solid #CEC5D1 !important" in css
    assert '.react-aria-ComboBox [role="group"]' in css
    assert '[role="group"][data-focus-within="true"]' in css
    assert '.react-aria-ComboBox input[role="combobox"]' in css
    assert '[role="option"][aria-selected="true"] [data-item-hl]' in css


def test_labor_card_spacing_and_disabled_select_placeholder_contract():
    css = (Path(__file__).parents[1] / "styles/company_profile.py").read_text()
    assert ".st-key-company_labor_card {\n            margin-top: 0;" in css
    assert '[data-testid="stTextInput"] input:disabled' in css
    assert ".st-key-company_labor_card input:disabled" not in css


def test_server_run_id_replaces_model_id_on_all_objects():
    result = {
        "rfq_run": {"run_id": "unknown_project_run_001"},
        "detected_objects": [
            {"run_id": "unknown_project_run_001", "object_id": "object-001"},
            {"run_id": "unknown_project_run_001", "object_id": "object-002"},
        ],
    }
    run_id = assign_server_run_id(result)
    assert run_id.startswith("run_")
    assert run_id != "unknown_project_run_001"
    assert result["rfq_run"]["run_id"] == run_id
    assert all(item["run_id"] == run_id for item in result["detected_objects"])


def test_one_creation_link_stores_only_hash_and_no_email_or_company_id():
    writes = []

    class InviteQuery:
        def insert(self, values):
            writes.append(values)
            return self

        def execute(self):
            return None

    class InviteClient:
        def table(self, name):
            assert name == "company_creation_invites"
            return InviteQuery()

    url = create_one_company_link(InviteClient(), "https://example.com", "Pilot company 1")
    parts = urlsplit(url)
    assert parts.path.startswith("/start/")
    token = parts.path.rsplit("/", 1)[-1]
    assert len(writes) == 1
    assert writes[0]["token_hash"] == invite_token_hash(token)
    assert writes[0]["label"] == "Pilot company 1"
    assert len(writes[0]["join_token"]) == 43
    assert writes[0]["join_token"] != token
    assert token not in str(writes)
    assert "company_id" not in url and "email" not in url


def test_live_schema_migration_precreates_staff_link_without_dropping_old_rpc():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_16_precreate_company_join_link.sql").read_text().lower()
    assert "add column if not exists join_token text" in sql
    assert "gen_random_bytes(32)" in sql
    assert "drop function" not in sql
    assert "drop table" not in sql
    assert "delete from" not in sql
    assert "truncate" not in sql
    assert "create function public.create_company_from_invite(" in sql
    assert "values (p_company_id, v_join_token)" in sql


def test_security_cutover_changes_access_only_and_preserves_rows():
    sql = (Path(__file__).parents[1] / "db/sql/2026_09_16_company_access_security_cutover.sql").read_text().lower()
    assert "revoke all privileges" in sql
    assert "rfq_estimate_pricing_overrides_anon_select" in sql
    assert "with (security_invoker = true)" in sql
    assert "create policy company_members_self_read" in sql
    assert "create policy company_member_read" in sql
    assert "create policy pricing_overrides_company_member" in sql
    assert "grant select, insert, update" in sql
    for forbidden in (
        "delete from", "truncate", "drop table", "drop view",
        "alter table public.companies add", "update public.", "insert into",
    ):
        assert forbidden not in sql


def test_company_join_url_has_only_random_token():
    token = new_invite_token()
    url = invite_url("https://example.com/?embed=true", token, "join")
    assert urlsplit(url).path == f"/join/{token}"
    assert parse_qs(urlsplit(url).query) == {"embed": ["true"]}
    wrapper = (Path(__file__).parents[1] / "cloudflare/index.html").read_text()
    redirects = (Path(__file__).parents[1] / "cloudflare/_redirects").read_text()
    assert "(?:start|join)" in wrapper
    assert 'appUrl.searchParams.set("invite", inviteToken)' in wrapper
    assert "/start/*  /index.html  200" in redirects
    assert "/join/*   /index.html  200" in redirects


def test_shared_invites_use_public_https_application_only():
    assert public_app_url() == DEFAULT_PUBLIC_APP_URL
    assert public_app_url("https://app.costerly.ai/") == "https://app.costerly.ai/"
    for local_url in (
        "http://127.0.0.1:8580",
        "https://localhost:8580",
        "http://[::1]:8580",
    ):
        with pytest.raises(ValueError, match="local address|public https"):
            public_app_url(local_url)


def test_creation_link_rejects_local_url_before_database_write():
    class Client:
        def table(self, _name):
            raise AssertionError("A local invitation must not touch the database")

    with pytest.raises(ValueError, match="public https"):
        create_one_company_link(Client(), "http://127.0.0.1:8580", "Local")


@pytest.mark.parametrize("request_url", [
    "http://127.0.0.1:8580/?invite=token",
    "http://localhost:8501/?invite=token",
    "http://[::1]:8501/?invite=token",
])
def test_registration_rejects_explicit_local_browser_origins(monkeypatch, request_url):
    monkeypatch.setattr(
        company_auth.st,
        "context",
        type("Context", (), {"url": request_url})(),
    )
    with pytest.raises(PermissionError, match="public Costerly application"):
        company_auth.require_public_invitation_request()


@pytest.mark.parametrize("request_url", [
    "https://app.costerly.ai/start/token",
    "https://costerly-app.streamlit.app/?embed=true&invite=token",
    "http://testserver/",
    "",
])
def test_registration_allows_public_or_test_browser_origins(monkeypatch, request_url):
    monkeypatch.setattr(
        company_auth.st,
        "context",
        type("Context", (), {"url": request_url})(),
    )
    company_auth.require_public_invitation_request()


def _render_invitation_signup():
    from state import company_auth
    from use_cases.invite_links import new_invite_token

    company_auth.render_login_or_signup(
        company_auth.InvitationContext("create", new_invite_token())
    )


def test_invited_visitor_sees_registration_form():
    app = AppTest.from_function(_render_invitation_signup).run()
    assert not app.exception
    assert len(app.tabs) == 0
    assert any(button.label == "Create Company Account" for button in app.button)
    assert any(input_.key == "signup_email" for input_ in app.text_input)
    assert any(input_.key == "signup_company_name" for input_ in app.text_input)
    assert any(input_.key == "signup_password_confirm" for input_ in app.text_input)
    assert not any(button.label.startswith("Already have a login?") for button in app.button)


def test_interrupted_creation_uses_existing_login_without_recreating_user(monkeypatch):
    calls = []
    monkeypatch.setattr(company_auth, "sign_in", lambda *_args: calls.append("signed in"))
    monkeypatch.setattr(company_auth, "sign_up", lambda *_args: calls.append("signed up"))
    company_auth.authenticate_invited_creator("owner@example.com", "Strong123", company_auth.InvitationContext("create", new_invite_token()))
    assert calls == ["signed in"]


def test_new_creator_signs_up_only_after_invalid_credentials(monkeypatch):
    calls = []

    def not_existing(*_args):
        calls.append("sign in attempted")
        raise company_auth.AuthApiError("Invalid login credentials", 400, "invalid_credentials")

    monkeypatch.setattr(company_auth, "sign_in", not_existing)
    monkeypatch.setattr(company_auth, "sign_up", lambda *_args: calls.append("signed up"))
    company_auth.authenticate_invited_creator("new@example.com", "Strong123", company_auth.InvitationContext("create", new_invite_token()))
    assert calls == ["sign in attempted", "signed up"]


def test_existing_email_with_wrong_password_gets_actionable_error(monkeypatch):
    monkeypatch.setattr(company_auth, "sign_in", lambda *_args: (_ for _ in ()).throw(
        company_auth.AuthApiError("Invalid login credentials", 400, "invalid_credentials")
    ))
    monkeypatch.setattr(company_auth, "sign_up", lambda *_args: (_ for _ in ()).throw(
        company_auth.AuthApiError("A user with this email address has already been registered", 422, "email_exists")
    ))
    with pytest.raises(company_auth.ExistingLoginPasswordError, match="password from your first attempt"):
        company_auth.authenticate_invited_creator("owner@example.com", "Wrong123", company_auth.InvitationContext("create", new_invite_token()))


def test_existing_login_error_is_shown_at_email_without_extra_button(monkeypatch):
    def wrong_existing_password(*_args):
        raise company_auth.ExistingLoginPasswordError(
            "This email already has a login. Enter the password from your first attempt."
        )

    monkeypatch.setattr(company_auth, "authenticate_invited_creator", wrong_existing_password)
    app = AppTest.from_function(_render_invitation_signup).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    app.text_input(key="signup_email").set_value("owner@example.com")
    app.text_input(key="signup_password").set_value("Wrong123")
    app.text_input(key="signup_password_confirm").set_value("Wrong123")
    next(button for button in app.button if button.label == "Create Company Account").click().run()
    assert any("already registered" in error.value for error in app.error)
    assert any('data-auth-field="email"' in item.value for item in app.markdown)
    assert not any('data-auth-field="password"' in item.value for item in app.markdown)
    assert not any(button.label.startswith("Already have a login?") for button in app.button)


def test_obvious_email_error_uses_quiet_field_marker_without_text():
    app = AppTest.from_function(_render_invitation_signup).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    app.text_input(key="signup_email").set_value("name@company..com")
    app.text_input(key="signup_password").set_value("Strong123")
    app.text_input(key="signup_password_confirm").set_value("Strong123")
    next(button for button in app.button if button.label == "Create Company Account").click().run()
    assert not app.error
    assert any('data-auth-field="email"' in item.value for item in app.markdown)
    assert not any("23514" in error.value or "companies_id_format" in error.value for error in app.error)


def test_submit_marks_every_invalid_registration_field_without_error_text():
    app = AppTest.from_function(_render_invitation_signup).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    next(button for button in app.button if button.label == "Create Company Account").click().run()
    markers = "\n".join(item.value for item in app.markdown)
    assert 'data-auth-field="company"' not in markers
    assert 'data-auth-field="email"' in markers
    assert 'data-auth-field="password"' in markers
    assert 'data-auth-field="confirm"' in markers
    assert not app.error


@pytest.mark.parametrize("email,password,confirm,company", [
    ("bad-email", "Strong123", "Strong123", "Workshop"),
    ("owner@example.com", "password1", "password1", "Workshop"),
    ("owner@example.com", "PASSWORD1", "PASSWORD1", "Workshop"),
    ("owner@example.com", "Password", "Password", "Workshop"),
    ("owner@example.com", "Strong123", "Different123", "Workshop"),
    ("owner@example.com", "Strong123", "Strong123", " "),
])
def test_company_registration_rejects_invalid_credentials(email, password, confirm, company):
    with pytest.raises(ValueError):
        company_auth.validate_registration(email, password, confirm, company)


def test_company_registration_accepts_checked_password():
    company_auth.validate_registration("owner@example.com", "Strong123", "Strong123", "Workshop")


@pytest.mark.parametrize("email,expected", [
    ("owner@company.com", True),
    ("name+tag@company.com.ai", True),
    ("name@sub.company.co.uk", True),
    ("name@company.ai", True),
    ("name@company.рф", True),
    ("name@company", False),
    ("name@company.", False),
    ("name@company.c", False),
    ("name@company.123", False),
    ("name@company..com", False),
    ("name@-company.com", False),
    ("name@company-.com", False),
    (".name@company.com", False),
    ("name..tag@company.com", False),
    ("name@@company.com", False),
    ("name @company.com", False),
])
def test_public_email_shape(email, expected):
    assert is_valid_email_address(email) is expected


def test_registration_and_profile_use_same_email_shape(monkeypatch):
    with pytest.raises(ValueError, match="email address"):
        company_auth.validate_registration("name@company..com", "Strong123", "Strong123", "Workshop")
    access = company_auth.CompanyAccess("user-1", "owner@example.com", "company-a", "owner", "token")
    monkeypatch.setattr(company_profile, "_current_access", lambda _access: access)
    with pytest.raises(ValueError, match="official email"):
        company_profile.save_company_contacts(access, "Workshop", "name@company..com", "")


def test_mismatched_password_never_reaches_signup(monkeypatch):
    calls = []
    monkeypatch.setattr(company_auth, "sign_up", lambda *_args: calls.append("signed up"))
    app = AppTest.from_function(_render_invitation_signup).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    app.text_input(key="signup_email").set_value("owner@example.com")
    app.text_input(key="signup_password").set_value("Strong123")
    app.text_input(key="signup_password_confirm").set_value("Different123")
    app.button[0].click().run()
    assert not calls
    assert not app.error
    assert any('data-auth-field="confirm"' in item.value for item in app.markdown)


def test_auth_ui_contract_hides_framework_hints_and_reserves_red_for_validation():
    css = (Path(__file__).parents[1] / "styles/auth.py").read_text()
    guidelines = (Path(__file__).parents[1] / "notes/UI_GUIDELINES.md").read_text()
    normalized_guidelines = " ".join(guidelines.split())
    assert '[data-testid="InputInstructions"]' in css
    assert "costerly-auth-invalid:not(:focus-within)" in css
    assert '[data-testid="stElementContainer"]:has(.auth-field-error-marker)' in css
    assert "marker.dataset.costerlyApplied" in css
    assert "Focus is never an error and must never be red" in normalized_guidelines
    assert "clears immediately when the current value becomes valid" in normalized_guidelines
    assert "One submit validates every field" in normalized_guidelines
    assert "Hidden validation markers must not reserve layout space" in normalized_guidelines
    assert "A missing interaction state is a product defect" in normalized_guidelines
    assert "acknowledge pointer-down immediately" in normalized_guidelines
    assert "Never leave a spinner or a disabled control behind after an error" in normalized_guidelines
    assert "Multi-stage progress must reflect measured work" in normalized_guidelines
    assert "Repeated clicks and retries cannot duplicate persistent work" in normalized_guidelines


def test_company_creation_acknowledges_valid_submit_immediately():
    interactions = (Path(__file__).parents[1] / "styles/auth.py").read_text()
    guidelines = (Path(__file__).parents[1] / "notes/UI_GUIDELINES.md").read_text()
    normalized_guidelines = " ".join(guidelines.split())
    assert "Checking your details..." in interactions
    assert "Creating your company..." in interactions
    assert "Setting up your company. This may take a few seconds." not in interactions
    assert "const invalid = fields.filter((field) => !fieldIsValid(field))" in interactions
    assert "if (invalid.length > 0) return" in interactions
    assert "costerly-auth-loading" in interactions
    assert "Disable duplicate submission" in normalized_guidelines
    assert "Do not enter a loading state when local validation fails" in normalized_guidelines
    assert "advance to creation only after that check succeeds" in normalized_guidelines


def test_sign_in_keeps_the_existing_auth_screen_until_the_target_is_ready():
    interactions = (Path(__file__).parents[1] / "styles/auth.py").read_text()
    ready_signal = (Path(__file__).parents[1] / "ui/js_guards.py").read_text()
    assert "if (originalLabel === 'Sign in')" in interactions
    assert "costerly-auth-sign-in-shell" in interactions
    assert "app.cloneNode(true)" in interactions
    assert "pointerEvents: 'none'" in interactions
    assert "costerly-auth-sign-in-shell" in ready_signal


def test_signup_requires_current_invite_and_uses_mail_free_admin_path(monkeypatch):
    invitation = company_auth.InvitationContext("join", new_invite_token())
    created = []
    signed_in = []

    class Admin:
        def create_user(self, values):
            created.append(values)

    class Auth:
        admin = Admin()

    class Server:
        auth = Auth()

    monkeypatch.setattr(company_auth, "invitation_from_url", lambda: invitation)
    monkeypatch.setattr(company_auth, "_server_client", lambda: Server())
    monkeypatch.setattr(company_auth, "sign_in", lambda email, password: signed_in.append((email, password)))
    company_auth.sign_up(" member@example.com ", "Secret123", invitation)
    assert created == [{
        "email": "member@example.com",
        "password": "Secret123",
        "email_confirm": True,
    }]
    assert signed_in == [(" member@example.com ", "Secret123")]

    monkeypatch.setattr(company_auth, "invitation_from_url", lambda: None)
    with pytest.raises(PermissionError):
        company_auth.sign_up("other@example.com", "Secret123", invitation)
    assert len(created) == 1


def test_authenticated_members_can_share_one_company(monkeypatch):
    state = {
        "auth_access_token": "jwt",
        "auth_refresh_token": "refresh",
        "auth_expires_at": time.time() + 3600,
    }
    monkeypatch.setattr(company_auth.st, "session_state", state)
    current_user = {"id": "user-1"}

    class Auth:
        def get_user(self, _token):
            user = type("User", (), {"id": current_user["id"], "email": "member@example.com"})()
            return type("Response", (), {"user": user})()

    class AuthClient:
        auth = Auth()

    monkeypatch.setattr(company_auth, "_auth_client", lambda: AuthClient())
    monkeypatch.setattr(company_auth, "_server_client", lambda: _Client([{"company_id": "company-a", "role": "member"}]))
    first = company_auth.current_company_access()
    current_user["id"] = "user-2"
    second = company_auth.current_company_access()
    assert first.user_id != second.user_id
    assert first.company_id == second.company_id == "company-a"


def test_company_access_uses_one_rls_request_for_valid_token(monkeypatch):
    def segment(value):
        raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    access_token = ".".join([
        segment({"alg": "HS256", "typ": "JWT"}),
        segment({"sub": "user-1", "email": "member@example.com"}),
        "signature",
    ])
    state = {
        "auth_access_token": access_token,
        "auth_refresh_token": "refresh",
        "auth_expires_at": time.time() + 3600,
    }
    monkeypatch.setattr(company_auth.st, "session_state", state)

    class Postgrest:
        token = None

        def auth(self, token):
            self.token = token

    class Auth:
        def get_user(self, _token):
            raise AssertionError("The successful RLS path must not call get_user")

    class Client(_Client):
        def __init__(self):
            super().__init__([{
                "user_id": "user-1",
                "company_id": "company-a",
                "role": "member",
            }])
            self.postgrest = Postgrest()
            self.auth = Auth()

    client = Client()
    monkeypatch.setattr(company_auth, "_auth_client", lambda: client)
    monkeypatch.setattr(
        company_auth,
        "_server_client",
        lambda: (_ for _ in ()).throw(
            AssertionError("The successful RLS path must not use service role")
        ),
    )

    access = company_auth.current_company_access()

    assert client.postgrest.token == access_token
    assert client.table_name == "company_members"
    assert access == company_auth.CompanyAccess(
        user_id="user-1",
        email="member@example.com",
        company_id="company-a",
        role="member",
        access_token=access_token,
    )
