"""Saved panel layouts and the two CNC routes in Labor V1."""

from collections import Counter, defaultdict
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import ceil, isfinite

from use_cases.wood_cnc_calculation import (
    DEFAULT_CNC_PARAMETERS, Blank, Placement, StockBatch, cnc_workload_from_layout,
    in_house_cost, layout_cutting, shared_cut_credits,
)


LABOR_VERSION = "Labor V1.2"
LAYOUT_VERSION = "cnc_sheet_layout_v1"
SHEET_FAMILIES = {
    "mdf_hdf", "faced_mdf", "fibreboard_hardboard", "particleboard",
    "melamine_faced_particleboard", "plywood", "plywood_special",
}
PLINTH_ROLES = {"plinth_visible_run", "plinth_front", "plinth_return"}
SPLIT_ROLES = PLINTH_ROLES | {"carcass_back", "frame_backing"}
DRILL_EXCLUSIONS = SPLIT_ROLES | {"drawer_box_bottom"}
PANEL_ROLES = {"carcass_sheet", "backing_sheet", "internal_sheet", "visible_sheet", "worktop_substrate"}
SUPPLIER_SHEET = (2440, 1220)
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


def _cut_stock(batch, split_allowed):
    """Split only approved rear or plinth roles. Surface direction is preserved."""
    margin = 2 * DEFAULT_CNC_PARAMETERS.trim_mm
    usable = batch.length_mm - margin, batch.width_mm - margin
    blanks = []
    splits = []
    for blank in batch.blanks:
        dims = blank.length_mm, blank.width_mm
        orientations = (dims, dims[::-1]) if blank.rotation_allowed else (dims,)
        if blank.part_id not in split_allowed or any(a <= usable[0] and b <= usable[1] for a, b in orientations):
            blanks.append(blank)
            continue
        # A single seam direction keeps the construction and edge treatment legible.
        options = []
        for l, w in orientations:
            if w <= usable[1]:
                options.append((ceil(l / usable[0]), l, w, "length"))
            if l <= usable[0]:
                options.append((ceil(w / usable[1]), l, w, "width"))
        pieces, length, width, axis = min(options, default=(0, *dims, "length"))
        if 2 <= pieces <= 16:
            l, w = (length / pieces, width) if axis == "length" else (length, width / pieces)
            blanks.append(replace(blank, length_mm=l, width_mm=w, quantity=blank.quantity * pieces))
            splits.append({"part_id": blank.part_id, "pieces_per_part": pieces, "length_mm": l, "width_mm": w})
        else:
            blanks.append(blank)
    return replace(batch, blanks=tuple(blanks)), splits


def _placed(batch, split_allowed):
    batch, splits = _cut_stock(batch, split_allowed)
    layouts = [layout_cutting(batch)]
    if any(blank.rotation_allowed for blank in batch.blanks):
        layouts.append(layout_cutting(batch, rotate_first=True))
    layout = min(layouts, key=lambda row: (sum(row["unplaced"].values()), row["stock_count"], row["path_m"]))
    return {**layout, "placements": [asdict(placement) for placement in layout["placements"]], "splits": splits}


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
        group = by_thickness.setdefault(thickness, {"blanks": [], "drilling": [], "split_allowed": set()})
        group["blanks"].append(blank)
        if row["role"] in SPLIT_ROLES:
            group["split_allowed"].add(part_id)
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
            layout = _placed(batch, group["split_allowed"])
            for part_id in layout["unplaced"]:
                issues.append({"reference": part_id, "issue": "Does not fit the selected sheet"})
            standard_supplier = (family == "melamine_faced_particleboard" and thickness == 17
                                 and w == 1220 and l in (2400, 2440))
            supplier_layout = layout if (l, w) == SUPPLIER_SHEET else None
            if standard_supplier and supplier_layout is None:
                supplier_layout = _placed(replace(batch, length_mm=SUPPLIER_SHEET[0]), group["split_allowed"])
            groups.append({
                "selection_key": line["selection_key"], "candidate_id": line["candidate_id"],
                "material": line["display_name"], "thickness_mm": thickness, "size_mm": [l, w],
                "layout": layout, "drilling": group["drilling"],
                "supplier_layout": supplier_layout if standard_supplier else None,
            })
    return {"version": LAYOUT_VERSION, "basis_sha256": sheet_layout_basis(plan), "groups": groups, "issues": issues}


def _workload(groups, layout_key, *, tool_changes=None):
    layouts = []
    drilling = []
    for group in groups:
        layout = group[layout_key]
        if layout is None:
            continue
        layouts.append({**layout, "placements": [Placement(**p) for p in layout["placements"]]})
        drilling.extend(Blank(**part) for part in group["drilling"])
    work = cnc_workload_from_layout(layouts, drilling_parts=drilling, tool_changes=tool_changes)
    return {key: value for key, value in work.items() if key != "batches"}


def _belongs(part_id, object_id):
    return part_id.partition(":")[0] == object_id


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
        supplier = _object_layout(group["supplier_layout"], object_id)
        if layout is None and supplier is None:
            continue
        projected.append({
            **group, "layout": layout, "supplier_layout": supplier,
            "drilling": [row for row in group["drilling"] if _belongs(row["part_id"], object_id)],
        })
    work = _workload(projected, "layout", tool_changes=0)
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
        work = _workload(groups, "layout")
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
    operator = round(internal["labor_hours"] * OPERATOR_RATE * (1 + EMPLOYER_LOAD), 2)
    shop_rows, supplier_rows = [], []
    for group in groups:
        saved_layout = group["layout"]
        line = priced_lines[group["selection_key"]]
        price = line["price_per_purchase_unit"] if line["currency"] == "ILS" else None
        detail = {"material": group["material"], "thickness_mm": group["thickness_mm"], "size_mm": group["size_mm"]}
        if saved_layout is not None:
            sheets = saved_layout["stock_count"]
            shop_rows.append({
                **detail, "sheets": sheets, "blanks": saved_layout["blank_count"],
                "stock_ex_vat": round(sheets * price, 2) if _positive(price) and sheets else None,
                "stock_is_assumed": line["selection_key"].startswith("assumption:"),
                "cut_m": saved_layout["cut_m"], "path_m": saved_layout["path_m"],
            })
        supplier = group["supplier_layout"]
        if not supplier or not supplier["stock_count"]:
            supplier_rows.append({**detail, "sheets": None, "bundle_ex_vat": None, "machining_ex_vat": None,
                                  "status": "Supplier quote required" if not supplier else "Supplier format does not fit"})
            continue
        drills = _workload([group], "supplier_layout")["drilled_part_count"]
        sheet_charge = round(supplier["stock_count"] * SUPPLIER_SHEET_RATE, 2)
        supplier_rows.append({
            **detail, "size_mm": list(SUPPLIER_SHEET), "sheets": supplier["stock_count"], "drilled_parts": drills,
            "bundle_ex_vat": sheet_charge, "machining_ex_vat": drills * SUPPLIER_MACHINING_RATE,
            "status": "Israel standard estimate · placed parts only" if supplier["unplaced"] else "Israel standard estimate",
        })
    return {
        "version": LABOR_VERSION, "work": work, "issues": issues,
        "in_house": {"operator_ex_vat": operator, "machine_ex_vat": machine, "materials": shop_rows},
        "subcontractor": supplier_rows,
    }
