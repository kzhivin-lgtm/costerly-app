"""Deterministic company-overhead allocation for Estimation v2."""

from __future__ import annotations

from typing import Any
from math import isfinite


_RESERVES = (
    ("warranty_reserve_percent", "Warranty reserve"),
    ("management_buffer_percent", "Management buffer"),
    ("design_bureau_commission_percent", "Design bureau commission"),
)


def estimate_object_overhead(
    *, estimate_id: str, object_id: str, company_id: str,
    settings: dict[str, Any], overhead_monthly: dict[str, Any],
    labor_hours: float | None, labor_cost: float | None,
    material_cost: float, partial: bool = False,
) -> dict[str, Any]:
    """Apply the preserved allocator to the current Materials/Labor subtotal.

    Hours and pay are supplied by the existing Labor calculation, including its
    saved overrides. This layer does not choose routes or recalculate wages.
    """
    capacity = _monthly_capacity_hours(settings)
    result: dict[str, Any] = {
        "status": "pending_labor", "object_id": object_id, "estimate_id": estimate_id,
        "company_id": company_id, "lines": [], "capacity_hours": capacity,
        "labor_hours": labor_hours, "material_cost": material_cost,
        "cost": None, "vat": None, "total": None,
        "vat_percent": _number(settings.get("vat_percent"), 18), "partial": partial,
    }
    if not isfinite(capacity) or capacity <= 0:
        return {**result, "status": "missing_capacity"}
    if labor_hours is None or labor_cost is None:
        return result
    hours, pay, materials = float(labor_hours), float(labor_cost), float(material_cost)
    if not all(isfinite(value) and value >= 0 for value in (hours, pay, materials)):
        return {**result, "status": "invalid_basis"}
    lines = build_overhead_lines(
        estimate_id=estimate_id, object_id=object_id, company_id=company_id,
        settings=settings, overhead_monthly=overhead_monthly,
        labor_hours_total=hours, subtotal_before_overhead=materials + pay,
    )
    if hours == 0:
        # Keep configured rows available for a subsequent manual-hours edit.
        # The legacy allocator's zero-hour result remains exactly zero.
        for field, group, label in _monthly_overhead_map():
            amount = _number(overhead_monthly.get(field), 0)
            if amount > 0:
                lines.append(_overhead_line(
                    estimate_id=estimate_id, object_id=object_id, company_id=company_id,
                    line_id=f"{object_id}_overhead_zero_{field}", group_name=group,
                    item_name=label, monthly_cost=amount, allocation_basis=f"0h / {_format_number(capacity)}h",
                    cost=0, sort_order=10000 + len(lines),
                    raw_json={"source_column": field, "labor_hours_total": 0,
                              "monthly_capacity_hours": capacity},
                ))
        for field, label in _RESERVES:
            percent = _number(settings.get(field), 0)
            if percent > 0:
                lines.append(_overhead_line(
                    estimate_id=estimate_id, object_id=object_id, company_id=company_id,
                    line_id=f"{object_id}_overhead_zero_{field}", group_name="Project reserves",
                    item_name=label, monthly_cost=percent, allocation_basis=f"{_format_number(percent)}% of self-cost",
                    cost=0, sort_order=10000 + len(lines),
                    raw_json={"source_column": field, "reserve_base": 0, "percent": percent},
                ))
    cost = round(sum(line["cost"] for line in lines), 2)
    vat = round(cost * result["vat_percent"] / 100, 2)
    return {**result, "status": "ready", "lines": lines,
            "cost": cost, "vat": vat, "total": round(cost + vat, 2)}


def build_overhead_lines(
    *, estimate_id: str, object_id: str, company_id: str,
    settings: dict[str, Any], overhead_monthly: dict[str, Any],
    labor_hours_total: float, subtotal_before_overhead: float,
) -> list[dict[str, Any]]:
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
        rows.append(_overhead_line(
            estimate_id=estimate_id, object_id=object_id, company_id=company_id,
            line_id=f"{object_id}_overhead_{sort_order:04d}", group_name=group_name,
            item_name=item_name, monthly_cost=monthly_cost,
            allocation_basis=f"{_format_number(labor_hours_total)}h / {_format_number(monthly_capacity_hours)}h",
            cost=cost, sort_order=sort_order,
            raw_json={"source_column": column, "labor_hours_total": labor_hours_total,
                      "monthly_capacity_hours": monthly_capacity_hours},
        ))
    reserve_base = subtotal_before_overhead + monthly_overhead_total
    for column, label in _RESERVES:
        percent = _number(settings.get(column), 0)
        if percent <= 0:
            continue
        sort_order += 10
        rows.append(_overhead_line(
            estimate_id=estimate_id, object_id=object_id, company_id=company_id,
            line_id=f"{object_id}_overhead_{sort_order:04d}", group_name="Project reserves",
            item_name=label, monthly_cost=percent,
            allocation_basis=f"{_format_number(percent)}% of self-cost",
            cost=round(reserve_base * percent / 100, 2), sort_order=sort_order,
            raw_json={"source_column": column, "reserve_base": reserve_base, "percent": percent},
        ))
    return rows


def _overhead_line(**values: Any) -> dict[str, Any]:
    raw_json = values.pop("raw_json")
    return {
        **values, "section": "overhead", "source": "overhead_engine",
        "sort_order": values["sort_order"], "needs_price": False,
        "needs_review": False, "raw_agent_json": raw_json,
    }


def _monthly_capacity_hours(settings: dict[str, Any]) -> float:
    return (
        _number(settings.get("production_workers"), 0)
        * _number(settings.get("workdays_per_month"), 0)
        * _number(settings.get("hours_per_day"), 0)
    )


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
        ("other_spendings_cost", "Other spendings", "Other spendings"),
    )


def _number(value: Any, default: float) -> float:
    try:
        return default if value is None or value == "" else float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}".rstrip("0").rstrip(".")
