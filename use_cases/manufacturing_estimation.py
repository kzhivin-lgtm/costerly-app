from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping, Sequence

from use_cases.manufacturing_costing import (
    CncRouterInHouseInputs,
    CncRouterSubcontractorInputs,
    CostCalculation,
    SheetLaserInHouseInputs,
    SheetLaserSubcontractorInputs,
    ValueRange,
    calculate_cnc_router_in_house,
    calculate_cnc_router_subcontractor,
    calculate_sheet_laser_in_house,
    calculate_sheet_laser_subcontractor,
)
from use_cases.manufacturing_parameters import (
    ManufacturingParameterError,
    ParameterRequirement,
    ParameterScope,
    resolve_manufacturing_parameters,
)
from use_cases.manufacturing_routing import (
    SheetMetalWork,
    WoodPanelWork,
    route_sheet_metal_work,
    route_wood_panel_work,
)


ZERO = ValueRange.point(0)


class ManufacturingEstimationError(ValueError):
    pass


def _decimal(value: Any, default: str = "0") -> Decimal:
    if value is None or value == "":
        return Decimal(default)
    return Decimal(str(value))


def _point(value: Any, default: str = "0") -> ValueRange:
    return ValueRange.point(_decimal(value, default))


def _scale(value: ValueRange, multiplier: Any) -> ValueRange:
    factor = _decimal(multiplier)
    return ValueRange(value.low * factor, value.typical * factor, value.high * factor)


def _tri(value: Any) -> bool | None:
    if value == "yes" or value is True:
        return True
    if value == "no" or value is False:
        return False
    return None


def _availability(context: Mapping[str, Any], machine_code: str) -> bool | None:
    for machine in context.get("machines") or []:
        if machine.get("machine_code") != machine_code:
            continue
        status = machine.get("availability_status")
        if status == "in_house":
            return True
        if status == "not_in_house":
            return False
    return None


def _reserve_level(context: Mapping[str, Any], machine_code: str) -> int:
    for machine in context.get("machines") or []:
        if machine.get("machine_code") == machine_code:
            level = machine.get("estimate_level")
            if level in {1, 2, 3, 4, 5}:
                return int(level)
    return 3


def _machine_rate_override(
    context: Mapping[str, Any], machine_code: str
) -> ValueRange | None:
    for machine in context.get("machines") or []:
        if machine.get("machine_code") != machine_code:
            continue
        if machine.get("availability_status") != "in_house":
            continue
        if machine.get("pricing_method") != "hourly":
            continue
        pricing = machine.get("pricing") or {}
        rate = _decimal(pricing.get("rate"))
        if rate > 0:
            return ValueRange.point(rate)
    return None


def _range(
    rows: Sequence[Mapping[str, Any]],
    *,
    calculator: str,
    key: str,
    unit: str,
    currency: str | None = None,
    material_family: str | None = None,
    thickness_mm: Any = None,
    machine_class: str | None = None,
) -> tuple[ValueRange, tuple[str, ...]]:
    result = resolve_manufacturing_parameters(
        rows,
        calculator=calculator,  # type: ignore[arg-type]
        requirements=[ParameterRequirement(key, unit, currency)],
        scope=ParameterScope(
            material_family=material_family,
            thickness_mm=(None if thickness_mm is None else _decimal(thickness_mm)),
            machine_class=machine_class,
        ),
    )
    result.require_complete()
    return result.value_range(key), result.parameter_ids


def _row(
    *,
    estimate_id: str,
    object_id: str,
    company_id: str,
    index: int,
    calculation: CostCalculation,
    feature: Mapping[str, Any],
) -> dict[str, Any]:
    selected = calculation.selected_cost.quantize(Decimal("0.01"))
    return {
        "estimate_id": estimate_id,
        "object_id": object_id,
        "line_id": f"{object_id}_manufacturing_{index:04d}",
        "company_id": company_id,
        "section": "labor",
        "group_name": "CNC / Laser manufacturing",
        "item_name": calculation.calculator.replace("_", " ").title(),
        "role": "machine service",
        "hours": 1,
        "rate": float(selected),
        "cost": float(selected),
        "source": "manufacturing_engine",
        "sort_order": 8_000 + index,
        "needs_price": False,
        "needs_review": float(feature.get("confidence") or 0) < 70,
        "evidence_pages": feature.get("evidence_pages") or "",
        "confidence": feature.get("confidence"),
        "notes": feature.get("notes") or "",
        "raw_agent_json": {
            "schema_version": "manufacturing_estimate_line_v1",
            "feature": dict(feature),
            "calculator": calculation.calculator,
            "reserve_level": calculation.reserve_level,
            "range": {
                "low": str(calculation.total.low),
                "typical": str(calculation.total.typical),
                "high": str(calculation.total.high),
                "selected": str(calculation.selected_cost),
            },
            "components": {
                key: {"low": str(value.low), "typical": str(value.typical), "high": str(value.high)}
                for key, value in calculation.components.items()
            },
            "parameter_ids": list(calculation.parameter_ids),
        },
    }


def build_manufacturing_cost_lines(
    *,
    estimation_result: Mapping[str, Any],
    production_context: Mapping[str, Any],
    parameter_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Route and price agent-extracted manufacturing features deterministically."""

    rows: list[dict[str, Any]] = []
    for index, feature in enumerate(estimation_result.get("manufacturing") or [], start=1):
        process = feature.get("process")
        if process == "cnc_router":
            decision = route_wood_panel_work(
                WoodPanelWork(
                    process_required=True,
                    part_count=feature.get("part_count"),
                    rectangular_parts_only=_tri(feature.get("rectangular_parts_only")),
                    single_face_processing=_tri(feature.get("single_face_processing")),
                    hole_count=feature.get("hole_count"),
                    standard_operations_only=_tri(feature.get("standard_operations_only")),
                    has_freeform_contours=_tri(feature.get("has_freeform_contours")),
                    has_internal_cutouts=_tri(feature.get("has_internal_cutouts")),
                    has_pockets=_tri(feature.get("has_pockets")),
                    has_horizontal_or_end_drilling=_tri(feature.get("has_horizontal_or_end_drilling")),
                    has_repeated_hole_patterns=_tri(feature.get("has_repeated_hole_patterns")),
                    has_tight_positional_relationships=_tri(feature.get("has_tight_positional_relationships")),
                ),
                cnc_in_house=_availability(production_context, "wood_cnc_router"),
                panel_saw_in_house=_availability(production_context, "wood_panel_saw"),
            )
            if decision.calculator == "cnc_router_in_house":
                calculation = _cnc_in_house(feature, production_context, parameter_rows)
            elif decision.calculator == "cnc_router_subcontractor":
                calculation = _cnc_subcontractor(feature, production_context, parameter_rows)
            else:
                continue
        elif process == "sheet_laser":
            decision = route_sheet_metal_work(
                SheetMetalWork(
                    process_required=True,
                    part_count=feature.get("part_count"),
                    straight_edge_to_edge_cuts_only=_tri(feature.get("straight_edge_to_edge_cuts_only")),
                    cut_count=feature.get("hole_count"),
                    rough_finish_acceptable=_tri(feature.get("rough_finish_acceptable")),
                    material_and_thickness_supported=_tri(feature.get("material_and_thickness_supported")),
                    basic_in_house_cutting_explicitly_confirmed=False,
                    has_holes_or_internal_features=(
                        None if feature.get("hole_count") is None else feature.get("hole_count") > 0
                    ),
                    has_curves_or_shaped_edges=_tri(feature.get("has_curves_or_shaped_edges")),
                    precision_or_repeatability_required=_tri(feature.get("precision_or_repeatability_required")),
                ),
                sheet_laser_in_house=_availability(production_context, "metal_sheet_laser"),
            )
            if decision.calculator == "sheet_laser_in_house":
                calculation = _laser_in_house(feature, production_context, parameter_rows)
            elif decision.calculator == "sheet_laser_subcontractor":
                calculation = _laser_subcontractor(feature, parameter_rows)
            else:
                continue
        else:
            continue

        rows.append(
            _row(
                estimate_id=str(estimation_result["estimate_id"]),
                object_id=str(estimation_result["object_id"]),
                company_id=str(estimation_result["company_id"]),
                index=index,
                calculation=calculation,
                feature=feature,
            )
        )
    return rows


def _cnc_in_house(feature, context, rows) -> CostCalculation:
    params: dict[str, ValueRange] = {}
    ids: list[str] = []
    definitions = (
        ("effective_feed_rate_m_per_min", "m/min"),
        ("seconds_per_hole", "s/hole"),
        ("tool_change_and_non_cutting_minutes", "min/job"),
        ("programming_minutes", "min/job"),
        ("setup_minutes", "min/job"),
        ("sheet_handling_minutes", "min/sheet"),
        ("machine_capacity_rate_per_hour", "ILS/hour"),
        ("programmer_rate_per_hour", "ILS/hour"),
        ("operator_rate_per_hour", "ILS/hour"),
        ("operator_attendance_fraction", "ratio"),
    )
    for key, unit in definitions:
        value, parameter_ids = _range(
            rows, calculator="cnc_router_in_house", key=key, unit=unit,
            currency="ILS" if unit.startswith("ILS/") else None,
            material_family=feature.get("material_family"),
            thickness_mm=feature.get("thickness_mm"), machine_class="nested_router",
        )
        params[key] = value
        ids.extend(parameter_ids)
    machine_rate = _machine_rate_override(context, "wood_cnc_router") or params["machine_capacity_rate_per_hour"]
    return calculate_cnc_router_in_house(
        CncRouterInHouseInputs(
            material_cost=ZERO,
            contour_length_m=_point(feature.get("path_length_m")),
            effective_feed_rate_m_per_min=params["effective_feed_rate_m_per_min"],
            pass_count=_point(feature.get("pass_count"), "1"),
            hole_count=_point(feature.get("hole_count")),
            seconds_per_hole=params["seconds_per_hole"],
            pocket_minutes=_point(feature.get("pocket_minutes")),
            tool_change_and_non_cutting_minutes=params["tool_change_and_non_cutting_minutes"],
            programming_minutes=params["programming_minutes"],
            setup_minutes=params["setup_minutes"],
            sheet_handling_minutes=_scale(params["sheet_handling_minutes"], feature.get("sheet_count") or 1),
            machine_capacity_rate_per_hour=machine_rate,
            programmer_rate_per_hour=params["programmer_rate_per_hour"],
            operator_rate_per_hour=params["operator_rate_per_hour"],
            operator_attendance_fraction=params["operator_attendance_fraction"],
            parameter_ids=tuple(ids),
        ),
        reserve_level=_reserve_level(context, "wood_cnc_router"),
    )


def _cnc_subcontractor(feature, context, rows) -> CostCalculation:
    ids: list[str] = []
    def get(key, unit, currency="ILS"):
        value, found = _range(rows, calculator="cnc_router_subcontractor", key=key, unit=unit, currency=currency, thickness_mm=feature.get("thickness_mm"))
        ids.extend(found)
        return value
    base = get("dxf_cutting_service", "ILS/job")
    minimum = get("provider_minimum", "ILS/job")
    delivery = get("allocated_delivery", "ILS/job")
    file_preparation = ZERO if _tri(feature.get("production_file_ready")) is True else get("file_preparation", "ILS/job")
    internal = ZERO
    if any(_tri(feature.get(key)) is True for key in ("has_internal_cutouts", "has_pockets", "has_horizontal_or_end_drilling")):
        internal = _scale(get("internal_feature_charge", "ILS/part"), feature.get("part_count") or 1)
    edge = ZERO
    if _decimal(feature.get("edge_banding_length_m")) > 0:
        edge = _scale(get("edge_banding_charge", "ILS/m"), feature.get("edge_banding_length_m"))
    return calculate_cnc_router_subcontractor(
        CncRouterSubcontractorInputs(
            provider_base_charge=base,
            base_includes_material=False,
            base_includes_cutting=True,
            programming_or_file_preparation=file_preparation,
            internal_feature_charge=internal,
            edge_banding=edge,
            provider_minimum=minimum,
            allocated_delivery=delivery,
            parameter_ids=tuple(ids),
        ),
        reserve_level=_reserve_level(context, "wood_cnc_router"),
    )


def _laser_in_house(feature, context, rows) -> CostCalculation:
    params: dict[str, ValueRange] = {}
    ids: list[str] = []
    definitions = (
        ("effective_cut_speed_m_per_min", "m/min", None),
        ("pierce_seconds", "s/pierce", None),
        ("rapid_moves_and_sheet_exchange_minutes", "min/sheet", None),
        ("programming_and_nesting_minutes", "min/job", None),
        ("setup_minutes", "min/job", None),
        ("machine_capacity_rate_per_hour", "ILS/hour", "ILS"),
        ("programmer_rate_per_hour", "ILS/hour", "ILS"),
        ("operator_rate_per_hour", "ILS/hour", "ILS"),
        ("operator_attendance_fraction", "ratio", None),
        ("assist_gas_cost_per_machine_hour", "ILS/hour", "ILS"),
        ("average_production_kw", "kW", None),
        ("electricity_cost_per_kwh", "ILS/kWh", "ILS"),
        ("consumables_cost_per_machine_hour", "ILS/hour", "ILS"),
        ("loading_unloading_minutes", "min/sheet", None),
    )
    for key, unit, currency in definitions:
        value, found = _range(
            rows, calculator="sheet_laser_in_house", key=key, unit=unit, currency=currency,
            material_family=feature.get("material_family"), thickness_mm=feature.get("thickness_mm"), machine_class="fiber_laser",
        )
        params[key] = value
        ids.extend(found)
    machine_rate = _machine_rate_override(context, "metal_sheet_laser") or params["machine_capacity_rate_per_hour"]
    return calculate_sheet_laser_in_house(
        SheetLaserInHouseInputs(
            sheet_material_cost=ZERO,
            cut_length_m=_point(feature.get("path_length_m")),
            effective_cut_speed_m_per_min=params["effective_cut_speed_m_per_min"],
            pierce_count=_point(feature.get("hole_count")),
            pierce_seconds=params["pierce_seconds"],
            rapid_moves_and_sheet_exchange_minutes=_scale(params["rapid_moves_and_sheet_exchange_minutes"], feature.get("sheet_count") or 1),
            programming_and_nesting_minutes=params["programming_and_nesting_minutes"],
            setup_minutes=params["setup_minutes"],
            machine_capacity_rate_per_hour=machine_rate,
            programmer_rate_per_hour=params["programmer_rate_per_hour"],
            operator_rate_per_hour=params["operator_rate_per_hour"],
            operator_attendance_fraction=params["operator_attendance_fraction"],
            assist_gas_cost_per_machine_hour=params["assist_gas_cost_per_machine_hour"],
            average_production_kw=params["average_production_kw"],
            electricity_cost_per_kwh=params["electricity_cost_per_kwh"],
            consumables_cost_per_machine_hour=params["consumables_cost_per_machine_hour"],
            loading_unloading_minutes=_scale(params["loading_unloading_minutes"], feature.get("sheet_count") or 1),
            parameter_ids=tuple(ids),
        ),
        reserve_level=3,
    )


def _laser_subcontractor(feature, rows) -> CostCalculation:
    ids: list[str] = []
    def get(key, unit):
        value, found = _range(rows, calculator="sheet_laser_subcontractor", key=key, unit=unit, currency="ILS")
        ids.extend(found)
        return value
    cut_charge = None
    path_length = feature.get("path_length_m")
    if path_length is not None and feature.get("material_family") and feature.get("thickness_mm") is not None:
        try:
            per_meter, found = _range(
                rows,
                calculator="sheet_laser_subcontractor",
                key="cut_charge_per_meter",
                unit="ILS/m",
                currency="ILS",
                material_family=feature.get("material_family"),
                thickness_mm=feature.get("thickness_mm"),
            )
            ids.extend(found)
            cut_charge = _scale(per_meter, path_length)
        except ManufacturingParameterError:
            cut_charge = None
    if cut_charge is None:
        machine_minutes = feature.get("machine_minutes")
        if machine_minutes is None:
            raise ManufacturingEstimationError(
                "Sheet-laser subcontracting requires a matched per-metre curve or machine_minutes."
            )
        cut_charge = _scale(get("cut_charge_per_machine_minute", "ILS/min"), machine_minutes)
    setup = get("provider_setup", "ILS/job")
    minimum = get("provider_minimum", "ILS/job")
    delivery = get("allocated_delivery", "ILS/job")
    file_preparation = ZERO if _tri(feature.get("production_file_ready")) is True else get("file_preparation", "ILS/job")
    return calculate_sheet_laser_subcontractor(
        SheetLaserSubcontractorInputs(
            provider_base_charge=ZERO,
            base_includes_material=False,
            base_includes_cutting=False,
            provider_setup=setup,
            provider_cut_charge=cut_charge,
            file_preparation=file_preparation,
            provider_minimum=minimum,
            allocated_delivery=delivery,
            parameter_ids=tuple(ids),
        ),
        reserve_level=3,
    )
