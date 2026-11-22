"""Saved panel layouts and the two CNC routes in Labor V1."""

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, ROUND_HALF_UP
import logging
from hashlib import sha256
import json
from math import ceil, isfinite

from use_cases.estimation_cnc_supplier_rates import (
    SUPPLIER_EDGE_RATE_INCLUDES_TAPE, SUPPLIER_EDGE_RATE_PER_M, SUPPLIER_MACHINING_RATE,
    SUPPLIER_PROFILE_VERSION, supplier_sheet_rate,
)
from use_cases.estimation_edge_banding import EDGE_FAMILY
from use_cases.wood_cnc_calculation import (
    DEFAULT_CNC_PARAMETERS, Blank, Placement, StockBatch, cnc_workload_from_layout,
    in_house_cost, layout_joinable_sheet, shared_cut_credits,
)


LABOR_VERSION = "Labor V1.2.23"
LAYOUT_VERSION = "cnc_sheet_layout_v2"
SHEET_FAMILIES = {
    "mdf_hdf", "faced_mdf", "fibreboard_hardboard", "particleboard",
    "melamine_faced_particleboard", "plywood", "plywood_special",
}
PLINTH_ROLES = {"plinth_visible_run", "plinth_front", "plinth_return"}
SPLIT_ROLES = PLINTH_ROLES | {"carcass_back", "frame_backing"}
DRILL_EXCLUSIONS = SPLIT_ROLES | {"drawer_box_bottom"}
PANEL_ROLES = {"carcass_sheet", "backing_sheet", "internal_sheet", "visible_sheet", "worktop_substrate"}
EMPLOYER_LOAD = 0.25
OPERATOR_RATE = 55


@dataclass(frozen=True)
class CncFilePreparationParameters:
    reference_positions: int = 85
    reference_minutes: float = 60
    supplier_includes_preparation: bool = False


DEFAULT_CNC_FILE_PREPARATION = CncFilePreparationParameters()


@dataclass(frozen=True)
class EdgeBandingParameters:
    feed_metres_per_minute: float = 7
    handling_seconds_per_side: float = 12
    setup_minutes: float = 10
    operator_gross_ils_per_hour: float = 50


DEFAULT_EDGE_BANDING = EdgeBandingParameters()


def _positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) and value > 0


def _family(line):
    key = line["selection_key"]
    return key.split(":")[2] if key.startswith("assumption:") else key.split("|", 1)[0]


def _sheet_lines(plan):
    return [line for line in plan["lines"] if line["purchase_kind"] == "sheet" and _family(line) in SHEET_FAMILIES]


def sheet_layout_basis(plan):
    """Fingerprint the stock and physical quantities, independent of prices and approval order."""
    fields = ("candidate_id", "selection_key", "purchasable_dimensions", "label_specifications", "allocations")
    material = [{key: line.get(key) for key in fields} for line in _sheet_lines(plan)]
    basis = {
        oid: (evidence.get("materials"), evidence.get("unpriced_requirements"))
        for oid, evidence in (plan.get("parts_check") or {}).items()
    }
    value = {"sheets": material, "quantities": plan.get("object_quantities") or {}, "requirements": basis}
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _parts_index(report):
    indexed = {}
    for object_id, obj in report["objects"].items():
        counters = Counter()
        for row in obj["parts"]:
            owner = row["owner_id"]
            counters[owner] += 1
            indexed[f"{object_id}:{owner}:{row['role']}:{counters[owner]:03d}"] = row
    return indexed


def _thickness(row, line):
    labels = line.get("label_specifications") or {}
    from_stock = labels.get("thickness_mm", labels.get("thickness"))
    if _positive(from_stock):
        return from_stock
    for term in line["selection_key"].split("|")[1:]:
        if term.startswith("thickness="):
            try:
                parsed = float(term.split("=", 1)[1])
            except ValueError:
                break
            return parsed if _positive(parsed) else None
    return row["dimensions"].get("thickness", {}).get("mm")


def _grain_required(row, line, family, *, material_choice=None):
    if material_choice == "mdf":
        return False
    visual = row.get("visual_stock") or {}
    return (family in {"plywood", "plywood_special"} or "veneer" in line["display_name"].casefold()
            or visual.get("surface") == "wood_grain"
            or any(surface.get("finish") == "wood_grain" for surface in row.get("finish_surfaces", ())))


def _line_groups(line, parts, object_quantities, scope_by_requirement, issues):
    quantities = Counter()
    sizes = {}
    material_choices = {}
    for allocation in line["allocations"]:
        part_id = allocation["demand_id"].removesuffix(":assumption")
        material_choices[part_id] = allocation.get("front_panel_material_choice")
        row = parts.get(part_id)
        requirement = allocation.get("object_id"), allocation.get("material_requirement_id")
        if ((row and row["role"] == "shared_worktop")
                or (not row and scope_by_requirement.get(requirement) == "worktop_sheet")):
            # The contrasting end of a kitchen worktop travels with the worktop.
            continue
        # Worktop surfaces derived from polygons have a surface suffix on their demand ID.
        if ":surface:" in part_id and part_id.partition(":surface:")[0] in parts:
            continue
        l, w, qty = (allocation.get(field) for field in ("length_mm", "width_mm", "quantity"))
        thickness = _thickness(row, line) if row else None
        if not all(_positive(value) for value in (l, w, qty, thickness)) or int(qty) != qty:
            issues.append({"reference": part_id, "issue": "Missing sheet, part dimensions or count"})
            continue
        key = part_id, thickness
        sizes[key] = l, w
        quantities[key] += int(qty)

    family = _family(line)
    by_thickness = {}
    for (part_id, thickness), qty in quantities.items():
        row = parts[part_id]
        blank = Blank(part_id, *sizes[part_id, thickness], qty,
                      rotation_allowed=not _grain_required(row, line, family, material_choice=material_choices.get(part_id)))
        group = by_thickness.setdefault(thickness, {"blanks": [], "drilling": []})
        group["blanks"].append(blank)
        if thickness >= DEFAULT_CNC_PARAMETERS.drilling_min_panel_mm and row["role"] not in DRILL_EXCLUSIONS:
            object_id = part_id.split(":", 1)[0]
            physical = row.get("quantity")
            if _positive(physical):
                physical *= row.get("scope_quantity", 1) * object_quantities.get(object_id, 1)
                group["drilling"].append(asdict(replace(blank, quantity=min(qty, ceil(physical)))))
    return by_thickness


def build_sheet_layout(report, plan):
    """Use the selected catalog stock and Parts references to save one layout per stock format."""
    parts = _parts_index(report)
    object_quantities = plan.get("object_quantities") or {}
    scope_by_requirement = {
        (oid, material["requirement_id"]): material.get("material_role")
        for oid, evidence in (plan.get("parts_check") or {}).items()
        for material in evidence.get("materials", ())
    }
    issues = [
        {"reference": f"{oid}:{material['requirement_id']}", "issue": "No selected sheet stock"}
        for oid, evidence in (plan.get("parts_check") or {}).items()
        for material in evidence.get("materials", ())
        if material["requirement_id"] in evidence.get("unpriced_requirements", ())
        and (material.get("family") in SHEET_FAMILIES or material.get("material_role") in PANEL_ROLES)
    ]
    groups = []
    for line in _sheet_lines(plan):
        dimensions = line.get("purchasable_dimensions") or {}
        l, w = dimensions.get("length_mm"), dimensions.get("width_mm")
        owners = sorted({row["object_id"] for row in line["allocations"]})
        if not all(_positive(d) and d > 2 * DEFAULT_CNC_PARAMETERS.trim_mm for d in (l, w)):
            issues.append({"reference": line["display_name"], "issue": "No usable sheet format", "object_ids": owners})
            continue
        family = _family(line)
        batch_groups = _line_groups(line, parts, object_quantities, scope_by_requirement, issues)
        for thickness, group in sorted(batch_groups.items()):
            if thickness > DEFAULT_CNC_PARAMETERS.automatic_profile_max_mm:
                issues.append({"reference": line["display_name"], "issue": "Thickness outside the CNC estimate profile",
                               "object_ids": sorted({blank.part_id.partition(":")[0] for blank in group["blanks"]})})
                continue
            stock_id = f"{line['candidate_id']}:{thickness:g}"
            batch = StockBatch(stock_id, "sheet", l, w, thickness, tuple(group["blanks"]),
                               common_cut=family == "melamine_faced_particleboard")
            layout = layout_joinable_sheet(batch)
            layout["placements"] = [asdict(placement) for placement in layout["placements"]]
            for part_id in layout["unplaced"]:
                issues.append({"reference": part_id, "issue": "Does not fit the selected sheet"})
            groups.append({
                "selection_key": line["selection_key"], "candidate_id": line["candidate_id"],
                "material": line["display_name"], "thickness_mm": thickness, "size_mm": [l, w],
                "layout": layout, "drilling": group["drilling"],
            })
    return {"version": LAYOUT_VERSION, "basis_sha256": sheet_layout_basis(plan), "groups": groups, "issues": issues}


def _workload(groups, *, tool_changes=None):
    layouts = []
    drilling = []
    for group in groups:
        layout = group["layout"]
        if layout is None:
            continue
        layouts.append({**layout, "placements": [Placement(**p) for p in layout["placements"]]})
        drilling.extend(Blank(**part) for part in group["drilling"])
    work = cnc_workload_from_layout(layouts, drilling_parts=drilling, tool_changes=tool_changes)
    return {key: value for key, value in work.items() if key != "batches"}


def _belongs(part_id, object_id):
    return part_id.partition(":")[0] == object_id


def describe_layout_issues(issues, layout, report):
    """Add source dimensions and sheet size to excluded parts."""
    parts = _parts_index(report)
    excluded = {}
    labels = {"carcass_side": "cabinet side", "carcass_back": "cabinet back"}
    for group in layout["groups"]:
        for reference, count in group["layout"]["unplaced"].items():
            part = parts.get(reference, {})
            role = part.get("role", "part")
            name = labels.get(role, role.replace("_", " "))
            block = part.get("block_id") or part.get("owner_id")
            where = f"{block}, " if block else ""
            dims = part.get("dimensions") or {}
            length, width = (dims.get(axis, {}).get("mm") for axis in ("length", "width"))
            size = f" ({length:g} × {width:g} mm)" if _positive(length) and _positive(width) else ""
            stock = " × ".join(f"{value:g}" for value in group["size_mm"])
            unit = name if count == 1 else f"{name}s"
            excluded[reference] = f"{where}{count} {unit}{size}. Selected sheet: {stock} mm."
    return [
        {**issue, "description": excluded.get(issue["reference"], f"{issue['reference']}: {issue['issue']}")}
        for issue in issues
    ]


def _object_layout(layout, object_id):
    if layout is None:
        return None
    placed = [row for row in layout["placements"] if _belongs(row["part_id"], object_id)]
    unplaced = {key: qty for key, qty in layout["unplaced"].items() if _belongs(key, object_id)}
    if not placed and not unplaced:
        return None
    occupied = defaultdict(float)
    for row in layout["placements"]:
        occupied[row["sheet"]] += row["length"] * row["width"]
    sheet_share = sum(row["length"] * row["width"] / occupied[row["sheet"]] for row in placed)
    perimeter = sum(2 * (row["length"] + row["width"]) for row in placed) / 1000
    common = 0
    if layout["common_m"]:
        credits = shared_cut_credits([Placement(**row) for row in layout["placements"]], layout["cutter_mm"])
        common = sum(value for part, value in credits.items() if _belongs(part, object_id))
    cut = perimeter - common
    return {
        **layout, "stock_count": sheet_share, "blank_count": len(placed),
        "batch_share": sheet_share / layout["stock_count"] if layout["stock_count"] else 0,
        "placements": placed, "unplaced": unplaced, "perimeter_m": perimeter, "common_m": common,
        "cut_m": cut, "path_m": cut * layout["passes"],
        "splits": [row for row in layout["splits"] if _belongs(row["part_id"], object_id)],
    }


def _object_work(groups, object_id):
    projected = []
    for group in groups:
        layout = _object_layout(group["layout"], object_id)
        if layout is None:
            continue
        projected.append({
            **group, "layout": layout,
            "drilling": [row for row in group["drilling"] if _belongs(row["part_id"], object_id)],
        })
    work = _workload(projected, tool_changes=0)
    active = [group["layout"] for group in groups if group["layout"]["stock_count"]]
    stock_total = sum(row["stock_count"] for row in active)
    if stock_total:
        changes = max(0, len({row["cutter_mm"] for row in active}) - 1)
        change_minutes = changes * DEFAULT_CNC_PARAMETERS.tool_change_min * work["sheet_count"] / stock_total
        for key in ("tool_change_minutes", "manual_minutes", "machine_minutes"):
            work[key] += change_minutes
    return projected, work


def _file_preparation(groups, operator_rate, parameters):
    # The saved layout retains Parts Check IDs on every copy and joined segment.
    positions = set()
    for group in groups:
        saved_layout = group["layout"]
        if saved_layout is not None:
            positions.update(row["part_id"] for row in saved_layout["placements"])
            positions.update(saved_layout["unplaced"])
    minutes = parameters.reference_minutes * len(positions) / parameters.reference_positions
    return {
        "position_count": len(positions),
        "minutes": minutes,
        "operator_ex_vat": round(minutes / 60 * operator_rate, 2),
        "supplier_includes_preparation": parameters.supplier_includes_preparation,
    }


def _edge_banding(plan, object_id, parameters):
    by_object = plan.get("edge_runs_by_object") or {}
    runs = by_object.get(object_id, ()) if object_id is not None else (
        run for rows in by_object.values() for run in rows
    )
    metres_by_tape = Counter()
    side_count = 0
    for row in runs:
        metres_by_tape[row["tape_kind"], row["tape_width_mm"]] += row["metres"]
        side_count += row["sides"]
    metres = round(sum(metres_by_tape.values()), 6)
    minutes = (
        parameters.setup_minutes + metres / parameters.feed_metres_per_minute
        + side_count * parameters.handling_seconds_per_side / 60
    ) if metres else 0
    supplier_rows = [
        {"tape_kind": tape, "tape_width_mm": width, "metres": round(length, 6),
         "rate_ex_vat": SUPPLIER_EDGE_RATE_PER_M.get((tape, width))}
        for (tape, width), length in sorted(metres_by_tape.items())
    ]
    return {
        "metres": metres, "sides": side_count, "minutes": round(minutes, 3),
        "in_house_ex_vat": round(minutes * parameters.operator_gross_ils_per_hour * (1 + EMPLOYER_LOAD) / 60, 2),
        "supplier_rates": supplier_rows,
        "supplier_ex_vat": round(sum(row["metres"] * row["rate_ex_vat"]
                                    for row in supplier_rows if row["rate_ex_vat"] is not None), 2),
        "supplier_unpriced_metres": round(sum(row["metres"] for row in supplier_rows
                                             if row["rate_ex_vat"] is None), 6),
        "supplier_includes_tape": SUPPLIER_EDGE_RATE_INCLUDES_TAPE,
    }


def _edge_stock_cost(plan, object_id, metres):
    """Use the existing tape purchase allocations, including shared rolls."""
    if not metres:
        return 0, True
    expected = {
        (oid, material["requirement_id"])
        for oid, parts in (plan.get("parts_check") or {}).items()
        if object_id is None or oid == object_id
        for material in parts.get("materials", ())
        if material.get("material_role") == EDGE_FAMILY
    }
    allocated = {
        (row["object_id"], row["material_requirement_id"])
        for line in plan.get("lines", ())
        if _family(line) == EDGE_FAMILY and line.get("currency") == "ILS"
        for row in line["allocations"]
        if object_id is None or row["object_id"] == object_id
    }
    costs = {
        (row["object_id"], row["material_requirement_id"]): row["cost_ex_vat"]
        for row in plan.get("object_material_costs", ())
        if (row["object_id"], row["material_requirement_id"]) in allocated
    }
    return (round(sum(costs.values()), 2) if costs else None, bool(expected) and expected <= costs.keys())


def calculate_labor_v1(
    layout, plan, *, machine_rate=None, object_id=None, operator_gross_rate=None,
    file_preparation_parameters=DEFAULT_CNC_FILE_PREPARATION,
    edge_parameters=DEFAULT_EDGE_BANDING,
):
    """Compare CNC work and purchasing for the same parts, without duplicate stock charges."""
    if layout.get("version") != LAYOUT_VERSION or layout["basis_sha256"] != sheet_layout_basis(plan):
        raise ValueError("The saved CNC layout and current material plan have different quantities or stock")
    priced_lines = {line["selection_key"]: line for line in _sheet_lines(plan)}
    groups = layout["groups"]
    issues = layout["issues"]
    if object_id is None:
        work = _workload(groups)
    else:
        groups, work = _object_work(groups, object_id)
        stock_names = {line["display_name"] for line in priced_lines.values()
                       if any(row["object_id"] == object_id for row in line["allocations"])}
        issues = [
            row for row in issues
            if (object_id in row["object_ids"] if "object_ids" in row
                else _belongs(row["reference"], object_id) or row["reference"] in stock_names)
        ]
    gross_rate = OPERATOR_RATE if operator_gross_rate is None else operator_gross_rate
    internal = in_house_cost(work, gross_rate_per_hour=gross_rate, machine_rate_per_hour=machine_rate)
    machine = internal["machine_cost"]
    operator_hours = ceil(round(internal["labor_hours"], 9))
    operator_rate = gross_rate * (1 + EMPLOYER_LOAD)
    operator = round(operator_hours * operator_rate, 2)
    file_preparation = _file_preparation(groups, operator_rate, file_preparation_parameters)
    shop_rows = []
    supplier_rows = []
    for group in groups:
        saved_layout = group["layout"]
        line = priced_lines[group["selection_key"]]
        price = line["price_per_purchase_unit"] if line["currency"] == "ILS" else None
        stock_is_assumed = (
            line.get("authority") == "assumption"
            or line["selection_key"].startswith("assumption:")
        )
        detail = {"material": group["material"], "thickness_mm": group["thickness_mm"], "size_mm": group["size_mm"]}
        if saved_layout is not None:
            sheets = saved_layout["stock_count"]
            usable_stock_rate = price if _positive(price) and not stock_is_assumed else None
            specs = line.get("label_specifications") or {}
            shop_rows.append({
                **detail, "sheets": sheets, "blanks": saved_layout["blank_count"],
                "stock_ex_vat": round(sheets * usable_stock_rate, 2) if sheets and usable_stock_rate else None,
                "stock_is_assumed": stock_is_assumed,
                "stock_price_is_estimated": (
                    (line.get("label_specifications") or {}).get("cnc_price_basis") == "reference_price_per_m2"
                ),
                "cut_m": saved_layout["cut_m"], "path_m": saved_layout["path_m"],
            })
            if sheets:
                if stock_is_assumed:
                    rate, basis = None, "quote_required"
                else:
                    rate, basis = supplier_sheet_rate(
                        _family(line), thickness_mm=group["thickness_mm"], size_mm=group["size_mm"],
                        specs=specs, stock_rate=usable_stock_rate, stock_name=group["material"],
                        variant=line["selection_key"].rpartition("|variant=")[2], stock_authority=line.get("authority"),
                    )
                supplier_rows.append({
                    **detail, "sheets": sheets, "rate_ex_vat": rate, "basis": basis,
                    "bundle_ex_vat": round(sheets * rate, 2) if rate is not None else None,
                })
    priced_bundles = [row["bundle_ex_vat"] for row in supplier_rows if row["bundle_ex_vat"] is not None]
    supplier = {
        "materials": supplier_rows,
        "unpriced_sheets": sum(row["sheets"] for row in supplier_rows if row["rate_ex_vat"] is None),
        "drilling_rate": SUPPLIER_MACHINING_RATE,
        "bundle_ex_vat": round(sum(priced_bundles), 2) if priced_bundles else None,
        "machining_ex_vat": work["drilled_part_count"] * SUPPLIER_MACHINING_RATE,
    }
    edging = _edge_banding(plan, object_id, edge_parameters)
    tape_cost, tape_cost_complete = _edge_stock_cost(plan, object_id, edging["metres"])
    return {
        "version": LABOR_VERSION, "work": work, "issues": issues, "file_preparation": file_preparation,
        "supplier_profile_version": SUPPLIER_PROFILE_VERSION,
        "edge_banding": {**edging, "tape_stock_ex_vat": tape_cost, "tape_stock_complete": tape_cost_complete},
        "unplaced_blanks": sum(sum(group["layout"]["unplaced"].values()) for group in groups),
        "joined_parts": [row for group in groups for row in group["layout"].get("splits", ())],
        "in_house": {
            "operator_ex_vat": operator, "operator_rate": operator_rate, "operator_hours": operator_hours,
            "machine_ex_vat": machine, "machine_rate": machine_rate, "materials": shop_rows,
        },
        "subcontractor": supplier,
    }


# Shared by Object Detail and persisted V3.1 Self Cost.

DISPLAY_HOURLY_RATE = Decimal("50")
DISPLAY_PAYROLL_SHARE = Decimal("0.25")
_LOG = logging.getLogger(__name__)

def labor_pay_metrics(hours, *, partial=False):
    if hours is None:
        return None
    hours = Decimal(str(hours))
    pay = (hours * DISPLAY_HOURLY_RATE).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    taxes = (pay * DISPLAY_PAYROLL_SHARE).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    return {'hours': hours, 'pay': pay, 'taxes': taxes, 'total': pay + taxes, 'partial': partial}


def sheet_pay_metrics(result):
    route = result.get('in_house_route', 'cnc')
    work = result['work']
    edge = result.get('cnc_edging', {'minutes': result['edge_banding']['minutes']})
    if not work['blank_count'] and not result['file_preparation']['minutes'] and not result['edge_banding']['metres']:
        return labor_pay_metrics(0, partial=bool(result['issues']))
    if route is None:
        return None
    partial = bool(result['issues'] or result['unplaced_blanks'])
    if route == 'panel_saw':
        saw = result['panel_saw']
        minutes = (saw['preparation_minutes'] + sum(saw['saw'].values()) + sum(saw['drilling'].values())
                   + saw['helper_minutes'] + saw['edging']['minutes'])
        partial |= bool(saw['unplaced'] or saw['geometry_review'] or saw['edging'].get('unestimated'))
        return labor_pay_metrics(Decimal(str(minutes)) / 60, partial=partial)
    hours = (Decimal(str(result['in_house']['operator_hours']))
             + Decimal(str(result['file_preparation']['minutes'])) / 60
             + Decimal(str(edge['minutes'])) / 60)
    return labor_pay_metrics(hours, partial=partial or bool(edge.get('unestimated')))


def object_labor_metrics(state, *, quantity=1, overrides=None):
    overrides = overrides or {}
    def manual(block, calculated):
        return (labor_pay_metrics(Decimal(str(overrides[block])) * Decimal(str(quantity)))
                if block in overrides else calculated)
    sheet = manual('sheet-processing', sheet_pay_metrics(state['result'])) if state['status'] == 'ready' else None
    assembly = state.get('assembly')
    assembled = None
    if assembly is not None:
        partial = bool(assembly['common_roles_for_review'] or any(block['issues'] for block in assembly['blocks']))
        assembled = manual('assembly', labor_pay_metrics(assembly['planned_minutes'] * Decimal(str(quantity)) / 60, partial=partial))
    known = [metrics for metrics in (sheet, assembled) if metrics is not None]
    total = None
    if known:
        total = {key: sum(item[key] for item in known) for key in ('hours', 'pay', 'taxes', 'total')}
        total['partial'] = len(known) != 2 or any(item['partial'] for item in known)
    return sheet, assembled, total


def load_object_labor(client, *, identity, parts_loader=None, plan_loader=None, machinery_loader=None, plan=None, parts_result=None):
    from use_cases.estimation_parts_check_runtime import load_parts_check
    from db.repositories import fetch_rfq_estimate_material_plan
    from use_cases.machinery import load_sheet_processing_machinery
    from use_cases.block_assembly import calculate_block_assembly
    from observability.runtime import report_runtime_failure
    parts_loader = parts_loader or load_parts_check
    plan_loader = plan_loader or fetch_rfq_estimate_material_plan
    machinery_loader = machinery_loader or load_sheet_processing_machinery
    company_id, run_id, estimate_id, object_id = identity
    params = {"client": client, "company_id": company_id, "run_id": run_id, "estimate_id": estimate_id}
    parts = parts_result if parts_result is not None else parts_loader(**params)
    if parts["status"] != "ready":
        return {"status": parts["status"]}
    report = json.loads(parts["payload"])
    if object_id not in report["objects"]:
        return {"status": "unavailable"}
    assembly = None
    try:
        assembly = calculate_block_assembly(report, object_id=object_id)
    except Exception as exc:
        report_runtime_failure("assembly.calculate", exc, rfq_run_id=run_id, estimate_id=estimate_id, object_id=object_id)
        _LOG.exception("Could not calculate Block Assembly for estimate %s", estimate_id)
    try:
        sheet = _load_object_sheet(client, report, company_id=company_id, estimate_id=estimate_id, object_id=object_id, plan_loader=plan_loader, machinery_loader=machinery_loader, plan=plan)
    except Exception as exc:
        report_runtime_failure("cnc.calculate", exc, rfq_run_id=run_id, estimate_id=estimate_id, object_id=object_id)
        _LOG.exception("Could not calculate Sheet Processing for estimate %s", estimate_id)
        sheet = {"status": "read_failed"}
    return {**sheet, "assembly": assembly}


def _load_object_sheet(client, report, *, company_id, estimate_id, object_id, plan_loader, machinery_loader, plan=None):
    from use_cases.sheet_processing import calculate_sheet_processing
    if plan is None:
        rows = plan_loader(client, estimate_id)
        if rows.empty:
            return {"status": "waiting_for_materials"}
        plan = rows.iloc[0].get("plan_payload") or {}
    if plan.get("status") not in {"planned", "needs_review"}:
        return {"status": "waiting_for_materials"}
    source = plan.get("parts_check_source") or {}
    if not source or any(source.get(k) != report.get(k) for k in (
        "run_id", "estimate_id", "input_ids", "source_audit_sha256", "overlay_revision"
    )):
        return {"status": "different_revision"}
    layout = report.get("sheet_layout") or {}
    if layout.get("version") != LAYOUT_VERSION or layout.get("basis_sha256") != sheet_layout_basis(plan):
        layout = build_sheet_layout(report, plan)
    machinery = machinery_loader(client, company_id)
    result = calculate_sheet_processing(
        report, layout, plan, object_id=object_id,
        machinery={**machinery, 'cnc_operator_wage': float(DISPLAY_HOURLY_RATE)},
    )
    result["issues"] = describe_layout_issues(result["issues"], layout, report)
    return {"status": "ready", "result": result}
