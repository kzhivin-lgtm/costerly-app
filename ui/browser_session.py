from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


_SESSION_COMPONENT = components.declare_component(
    "costerly_browser_session",
    path=str(Path(__file__).with_name("browser_session_component")),
)


def write_fast_resume_cookie(resume_blob: str) -> None:
    """Persist an opaque resume blob through the existing session component."""
    with st.sidebar:
        _SESSION_COMPONENT(
            action="store_resume",
            requestId="",
            session=None,
            resumeBlob=resume_blob,
            key="costerly_fast_resume_writer",
            default=None,
        )


def browser_session_exchange(
    *,
    action: str,
    request_id: str,
    session: dict[str, object] | None = None,
    resume_blob: str | None = None,
) -> dict[str, object] | None:
    """Exchange auth tokens through a zero-height component outside main layout.

    The component always lives in Streamlit's hidden sidebar. It therefore
    cannot become a flex child of the main block container or change any screen
    geometry.
    """
    with st.sidebar:
        raw = _SESSION_COMPONENT(
            action=action,
            requestId=request_id,
            session=session,
            resumeBlob=resume_blob,
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
