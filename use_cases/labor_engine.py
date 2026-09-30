from __future__ import annotations

"""Deterministic Labor Engine v0.

This module is intentionally independent from the legacy Estimation Agent.
It converts validated object facts into auditable labor traces only. Pricing,
overhead, margin, and supplier component prices belong to later layers.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


LABOR_BASELINE_VERSION = "labor_time_v0"


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


# The catalog is intentionally narrow at first. Every value is traceable to
# LABOR_TIME_BASELINE_V0.md and is expanded only when its template is enabled.
BASELINES: dict[str, OperationBaseline] = {
    "sheet_nesting": OperationBaseline(4, 3, "cnc_operator", 60),
    "panel_material_handling": OperationBaseline(3, 0.8, "general_worker", 25),
    "panel_saw_cutting": OperationBaseline(6, 0.45, "wood_machine_operator", 40),
    "cnc_router_profile_cutting": OperationBaseline(12, 0.35, "cnc_operator", 40, attendance_fraction=0.25),
    "cnc_vertical_drilling": OperationBaseline(12, 0.12, "cnc_operator", 40, attendance_fraction=0.25),
    "manual_drilling": OperationBaseline(6, 0.45, "carpenter", 25),
    "edge_banding": OperationBaseline(8, 0.55, "wood_machine_operator", 60),
    "carcass_assembly": OperationBaseline(5, 16, "carpenter", 25),
    "drawer_assembly": OperationBaseline(4, 14, "carpenter", 25),
    "door_front_fitting": OperationBaseline(3, 8, "carpenter", 25),
    "hardware_installation": OperationBaseline(3, 2.5, "carpenter", 25),
    "quality_inspection": OperationBaseline(3, 4, "production_manager", 25),
    "protective_packaging": OperationBaseline(3, 7, "packer", 25),
    "metal_profile_cutting": OperationBaseline(8, 1.2, "metal_machine_operator", 25),
    "metal_assembly": OperationBaseline(8, 10, "welder", 25),
    "mig_mag_welding": OperationBaseline(8, 4.55, "welder", 70),
    "tig_welding": OperationBaseline(12, 12, "welder", 25),
    "metal_grinding": OperationBaseline(5, 2.8, "grinder_polisher", 25),
    "metal_polishing": OperationBaseline(8, 28, "grinder_polisher", 25),
    "powder_coating_preparation": OperationBaseline(8, 3.5, "powder_coating_operator", 25),
    "powder_coating_application": OperationBaseline(10, 2.5, "powder_coating_operator", 25),
    "sheet_metal_bending": OperationBaseline(12, 0.08, "press_brake_operator", 70),
}


def _number(value: Any, name: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool):
        raise LaborEngineError(f"{name} must be numeric.")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise LaborEngineError(f"{name} must be numeric.") from error
    if number < minimum:
        raise LaborEngineError(f"{name} must be at least {minimum}.")
    return number


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    number = _number(value, name, minimum=minimum)
    if not number.is_integer():
        raise LaborEngineError(f"{name} must be an integer.")
    return int(number)


def _review(reason: str) -> dict[str, Any]:
    return {
        "status": "review_required",
        "labor_lines": [],
        "purchased_components": [],
        "review_items": [{"code": reason, "severity": "blocking"}],
    }


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


def _attendance(context: Mapping[str, Any], machine: str, fallback: float) -> float:
    values = context.get("machine_attendance_fraction") or {}
    value = values.get(machine, fallback) if isinstance(values, Mapping) else fallback
    return _number(value, f"machine_attendance_fraction.{machine}", minimum=0)


def _line(
    code: str,
    quantity: float,
    *,
    route: str,
    provenance: Sequence[str],
    context: Mapping[str, Any],
    batch_key: str,
    crew_size: int = 1,
) -> dict[str, Any]:
    baseline = BASELINES[code]
    elapsed = max(
        baseline.minimum_minutes,
        baseline.setup_minutes + baseline.minutes_per_unit * quantity,
    )
    attendance = baseline.attendance_fraction
    if code.startswith("cnc_"):
        attendance = _attendance(context, "wood_cnc_router", attendance)
    role_hours = elapsed * attendance * crew_size / 60
    return {
        "operation_code": code,
        "route": route,
        "role_allocations": [{"role": baseline.role, "hours": round(role_hours, 4)}],
        "baseline_version": LABOR_BASELINE_VERSION,
        "baseline_confidence": baseline.confidence,
        "input_drivers": {"quantity": quantity, "unit": "derived"},
        "formula": "crew * max(min_batch, setup + rate * quantity) / 60",
        "elapsed_minutes": round(elapsed, 3),
        "batch_key": batch_key,
        "provenance": list(provenance),
    }


def _panel_dimensions(dimensions: Mapping[str, Any], shelves: int) -> list[tuple[float, float]]:
    width = _number(dimensions.get("width"), "dimensions_mm.width", minimum=1)
    depth = _number(dimensions.get("depth"), "dimensions_mm.depth", minimum=1)
    height = _number(dimensions.get("height"), "dimensions_mm.height", minimum=1)
    return [(depth, height), (depth, height), (width, depth), (width, depth), (width, height)] + [(width, depth)] * shelves


def _cut_sequences(panels: Sequence[tuple[float, float]]) -> int:
    # A transparent V0 proxy for a cutting map. It is deliberately not the
    # panel count, and will later be replaced by a real nesting plan.
    return sum(2 for _ in panels) + 1


def _banded_length_m(panels: Sequence[tuple[float, float]]) -> float:
    # Front edges of sides, top, bottom and every shelf. Back is not banded.
    return round(sum(height for _, height in panels[:2]) / 1000 + sum(width for width, _ in panels[2:4]) / 1000 + sum(width for width, _ in panels[5:]) / 1000, 3)


def _common_workshop_closeout(
    lines: list[dict[str, Any]],
    *,
    module_count: int,
    context: Mapping[str, Any],
    provenance: Sequence[str],
) -> None:
    """Add self-cost workshop work only, never sales delivery or installation."""
    lines.extend(
        [
            _line("quality_inspection", module_count, route="in_house_manual", provenance=provenance, context=context, batch_key="workshop_closeout"),
            _line("protective_packaging", module_count, route="in_house_manual", provenance=provenance, context=context, batch_key="workshop_closeout"),
        ]
    )


def _metal_alloy(material: Mapping[str, Any]) -> str | None:
    family = str(material.get("family") or "").strip()
    specification = material.get("specification") or {}
    if not isinstance(specification, Mapping):
        specification = {}
    declared = str(specification.get("alloy") or "").lower().replace(" ", "_")
    if family == "carbon_steel":
        return "carbon_steel"
    if family in {"stainless_304", "stainless_316"}:
        return family
    if family == "stainless_steel":
        if "316" in declared:
            return "stainless_316"
        if "304" in declared:
            return "stainless_304"
    return None


def _estimate_metal_table_frame(
    object_fact: Mapping[str, Any], company_context: Mapping[str, Any]
) -> dict[str, Any]:
    dimensions = object_fact.get("dimensions_mm")
    features = object_fact.get("features") or {}
    materials = object_fact.get("materials") or []
    if not isinstance(dimensions, Mapping) or not isinstance(features, Mapping):
        return _review("missing_metal_frame_facts")
    try:
        width = _number(dimensions.get("width"), "dimensions_mm.width", minimum=1)
        depth = _number(dimensions.get("depth"), "dimensions_mm.depth", minimum=1)
        height = _number(dimensions.get("height"), "dimensions_mm.height", minimum=1)
        quantity = _integer(object_fact.get("quantity"), "quantity", minimum=1)
        section = _number(features.get("profile_section_mm"), "features.profile_section_mm", minimum=1)
    except LaborEngineError as error:
        return _review(str(error))
    if not materials or not isinstance(materials[0], Mapping):
        return _review("missing_metal_material")
    alloy = _metal_alloy(materials[0])
    if alloy is None:
        return _review("unsupported_metal_alloy")
    machines = _machine_set(company_context)
    if "metal_profile_saw" not in machines:
        return _review("no_supported_metal_profile_route")
    visible_stainless = alloy.startswith("stainless") and str(features.get("visible_finish") or "") in {"brushed", "satin", "polished"}
    coating = str(features.get("coating") or "none")
    if visible_stainless and coating != "none":
        return _review("incompatible_stainless_visible_finish_and_coating")
    qualified_roles = set(company_context.get("qualified_roles") or [])
    if visible_stainless and not ({"grinder_polisher", "metal_finisher"} & qualified_roles):
        return _review("stainless_visible_finish_qualification_unknown")
    member_lengths_m = (4 * height + 2 * width + 4 * depth) / 1000 * quantity
    # Standard table frame has 12 closed/tee joints. Each is tied to the
    # declared profile face, so the weld proxy remains visible and editable.
    weld_length_m = 12 * section / 1000 * quantity
    provenance = ["template:metal_table_frame", "derived:standard_12_joint_frame", f"material:{alloy}"]
    profile_rate = 1.6 if alloy.startswith("stainless") else 1.2
    assembly_rate = 16 if visible_stainless else 10
    weld_code = "tig_welding" if alloy.startswith("stainless") else "mig_mag_welding"
    lines = [
        _line("metal_profile_cutting", 10 * quantity, route="in_house_machine", provenance=provenance, context=company_context, batch_key=f"profile:{alloy}"),
        _line("metal_assembly", quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key="metal_table_frame"),
        _line(weld_code, weld_length_m, route="in_house_manual", provenance=provenance, context=company_context, batch_key=f"weld:{alloy}"),
    ]
    # The source-backed generic values have material branches. Expose the
    # selected branch rather than silently changing the formula.
    lines[0]["elapsed_minutes"] = round(8 + profile_rate * (10 * quantity), 3)
    lines[0]["role_allocations"][0]["hours"] = round(lines[0]["elapsed_minutes"] / 60, 4)
    lines[0]["input_drivers"] = {
        "profile_cut_count": 10 * quantity,
        "member_total_length_m": round(member_lengths_m, 3),
        "unit": "derived",
    }
    lines[1]["elapsed_minutes"] = round(8 + assembly_rate * quantity, 3)
    lines[1]["role_allocations"][0]["hours"] = round(lines[1]["elapsed_minutes"] / 60, 4)
    if visible_stainless:
        exposed_area_sqm = 2 * (width * depth) / 1_000_000 * quantity
        lines.append(_line("metal_grinding", weld_length_m, route="in_house_manual", provenance=provenance, context=company_context, batch_key="stainless_visible_finish"))
        polishing = _line("metal_polishing", exposed_area_sqm, route="in_house_manual", provenance=provenance, context=company_context, batch_key="stainless_visible_finish")
        polishing["elapsed_minutes"] = round(12 + 55 * exposed_area_sqm, 3)
        polishing["role_allocations"][0]["hours"] = round(polishing["elapsed_minutes"] / 60, 4)
        lines.append(polishing)
    elif coating == "powder":
        if "finish_powder_booth" in machines:
            lines.extend([
                _line("powder_coating_preparation", quantity, route="in_house_machine", provenance=provenance, context=company_context, batch_key="powder:black"),
                _line("powder_coating_application", quantity, route="in_house_machine", provenance=provenance, context=company_context, batch_key="powder:black"),
            ])
        else:
            return _review("external_powder_component_not_yet_enabled")
    _common_workshop_closeout(
        lines,
        module_count=quantity,
        context=company_context,
        provenance=provenance,
    )
    return {"object_id": object_fact.get("object_id"), "status": "estimated", "labor_lines": lines, "purchased_components": [], "review_items": []}


def _estimate_sheet_metal_box(
    object_fact: Mapping[str, Any], company_context: Mapping[str, Any]
) -> dict[str, Any]:
    dimensions = object_fact.get("dimensions_mm")
    materials = object_fact.get("materials") or []
    if not isinstance(dimensions, Mapping) or not materials or not isinstance(materials[0], Mapping):
        return _review("missing_sheet_metal_box_facts")
    try:
        width = _number(dimensions.get("width"), "dimensions_mm.width", minimum=1)
        depth = _number(dimensions.get("depth"), "dimensions_mm.depth", minimum=1)
        quantity = _integer(object_fact.get("quantity"), "quantity", minimum=1)
    except LaborEngineError as error:
        return _review(str(error))
    machines = _machine_set(company_context)
    if "metal_press_brake" not in machines:
        return _review("no_supported_press_brake_route")
    contour_m = 2 * (width + depth) / 1000 * quantity
    provenance = ["template:sheet_metal_box", "derived:closed_box_four_bends"]
    lines = [_line("sheet_metal_bending", 4 * quantity, route="in_house_machine", provenance=provenance, context=company_context, batch_key="sheet_metal_box")]
    purchased = []
    if "metal_sheet_laser" not in machines:
        purchased.append({"component_type": "sheet_laser_cut_part", "route": "external_component", "attributes": {"contour_length_m": round(contour_m, 3)}})
    else:
        return _review("in_house_sheet_laser_labor_not_yet_enabled")
    return {"object_id": object_fact.get("object_id"), "status": "estimated", "labor_lines": lines, "purchased_components": purchased, "review_items": []}


def estimate_labor(
    object_fact: Mapping[str, Any],
    company_context: Mapping[str, Any],
) -> dict[str, Any]:
    """Return an explainable Labor Engine result for supported panel templates."""

    template = object_fact.get("template_code")
    if template == "metal_table_frame":
        return _estimate_metal_table_frame(object_fact, company_context)
    if template == "sheet_metal_box":
        return _estimate_sheet_metal_box(object_fact, company_context)
    supported = {"base_cabinet_open", "wall_cabinet_hinged", "vanity_cabinet"}
    if template not in supported:
        return _review("unsupported_template")

    try:
        quantity = _integer(object_fact.get("quantity"), "quantity", minimum=1)
        dimensions = object_fact.get("dimensions_mm")
        if not isinstance(dimensions, Mapping):
            return _review("missing_dimensions")
        shelves = _integer((object_fact.get("features") or {}).get("shelf_count", 0), "features.shelf_count")
        features = object_fact.get("features") or {}
        if not isinstance(features, Mapping):
            return _review("invalid_features")
        doors = _integer(features.get("door_count", 0), "features.door_count")
        drawers = _integer(features.get("drawer_count", 0), "features.drawer_count")
    except LaborEngineError as error:
        return _review(str(error))

    materials = object_fact.get("materials") or []
    if not isinstance(materials, Sequence) or not materials:
        return _review("missing_panel_material")
    primary_material = materials[0]
    if not isinstance(primary_material, Mapping) or not primary_material.get("family"):
        return _review("missing_panel_material")

    profile = object_fact.get("construction_profile") or "panel_screw_standard"
    holes_per_connection = {"panel_screw_standard": 4, "confirmat": 4, "cam_dowel": 6, "dowel_glue": 4}.get(profile)
    if holes_per_connection is None:
        return _review("unsupported_construction_profile")

    machines = _machine_set(company_context)
    has_cnc = "wood_cnc_router" in machines
    has_panel_saw = "wood_panel_saw" in machines
    if not has_cnc and not has_panel_saw:
        return _review("no_supported_panel_route")
    if "wood_edge_bander" not in machines:
        return _review("edge_bander_availability_unknown")

    try:
        panels = _panel_dimensions(dimensions, shelves)
    except LaborEngineError as error:
        return _review(str(error))
    connections = 4 + 2 * shelves
    provenance = [f"template:{template}", f"connection:{profile}"]
    lines: list[dict[str, Any]] = []
    specification = primary_material.get("specification") or {}
    thickness = (
        specification.get("thickness_mm")
        if isinstance(specification, Mapping)
        else None
    )
    if thickness is None:
        thickness = primary_material.get("thickness_mm", "unknown")
    material_batch = f"{primary_material['family']}:{thickness}"
    panel_count = len(panels) * quantity
    lines.append(_line("panel_material_handling", panel_count, route="in_house_manual", provenance=provenance, context=company_context, batch_key=material_batch))
    lines.append(_line("sheet_nesting", quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key=material_batch))

    if has_cnc:
        contour_length = sum(2 * (width + height) for width, height in panels) / 1000 * quantity
        holes = connections * holes_per_connection * quantity
        lines.extend(
            [
                _line("cnc_router_profile_cutting", contour_length, route="in_house_machine", provenance=provenance, context=company_context, batch_key=f"cnc:{material_batch}"),
                _line("cnc_vertical_drilling", holes, route="in_house_machine", provenance=provenance, context=company_context, batch_key=f"cnc:{material_batch}"),
            ]
        )
    else:
        cuts = _cut_sequences(panels) * quantity
        holes = connections * holes_per_connection * quantity
        lines.extend(
            [
                _line("panel_saw_cutting", cuts, route="in_house_machine", provenance=provenance, context=company_context, batch_key=material_batch),
                _line("manual_drilling", holes, route="in_house_manual", provenance=provenance, context=company_context, batch_key=material_batch),
            ]
        )

    lines.append(_line("edge_banding", _banded_length_m(panels) * quantity, route="in_house_machine", provenance=provenance, context=company_context, batch_key=material_batch))
    lines.append(_line("carcass_assembly", quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key=template))

    if doors:
        lines.append(_line("door_front_fitting", doors * quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key="door_hardware"))
        lines.append(_line("hardware_installation", doors * 2 * quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key="door_hardware"))
    if drawers:
        lines.append(_line("drawer_assembly", drawers * quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key="drawer_system"))
        lines.append(_line("hardware_installation", drawers * 2 * quantity, route="in_house_manual", provenance=provenance, context=company_context, batch_key="drawer_system"))

    purchased: list[dict[str, Any]] = []
    if template == "vanity_cabinet":
        purchased.append({"component_type": "stone_countertop", "route": "external_component", "attributes": {"cutout_included": bool(features.get("plumbing_cutout"))}})

    _common_workshop_closeout(
        lines,
        module_count=quantity,
        context=company_context,
        provenance=provenance,
    )
    return {
        "object_id": object_fact.get("object_id"),
        "status": "estimated",
        "labor_lines": lines,
        "purchased_components": purchased,
        "review_items": [],
    }
