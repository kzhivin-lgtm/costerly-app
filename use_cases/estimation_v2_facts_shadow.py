"""Fail-isolated Estimation v2 Object Facts shadow coordinator."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from agents.estimation_v2_facts_agent import (
    ESTIMATION_V2_FACTS_AGENT_VERSION,
    run_estimation_v2_facts_agent,
)
from db.repositories import (
    fetch_active_israel_material_families,
    fetch_estimation_v2_fact_result,
    insert_agent_usage_event_returning_id,
    insert_estimation_v2_fact_result,
)


def run_estimation_v2_facts_shadow_batch(
    *,
    client: Any,
    inputs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Extract and persist facts without affecting the active estimate workflow."""
    families = fetch_active_israel_material_families(client)
    if not families:
        return {
            "created_result_ids": [],
            "reused_input_ids": [],
            "failed": {
                str(row.get("input_id") or "unknown"): "active_israel_material_family_catalog_empty"
                for row in inputs
            },
        }

    created: list[str] = []
    reused: list[str] = []
    failed: dict[str, str] = {}
    for row in inputs:
        input_id = str(row.get("input_id") or "").strip()
        payload = row.get("input_payload")
        revision = row.get("object_input_revision", 1)
        if not input_id or not isinstance(payload, Mapping):
            failed[input_id or "unknown"] = "invalid_shadow_input"
            continue
        try:
            existing = fetch_estimation_v2_fact_result(
                client,
                input_id=input_id,
                agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION,
            )
            if existing:
                reused.append(input_id)
                continue
            result = run_estimation_v2_facts_agent(
                input_id=input_id,
                object_input_revision=int(revision),
                estimation_input=payload,
                allowed_material_families=families,
            )
            usage_id = insert_agent_usage_event_returning_id(client, result["usage_event"])
            created.append(insert_estimation_v2_fact_result(
                client,
                input_id=input_id,
                agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION,
                facts_payload=result["facts"],
                agent_usage_event_id=usage_id,
            ))
        except Exception as exc:
            failed[input_id] = f"{type(exc).__name__}: {exc}"
    return {
        "created_result_ids": created,
        "reused_input_ids": reused,
        "failed": failed,
    }
