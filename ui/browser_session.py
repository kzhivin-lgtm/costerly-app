from __future__ import annotations

import json
from pathlib import Path

import streamlit.components.v1 as components


_SESSION_COMPONENT = components.declare_component(
    "costerly_browser_session",
    path=str(Path(__file__).with_name("browser_session_component")),
)


def browser_session_exchange(
    *, action: str, request_id: str, session: dict[str, object] | None = None
) -> dict[str, object] | None:
    """Read, write, or clear the browser's persisted Supabase session."""
    raw = _SESSION_COMPONENT(
        action=action,
        requestId=request_id,
        session=session,
        key="costerly_browser_session",
        default=None,
    )
    if not isinstance(raw, str):
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None
