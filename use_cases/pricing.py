from __future__ import annotations

import re
from typing import Any

import pandas as pd

from db.repositories import (
    fetch_company_data,
    fetch_rfq_estimate_lines_for_object,
    replace_rfq_overhead_lines_for_object,
    update_rfq_estimate_line,
    update_rfq_object_estimate_totals,
)
from db.supabase_client import get_supabase_client


def price_estimated_object(
    *,
    estimate_id: str,
    object_id: str,
    company_id: str,
) -> dict[str, float]:
    """Resolve catalog prices/rates and calculate object self-cost totals."""
    client = get_supabase_client()
    company_data = fetch_company_data(client, company_id)
    lines_df = fetch_rfq_estimate_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
    )

    settings = _first_row(company_data["overhead_settings"])
    vat_percent = _number(settings.get("vat_percent"), 18)
    employer_load_percent = _number(settings.get("employer_load_percent"), 25)

    material_total = 0.0
    labor_base_total = 0.0
    labor_hours_total = 0.0

    for _, line in lines_df.iterrows():
        item = line.to_dict()
        if item.get("section") == "material":
            line_cost = _price_material_line(client, item, company_data["materials"])
            material_total += line_cost
        elif item.get("section") == "labor":
            line_cost = _price_labor_line(client, item, company_data["labor"])
            labor_base_total += line_cost
            labor_hours_total += _number(item.get("hours"), 0)

    labor_total = labor_base_total * (1 + employer_load_percent / 100)
    overhead_lines = _build_overhead_lines(
        estimate_id=estimate_id,
        object_id=object_id,
        company_id=company_id,
        settings=settings,
        overhead_monthly=_first_row(company_data["overhead_monthly"]),
        labor_hours_total=labor_hours_total,
        subtotal_before_overhead=material_total + labor_total,
    )
    replace_rfq_overhead_lines_for_object(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        lines=overhead_lines,
    )

    overhead_total = sum(_number(line.get("cost"), 0) for line in overhead_lines)
    self_cost_ex_vat = round(material_total + labor_total + overhead_total, 2)
    vat_amount = round(self_cost_ex_vat * vat_percent / 100, 2)
    self_cost_total = round(self_cost_ex_vat + vat_amount, 2)

    update_rfq_object_estimate_totals(
        client,
        estimate_id=estimate_id,
        object_id=object_id,
        self_cost_ex_vat=self_cost_ex_vat,
        vat_amount=vat_amount,
        self_cost_total=self_cost_total,
    )

    return {
        "material_total": round(material_total, 2),
        "labor_base_total": round(labor_base_total, 2),
        "labor_total": round(labor_total, 2),
        "labor_hours_total": round(labor_hours_total, 2),
        "overhead_total": round(overhead_total, 2),
        "self_cost_ex_vat": self_cost_ex_vat,
        "vat_amount": vat_amount,
        "self_cost_total": self_cost_total,
    }


def _price_material_line(client: Any, line: dict[str, Any], materials_df: pd.DataFrame) -> float:
    """Match an agent material line to the company material catalog."""
    match = _best_material_match(line, materials_df)
    quantity = _number(line.get("quantity"), 0)

    if match is None:
        update_rfq_estimate_line(
            client,
            estimate_id=line["estimate_id"],
            line_id=line["line_id"],
            values={"needs_price": True, "needs_review": True},
        )
        return 0.0

    unit_cost = _number(match.get("price"), 0)
    waste_pct = _number(match.get("waste_pct"), 0)
    cost = round(quantity * unit_cost * (1 + waste_pct / 100), 2)

    update_rfq_estimate_line(
        client,
        estimate_id=line["estimate_id"],
        line_id=line["line_id"],
        values={
            "unit_cost": unit_cost,
            "cost": cost,
            "needs_price": False,
            "needs_review": bool(line.get("needs_review")),
        },
    )
    return cost


def _price_labor_line(client: Any, line: dict[str, Any], labor_df: pd.DataFrame) -> float:
    """Match an agent labor role to company labor rates."""
    match = _best_labor_match(line, labor_df)
    hours = _number(line.get("hours"), 0)

    if match is None:
        update_rfq_estimate_line(
            client,
            estimate_id=line["estimate_id"],
            line_id=line["line_id"],
            values={"needs_review": True},
        )
        return 0.0

    rate = _labor_rate(match)
    cost = round(hours * rate, 2)

    update_rfq_estimate_line(
        client,
        estimate_id=line["estimate_id"],
        line_id=line["line_id"],
        values={
            "rate": rate,
            "cost": cost,
            "needs_review": bool(line.get("needs_review")),
        },
    )
    return cost


def _build_overhead_lines(
    *,
    estimate_id: str,
    object_id: str,
    company_id: str,
    settings: dict[str, Any],
    overhead_monthly: dict[str, Any],
    labor_hours_total: float,
    subtotal_before_overhead: float,
) -> list[dict[str, Any]]:
    """Allocate company overhead to one object from deterministic settings."""
    if labor_hours_total <= 0:
        return []

    monthly_capacity_hours = _monthly_capacity_hours(settings)
    if monthly_capacity_hours <= 0:
        return []

    sort_order = 10_000
    rows: list[dict[str, Any]] = []
    monthly_overhead_total = 0.0

    for column, group_name, item_name in _monthly_overhead_map():
        monthly_cost = _number(overhead_monthly.get(column), 0)
        if monthly_cost <= 0:
            continue

        sort_order += 10
        cost = round(monthly_cost * labor_hours_total / monthly_capacity_hours, 2)
        monthly_overhead_total += cost
        rows.append(
            _overhead_line(
                estimate_id=estimate_id,
                object_id=object_id,
                company_id=company_id,
                line_id=f"{object_id}_overhead_{sort_order:04d}",
                group_name=group_name,
                item_name=item_name,
                monthly_cost=monthly_cost,
                allocation_basis=f"{_format_number(labor_hours_total)}h / {_format_number(monthly_capacity_hours)}h",
                cost=cost,
                sort_order=sort_order,
                raw_json={
                    "source_column": column,
                    "labor_hours_total": labor_hours_total,
                    "monthly_capacity_hours": monthly_capacity_hours,
                },
            )
        )

    reserve_base = subtotal_before_overhead + monthly_overhead_total
    for column, label in (
        ("warranty_reserve_percent", "Warranty reserve"),
        ("management_buffer_percent", "Management buffer"),
        ("design_bureau_commission_percent", "Design bureau commission"),
    ):
        percent = _number(settings.get(column), 0)
        if percent <= 0:
            continue

        sort_order += 10
        cost = round(reserve_base * percent / 100, 2)
        rows.append(
            _overhead_line(
                estimate_id=estimate_id,
                object_id=object_id,
                company_id=company_id,
                line_id=f"{object_id}_overhead_{sort_order:04d}",
                group_name="Project reserves",
                item_name=label,
                monthly_cost=percent,
                allocation_basis=f"{_format_number(percent)}% of self-cost",
                cost=cost,
                sort_order=sort_order,
                raw_json={
                    "source_column": column,
                    "reserve_base": reserve_base,
                    "percent": percent,
                },
            )
        )

    return rows


def _overhead_line(
    *,
    estimate_id: str,
    object_id: str,
    company_id: str,
    line_id: str,
    group_name: str,
    item_name: str,
    monthly_cost: float,
    allocation_basis: str,
    cost: float,
    sort_order: int,
    raw_json: dict[str, Any],
) -> dict[str, Any]:
    return {
        "estimate_id": estimate_id,
        "object_id": object_id,
        "line_id": line_id,
        "company_id": company_id,
        "section": "overhead",
        "group_name": group_name,
        "item_name": item_name,
        "monthly_cost": monthly_cost,
        "allocation_basis": allocation_basis,
        "cost": cost,
        "source": "pricing_engine",
        "sort_order": sort_order,
        "needs_price": False,
        "needs_review": False,
        "raw_agent_json": raw_json,
    }


def _monthly_capacity_hours(settings: dict[str, Any]) -> float:
    production_workers = _number(settings.get("production_workers"), 0)
    workdays_per_month = _number(settings.get("workdays_per_month"), 0)
    hours_per_day = _number(settings.get("hours_per_day"), 0)
    return production_workers * workdays_per_month * hours_per_day


def _monthly_overhead_map() -> tuple[tuple[str, str, str], ...]:
    return (
        ("rent_facilities_cost", "Facility / rent / arnona", "Rent"),
        ("arnona_facilities_cost", "Facility / rent / arnona", "Arnona"),
        ("maintenance_fee_facilities_cost", "Facility / rent / arnona", "Maintenance fee"),
        ("electricity_utilities_cost", "Utilities / safety", "Electricity"),
        ("water_utilities_cost", "Utilities / safety", "Water"),
        ("compressed_air_gas_utilities_cost", "Utilities / safety", "Compressed air / gas"),
        ("insurance_safety_fire_utilities_cost", "Utilities / safety", "Insurance / safety / fire"),
        ("equipment_depreciation_machinery_cost", "Machinery / equipment", "Equipment depreciation"),
        ("machine_consumables_wear_machinery_cost", "Machinery / equipment", "Machine consumables / wear"),
        ("software_subscriptions_admin_cost", "Software / shop supplies / waste", "Software subscriptions"),
        ("shop_supplies_cleaning_admin_cost", "Software / shop supplies / waste", "Shop supplies / cleaning"),
        ("waste_removal_admin_cost", "Software / shop supplies / waste", "Waste removal"),
    )


def _best_material_match(line: dict[str, Any], materials_df: pd.DataFrame) -> dict[str, Any] | None:
    if materials_df.empty:
        return None

    query = _tokens(
        " ".join(
            str(line.get(key) or "")
            for key in ("catalog_match_query", "item_name", "group_name", "unit")
        )
    )
    best_score = 0
    best_row: dict[str, Any] | None = None

    for _, row in materials_df.iterrows():
        item = row.to_dict()
        haystack = _tokens(
            " ".join(
                str(item.get(key) or "")
                for key in (
                    "material_name",
                    "material_type",
                    "material_category",
                    "surface",
                    "finish",
                    "substrate",
                    "size",
                    "thickness",
                )
            )
        )
        score = len(query & haystack)
        if score > best_score:
            best_score = score
            best_row = item

    return best_row if best_score > 0 else None


def _best_labor_match(line: dict[str, Any], labor_df: pd.DataFrame) -> dict[str, Any] | None:
    if labor_df.empty:
        return None

    query = _tokens(
        " ".join(str(line.get(key) or "") for key in ("role", "item_name", "group_name"))
    )
    best_score = 0
    best_row: dict[str, Any] | None = None

    for _, row in labor_df.iterrows():
        item = row.to_dict()
        if item.get("active") is False:
            continue
        haystack = _tokens(
            " ".join(
                str(item.get(key) or "")
                for key in ("labor_code", "role_name", "role_group", "role_level")
            )
        )
        score = len(query & haystack)
        if score > best_score:
            best_score = score
            best_row = item

    return best_row if best_score > 0 else None


def _labor_rate(row: dict[str, Any]) -> float:
    hourly_rate = _number(row.get("hourly_rate"), 0)
    if hourly_rate > 0:
        return hourly_rate

    monthly_salary = _number(row.get("monthly_salary"), 0)
    monthly_hours = _number(row.get("monthly_hours"), 0)
    if monthly_salary > 0 and monthly_hours > 0:
        return round(monthly_salary / monthly_hours, 2)
    return 0.0


def _first_row(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def _number(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-zA-Z0-9]+", value.lower())
        if len(token) >= 3
    }
