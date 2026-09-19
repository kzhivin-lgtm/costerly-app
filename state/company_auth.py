from __future__ import annotations

from dataclasses import dataclass
import re
import secrets
import time
from urllib.parse import urlsplit

import streamlit as st
from supabase import create_client
from supabase_auth.errors import AuthApiError
from postgrest.exceptions import APIError

from config import get_optional_secret
from db.supabase_client import get_supabase_client
from styles.auth import (
    apply_auth_css,
    install_auth_form_interactions,
    render_auth_field_error,
    show_company_creation_started,
)
from use_cases.invite_links import (
    DEFAULT_PUBLIC_APP_URL,
    invite_token_hash,
    invite_url,
    new_invite_token,
    public_app_url,
    valid_invite_token,
)
from use_cases.email_addresses import is_valid_email_address
from ui.app_header import render_account_header_controls
from ui.browser_session import browser_session_exchange, write_fast_resume_cookie
from state.session_resume import restore_resume_session, seal_resume_session


@dataclass(frozen=True)
class CompanyAccess:
    user_id: str
    email: str
    company_id: str | None
    role: str | None
    access_token: str


@dataclass(frozen=True)
class InvitationContext:
    kind: str  # "create" or "join"
    token: str


class ExistingLoginPasswordError(ValueError):
    """An invited signup used an existing email with a different password."""


_LOCAL_REGISTRATION_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _request_uses_localhost(request_url: str | None) -> bool:
    """Identify only explicit local browser origins; test/unknown URLs stay neutral."""
    if not request_url:
        return False
    return (urlsplit(str(request_url)).hostname or "").lower() in _LOCAL_REGISTRATION_HOSTS


def require_public_invitation_request() -> None:
    """Prevent an invitation from creating accounts or companies via localhost."""
    try:
        request_url = str(st.context.url or "")
    except Exception:
        request_url = ""
    if _request_uses_localhost(request_url):
        raise PermissionError(
            "Open this invitation through the public Costerly application. "
            "Company accounts cannot be created on localhost."
        )


def _render_auth_heading(title: str, subtitle: str | None = None) -> None:
    apply_auth_css()
    st.markdown('<div class="auth-screen-active" style="display:none"></div>', unsafe_allow_html=True)
    variant = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    html = (
        f'<div class="auth-brand auth-brand-{variant}">'
        f'<h1>{title}</h1>'
        + (f'<p>{subtitle}</p>' if subtitle else '')
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def validate_registration(
    email: str, password: str, password_confirm: str, company_name: str | None = None
) -> None:
    errors = registration_validation_errors(email, password, password_confirm, company_name)
    if errors:
        raise ValueError(next(iter(errors.values())))


def registration_validation_errors(
    email: str, password: str, password_confirm: str, company_name: str | None = None
) -> dict[str, str]:
    """Return every invalid registration field so one submit marks them all."""
    errors: dict[str, str] = {}
    if company_name is not None and not company_name.strip():
        errors["company"] = "Enter your company name."
    if not is_valid_email_address(email):
        errors["email"] = "Enter an email address like name@company.com."
    if len(password) < 8 or not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
        errors["password"] = "Password needs at least 8 characters, an uppercase letter, a lowercase letter, and a number."
    if not password_confirm:
        errors["confirm"] = "Confirm your password."
    elif password != password_confirm:
        errors["confirm"] = "Passwords do not match."
    return errors


def company_auth_enabled() -> bool:
    """Opt-in until the DB migration and browser policy switch deploy together."""
    return str(get_optional_secret("COMPANY_AUTH_ENABLED", "false")).lower() in {
        "1", "true", "yes", "on",
    }


def _auth_client():
    url = get_optional_secret("SUPABASE_URL")
    key = get_optional_secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Company auth requires SUPABASE_URL and SUPABASE_ANON_KEY.")
    # Do not share an auth client across Streamlit users: its session is mutable.
    return create_client(url, key)


def _server_client():
    if not get_optional_secret("SUPABASE_SERVICE_ROLE_KEY"):
        raise RuntimeError("Company auth requires a server-side service role key.")
    return get_supabase_client()


def _store_auth_session(session: object) -> None:
    if session is None:
        raise RuntimeError("Supabase did not return a sign-in session.")
    st.session_state.auth_access_token = session.access_token
    st.session_state.auth_refresh_token = session.refresh_token
    st.session_state.auth_expires_at = int(session.expires_at or 0)
    resume_blob = seal_resume_session(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_at=int(session.expires_at or 0),
    )
    st.session_state._browser_auth_pending = {
        "action": "store",
        "request_id": secrets.token_urlsafe(12),
        "session": {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": int(session.expires_at or 0),
        },
        "resume_blob": resume_blob,
    }


def sync_browser_auth_session() -> bool:
    """Restore or persist the tab-scoped Supabase session.

    Reads browser storage only while bootstrapping a new Streamlit session.
    Store and clear commands are fire-and-forget so their component render
    cannot schedule a rerun that consumes the next user interaction.
    """
    pending = st.session_state.get("_browser_auth_pending")
    has_memory_session = bool(
        st.session_state.get("auth_access_token")
        and st.session_state.get("auth_refresh_token")
    )
    if (
        not isinstance(pending, dict)
        and not st.session_state.get("_browser_auth_initialized")
        and not has_memory_session
    ):
        outcome, restored = restore_resume_session(st.context.cookies)
        st.session_state._fast_resume_outcome = outcome
        if restored is not None:
            st.session_state.auth_access_token = restored["access_token"]
            st.session_state.auth_refresh_token = restored["refresh_token"]
            st.session_state.auth_expires_at = restored["expires_at"]
            st.session_state._browser_auth_initialized = True
            st.session_state._browser_auth_sync_outcome = "fast_resume_restored"
            return True
    elif "_fast_resume_outcome" not in st.session_state:
        st.session_state._fast_resume_outcome = "not_attempted"

    if isinstance(pending, dict):
        action = str(pending.get("action") or "read")
        request_id = str(pending.get("request_id") or "")
        session = pending.get("session") if isinstance(pending.get("session"), dict) else None
        resume_blob = (
            str(pending.get("resume_blob")) if pending.get("resume_blob") else None
        )
    elif st.session_state.get("_browser_auth_initialized"):
        st.session_state._browser_auth_sync_outcome = "already_initialized"
        return True
    else:
        request_id = st.session_state.setdefault(
            "_browser_auth_read_request", secrets.token_urlsafe(12)
        )
        action = "read"
        session = None
        resume_blob = None

    result = browser_session_exchange(
        action=action,
        request_id=request_id,
        session=session,
        resume_blob=resume_blob,
    )
    if action in {"store", "clear"}:
        st.session_state.pop("_browser_auth_pending", None)
        st.session_state._browser_auth_initialized = True
        st.session_state._browser_auth_sync_outcome = f"{action}_dispatched"
        return True

    if not result or result.get("requestId") != request_id:
        st.session_state._browser_auth_sync_outcome = (
            "memory_session" if has_memory_session else "waiting_for_browser"
        )
        return has_memory_session

    if isinstance(pending, dict):
        st.session_state.pop("_browser_auth_pending", None)

    stored = result.get("session")
    if not has_memory_session and isinstance(stored, dict):
        access_token = stored.get("access_token")
        refresh_token = stored.get("refresh_token")
        if isinstance(access_token, str) and isinstance(refresh_token, str):
            st.session_state.auth_access_token = access_token
            st.session_state.auth_refresh_token = refresh_token
            expires_at = int(stored.get("expires_at") or 0)
            st.session_state.auth_expires_at = expires_at
            resume_blob = seal_resume_session(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            if resume_blob:
                write_fast_resume_cookie(resume_blob)
                st.session_state._fast_resume_outcome = "promoted_from_browser"
    st.session_state._browser_auth_initialized = True
    st.session_state._browser_auth_sync_outcome = (
        "browser_session_restored"
        if not has_memory_session and isinstance(stored, dict)
        else "browser_session_empty"
    )
    return True


def clear_auth_session() -> None:
    for key in list(st.session_state.keys()):
        if key not in {"_app_boot_id", "_runtime_session_id", "_runtime_trace_id"}:
            del st.session_state[key]


def sign_in(email: str, password: str) -> None:
    response = _auth_client().auth.sign_in_with_password(
        {"email": email.strip(), "password": password}
    )
    clear_auth_session()
    _store_auth_session(response.session)


def sign_up(email: str, password: str, invitation: InvitationContext) -> None:
    """Create an invited account without changing project-wide mail settings."""
    require_public_invitation_request()
    if not valid_invite_token(invitation.token) or invitation_from_url() != invitation:
        raise PermissionError("A valid invitation link is required.")
    validate_registration(email, password, password)
    # Admin create_user is server-only and sends no confirmation email.
    # The pilot deliberately accepts unverified email identifiers. The key is
    # never passed to client-side JavaScript.
    _server_client().auth.admin.create_user({
        "email": email.strip(),
        "password": password,
        "email_confirm": True,
    })
    sign_in(email, password)


def authenticate_invited_creator(email: str, password: str, invitation: InvitationContext) -> None:
    """Finish an interrupted signup without offering a second registration path."""
    try:
        sign_in(email, password)
        return
    except AuthApiError as exc:
        if exc.code != "invalid_credentials":
            raise
    try:
        sign_up(email, password, invitation)
    except AuthApiError as exc:
        if exc.code in {"email_exists", "user_already_exists"}:
            raise ExistingLoginPasswordError(
                "This email already has a login. Enter the password from your first attempt."
            ) from exc
        raise


def sign_out() -> None:
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")
    if access_token and refresh_token:
        try:
            client = _auth_client()
            client.auth.set_session(access_token, refresh_token)
            client.auth.sign_out()
        except Exception:
            pass  # Local logout must work even if the network is unavailable.
    clear_auth_session()
    st.session_state._browser_auth_pending = {
        "action": "clear",
        "request_id": secrets.token_urlsafe(12),
        "session": None,
    }


def current_company_access() -> CompanyAccess | None:
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")
    if not access_token or not refresh_token:
        return None

    try:
        client = _auth_client()
        if int(st.session_state.get("auth_expires_at") or 0) <= time.time() + 60:
            refreshed = client.auth.refresh_session(refresh_token)
            _store_auth_session(refreshed.session)
            access_token = st.session_state.auth_access_token
        response = client.auth.get_user(access_token)
        user = response.user if response else None
        if user is None:
            clear_auth_session()
            return None
    except AuthApiError:
        clear_auth_session()
        st.session_state._browser_auth_pending = {
            "action": "clear",
            "request_id": secrets.token_urlsafe(12),
            "session": None,
        }
        return None

    members = (
        _server_client().table("company_members")
        .select("company_id,role")
        .eq("user_id", str(user.id))
        .limit(1)
        .execute()
    )
    company_id = str(members.data[0]["company_id"]) if members.data else None
    role = str(members.data[0]["role"]) if members.data else None
    return CompanyAccess(
        user_id=str(user.id),
        email=str(user.email or ""),
        company_id=company_id,
        role=role,
        access_token=str(access_token),
    )


def invitation_from_url() -> InvitationContext | None:
    token = str(st.query_params.get("invite") or "")
    if not valid_invite_token(token):
        return None
    token_hash = invite_token_hash(token)
    creation = (
        _server_client().table("company_creation_invites")
        .select("used_at")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    ).data or []
    if creation and creation[0].get("used_at") is None:
        return InvitationContext("create", token)
    company = (
        _server_client().table("company_join_links")
        .select("company_id")
        .eq("join_token", token)
        .limit(1)
        .execute()
    ).data or []
    return InvitationContext("join", token) if company else None


def create_company_for_user(
    access: CompanyAccess, display_name: str, invite_token: str
) -> str:
    require_public_invitation_request()
    name = display_name.strip()
    if not name:
        raise ValueError("Company name is required.")
    if access.company_id is not None:
        raise ValueError("This user already belongs to a company.")
    # Revalidate the user and membership before privileged writes.
    fresh = current_company_access()
    if fresh is None or fresh.user_id != access.user_id or fresh.company_id:
        raise PermissionError("Company access changed. Please sign in again.")
    # The existing companies table accepts exactly three numeric characters.
    # RPC creation is transactional; a duplicate company ID leaves the invite
    # unused, so a concurrent signup can safely retry with another ID.
    attempted_ids: set[str] = set()
    for _ in range(12):
        company_id = f"{secrets.randbelow(999) + 1:03d}"
        if company_id in attempted_ids:
            continue
        attempted_ids.add(company_id)
        try:
            result = _server_client().rpc("create_company_from_invite", {
                "p_token_hash": invite_token_hash(invite_token),
                "p_user_id": fresh.user_id,
                "p_company_id": company_id,
                "p_display_name": name,
            }).execute()
            return str(result.data)
        except APIError as exc:
            if exc.code != "23505":
                raise
    raise RuntimeError("No available company ID was allocated. Contact support.")


def join_company_for_user(access: CompanyAccess, invite_token: str) -> str:
    require_public_invitation_request()
    if access.company_id is not None:
        raise PermissionError("This user already belongs to a company.")
    fresh = current_company_access()
    if fresh is None or fresh.user_id != access.user_id or fresh.company_id is not None:
        raise PermissionError("Company access changed. Please sign in again.")
    if not valid_invite_token(invite_token):
        raise ValueError("Invalid company link.")
    result = _server_client().rpc("join_company_by_link", {
        "p_join_token": invite_token,
        "p_user_id": fresh.user_id,
    }).execute()
    return str(result.data)


def company_join_url(access: CompanyAccess) -> str:
    if access.company_id is None or access.role != "owner":
        raise PermissionError("Only the company owner can view the join link.")
    fresh = current_company_access()
    if fresh is None or fresh.user_id != access.user_id or fresh.company_id != access.company_id or fresh.role != "owner":
        raise PermissionError("Company access changed. Please sign in again.")
    rows = (
        _server_client().table("company_join_links")
        .select("join_token")
        .eq("company_id", fresh.company_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise RuntimeError("The company join link is missing.")
    base_url = public_app_url(
        get_optional_secret("COSTERLY_PUBLIC_URL") or DEFAULT_PUBLIC_APP_URL
    )
    return invite_url(base_url, str(rows[0]["join_token"]), "join")


def render_login_or_signup(invitation: InvitationContext | None) -> None:
    install_auth_form_interactions()
    if invitation is not None and invitation.kind == "create":
        _render_auth_heading("Create Your Company Account")
        raw_creation_error = st.session_state.get("company_creation_error") or {}
        creation_errors = (
            {raw_creation_error[0]: raw_creation_error[1]}
            if isinstance(raw_creation_error, tuple)
            else raw_creation_error
        )
        with st.form("company_creation_registration"):
            company_name = st.text_input("Your company name", key="signup_company_name", placeholder="Company name")
            if "company" in creation_errors:
                render_auth_field_error("company", creation_errors["company"])
            email = st.text_input("Email", key="signup_email", placeholder="you@company.com")
            if "email" in creation_errors:
                render_auth_field_error("email", creation_errors["email"])
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            if "password" in creation_errors:
                render_auth_field_error("password", creation_errors["password"])
            if "confirm" in creation_errors:
                render_auth_field_error("confirm", creation_errors["confirm"])
            st.caption("Use at least 8 characters with an uppercase letter, a lowercase letter, and a number.")
            submit = st.form_submit_button("Create Company Account", type="primary", use_container_width=True)
            if "service" in creation_errors:
                st.error(creation_errors["service"])
        install_auth_form_interactions()
        if submit:
            st.session_state.pop("company_creation_error", None)
            validation_errors = registration_validation_errors(email, password, confirm, company_name)
            if validation_errors:
                st.session_state.company_creation_error = validation_errors
                st.rerun()
            try:
                authenticate_invited_creator(email, password, invitation)
                access = current_company_access()
                if access is None:
                    raise RuntimeError("Sign-in session was not returned.")
                if access.company_id is not None:
                    raise ExistingLoginPasswordError(
                        "This email is already registered. Use a different email."
                    )
            except ExistingLoginPasswordError:
                st.session_state.company_creation_error = {
                    "email": "This email is already registered. Use a different email."
                }
                st.rerun()
            except PermissionError as exc:
                st.session_state.company_creation_error = {"service": str(exc)}
                st.rerun()
            except ValueError as exc:
                st.session_state.company_creation_error = {"service": str(exc)}
                st.rerun()
            except AuthApiError as exc:
                message = (
                    "This email is already registered. Use a different email."
                    if exc.code in {"email_exists", "user_already_exists"}
                    else "We couldn't create your login. Check your email and try again."
                )
                field = "email" if exc.code in {"email_exists", "user_already_exists"} else "service"
                st.session_state.company_creation_error = {field: message}
                st.rerun()
            except Exception:
                st.session_state.company_creation_error = {"service": "We couldn't create your login. Try again in a moment."}
                st.rerun()
            try:
                show_company_creation_started()
                create_company_for_user(access, company_name, invitation.token)
                st.session_state.screen = "account"
                if "invite" in st.query_params:
                    del st.query_params["invite"]
                st.rerun()
            except Exception:
                st.session_state.pending_company_name = company_name.strip()
                st.session_state.company_setup_error = "Your login was created, but company setup did not finish. Use this link to try again."
                st.rerun()
        return

    if invitation is not None and invitation.kind == "join":
        _render_auth_heading("Join your company", "Create your own login to work with your team.")
        with st.form("company_join_registration"):
            email = st.text_input("Email", key="signup_email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm password", type="password", key="signup_password_confirm")
            st.caption("At least 8 characters, one uppercase letter, one lowercase letter, and one number.")
            submit = st.form_submit_button("Create account", type="primary")
        install_auth_form_interactions()
        if submit:
            try:
                validate_registration(email, password, confirm)
                sign_up(email, password, invitation)
                access = current_company_access()
                if access is None:
                    raise RuntimeError("Sign-in session was not returned.")
                join_company_for_user(access, invitation.token)
                if "invite" in st.query_params:
                    del st.query_params["invite"]
                st.rerun()
            except PermissionError as exc:
                st.error(str(exc))
            except Exception:
                st.error("We couldn't finish joining this company. If your login was created, sign in using the same link.")
        return

    _render_auth_heading("Sign in")
    login_error = st.session_state.get("company_login_error")
    with st.form("company_login"):
        email = st.text_input("Email", key="login_email", placeholder="you@company.com")
        password = st.text_input("Password", type="password", key="login_password")
        if login_error:
            st.error(login_error)
        submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    install_auth_form_interactions()
    if submit:
        st.session_state.pop("company_login_error", None)
        try:
            sign_in(email, password)
            st.rerun()
        except Exception:
            st.session_state.company_login_error = "Could not sign in. Check your email and password."
            st.rerun()


def render_company_setup(
    access: CompanyAccess, invitation: InvitationContext | None
) -> None:
    if invitation is None:
        st.error("A valid invitation link is required to join or create a company.")
    elif invitation.kind == "create":
        st.title("Finish creating your company")
        st.caption("Pricing and contact details can be added later.")
        if st.session_state.get("company_setup_error"):
            st.error(st.session_state.pop("company_setup_error"))
        with st.form("create_company"):
            name = st.text_input("Company name", value=st.session_state.get("pending_company_name", ""))
            submit = st.form_submit_button("Continue")
        if submit:
            try:
                create_company_for_user(access, name, invitation.token)
                st.session_state.screen = "account"
                if "invite" in st.query_params:
                    del st.query_params["invite"]
                st.rerun()
            except PermissionError as exc:
                st.error(str(exc))
            except Exception:
                st.error("Company setup did not finish. Try again, or contact support if it keeps failing.")
    else:
        st.title("Join your company")
        st.caption("Your company is set by this link. No company selection is needed.")
        join = st.button("Join company", type="primary")
        if join:
            try:
                join_company_for_user(access, invitation.token)
                if "invite" in st.query_params:
                    del st.query_params["invite"]
                st.rerun()
            except PermissionError as exc:
                st.error(str(exc))
            except Exception:
                st.error("This company link is no longer valid.")
    if st.button("Sign out", key="setup_sign_out"):
        sign_out()
        st.rerun()


def render_account_control(access: CompanyAccess) -> None:
    if st.session_state.get("screen") == "account":
        return
    action = render_account_header_controls()
    if action == "profile":
        st.session_state.screen = "account"
        st.rerun()
    if action == "sign_out":
        sign_out()
        st.rerun()


def render_company_account(access: CompanyAccess) -> None:
    from screens.company_profile import render_company_profile

    render_company_profile(access)
