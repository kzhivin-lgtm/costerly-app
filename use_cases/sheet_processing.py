"""Apply the shop norms to the sheet routes on an Object Detail card."""

from collections import Counter
from dataclasses import dataclass

from use_cases.estimation_labor_v1 import (
    EMPLOYER_LOAD, _family, _line_groups, _parts_index, _positive, _sheet_lines, calculate_labor_v1,
)
from use_cases.panel_saw_calculation import DEFAULT_PANEL_SAW, panel_saw_group


@dataclass(frozen=True)
class ShopParameters:
    manual_pace: float = 1.25
    manual_working_share: float = 0.80
    helper_share: float = 0.10
    edge_bander_working_share: float = 0.85
    iron_working_share: float = 0.75
    iron_setup_minutes: float = 5
    iron_heat_seconds_per_m: float = 70
    iron_trim_seconds_per_m: float = 50
    iron_handling_seconds_per_side: float = 30
    drill_setup_minutes: float = 15
    mark_seconds_per_part: float = 60
    hinge_cup_seconds: float = 90
    hinge_plate_seconds: float = 60
    slide_seconds: float = 90
    lift_kit_seconds: float = 240
    joint_setup_seconds: float = 50
    default_gross_wage: float = 50


DEFAULT_SHOP_PARAMETERS = ShopParameters()


def _manual_drilling(parts, drilled_count, object_quantity, params):
    counts = Counter()
    cabinets = set()
    for part in parts:
        quantity = part.get("quantity")
        if not _positive(quantity):
            continue
        role = part["role"]
        counts[role] += quantity * part.get("scope_quantity", 1) * object_quantity
        if role in {"carcass_top", "carcass_bottom"}:
            cabinets.add(part["owner_id"])
    # Assume four corners with two accesses per cabinet, one per drawer corner,
    # and one per rib end or two per frame-side end.
    joints = (8 * len(cabinets) * object_quantity + 4 * counts["drawer_box_bottom"]
              + 4 * counts["frame_side"] + 2 * counts["vertical_rib"])
    slides = counts["drawer_slide"] + counts["pull_out_shelf_slide"]
    operations = {
        "marking": drilled_count * params.mark_seconds_per_part / 60,
        "hinge_cups": counts["hinge"] * params.hinge_cup_seconds / 60,
        "hinge_plates": counts["hinge"] * params.hinge_plate_seconds / 60,
        "slides": slides * params.slide_seconds / 60,
        "lifts": counts["gas_lift"] * params.lift_kit_seconds / 60,
        "joints": joints * params.joint_setup_seconds / 60,
    }
    operations["setup"] = params.drill_setup_minutes if any(operations.values()) else 0
    return {key: value * params.manual_pace / params.manual_working_share for key, value in operations.items()}


def _edging(edge, runs, *, use_machine, rate, params):
    if use_machine:
        minutes = edge["minutes"] / params.edge_bander_working_share
        return {"method": "Edge bander", "minutes": minutes, "cost": round(minutes * rate / 60, 2), "note": ""}
    supported = [run for run in runs if run["tape_kind"] in {"melamine", "veneer"}]
    metres = sum(run["metres"] for run in supported)
    sides = sum(run["sides"] for run in supported)
    base_minutes = (params.iron_setup_minutes + (metres * (params.iron_heat_seconds_per_m
                    + params.iron_trim_seconds_per_m) + sides * params.iron_handling_seconds_per_side) / 60
                    if metres else 0)
    minutes = base_minutes * params.manual_pace / params.iron_working_share
    if edge["metres"] and len(supported) < len(runs):
        note = "Some tape requires a different edge process"
    elif metres:
        note = "Confirm iron-on tape" if all(row["tape_kind"] == "melamine" for row in supported) else "Confirm tape and veneer timing"
    else:
        note = ""
    return {"method": "Iron-on", "minutes": minutes, "cost": round(minutes * rate / 60, 2),
            "note": note, "unestimated": len(supported) < len(runs)}


def _saw_work(report, layout, plan, *, object_id):
    part_index = _parts_index(report)
    quantities = plan.get("object_quantities") or {}
    roles = {(oid, row["requirement_id"]): row.get("material_role")
             for oid, parts in (plan.get("parts_check") or {}).items() for row in parts.get("materials", ())}
    groups = {(row["selection_key"], row["thickness_mm"]): row for row in layout["groups"]}
    prefix = object_id + ":"
    missing = 0
    stock_rows = []
    minutes = Counter()
    work = Counter()
    geometry_review = False
    for line in _sheet_lines(plan):
        if not any(row["object_id"] == object_id for row in line["allocations"]):
            continue
        for thickness, data in _line_groups(line, part_index, quantities, roles, []).items():
            own_blanks = [part for part in data["blanks"] if part.part_id.startswith(prefix)]
            if not own_blanks:
                continue
            group = groups.get((line["selection_key"], thickness))
            if group is None:
                missing += sum(part.quantity for part in own_blanks)
                continue
            # The rectangle estimate must not imply that known contours and cutouts can be sawn.
            geometry_review |= any(part_index[part.part_id].get(field) for part in own_blanks for field in (
                "worktop_outline", "worktop_cutouts", "has_freeform_contours", "has_internal_cutouts", "has_pockets",
            ))
            saw = panel_saw_group(group, data["blanks"], family=_family(line))
            missing += sum(quantity for key, quantity in saw["unplaced"].items() if key.startswith(prefix))
            share = 0.0
            for sheet in saw["sheets"]:
                placed = sheet["placements"]
                own = [part for part in placed if part.part_id.startswith(prefix)]
                if not own:
                    continue
                area_share = (sum(part.length * part.width for part in own)
                              / sum(part.length * part.width for part in placed))
                share += area_share
                work.update(blanks=len(own), cuts=sheet["cuts"] * area_share,
                            cut_metres=sheet["cut_metres"] * area_share, stops=sheet["stop_changes"] * area_share)
                minutes.update({key: value * area_share for key, value in sheet["minutes"].items()})
                minutes["sort"] += len(own) * DEFAULT_PANEL_SAW.sort_seconds / 60
            if share:
                rate = line["price_per_purchase_unit"]
                priced = (line["currency"] == "ILS" and not line["selection_key"].startswith("assumption:")
                          and line.get("authority") != "assumption" and _positive(rate))
                stock_rows.append({"sheets": share, "stock_ex_vat": round(share * rate, 2) if priced else None})
    return dict(minutes), dict(work), stock_rows, missing, geometry_review


def calculate_sheet_processing(report, layout, plan, *, object_id, machinery, params=DEFAULT_SHOP_PARAMETERS):
    """Compare the supplier with the applicable in-house estimate, using one saved Parts Check."""
    result = calculate_labor_v1(layout, plan, object_id=object_id,
                                operator_gross_rate=machinery.get("cnc_operator_wage"))
    availability = machinery.get("availability") or {}
    cnc_status = availability.get("wood_cnc_router")
    saw_status = availability.get("wood_panel_saw")
    bander_status = availability.get("wood_edge_bander")
    wage = params.default_gross_wage * (1 + EMPLOYER_LOAD)
    runs = (plan.get("edge_runs_by_object") or {}).get(object_id, ())
    edge = result["edge_banding"]
    result["cnc_edging"] = _edging(edge, runs, use_machine=bander_status != "not_in_house", rate=wage, params=params)
    result["in_house_route"] = None if cnc_status == "not_in_house" else "cnc"
    result["panel_saw"] = None
    if cnc_status == "in_house" or not result["work"]["blank_count"] or saw_status == "not_in_house":
        return result

    base, volume, materials, missing, geometry_review = _saw_work(report, layout, plan, object_id=object_id)
    drill = _manual_drilling(report["objects"][object_id]["parts"], result["work"]["drilled_part_count"],
                            (plan.get("object_quantities") or {}).get(object_id, 1), params)
    operation_factor = params.manual_pace / params.manual_working_share
    saw = {key: value * operation_factor for key, value in base.items()}
    prep = result["file_preparation"]["minutes"] * params.manual_pace
    helper = sum(base.values()) * params.manual_pace * params.helper_share
    edging = _edging(edge, runs, use_machine=bander_status == "in_house", rate=wage, params=params)
    result["panel_saw"] = {
        "materials": materials, "volume": volume, "saw": saw, "drilling": drill, "edging": edging,
        "preparation_minutes": prep, "preparation_cost": round(prep * wage / 60, 2),
        "operator_cost": round((sum(saw.values()) + sum(drill.values()) + helper) * wage / 60, 2),
        "helper_minutes": helper, "unplaced": missing, "geometry_review": geometry_review,
        "minutes": prep + sum(saw.values()) + sum(drill.values()) + edging["minutes"],
    }
    if cnc_status != "in_house" and saw_status == "in_house" and not (missing or geometry_review or result["issues"]):
        result["in_house_route"] = "panel_saw"
    return result
