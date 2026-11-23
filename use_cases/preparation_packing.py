"""Paid man-minutes for dispatch checking and dimension-based packing."""

from collections import Counter, defaultdict
from decimal import Decimal
from math import isfinite


VERSION = "preparation_packing_v1"
SIZE_LIMITS_MM = {"S": (600, 600, 400), "M": (1200, 800, 600), "L": (2000, 1200, 800)}
PACKING_MINUTES = {"S": 10, "M": 15, "L": 20, "XL": 25}
INTERFACE_MINUTES = 30


def _positive(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def packing_size(dimensions):
    """Smallest inclusive three-axis class, independent of orientation."""
    if len(dimensions) != 3 or not all(_positive(value) for value in dimensions):
        return None
    sides = sorted(dimensions, reverse=True)
    return next((name for name, limits in SIZE_LIMITS_MM.items()
                 if all(side <= limit for side, limit in zip(sides, limits))), "XL")


def _dimensions(part):
    return {key: value.get("mm") for key, value in part.get("dimensions", {}).items()
            if isinstance(value, dict)}


def packing_units(source):
    """Keep Block ownership, plus separate bundles of object-level loose parts."""
    units = []
    block_ids = {block["id"] for block in source.get("blocks", ())}
    parts = defaultdict(list)
    for part in source.get("parts", ()):
        parts[part.get("block_id") or part.get("owner_id")].append(part)
    for block in source.get("blocks", ()):
        envelope = block.get("envelope") or {}
        dims = {axis: envelope[axis].get("mm") if isinstance(envelope.get(axis), dict)
                else envelope.get(axis + "_mm") for axis in ("width", "height", "depth")}
        refs = {axis: envelope[axis].get("refs", []) if isinstance(envelope.get(axis), dict) else [] for axis in dims}
        basis = "saved_block_envelope"
        if not _positive(dims["depth"]):
            sides = [part for part in parts[block["id"]] if part.get("role") == "carcass_side"
                     and _positive(_dimensions(part).get("width"))]
            if sides:
                front = max((_dimensions(p).get("thickness") or 0 for p in parts[block["id"]]
                             if p.get("role") in {"drawer_front", "door_front", "lift_up_front"}), default=0)
                dims["depth"] = max(_dimensions(p)["width"] for p in sides) + front
                refs["depth"] = [p.get("instance_ref") or p.get("owner_id") for p in sides]
                basis = "saved_side_depth_plus_front_thickness"
        units.append({"id": block["id"], "kind": "block", "dimensions_mm": dims,
                      "quantity": block.get("quantity", 1), "basis": basis, "source_refs": refs})
    for owner, rows in parts.items():
        if owner is None or owner in block_ids:
            continue
        dimensions, valid = [], True
        for part in rows:
            d = _dimensions(part)
            sides = [d.get("length"), d.get("width"), d.get("thickness")]
            quantity = part.get("quantity", 1) * part.get("scope_quantity", 1) if _positive(part.get("quantity", 1)) and _positive(part.get("scope_quantity", 1)) else None
            if not all(_positive(v) for v in sides) or not _positive(quantity):
                valid = False
                break
            a, b, c = sorted(sides, reverse=True)
            dimensions.append((a, b, c * quantity))
        dims = ({"width": max(d[0] for d in dimensions), "height": max(d[1] for d in dimensions),
                 "depth": sum(d[2] for d in dimensions)} if valid and dimensions else {})
        units.append({"id": str(owner), "kind": "loose_bundle", "quantity": 1, "dimensions_mm": dims,
                      "basis": "stacked_saved_parts_bundle", "source_refs": [p.get("instance_ref") for p in rows]})
    return units


def calculate_preparation_packing(parts_report, *, object_id):
    """Never replace absent legacy interface evidence with zero connections."""
    source = parts_report["objects"][object_id]
    evidence = source.get("preparation_evidence") or {}
    units = packing_units(source)
    known_ids = {row["id"] for row in units}
    issues, counts, packed = [], Counter(), []
    for unit in units:
        quantity = unit["quantity"]
        if not _positive(quantity) or int(quantity) != quantity:
            issues.append({"unit_id": unit["id"], "reason": "packing_quantity_unresolved"})
            packed.append({**unit, "size": None, "minutes_per_unit": None, "man_minutes": None})
            continue
        size = packing_size([unit["dimensions_mm"].get(axis) for axis in ("width", "height", "depth")])
        if size is None:
            # An already known oversized axis proves XL without guessing the others.
            if all(v is None or _positive(v) for v in unit["dimensions_mm"].values()) and any(
                    _positive(v) and v > 2000 for v in unit["dimensions_mm"].values()):
                size = "XL"
            else:
                issues.append({"unit_id": unit["id"], "reason": "packing_dimensions_unresolved"})
        if size is not None:
            counts[size] += int(quantity)
            packed.append({**unit, "size": size, "minutes_per_unit": PACKING_MINUTES[size],
                           "man_minutes": PACKING_MINUTES[size] * int(quantity)})
        else:
            packed.append({**unit, "size": None, "minutes_per_unit": None, "man_minutes": None})
    interfaces, seen = [], {}
    for row in evidence.get("interfaces", ()):
        nodes = row.get("unit_ids", ())
        if len(nodes) != 2 or len(set(nodes)) != 2 or not set(nodes) <= known_ids or not row.get("source_refs"):
            issues.append({"reason": "invalid_interface_evidence"})
            continue
        key = (tuple(sorted(nodes)), row.get("interface_id", "block_mating"))
        if key in seen:
            existing = seen[key]
            for ref in row["source_refs"]:
                if ref not in existing["source_refs"]:
                    existing["source_refs"].append(ref)
            if existing["quantity"] != row.get("quantity", 1):
                issues.append({"reason": "interface_quantity_conflict", "unit_ids": sorted(nodes),
                               "quantities": [existing["quantity"], row.get("quantity", 1)]})
                existing["quantity"] = None
                existing["man_minutes"] = None
            continue
        quantity = row.get("quantity", 1)
        if not _positive(quantity) or int(quantity) != quantity:
            issues.append({"reason": "interface_quantity_unresolved", "unit_ids": sorted(nodes)})
            continue
        item = {**row, "quantity": int(quantity), "unit_ids": sorted(nodes),
                "source_refs": list(row["source_refs"]), "man_minutes": int(quantity) * INTERFACE_MINUTES}
        interfaces.append(item)
        seen[key] = item
    checking_known = (evidence.get("status") == "ready" or not units) and not any(
        "interface" in row["reason"] for row in issues)
    if not checking_known:
        issues.append({"reason": "interface_evidence_unavailable"})
    packing_minutes = sum(row["man_minutes"] for row in packed if row["man_minutes"] is not None)
    checking_minutes = sum(row["man_minutes"] for row in interfaces if row["man_minutes"] is not None)
    return {"version": VERSION, "time_basis": "planned_man_minutes", "packing_units": packed,
            "size_counts": dict(counts), "interfaces": interfaces, "interface_minutes": INTERFACE_MINUTES,
            "packing_minutes": packing_minutes, "checking_minutes": checking_minutes,
            "checking_known": checking_known, "packing_partial": any("packing_" in row["reason"] for row in issues),
            "packing_unit_count": len(units),
            "issues": issues, "planned_minutes": Decimal(packing_minutes + checking_minutes)}
