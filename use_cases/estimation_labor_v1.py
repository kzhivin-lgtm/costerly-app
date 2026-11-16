"""Saved panel layouts and the two CNC routes in Labor V1."""

from collections import Counter, defaultdict
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import ceil, isfinite

from use_cases.wood_cnc_calculation import (
    DEFAULT_CNC_PARAMETERS, Blank, Placement, StockBatch, cnc_workload_from_layout,
    in_house_cost, layout_joinable_sheet, shared_cut_credits,
)


LABOR_VERSION = "Labor V1.2.5"
LAYOUT_VERSION = "cnc_sheet_layout_v2"
SHEET_FAMILIES = {
    "mdf_hdf", "faced_mdf", "fibreboard_hardboard", "particleboard",
    "melamine_faced_particleboard", "plywood", "plywood_special",
}
PLINTH_ROLES = {"plinth_visible_run", "plinth_front", "plinth_return"}
SPLIT_ROLES = PLINTH_ROLES | {"carcass_back", "frame_backing"}
DRILL_EXCLUSIONS = SPLIT_ROLES | {"drawer_box_bottom"}
PANEL_ROLES = {"carcass_sheet", "backing_sheet", "internal_sheet", "visible_sheet", "worktop_substrate"}
SUPPLIER_SHEET_RATE = 245
SUPPLIER_MACHINING_RATE = 12
EMPLOYER_LOAD = 0.25
OPERATOR_RATE = 55


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


def _grain_required(row, line, family):
    visual = row.get("visual_stock") or {}
    return (family in {"plywood", "plywood_special"} or "veneer" in line["display_name"].casefold()
            or visual.get("surface") == "wood_grain"
            or any(surface.get("finish") == "wood_grain" for surface in row.get("finish_surfaces", ())))


def _line_groups(line, parts, object_quantities, scope_by_requirement, issues):
    quantities = Counter()
    sizes = {}
    for allocation in line["allocations"]:
        part_id = allocation["demand_id"].removesuffix(":assumption")
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
        blank = Blank(part_id, *sizes[part_id, thickness], qty, rotation_allowed=not _grain_required(row, line, family))
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


def calculate_labor_v1(layout, plan, *, machine_rate=None, object_id=None):
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
    internal = in_house_cost(work, gross_rate_per_hour=OPERATOR_RATE, machine_rate_per_hour=machine_rate)
    machine = internal["machine_cost"]
    operator_hours = ceil(round(internal["labor_hours"], 9))
    operator_rate = OPERATOR_RATE * (1 + EMPLOYER_LOAD)
    operator = round(operator_hours * operator_rate, 2)
    shop_rows = []
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
            shop_rows.append({
                **detail, "sheets": sheets, "blanks": saved_layout["blank_count"],
                "stock_ex_vat": (
                    round(sheets * price, 2)
                    if sheets and _positive(price) and not stock_is_assumed
                    else None
                ),
                "stock_is_assumed": stock_is_assumed,
                "stock_price_is_estimated": (
                    (line.get("label_specifications") or {}).get("cnc_price_basis") == "reference_price_per_m2"
                ),
                "cut_m": saved_layout["cut_m"], "path_m": saved_layout["path_m"],
            })
    supplier = {
        "sheet_rate": SUPPLIER_SHEET_RATE,
        "drilling_rate": SUPPLIER_MACHINING_RATE,
        "bundle_ex_vat": round(work["sheet_count"] * SUPPLIER_SHEET_RATE, 2),
        "machining_ex_vat": work["drilled_part_count"] * SUPPLIER_MACHINING_RATE,
    }
    return {
        "version": LABOR_VERSION, "work": work, "issues": issues,
        "unplaced_blanks": sum(sum(group["layout"]["unplaced"].values()) for group in groups),
        "joined_parts": [row for group in groups for row in group["layout"].get("splits", ())],
        "in_house": {
            "operator_ex_vat": operator, "operator_rate": operator_rate, "operator_hours": operator_hours,
            "machine_ex_vat": machine, "machine_rate": machine_rate, "materials": shop_rows,
        },
        "subcontractor": supplier,
    }
