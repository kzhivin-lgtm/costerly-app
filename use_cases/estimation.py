from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from db.repositories import (
    fetch_company_overhead_settings,
    fetch_latest_estimation_facts_by_object,
    fetch_rfq_estimate_pricing_overrides,
    fetch_rfq_estimate_lines,
    fetch_rfq_estimate_lines_for_object,
    fetch_rfq_estimate_material_plan,
    fetch_rfq_object_estimates,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    update_rfq_estimate_line,
    update_rfq_detected_object,
    update_rfq_object_estimate_approved,
    update_rfq_object_estimate_quantity,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
    upsert_rfq_estimate_material_norm_override,
    mark_rfq_estimate_material_plan_stale,
    reset_rfq_object_estimate_approvals,
    upsert_rfq_estimate_shell,
)
from db.supabase_client import get_supabase_client
from agents.estimation_v3_material_facts_agent import ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION
from db.company_access import assert_estimate_owned, assert_run_owned
from state.company_auth import company_auth_enabled
from state.session import get_company_id
from models.estimation import ObjectEstimateSeed
from use_cases.retry import read_with_retry


def _assert_screen_estimate_access(client: Any, estimate_id: str) -> None:
    if company_auth_enabled():
        assert_estimate_owned(client, estimate_id, get_company_id())


def _material_plan_status(row: Any) -> str:
    if not isinstance(row, dict):
        return "pending"
    return str(row.get("plan_status") or (row.get("plan_payload") or {}).get("status") or "pending")


def _material_plan_blocking_state(row: Any) -> tuple[str, str]:
    """Return a truthful visible state for an estimate-wide material plan."""
    status = _material_plan_status(row)
    if status == "needs_review":
        payload = dict((row or {}).get("plan_payload") or {}) if isinstance(row, dict) else {}
        unresolved_count = len(payload.get("unresolved_requirement_ids") or [])
        count_text = f"{unresolved_count} material requirement{'s' if unresolved_count != 1 else ''}"
        return (
            "MATERIALS NEED REVIEW",
            f"Materials need review: {count_text} could not be placed in the Company or Israel catalog. "
            "Approval remains unavailable.",
        )
    if status == "failed":
        return (
            "MATERIAL PLAN FAILED",
            "The estimate-wide material plan could not be calculated. Approval remains unavailable.",
        )
    return (
        "MATERIALS FINALIZING",
        "Materials are being recalculated for every object. Approval becomes available when the "
        "estimate-wide purchase plan is ready.",
    )


def _invalidate_and_queue_material_plan(
    client: Any,
    *,
    estimate_id: str,
    company_id: str,
    run_id: str,
    reason_code: str,
) -> None:
    """Invalidate every object approval, then queue one estimate-wide rebuild."""
    mark_rfq_estimate_material_plan_stale(
        client,
        estimate_id=estimate_id,
        company_id=company_id,
        reason_code=reason_code,
    )
    reset_rfq_object_estimate_approvals(client, estimate_id=estimate_id)
    # Local import avoids the existing runtime -> estimation dependency cycle.
    from use_cases.estimation_runtime import queue_material_plan_recalculation

    queue_material_plan_recalculation(
        estimate_id=estimate_id,
        run_id=run_id,
        company_id=company_id,
    )


def start_estimation_for_run(
    *,
    run_id: str,
    company_id: str,
    ignored_object_ids: set[str] | None = None,
    estimate_id: str | None = None,
) -> dict[str, Any]:
    """Create pending estimation records for all detected RFQ objects.

    Called when the user leaves File Review for Objects Estimation. This does
    not call Claude yet; it only creates stable DB work items that the future
    Estimation Agent can fill object by object.
    """
    client = get_supabase_client()
    if company_auth_enabled():
        assert_run_owned(client, run_id, company_id)
    run_df = fetch_rfq_run(client, run_id)
    objects_df = fetch_rfq_detected_objects(client, run_id)
    ignored_object_ids = ignored_object_ids or set()

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
        if str(row.get("object_id")) not in ignored_object_ids
    ]

    estimate_id = estimate_id or build_estimate_id(run_id)
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


def build_estimate_id(run_id: str) -> str:
    estimate_stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{run_id}_estimate_{estimate_stamp}"


def load_objects_estimation_data(estimate_id: str) -> dict[str, Any]:
    """Load current object estimate statuses for the Objects Estimation screen."""
    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    objects_df = read_with_retry(lambda: fetch_rfq_object_estimates(client, estimate_id))
    try:
        overrides_df = read_with_retry(lambda: fetch_rfq_estimate_pricing_overrides(client, estimate_id))
    except Exception:
        overrides_df = None
    try:
        material_plan_df = read_with_retry(lambda: fetch_rfq_estimate_material_plan(client, estimate_id))
    except Exception:
        material_plan_df = None
    material_plan_row = (
        material_plan_df.iloc[0].to_dict()
        if material_plan_df is not None and not material_plan_df.empty
        else None
    )
    material_plan = dict((material_plan_row or {}).get("plan_payload") or {})
    sale_price_overrides = _pricing_overrides_by_object(overrides_df)
    settings: dict[str, Any] = {}
    if not objects_df.empty:
        company_id = str(objects_df.iloc[0].get("company_id") or "")
        if company_id:
            settings = _first_row(fetch_company_overhead_settings(client, company_id))
    vat_percent = _number(settings.get("vat_percent"), 18)
    markup_percent = _number(settings.get("sale_price_markup_percent"), 30)
    delivery_percent = _number(settings.get("delivery_percent"), 3)
    installation_percent = _number(settings.get("installation_percent"), 10)
    facts_by_object: dict[str, dict] = {}
    if not objects_df.empty:
        run_id = str(objects_df.iloc[0].get("run_id") or "")
        if run_id:
            try:
                facts_by_object = fetch_latest_estimation_facts_by_object(
                    client,
                    run_id=run_id,
                    agent_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION,
                )
            except Exception:
                facts_by_object = {}

    rows = []
    for _, item in objects_df.iterrows():
        row = item.to_dict()
        object_id = str(row.get("object_id") or "")
        quantity = _number(row.get("quantity"), 1)
        facts_result = facts_by_object.get(object_id) or {}
        facts_payload = facts_result.get("facts_payload") or {}
        materials = facts_payload.get("materials") or []
        material_names = [
            str(material.get("source_name") or "").strip()
            for material in materials
            if isinstance(material, dict) and str(material.get("source_name") or "").strip()
        ]
        status = str(row.get("status") or "pending")
        self_cost = row.get("self_cost_ex_vat")
        priced = status in {"completed", "review_required"} and self_cost is not None
        sale_price_unit = _suggested_sale_price(self_cost, markup_percent) if priced else None
        sale_price_overridden = priced and row.get("object_id") in sale_price_overrides
        if sale_price_overridden:
            sale_price_unit = sale_price_overrides[row.get("object_id")]
        rows.append(
            {
                "object_key": row.get("object_id"),
                "name": row.get("object_name"),
                "materials": ", ".join(material_names),
                "quantity": quantity,
                "self_cost_unit": self_cost if self_cost is not None else status,
                "status": status,
                "progress_percent": row.get("progress_percent"),
                "progress_label": row.get("progress_label"),
                "progress_updated_at": row.get("progress_updated_at"),
                "sale_price_unit": sale_price_unit,
                "sale_price_total": _line_total(sale_price_unit, quantity),
                "sale_price_overridden": sale_price_overridden,
                "suggestion": f"suggested: SC + {_format_number(markup_percent)}%",
                "reviewed": bool(row.get("approved")),
                "details_available": bool(facts_result),
                "facts_status": facts_result.get("status"),
            }
        )

    project_costs, summary = _objects_project_pricing(
        rows,
        sale_price_overrides,
        vat_percent=vat_percent,
        delivery_percent=delivery_percent,
        installation_percent=installation_percent,
    )
    return {
        "rows": rows,
        "project_costs": project_costs,
        "summary": summary,
        "material_plan": material_plan,
        "material_plan_ready": _material_plan_status(material_plan_row) == "planned",
    }


def _suggested_sale_price(self_cost: Any, markup_percent: float = 30) -> float | None:
    """Return the company-configured suggested sale price."""
    if self_cost is None or self_cost == "":
        return None
    if isinstance(self_cost, float) and self_cost != self_cost:
        return None
    return round(_number(self_cost, 0) * (1 + _number(markup_percent, 30) / 100), 2)


def _line_total(unit_price: Any, quantity: Any) -> float | None:
    if unit_price is None or unit_price == "":
        return None
    return round(_number(unit_price, 0) * _number(quantity, 1), 2)


def _pricing_overrides_by_object(overrides_df: Any) -> dict[str, float]:
    if overrides_df is None or overrides_df.empty:
        return {}
    overrides: dict[str, float] = {}
    for _, item in overrides_df.iterrows():
        row = item.to_dict()
        if row.get("field") != "sale_price_unit":
            continue
        object_key = str(row.get("object_key") or "")
        if not object_key:
            continue
        overrides[object_key] = round(_number(row.get("value"), 0), 2)
    return overrides


def _objects_project_pricing(
    rows: list[dict[str, Any]],
    sale_price_overrides: dict[str, float] | None = None,
    *,
    vat_percent: float = 18,
    delivery_percent: float = 3,
    installation_percent: float = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Calculate project-level suggested costs after all objects are priced."""
    sale_price_overrides = sale_price_overrides or {}
    object_rows = [row for row in rows if row.get("object_key")]
    all_priced = bool(object_rows) and all(
        str(row.get("status") or "").lower() in {"completed", "review_required"}
        and row.get("sale_price_total") is not None
        for row in object_rows
    )
    objects_subtotal = sum(_number(row.get("sale_price_total"), 0) for row in object_rows)

    delivery_suggested = round(objects_subtotal * delivery_percent / 100, 2) if all_priced else None
    installation_suggested = round(objects_subtotal * installation_percent / 100, 2) if all_priced else None
    delivery = sale_price_overrides.get("delivery", delivery_suggested)
    installation = sale_price_overrides.get("installation", installation_suggested)
    project_price = (
        round(objects_subtotal + _number(delivery, 0) + _number(installation, 0), 2)
        if all_priced
        else None
    )
    vat = (
        round(_number(project_price, 0) * _number(vat_percent, 18) / 100, 2)
        if all_priced
        else None
    )
    total = round(_number(project_price, 0) + _number(vat, 0), 2) if all_priced else None

    return (
        [
            {
                "object_key": "delivery",
                "name": "Delivery",
                "materials": "project-level cost",
                "quantity": 1,
                "self_cost_unit": None,
                "sale_price_unit": delivery,
                "sale_price_total": None,
                "sale_price_overridden": "delivery" in sale_price_overrides,
                "percent": delivery_percent,
                "suggestion": "" if "delivery" in sale_price_overrides else f"suggested: {_format_number(delivery_percent)}% of objects subtotal",
                "reviewed": False,
            },
            {
                "object_key": "installation",
                "name": "Installation",
                "materials": "project-level cost",
                "quantity": 1,
                "self_cost_unit": None,
                "sale_price_unit": installation,
                "sale_price_total": None,
                "sale_price_overridden": "installation" in sale_price_overrides,
                "percent": installation_percent,
                "suggestion": "" if "installation" in sale_price_overrides else f"suggested: {_format_number(installation_percent)}% of objects subtotal",
                "reviewed": False,
            },
        ],
        {"project_price": project_price, "vat": vat, "total": total, "vat_percent": vat_percent},
    )


def load_object_detail_data(*, estimate_id: str, object_id: str) -> dict[str, Any]:
    """Load one object's persisted estimation lines for Object Detail."""
    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    try:
        material_plan_df = fetch_rfq_estimate_material_plan(client, estimate_id)
    except Exception:
        material_plan_df = None
    material_plan_row = (
        material_plan_df.iloc[0].to_dict()
        if material_plan_df is not None and not material_plan_df.empty
        else None
    )
    material_plan = dict((material_plan_row or {}).get("plan_payload") or {})
    plan_status = _material_plan_status(material_plan_row)
    plan_blocking_label, plan_blocking_message = _material_plan_blocking_state(
        material_plan_row
    )

    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        raise RuntimeError(f"Object estimate not found: {estimate_id}/{object_id}")

    object_row = matching.iloc[0].to_dict()
    canonical_quantity = _number(object_row.get("quantity"), 1)
    facts_result = {}
    try:
        facts_result = fetch_latest_estimation_facts_by_object(
            client,
            run_id=str(object_row.get("run_id") or ""),
            agent_version=ESTIMATION_V3_MATERIAL_FACTS_AGENT_VERSION,
        ).get(object_id) or {}
    except Exception:
        facts_result = {}
    facts_payload = facts_result.get("facts_payload") or {}
    settings = _first_row(
        fetch_company_overhead_settings(client, str(object_row.get("company_id")))
    )
    vat_percent = _number(settings.get("vat_percent"), 18)
    employer_load_percent = _number(settings.get("employer_load_percent"), 25)

    material_rows = []
    labor_rows = []
    overhead_rows = []

    for _, line in lines_df.iterrows():
        item = line.to_dict()
        if item.get("section") == "material":
            raw_agent_json = item.get("raw_agent_json") or {}
            material_rows.append(
                {
                    "group": item.get("group_name"),
                    "line_id": item.get("line_id"),
                    "item": item.get("item_name"),
                    "unit": item.get("unit"),
                    "unit_cost": item.get("unit_cost"),
                    "qty": item.get("quantity"),
                    "cost": item.get("cost"),
                    "locked": item.get("source") == "pricing_policy",
                    "policy_percent": (
                        raw_agent_json.get("percent")
                        if isinstance(raw_agent_json, dict) else None
                    ),
                }
            )
        elif item.get("section") == "labor":
            labor_rows.append(
                {
                    "group": item.get("group_name"),
                    "line_id": item.get("line_id"),
                    "work": item.get("item_name"),
                    "role": item.get("role"),
                    "hours": item.get("hours"),
                    "rate": item.get("rate"),
                    "cost": item.get("cost"),
                    "source": item.get("source"),
                }
            )
        elif item.get("section") == "overhead":
            monthly_cost = item.get("monthly_cost")
            allocation = item.get("allocation_basis")
            monthly_cost_display = (
                f"{_format_number(_number(monthly_cost, 0))}%"
                if str(allocation or "").startswith(f"{_format_number(_number(monthly_cost, 0))}%")
                else None
            )
            overhead_rows.append(
                {
                    "group": item.get("group_name"),
                    "line_id": item.get("line_id"),
                    "item": item.get("item_name"),
                    "monthly_cost": monthly_cost,
                    "monthly_cost_display": monthly_cost_display,
                    "allocation": allocation,
                    "cost": item.get("cost"),
                }
            )

    if not material_rows:
        material_rows = _material_rows_from_material_facts(facts_payload)

    material_total = sum(_number(row.get("cost"), 0) for row in material_rows)
    manufacturing_total = sum(
        _number(row.get("cost"), 0)
        for row in labor_rows
        if row.get("source") == "manufacturing_engine"
    )
    labor_base_total = sum(
        _number(row.get("cost"), 0)
        for row in labor_rows
        if row.get("source") != "manufacturing_engine"
    )
    labor_hours_total = sum(
        _number(row.get("hours"), 0)
        for row in labor_rows
        if row.get("source") != "manufacturing_engine"
    )
    employer_load = round(labor_base_total * employer_load_percent / 100, 2)
    labor_total = labor_base_total + employer_load + manufacturing_total
    overhead_total = sum(_number(row.get("cost"), 0) for row in overhead_rows)
    operation_confidences = [
        _number(row.get("confidence"), 0)
        for row in (facts_payload.get("labor_operations") or [])
        if isinstance(row, dict) and row.get("confidence") is not None
    ]

    return {
        "object_key": object_id,
        "run_id": str(object_row.get("run_id") or ""),
        "estimate_id": estimate_id,
        "name": object_row.get("object_name"),
        "quantity": canonical_quantity,
        "approved": bool(object_row.get("approved")),
        "material_plan_ready": plan_status == "planned",
        "material_plan_status": plan_status,
        "material_plan_blocking_label": plan_blocking_label,
        "material_plan_blocking_message": plan_blocking_message,
        "confidence": round(sum(operation_confidences) / len(operation_confidences))
        if operation_confidences else "—",
        "preview_label": "Object preview",
        "preview_url": _estimation_preview_url(
            client,
            str(facts_payload.get("primary_preview_ref") or ""),
            company_id=str(object_row.get("company_id") or ""),
        ),
        "facts_status": facts_result.get("status"),
        "sections": [
            {
                "key": "material",
                "title": "Material cost",
                "metrics": [
                    ("Cost", material_total),
                    (f"VAT {_format_number(vat_percent)}%", round(material_total * vat_percent / 100, 2)),
                    ("Total", round(material_total * (1 + vat_percent / 100), 2)),
                ],
                "columns": ["Item", "Unit", "Unit cost", "Per item", "Cost"],
                "rows": material_rows,
            },
        ],
        "self_cost": {
            "title": f"{object_row.get('object_name') or 'Object'} self cost (SC)",
            "excl_vat": object_row.get("self_cost_ex_vat"),
            "vat": object_row.get("vat_amount"),
            "total": object_row.get("self_cost_total"),
        },
    }


def _material_rows_from_material_facts(facts_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    target_quantity = max(_number(facts_payload.get("quantity"), 1), 1)
    for material in facts_payload.get("materials") or []:
        if not isinstance(material, dict):
            continue
        raw_quantity = material.get("quantity")
        quantity_per_item = (
            None if raw_quantity is None
            else round(_number(raw_quantity, 0) / target_quantity, 6)
        )
        rows.append({
            "group": "Detected materials",
            "line_id": material.get("requirement_id"),
            "item": material.get("source_name") or material.get("family"),
            "unit": material.get("unit"),
            "unit_cost": None,
            "qty": quantity_per_item,
            "cost": None,
        })
    return rows


def _estimation_preview_url(
    client: Any,
    storage_ref: str,
    *,
    company_id: str,
) -> str | None:
    prefix = "storage://rfq-estimation-evidence/"
    if not storage_ref.startswith(prefix):
        return None
    object_path = storage_ref.removeprefix(prefix)
    if not company_id or not object_path.startswith(f"{company_id}/"):
        return None
    try:
        response = client.storage.from_("rfq-estimation-evidence").create_signed_url(
            object_path,
            3600,
        )
    except Exception:
        return None
    if isinstance(response, dict):
        return response.get("signedURL") or response.get("signed_url")
    return getattr(response, "signedURL", None) or getattr(response, "signed_url", None)


def approve_object_estimate(
    *,
    estimate_id: str,
    object_id: str,
    recalculate: bool = True,
) -> None:
    """Mark one object estimate approved in Supabase."""
    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    _require_final_material_plan(client, estimate_id)
    if recalculate:
        _recalculate_object_estimate_totals(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
        )
    update_rfq_object_estimate_approved(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        approved=True,
    )


def _require_final_material_plan(client: Any, estimate_id: str) -> None:
    """Prevent object approval before estimate-wide stock rounding is complete."""
    try:
        plan_df = fetch_rfq_estimate_material_plan(client, estimate_id)
    except Exception as exc:
        raise ValueError("Materials are still being finalized for this estimate") from exc
    if plan_df.empty:
        raise ValueError("Materials are still being finalized for this estimate")
    row = plan_df.iloc[0].to_dict()
    if _material_plan_status(row) != "planned":
        raise ValueError(_material_plan_blocking_state(row)[1])


def _object_material_context(client: Any, *, estimate_id: str, object_id: str) -> dict[str, Any]:
    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        raise PermissionError("Object is not part of this estimate.")
    return matching.iloc[0].to_dict()


def _material_requirement_id(line: dict[str, Any]) -> str:
    raw = line.get("raw_agent_json") or {}
    if not isinstance(raw, dict):
        return ""
    facts = raw.get("facts") or {}
    return str(facts.get("requirement_id") or "") if isinstance(facts, dict) else ""


def _material_total_cost(*, unit_cost: float, quantity_per_item: float, object_quantity: float) -> float:
    return round(unit_cost * quantity_per_item * max(object_quantity, 1), 2)


def _material_norms_from_plan(plan_snapshot: dict[str, Any]) -> dict[tuple[str, str], tuple[str, float]]:
    """Return deterministic net norms, never rounded purchase quantities.

    Object Detail describes what one finished item consumes.  A plan line may
    buy whole sheets or stock bars, but those purchasing units must not be
    copied into an individual object's norm.  The selected candidate supplies
    the physical form, while its allocations supply the net area, length or
    count for each material requirement.
    """
    result: dict[tuple[str, str], tuple[str, float]] = {}
    for line in plan_snapshot.get("lines") or []:
        if not isinstance(line, dict):
            continue
        purchase_kind = str(line.get("purchase_kind") or "")
        if purchase_kind == "sheet":
            unit, divisor, dimension = "m²", 1_000_000.0, "area"
        elif purchase_kind == "linear_stock":
            unit, divisor, dimension = "m", 1_000.0, "length"
        elif purchase_kind == "piece":
            unit, divisor, dimension = "piece", 1.0, "quantity"
        else:
            continue
        for allocation in line.get("allocations") or []:
            if not isinstance(allocation, dict):
                continue
            object_id = str(allocation.get("object_id") or "")
            requirement_id = str(allocation.get("material_requirement_id") or "")
            if not object_id or not requirement_id:
                continue
            if dimension == "area":
                amount = _number(allocation.get("area_mm2"), 0) / divisor
                if amount <= 0:
                    amount = (
                        _number(allocation.get("length_mm"), 0)
                        * _number(allocation.get("width_mm"), 0)
                        * _number(allocation.get("quantity"), 1)
                        / divisor
                    )
            elif dimension == "length":
                amount = _number(allocation.get("length_mm"), 0) / divisor
                amount *= _number(allocation.get("quantity"), 1)
            else:
                amount = _number(allocation.get("quantity"), 0)
            if amount <= 0:
                continue
            key = (object_id, requirement_id)
            existing = result.get(key)
            # One pricing key must map to one purchase form.  If a malformed
            # plan violates that invariant, do not publish an arbitrary unit.
            if existing and existing[0] != unit:
                result.pop(key, None)
                continue
            result[key] = (unit, (existing[1] if existing else 0.0) + amount)
    return result


def apply_material_plan_allocations(
    client: Any,
    *,
    estimate_id: str,
    plan_snapshot: dict[str, Any],
) -> None:
    """Project rounded purchase costs back into the owning Object Detail rows."""
    if str(plan_snapshot.get("status") or "") != "planned":
        return
    allocation_costs = {
        (str(row.get("object_id") or ""), str(row.get("material_requirement_id") or "")): _number(
            row.get("cost_ex_vat"), 0
        )
        for row in plan_snapshot.get("object_material_costs") or []
        if isinstance(row, dict)
    }
    material_norms = _material_norms_from_plan(plan_snapshot)
    resolved_names = {
        (str(allocation.get("object_id") or ""), str(allocation.get("material_requirement_id") or "")):
        str(line.get("display_name") or "")
        for line in plan_snapshot.get("lines") or []
        if isinstance(line, dict)
        for allocation in line.get("allocations") or []
        if isinstance(allocation, dict) and str(line.get("display_name") or "")
    }
    if not allocation_costs or not material_norms:
        return
    lines_df = fetch_rfq_estimate_lines(client, estimate_id)
    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    object_quantities = {
        str(row.get("object_id") or ""): _number(row.get("quantity"), 1)
        for _, row in objects_df.iterrows()
    }
    affected_object_ids: set[str] = set()
    for _, item in lines_df.iterrows():
        line = item.to_dict()
        if str(line.get("section") or "") != "material":
            continue
        object_id = str(line.get("object_id") or "")
        requirement_id = _material_requirement_id(line)
        allocated_cost = allocation_costs.get((object_id, requirement_id))
        norm = material_norms.get((object_id, requirement_id))
        if allocated_cost is None or norm is None:
            continue
        unit, total_required_quantity = norm
        if total_required_quantity <= 0:
            continue
        quantity_per_item = total_required_quantity / max(object_quantities.get(object_id, 1), 1)
        effective_unit_cost = round(allocated_cost / total_required_quantity, 4)
        update_rfq_estimate_line(
            client,
            estimate_id=estimate_id,
            line_id=str(line.get("line_id") or ""),
            values={
                "unit_cost": effective_unit_cost,
                "unit": unit,
                "quantity": quantity_per_item,
                "cost": round(allocated_cost, 2),
                "notes": "Allocated from the estimate-wide Material Plan",
                "updated_at": datetime.now(UTC).isoformat(),
                **({"item_name": resolved_names[(object_id, requirement_id)]}
                   if resolved_names.get((object_id, requirement_id)) else {}),
            },
        )
        affected_object_ids.add(object_id)
    for object_id in affected_object_ids:
        _recalculate_object_estimate_totals(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
        )


def update_object_quantity(
    *,
    estimate_id: str,
    run_id: str,
    object_id: str,
    quantity: float,
) -> float:
    """Persist one canonical item quantity and keep the estimate mirror aligned."""
    normalized = round(float(quantity), 3)
    if normalized <= 0 or normalized > 1_000_000:
        raise ValueError("Quantity must be greater than zero.")

    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    if company_auth_enabled():
        assert_run_owned(client, run_id, get_company_id())

    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    matching = objects_df[
        (objects_df["object_id"] == object_id)
        & (objects_df["run_id"] == run_id)
    ]
    if matching.empty:
        raise PermissionError("Object is not part of this estimate.")

    update_rfq_object_estimate_quantity(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        quantity=normalized,
        approved=False,
    )
    update_rfq_detected_object(
        client,
        run_id=run_id,
        object_id=object_id,
        values={"quantity": normalized},
    )
    company_id = str(matching.iloc[0].get("company_id") or "")
    if company_id:
        _invalidate_and_queue_material_plan(
            client,
            estimate_id=estimate_id,
            company_id=company_id,
            run_id=run_id,
            reason_code="object_quantity_changed",
        )
    return normalized


def apply_object_detail_line_edit(
    *,
    estimate_id: str,
    object_id: str,
    line_id: str,
    field: str,
    value: str,
) -> None:
    """Persist one Object Detail edit and recalculate object totals."""
    field = str(field or "")
    if field not in {
        "unit_cost",
        "quantity",
        "hours",
        "rate",
        "monthly_cost",
        "allocation_basis",
    }:
        return

    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    matching = lines_df[lines_df["line_id"] == line_id]
    if matching.empty:
        return

    line = matching.iloc[0].to_dict()
    section = str(line.get("section") or "")
    if str(line.get("source") or "") == "pricing_policy":
        return
    requirement_id = _material_requirement_id(line) if section == "material" and field == "quantity" else ""
    if section == "material" and field == "quantity" and not requirement_id:
        raise ValueError("Material requirement cannot be edited without a stable requirement id.")
    object_row = _object_material_context(client, estimate_id=estimate_id, object_id=object_id)
    object_quantity = _number(object_row.get("quantity"), 1)
    updates: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
    material_norm_changed = False

    if field == "allocation_basis":
        if section != "overhead":
            return
        updates["allocation_basis"] = str(value or "").strip()
    else:
        numeric_value = _number_from_edit(value)
        updates[field] = numeric_value

        if section == "material" and field in {"unit_cost", "quantity"}:
            if field == "quantity" and numeric_value <= 0:
                raise ValueError("Material norm per item must be greater than zero.")
            unit_cost = numeric_value if field == "unit_cost" else _number(line.get("unit_cost"), 0)
            quantity = numeric_value if field == "quantity" else _number(line.get("quantity"), 0)
            updates["cost"] = _material_total_cost(
                unit_cost=unit_cost,
                quantity_per_item=quantity,
                object_quantity=object_quantity,
            )
            material_norm_changed = field == "quantity"
        elif section == "labor" and field in {"hours", "rate"}:
            hours = numeric_value if field == "hours" else _number(line.get("hours"), 0)
            rate = numeric_value if field == "rate" else _number(line.get("rate"), 0)
            updates["cost"] = round(hours * rate, 2)
        elif section == "overhead" and field == "monthly_cost":
            old_monthly = _number(line.get("monthly_cost"), 0)
            old_cost = _number(line.get("cost"), 0)
            ratio = old_cost / old_monthly if old_monthly else 0
            updates["cost"] = round(numeric_value * ratio, 2)
        else:
            return

    update_rfq_estimate_line(
        client,
        estimate_id=estimate_id,
        line_id=line_id,
        values=updates,
    )
    if material_norm_changed:
        upsert_rfq_estimate_material_norm_override(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            material_requirement_id=requirement_id,
            company_id=str(object_row.get("company_id") or ""),
            quantity_per_item=numeric_value,
            unit=str(line.get("unit") or ""),
            source_line_id=line_id,
        )
        _invalidate_and_queue_material_plan(
            client,
            estimate_id=estimate_id,
            company_id=str(object_row.get("company_id") or ""),
            run_id=str(object_row.get("run_id") or ""),
            reason_code="material_norm_changed",
        )
    _recalculate_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )


def apply_object_detail_snapshot(
    *,
    estimate_id: str,
    object_id: str,
    run_id: str | None = None,
    edits: list[Any],
    approve: bool = False,
) -> bool:
    """Persist the current Object Detail table snapshot and recalculate once."""
    allowed_fields = {
        "unit_cost",
        "quantity",
        "hours",
        "rate",
        "monthly_cost",
        "allocation_basis",
    }
    edits_by_line: dict[str, dict[str, Any]] = {}
    object_quantity: Any = None
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        line_id = str(edit.get("line_id") or "")
        field = str(edit.get("field") or "")
        if line_id == "__object__" and field == "object_quantity":
            object_quantity = edit.get("value")
            continue
        if not line_id or field not in allowed_fields:
            continue
        edits_by_line.setdefault(line_id, {})[field] = edit.get("value")

    if not edits_by_line and object_quantity is None:
        return True

    if object_quantity is not None:
        update_object_quantity(
            estimate_id=estimate_id,
            run_id=str(run_id or ""),
            object_id=object_id,
            quantity=_number_from_edit(object_quantity),
        )
    if not edits_by_line:
        return False if object_quantity is not None else True

    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    if lines_df.empty:
        return False

    object_row = _object_material_context(client, estimate_id=estimate_id, object_id=object_id)
    current_object_quantity = _number(object_row.get("quantity"), 1)
    material_norm_overrides: list[tuple[str, float, str, str]] = []

    for _, item in lines_df.iterrows():
        line = item.to_dict()
        line_id = str(line.get("line_id") or "")
        line_edits = edits_by_line.get(line_id)
        if not line_edits:
            continue

        section = str(line.get("section") or "")
        if str(line.get("source") or "") == "pricing_policy":
            continue
        updates: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        next_values = dict(line)

        if "allocation_basis" in line_edits and section == "overhead":
            value = str(line_edits["allocation_basis"] or "").strip()
            updates["allocation_basis"] = value
            next_values["allocation_basis"] = value

        for field, value in line_edits.items():
            if field == "allocation_basis":
                continue
            if field not in _editable_numeric_fields_for_section(section):
                continue
            numeric_value = _number_from_edit(value)
            updates[field] = numeric_value
            next_values[field] = numeric_value

        if section == "material" and {"unit_cost", "quantity"} & updates.keys():
            quantity_per_item = _number(next_values.get("quantity"), 0)
            if "quantity" in updates:
                if quantity_per_item <= 0:
                    raise ValueError("Material norm per item must be greater than zero.")
                requirement_id = _material_requirement_id(line)
                if not requirement_id:
                    raise ValueError("Material requirement cannot be edited without a stable requirement id.")
                material_norm_overrides.append((
                    requirement_id,
                    quantity_per_item,
                    str(line.get("unit") or ""),
                    line_id,
                ))
            updates["cost"] = _material_total_cost(
                unit_cost=_number(next_values.get("unit_cost"), 0),
                quantity_per_item=quantity_per_item,
                object_quantity=current_object_quantity,
            )
        elif section == "labor" and {"hours", "rate"} & updates.keys():
            updates["cost"] = round(
                _number(next_values.get("hours"), 0)
                * _number(next_values.get("rate"), 0),
                2,
            )
        elif section == "overhead" and "monthly_cost" in updates:
            old_monthly = _number(line.get("monthly_cost"), 0)
            old_cost = _number(line.get("cost"), 0)
            ratio = old_cost / old_monthly if old_monthly else 0
            updates["cost"] = round(_number(next_values.get("monthly_cost"), 0) * ratio, 2)

        if len(updates) == 1:
            continue
        update_rfq_estimate_line(
            client,
            estimate_id=estimate_id,
            line_id=line_id,
            values=updates,
        )

    for requirement_id, quantity_per_item, unit, source_line_id in material_norm_overrides:
        upsert_rfq_estimate_material_norm_override(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            material_requirement_id=requirement_id,
            company_id=str(object_row.get("company_id") or ""),
            quantity_per_item=quantity_per_item,
            unit=unit,
            source_line_id=source_line_id,
        )

    material_input_changed = bool(material_norm_overrides) or object_quantity is not None
    if material_input_changed:
        _invalidate_and_queue_material_plan(
            client,
            estimate_id=estimate_id,
            company_id=str(object_row.get("company_id") or ""),
            run_id=str(object_row.get("run_id") or run_id or ""),
            reason_code="material_norm_changed" if material_norm_overrides else "object_quantity_changed",
        )

    _recalculate_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        approved=True if approve and not material_input_changed else None,
    )
    return not material_input_changed


def _editable_numeric_fields_for_section(section: str) -> set[str]:
    if section == "material":
        return {"unit_cost", "quantity"}
    if section == "labor":
        return {"hours", "rate"}
    if section == "overhead":
        return {"monthly_cost"}
    return set()


def _number_from_edit(value: Any) -> float:
    cleaned = (
        str(value or "")
        .replace("₪", "")
        .replace("%", "")
        .replace(",", "")
        .replace("\u202f", "")
        .strip()
    )
    return max(0, _number(cleaned, 0))


def _recalculate_object_estimate_totals(
    client: Any,
    *,
    estimate_id: str,
    object_id: str,
    approved: bool | None = None,
) -> None:
    objects_df = fetch_rfq_object_estimates(client, estimate_id)
    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        return

    object_row = matching.iloc[0].to_dict()
    settings = _first_row(fetch_company_overhead_settings(client, str(object_row.get("company_id"))))
    vat_percent = _number(settings.get("vat_percent"), 18)
    employer_load_percent = _number(settings.get("employer_load_percent"), 25)

    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    primary_material_total = sum(
        _number(row.get("cost"), 0)
        for _, item in lines_df.iterrows()
        if (row := item.to_dict()).get("section") == "material"
        and row.get("source") != "pricing_policy"
    )
    coating_material_total = sum(
        _number(row.get("cost"), 0)
        for _, item in lines_df.iterrows()
        if (row := item.to_dict()).get("section") == "material"
        and row.get("source") != "pricing_policy"
        and isinstance(row.get("raw_agent_json"), dict)
        and str((row.get("raw_agent_json") or {}).get("facts", {}).get("family") or "")
        in {"wood_coatings", "metal_coatings"}
    )
    for _, item in lines_df.iterrows():
        row = item.to_dict()
        if row.get("section") != "material" or row.get("source") != "pricing_policy":
            continue
        raw_agent_json = row.get("raw_agent_json") or {}
        percent = _number(
            raw_agent_json.get("percent") if isinstance(raw_agent_json, dict) else None,
            0,
        )
        basis = raw_agent_json.get("basis") if isinstance(raw_agent_json, dict) else None
        base = coating_material_total if basis == "coatings" else primary_material_total
        amount = round(base * percent / 100, 2)
        update_rfq_estimate_line(
            client,
            estimate_id=estimate_id,
            line_id=str(row.get("line_id") or ""),
            values={"cost": amount, "updated_at": datetime.now(UTC).isoformat()},
        )
        lines_df.loc[lines_df["line_id"] == row.get("line_id"), "cost"] = amount
    material_total = 0.0
    labor_base_total = 0.0
    manufacturing_total = 0.0
    overhead_total = 0.0
    for _, line in lines_df.iterrows():
        row = line.to_dict()
        section = str(row.get("section") or "")
        cost = _number(row.get("cost"), 0)
        if section == "material":
            material_total += cost
        elif section == "labor":
            if row.get("source") == "manufacturing_engine":
                manufacturing_total += cost
            else:
                labor_base_total += cost
        elif section == "overhead":
            overhead_total += cost

    employer_load = round(labor_base_total * employer_load_percent / 100, 2)
    self_cost_ex_vat = round(
        material_total + labor_base_total + employer_load + manufacturing_total + overhead_total,
        2,
    )
    vat_amount = round(self_cost_ex_vat * vat_percent / 100, 2)
    update_rfq_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        self_cost_ex_vat=self_cost_ex_vat,
        vat_amount=vat_amount,
        self_cost_total=round(self_cost_ex_vat + vat_amount, 2),
        approved=approved,
    )


def _first_row(df: Any) -> dict[str, Any]:
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def _number(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, float) and value != value:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")
