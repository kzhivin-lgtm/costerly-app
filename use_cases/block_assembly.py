"""Estimate shop assembly of one item from its saved Parts Check."""

from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite


ACTIVE_MINUTES = {
    "kit_handling": 2, "carcass": 14, "back": 4, "fixed_panel_or_shelf": 4,
    "drawer_box": 8, "drawer_runner_installation": 6, "drawer_runner_adjustment": 5, "drawer_front": 5,
    "shelf_runner_installation": 6, "shelf_runner_check": 1,
    "hinge_and_plate": 2, "door_fitting": 5, "lift_kit": 8, "lift_front_fitting": 5,
    "push_latch": 3, "bench_setup": 6,
}
MANUAL_PACE = Decimal("1.25")
WORKING_SHARE = Decimal("0.80")
HOURLY_BASE_ILS = Decimal("50")
_FIXED_ROLES = ("fixed_panel", "fixed_open_shelf", "drawer_bay_divider")
_CARCASS_ROLES = ("carcass_side", "carcass_top", "carcass_bottom")
_SLIDE_ROLES = ("drawer_slide", "pull_out_shelf_slide")
_SUPPORTED_ROLES = frozenset((
    *_CARCASS_ROLES, *_FIXED_ROLES, *_SLIDE_ROLES, "carcass_back",
    "drawer_box_side", "drawer_box_end", "drawer_box_bottom", "drawer_front",
    "pull_out_shelf", "hinge", "door_front", "gas_lift", "lift_up_front", "push_latch",
))
HARDWARE_OPERATIONS = frozenset({'drawer_runner_installation', 'drawer_runner_adjustment',
    'shelf_runner_installation', 'shelf_runner_check', 'hinge_and_plate', 'door_fitting', 'drawer_front',
    'lift_kit', 'lift_front_fitting', 'push_latch'})


def partition_block_assembly(result):
    """Partition existing operations without adding a norm or changing original data."""
    partitions = []
    for hardware in (False, True):
        blocks = []
        for block in result.get('blocks', ()):
            operations = [op for op in block.get('operations', ())
                          if (op['operation'] in HARDWARE_OPERATIONS) == hardware]
            active = sum(op['active_minutes'] for op in operations)
            planned = _planned_minutes(active)
            blocks.append({**block, 'operations': operations, 'active_minutes': active,
                           'planned_minutes': planned, 'base_labor_ils': _labor_cost(planned)})
        planned = sum((block['planned_minutes'] for block in blocks), Decimal(0))
        if not blocks and not hardware:
            planned = Decimal(str(result['planned_minutes']))
        partitions.append({**result, 'blocks': blocks, 'active_minutes': sum(b['active_minutes'] for b in blocks),
                           'planned_minutes': planned, 'base_labor_ils': _labor_cost(planned)})
    return tuple(partitions)


def _whole_quantity(value):
    return type(value) in (int, float) and isfinite(value) and value > 0 and int(value) == value


def _block_operations(parts, duplicate_refs):
    counts = Counter()
    issues = []
    for part in parts:
        role = part.get("role")
        if role not in _SUPPORTED_ROLES:
            continue
        if (role, part.get("instance_ref")) in duplicate_refs:
            issues.append(f"{role}: duplicate part evidence")
            continue
        quantity, repeats = part.get("quantity"), part.get("scope_quantity", 1)
        if not _whole_quantity(quantity) or not _whole_quantity(repeats):
            issues.append(f"{role}: quantity unresolved")
            continue
        count = int(quantity) * int(repeats)
        if role in _SLIDE_ROLES and part.get("unit") in ("pair", "set"):
            count *= 2
        counts[role] += count

    side_pairs, side_remainder = divmod(counts["carcass_side"], 2)
    tops, bottoms = counts["carcass_top"], counts["carcass_bottom"]
    carcasses = min(side_pairs, tops, bottoms)
    if side_remainder or side_pairs != tops or side_pairs != bottoms:
        issues.append("Carcass panels do not form complete sets")
    drawer_sides, side_remainder = divmod(counts["drawer_box_side"], 2)
    drawer_ends, end_remainder = divmod(counts["drawer_box_end"], 2)
    drawer_bottoms = counts["drawer_box_bottom"]
    drawers = min(drawer_sides, drawer_ends, drawer_bottoms)
    if side_remainder or end_remainder or drawer_sides != drawer_ends or drawer_sides != drawer_bottoms:
        issues.append("Drawer panels do not form complete boxes")
    drawer_pairs, drawer_remainder = divmod(counts["drawer_slide"], 2)
    shelf_pairs, shelf_remainder = divmod(counts["pull_out_shelf_slide"], 2)
    if drawer_remainder or drawer_pairs != drawers or drawers != counts["drawer_front"]:
        issues.append("Drawer boxes, fronts or slide pairs need review")
    if shelf_remainder or shelf_pairs != counts["pull_out_shelf"]:
        issues.append("Pull-out shelves or slide pairs need review")

    operations = {
        "carcass": carcasses, "back": counts["carcass_back"],
        "fixed_panel_or_shelf": sum(counts[role] for role in _FIXED_ROLES),
        "drawer_box": drawers, "drawer_front": counts["drawer_front"],
        "drawer_runner_installation": drawer_pairs, "drawer_runner_adjustment": drawer_pairs,
        "shelf_runner_installation": shelf_pairs, "shelf_runner_check": shelf_pairs,
        "hinge_and_plate": counts["hinge"], "door_fitting": counts["door_front"],
        "lift_kit": counts["gas_lift"], "lift_front_fitting": counts["lift_up_front"],
        "push_latch": counts["push_latch"],
    }
    if any(operations.values()):
        operations.update(bench_setup=1, kit_handling=1)
    return {key: operations[key] for key in ACTIVE_MINUTES if operations.get(key)}, list(dict.fromkeys(issues))


def _planned_minutes(active_minutes):
    return Decimal(active_minutes) * MANUAL_PACE / WORKING_SHARE


def _labor_cost(planned_minutes):
    return (planned_minutes * HOURLY_BASE_ILS / 60).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_block_assembly(parts_report, *, object_id):
    """Keep Block ownership and distinguish confirmed counts from unpriced work."""
    source = parts_report["objects"][object_id]
    duplicate_refs = {(issue.get("role"), issue.get("source_ref"))
                      for issue in source.get("inventory_issues", ())
                      if issue.get("reason") == "duplicate_part_evidence" and issue.get("source_ref")}
    scoped = {block["id"]: [] for block in source.get("blocks", ())}
    common_roles = set()
    for part in source.get("parts", ()):
        if block_id := part.get("block_id"):
            scoped.setdefault(block_id, []).append(part)
        elif part.get("role") in _SUPPORTED_ROLES:
            common_roles.add(part["role"])

    blocks = []
    for block_id, parts in scoped.items():
        operations, issues = _block_operations(parts, duplicate_refs)
        minutes = sum(ACTIVE_MINUTES[key] * count for key, count in operations.items())
        planned = _planned_minutes(minutes)
        blocks.append({
            "block_id": block_id, "active_minutes": minutes, "planned_minutes": planned,
            "base_labor_ils": _labor_cost(planned), "issues": issues,
            "operations": [
                {"operation": key, "quantity": count, "minutes_per_unit": ACTIVE_MINUTES[key],
                 "active_minutes": ACTIVE_MINUTES[key] * count}
                for key, count in operations.items()
            ],
        })
    active = sum(block["active_minutes"] for block in blocks)
    planned = _planned_minutes(active)
    return {
        "blocks": blocks, "active_minutes": active, "planned_minutes": planned,
        "base_labor_ils": _labor_cost(planned), "hourly_base_ils": HOURLY_BASE_ILS,
        "common_roles_for_review": sorted(common_roles),
    }
