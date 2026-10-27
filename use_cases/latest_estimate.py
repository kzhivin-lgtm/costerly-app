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


def load_latest_file_review_route(client, company_id: str) -> dict[str, str] | None:
    """Return the newest successfully processed RFQ for the header restore action.

    File Review is available before a user presses Continue and creates an
    ``rfq_estimates`` shell.  The header action therefore must be based on the
    completed Processing ledger, not on estimates alone.  This avoids opening
    an unrelated older file after ``New Estimate``.
    """
    rows = (
        client.table("agent_usage_events")
        .select("run_id")
        .eq("company_id", str(company_id))
        .eq("agent_name", "orchestration")
        .eq("operation", "rfq_processing_cycle")
        .eq("status", "succeeded")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    run_id = str(rows[0].get("run_id") or "").strip()
    return {"estimate_id": "", "run_id": run_id} if run_id else None


def load_latest_estimate_route_for_run(
    client,
    company_id: str,
    run_id: str,
) -> dict[str, str] | None:
    """Return the newest durable estimate for one already-authorized RFQ run."""
    rows = (
        client.table("rfq_estimates")
        .select("estimate_id,run_id")
        .eq("company_id", str(company_id))
        .eq("run_id", str(run_id))
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
    persisted_run_id = str(row.get("run_id") or "")
    if not estimate_id or persisted_run_id != str(run_id):
        return None
    return {"estimate_id": estimate_id, "run_id": persisted_run_id}
