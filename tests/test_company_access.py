from __future__ import annotations

from pathlib import Path
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from postgrest.exceptions import APIError
from streamlit.testing.v1 import AppTest

from db.company_access import assert_company_owner, assert_estimate_owned, assert_run_owned
from state import company_auth
from screens import company_profile
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


@pytest.mark.parametrize("role", ["owner", "member"])
def test_company_profile_has_four_sections_and_owner_only_controls(monkeypatch, role):
    monkeypatch.setattr(company_profile, "load_company_profile", lambda _access: {
        "company_name": "Workshop", "public_email": "", "public_phone": "",
    })
    monkeypatch.setattr(company_profile, "load_company_members", lambda _access: [
        {"Email": "owner@example.com", "Role": "Owner"},
    ])
    monkeypatch.setattr(company_auth, "company_join_url", lambda _access: "https://example.com/join/token")
    app = AppTest.from_function(_render_profile_test)
    app.session_state["test_profile_role"] = role
    app.run()
    assert not app.exception
    assert [heading.value for heading in app.subheader] == [
        "Details", "Metrics", "Users", "Price lists",
    ]
    assert any(button.label == "Continue to upload" for button in app.button)
    assert any(button.label == "Save details" for button in app.button) == (role == "owner")
    assert len(app.code) == (1 if role == "owner" else 0)


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
