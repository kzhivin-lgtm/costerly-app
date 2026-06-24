from __future__ import annotations

from agents.anthropic_adapter import run_anthropic_detection_agent_with_fallback
from agents.prompt_loader import load_detection_agent_prompt
from agents.schemas.detection_schema import validate_detection_result


def get_secret(name: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass

    return default


def run_detection_agent(
    file_name: str,
    company_id: str = "001",
    file_bytes: bytes | None = None,
) -> dict:
    """
    Detection Agent entrypoint.

    Runs the real Claude-backed Detection Agent.
    """

    # Fail loudly if the prompt file is missing or empty.
    _prompt = load_detection_agent_prompt()

    if file_bytes is None:
        raise ValueError("Detection Agent requires uploaded file bytes.")

    result = run_anthropic_detection_agent_with_fallback(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
    )
    return validate_detection_result(result)
