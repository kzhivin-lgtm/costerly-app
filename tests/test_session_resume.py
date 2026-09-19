from __future__ import annotations

import json
from urllib.parse import quote

from cryptography.fernet import Fernet

from state import session_resume


def _configure(monkeypatch, key: str, *, enabled: bool = True) -> None:
    values = {
        "COSTERLY_FAST_RESUME_ENABLED": "true" if enabled else "false",
        "COSTERLY_SESSION_SEAL_KEY": key,
    }
    monkeypatch.setattr(
        session_resume,
        "get_optional_secret",
        lambda name, default=None: values.get(name, default),
    )


def test_resume_blob_round_trip_is_opaque_and_cookie_safe(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    _configure(monkeypatch, key)

    blob = session_resume.seal_resume_session(
        access_token="access-private",
        refresh_token="refresh-private",
        expires_at=1234567890,
    )

    assert blob is not None
    assert "access-private" not in blob
    assert "refresh-private" not in blob
    outcome, restored = session_resume.restore_resume_session(
        {session_resume.COOKIE_NAME: quote(blob)}
    )
    assert outcome == "restored"
    assert restored == {
        "access_token": "access-private",
        "refresh_token": "refresh-private",
        "expires_at": 1234567890,
    }


def test_resume_blob_rejects_tamper_and_expiry(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    _configure(monkeypatch, key)
    payload = json.dumps(
        {
            "v": session_resume.PAYLOAD_VERSION,
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_at": 123,
        }
    ).encode()
    issued_at = 1000
    blob = Fernet(key.encode()).encrypt_at_time(payload, issued_at).decode()

    outcome, restored = session_resume.restore_resume_session(
        {session_resume.COOKIE_NAME: blob + "tampered"}, current_time=issued_at + 1
    )
    assert (outcome, restored) == ("invalid", None)

    outcome, restored = session_resume.restore_resume_session(
        {session_resume.COOKIE_NAME: blob},
        current_time=issued_at + session_resume.COOKIE_TTL_SECONDS + 1,
    )
    assert (outcome, restored) == ("invalid", None)


def test_resume_disabled_or_misconfigured_falls_back(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    _configure(monkeypatch, key, enabled=False)
    assert session_resume.restore_resume_session({}) == ("disabled", None)
    assert (
        session_resume.seal_resume_session(
            access_token="access", refresh_token="refresh", expires_at=123
        )
        is None
    )

    _configure(monkeypatch, "invalid-key")
    assert session_resume.restore_resume_session({}) == ("misconfigured", None)


def test_representative_resume_blob_fits_one_cookie(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    _configure(monkeypatch, key)
    blob = session_resume.seal_resume_session(
        access_token="a" * 2000,
        refresh_token="r" * 128,
        expires_at=1234567890,
    )
    assert blob is not None
    assert len(blob) < 3800
