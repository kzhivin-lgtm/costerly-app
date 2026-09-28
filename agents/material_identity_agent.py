from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_ESTIMATION_MODEL,
    create_claude_message,
    extract_text_from_claude_response,
    get_anthropic_client,
    get_secret,
    strip_schema_for_claude,
)
from agents.schemas.material_identity_agent_schema import (
    MATERIAL_IDENTITY_AGENT_SCHEMA,
    validate_material_identity_decisions,
)


MATERIAL_IDENTITY_AGENT_VERSION = "material_identity_agent_v1_bounded_batch"
PROMPT_PATH = Path(__file__).parent / "prompts" / "material_identity_agent_prompt.md"
MAX_BATCH_ROWS = 60


def run_material_identity_agent(
    requests: Sequence[dict[str, Any]], *, model: str | None = None
) -> list[dict[str, Any]]:
    """Decide one bounded shortlist batch without database or retry access."""
    if not requests:
        return []
    if len(requests) > MAX_BATCH_ROWS:
        raise ValueError(f"material identity batch exceeds {MAX_BATCH_ROWS} rows")
    for row in requests:
        if len(row.get("candidates") or []) > 5:
            raise ValueError("material identity shortlist exceeds five candidates")
    selected_model = model or get_secret(
        "CLAUDE_MATERIAL_IDENTITY_MODEL", DEFAULT_CLAUDE_ESTIMATION_MODEL
    )
    response = create_claude_message(
        get_anthropic_client().with_options(timeout=45.0, max_retries=0),
        model=selected_model,
        max_tokens=8192,
        temperature=0,
        system=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        messages=[{
            "role": "user",
            "content": [{
                "type": "text",
                "text": "Resolve this bounded batch once:\n"
                + json.dumps(list(requests), ensure_ascii=False, separators=(",", ":")),
            }],
        }],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": strip_schema_for_claude(MATERIAL_IDENTITY_AGENT_SCHEMA),
            }
        },
    )
    result = json.loads(extract_text_from_claude_response(response))
    return validate_material_identity_decisions(requests, result)
