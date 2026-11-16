"""Choose purchase formats for oversized parts before the CNC layout is published."""

from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite

from use_cases.material_engine import cnc_sized_sheet_quantity, plan_material_purchases
from use_cases.wood_cnc_calculation import (
    DEFAULT_CNC_PARAMETERS, Blank, StockBatch, layout_joinable_sheet, sheet_fits_part,
)


WOOD_SHEET_FAMILIES = {
    "mdf_hdf", "faced_mdf", "fibreboard_hardboard", "particleboard",
    "melamine_faced_particleboard", "plywood", "plywood_special",
}
JOIN_FIRST = {"carcass_back", "frame_backing", "plinth_front", "plinth_return", "plinth_visible_run"}
_WIDE_LDSP_KEY = "melamine_faced_particleboard|thickness=17"
_OVERSIZE_LDSP_FORMATS = (
    (2750, 1220, "mazonit", "https://www.mazonit.co.il/prdFiles/melamin16.pdf"),
    (2800, 2070, "averbuch", "https://www.averbuch.co.il/images/ul240756/16df56d7e2629f1383324bc767e57ace.pdf"),
)


def _sheet_size(candidate):
    if candidate.purchase_kind != "sheet":
        return None
    dimensions = candidate.purchasable_dimensions or {}
    try:
        length, width = (float(dimensions[key]) for key in ("length_mm", "width_mm"))
    except (KeyError, TypeError, ValueError):
        return None
    if not all(isfinite(side) and side > 2 * DEFAULT_CNC_PARAMETERS.trim_mm for side in (length, width)):
        return None
    return length, width


def _part_blank(demand, part):
    return Blank(
        demand.demand_id, float(demand.length_mm), float(demand.width_mm), int(demand.quantity),
        rotation_allowed=bool(part["rotation_allowed"]),
    )


def _fits(candidate, blank):
    size = _sheet_size(candidate)
    return size and sheet_fits_part(
        blank.length_mm, blank.width_mm, *size, rotation_allowed=blank.rotation_allowed,
    )


def _oversize_candidate(stock, demand, candidates, blank):
    fitting = [
        candidates[key] for key in demand.compatible_candidate_ids
        if key in candidates and candidates[key].selection_key == stock.selection_key
        and candidates[key].currency == stock.currency
        and candidates[key].authority in {"company", "israel_reference"}
        and _fits(candidates[key], blank)
    ]
    def rank(option):
        size = _sheet_size(option)
        count = layout_joinable_sheet(StockBatch(
            option.candidate_id, "sheet", *size, 17.0, (blank,),
        ))["stock_count"]
        return option.authority != "company", count, Decimal(str(option.price_per_purchase_unit)), option.candidate_id

    if fitting:
        return min(fitting, key=rank)
    if stock.selection_key != _WIDE_LDSP_KEY or stock.currency != "ILS":
        return None
    # Catalogues document compatible formats. Estimate the stock cost from the
    # same material-only Israel Reference rate and keep the existing sheet-count priority.
    references = [
        candidates[key] for key in demand.compatible_candidate_ids
        if key in candidates and candidates[key].selection_key == stock.selection_key
        and candidates[key].authority == "israel_reference"
        and (candidates[key].label_specifications or {}).get("reference_stock_ils_per_m2")
    ]
    if not references:
        return None
    basis = min(references, key=lambda row: (
        Decimal(row.label_specifications["reference_stock_ils_per_m2"]), row.candidate_id,
    ))
    per_m2 = Decimal(basis.label_specifications["reference_stock_ils_per_m2"])
    estimates = []
    for length, width, vendor, source in _OVERSIZE_LDSP_FORMATS:
        if not sheet_fits_part(blank.length_mm, blank.width_mm, length, width, rotation_allowed=blank.rotation_allowed):
            continue
        area = Decimal(length * width) / 1_000_000
        estimates.append(replace(
            basis,
            candidate_id=f"{basis.reference_price_id}:{vendor}-{length}x{width}",
            display_name=f"LDSP, 17 mm, {length} × {width} mm (estimated price)",
            purchasable_dimensions={"length_mm": length, "width_mm": width},
            price_per_purchase_unit=(per_m2 * area).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            label_specifications={
                **basis.label_specifications, "cnc_format_source": source,
                "cnc_price_basis": "reference_price_per_m2",
            },
        ))
    return min(estimates, key=rank, default=None)


def _regular_stock(stock, line, by_id, parts, candidates):
    """Keep a regular format for the parts it can cover in a mixed-size group."""
    demand_ids = [allocation.demand_id for allocation in line.allocations]
    blanks = [_part_blank(by_id[key], parts[key]) for key in demand_ids if key in parts]
    if len(blanks) < 2:
        return stock
    length, width = _sheet_size(stock)
    common_ids = set(by_id[demand_ids[0]].compatible_candidate_ids)
    for key in demand_ids[1:]:
        common_ids.intersection_update(by_id[key].compatible_candidate_ids)
    regular = []
    for key in common_ids:
        option = candidates[key]
        size = _sheet_size(option)
        if (not size or size[0] * size[1] >= length * width or option.authority != stock.authority
                or option.currency != stock.currency or option.selection_key != stock.selection_key):
            continue
        fits_count = sum(bool(_fits(option, blank)) for blank in blanks)
        if 0 < fits_count < len(blanks):
            regular.append((-fits_count, Decimal(str(option.price_per_purchase_unit)), key, option))
    return min(regular, key=lambda entry: entry[:3])[3] if regular else stock


def _ensure_stock_count(line, candidates, demands, parts):
    candidate = candidates[line.candidate_id]
    locked = []
    thickness = 0.0
    for allocation in line.allocations:
        part = parts.get(allocation.demand_id)
        if part is None:
            continue
        demand = demands[allocation.demand_id]
        blank = _part_blank(demand, part)
        if not blank.rotation_allowed:
            locked.append(demand.demand_id)
        if demand.volume_mm3:
            thickness = max(thickness, float(demand.volume_mm3) / (
                blank.length_mm * blank.width_mm * blank.quantity
            ))
    if thickness > DEFAULT_CNC_PARAMETERS.automatic_profile_max_mm:
        return line
    candidate = replace(
        candidate, label_specifications={
            **dict(candidate.label_specifications or {}),
            "cnc_sheet_sizing": {"thickness_mm": thickness or 17.0, "locked_part_ids": sorted(locked)},
        },
    )
    candidates[candidate.candidate_id] = candidate
    quantity = cnc_sized_sheet_quantity(
        candidate, [demands[allocation.demand_id] for allocation in line.allocations], line.purchase_quantity,
    )
    return replace(line, purchase_quantity=quantity, total_cost=quantity * line.price_per_purchase_unit)


def route_oversized_cnc_parts(plan, *, demands, candidates, parts):
    """Keep regular stock and route only oversize parts to compatible larger stock."""
    by_id = {demand.demand_id: demand for demand in demands}
    revised = {}
    affected_keys = set()
    for line in plan.lines:
        stock = candidates[line.candidate_id]
        if stock.material_family not in WOOD_SHEET_FAMILIES or not _sheet_size(stock):
            continue
        stock = _regular_stock(stock, line, by_id, parts, candidates)
        oversize = False
        for allocation in line.allocations:
            part = parts.get(allocation.demand_id)
            if part is None:
                continue
            demand = by_id[allocation.demand_id]
            blank = _part_blank(demand, part)
            if _fits(stock, blank):
                continue
            oversize = True
            if part["role"] in JOIN_FIRST:
                continue
            alternate = _oversize_candidate(stock, demand, candidates, blank)
            if alternate is None:
                continue
            key = f"{line.selection_key}|cnc_stock={alternate.candidate_id}"
            candidate_id = f"{alternate.candidate_id}:cnc-oversize"
            candidates[candidate_id] = replace(alternate, selection_key=key, candidate_id=candidate_id)
            revised[demand.demand_id] = replace(demand, selection_key=key, compatible_candidate_ids=(candidate_id,))
            affected_keys.add(key)
        if oversize:
            affected_keys.add(line.selection_key)
            for allocation in line.allocations:
                original = by_id[allocation.demand_id]
                revised.setdefault(original.demand_id, replace(original, compatible_candidate_ids=(stock.candidate_id,)))
    if not revised:
        return plan
    by_id.update(revised)
    updated = plan_material_purchases(demands=tuple(by_id.values()), candidates=tuple(candidates.values()))
    return replace(updated, lines=tuple(
        _ensure_stock_count(line, candidates, by_id, parts)
        if line.selection_key in affected_keys else line
        for line in updated.lines
    ))
