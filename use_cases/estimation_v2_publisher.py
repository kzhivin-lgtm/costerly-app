"""Deterministic Estimation v2 publisher for the existing product UI.

Object Facts are evidence-backed input only. This module owns material price
resolution, Labor Engine execution, overhead allocation, persistence and the
final object status consumed by Objects and Object Detail.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Sequence

from db.repositories import (
    fetch_active_israel_material_families,
    fetch_estimation_v2_fact_result,
    replace_rfq_estimate_lines_for_object,
    update_rfq_object_estimate_progress,
    update_rfq_object_estimate_totals,
)
from agents.estimation_v2_facts_agent import ESTIMATION_V2_FACTS_AGENT_VERSION
from use_cases.estimate_material_resolution import resolve_estimate_material_requirement
from use_cases.estimation_v2_bom import EstimationV2BomError, derive_supported_bom
from use_cases.estimation_v2_composition import compose_object_estimate, validate_object_facts
from use_cases.estimation_v2_labor_adapter import build_labor_input_v1
from use_cases.labor_engine import estimate_labor
from use_cases.machinery import build_company_production_context
from use_cases.material_price_resolver import _unit_price_multiplier
from use_cases.overhead_engine import build_overhead_lines


_ROLE_CANDIDATES = {
    "carpenter": ("carpenter",),
    "cnc_operator": ("cnc_operator",),
    "wood_machine_operator": ("cnc_operator", "carpenter"),
    "general_worker": ("general_worker", "carpenter"),
    "packer": ("general_worker", "carpenter"),
    "production_manager": ("production_manager", "general_manager"),
    "welder": ("welder",),
    "metal_machine_operator": ("welder", "general_worker"),
    "press_brake_operator": ("welder",),
    "grinder_polisher": ("painter_finisher", "welder"),
    "metal_finisher": ("painter_finisher", "welder"),
    "powder_coating_operator": ("painter_finisher",),
}


def _rows(client: Any, table: str, *, company_id: str | None = None) -> list[dict[str, Any]]:
    query = client.table(table).select("*")
    if company_id:
        query = query.eq("company_id", company_id)
    return [dict(row) for row in (query.execute().data or [])]


def _paged_rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read a full resolver catalog instead of PostgREST's first 1,000 rows."""
    page_size = 1000
    start = 0
    result: list[dict[str, Any]] = []
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(start, start + page_size - 1).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < page_size:
            return result
        start += page_size


def _number(value: Any, default: float = 0) -> float:
    try:
        return default if value is None or value == "" else float(value)
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(child) for child in value]
    return value


def _public_facts(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: child for key, child in value.items() if not str(key).startswith("_bom_")}


def _settings(client: Any, company_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = _rows(client, "overhead_settings", company_id=company_id)
    monthly = _rows(client, "overhead_monthly", company_id=company_id)
    return (settings[0] if settings else {}, monthly[0] if monthly else {})


def _catalogs(client: Any, company_id: str) -> dict[str, list[dict[str, Any]]]:
    identities = _paged_rows(
        client,
        "reference_material_pricing_identities",
        filters={"market_code": "IL", "status": "active"},
    )
    prices = _paged_rows(
        client,
        "market_material_pricing_identity_prices",
        filters={"status": "active"},
    )
    return {
        "items": _rows(client, "company_material_items", company_id=company_id),
        "offers": _rows(client, "company_material_offers", company_id=company_id),
        "identities": identities,
        "prices": prices,
        "reference_materials": _paged_rows(client, "reference_materials", filters={"active": True}),
        "pricing_identity_members": _paged_rows(
            client, "reference_material_pricing_identity_members", filters={}
        ),
    }


def _company_offer_price(
    resolution: Any,
    offers: Sequence[Mapping[str, Any]],
    *,
    requested_unit: str,
    vat_percent: float,
) -> tuple[float | None, str]:
    candidates: list[tuple[Decimal, str]] = []
    allowed = set(resolution.offer_ids)
    for offer in offers:
        offer_id = str(offer.get("offer_id") or "")
        if offer_id not in allowed:
            continue
        multiplier = _unit_price_multiplier(str(offer.get("normalized_unit") or ""), requested_unit)
        if multiplier is None:
            continue
        try:
            price = Decimal(str(offer.get("normalized_price"))) * multiplier
        except Exception:
            continue
        if offer.get("vat_included") is True:
            price /= Decimal("1") + Decimal(str(vat_percent)) / Decimal("100")
        if price > 0:
            candidates.append((price, offer_id))
    if not candidates:
        return None, "company-offer:unavailable"
    candidates.sort(key=lambda item: (item[0], item[1]))
    middle = candidates[(len(candidates) - 1) // 2]
    return round(float(middle[0]), 4), f"company-offer:{middle[1]}"


def _material_rows_and_costs(
    *,
    facts: Mapping[str, Any],
    catalogs: Mapping[str, Sequence[Mapping[str, Any]]],
    vat_percent: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for index, material in enumerate(facts.get("materials") or [], start=1):
        line_id = f"{facts['object_id']}_material_{index:04d}"
        quantity = _number(material.get("quantity"))
        unit = str(material.get("unit") or "")
        resolution = resolve_estimate_material_requirement(
            requirement_name=str(material.get("source_name") or material.get("family") or ""),
            material_family=str(material.get("family") or "") or None,
            specifications=material.get("specification") or {},
            requested_unit=unit,
            company_material_items=catalogs["items"],
            company_offers=catalogs["offers"],
            pricing_identities=catalogs["identities"],
            pricing_identity_prices=catalogs["prices"],
            reference_materials=catalogs.get("reference_materials") or [],
            pricing_identity_members=catalogs.get("pricing_identity_members") or [],
            as_of=date.today(),
        )
        unit_cost: float | None = None
        source_ref = "material-resolution:unresolved"
        if resolution.status == "resolved" and resolution.authority == "company":
            unit_cost, source_ref = _company_offer_price(
                resolution, catalogs["offers"], requested_unit=unit, vat_percent=vat_percent
            )
        elif resolution.status == "resolved" and resolution.price_typical is not None:
            unit_cost = float(resolution.price_typical)
            source_ref = f"israel-pricing:{resolution.pricing_identity_price_id}"
        cost = round(quantity * unit_cost, 2) if unit_cost is not None and quantity > 0 else None
        reason_codes = [] if cost is not None else ["material_price_unresolved"]
        assumption_review = material.get("requirement_id") in {"bom-profile", "bom-mdf"}
        cost_lines.append({
            "line_id": line_id, "section": "material",
            "status": "resolved" if cost is not None else "review_required",
            "amount": cost, "currency": "ILS", "source_ref": source_ref,
            "reason_codes": reason_codes,
        })
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "material",
            "group_name": "Materials", "item_name": material.get("source_name") or material.get("family"),
            "catalog_match_query": material.get("source_name"), "unit": unit,
            "unit_cost": unit_cost, "quantity": quantity or None, "cost": cost,
            "source": "estimation_v2", "sort_order": index * 10,
            "needs_price": cost is None, "needs_review": cost is None or assumption_review,
            "confidence": (facts.get("template") or {}).get("confidence"),
            "raw_agent_json": _json_safe({
                "facts": dict(material), "resolution": resolution.__dict__,
                "bom_calculation": (facts.get("_bom_calculations") or {}).get(material.get("requirement_id")),
                "bom_assumptions": facts.get("_bom_assumptions") or [],
            }),
        })
    return db_rows, cost_lines


def _purchased_component_rows_and_costs(
    facts: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Expose unresolved bought fabrication in Object Detail, never as free material."""
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    for index, component in enumerate(facts.get("purchased_components") or [], start=1):
        line_id = f"{facts['object_id']}_purchased_{index:04d}"
        component_type = str(component.get("component_type") or "Purchased component")
        db_rows.append({
            "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
            "line_id": line_id, "company_id": facts["company_id"], "section": "material",
            "group_name": "Purchased fabricated components",
            "item_name": component_type.replace("_", " ").title(),
            "unit": component.get("unit"), "quantity": component.get("quantity"),
            "unit_cost": None, "cost": None, "source": "estimation_v2",
            "sort_order": 500 + index * 10, "needs_price": True, "needs_review": True,
            "raw_agent_json": _json_safe(dict(component)),
        })
        cost_lines.append({
            "line_id": f"{line_id}_cost", "section": "purchased_component",
            "status": "review_required", "amount": None, "currency": "ILS",
            "source_ref": f"purchased-component:{component.get('component_id') or index}",
            "reason_codes": ["purchased_component_price_unresolved"],
        })
    return db_rows, cost_lines


def _employee_rate(employee: Mapping[str, Any], monthly_capacity: float) -> float | None:
    gross_hourly = _number(employee.get("gross_hourly_rate"))
    if gross_hourly > 0:
        return gross_hourly
    gross_monthly = _number(employee.get("gross_monthly_salary"))
    return round(gross_monthly / monthly_capacity, 4) if gross_monthly > 0 and monthly_capacity > 0 else None


def _role_rate(
    role: str,
    employees: Sequence[Mapping[str, Any]],
    monthly_capacity: float,
) -> tuple[float | None, str | None]:
    active = [row for row in employees if not row.get("deleted_at")]
    for position in _ROLE_CANDIDATES.get(role, (role,)):
        matches = [row for row in active if str(row.get("position_code") or "") == position]
        rates = [rate for row in matches if (rate := _employee_rate(row, monthly_capacity)) is not None]
        if rates:
            return round(sum(rates) / len(rates), 4), position
    return None, None


def _labor_rows_and_costs(
    *, client: Any, facts: Mapping[str, Any], settings: Mapping[str, Any],
    employees: Sequence[Mapping[str, Any]] | None = None,
    production_context: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, float]:
    labor_input = build_labor_input_v1(facts)
    context = dict(production_context or build_company_production_context(str(facts["company_id"]), client=client))
    result = estimate_labor(labor_input, context)
    if result.get("status") != "estimated":
        return [], [{
            "line_id": f"{facts['object_id']}_labor_unresolved", "section": "labor",
            "status": "review_required", "amount": None, "currency": "ILS",
            "source_ref": "labor-engine:review", "reason_codes": ["labor_review_required"],
        }], 0, 0
    employees = list(employees) if employees is not None else _rows(
        client, "company_employees", company_id=str(facts["company_id"])
    )
    monthly_capacity = (
        _number(settings.get("workdays_per_month"), 22)
        * _number(settings.get("hours_per_day"), 8)
    )
    db_rows: list[dict[str, Any]] = []
    cost_lines: list[dict[str, Any]] = []
    base_total = 0.0
    hours_total = 0.0
    unresolved = False
    sort_order = 1000
    for operation in result.get("labor_lines") or []:
        for allocation in operation.get("role_allocations") or []:
            sort_order += 10
            role = str(allocation.get("role") or "")
            hours = _number(allocation.get("hours"))
            rate, matched_role = _role_rate(role, employees, monthly_capacity)
            cost = round(hours * rate, 2) if rate is not None and hours > 0 else None
            unresolved = unresolved or cost is None
            if cost is not None:
                base_total += cost
                hours_total += hours
            db_rows.append({
                "estimate_id": facts["estimate_id"], "object_id": facts["object_id"],
                "line_id": f"{facts['object_id']}_labor_{sort_order:04d}",
                "company_id": facts["company_id"], "section": "labor",
                "group_name": "Labor", "item_name": str(operation.get("operation_code") or "Work").replace("_", " ").title(),
                "role": matched_role or role, "hours": hours, "rate": rate, "cost": cost,
                "source": "labor_engine_v0", "sort_order": sort_order,
                "needs_price": False, "needs_review": cost is None,
                "confidence": operation.get("baseline_confidence"), "hours_basis": operation.get("formula"),
                "raw_agent_json": dict(operation),
            })
    employer_percent = _number(settings.get("employer_load_percent"), 25)
    labor_total = round(base_total * (1 + employer_percent / 100), 2)
    cost_lines.append({
        "line_id": f"{facts['object_id']}_labor_total", "section": "labor",
        "status": "review_required" if unresolved else "resolved",
        "amount": None if unresolved else labor_total, "currency": "ILS",
        "source_ref": "labor-engine:labor_time_v0",
        "reason_codes": ["labor_review_required"] if unresolved else [],
    })
    return db_rows, cost_lines, hours_total, labor_total


def _safe_db_lines(lines: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Keep the publisher compatible until optional classification migration lands."""
    return [
        {key: value for key, value in dict(line).items() if key not in {"economic_classification", "price_scope"}}
        for line in lines
    ]


def build_estimation_v2_context(client: Any, company_id: str) -> dict[str, Any]:
    settings, overhead_monthly = _settings(client, company_id)
    return {
        "families": fetch_active_israel_material_families(client),
        "catalogs": _catalogs(client, company_id),
        "settings": settings,
        "overhead_monthly": overhead_monthly,
        "employees": _rows(client, "company_employees", company_id=company_id),
        "production_context": build_company_production_context(company_id, client=client),
    }


def publish_estimation_v2_object(
    *, client: Any, estimate_id: str, input_row: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    input_id = str(input_row.get("input_id") or "")
    object_id = str(input_row.get("object_id") or "")
    fact_result = fetch_estimation_v2_fact_result(
        client, input_id=input_id, agent_version=ESTIMATION_V2_FACTS_AGENT_VERSION
    )
    if not fact_result:
        raise RuntimeError("Object Facts result is missing after extraction.")
    facts = dict(fact_result.get("facts_payload") or {})
    shared = dict(context or build_estimation_v2_context(client, str(facts["company_id"])))
    families = set(shared["families"])
    validate_object_facts(facts, allowed_material_families=families)

    bom_result = None
    if facts.get("status") != "failed":
        try:
            bom_result = derive_supported_bom(facts)
        except EstimationV2BomError:
            bom_result = None
    if bom_result is not None:
        facts = dict(bom_result["facts"])
        validate_object_facts(facts, allowed_material_families=families)
        facts["_bom_calculations"] = dict(bom_result["calculations"])
        facts["_bom_assumptions"] = list(bom_result["assumptions"])

    if facts.get("status") != "ready":
        review_facts = {**facts, "estimate_id": estimate_id}
        review_settings = dict(shared.get("settings") or {})
        material_rows, _material_costs = _material_rows_and_costs(
            facts=review_facts,
            catalogs=shared.get("catalogs") or {"items": [], "offers": [], "identities": [], "prices": []},
            vat_percent=_number(review_settings.get("vat_percent"), 18),
        )
        purchased_rows, _purchased_costs = _purchased_component_rows_and_costs(review_facts)
        replace_rfq_estimate_lines_for_object(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            lines=_safe_db_lines([*material_rows, *purchased_rows]),
        )
        update_rfq_object_estimate_progress(
            client, estimate_id=estimate_id, object_id=object_id,
            status="review_required", progress_percent=100,
            progress_label="object_facts_review_required",
        )
        return {"object_id": object_id, "status": "review_required", "reason_codes": [
            str(item.get("code")) for item in facts.get("review_items") or []
            if item.get("severity") == "blocking"
        ]}

    settings = dict(shared["settings"])
    overhead_monthly = dict(shared["overhead_monthly"])
    vat_percent = _number(settings.get("vat_percent"), 18)
    pricing_facts = {**facts, "estimate_id": estimate_id}
    material_rows, material_costs = _material_rows_and_costs(
        facts=pricing_facts, catalogs=shared["catalogs"], vat_percent=vat_percent
    )
    purchased_rows, purchased_costs = _purchased_component_rows_and_costs(pricing_facts)
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id, status="running",
        progress_percent=70, progress_label="materials_resolved",
    )
    labor_rows, labor_costs, labor_hours, labor_total = _labor_rows_and_costs(
        client=client, facts=pricing_facts, settings=settings,
        employees=shared["employees"], production_context=shared["production_context"],
    )
    material_total = sum(_number(line.get("cost")) for line in material_rows)
    overhead_rows = _safe_db_lines(build_overhead_lines(
        estimate_id=estimate_id, object_id=object_id, company_id=str(facts["company_id"]),
        settings=settings, overhead_monthly=overhead_monthly,
        labor_hours_total=labor_hours,
        subtotal_before_overhead=material_total + labor_total,
    ))
    overhead_total = sum(_number(line.get("cost")) for line in overhead_rows)
    overhead_costs = [{
        "line_id": f"{object_id}_overhead_total", "section": "overhead",
        "status": "resolved" if overhead_rows else "review_required",
        "amount": overhead_total if overhead_rows else None, "currency": "ILS",
        "source_ref": "overhead-engine:company-profile",
        "reason_codes": [] if overhead_rows else ["overhead_review_required"],
    }]
    machinery_costs = []
    if facts.get("manufacturing_features"):
        machinery_costs.append({
            "line_id": f"{object_id}_machinery_overhead", "section": "machinery",
            "status": "resolved", "amount": 0, "currency": "ILS",
            "source_ref": "company-overhead:machinery", "reason_codes": [],
        })
    composition = compose_object_estimate(
        facts=_public_facts(facts),
        cost_lines=[*material_costs, *purchased_costs, *labor_costs, *machinery_costs, *overhead_costs],
        allowed_material_families=families,
    )
    replace_rfq_estimate_lines_for_object(
        client, estimate_id=estimate_id, object_id=object_id,
        lines=_safe_db_lines([*material_rows, *purchased_rows, *labor_rows, *overhead_rows]),
    )
    status = "completed" if composition["status"] == "complete" else "review_required"
    if status == "completed":
        self_cost = _number(composition["self_cost_unit"])
        vat = round(self_cost * vat_percent / 100, 2)
        update_rfq_object_estimate_totals(
            client, estimate_id=estimate_id, object_id=object_id,
            self_cost_ex_vat=self_cost, vat_amount=vat,
            self_cost_total=round(self_cost + vat, 2),
        )
    update_rfq_object_estimate_progress(
        client, estimate_id=estimate_id, object_id=object_id, status=status,
        progress_percent=100,
        progress_label="completed" if status == "completed" else "costing_review_required",
    )
    return composition
