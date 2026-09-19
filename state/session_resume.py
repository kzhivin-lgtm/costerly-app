from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import unquote

from cryptography.fernet import Fernet, InvalidToken

from config import get_optional_secret


COOKIE_NAME = "__Host-costerly-resume-v1"
COOKIE_TTL_SECONDS = 30 * 60
PAYLOAD_VERSION = 1


def fast_resume_enabled() -> bool:
    return str(get_optional_secret("COSTERLY_FAST_RESUME_ENABLED", "false")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _fernet() -> Fernet | None:
    key = get_optional_secret("COSTERLY_SESSION_SEAL_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode("ascii"))
    except (TypeError, ValueError):
        return None


def seal_resume_session(
    *, access_token: str, refresh_token: str, expires_at: int
) -> str | None:
    if not fast_resume_enabled():
        return None
    fernet = _fernet()
    if fernet is None:
        return None
    payload = json.dumps(
        {
            "v": PAYLOAD_VERSION,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": int(expires_at),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return fernet.encrypt(payload).decode("ascii")


def restore_resume_session(
    cookies: Mapping[str, str], *, current_time: int | None = None
) -> tuple[str, dict[str, Any] | None]:
    if not fast_resume_enabled():
        return "disabled", None
    fernet = _fernet()
    if fernet is None:
        return "misconfigured", None
    raw = cookies.get(COOKIE_NAME)
    if not raw:
        return "missing", None
    try:
        token = unquote(str(raw)).encode("ascii")
        if current_time is None:
            decrypted = fernet.decrypt(token, ttl=COOKIE_TTL_SECONDS)
        else:
            decrypted = fernet.decrypt_at_time(
                token,
                ttl=COOKIE_TTL_SECONDS,
                current_time=int(current_time),
            )
        payload = json.loads(decrypted)
    except (InvalidToken, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return "invalid", None
    if not isinstance(payload, dict) or payload.get("v") != PAYLOAD_VERSION:
        return "invalid", None
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_at = payload.get("expires_at")
    if (
        not isinstance(access_token, str)
        or not access_token
        or not isinstance(refresh_token, str)
        or not refresh_token
        or not isinstance(expires_at, int)
    ):
        return "invalid", None
    return (
        "restored",
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        },
    )
