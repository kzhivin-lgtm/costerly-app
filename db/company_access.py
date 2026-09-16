from __future__ import annotations

from supabase import Client


def assert_run_owned(client: Client, run_id: str, company_id: str) -> None:
    """Reject foreign or missing RFQs before any service-role read/write."""
    rows = (
        client.table("rfq_runs")
        .select("company_id")
        .eq("run_id", run_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows or str(rows[0].get("company_id")) != company_id:
        raise PermissionError("RFQ run is not available to this company.")


def assert_estimate_owned(client: Client, estimate_id: str, company_id: str) -> None:
    """Reject foreign or missing estimates before any service-role read/write."""
    rows = (
        client.table("rfq_estimates")
        .select("company_id")
        .eq("estimate_id", estimate_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows or str(rows[0].get("company_id")) != company_id:
        raise PermissionError("Estimate is not available to this company.")


def assert_company_owner(client: Client, user_id: str, company_id: str) -> None:
    """Recheck the owner role before server-side company-wide mutations."""
    rows = (
        client.table("company_members")
        .select("company_id,role")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    ).data or []
    if not rows or rows[0].get("company_id") != company_id or rows[0].get("role") != "owner":
        raise PermissionError("Only the company owner can change company settings.")
