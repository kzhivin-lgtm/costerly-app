from __future__ import annotations

"""Universal deterministic labor calculator.

The Estimation Agent supplies a validated fabrication-operation plan derived
from the actual object. This module knows operation formulas and company
capabilities only. It never classifies objects or selects work by object name.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from use_cases.estimation_v2_composition import LABOR_OPERATION_VALUES


LABOR_BASELINE_VERSION = "labor_time_v1"


class LaborEngineError(ValueError):
    pass


@dataclass(frozen=True)
class OperationBaseline:
    setup_minutes: float
    minutes_per_unit: float
    role: str
    confidence: int
    minimum_minutes: float = 0.0
    attendance_fraction: float = 1.0


def _b(setup: float, rate: float, role: str, confidence: int, *, attendance: float = 1.0) -> OperationBaseline:
    return OperationBaseline(setup, rate, role, confidence, attendance_fraction=attendance)


BASELINES: dict[str, OperationBaseline] = {
    "estimate_review": _b(4, 8, "estimator", 25),
    "shop_drawing": _b(10, 25, "draftsperson", 25),
    "cnc_programming": _b(10, 12, "cnc_operator", 25),
    "sheet_nesting": _b(4, 3, "cnc_operator", 60),
    "supplier_quotation": _b(5, 8, "estimator", 25),
    "quality_inspection": _b(3, 4, "production_manager", 25),
    "panel_material_handling": _b(3, 0.8, "general_worker", 25),
    "panel_saw_cutting": _b(6, 0.45, "wood_machine_operator", 40),
    "cnc_router_profile_cutting": _b(12, 0.35, "cnc_operator", 40, attendance=0.25),
    "cnc_vertical_drilling": _b(12, 0.12, "cnc_operator", 40, attendance=0.25),
    "cnc_horizontal_drilling": _b(10, 0.20, "cnc_operator", 40, attendance=0.25),
    "cnc_grooving": _b(12, 0.45, "cnc_operator", 40, attendance=0.25),
    "cnc_pocketing": _b(12, 0.75, "cnc_operator", 40, attendance=0.25),
    "manual_panel_cutting": _b(8, 1.4, "carpenter", 25),
    "manual_drilling": _b(6, 0.45, "carpenter", 25),
    "manual_routing": _b(8, 1.5, "carpenter", 25),
    "edge_banding": _b(8, 0.55, "wood_machine_operator", 60),
    "veneer_lamination": _b(18, 6, "wood_machine_operator", 25),
    "solid_wood_ripping": _b(8, 0.55, "wood_machine_operator", 60),
    "solid_wood_crosscutting": _b(6, 0.65, "wood_machine_operator", 60),
    "solid_wood_jointing_planing": _b(10, 0.9, "wood_machine_operator", 25),
    "solid_wood_profiling": _b(14, 1.15, "wood_machine_operator", 25),
    "solid_wood_glueup": _b(12, 2.2, "carpenter", 25),
    "wood_sanding": _b(8, 12, "painter_finisher", 25),
    "carcass_assembly": _b(5, 16, "carpenter", 25),
    "drawer_assembly": _b(3, 11, "carpenter", 25),
    "door_front_fitting": _b(3, 8, "carpenter", 25),
    "hardware_installation": _b(3, 2.5, "carpenter", 25),
    "workshop_dry_fit": _b(5, 8, "carpenter", 25),
    "sheet_laser_cutting": _b(10, 0.28, "laser_operator", 70, attendance=0.25),
    "sheet_shearing": _b(8, 0.7, "metal_machine_operator", 25),
    "metal_profile_cutting": _b(8, 1.2, "metal_machine_operator", 25),
    "metal_drilling": _b(8, 0.6, "metal_machine_operator", 25),
    "metal_milling": _b(15, 0.6, "metal_machine_operator", 25),
    "metal_punching": _b(10, 0.25, "metal_machine_operator", 40),
    "sheet_metal_bending": _b(12, 0.08, "press_brake_operator", 70),
    "metal_profile_bending": _b(20, 3.5, "metal_machine_operator", 25),
    "metal_rolling": _b(20, 7, "metal_machine_operator", 25),
    "mig_mag_welding": _b(8, 4.55, "welder", 70),
    "tig_welding": _b(12, 12, "welder", 25),
    "metal_grinding": _b(5, 2.8, "grinder_polisher", 25),
    "metal_polishing": _b(8, 28, "grinder_polisher", 25),
    "metal_assembly": _b(8, 10, "welder", 25),
    "finish_surface_preparation": _b(8, 11, "painter_finisher", 25),
    "wood_staining": _b(8, 6, "painter_finisher", 25),
    "wood_priming": _b(10, 7, "painter_finisher", 25),
    "wood_lacquering": _b(10, 8, "painter_finisher", 25),
    "wet_spray_painting": _b(12, 9, "painter_finisher", 25),
    "powder_coating_preparation": _b(8, 3.5, "powder_coating_operator", 25),
    "powder_coating_application": _b(10, 2.5, "powder_coating_operator", 25),
    "sandblasting": _b(10, 7, "metal_finisher", 25),
    "galvanizing": _b(8, 0.5, "general_worker", 25),
    "protective_packaging": _b(3, 7, "packer", 25),
}


MACHINE_REQUIREMENTS: dict[str, str] = {
    "panel_saw_cutting": "wood_panel_saw",
    "cnc_router_profile_cutting": "wood_cnc_router",
    "cnc_vertical_drilling": "wood_cnc_router",
    "cnc_horizontal_drilling": "wood_cnc_router",
    "cnc_grooving": "wood_cnc_router",
    "cnc_pocketing": "wood_cnc_router",
    "edge_banding": "wood_edge_bander",
    "veneer_lamination": "wood_veneer_press",
    "solid_wood_ripping": "wood_solid_preparation",
    "solid_wood_crosscutting": "wood_solid_preparation",
    "solid_wood_jointing_planing": "wood_solid_preparation",
    "solid_wood_profiling": "wood_solid_preparation",
    "sheet_laser_cutting": "metal_sheet_laser",
    "metal_profile_cutting": "metal_profile_saw",
    "metal_punching": "metal_punch_press",
    "sheet_metal_bending": "metal_press_brake",
    "metal_profile_bending": "metal_profile_bender",
    "metal_rolling": "metal_rolling_machine",
    "wet_spray_painting": "finish_wet_spray_booth",
    "powder_coating_preparation": "finish_powder_booth",
    "powder_coating_application": "finish_powder_booth",
    "sandblasting": "finish_sandblast_booth",
    "galvanizing": "finish_galvanizing",
}


def _number(value: Any, name: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool):
        raise LaborEngineError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise LaborEngineError(f"{name} must be numeric") from exc
    if number < minimum:
        raise LaborEngineError(f"{name} must be at least {minimum}")
    return number


def _machine_set(context: Mapping[str, Any]) -> set[str]:
    machines = context.get("machinery") or context.get("machines") or []
    result: set[str] = set()
    for machine in machines:
        if isinstance(machine, str):
            result.add(machine)
        elif isinstance(machine, Mapping) and machine.get("availability_status") == "in_house":
            code = machine.get("machine_code")
            if isinstance(code, str):
                result.add(code)
    return result


def _review(reason: str) -> dict[str, Any]:
    return {
        "status": "review_required",
        "labor_lines": [],
        "purchased_components": [],
        "review_items": [{"code": reason, "severity": "blocking"}],
    }


def _operation_line(operation: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    code = str(operation["operation_code"])
    baseline = BASELINES[code]
    quantity = _number(operation["quantity"], f"{code}.quantity", minimum=0.000001)
    elapsed = max(baseline.minimum_minutes, baseline.setup_minutes + baseline.minutes_per_unit * quantity)
    machine_code = operation.get("machine_code")
    attendance = baseline.attendance_fraction
    attendance_values = context.get("machine_attendance_fraction") or {}
    if machine_code and isinstance(attendance_values, Mapping):
        attendance = _number(
            attendance_values.get(machine_code, attendance),
            f"machine_attendance_fraction.{machine_code}",
        )
    role_hours = elapsed * attendance / 60
    return {
        "operation_code": code,
        "route": operation["route"],
        "role_allocations": [{"role": baseline.role, "hours": round(role_hours, 4)}],
        "baseline_version": LABOR_BASELINE_VERSION,
        "baseline_confidence": min(int(operation["confidence"]), baseline.confidence),
        "input_drivers": {
            "quantity": quantity,
            "unit": operation["unit"],
            "basis": operation["basis"],
            "material_requirement_ids": list(operation["material_requirement_ids"]),
            "machine_code": machine_code,
        },
        "formula": "attendance * max(minimum, setup + rate * quantity) / 60",
        "elapsed_minutes": round(elapsed, 3),
        "batch_key": operation["batch_key"],
        "provenance": [operation["provenance"], *operation["evidence_refs"]],
    }


def estimate_labor(object_fact: Mapping[str, Any], company_context: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and price no work, returning hours for an agent-created plan."""
    operations = object_fact.get("labor_operations")
    if not isinstance(operations, Sequence) or isinstance(operations, (str, bytes)) or not operations:
        return _review("labor_plan_missing")
    machines = _machine_set(company_context)
    lines: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(operations):
        if not isinstance(value, Mapping):
            return _review(f"labor_operation_invalid:{index}")
        operation_id = str(value.get("operation_id") or "")
        code = str(value.get("operation_code") or "")
        route = str(value.get("route") or "")
        if not operation_id or operation_id in seen_ids:
            return _review("labor_operation_id_invalid")
        seen_ids.add(operation_id)
        if code not in LABOR_OPERATION_VALUES or code not in BASELINES:
            return _review(f"labor_operation_unsupported:{code}")
        required_machine = MACHINE_REQUIREMENTS.get(code)
        declared_machine = value.get("machine_code")
        if required_machine:
            if route != "in_house_machine" or declared_machine != required_machine:
                return _review(f"machinery_route_invalid:{code}")
            if required_machine not in machines:
                return _review(f"machinery_unavailable:{required_machine}")
        elif route != "in_house_manual" or declared_machine is not None:
            return _review(f"manual_route_invalid:{code}")
        try:
            lines.append(_operation_line(value, company_context))
        except (KeyError, LaborEngineError, TypeError, ValueError) as exc:
            return _review(f"labor_operation_invalid:{operation_id}:{exc}")
    return {
        "object_id": object_fact.get("object_id"),
        "status": "estimated",
        "labor_lines": lines,
        "purchased_components": [],
        "review_items": [],
    }
