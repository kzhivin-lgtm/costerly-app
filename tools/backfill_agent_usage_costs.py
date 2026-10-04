"""Backfill historical Anthropic token costs in the production usage ledger.

Run after deploying the code and applying the Admin v3 SQL migration. The script
only fills null monetary fields for successful Naming requests. It never
overwrites a recorded cost. Mistral OCR is deliberately excluded.
"""

from __future__ import annotations

from typing import Any

from config import calculate_llm_cost_usd
from db.supabase_client import get_supabase_client


def _naming_cost(row: dict[str, Any]) -> dict[str, str | None]:
    usage = row.get("raw_usage") or {}
    return calculate_llm_cost_usd(
        model=str(row.get("model") or ""),
        input_tokens=int(usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("output_tokens") or 0),
    )


def backfill_agent_usage_costs() -> dict[str, int]:
    client = get_supabase_client()
    rows = (
        client.table("agent_usage_events")
        .select("id,agent_name,model,status,total_cost_usd,raw_usage")
        .eq("agent_name", "naming")
        .eq("status", "succeeded")
        .is_("total_cost_usd", "null")
        .execute()
        .data
        or []
    )
    updated = {"naming": 0, "skipped": 0}
    for row in rows:
        costs = _naming_cost(row)
        if not costs.get("total_cost_usd"):
            updated["skipped"] += 1
            continue
        raw_usage = dict(row.get("raw_usage") or {})
        raw_usage["cost_category"] = "detection"
        raw_usage["cost_backfill"] = "anthropic_usage_tokens_2026_10_04"
        client.table("agent_usage_events").update({
            **costs,
            "raw_usage": raw_usage,
        }).eq("id", row["id"]).execute()
        updated["naming"] += 1
    return updated


if __name__ == "__main__":
    print(backfill_agent_usage_costs())
