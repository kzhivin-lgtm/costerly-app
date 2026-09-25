from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from state.session_resume import COOKIE_NAME, COOKIE_TTL_SECONDS


_SESSION_COMPONENT = components.declare_component(
    "costerly_browser_session",
    path=str(Path(__file__).with_name("browser_session_component")),
)


def write_fast_resume_cookie(resume_blob: str) -> None:
    """Persist an opaque resume blob without creating a component callback."""
    cookie_name = json.dumps(COOKIE_NAME)
    cookie_value = json.dumps(resume_blob)
    with st.sidebar:
        components.html(
            f"""
            <script>
            (() => {{
              const name = {cookie_name};
              const value = {cookie_value};
              document.cookie =
                `${{name}}=${{encodeURIComponent(value)}}; ` +
                `Max-Age={COOKIE_TTL_SECONDS}; Path=/; Secure; SameSite=None; Partitioned`;
            }})();
            </script>
            """,
            height=0,
            width=0,
        )


def clear_recovery_browser_route() -> None:
    """Ask the public wrapper to remove the completed recovery route."""
    with st.sidebar:
        components.html(
            """
            <script>
            window.top.postMessage({type: "costerly:recovery-complete"}, "*");
            </script>
            """,
            height=0,
            width=0,
        )


def browser_session_exchange(
    *,
    action: str,
    request_id: str,
    session: dict[str, object] | None = None,
    resume_blob: str | None = None,
    trace_id: str | None = None,
    run_id: str | None = None,
    run_sequence: int | None = None,
    server_elapsed_before_component_ms: float | None = None,
    recovery_requested: bool = False,
    confirmation_requested: bool = False,
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
            traceId=trace_id or "",
            runId=run_id or "",
            runSequence=int(run_sequence or 0),
            serverElapsedBeforeComponentMs=server_elapsed_before_component_ms,
            recoveryRequested=bool(recovery_requested),
            confirmationRequested=bool(confirmation_requested),
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
