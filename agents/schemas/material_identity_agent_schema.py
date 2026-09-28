from __future__ import annotations

from typing import Any, Sequence


IDENTITY_DECISIONS = {
    "link_existing",
    "new_variant",
    "new_material",
    "operation_service",
    "unresolved",
}

MATERIAL_IDENTITY_AGENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decisions"],
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "source_row_id",
                    "decision",
                    "selected_material_id",
                    "confidence",
                    "reason",
                ],
                "properties": {
                    "source_row_id": {"type": "string"},
                    "decision": {
                        "type": "string",
                        "enum": sorted(IDENTITY_DECISIONS),
                    },
                    "selected_material_id": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                    "reason": {"type": "string"},
                },
            },
        }
    },
}


def validate_material_identity_decisions(
    requests: Sequence[dict[str, Any]], result: dict[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(result, dict) or set(result) != {"decisions"}:
        raise ValueError("material identity result fields do not match the contract")
    decisions = result["decisions"]
    if not isinstance(decisions, list):
        raise ValueError("material identity decisions must be a list")
    request_by_id = {str(row["source_row_id"]): row for row in requests}
    if len(request_by_id) != len(requests):
        raise ValueError("material identity request row IDs must be unique")
    seen: set[str] = set()
    required = {
        "source_row_id", "decision", "selected_material_id", "confidence", "reason"
    }
    for row in decisions:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("material identity decision fields do not match the contract")
        source_row_id = str(row["source_row_id"])
        if source_row_id not in request_by_id or source_row_id in seen:
            raise ValueError("material identity decision contains an unknown or duplicate row")
        seen.add(source_row_id)
        if row["decision"] not in IDENTITY_DECISIONS:
            raise ValueError("unsupported material identity decision")
        confidence = row["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 100:
            raise ValueError("material identity confidence must be between 0 and 100")
        selected = str(row["selected_material_id"] or "")
        allowed = {
            str(candidate["material_id"])
            for candidate in request_by_id[source_row_id].get("candidates") or []
        }
        if row["decision"] == "link_existing":
            if not selected or selected not in allowed:
                raise ValueError("selected material must be one of the supplied candidates")
        elif selected:
            raise ValueError("only link_existing may select a material")
    if seen != set(request_by_id):
        raise ValueError("material identity result must decide every requested row")
    return decisions
