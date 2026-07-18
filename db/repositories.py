from __future__ import annotations

from datetime import UTC, datetime
import json

import pandas as pd
from supabase import Client


def fetch_table(
    client: Client,
    table_name: str,
    order_by: str | None = None,
    filters: dict | None = None,
) -> pd.DataFrame:
    query = client.table(table_name).select("*")

    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)

    if order_by:
        query = query.order(order_by)

    response = query.execute()
    return pd.DataFrame(response.data or [])


def fetch_company_data(client: Client, company_id: str) -> dict[str, pd.DataFrame]:
    return {
        "labor": fetch_table(client, "labor", filters={"company_id": company_id}),
        "materials": fetch_table(client, "materials", filters={"company_id": company_id}),
        "works": fetch_table(client, "works", order_by="sort_order", filters={"company_id": company_id}),
        "company_machines": fetch_table(client, "company_machines", order_by="industry", filters={"company_id": company_id}),
        "overhead_settings": fetch_table(client, "overhead_settings", filters={"company_id": company_id}),
        "overhead_monthly": fetch_table(client, "overhead_monthly", filters={"company_id": company_id}),
        "work_drivers": fetch_table(client, "work_drivers", order_by="sort_order"),
        "machining_point_rules": fetch_table(client, "machining_point_rules", order_by="sort_order"),
    }


def fetch_company_overhead_settings(client: Client, company_id: str) -> pd.DataFrame:
    return fetch_table(client, "overhead_settings", filters={"company_id": company_id})


def fetch_estimate_driver_quantities(
    client: Client,
    company_id: str,
    estimate_id: str,
    object_id: str | None = None,
) -> pd.DataFrame:
    filters = {"company_id": company_id, "estimate_id": estimate_id}
    if object_id:
        filters["object_id"] = object_id

    return fetch_table(
        client,
        "estimate_driver_quantities",
        order_by="driver_code",
        filters=filters,
    )


def upsert_rfq_detection_result(client: Client, detection_result: dict) -> None:
    rfq_run = detection_result["rfq_run"]
    detected_objects = detection_result["detected_objects"]

    run_id = rfq_run["run_id"]

    client.table("rfq_runs").upsert(
        rfq_run,
        on_conflict="run_id",
    ).execute()

    client.table("rfq_detected_objects").delete().eq(
        "run_id",
        run_id,
    ).execute()

    if detected_objects:
        client.table("rfq_detected_objects").upsert(
            detected_objects,
            on_conflict="run_id,object_id",
        ).execute()


def insert_agent_usage_event(client: Client, usage_event: dict) -> None:
    """Persist one LLM usage ledger event for cost-efficiency tracking."""
    try:
        client.table("agent_usage_events").insert(usage_event).execute()
    except Exception as exc:
        # Keep timing data in raw_usage until the duration_seconds migration is applied.
        if "duration_seconds" not in str(exc):
            raise
        legacy_event = dict(usage_event)
        duration_seconds = legacy_event.pop("duration_seconds", None)
        raw_usage = dict(legacy_event.get("raw_usage") or {})
        raw_usage["duration_seconds"] = duration_seconds
        legacy_event["raw_usage"] = raw_usage
        client.table("agent_usage_events").insert(legacy_event).execute()


def fetch_rfq_run(client: Client, run_id: str) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_runs",
        filters={"run_id": run_id},
    )


def fetch_rfq_detected_objects(client: Client, run_id: str) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_detected_objects",
        order_by="object_id",
        filters={"run_id": run_id},
    )


def fetch_agent_usage_events(client: Client, run_id: str) -> pd.DataFrame:
    """Load persisted runtime/cost events for one RFQ run."""
    return fetch_table(
        client,
        "agent_usage_events",
        order_by="created_at",
        filters={"run_id": run_id},
    )


def fetch_latest_ocr_result(client: Client, run_id: str) -> dict | None:
    """Load the latest complete OCR result and Detection handoff for a run."""
    response = (
        client.table("agent_usage_events")
        .select("raw_usage")
        .eq("run_id", run_id)
        .eq("agent_name", "ocr")
        .eq("operation", "document_ocr")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None

    raw_usage = response.data[0].get("raw_usage") or {}
    if isinstance(raw_usage, str):
        try:
            raw_usage = json.loads(raw_usage)
        except (TypeError, ValueError):
            return None
    if not isinstance(raw_usage, dict):
        return None

    ocr_result = raw_usage.get("ocr_result")
    if not isinstance(ocr_result, dict):
        return None
    return {
        "ocr_result": ocr_result,
        "detection_context": str(raw_usage.get("detection_context") or ""),
    }


def update_rfq_detected_object(
    client: Client,
    *,
    run_id: str,
    object_id: str,
    values: dict,
) -> None:
    """Persist user edits from File Review before estimation starts."""
    client.table("rfq_detected_objects").update(values).eq(
        "run_id",
        run_id,
    ).eq(
        "object_id",
        object_id,
    ).execute()


def upsert_rfq_estimate_shell(
    client: Client,
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    object_estimates: list[dict],
) -> None:
    """Create the estimation work shell without running the Estimation Agent."""
    client.table("rfq_estimates").upsert(
        {
            "estimate_id": estimate_id,
            "run_id": run_id,
            "company_id": company_id,
            "status": "pending",
        },
        on_conflict="estimate_id",
    ).execute()

    if object_estimates:
        client.table("rfq_object_estimates").upsert(
            object_estimates,
            on_conflict="estimate_id,object_id",
        ).execute()


def fetch_rfq_estimate(client: Client, estimate_id: str) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_estimates",
        filters={"estimate_id": estimate_id},
    )


def fetch_rfq_object_estimates(client: Client, estimate_id: str) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_object_estimates",
        order_by="object_id",
        filters={"estimate_id": estimate_id},
    )


def fetch_rfq_estimate_pricing_overrides(client: Client, estimate_id: str) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_estimate_pricing_overrides",
        order_by="object_key",
        filters={"estimate_id": estimate_id},
    )


def fetch_rfq_estimate_lines_for_object(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
) -> pd.DataFrame:
    return fetch_table(
        client,
        "rfq_estimate_lines",
        order_by="sort_order",
        filters={"estimate_id": estimate_id, "object_id": object_id},
    )


def replace_rfq_estimate_lines_for_object(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    lines: list[dict],
) -> None:
    """Replace material/labor estimate lines for one object estimate."""
    client.table("rfq_estimate_lines").delete().eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "object_id",
        object_id,
    ).execute()

    if lines:
        client.table("rfq_estimate_lines").upsert(
            lines,
            on_conflict="estimate_id,line_id",
        ).execute()


def replace_rfq_overhead_lines_for_object(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    lines: list[dict],
) -> None:
    """Replace deterministic overhead lines for one object estimate."""
    client.table("rfq_estimate_lines").delete().eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "object_id",
        object_id,
    ).eq(
        "section",
        "overhead",
    ).execute()

    if lines:
        client.table("rfq_estimate_lines").upsert(
            lines,
            on_conflict="estimate_id,line_id",
        ).execute()


def update_rfq_estimate_line(
    client: Client,
    *,
    estimate_id: str,
    line_id: str,
    values: dict,
) -> None:
    """Update deterministic pricing fields for one estimate line."""
    client.table("rfq_estimate_lines").update(values).eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "line_id",
        line_id,
    ).execute()


def update_rfq_object_estimate_totals(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    self_cost_ex_vat: float,
    vat_amount: float,
    self_cost_total: float,
) -> None:
    """Persist deterministic self-cost totals for one object estimate."""
    client.table("rfq_object_estimates").update(
        {
            "self_cost_ex_vat": self_cost_ex_vat,
            "vat_amount": vat_amount,
            "self_cost_total": self_cost_total,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    ).eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "object_id",
        object_id,
    ).execute()


def update_rfq_object_estimate_approved(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    approved: bool,
) -> None:
    """Persist Object Detail approval state."""
    client.table("rfq_object_estimates").update(
        {
            "approved": approved,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    ).eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "object_id",
        object_id,
    ).execute()


def update_rfq_object_estimate_status(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    status: str,
) -> None:
    client.table("rfq_object_estimates").update(
        {"status": status},
    ).eq(
        "estimate_id",
        estimate_id,
    ).eq(
        "object_id",
        object_id,
    ).execute()


def update_rfq_object_estimate_progress(
    client: Client,
    *,
    estimate_id: str,
    object_id: str,
    status: str,
    progress_percent: int,
    progress_label: str,
) -> None:
    """Persist object estimation progress, falling back to status-only schema."""
    progress_percent = max(0, min(100, int(progress_percent)))
    try:
        client.table("rfq_object_estimates").update(
            {
                "status": status,
                "progress_percent": progress_percent,
                "progress_label": progress_label,
                "progress_updated_at": datetime.now(UTC).isoformat(),
            },
        ).eq(
            "estimate_id",
            estimate_id,
        ).eq(
            "object_id",
            object_id,
        ).execute()
    except Exception:
        update_rfq_object_estimate_status(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            status=status,
        )
