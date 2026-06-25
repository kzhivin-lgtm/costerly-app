from __future__ import annotations

from typing import Any

from agents.estimation_agent import run_estimation_agent
from agents.schemas.estimation_schema import validate_estimation_result
from db.repositories import (
    fetch_rfq_estimate_lines_for_object,
    fetch_rfq_object_estimates,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    insert_agent_usage_event,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_status,
    upsert_rfq_estimate_shell,
)
from db.supabase_client import get_supabase_client
from models.estimation import ObjectEstimateSeed
from use_cases.pricing import price_estimated_object


def start_estimation_for_run(*, run_id: str, company_id: str) -> dict[str, Any]:
    """Create pending estimation records for all detected RFQ objects.

    Called when the user leaves File Review for Objects Estimation. This does
    not call Claude yet; it only creates stable DB work items that the future
    Estimation Agent can fill object by object.
    """
    client = get_supabase_client()
    run_df = fetch_rfq_run(client, run_id)
    objects_df = fetch_rfq_detected_objects(client, run_id)

    if run_df.empty:
        raise RuntimeError(f"RFQ run not found in Supabase: {run_id}")

    seeds = [
        ObjectEstimateSeed(
            run_id=run_id,
            company_id=company_id,
            object_id=str(row.get("object_id")),
            object_name=str(row.get("object_name") or "Untitled object"),
            quantity=float(row.get("quantity") or 1),
        )
        for _, row in objects_df.iterrows()
    ]

    estimate_id = f"{run_id}_estimate_001"
    object_estimates = [
        {
            "estimate_id": estimate_id,
            "run_id": seed.run_id,
            "company_id": seed.company_id,
            "object_id": seed.object_id,
            "object_name": seed.object_name,
            "quantity": seed.quantity,
            "status": "pending",
        }
        for seed in seeds
    ]

    upsert_rfq_estimate_shell(
        client,
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
        object_estimates=object_estimates,
    )

    return {
        "estimate_id": estimate_id,
        "run_id": run_id,
        "object_count": len(object_estimates),
        "status": "pending",
    }


def load_objects_estimation_data(estimate_id: str) -> dict[str, Any]:
    """Load current object estimate statuses for the Objects Estimation screen."""
    client = get_supabase_client()
    objects_df = fetch_rfq_object_estimates(client, estimate_id)

    rows = []
    for _, item in objects_df.iterrows():
        row = item.to_dict()
        status = str(row.get("status") or "pending")
        self_cost = row.get("self_cost_ex_vat")
        rows.append(
            {
                "object_key": row.get("object_id"),
                "name": row.get("object_name"),
                "materials": status,
                "quantity": row.get("quantity"),
                "self_cost_unit": self_cost if self_cost is not None else status,
                "sale_price_unit": None,
                "sale_price_total": None,
                "suggestion": "suggested: SC + 30%",
                "reviewed": bool(row.get("approved")),
            }
        )

    return {
        "rows": rows,
        "project_costs": [
            {
                "object_key": "delivery",
                "name": "Delivery",
                "materials": "project-level cost",
                "quantity": 1,
                "self_cost_unit": None,
                "sale_price_unit": None,
                "sale_price_total": None,
                "suggestion": "suggested: 3% of objects subtotal",
                "reviewed": False,
            },
            {
                "object_key": "installation",
                "name": "Installation",
                "materials": "project-level cost",
                "quantity": 1,
                "self_cost_unit": None,
                "sale_price_unit": None,
                "sale_price_total": None,
                "suggestion": "suggested: 10% of objects subtotal",
                "reviewed": False,
            },
        ],
        "summary": {"project_price": None, "vat": None, "total": None},
    }


def load_object_detail_data(*, estimate_id: str, object_id: str) -> dict[str, Any]:
    """Load one object's persisted estimation lines for Object Detail."""
    client = get_supabase_client()
    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )

    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        raise RuntimeError(f"Object estimate not found: {estimate_id}/{object_id}")

    object_row = matching.iloc[0].to_dict()
    material_rows = []
    labor_rows = []

    for _, line in lines_df.iterrows():
        item = line.to_dict()
        if item.get("section") == "material":
            material_rows.append(
                {
                    "group": item.get("group_name"),
                    "item": item.get("item_name"),
                    "unit": item.get("unit"),
                    "unit_cost": item.get("unit_cost"),
                    "qty": item.get("quantity"),
                    "cost": item.get("cost"),
                }
            )
        elif item.get("section") == "labor":
            labor_rows.append(
                {
                    "group": item.get("group_name"),
                    "work": item.get("item_name"),
                    "role": item.get("role"),
                    "hours": item.get("hours"),
                    "rate": item.get("rate"),
                    "cost": item.get("cost"),
                }
            )

    return {
        "object_key": object_id,
        "name": object_row.get("object_name"),
        "quantity": object_row.get("quantity"),
        "confidence": "—",
        "preview_label": "Object preview",
        "sections": [
            {
                "title": "Material cost",
                "metrics": [("Cost", None), ("VAT 18%", None), ("Total", None)],
                "columns": ["Item", "Unit", "Unit cost", "Qty", "Cost"],
                "rows": material_rows,
            },
            {
                "title": "Labor cost",
                "metrics": [
                    ("Total hours", "—"),
                    ("Cost", None),
                    ("Employer 25%", None),
                    ("Total", None),
                ],
                "columns": ["Work", "Role", "Hours", "Rate", "Cost"],
                "rows": labor_rows,
            },
        ],
        "self_cost": {
            "title": f"{object_row.get('object_name') or 'Object'} self cost (SC)",
            "excl_vat": object_row.get("self_cost_ex_vat"),
            "vat": object_row.get("vat_amount"),
            "total": object_row.get("self_cost_total"),
        },
    }


def estimate_first_object_for_run(
    *,
    estimate_id: str,
    run_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
) -> dict[str, Any]:
    """Run the first detected object estimate for an existing estimate shell."""
    client = get_supabase_client()
    objects_df = fetch_rfq_detected_objects(client, run_id)
    if objects_df.empty:
        return {
            "estimate_id": estimate_id,
            "run_id": run_id,
            "status": "no_objects",
        }

    first_object = objects_df.iloc[0].to_dict()
    return estimate_one_object(
        estimate_id=estimate_id,
        run_id=run_id,
        object_id=str(first_object["object_id"]),
        company_id=company_id,
        file_name=file_name,
        file_bytes=file_bytes,
    )


def estimate_one_object(
    *,
    estimate_id: str,
    run_id: str,
    object_id: str,
    company_id: str,
    file_name: str,
    file_bytes: bytes,
) -> dict[str, Any]:
    """Run Estimation Agent for one detected object and persist draft lines."""
    client = get_supabase_client()
    objects_df = fetch_rfq_detected_objects(client, run_id)
    matching = objects_df[objects_df["object_id"] == object_id]

    if matching.empty:
        raise RuntimeError(f"Detected object not found: {run_id}/{object_id}")

    detected_object = matching.iloc[0].to_dict()
    update_rfq_object_estimate_status(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        status="running",
    )

    try:
        estimation_result = run_estimation_agent(
            file_name=file_name,
            company_id=company_id,
            file_bytes=file_bytes,
            estimate_id=estimate_id,
            run_id=run_id,
            detected_object=detected_object,
        )
        usage_event = estimation_result.pop("_agent_usage", None)
        validated = validate_estimation_result(estimation_result)
        lines = build_estimate_lines_from_agent_result(validated)

        replace_rfq_estimate_lines_for_object(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            lines=lines,
        )
        pricing_result = price_estimated_object(
            estimate_id=estimate_id,
            object_id=object_id,
            company_id=company_id,
        )
        update_rfq_object_estimate_status(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            status="completed",
        )

        if usage_event:
            try:
                insert_agent_usage_event(client, usage_event)
            except Exception as exc:
                print(f"[Usage Ledger] Could not save estimation usage: {exc}")

        return {
            "estimate_id": estimate_id,
            "run_id": run_id,
            "object_id": object_id,
            "line_count": len(lines),
            "pricing": pricing_result,
            "status": "completed",
        }
    except Exception:
        update_rfq_object_estimate_status(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            status="failed",
        )
        raise


def build_estimate_lines_from_agent_result(
    estimation_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert validated Estimation Agent JSON into DB line rows.

    Material prices and labor rates stay empty here. A deterministic calculation
    engine will match catalogs and fill costs after the agent proposes
    material quantities and labor hours.
    """
    estimate_id = estimation_result["estimate_id"]
    object_id = estimation_result["object_id"]
    company_id = estimation_result["company_id"]

    rows: list[dict[str, Any]] = []
    sort_order = 0

    for item in estimation_result["materials"]:
        sort_order += 10
        rows.append(
            {
                "estimate_id": estimate_id,
                "object_id": object_id,
                "line_id": f"{object_id}_material_{sort_order:04d}",
                "company_id": company_id,
                "section": "material",
                "group_name": item["group_name"],
                "item_name": item["item_name"],
                "catalog_match_query": item["catalog_match_query"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quantity_basis": item["quantity_basis"],
                "evidence_pages": item["evidence_pages"],
                "confidence": item["confidence"],
                "notes": item["notes"],
                "needs_price": True,
                "needs_review": item["confidence"] < 70,
                "sort_order": sort_order,
                "raw_agent_json": item,
            }
        )

    for item in estimation_result["labor"]:
        sort_order += 10
        rows.append(
            {
                "estimate_id": estimate_id,
                "object_id": object_id,
                "line_id": f"{object_id}_labor_{sort_order:04d}",
                "company_id": company_id,
                "section": "labor",
                "group_name": item["group_name"],
                "item_name": item["work_name"],
                "role": item["role"],
                "hours": item["hours"],
                "hours_basis": item["hours_basis"],
                "evidence_pages": item["evidence_pages"],
                "confidence": item["confidence"],
                "notes": item["notes"],
                "needs_price": False,
                "needs_review": item["confidence"] < 70,
                "sort_order": sort_order,
                "raw_agent_json": item,
            }
        )

    return rows
