from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import html
import json
import re
import secrets
import time
from urllib.parse import urlsplit, urlunsplit

import streamlit as st
from supabase import create_client
from supabase_auth.errors import AuthApiError, AuthError
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
from ui.browser_session import (
    browser_session_exchange,
    clear_recovery_browser_route,
    write_fast_resume_cookie,
)
from state.session_resume import restore_resume_session, seal_resume_session
from state.legal_consent import (
    SUPPORT_EMAIL,
    TERMS_CHECKBOX_TEXT,
    current_legal_documents,
    email_confirmation_url,
    legal_consent_enabled,
    pending_registration_for_user,
    record_current_terms_acceptance,
    record_pending_registration,
    terms_disclosure_content,
)


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
            "Open this invitation through the public Costerly AI application. "
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
    email: str,
    password: str,
    password_confirm: str,
    company_name: str | None = None,
    terms_accepted: bool | None = None,
) -> None:
    errors = registration_validation_errors(
        email,
        password,
        password_confirm,
        company_name,
        terms_accepted,
    )
    if errors:
        raise ValueError(next(iter(errors.values())))


def registration_validation_errors(
    email: str,
    password: str,
    password_confirm: str,
    company_name: str | None = None,
    terms_accepted: bool | None = None,
) -> dict[str, str]:
    """Return every invalid registration field so one submit marks them all."""
    errors: dict[str, str] = {}
    if company_name is not None and not company_name.strip():
        errors["company"] = "Enter your company name"
    if not is_valid_email_address(email):
        errors["email"] = "Enter an email address like name@company.com"
    if len(password) < 8 or not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
        errors["password"] = "Password needs at least 8 characters, an uppercase letter, a lowercase letter and a number"
    if not password_confirm:
        errors["confirm"] = "Confirm your password"
    elif password != password_confirm:
        errors["confirm"] = "Passwords do not match"
    if terms_accepted is False:
        errors["terms"] = "Agree to the Terms of Service to continue"
    return errors


def password_validation_errors(password: str, password_confirm: str) -> dict[str, str]:
    """Apply the registration password policy without requiring an email."""
    errors: dict[str, str] = {}
    if len(password) < 8 or not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password):
        errors["password"] = "Password needs at least 8 characters, an uppercase letter, a lowercase letter and a number"
        return errors
    if not password_confirm:
        errors["confirm"] = "Confirm your password"
    elif password != password_confirm:
        errors["confirm"] = "Passwords do not match"
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


def sync_browser_auth_session(
    *,
    trace_id: str | None = None,
    run_id: str | None = None,
    run_sequence: int | None = None,
    server_elapsed_before_component_ms: float | None = None,
    recovery_requested: bool = False,
    confirmation_requested: bool = False,
) -> bool:
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
        and not recovery_requested
        and not confirmation_requested
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
    elif (
        st.session_state.get("_browser_auth_initialized")
        and not recovery_requested
        and not confirmation_requested
    ):
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
        trace_id=trace_id,
        run_id=run_id,
        run_sequence=run_sequence,
        server_elapsed_before_component_ms=server_elapsed_before_component_ms,
        recovery_requested=recovery_requested,
        confirmation_requested=confirmation_requested,
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
    is_recovery = bool(result.get("recovery"))
    is_confirmation = bool(result.get("confirmation"))
    if not has_memory_session and isinstance(stored, dict):
        access_token = stored.get("access_token")
        refresh_token = stored.get("refresh_token")
        if isinstance(access_token, str) and isinstance(refresh_token, str):
            st.session_state.auth_access_token = access_token
            st.session_state.auth_refresh_token = refresh_token
            expires_at = int(stored.get("expires_at") or 0)
            st.session_state.auth_expires_at = expires_at
            if is_recovery:
                st.session_state.auth_recovery_mode = True
                st.session_state.auth_recovery_email = _token_email_claim(
                    access_token
                )
                st.session_state._fast_resume_outcome = "recovery_session"
            elif is_confirmation:
                st.session_state.auth_confirmation_complete = True
                resume_blob = seal_resume_session(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                )
                if resume_blob:
                    write_fast_resume_cookie(resume_blob)
                    st.session_state._fast_resume_outcome = "confirmation_session"
            else:
                resume_blob = seal_resume_session(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                )
                if resume_blob:
                    write_fast_resume_cookie(resume_blob)
                    st.session_state._fast_resume_outcome = "promoted_from_browser"
    if recovery_requested and not is_recovery:
        st.session_state.auth_recovery_error = True
        st.session_state.auth_recovery_mode = True
    if confirmation_requested and not is_confirmation:
        st.session_state.auth_confirmation_error = True
    st.session_state._browser_auth_initialized = True
    st.session_state._browser_auth_sync_outcome = (
        "browser_session_restored"
        if not has_memory_session and isinstance(stored, dict)
        else "browser_session_empty"
    )
    return True


def password_recovery_url() -> str:
    """Return the exact public recovery route allowed by Supabase Auth."""
    base = public_app_url(
        get_optional_secret("COSTERLY_PUBLIC_URL") or DEFAULT_PUBLIC_APP_URL
    )
    parts = urlsplit(base)
    return urlunsplit((parts.scheme, parts.netloc, "/recover", "", ""))


def request_password_recovery(email: str) -> None:
    """Ask Supabase to send a neutral, expiring recovery link."""
    if not is_valid_email_address(email):
        raise ValueError("Enter an email address like name@company.com")
    started_at = time.perf_counter()
    status = "ok"
    try:
        _auth_client().auth.reset_password_for_email(
            email.strip(),
            {"redirect_to": password_recovery_url()},
        )
    except Exception:
        status = "error"
        raise
    finally:
        st.session_state._runtime_completed_action = {
            "action": "auth_password_recovery_requested",
            "status": status,
            "duration_ms": (time.perf_counter() - started_at) * 1000,
        }


def update_recovered_password(password: str, password_confirm: str) -> None:
    """Update the password only through the verified Supabase recovery session."""
    errors = password_validation_errors(password, password_confirm)
    if errors:
        raise ValueError(next(iter(errors.values())))
    if not st.session_state.get("auth_recovery_mode"):
        raise PermissionError("Open a valid password recovery link first")
    access_token = str(st.session_state.get("auth_access_token") or "")
    refresh_token = str(st.session_state.get("auth_refresh_token") or "")
    if not access_token or not refresh_token:
        raise PermissionError("This password recovery link is no longer valid")
    started_at = time.perf_counter()
    status = "ok"
    error_type = ""
    error_code = ""
    try:
        client = _auth_client()
        client.auth.set_session(access_token, refresh_token)
        client.auth.update_user({"password": password})
    except Exception as exc:
        status = "error"
        error_type = type(exc).__name__
        error_code = str(getattr(exc, "code", "") or "unknown")
        raise
    finally:
        st.session_state._runtime_completed_action = {
            "action": "auth_password_updated",
            "status": status,
            "duration_ms": (time.perf_counter() - started_at) * 1000,
        }
        if error_type:
            st.session_state._runtime_completed_action.update({
                "error_type": error_type,
                "error_code": error_code,
            })


def _password_update_error_message(exc: AuthError) -> str:
    """Return actionable recovery copy without exposing provider details."""
    code = str(getattr(exc, "code", "") or "")
    if code == "weak_password":
        return "Use a stronger password that meets every requirement shown above"
    if code == "same_password":
        return "Choose a password different from your current password"
    if code in {"reauthentication_needed", "reauthentication_not_valid"}:
        return "Request a new password reset link and try again"
    if code in {"invalid_jwt", "session_not_found", "otp_expired"}:
        return "This password recovery link is no longer valid. Request a new one"
    return "We couldn't update your password. Request a new recovery link and try again"


def _submit_password_recovery_request() -> None:
    """Send recovery from Sign in without introducing another auth screen."""
    email = str(st.session_state.get("login_email") or "")
    st.session_state.auth_feedback_id = secrets.token_urlsafe(8)
    st.session_state.pop("company_login_error", None)
    st.session_state.pop("company_login_invalid_fields", None)
    st.session_state.pop("password_recovery_request_error", None)
    st.session_state.pop("password_recovery_request_complete", None)
    if not is_valid_email_address(email):
        st.session_state.password_recovery_request_error = (
            "Enter your email to reset your password"
        )
        return
    try:
        request_password_recovery(email)
    except Exception:
        # Keep the response neutral. Neither account existence nor delivery
        # provider state should be exposed from the Sign in screen.
        pass
    st.session_state.password_recovery_request_complete = True


def _clear_password_recovery(*, updated: bool) -> None:
    """Clear the short-lived recovery session and return to normal Sign in."""
    completed_action = st.session_state.get("_runtime_completed_action")
    clear_auth_session()
    if completed_action:
        st.session_state._runtime_completed_action = completed_action
    st.session_state._browser_auth_pending = {
        "action": "clear",
        "request_id": secrets.token_urlsafe(12),
        "session": None,
    }
    st.session_state.auth_view = "sign_in"
    st.session_state.clear_recovery_browser_route = True
    if updated:
        st.session_state.password_recovery_complete = True
        st.session_state.auth_feedback_id = secrets.token_urlsafe(8)
    if "auth_flow" in st.query_params:
        del st.query_params["auth_flow"]


def _finish_password_recovery() -> None:
    _clear_password_recovery(updated=True)


def _abandon_password_recovery() -> None:
    _clear_password_recovery(updated=False)


def clear_auth_session() -> None:
    for key in list(st.session_state.keys()):
        if key not in {
            "_app_boot_id",
            "_runtime_session_id",
            "_runtime_trace_id",
            "_runtime_run_sequence",
        }:
            del st.session_state[key]


def sign_in(email: str, password: str) -> None:
    started_at = time.perf_counter()
    try:
        response = _auth_client().auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
    except Exception:
        st.session_state._runtime_completed_action = {
            "action": "auth_sign_in",
            "status": "error",
            "duration_ms": (time.perf_counter() - started_at) * 1000,
        }
        raise
    clear_auth_session()
    _store_auth_session(response.session)
    st.session_state._runtime_completed_action = {
        "action": "auth_sign_in",
        "status": "ok",
        "duration_ms": (time.perf_counter() - started_at) * 1000,
    }


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


def begin_verified_sign_up(
    email: str,
    password: str,
    invitation: InvitationContext,
    *,
    organization_name: str | None = None,
) -> None:
    """Create an inactive account and preserve its legal registration context."""
    require_public_invitation_request()
    if not valid_invite_token(invitation.token) or invitation_from_url() != invitation:
        raise PermissionError("A valid invitation link is required.")
    documents = current_legal_documents(_server_client())
    response = _auth_client().auth.sign_up({
        "email": email.strip(),
        "password": password,
        "options": {
            "email_redirect_to": email_confirmation_url(),
            "data": {"costerly_registration": True},
        },
    })
    user = response.user if response else None
    if user is None or not getattr(user, "id", None):
        raise RuntimeError("Supabase did not return the pending user")
    identities = getattr(user, "identities", None)
    if identities is not None and len(identities) == 0:
        # Supabase intentionally returns an obfuscated user for an existing
        # address. Preserve the same visible outcome without fabricating legal
        # evidence for an identity that did not authenticate.
        st.session_state.pending_verification_email = email.strip()
        return
    if getattr(response, "session", None) is not None:
        raise RuntimeError("Email verification is not enabled for new accounts")
    record_pending_registration(
        _server_client(),
        user_id=str(user.id),
        email=email,
        invitation_kind=invitation.kind,
        invitation_token=invitation.token,
        organization_name=organization_name,
        documents=documents,
    )
    st.session_state.pending_verification_email = email.strip()


def _render_registration_terms(documents, *, key: str) -> bool:
    preview, full_terms = terms_disclosure_content()
    st.markdown(
        '<div class="auth-terms-disclosure">'
        '<details>'
        '<summary>'
        '<span class="auth-terms-chevron" aria-hidden="true"></span>'
        f'<span class="auth-terms-preview">{html.escape(preview)}</span>'
        '</summary>'
        f'<div class="auth-terms-full">{full_terms}</div>'
        '</details>'
        '</div>',
        unsafe_allow_html=True,
    )
    accepted = st.checkbox(TERMS_CHECKBOX_TEXT, key=key)
    return bool(accepted)


def render_email_verification_pending() -> None:
    install_auth_form_interactions()
    _render_auth_heading("Check your email to verify your account")
    st.markdown(
        f'<div class="auth-verification-support">Didn\'t receive the email? '
        f'<a href="mailto:{SUPPORT_EMAIL}">Contact support</a></div>',
        unsafe_allow_html=True,
    )


def render_email_confirmation_error() -> None:
    install_auth_form_interactions()
    _render_auth_heading("This verification link is invalid or has expired")
    st.markdown(
        f'<div class="auth-verification-support">'
        f'<a href="/" target="_top">Return to sign in</a> · '
        f'<a href="mailto:{SUPPORT_EMAIL}">Contact support</a></div>',
        unsafe_allow_html=True,
    )


def render_terms_acceptance(access: CompanyAccess) -> None:
    """Block application data until this authenticated user accepts current Terms."""
    install_auth_form_interactions()
    server_client = _server_client()
    documents = current_legal_documents(server_client)
    _render_auth_heading("Updated Terms of Service")
    error = str(st.session_state.get("terms_acceptance_error") or "")
    with st.form("current_terms_acceptance"):
        accepted = _render_registration_terms(documents, key="current_terms_accepted")
        if error:
            render_auth_field_error("terms", error, show_message=True)
        submit = st.form_submit_button(
            "Continue",
            type="primary",
            use_container_width=True,
        )
    st.button(
        "Sign out",
        key="terms_gate_sign_out",
        use_container_width=True,
        on_click=sign_out,
    )
    install_auth_form_interactions()
    if not submit:
        return
    st.session_state.pop("terms_acceptance_error", None)
    if not accepted:
        st.session_state.terms_acceptance_error = (
            "Agree to the Terms of Service to continue"
        )
        st.rerun()
    try:
        record_current_terms_acceptance(
            _server_client(),
            user_id=access.user_id,
            company_id=str(access.company_id or ""),
            email=access.email,
        )
    except Exception:
        st.session_state.terms_acceptance_error = (
            "We couldn't record your agreement. Try again in a moment"
        )
        st.rerun()
    st.session_state.pop("current_terms_accepted", None)
    st.rerun()


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
    started_at = time.perf_counter()
    network_status = "ok"
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")
    if access_token and refresh_token:
        try:
            client = _auth_client()
            client.auth.set_session(access_token, refresh_token)
            client.auth.sign_out()
        except Exception:
            network_status = "error"  # Local logout must still complete.
    clear_auth_session()
    st.session_state._browser_auth_pending = {
        "action": "clear",
        "request_id": secrets.token_urlsafe(12),
        "session": None,
    }
    st.session_state._runtime_completed_action = {
        "action": "auth_sign_out",
        "status": network_status,
        "duration_ms": (time.perf_counter() - started_at) * 1000,
    }


def _submit_login() -> None:
    """Authenticate before Streamlit renders the post-submit script run."""
    email = str(st.session_state.get("login_email") or "")
    password = str(st.session_state.get("login_password") or "")
    st.session_state.auth_feedback_id = secrets.token_urlsafe(8)
    st.session_state.pop("company_login_error", None)
    st.session_state.pop("company_login_invalid_fields", None)
    st.session_state.pop("password_recovery_request_error", None)
    st.session_state.pop("password_recovery_request_complete", None)
    invalid_fields: list[str] = []
    if not is_valid_email_address(email):
        invalid_fields.append("email")
    if not password:
        invalid_fields.append("password")
    if invalid_fields:
        st.session_state.company_login_invalid_fields = invalid_fields
        st.session_state.company_login_error = "Check your email and password"
        return
    try:
        sign_in(email, password)
        access = current_company_access()
        pending_registration = None
        if legal_consent_enabled() and access is not None and access.company_id is None:
            pending_registration = pending_registration_for_user(
                _server_client(),
                access.user_id,
            )
        if access is None or (
            access.company_id is None and pending_registration is None
        ):
            sign_out()
            raise PermissionError("Company access is required")
    except AuthApiError as exc:
        if str(getattr(exc, "code", "")) in {
            "email_not_confirmed",
            "email_not_verified",
        }:
            st.session_state.pending_verification_email = email.strip()
            return
        st.session_state.company_login_invalid_fields = ["email", "password"]
        st.session_state.company_login_error = "Check your email and password"
    except Exception:
        st.session_state.company_login_invalid_fields = ["email", "password"]
        st.session_state.company_login_error = "Check your email and password"


def _verified_token_identity(access_token: str) -> tuple[str, str]:
    """Read identity claims only after Supabase has accepted the token."""
    parts = access_token.split(".")
    if len(parts) != 3:
        raise ValueError("Access token is not a JWT.")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    user_id = claims.get("sub") if isinstance(claims, dict) else None
    email = claims.get("email") if isinstance(claims, dict) else None
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("Verified access token has no subject.")
    return user_id, email if isinstance(email, str) else ""


def _token_email_claim(access_token: str) -> str:
    """Read the recovery email for display only, never for authorization."""
    try:
        parts = access_token.split(".")
        if len(parts) != 3:
            return ""
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
        email = claims.get("email") if isinstance(claims, dict) else None
        return email if isinstance(email, str) else ""
    except (ValueError, TypeError, json.JSONDecodeError):
        return ""


def _company_access_via_rls(access_token: str) -> CompanyAccess:
    """Validate the JWT and read its own membership in one PostgREST request."""
    client = _auth_client()
    client.postgrest.auth(access_token)
    rows = (
        client.table("company_members")
        .select("user_id,company_id,role")
        .limit(1)
        .execute()
    ).data or []
    user_id, email = _verified_token_identity(access_token)
    membership = rows[0] if rows else {}
    member_user_id = membership.get("user_id")
    if member_user_id is not None and str(member_user_id) != user_id:
        raise PermissionError("Company membership identity does not match the session.")
    return CompanyAccess(
        user_id=user_id,
        email=email,
        company_id=(
            str(membership["company_id"])
            if membership.get("company_id") is not None
            else None
        ),
        role=(
            str(membership["role"])
            if membership.get("role") is not None
            else None
        ),
        access_token=access_token,
    )


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
        try:
            return _company_access_via_rls(str(access_token))
        except (APIError, AttributeError, UnicodeError, ValueError):
            # Compatibility fallback preserves the established auth path if the
            # installed client or production schema cannot use the RLS shortcut.
            pass
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
    member_invites = (
        _server_client().table("company_member_invites")
        .select("expires_at,used_at")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    ).data or []
    if not member_invites or member_invites[0].get("used_at") is not None:
        return None
    expires_at = str(member_invites[0].get("expires_at") or "")
    try:
        expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if expires <= datetime.now(timezone.utc):
        return None
    return InvitationContext("join", token)


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
    result = _server_client().rpc("join_company_by_one_time_invite", {
        "p_token_hash": invite_token_hash(invite_token),
        "p_user_id": fresh.user_id,
    }).execute()
    return str(result.data)


def create_company_join_url(access: CompanyAccess) -> str:
    """Create one bearer invitation that expires in 24 hours."""
    if access.company_id is None or access.role != "owner":
        raise PermissionError("Only the company owner can create an invitation.")
    fresh = current_company_access()
    if fresh is None or fresh.user_id != access.user_id or fresh.company_id != access.company_id or fresh.role != "owner":
        raise PermissionError("Company access changed. Please sign in again.")
    token = new_invite_token()
    now = datetime.now(timezone.utc)
    _server_client().table("company_member_invites").insert({
        "token_hash": invite_token_hash(token),
        "company_id": fresh.company_id,
        "created_by": fresh.user_id,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=24)).isoformat(),
    }).execute()
    base_url = public_app_url(
        get_optional_secret("COSTERLY_PUBLIC_URL") or DEFAULT_PUBLIC_APP_URL
    )
    return invite_url(base_url, token, "join")


def remove_company_member(access: CompanyAccess, member_user_id: str) -> None:
    if access.company_id is None or access.role != "owner":
        raise PermissionError("Only the company owner can remove access.")
    fresh = current_company_access()
    if (
        fresh is None
        or fresh.user_id != access.user_id
        or fresh.company_id != access.company_id
        or fresh.role != "owner"
    ):
        raise PermissionError("Company access changed. Please sign in again.")
    target = str(member_user_id or "").strip()
    if not target:
        raise ValueError("Company member is required.")
    if target == fresh.user_id:
        raise PermissionError("The company owner cannot be removed.")
    _server_client().rpc("remove_company_member_access", {
        "p_company_id": fresh.company_id,
        "p_owner_id": fresh.user_id,
        "p_member_id": target,
    }).execute()


def render_login_or_signup(invitation: InvitationContext | None) -> None:
    install_auth_form_interactions()
    if st.session_state.get("pending_verification_email"):
        render_email_verification_pending()
        return
    if st.session_state.get("auth_confirmation_error"):
        render_email_confirmation_error()
        return
    if invitation is not None and invitation.kind == "create":
        _render_auth_heading("Create Your Company Account")
        legal_documents = None
        if legal_consent_enabled():
            try:
                legal_documents = current_legal_documents(_server_client())
            except Exception:
                st.error("Registration is temporarily unavailable. Try again later")
                st.stop()
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
            st.caption("Use at least 8 characters with an uppercase letter, a lowercase letter and a number")
            terms_accepted = True
            if legal_documents is not None:
                terms_accepted = _render_registration_terms(
                    legal_documents,
                    key="company_creation_terms_accepted",
                )
                if "terms" in creation_errors:
                    render_auth_field_error(
                        "terms",
                        creation_errors["terms"],
                        show_message=True,
                    )
            submit = st.form_submit_button("Create Company Account", type="primary", use_container_width=True)
            if "service" in creation_errors:
                st.error(creation_errors["service"])
        install_auth_form_interactions()
        if submit:
            st.session_state.pop("company_creation_error", None)
            validation_errors = registration_validation_errors(
                email,
                password,
                confirm,
                company_name,
                terms_accepted if legal_documents is not None else None,
            )
            if validation_errors:
                st.session_state.company_creation_error = validation_errors
                st.rerun()
            try:
                if legal_documents is not None:
                    begin_verified_sign_up(
                        email,
                        password,
                        invitation,
                        organization_name=company_name,
                    )
                    st.rerun()
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
        _render_auth_heading("Join your company")
        legal_documents = None
        if legal_consent_enabled():
            try:
                legal_documents = current_legal_documents(_server_client())
            except Exception:
                st.error("Registration is temporarily unavailable. Try again later")
                st.stop()
        raw_join_error = st.session_state.get("company_join_error") or {}
        join_errors = (
            {raw_join_error[0]: raw_join_error[1]}
            if isinstance(raw_join_error, tuple)
            else raw_join_error
        )
        with st.form("company_join_registration"):
            email = st.text_input("Email", key="signup_email", placeholder="you@company.com")
            if "email" in join_errors:
                render_auth_field_error("email", join_errors["email"])
            password = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm password", type="password", key="signup_password_confirm")
            if "password" in join_errors:
                render_auth_field_error("password", join_errors["password"])
            if "confirm" in join_errors:
                render_auth_field_error("confirm", join_errors["confirm"])
            st.caption("At least 8 characters, one uppercase letter, one lowercase letter and one number")
            terms_accepted = True
            if legal_documents is not None:
                terms_accepted = _render_registration_terms(
                    legal_documents,
                    key="company_join_terms_accepted",
                )
                if "terms" in join_errors:
                    render_auth_field_error(
                        "terms",
                        join_errors["terms"],
                        show_message=True,
                    )
            submit = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )
            if "service" in join_errors:
                st.error(join_errors["service"])
        install_auth_form_interactions()
        if submit:
            st.session_state.pop("company_join_error", None)
            validation_errors = registration_validation_errors(
                email,
                password,
                confirm,
                terms_accepted=(
                    terms_accepted if legal_documents is not None else None
                ),
            )
            if validation_errors:
                st.session_state.company_join_error = validation_errors
                st.rerun()
            try:
                if legal_documents is not None:
                    begin_verified_sign_up(email, password, invitation)
                    st.rerun()
                sign_up(email, password, invitation)
                access = current_company_access()
                if access is None:
                    raise RuntimeError("Sign-in session was not returned.")
                join_company_for_user(access, invitation.token)
                if "invite" in st.query_params:
                    del st.query_params["invite"]
                st.rerun()
            except PermissionError as exc:
                st.session_state.company_join_error = {"service": str(exc)}
                st.rerun()
            except AuthApiError as exc:
                message = (
                    "This email is already registered. Sign in using the same company link."
                    if exc.code in {"email_exists", "user_already_exists"}
                    else "We couldn't create your login. Check your email and try again."
                )
                field = (
                    "email"
                    if exc.code in {"email_exists", "user_already_exists"}
                    else "service"
                )
                st.session_state.company_join_error = {field: message}
                st.rerun()
            except Exception:
                st.session_state.company_join_error = {
                    "service": (
                        "We couldn't finish joining this company. If your login was "
                        "created, sign in using the same link."
                    )
                }
                st.rerun()
        return

    _render_auth_heading("Sign in")
    login_error = st.session_state.get("company_login_error")
    login_invalid_fields = set(
        st.session_state.get("company_login_invalid_fields") or []
    )
    recovery_request_error = st.session_state.get("password_recovery_request_error")
    recovery_request_complete = st.session_state.get(
        "password_recovery_request_complete", False
    )
    recovery_complete = st.session_state.pop("password_recovery_complete", False)
    if st.session_state.pop("clear_recovery_browser_route", False):
        clear_recovery_browser_route()
    with st.form("company_login"):
        st.text_input("Email", key="login_email", placeholder="you@company.com")
        password_label, recovery_action = st.columns(
            [0.7, 0.3],
            gap=None,
            vertical_alignment="center",
        )
        with password_label:
            st.markdown(
                '<span class="auth-password-row-marker">Password</span>',
                unsafe_allow_html=True,
            )
        with recovery_action:
            if not recovery_request_complete:
                st.form_submit_button(
                    "Forgot password?",
                    on_click=_submit_password_recovery_request,
                )
        st.text_input(
            "Password",
            type="password",
            key="login_password",
            label_visibility="collapsed",
        )
        if "email" in login_invalid_fields:
            render_auth_field_error(
                "email",
                "Enter an email address like name@company.com",
            )
        if "password" in login_invalid_fields:
            render_auth_field_error(
                "password",
                "Password needs at least 8 characters, an uppercase letter, a lowercase letter and a number",
            )
        if recovery_request_error:
            render_auth_field_error("email", str(recovery_request_error))
        feedback_message = ""
        feedback_kind = ""
        if recovery_request_error:
            feedback_message = "Enter your email to reset your password"
            feedback_kind = "error"
        elif login_error:
            feedback_message = "Check your email and password"
            feedback_kind = "error"
        elif recovery_request_complete:
            feedback_message = (
                "If an account exists for this email, we sent a password reset link"
            )
            feedback_kind = "notice"
        elif recovery_complete:
            feedback_message = (
                "Your password has been updated. Sign in with your new password"
            )
            feedback_kind = "success"
        if feedback_message:
            feedback_id = str(
                st.session_state.get("auth_feedback_id") or "auth-feedback"
            )
            feedback_classes = (
                f"auth-form-feedback auth-form-feedback-{feedback_kind}"
            )
            if feedback_kind == "error":
                feedback_classes += " auth-form-feedback-dismissible"
            st.markdown(
                f'<div class="{feedback_classes}" '
                f'data-auth-feedback-id="{feedback_id}" '
                f'role="{"alert" if feedback_kind == "error" else "status"}">'
                f"{feedback_message}</div>",
                unsafe_allow_html=True,
            )
        if recovery_request_complete:
            st.markdown(
                '<span class="auth-recovery-sent" role="status"></span>',
                unsafe_allow_html=True,
            )
        st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True,
            on_click=_submit_login,
        )
    install_auth_form_interactions()


def render_password_reset() -> None:
    """Render the authenticated password update step for a recovery link."""
    install_auth_form_interactions()
    _render_auth_heading("Reset password")
    if st.session_state.get("auth_recovery_error"):
        st.error("This password recovery link is invalid or has expired")
        st.button(
            "Return to sign in",
            key="invalid_recovery_return",
            use_container_width=True,
            on_click=_abandon_password_recovery,
        )
        return

    raw_error = st.session_state.get("password_reset_error") or {}
    errors = raw_error if isinstance(raw_error, dict) else {"service": str(raw_error)}
    with st.form("password_recovery_update"):
        st.text_input(
            "Email",
            value=str(st.session_state.get("auth_recovery_email") or ""),
            key="recovery_email",
            disabled=True,
        )
        password = st.text_input(
            "New password",
            type="password",
            key="recovery_password",
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="recovery_password_confirm",
        )
        if "password" in errors:
            render_auth_field_error(
                "password",
                errors["password"],
                show_message=True,
            )
        if "confirm" in errors:
            render_auth_field_error(
                "confirm",
                errors["confirm"],
                show_message=True,
            )
        if not ({"password", "confirm"} & errors.keys()):
            st.caption(
                "At least 8 characters, one uppercase letter, one lowercase letter and one number"
            )
        submit = st.form_submit_button(
            "Reset password",
            type="primary",
            use_container_width=True,
        )
        if "service" in errors:
            st.error(errors["service"])
    install_auth_form_interactions()
    if submit:
        st.session_state.pop("password_reset_error", None)
        validation_errors = password_validation_errors(password, confirm)
        if validation_errors:
            st.session_state.password_reset_error = validation_errors
            st.rerun()
        try:
            update_recovered_password(password, confirm)
        except PermissionError as exc:
            st.session_state.password_reset_error = {"service": str(exc)}
            st.rerun()
        except AuthError as exc:
            st.session_state.password_reset_error = {
                "service": _password_update_error_message(exc)
            }
            st.rerun()
        except Exception:
            st.session_state.password_reset_error = {
                "service": "We couldn't update your password. Request a new recovery link and try again"
            }
            st.rerun()
        _finish_password_recovery()
        st.rerun()


def render_company_setup(
    access: CompanyAccess, invitation: InvitationContext | None
) -> None:
    st.markdown(
        '<div class="company-setup-active" style="display:none"></div>',
        unsafe_allow_html=True,
    )
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
    st.button("Sign out", key="setup_sign_out", on_click=sign_out)


def _open_company_account() -> None:
    """Set navigation state before Streamlit starts the Profile render."""
    from state.session import set_screen

    set_screen("account")


def render_account_control(access: CompanyAccess) -> None:
    if st.session_state.get("screen") == "account":
        return
    render_account_header_controls(
        on_profile=_open_company_account,
        on_sign_out=sign_out,
        show_projects=st.session_state.get("screen", "upload") == "upload",
    )


def render_company_account(access: CompanyAccess, *, trace=None) -> None:
    if trace is None:
        from screens.company_profile import render_company_profile

        render_company_profile(access)
        return

    with trace.span("server.company_profile_import"):
        from screens.company_profile import render_company_profile

    with trace.span("server.company_profile_render"):
        render_company_profile(access, trace=trace)
