from pathlib import Path
import hashlib

import streamlit as st
from streamlit.testing.v1 import AppTest

from state import company_auth, legal_consent


ROOT = Path(__file__).parents[1]


class _Rows:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, rows):
        self.rows = list(rows)
        self.filters = []

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def limit(self, _value):
        return self

    def execute(self):
        rows = [
            row for row in self.rows
            if all(row.get(key) == value for key, value in self.filters)
        ]
        return _Rows(rows)


class _Client:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return _Table(self.tables.get(name, []))


def _documents() -> legal_consent.LegalDocumentSet:
    return legal_consent.LegalDocumentSet(
        terms=legal_consent.LegalDocument(
            document_type="terms",
            version="1.0",
            acceptance_version="1",
            title="Terms of Service",
            effective_at="2026-09-25T00:00:00Z",
            content_sha256="a" * 64,
            public_path="/terms",
            requires_reacceptance=True,
        ),
        privacy=legal_consent.LegalDocument(
            document_type="privacy",
            version="1.0",
            acceptance_version="1",
            title="Privacy Policy",
            effective_at="2026-09-25T00:00:00Z",
            content_sha256="b" * 64,
            public_path="/privacy",
            requires_reacceptance=False,
        ),
    )


def _render_company_registration():
    from state import company_auth

    company_auth.render_login_or_signup(
        company_auth.InvitationContext("create", "A" * 43)
    )


def _render_sign_in():
    from state import company_auth

    company_auth.render_login_or_signup(None)


def _render_member_registration():
    from state import company_auth

    company_auth.render_login_or_signup(
        company_auth.InvitationContext("join", "B" * 43)
    )


def _render_terms_gate():
    from state import company_auth

    company_auth.render_terms_acceptance(
        company_auth.CompanyAccess(
            user_id="user-1",
            email="owner@example.com",
            company_id="001",
            role="owner",
            access_token="token",
        )
    )


def _render_missing_invitation_setup():
    from state import company_auth

    company_auth.render_company_setup(
        company_auth.CompanyAccess("user-1", "owner@example.com", None, None, "token"),
        None,
    )


def _render_create_company_setup():
    from state import company_auth

    company_auth.render_company_setup(
        company_auth.CompanyAccess("user-1", "owner@example.com", None, None, "token"),
        company_auth.InvitationContext("create", "A" * 43),
    )


def _render_join_company_setup():
    from state import company_auth

    company_auth.render_company_setup(
        company_auth.CompanyAccess("user-1", "owner@example.com", None, None, "token"),
        company_auth.InvitationContext("join", "A" * 43),
    )


def test_new_registration_shows_terms_before_the_only_submit(monkeypatch):
    monkeypatch.setattr(company_auth, "legal_consent_enabled", lambda: True)
    monkeypatch.setattr(company_auth, "current_legal_documents", lambda _client: _documents())
    monkeypatch.setattr(company_auth, "_server_client", lambda: object())

    app = AppTest.from_function(_render_company_registration).run()

    assert not app.exception
    assert len([b for b in app.button if b.label == "Create Company Account"]) == 1
    terms = next(
        checkbox for checkbox in app.checkbox
        if checkbox.label == legal_consent.TERMS_CHECKBOX_TEXT
    )
    assert terms.value is False
    assert not app.expander
    rendered = "\n".join(item.value for item in app.markdown)
    assert 'class="auth-terms-disclosure"' in rendered
    assert 'class="auth-terms-preview"' in rendered
    assert "These Terms of Service" in rendered
    assert "<h2>1. Service, customer and user roles</h2>" in rendered
    assert "&lt;h2&gt;" not in rendered
    assert "Terms govern professional use" not in rendered
    assert "Read the full Terms of Service" not in rendered
    assert "Privacy Policy is available" not in rendered


def test_new_registration_cannot_submit_without_terms(monkeypatch):
    calls = []
    monkeypatch.setattr(company_auth, "legal_consent_enabled", lambda: True)
    monkeypatch.setattr(company_auth, "current_legal_documents", lambda _client: _documents())
    monkeypatch.setattr(company_auth, "_server_client", lambda: object())
    monkeypatch.setattr(
        company_auth,
        "begin_verified_sign_up",
        lambda *_args, **_kwargs: calls.append("signup"),
    )

    app = AppTest.from_function(_render_company_registration).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    app.text_input(key="signup_email").set_value("owner@example.com")
    app.text_input(key="signup_password").set_value("Strong123")
    app.text_input(key="signup_password_confirm").set_value("Strong123")
    next(b for b in app.button if b.label == "Create Company Account").click().run()

    assert not calls
    assert any(
        "Agree to the Terms of Service" in item.value
        for item in app.markdown
    )


def test_member_invitation_requires_terms_on_its_only_submit(monkeypatch):
    calls = []
    monkeypatch.setattr(company_auth, "legal_consent_enabled", lambda: True)
    monkeypatch.setattr(company_auth, "current_legal_documents", lambda _client: _documents())
    monkeypatch.setattr(company_auth, "_server_client", lambda: object())
    monkeypatch.setattr(
        company_auth,
        "begin_verified_sign_up",
        lambda *_args, **_kwargs: calls.append("signup"),
    )

    app = AppTest.from_function(_render_member_registration).run()
    assert len([b for b in app.button if b.label == "Create account"]) == 1
    app.text_input(key="signup_email").set_value("member@example.com")
    app.text_input(key="signup_password").set_value("Strong123")
    app.text_input(key="signup_password_confirm").set_value("Strong123")
    next(b for b in app.button if b.label == "Create account").click().run()

    assert calls == []
    assert any(
        "Agree to the Terms of Service" in item.value
        for item in app.markdown
    )


def test_one_accepted_signup_advances_directly_to_verification(monkeypatch):
    calls = []
    monkeypatch.setattr(company_auth, "legal_consent_enabled", lambda: True)
    monkeypatch.setattr(company_auth, "current_legal_documents", lambda _client: _documents())
    monkeypatch.setattr(company_auth, "_server_client", lambda: object())

    def begin(*_args, **_kwargs):
        calls.append("signup")
        st.session_state.pending_verification_email = "owner@example.com"

    monkeypatch.setattr(company_auth, "begin_verified_sign_up", begin)
    app = AppTest.from_function(_render_company_registration).run()
    app.text_input(key="signup_company_name").set_value("Workshop")
    app.text_input(key="signup_email").set_value("owner@example.com")
    app.text_input(key="signup_password").set_value("Strong123")
    app.text_input(key="signup_password_confirm").set_value("Strong123")
    app.checkbox(key="company_creation_terms_accepted").check()
    next(b for b in app.button if b.label == "Create Company Account").click().run()

    assert calls == ["signup"]
    rendered = "\n".join(item.value for item in app.markdown)
    assert "Check your email to verify your account" in rendered
    assert not any(b.label == "Create Company Account" for b in app.button)


def test_returning_sign_in_never_discloses_terms_before_authentication(monkeypatch):
    monkeypatch.setattr(company_auth, "legal_consent_enabled", lambda: True)
    app = AppTest.from_function(_render_sign_in).run()

    assert not app.exception
    assert not any(
        checkbox.label == legal_consent.TERMS_CHECKBOX_TEXT
        for checkbox in app.checkbox
    )
    assert not app.expander


def test_verification_screen_is_minimal_and_has_quiet_support_route():
    app = AppTest.from_function(_render_sign_in)
    app.session_state["pending_verification_email"] = "owner@example.com"
    app.run()

    rendered = "\n".join(item.value for item in app.markdown)
    assert "Check your email to verify your account" in rendered
    assert "Contact support" in rendered
    assert "auth-message-card" in rendered
    assert not app.text_input
    assert not app.button


def test_every_company_setup_state_uses_the_shared_auth_template():
    missing = AppTest.from_function(_render_missing_invitation_setup).run()
    create = AppTest.from_function(_render_create_company_setup).run()
    join = AppTest.from_function(_render_join_company_setup).run()

    missing_markup = "\n".join(item.value for item in missing.markdown)
    create_markup = "\n".join(item.value for item in create.markdown)
    join_markup = "\n".join(item.value for item in join.markdown)
    assert "Invitation required" in missing_markup
    assert "auth-message-card" in missing_markup
    assert "Finish creating your company" in create_markup
    assert "Join your company" in join_markup
    assert any(button.label == "Continue" for button in create.button)
    assert any(button.label == "Join company" for button in join.button)
    assert all(not app.exception for app in (missing, create, join))


def test_auth_screen_inventory_uses_one_heading_renderer():
    source = (ROOT / "state/company_auth.py").read_text()
    setup_source = source.split("def render_company_setup", 1)[1].split(
        "def _open_company_account", 1
    )[0]
    expected_headings = {
        "Sign in",
        "Create Your Company Account",
        "Join your company",
        "Check your email to verify your account",
        "This verification link is invalid or has expired",
        "Reset password",
        "Updated Terms of Service",
        "Finish creating your company",
        "Invitation required",
    }
    for heading in expected_headings:
        assert f'_render_auth_heading("{heading}")' in source
    assert "st.title(" not in setup_source


def test_terms_validation_is_part_of_the_first_registration_submit():
    errors = company_auth.registration_validation_errors(
        "owner@example.com",
        "Strong123",
        "Strong123",
        "Workshop",
        False,
    )
    assert errors == {"terms": "Agree to the Terms of Service to continue"}


def test_confirmation_and_permanent_privacy_routes_are_wired():
    wrapper = (ROOT / "cloudflare/index.html").read_text()
    component = (ROOT / "ui/browser_session_component/index.html").read_text()
    redirects = (ROOT / "cloudflare/_redirects").read_text()

    assert '["signup", "email"].includes(recoveryFragment.get("type"))' in wrapper
    assert 'appUrl.searchParams.set("auth_flow", "confirmation")' in wrapper
    assert "costerly:confirmation-fragment-consumed" in wrapper
    assert '<a href="/privacy"' in wrapper
    assert 'args.confirmationRequested' in component
    assert 'confirmation: Boolean(confirmationSession)' in component
    assert "/confirm  /index.html  200" in redirects
    assert "/terms " not in redirects
    assert "/privacy " not in redirects
    assert (ROOT / "cloudflare/terms.html").is_file()
    assert (ROOT / "cloudflare/privacy.html").is_file()


def test_updated_terms_gate_precedes_application_controls():
    app_source = (ROOT / "app.py").read_text()
    gate_position = app_source.index("needs_terms = terms_acceptance_required(")
    controls_position = app_source.index("render_account_control(access)")
    assert gate_position < controls_position

    auth_source = (ROOT / "state/company_auth.py").read_text()
    gate_source = auth_source.split("def render_terms_acceptance", 1)[1].split(
        "def authenticate_invited_creator", 1
    )[0]
    assert '"Sign out"' in gate_source
    assert "on_click=sign_out" in gate_source


def test_terms_gate_uses_the_minimal_updated_terms_heading(monkeypatch):
    monkeypatch.setattr(company_auth, "current_legal_documents", lambda _client: _documents())
    monkeypatch.setattr(company_auth, "_server_client", lambda: object())

    app = AppTest.from_function(_render_terms_gate).run()
    rendered = "\n".join(item.value for item in app.markdown)
    assert '<h1>Updated Terms of Service</h1>' in rendered
    assert "We updated" not in rendered
    assert "We’ve updated" not in rendered
    assert '<span class="auth-terms-title">' not in rendered


def test_terms_heading_uses_the_established_regular_weight_and_disclosure_fades():
    css = (ROOT / "styles/auth.py").read_text()

    assert ".auth-brand-terms-of-service h1" in css
    assert ".auth-brand-updated-terms-of-service h1" in css
    assert "font-size: 40px;" in css
    assert "font-weight: 400;" in css
    assert ".auth-terms-preview" in css
    assert "-webkit-line-clamp: 3;" in css
    assert "mask-image: linear-gradient" in css
    assert "details[open] .auth-terms-preview" in css


def test_terms_gate_uses_the_same_auth_geometry_as_sign_in():
    css = (ROOT / "styles/auth.py").read_text()

    assert "position: absolute;" in css
    assert "top: calc(var(--app-header-top) + 16px);" in css
    assert '[data-testid="stElementContainer"]:has(.costerly-app-header)' in css
    shared_heading_slot = css.split(".auth-brand {", 1)[1].split("}", 1)[0]
    assert "min-height: 90px;" in shared_heading_slot
    assert "margin-bottom: 24px;" in shared_heading_slot
    assert "align-items: center;" in shared_heading_slot
    assert ".auth-message-card" in css


def test_terms_gate_rejects_missing_consent_without_a_server_rerun():
    interactions = (ROOT / "styles/auth.py").read_text()
    gate_source = (ROOT / "state/company_auth.py").read_text().split(
        "def render_terms_acceptance", 1
    )[1].split("def authenticate_invited_creator", 1)[0]
    message = (
        "To continue using Costerly AI, please agree to the updated Terms of Service"
    )

    assert "function setTermsFeedback" in interactions
    assert "event.preventDefault();" in interactions
    assert "event.stopImmediatePropagation();" in interactions
    assert "}, true);" in interactions
    assert message in interactions
    assert message in gate_source


def test_current_legal_documents_identify_the_registered_exempt_dealer():
    terms = (ROOT / "cloudflare/terms.html").read_text()
    privacy = (ROOT / "cloudflare/privacy.html").read_text()

    for document in (terms, privacy):
        assert "Kirill Ginzburg" in document
        assert "קיריל גינזבורג" in document
        assert "346904519" in document
        assert "exempt dealer (osek patur)" in document
        assert "עוסק פטור" not in document


def test_version_one_publication_remains_an_immutable_audit_record():
    publication = (
        ROOT / "db/sql/2026_09_25_publish_legal_documents_v1.sql"
    ).read_text()

    assert "('terms', '1.0'), ('privacy', '1.0')" in publication
    assert "a4f970a69d10f0988b275b704f36bee297ad2a23c53b59853c85895d7bfc6fa4" in publication
    assert "437bd95ede5edef786762d9a5ec185935bf518808d517ddcf7d6a46188f7b17d" in publication


def test_version_one_one_publication_remains_an_immutable_audit_record():
    publication = (
        ROOT / "db/sql/2026_09_25_publish_legal_documents_v1_1.sql"
    ).read_text()

    assert "c57cb8acd7fc91a59d05a6c49bf0fc52b9efbf1e614500a092d59039952630c1" in publication
    assert "96fbec67a23be6b518a60ae42d988a8e86f745de1e2b718f8a32b03131b44801" in publication
    assert "('terms', '1.1'), ('privacy', '1.1')" in publication


def test_terms_one_two_contains_the_agreed_product_and_risk_contract():
    terms = (ROOT / "cloudflare/terms.html").read_text()
    privacy = (ROOT / "cloudflare/privacy.html").read_text()

    required_terms = (
        "Organization Admin",
        "A Member does not represent",
        "invitation links",
        "The Operator is not required to investigate",
        "defend, indemnify and hold harmless",
        "limited, non-exclusive license",
        "need-to-know basis",
        "not used to train or improve the provider's general-purpose models",
        "output generated from Customer Content belongs to the Customer",
        "does not automatically convert into a paid subscription",
        "automatically renews",
        "have no independent cash value",
        "future billing periods after reasonable notice",
        "may be stored indefinitely",
        "Material changes require affected users to accept a new version",
        "future Costerly AI Ltd.",
        "US$100",
        "Tel Aviv-Jaffa",
        "entire agreement",
        "Failure to enforce a provision is not a waiver",
        "events beyond reasonable control",
        "will survive termination",
    )
    for clause in required_terms:
        assert clause in terms
    assert "where configuration permits" not in terms
    assert "where their applicable service terms provide" not in terms
    assert "Coasterly" not in terms + privacy


def test_terms_one_two_closes_customer_user_billing_ai_and_processing_gaps():
    terms = (ROOT / "cloudflare/terms.html").read_text()
    publication = (
        ROOT / "db/sql/2026_09_25_publish_legal_documents_v1_2.sql"
    ).read_text()

    required_terms = (
        "Version 1.2, effective September 25, 2026",
        "The Customer, not an individual user or payer",
        'Organization Admins and Members are collectively "Users."',
        "authorized to create the account for the Customer, accept these Terms for the Customer",
        "A Member does not represent",
        "all acts and omissions of its Users",
        "its Users' acts or omissions",
        "clients, customers, contractors, architects, suppliers, employees, data subjects",
        "trade name, not a separate legal entity",
        "only AI-provider services, account types, contractual terms and technical configurations",
        "A paid subscription belongs to the Customer",
        "identity of the cardholder or payment-method owner does not change the Customer",
        "Customer is the controller and the Operator is the processor",
        "confirmed personal-data breach affecting Customer Content",
        "cross-border transfers needed to provide the service and permitted by applicable law",
        "separate Data Processing Agreement may supplement these Terms",
    )
    for clause in required_terms:
        assert clause in terms

    published_bytes = (
        (ROOT / "cloudflare/terms.html")
        .read_bytes()
        .replace(b"<!--email_off-->", b"")
        .replace(b"<!--/email_off-->", b"")
    )
    assert hashlib.sha256(published_bytes).hexdigest() in publication
    assert "acceptance_version from 2 to 3" in publication
    assert "where document_type = 'terms' and version = '1.1'" in publication


def test_privacy_one_two_matches_the_reviewed_notice_and_tracking_contract():
    privacy_path = ROOT / "cloudflare/privacy.html"
    privacy = privacy_path.read_text()
    publication = (
        ROOT / "db/sql/2026_09_25_publish_privacy_v1_2.sql"
    ).read_text()

    required_privacy = (
        "Version 1.2, effective September 25, 2026",
        "trade name under which the service is operated",
        "registration no. 346904519",
        "Costerly AI is not a separate legal entity",
        "Providing account and contact information is not required by law",
        "If this information is not provided",
        "Customer Content is used to provide, operate, support, secure and troubleshoot",
        "aggregated or de-identified information",
        "service terms, account types and technical configurations",
        "short-lived encrypted session-resume cookie",
        "tab-scoped session storage",
        "first-party browser and server usage, reliability and performance events",
        "does not currently use third-party analytics or advertising cookies or SDKs",
        "transferred from Israel",
        "safeguards required by applicable law for international transfers",
    )
    for clause in required_privacy:
        assert clause in privacy

    assert "develop service functionality" not in privacy
    assert "AI provider engaged for the service must not" not in privacy
    assert "business registration and exempt dealer number" not in privacy

    published_bytes = (
        privacy_path.read_bytes()
        .replace(b"<!--email_off-->", b"")
        .replace(b"<!--/email_off-->", b"")
    )
    assert hashlib.sha256(published_bytes).hexdigest() in publication
    assert "Privacy acceptance_version remains 1" in publication
    assert "requires_reacceptance" in publication
    assert "false" in publication
    assert "where document_type = 'privacy' and version = '1.1'" in publication


def test_migration_keeps_acceptance_evidence_append_only_and_server_written():
    sql = (
        ROOT / "db/sql/2026_09_25_legal_consent_verified_registration.sql"
    ).read_text()
    assert "legal_acceptance_events_append_only" in sql
    assert "legal_acceptance_bindings_append_only" in sql
    assert "grant execute on function public.begin_verified_legal_registration" in sql
    assert "grant execute on function public.complete_verified_legal_registration" in sql
    assert "grant execute on function public.record_current_terms_acceptance" in sql
    assert "from public, anon, authenticated" in sql


def test_migration_is_additive_and_refuses_a_partial_rerun():
    sql = (
        ROOT / "db/sql/2026_09_25_legal_consent_verified_registration.sql"
    ).read_text().lower()

    assert "drop table" not in sql
    assert "drop function" not in sql
    assert "drop trigger" not in sql
    assert "truncate " not in sql
    assert "create or replace" not in sql
    assert "a 3.11.1 legal-consent object already exists" in sql
    assert "required company access tables are missing" in sql


def test_feature_flag_defaults_on_with_explicit_rollback(monkeypatch):
    monkeypatch.delenv("LEGAL_CONSENT_ENABLED", raising=False)
    monkeypatch.setattr(
        legal_consent,
        "get_optional_secret",
        lambda _name, default=None: default,
    )
    assert legal_consent.legal_consent_enabled() is True

    monkeypatch.setattr(legal_consent, "get_optional_secret", lambda *_args: "false")
    assert legal_consent.legal_consent_enabled() is False


def test_returning_user_gate_uses_authenticated_user_and_terms_acceptance_version():
    tables = {
        "legal_document_releases": [
            {"document_type": "terms", "version": "1.1"},
            {"document_type": "privacy", "version": "3.0"},
        ],
        "legal_documents": [
            {
                "document_type": "terms",
                "version": "1.1",
                "acceptance_version": "1",
                "title": "Terms of Service",
                "effective_at": "2026-09-25T00:00:00Z",
                "content_sha256": "a" * 64,
                "public_path": "/terms",
                "requires_reacceptance": False,
                "published_at": "2026-09-25T00:00:00Z",
            },
            {
                "document_type": "privacy",
                "version": "3.0",
                "acceptance_version": "3",
                "title": "Privacy Policy",
                "effective_at": "2026-09-25T00:00:00Z",
                "content_sha256": "b" * 64,
                "public_path": "/privacy",
                "requires_reacceptance": False,
                "published_at": "2026-09-25T00:00:00Z",
            },
        ],
        "legal_acceptance_events": [
            {
                "event_id": "event-1",
                "user_id": "authenticated-user",
                "terms_acceptance_version": "1",
            }
        ],
    }
    client = _Client(tables)

    assert legal_consent.terms_acceptance_required(
        client, "authenticated-user"
    ) is False
    assert legal_consent.terms_acceptance_required(client, "another-user") is True

    tables["legal_documents"][0]["acceptance_version"] = "2"
    assert legal_consent.terms_acceptance_required(
        _Client(tables), "authenticated-user"
    ) is True
    assert legal_consent.has_terms_acceptance_history(
        _Client(tables), "authenticated-user"
    ) is True
    assert legal_consent.has_terms_acceptance_history(
        _Client(tables), "another-user"
    ) is False


def test_confirmation_email_is_branded_direct_and_not_threaded():
    html = (ROOT / "notes/email_templates/confirm_signup.html").read_text()
    subject = (
        ROOT / "notes/email_templates/confirm_signup.subject.txt"
    ).read_text().strip()

    assert "Costerly AI" in html
    assert 'href="{{ .ConfirmationURL }}"' in html
    assert ">Verify email</a>" in html
    assert "costerly-ai-logo.png" in html
    assert "light only" in html
    assert "gmail-blend-difference-black" in html
    assert "{{ .TokenHash }}" in subject
