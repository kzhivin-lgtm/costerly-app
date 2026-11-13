from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from math import isfinite
import re
from typing import Any

from db.repositories import (
    delete_rfq_estimate_material_purchase_overrides,
    fetch_company_overhead_settings,
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
    upsert_rfq_estimate_material_norm_overrides,
    upsert_rfq_estimate_material_purchase_override,
    upsert_rfq_estimate_material_purchase_overrides,
    upsert_rfq_estimate_lines,
    mark_rfq_estimate_material_plan_stale,
    reset_rfq_object_estimate_approvals,
    upsert_rfq_estimate_shell,
)
from db.supabase_client import get_supabase_client
from db.company_access import assert_estimate_owned, assert_run_owned
from state.company_auth import company_auth_enabled
from state.session import get_company_id
from models.estimation import ObjectEstimateSeed
from use_cases.material_normalization import canonical_material_display_name
from use_cases.price_source_taxonomy import source_family_for_catalog_family
from use_cases.retry import read_with_retry


_ASSUMPTION_MATERIAL_DISPLAY_NAMES = {
    "mdf_hdf": "MDF",
    "melamine_faced_particleboard": "LDSP",
    "particleboard": "Particleboard",
    "fibreboard_hardboard": "Hardboard",
    "timber_solid_wood_panel": "Solid wood panel",
    "paint_lacquer_stain": "Paint finish",
    "metal_round_bar_rod_wire": "Furniture leg",
    "purchased_fabricated_component": "Furniture leg",
}
_ASSUMPTION_ROLE_WORDS = frozenset({
    "cabinet", "carcass", "facade", "table", "seat", "worktop", "countertop",
    "drawer", "panel", "backing", "sheet", "leg",
})
_COATING_MATERIAL_FAMILIES = frozenset({
    "wood_coatings", "metal_coatings", "paint_lacquer_stain",
})
_MATERIAL_POLICY_SPECS = (
    ("consumables", "Consumables", "consumables_percent", "materials", 5.0),
    ("paint_consumables", "Paint consumables", "paint_consumables_percent", "coatings", 10.0),
    ("packaging", "Packaging", "packaging_percent", "materials", 1.0),
)


def _assert_screen_estimate_access(
    client: Any, estimate_id: str, *, company_id: str | None = None,
) -> None:
    if company_auth_enabled():
        assert_estimate_owned(client, estimate_id, company_id or get_company_id())


def _material_plan_status(row: Any) -> str:
    if not isinstance(row, dict):
        return "pending"
    return str(row.get("plan_status") or (row.get("plan_payload") or {}).get("status") or "pending")


def _invalidate_and_queue_material_plan(
    client: Any,
    *,
    estimate_id: str,
    company_id: str,
    run_id: str,
    reason_code: str,
    previous_plan: dict[str, Any] | None = None,
) -> Future:
    """Invalidate every object approval, then queue one estimate-wide rebuild."""
    mark_rfq_estimate_material_plan_stale(
        client,
        estimate_id=estimate_id,
        company_id=company_id,
        reason_code=reason_code,
        **({"previous_plan": previous_plan} if previous_plan is not None else {}),
    )
    reset_rfq_object_estimate_approvals(client, estimate_id=estimate_id)
    # Local import avoids the existing runtime -> estimation dependency cycle.
    from use_cases.estimation_runtime import queue_material_plan_recalculation

    return queue_material_plan_recalculation(
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


_FRONT_PART_ROLES = {"facade", "door_front", "drawer_front", "lift_up_front", "hinged_facade", "lift_up_facade"}
_VISIBLE_PARTS = (
    ("LED", {"led_strip_run"}),
    ("Mirror", {"mirror", "mirror_glass"}),
    ("Glass boxes", {"glass_box", "glass_box_bottom", "glass_box_long_wall", "glass_box_end_wall"}),
)


def _object_visible_materials(plan: dict[str, Any], checked: dict[str, Any], object_id: str) -> str:
    """Summarize one facade material and the visible features of this object."""
    roles = {part.get("component_role") for part in checked.get("parts", ())}
    front_area: dict[str, float] = {}
    for line in plan.get("lines") or ():
        allocations = [a for a in line.get("allocations") or () if a.get("object_id") == object_id]
        if not allocations:
            continue
        family, *keys = str(line.get("selection_key") or "").split("|")
        attrs = dict(key.split("=", 1) for key in keys if "=" in key)
        if family == "mirror":
            roles.add("mirror")
        if family == "hardware_electrical_component" and str(line.get("display_name") or "").lower().startswith("led strip"):
            roles.add("led_strip_run")
        for allocation in allocations:
            parts = str(allocation.get("demand_id") or "").removesuffix(":assumption").rsplit(":", 2)
            if len(parts) < 3:
                continue
            role = parts[-2]
            roles.add(role)
            if role in _FRONT_PART_ROLES and family and not family.startswith("assumption:"):
                entity = _ASSUMPTION_MATERIAL_DISPLAY_NAMES.get(family) or source_family_for_catalog_family(family)
                if family == "mdf_hdf" and attrs.get("board_type") in {"mdf", "hdf"}:
                    entity = attrs["board_type"]
                label = canonical_material_display_name(entity, {"thickness_mm": attrs.get("thickness")})
                front_area[label] = front_area.get(label, 0) + _number(allocation.get("area_mm2"), 0)
    labels = []
    if front_area:
        labels.append(f"{max(front_area, key=front_area.__getitem__)} fronts")
    elif roles & _FRONT_PART_ROLES:
        labels.append("Fronts")
    labels.extend(label for label, component_roles in _VISIBLE_PARTS if roles & component_roles)
    return " · ".join(labels)


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
    checked_objects = material_plan.get("parts_check") or {}
    rows = []
    for _, item in objects_df.iterrows():
        row = item.to_dict()
        object_id = str(row.get("object_id") or "")
        quantity = _number(row.get("quantity"), 1)
        checked = checked_objects.get(object_id) or {}
        visible_materials = _object_visible_materials(material_plan, checked, object_id)
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
                "materials": visible_materials,
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
                "details_available": bool(checked or visible_materials or
                                          _material_rows_from_plan(material_plan, object_id=object_id)),
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


def load_object_detail_data(
    *, estimate_id: str, object_id: str, company_id: str | None = None,
) -> dict[str, Any]:
    """Load one object's persisted estimation lines for Object Detail."""
    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id, company_id=company_id)

    # These three projections are independent.  Object Detail used to make
    # them serially, so first Review paid their combined network latency.
    # They are read-only and use the same request-scoped client already shared
    # safely with the estimation runtime.
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="object-detail-read") as executor:
        objects_future = executor.submit(fetch_rfq_object_estimates, client, estimate_id)
        lines_future = executor.submit(
            fetch_rfq_estimate_lines_for_object,
            client,
            estimate_id=estimate_id,
            object_id=object_id,
        )
        material_plan_future = executor.submit(
            fetch_rfq_estimate_material_plan, client, estimate_id,
        )
        objects_df = objects_future.result()
        lines_df = lines_future.result()
        try:
            material_plan_df = material_plan_future.result()
        except Exception:
            material_plan_df = None
    material_plan_row = (
        material_plan_df.iloc[0].to_dict()
        if material_plan_df is not None and not material_plan_df.empty
        else None
    )
    material_plan = dict((material_plan_row or {}).get("plan_payload") or {})
    plan_status = _material_plan_status(material_plan_row)

    matching = objects_df[objects_df["object_id"] == object_id]
    if matching.empty:
        raise RuntimeError(f"Object estimate not found: {estimate_id}/{object_id}")

    object_row = matching.iloc[0].to_dict()
    canonical_quantity = _number(object_row.get("quantity"), 1)
    checked = (material_plan.get("parts_check") or {}).get(object_id) or {}
    settings = _first_row(fetch_company_overhead_settings(client, str(object_row.get("company_id"))))
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
                    "price_source": (
                        raw_agent_json.get("price_source")
                        if isinstance(raw_agent_json, dict) else None
                    ),
                    "material_plan_allocation": (
                        raw_agent_json.get("material_plan_allocation")
                        if isinstance(raw_agent_json, dict) else None
                    ),
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

    plan_material_rows = _material_rows_from_plan(material_plan, object_id=object_id)
    if plan_material_rows:
        material_rows = plan_material_rows + _material_policy_rows_from_lines(lines_df)
    if checked:
        missing = set(checked.get("unpriced_requirements") or ())
        material_rows = [*plan_material_rows, *[
            {"item": material["source_name"], "required_material_value": material["quantity"],
             "required_material_unit": {"m2": "m²"}.get(material["unit"], material["unit"]), "total": None}
            for material in checked["materials"] if material["requirement_id"] in missing
        ], *_material_policy_rows_from_lines(lines_df)]

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

    return {
        "object_key": object_id,
        "run_id": str(object_row.get("run_id") or ""),
        "estimate_id": estimate_id,
        "name": object_row.get("object_name"),
        "quantity": canonical_quantity,
        "approved": bool(object_row.get("approved")),
        "material_plan_ready": plan_status == "planned",
        "material_plan_status": plan_status,
        "confidence": "—",
        "preview_label": "Object preview",
        "preview_url": _estimation_preview_url(
            client,
            str(checked.get("primary_preview_ref") or ""),
            company_id=str(object_row.get("company_id") or ""),
        ),
        "elements": _element_rows_from_bom(checked),
        "sections": [
            {
                "key": "material",
                "title": "Materials",
                "metrics": [],
                "columns": ["Material", "Required material", "Purchase unit", "Unit price", "Purchase quantity", "Total"],
                "rows": sorted(material_rows, key=_material_display_order),
            },
        ],
        "self_cost": {
            "title": f"{object_row.get('object_name') or 'Object'} self cost (SC)",
            "vat_percent": vat_percent,
            "excl_vat": object_row.get("self_cost_ex_vat"),
            "vat": object_row.get("vat_amount"),
            "total": object_row.get("self_cost_total"),
        },
    }


def _material_rows_from_plan(plan_snapshot: dict[str, Any], *, object_id: str) -> list[dict[str, Any]]:
    """Project nesting is internal; render the selected material and physical demand."""
    assumption_by_requirement = {
        str(row.get("material_requirement_id") or ""): row
        for row in plan_snapshot.get("assumption_fallbacks") or []
        if isinstance(row, dict) and str(row.get("object_id") or "") in {"", object_id}
    }
    allocated_costs = {str(row["material_requirement_id"]): _number(row.get("cost_ex_vat"), 0)
                       for row in plan_snapshot.get("object_material_costs", ()) if row.get("object_id") == object_id}
    rows = []
    for line in plan_snapshot.get("lines") or []:
        if not isinstance(line, dict):
            continue
        allocations = [
            allocation for allocation in line.get("allocations") or []
            if isinstance(allocation, dict) and str(allocation.get("object_id") or "") == object_id
        ]
        if not allocations:
            continue
        purchase_kind = str(line.get("purchase_kind") or "")
        required_value, required_unit = _required_material_volume(allocations, purchase_kind=purchase_kind)
        if required_value <= 0:
            continue
        authority = {"company": "C", "israel_reference": "I"}.get(
            str(line.get("authority") or ""), "A"
        )
        requirement_ids = {
            str(allocation.get("material_requirement_id") or "") for allocation in allocations
        }
        fallback = (
            assumption_by_requirement[next(iter(requirement_ids))]
            if authority == "A" and len(requirement_ids) == 1
            and next(iter(requirement_ids), "") in assumption_by_requirement else None
        )
        selection_key = str(line.get("selection_key") or "")
        family = (fallback or {}).get("material_family") or selection_key.split("|", 1)[0]
        project_required, _ = _required_material_volume(line["allocations"], purchase_kind=purchase_kind)
        dimensions = line.get("purchasable_dimensions") or {}
        length = _number(dimensions.get("length_mm"), 0)
        width = _number(dimensions.get("width_mm"), 0)
        rows.append({
            "item": (
                _assumption_material_display_name(fallback)
                if isinstance(fallback, dict) else str(line.get("display_name") or "Material")
            ),
            "price_source": authority,
            "required_material_value": required_value, "required_material_unit": required_unit,
            "required_material_line_id": (
                f"__material_requirement__:{next(iter(requirement_ids))}" if len(requirement_ids) == 1
                else f"__material_selection__:{selection_key}" if selection_key else ""
            ),
            "purchase_unit": _purchase_unit_display(line),
            "purchase_quantity_value": _number(line.get("purchase_quantity"), 0),
            "purchase_quantity_unit": _purchase_unit_label(purchase_kind),
            "purchase_quantity_line_id": f"__material_purchase__:{line.get('selection_key')}",
            "purchase_kind": purchase_kind,
            "purchase_is_manual": bool(line.get("purchase_quantity_is_manual")),
            "project_required": project_required,
            "purchase_unit_cost": line.get("price_per_purchase_unit"),
            "stock_coverage": (
                length * width / 1_000_000 / 1.10 if purchase_kind == "sheet" else
                length / 1_000 if purchase_kind == "linear_stock" else
                _number(line.get("package_quantity"), 1) or 1
            ),
            "is_coating": family in _COATING_MATERIAL_FAMILIES,
            **({"material_family": family} if family else {}),
            "total": (round(sum(allocated_costs.get(req, 0) for req in requirement_ids), 2)
                      if plan_snapshot.get("parts_check") else _number(line.get("total_cost"), 0)),
        })
    return rows


def _material_display_order(row: dict[str, Any]) -> int:
    """Order Object Detail rows by what they represent, retaining order within each group."""
    if row.get("locked"):
        return 5
    name = str(row.get("item") or "").casefold()
    family = str(row.get("material_family") or "")
    unit = str(row.get("purchase_unit") or row.get("unit") or "").casefold()
    if re.search(r"\bled\b|светодиод", name):
        return 4
    if family in {"glass", "mirror"} or re.search(r"\b(?:glass|mirror)\b|стекло|зеркал", name):
        return 1
    if unit.startswith("sheet") or row.get("required_material_unit") == "m²" or unit in {"m²", "m2"}:
        return 0
    if family.startswith("hardware_") or unit in {"piece", "pcs", "set", "pair"}:
        return 3
    return 2


def _material_policy_rows_from_lines(lines_df: Any) -> list[dict[str, Any]]:
    """Render locked Profile formulas after the physical Material Plan rows."""
    rows = []
    for _, item in lines_df.iterrows():
        line = item.to_dict()
        if str(line.get("section") or "") != "material" or str(line.get("source") or "") != "pricing_policy":
            continue
        raw = line.get("raw_agent_json") or {}
        if not isinstance(raw, dict):
            raw = {}
        rows.append({
            "item": str(line.get("item_name") or "Formula"),
            "locked": True,
            "policy_percent": _number(raw.get("percent"), 0),
            "policy_basis": str(raw.get("basis") or "materials"),
            "total": _number(line.get("cost"), 0),
        })
    return rows


def _assumption_material_display_name(fallback: dict[str, Any]) -> str:
    source_name = " ".join(str(fallback.get("source_name") or "").split()).strip()
    words = {word.strip(" ,./-_").casefold() for word in source_name.split()}
    family = str(fallback.get("material_family") or "")
    name = (
        source_name if source_name and not (words & _ASSUMPTION_ROLE_WORDS)
        else _ASSUMPTION_MATERIAL_DISPLAY_NAMES.get(family, "Material")
    )
    specification = fallback.get("specification") or {}
    thickness = _number(specification.get("thickness_mm"), 0) if isinstance(specification, dict) else 0
    return f"{name} {_format_number(thickness)} mm" if thickness > 0 else name


def _required_material_volume(
    allocations: list[dict[str, Any]], *, purchase_kind: str,
) -> tuple[float, str]:
    if purchase_kind == "sheet":
        area_mm2 = sum(
            _number(allocation.get("area_mm2"), 0)
            or (
                _number(allocation.get("length_mm"), 0)
                * _number(allocation.get("width_mm"), 0)
                * _number(allocation.get("quantity"), 1)
            )
            for allocation in allocations
        )
        return area_mm2 / 1_000_000, "m²"
    if purchase_kind in {"linear_stock", "linear_cut"}:
        length_mm = sum(
            _number(allocation.get("length_mm"), 0) * _number(allocation.get("quantity"), 1)
            for allocation in allocations
        )
        return length_mm / 1_000, "m"
    if purchase_kind == "volume_direct":
        volume_mm3 = sum(_number(allocation.get("volume_mm3"), 0) for allocation in allocations)
        return volume_mm3 / 1_000_000_000, "m³"
    return sum(_number(allocation.get("quantity"), 0) for allocation in allocations), "piece"


def _material_policy_base_totals(lines_df: Any) -> tuple[float, float]:
    """Return the Profile formula bases, excluding the formula rows themselves."""
    primary_material_total = 0.0
    coating_material_total = 0.0
    for _, item in lines_df.iterrows():
        row = item.to_dict()
        if str(row.get("section") or "") != "material" or str(row.get("source") or "") == "pricing_policy":
            continue
        cost = _number(row.get("cost"), 0)
        primary_material_total += cost
        raw = row.get("raw_agent_json") or {}
        facts = raw.get("facts") if isinstance(raw, dict) else {}
        family = str((facts or {}).get("family") or "") if isinstance(facts, dict) else ""
        if family in _COATING_MATERIAL_FAMILIES:
            coating_material_total += cost
    return round(primary_material_total, 2), round(coating_material_total, 2)


def _material_policy_lines(
    *, estimate_id: str, object_id: str, company_id: str, settings: dict[str, Any],
    primary_material_total: float, coating_material_total: float,
) -> list[dict[str, Any]]:
    """Build the three Profile-owned, non-editable material allowances."""
    lines = []
    for offset, (policy_key, label, setting_key, basis, default_percent) in enumerate(_MATERIAL_POLICY_SPECS):
        percent = _number(settings.get(setting_key), default_percent)
        base = coating_material_total if basis == "coatings" else primary_material_total
        amount = round(max(base, 0) * percent / 100, 2)
        basis_label = "coating material cost" if basis == "coatings" else "primary material cost"
        lines.append({
            "estimate_id": estimate_id,
            "object_id": object_id,
            "company_id": company_id,
            "line_id": f"{object_id}_material_policy_{policy_key}",
            "section": "material",
            "group_name": "Materials",
            "item_name": label,
            "catalog_match_query": None,
            "unit": "formula",
            "unit_cost": None,
            "quantity": None,
            "cost": amount,
            "source": "pricing_policy",
            "sort_order": 900 + offset * 10,
            "needs_price": False,
            "needs_review": False,
            "confidence": 100,
            "quantity_basis": "formula",
            "notes": f"{_format_number(percent)}% of {basis_label}",
            "raw_agent_json": {
                "policy": f"{policy_key}_percent_of_{basis}",
                "percent": percent,
                "basis": basis,
                "base_material_cost": base,
                "locked": True,
            },
        })
    return lines


def _purchase_unit_display(line: dict[str, Any]) -> str:
    purchase_kind = str(line.get("purchase_kind") or "")
    dimensions = line.get("purchasable_dimensions") or {}
    if purchase_kind == "sheet":
        length = _number(dimensions.get("length_mm"), 0) if isinstance(dimensions, dict) else 0
        width = _number(dimensions.get("width_mm"), 0) if isinstance(dimensions, dict) else 0
        if length > 0 and width > 0:
            return f"sheet {_format_number(length)} × {_format_number(width)} mm"
        return "sheet"
    if purchase_kind == "linear_stock":
        length = _number(dimensions.get("length_mm"), 0) if isinstance(dimensions, dict) else 0
        return f"stock {_format_number(length)} mm" if length > 0 else "stock length"
    return "piece" if purchase_kind in {"piece", "direct"} else _purchase_unit_label(purchase_kind)


def _element_rows_from_bom(facts_payload: dict[str, Any]) -> list[dict[str, Any]]:
    labels = {
        "carcass_side": "Side panel", "carcass_top_bottom": "Top / bottom panel",
        "carcass_back": "Back panel", "facade": "Front panel", "drawer_front": "Drawer front",
        "drawer_bottom": "Drawer bottom", "drawer_side": "Drawer side", "drawer_back": "Drawer back",
        "top": "Top panel", "leg": "Leg", "led_strip_run": "LED strip run",
    }
    axes = ("length", "width", "thickness")
    grouped: dict[tuple[object, ...], dict[str, Any]] = {}
    for index, part in enumerate(facts_payload.get("parts") or []):
        if not isinstance(part, dict):
            continue
        role = str(part.get("component_role") or "")
        label = labels.get(role, role.replace("_", " ").capitalize() or "Element")
        dimensions = tuple(_number(part.get(f"{axis}_mm"), 0) or None for axis in axes)
        count = _number(part.get("quantity"), 0)
        # A missing panel dimension is not evidence of an identical cut.
        length, width, thickness = dimensions
        incomplete = (
            length is None and (width is not None or thickness is not None)
            or width is None and thickness is not None
            or width is not None and thickness is None and "thickness_mm" in part
        )
        key = (role, *dimensions, index if incomplete or count <= 0 else None)
        if key not in grouped:
            last = max((i for i, value in enumerate(dimensions) if value is not None), default=-1)
            size = " × ".join(_format_number(value) if value is not None else "—" for value in dimensions[:last + 1])
            grouped[key] = {"label": label, "quantity": 0, "size": f"{size} mm" if size else "",
                            "estimated": False}
        row = grouped[key]
        row["estimated"] |= bool(part.get("estimated_dimensions"))
        row["quantity"] = row["quantity"] + count if count > 0 else None
    for row in grouped.values():
        if row.pop("estimated") and row["size"]:
            row["size"] = f"≈ {row['size']}"
    return list(grouped.values())


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
    recalculate: bool = False,
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


def _purchase_unit_label(purchase_kind: object) -> str:
    return {
        "sheet": "sheet",
        "linear_stock": "stock length",
        "linear_cut": "cut length",
        "piece": "piece",
        "direct": "purchase unit",
        "volume_direct": "m³",
    }.get(str(purchase_kind or ""), "purchase unit")


def _project_material_purchase_rows(plan_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Return actual estimate-wide purchases, never per-object consumption norms."""
    result = []
    for line in plan_snapshot.get("lines") or []:
        if not isinstance(line, dict):
            continue
        quantity = _number(line.get("purchase_quantity"), 0)
        if quantity <= 0:
            continue
        result.append({
            "item": str(line.get("display_name") or "Material"),
            "purchase": f"{_format_number(quantity)} {_purchase_unit_label(line.get('purchase_kind'))}",
            "unit_price": _number(line.get("price_per_purchase_unit"), 0),
            "total_cost": _number(line.get("total_cost"), 0),
            "price_source": {"company": "C", "israel_reference": "I"}.get(
                str(line.get("authority") or ""), "A"
            ),
        })
    return result


def _material_norms_from_plan(
    plan_snapshot: dict[str, Any], *, selection_key: str | None = None,
) -> dict[tuple[str, str], tuple[str, float]]:
    """Return internal allocation weights, never rendered purchase quantities."""
    result: dict[tuple[str, str], tuple[str, float]] = {}
    for line in plan_snapshot.get("lines") or []:
        if not isinstance(line, dict):
            continue
        if selection_key is not None and line.get("selection_key") != selection_key:
            continue
        purchase_kind = str(line.get("purchase_kind") or "")
        if purchase_kind == "sheet":
            unit, divisor, dimension = "m²", 1_000_000.0, "area"
        elif purchase_kind in {"linear_stock", "linear_cut"}:
            unit, divisor, dimension = "m", 1_000.0, "length"
        elif purchase_kind in {"piece", "direct"}:
            unit, divisor, dimension = "piece", 1.0, "quantity"
        elif purchase_kind == "volume_direct":
            unit, divisor, dimension = "m³", 1_000_000_000.0, "volume"
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
            elif dimension == "volume":
                amount = _number(allocation.get("volume_mm3"), 0) / divisor
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


def save_object_detail_material_edits(
    *, estimate_id: str, object_id: str, edits: list[dict[str, Any]],
) -> Future:
    """Validate and save a material draft, then queue one pricing update."""
    if not edits or len(edits) > 500:
        raise ValueError("Select between 1 and 500 material changes.")
    client = get_supabase_client()
    _assert_screen_estimate_access(client, estimate_id)
    obj = _object_material_context(client, estimate_id=estimate_id, object_id=object_id)
    company_id = str(obj["company_id"])
    plan = _first_row(fetch_rfq_estimate_material_plan(client, estimate_id)).get("plan_payload") or {}
    owned = {
        line["selection_key"]: line for line in plan.get("lines", ())
        if line.get("selection_key") and any(a.get("object_id") == object_id for a in line.get("allocations", ()))
    }
    purchases, norm_rows = {}, {}
    auto_purchase = set()
    current_quantity = _number(obj.get("quantity"), 1) or 1
    object_quantity = None
    for edit in edits:
        if isinstance(edit, dict) and edit.get("field") == "object_quantity" and edit.get("lineId") == "__object__":
            object_quantity = _number(edit.get("value"), 0)
            if not isfinite(object_quantity) or not 0 < object_quantity <= 1_000_000 or object_quantity != round(object_quantity, 3):
                raise ValueError("Enter a positive object quantity with up to three decimal places.")
    if object_quantity == current_quantity:
        object_quantity = None
    if object_quantity is not None:
        current_quantity = object_quantity
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError("Invalid material edit.")
        field = edit.get("field")
        line_id = str(edit.get("lineId") or "")
        if field == "object_quantity" and line_id == "__object__":
            continue
        if not plan.get("parts_check_source"):
            raise ValueError("A saved material plan is required to edit materials.")
        amount = _number(edit.get("value"), 0)
        if not isfinite(amount) or amount < 0.0001 or amount >= 10_000_000_000 or amount != round(amount, 4):
            raise ValueError("Enter a positive quantity with up to four decimal places.")
        if field == "purchase_quantity" and line_id.startswith("__material_purchase__:"):
            key = line_id.removeprefix("__material_purchase__:")
            if key not in owned:
                raise ValueError("This purchase line is no longer available.")
            purchases[key] = amount
            continue
        if field != "required_material":
            raise ValueError("This field cannot be recalculated.")
        if line_id.startswith("__material_selection__:"):
            key = line_id.removeprefix("__material_selection__:")
            norms = _material_norms_from_plan(plan, selection_key=key) if key in owned else {}
            affected_keys = {key} if key in owned else set()
        elif line_id.startswith("__material_requirement__:"):
            requirement_id = line_id.removeprefix("__material_requirement__:")
            norms = {key: val for key, val in _material_norms_from_plan(plan).items() if key[1] == requirement_id}
            affected_keys = {key for key, line in owned.items() if any(
                allocation.get("object_id") == object_id and allocation.get("material_requirement_id") == requirement_id
                for allocation in line["allocations"]
            )}
        else:
            norms = {}
            affected_keys = set()
        requirements = {key[1]: val for key, val in norms.items() if key[0] == object_id}
        if not requirements or len({unit for unit, _ in requirements.values()}) != 1:
            raise ValueError("This material row has no editable requirement.")
        total = sum(quantity for _, quantity in requirements.values())
        if object_quantity is None and abs(amount - total) < 1e-8:
            continue
        auto_purchase.update(affected_keys)
        per_item = amount / current_quantity
        ordered = sorted(requirements.items(), key=lambda item: item[1][1])
        shares = [(key, unit, round(per_item * quantity / total, 4))
                  for key, (unit, quantity) in ordered[:-1]]
        last_key, (last_unit, _) = ordered[-1]
        shares.append((last_key, last_unit, round(per_item - sum(q for _, _, q in shares), 4)))
        if any(quantity <= 0 for _, _, quantity in shares):
            raise ValueError("The required quantity is too small for this material row.")
        for requirement_id, unit, quantity in shares:
            norm_rows[requirement_id] = {"estimate_id": estimate_id, "object_id": object_id,
                "material_requirement_id": requirement_id, "company_id": company_id,
                "quantity_per_item": quantity, "unit": unit, "source_line_id": None}

    if not norm_rows and not purchases and object_quantity is None:
        receipt = Future()
        receipt.set_result(plan)
        return receipt
    if object_quantity is not None:
        update_object_quantity(estimate_id=estimate_id, run_id=str(obj["run_id"]), object_id=object_id,
                               quantity=object_quantity, queue_recalculation=False)
    if purchases:
        upsert_rfq_estimate_material_purchase_overrides(
            client, estimate_id=estimate_id, company_id=company_id, quantities=purchases,
        )
    if norm_rows:
        upsert_rfq_estimate_material_norm_overrides(client, rows=list(norm_rows.values()))
        delete_rfq_estimate_material_purchase_overrides(
            client, estimate_id=estimate_id, company_id=company_id, selection_keys=auto_purchase - purchases.keys(),
        )
    if norm_rows or object_quantity is not None:
        # A quantity change can affect every material. A pure norm edit
        # only touches stock lines whose complete allocation is saved.
        edited_requirements = set(norm_rows)
        norm_keys = set()
        owners_by_requirement: dict[str, set[str]] = {}
        for key, line in owned.items():
            for allocation in line["allocations"]:
                requirement = allocation.get("material_requirement_id")
                if allocation.get("object_id") == object_id and requirement in edited_requirements:
                    owners_by_requirement.setdefault(requirement, set()).add(key)
                    norm_keys.add(key)
        scoped_norm = (object_quantity is None and set(owners_by_requirement) == edited_requirements
                       and all(len(keys) == 1 for keys in owners_by_requirement.values())
                       and not (purchases.keys() - norm_keys))
        if scoped_norm:
            reset_rfq_object_estimate_approvals(client, estimate_id=estimate_id)
            from use_cases.estimation_runtime import queue_material_plan_recalculation

            return queue_material_plan_recalculation(
                estimate_id=estimate_id, company_id=company_id, run_id=str(obj["run_id"]),
                norm_keys=frozenset(norm_keys),
            )
        return _invalidate_and_queue_material_plan(
            client, estimate_id=estimate_id, company_id=company_id, run_id=str(obj["run_id"]),
            reason_code="material_norm_changed" if norm_rows else "object_quantity_changed", previous_plan=plan,
        )
    reset_rfq_object_estimate_approvals(client, estimate_id=estimate_id)
    from use_cases.estimation_runtime import queue_material_plan_recalculation

    return queue_material_plan_recalculation(estimate_id=estimate_id, company_id=company_id,
                                              run_id=str(obj["run_id"]), purchase_only=True)


def apply_material_plan_allocations(
    client: Any,
    *,
    estimate_id: str,
    plan_snapshot: dict[str, Any],
    changed_requirements: set[tuple[str, str]] | None = None,
) -> None:
    """Project rounded purchase costs back into the owning Object Detail rows."""
    # A partial plan is still authoritative for the requirements it actually
    # resolved. Do not hide priced Company/Israel materials merely because a
    # different requirement remains review-required.
    if str(plan_snapshot.get("status") or "") not in {"planned", "needs_review"}:
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
    resolved_authorities = {
        (str(allocation.get("object_id") or ""), str(allocation.get("material_requirement_id") or "")):
        str(line.get("authority") or "")
        for line in plan_snapshot.get("lines") or []
        if isinstance(line, dict)
        for allocation in line.get("allocations") or []
        if isinstance(allocation, dict)
    }
    purchase_context = {
        (str(allocation.get("object_id") or ""), str(allocation.get("material_requirement_id") or "")): {
            "purchase_kind": str(line.get("purchase_kind") or ""),
            "purchase_quantity": _number(line.get("purchase_quantity"), 0),
            "purchase_unit": _purchase_unit_label(line.get("purchase_kind")),
            "price_per_purchase_unit": _number(line.get("price_per_purchase_unit"), 0),
            "purchase_total_cost": _number(line.get("total_cost"), 0),
        }
        for line in plan_snapshot.get("lines") or []
        if isinstance(line, dict)
        for allocation in line.get("allocations") or []
        if isinstance(allocation, dict)
    }
    assumption_fallbacks = {
        (str(row.get("object_id") or ""), str(row.get("material_requirement_id") or "")): row
        for row in plan_snapshot.get("assumption_fallbacks") or []
        if isinstance(row, dict)
    }
    checked_objects = plan_snapshot.get("parts_check") or {}
    if not allocation_costs and not assumption_fallbacks and not checked_objects:
        return
    lines_df = fetch_rfq_estimate_lines(client, estimate_id)
    affected_object_ids: set[str] = set()
    for _, item in lines_df.iterrows():
        line = item.to_dict()
        if str(line.get("section") or "") != "material":
            continue
        object_id = str(line.get("object_id") or "")
        requirement_id = _material_requirement_id(line)
        if changed_requirements is not None and (object_id, requirement_id) not in changed_requirements:
            continue
        assumption = assumption_fallbacks.get((object_id, requirement_id))
        allocated_cost = allocation_costs.get((object_id, requirement_id))
        norm = material_norms.get((object_id, requirement_id))
        if allocated_cost is None or norm is None:
            continue
        _unit, total_required_quantity = norm
        if total_required_quantity <= 0:
            continue
        context = purchase_context.get((object_id, requirement_id))
        if context is None:
            continue
        raw_agent_json = {
            **(line.get("raw_agent_json") if isinstance(line.get("raw_agent_json"), dict) else {}),
            "material_plan_allocation": {**context, "allocated_cost": round(allocated_cost, 2)},
        }
        if assumption is not None:
            rationale = (assumption.get("assumption_price") or {}).get("rationale") or []
            update_rfq_estimate_line(
                client,
                estimate_id=estimate_id,
                line_id=str(line.get("line_id") or ""),
                values={
                    "item_name": str(assumption["source_name"]),
                    "unit": "project allocation",
                    "quantity": None,
                    "unit_cost": None,
                    "cost": round(allocated_cost, 2),
                    "needs_price": False,
                    "needs_review": False,
                    "notes": " ".join(str(item) for item in rationale),
                    "raw_agent_json": {**raw_agent_json, "price_source": "A"},
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            affected_object_ids.add(object_id)
            continue
        update_rfq_estimate_line(
            client,
            estimate_id=estimate_id,
            line_id=str(line.get("line_id") or ""),
            values={
                "unit_cost": None,
                "unit": "project allocation",
                "quantity": None,
                "cost": round(allocated_cost, 2),
                "needs_price": False,
                "notes": "Allocated from the estimate-wide Material Plan",
                "raw_agent_json": {
                    **raw_agent_json,
                    "price_source": {"company": "C", "israel_reference": "I"}.get(
                        resolved_authorities.get((object_id, requirement_id)), "A"
                    ),
                },
                "updated_at": datetime.now(UTC).isoformat(),
                **({"item_name": resolved_names[(object_id, requirement_id)]}
                   if resolved_names.get((object_id, requirement_id)) else {}),
            },
        )
        affected_object_ids.add(object_id)
    target_objects = affected_object_ids | checked_objects.keys() if changed_requirements is None else affected_object_ids
    for object_id in target_objects:
        checked = checked_objects.get(object_id) or {}
        review_required = bool(checked.get("issues") or checked.get("has_estimated_costs")
                               or checked.get("unpriced_requirements") or checked.get("has_unresolved_demands"))
        if checked and object_id not in affected_object_ids:
            update_rfq_object_estimate_totals(
                client, estimate_id=estimate_id, object_id=object_id,
                self_cost_ex_vat=None, vat_amount=None, self_cost_total=None,
            )
            update_rfq_object_estimate_progress(
                client, estimate_id=estimate_id, object_id=object_id,
                status="review_required", progress_percent=100, progress_label="material_plan_needs_review",
            )
            continue
        object_rows = fetch_rfq_estimate_lines_for_object(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
        )
        object_context = _object_material_context(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
        )
        settings = _first_row(fetch_company_overhead_settings(
            client,
            str(object_context.get("company_id") or ""),
        ))
        primary_material_total, coating_material_total = _material_policy_base_totals(object_rows)
        policy_lines = _material_policy_lines(
            estimate_id=estimate_id,
            object_id=object_id,
            company_id=str(object_context.get("company_id") or ""),
            settings=settings,
            primary_material_total=primary_material_total,
            coating_material_total=coating_material_total,
        )
        upsert_rfq_estimate_lines(client, lines=policy_lines)
        _recalculate_object_estimate_totals(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            **({"object_row": object_context, "settings": settings, "lines_df": object_rows,
                "published_policy_lines": policy_lines} if changed_requirements is not None else {}),
        )
        update_rfq_object_estimate_progress(
            client,
            estimate_id=estimate_id,
            object_id=object_id,
            status="review_required" if review_required else "completed",
            progress_percent=100,
            progress_label="material_plan_needs_review" if review_required else "materials_costed",
        )


def update_object_quantity(
    *,
    estimate_id: str,
    run_id: str,
    object_id: str,
    quantity: float,
    queue_recalculation: bool = True,
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
    if company_id and queue_recalculation:
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
    required_material_edits: dict[str, Any] = {}
    purchase_quantity_edits: dict[str, Any] = {}
    object_quantity: Any = None
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        line_id = str(edit.get("line_id") or "")
        field = str(edit.get("field") or "")
        if line_id == "__object__" and field == "object_quantity":
            object_quantity = edit.get("value")
            continue
        if line_id.startswith("__material_requirement__:") and field == "required_material":
            required_material_edits[line_id.removeprefix("__material_requirement__:")] = edit.get("value"); continue
        if line_id.startswith("__material_purchase__:") and field == "purchase_quantity":
            purchase_quantity_edits[line_id.removeprefix("__material_purchase__:")] = edit.get("value"); continue
        if not line_id or field not in allowed_fields:
            continue
        edits_by_line.setdefault(line_id, {})[field] = edit.get("value")

    if not edits_by_line and not required_material_edits and not purchase_quantity_edits and object_quantity is None:
        return True

    if object_quantity is not None:
        update_object_quantity(
            estimate_id=estimate_id,
            run_id=str(run_id or ""),
            object_id=object_id,
            quantity=_number_from_edit(object_quantity),
        )
    if not edits_by_line and not required_material_edits and not purchase_quantity_edits:
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

    if required_material_edits:
        current_plan = _first_row(fetch_rfq_estimate_material_plan(client, estimate_id))
        material_norms = _material_norms_from_plan(current_plan.get("plan_payload") if isinstance(current_plan.get("plan_payload"), dict) else {})
        source_line_ids = {_material_requirement_id(item.to_dict()): str(item.to_dict().get("line_id") or "") for _, item in lines_df.iterrows() if _material_requirement_id(item.to_dict())}
        for requirement_id, value in required_material_edits.items():
            current = material_norms.get((object_id, requirement_id))
            if current is None: raise ValueError("Material requirement cannot be edited without a current physical unit.")
            unit, _ = current; total_required = _number_from_edit(value)
            if total_required <= 0: raise ValueError("Required material must be greater than zero.")
            material_norm_overrides.append((requirement_id, total_required / current_object_quantity, unit, source_line_ids.get(requirement_id, "")))

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

    for selection_key, value in purchase_quantity_edits.items():
        purchase_quantity = _number_from_edit(value)
        if not selection_key or purchase_quantity <= 0: raise ValueError("Purchase quantity must be greater than zero.")
        upsert_rfq_estimate_material_purchase_override(client, estimate_id=estimate_id, selection_key=selection_key, company_id=str(object_row.get("company_id") or ""), purchase_quantity=purchase_quantity)

    material_input_changed = bool(material_norm_overrides) or bool(purchase_quantity_edits) or object_quantity is not None
    if material_input_changed:
        _invalidate_and_queue_material_plan(
            client,
            estimate_id=estimate_id,
            company_id=str(object_row.get("company_id") or ""),
            run_id=str(object_row.get("run_id") or run_id or ""),
            reason_code="material_norm_changed" if material_norm_overrides else "purchase_quantity_changed" if purchase_quantity_edits else "object_quantity_changed",
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
    object_row: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
    lines_df: Any = None,
    published_policy_lines: list[dict[str, Any]] | None = None,
) -> None:
    if object_row is None:
        objects_df = fetch_rfq_object_estimates(client, estimate_id)
        matching = objects_df[objects_df["object_id"] == object_id]
        if matching.empty:
            return
        object_row = matching.iloc[0].to_dict()
    if settings is None:
        settings = _first_row(fetch_company_overhead_settings(client, str(object_row.get("company_id"))))
    vat_percent = _number(settings.get("vat_percent"), 18)
    employer_load_percent = _number(settings.get("employer_load_percent"), 25)

    if lines_df is None:
        lines_df = fetch_rfq_estimate_lines_for_object(
            client, estimate_id=estimate_id, object_id=object_id,
        )
    if published_policy_lines is None:
        primary_material_total, coating_material_total = _material_policy_base_totals(lines_df)
        for _, item in lines_df.iterrows():
            row = item.to_dict()
            if row.get("section") != "material" or row.get("source") != "pricing_policy":
                continue
            raw_agent_json = row.get("raw_agent_json") or {}
            percent = _number(raw_agent_json.get("percent") if isinstance(raw_agent_json, dict) else None, 0)
            basis = raw_agent_json.get("basis") if isinstance(raw_agent_json, dict) else None
            base = coating_material_total if basis == "coatings" else primary_material_total
            amount = round(base * percent / 100, 2)
            update_rfq_estimate_line(
                client, estimate_id=estimate_id, line_id=str(row.get("line_id") or ""),
                values={"cost": amount, "updated_at": datetime.now(UTC).isoformat()},
            )
            lines_df.loc[lines_df["line_id"] == row.get("line_id"), "cost"] = amount
    material_total = sum(row["cost"] for row in published_policy_lines or ())
    labor_base_total = 0.0
    manufacturing_total = 0.0
    overhead_total = 0.0
    checked_material_plan = False
    for _, line in lines_df.iterrows():
        row = line.to_dict()
        section = str(row.get("section") or "")
        cost = _number(row.get("cost"), 0)
        if section == "material":
            if published_policy_lines is not None and row.get("source") == "pricing_policy":
                continue
            material_total += cost
            checked_material_plan |= row.get("source") == "parts_check"
        elif section == "labor":
            if row.get("source") == "manufacturing_engine":
                manufacturing_total += cost
            else:
                labor_base_total += cost
        elif section == "overhead":
            overhead_total += cost

    if checked_material_plan:
        material_total /= _number(object_row.get("quantity"), 1) or 1
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
