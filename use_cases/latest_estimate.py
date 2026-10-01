from __future__ import annotations


def load_latest_estimate_route(client, company_id: str) -> dict[str, str] | None:
    """Return the newest company-owned estimate that can reopen Objects.

    Estimate rows are durable while browser session state is not.  This lookup
    intentionally reads only the owning company's latest shell and never
    creates, recalculates, or mutates an estimate.
    """
    rows = (
        client.table("rfq_estimates")
        .select("estimate_id,run_id")
        .eq("company_id", str(company_id))
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    row = rows[0]
    estimate_id = str(row.get("estimate_id") or "")
    run_id = str(row.get("run_id") or "")
    if not estimate_id or not run_id:
        return None
    return {"estimate_id": estimate_id, "run_id": run_id}
