from __future__ import annotations

import hashlib
import re
import secrets
from typing import Any
from urllib.parse import urlsplit, urlunsplit


_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
DEFAULT_PUBLIC_APP_URL = "https://app.costerly.ai/"
INVITATION_ROUTES = {"start", "join"}


def new_invite_token() -> str:
    """One 256-bit bearer token; no company ID or email is encoded in it."""
    return secrets.token_urlsafe(32)


def valid_invite_token(token: str) -> bool:
    return bool(_TOKEN_PATTERN.fullmatch(token))


def invite_token_hash(token: str) -> str:
    if not valid_invite_token(token):
        raise ValueError("Invalid invitation token format.")
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def invite_url(base_url: str, token: str, route: str) -> str:
    if not valid_invite_token(token):
        raise ValueError("Invalid invitation token format.")
    if route not in INVITATION_ROUTES:
        raise ValueError("Invitation route must be 'start' or 'join'.")
    parts = urlsplit(base_url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.fragment:
        raise ValueError("A public http(s) base URL without a fragment is required.")
    path = f"{parts.path.rstrip('/')}/{route}/{token}"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


def public_app_url(configured_url: str | None = None) -> str:
    """Return the stable public wrapper URL used in every shared invitation."""
    value = (configured_url or DEFAULT_PUBLIC_APP_URL).strip()
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.netloc or parts.fragment:
        raise ValueError("COSTERLY_PUBLIC_URL must be a public https URL without a fragment.")
    hostname = (parts.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Company invitation links cannot use a local address.")
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def create_one_company_link(client: Any, base_url: str, label: str | None = None) -> str:
    """Create the owner and future staff keys, returning only the owner URL."""
    owner_token = new_invite_token()
    staff_token = new_invite_token()
    url = invite_url(public_app_url(base_url), owner_token, "start")  # Validate before touching Supabase.
    client.table("company_creation_invites").insert({
        "token_hash": invite_token_hash(owner_token),
        "join_token": staff_token,
        "label": label.strip() if label else None,
    }).execute()
    return url
