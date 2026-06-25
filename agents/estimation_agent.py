from __future__ import annotations

from agents.anthropic_adapter import run_anthropic_estimation_agent
from agents.prompt_loader import load_estimation_agent_prompt
from agents.schemas.estimation_schema import validate_estimation_result


def run_estimation_agent(
    *,
    file_name: str,
    company_id: str,
    file_bytes: bytes,
    estimate_id: str,
    run_id: str,
    detected_object: dict,
) -> dict:
    """Estimation Agent entrypoint for one detected object."""
    _prompt = load_estimation_agent_prompt()

    if file_bytes is None:
        raise ValueError("Estimation Agent requires uploaded file bytes.")

    result = run_anthropic_estimation_agent(
        file_name=file_name,
        company_id=company_id,
        file_bytes=file_bytes,
        estimate_id=estimate_id,
        run_id=run_id,
        detected_object=detected_object,
    )

    usage_event = result.pop("_agent_usage", None)
    validated = validate_estimation_result(result)
    if usage_event:
        validated["_agent_usage"] = usage_event
    return validated
