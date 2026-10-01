from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from db.repositories import (
    fetch_company_overhead_settings,
    fetch_latest_estimation_v2_facts_by_object,
    fetch_rfq_estimate_pricing_overrides,
    fetch_rfq_estimate_lines_for_object,
    fetch_rfq_object_estimates,
    fetch_rfq_detected_objects,
    fetch_rfq_run,
    update_rfq_estimate_line,
    update_rfq_object_estimate_approved,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
    upsert_rfq_estimate_shell,
)
from db.supabase_client import get_supabase_client
from db.company_access import assert_estimate_owned, assert_run_owned
from state.company_auth import company_auth_enabled
from state.session import get_company_id
from models.estimation import ObjectEstimateSeed
from use_cases.retry import read_with_retry


def _assert_screen_estimate_access(client: Any, estimate_id: str) -> None:
    if company_auth_enabled():
        assert_estimate_owned(client, estimate_id, get_company_id())


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
    sale_price_overrides = _pricing_overrides_by_object(overrides_df)
    facts_by_object: dict[str, dict] = {}
    if not objects_df.empty:
        run_id = str(objects_df.iloc[0].get("run_id") or "")
        if run_id:
            try:
                facts_by_object = fetch_latest_estimation_v2_facts_by_object(
                    client,
                    run_id=run_id,
                )
            except Exception:
                facts_by_object = {}

    rows = []
    for _, item in objects_df.iterrows():
        row = item.to_dict()
        object_id = str(row.get("object_id") or "")
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
        sale_price_unit = _suggested_sale_price(self_cost) if status == "completed" else None
        sale_price_overridden = status == "completed" and row.get("object_id") in sale_price_overrides
        if sale_price_overridden:
            sale_price_unit = sale_price_overrides[row.get("object_id")]
        rows.append(
            {
                "object_key": row.get("object_id"),
                "name": row.get("object_name"),
                "materials": ", ".join(material_names),
                "quantity": row.get("quantity"),
                "self_cost_unit": self_cost if self_cost is not None else status,
                "status": status,
                "progress_percent": row.get("progress_percent"),
                "progress_label": row.get("progress_label"),
                "progress_updated_at": row.get("progress_updated_at"),
                "sale_price_unit": sale_price_unit,
                "sale_price_total": _line_total(sale_price_unit, row.get("quantity")),
                "sale_price_overridden": sale_price_overridden,
                "suggestion": "suggested: SC + 30%",
                "reviewed": bool(row.get("approved")),
                "details_available": bool(facts_result),
                "facts_status": facts_result.get("status"),
            }
        )

    vat_percent = 18.0
    if not objects_df.empty:
        company_id = str(objects_df.iloc[0].get("company_id") or "")
        if company_id:
            settings = _first_row(fetch_company_overhead_settings(client, company_id))
            vat_percent = _number(settings.get("vat_percent"), 18)
    project_costs, summary = _objects_project_pricing(
        rows,
        sale_price_overrides,
        vat_percent=vat_percent,
    )
    return {
        "rows": rows,
        "project_costs": project_costs,
        "summary": summary,
    }


def _suggested_sale_price(self_cost: Any) -> float | None:
    """Return MVP suggested sale price: self cost plus 30%."""
    if self_cost is None or self_cost == "":
        return None
    if isinstance(self_cost, float) and self_cost != self_cost:
        return None
    return round(_number(self_cost, 0) * 1.3, 2)


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
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Calculate project-level suggested costs after all objects are priced."""
    sale_price_overrides = sale_price_overrides or {}
    object_rows = [row for row in rows if row.get("object_key")]
    all_completed = bool(object_rows) and all(
        str(row.get("status") or "").lower() == "completed" for row in object_rows
    )
    objects_subtotal = sum(_number(row.get("sale_price_total"), 0) for row in object_rows)

    delivery_suggested = round(objects_subtotal * 0.03, 2) if all_completed else None
    installation_suggested = round(objects_subtotal * 0.10, 2) if all_completed else None
    delivery = sale_price_overrides.get("delivery", delivery_suggested)
    installation = sale_price_overrides.get("installation", installation_suggested)
    project_price = (
        round(objects_subtotal + _number(delivery, 0) + _number(installation, 0), 2)
        if all_completed
        else None
    )
    vat = (
        round(_number(project_price, 0) * _number(vat_percent, 18) / 100, 2)
        if all_completed
        else None
    )
    total = round(_number(project_price, 0) + _number(vat, 0), 2) if all_completed else None

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
                "suggestion": "" if "delivery" in sale_price_overrides else "suggested: 3% of objects subtotal",
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
                "suggestion": "" if "installation" in sale_price_overrides else "suggested: 10% of objects subtotal",
                "reviewed": False,
            },
        ],
        {"project_price": project_price, "vat": vat, "total": total},
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

    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        raise RuntimeError(f"Object estimate not found: {estimate_id}/{object_id}")

    object_row = matching.iloc[0].to_dict()
    facts_result = {}
    try:
        facts_result = fetch_latest_estimation_v2_facts_by_object(
            client,
            run_id=str(object_row.get("run_id") or ""),
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
            material_rows.append(
                {
                    "group": item.get("group_name"),
                    "line_id": item.get("line_id"),
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
        material_rows = _material_rows_from_v2_facts(facts_payload)

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
        "name": object_row.get("object_name"),
        "quantity": object_row.get("quantity"),
        "approved": bool(object_row.get("approved")),
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
                "columns": ["Item", "Unit", "Unit cost", "Qty", "Cost"],
                "rows": material_rows,
            },
            {
                "key": "labor",
                "title": "Labor cost",
                "metrics": [
                    ("Total hours", f"{_format_number(labor_hours_total)} h"),
                    ("Cost", labor_base_total),
                    ("Employer 25%", employer_load),
                    ("Total", labor_total),
                ],
                "columns": ["Work", "Role", "Hours", "Rate", "Cost"],
                "rows": labor_rows,
            },
            {
                "key": "overhead",
                "title": "Overhead",
                "metrics": [
                    ("Cost", overhead_total),
                    ("VAT", round(overhead_total * vat_percent / 100, 2)),
                    ("Total", round(overhead_total * (1 + vat_percent / 100), 2)),
                ],
                "columns": ["Group", "Monthly cost", "Allocation", "Cost"],
                "rows": overhead_rows,
            },
        ],
        "self_cost": {
            "title": f"{object_row.get('object_name') or 'Object'} self cost (SC)",
            "excl_vat": object_row.get("self_cost_ex_vat"),
            "vat": object_row.get("vat_amount"),
            "total": object_row.get("self_cost_total"),
        },
    }


def _material_rows_from_v2_facts(facts_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for material in facts_payload.get("materials") or []:
        if not isinstance(material, dict):
            continue
        rows.append({
            "group": "Detected materials",
            "line_id": material.get("requirement_id"),
            "item": material.get("source_name") or material.get("family"),
            "unit": material.get("unit"),
            "unit_cost": None,
            "qty": material.get("quantity"),
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
    updates: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}

    if field == "allocation_basis":
        if section != "overhead":
            return
        updates["allocation_basis"] = str(value or "").strip()
    else:
        numeric_value = _number_from_edit(value)
        updates[field] = numeric_value

        if section == "material" and field in {"unit_cost", "quantity"}:
            unit_cost = numeric_value if field == "unit_cost" else _number(line.get("unit_cost"), 0)
            quantity = numeric_value if field == "quantity" else _number(line.get("quantity"), 0)
            updates["cost"] = round(unit_cost * quantity, 2)
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
    _recalculate_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )


def apply_object_detail_snapshot(
    *,
    estimate_id: str,
    object_id: str,
    edits: list[Any],
) -> None:
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
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        line_id = str(edit.get("line_id") or "")
        field = str(edit.get("field") or "")
        if not line_id or field not in allowed_fields:
            continue
        edits_by_line.setdefault(line_id, {})[field] = edit.get("value")

    if not edits_by_line:
        return

    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )
    if lines_df.empty:
        return

    for _, item in lines_df.iterrows():
        line = item.to_dict()
        line_id = str(line.get("line_id") or "")
        line_edits = edits_by_line.get(line_id)
        if not line_edits:
            continue

        section = str(line.get("section") or "")
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
            updates["cost"] = round(
                _number(next_values.get("unit_cost"), 0)
                * _number(next_values.get("quantity"), 0),
                2,
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

    _recalculate_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )


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
