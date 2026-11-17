"""Estimate a finished glass set from the physical pieces in Parts Check."""

from decimal import Decimal, ROUND_HALF_UP
from math import isfinite


GLASS_SET_REQUIREMENT = "cb-finished-glass-set"
GLASS_SET_NAME = "Finished glass set"
_GLASS_BOX_PANES = {
    "glass_box_lid": "Glass lid",
    "glass_box_bottom": "Glass lid",  # Earlier shelf-linked Parts Check reports called it a bottom.
    "glass_box_long_wall": "Long glass wall",
    "glass_box_end_wall": "End glass wall",
}
_CENT = Decimal("0.01")


def finished_glass_part(row, measurements, *, family, multiplier):
    role = row["role"]
    if role == "mirror_glass" or (role not in _GLASS_BOX_PANES and family != "glass"):
        return None
    name = str(row.get("material_hint") or "").strip().casefold()
    count = row.get("quantity")
    return {
        "label": _GLASS_BOX_PANES.get(role, role.replace("_", " ").capitalize()),
        **{f"{axis}_mm": measurements.get(axis, {}).get("mm") for axis in ("length", "width", "thickness")},
        "quantity": count * multiplier if type(count) in (int, float) and isfinite(count) and count > 0 else None,
        "tempered": "tempered" in name or "закал" in name,
        "standard_rectangle": role in _GLASS_BOX_PANES and name == "tempered glass",
    }


def finished_glass_set(parts):
    grouped = {}
    for part in parts:
        key = tuple(part[k] for k in ("label", "length_mm", "width_mm", "thickness_mm", "tempered", "standard_rectangle"))
        if key not in grouped:
            grouped[key] = dict(part)
        else:
            count = grouped[key]["quantity"]
            grouped[key]["quantity"] = None if count is None or part["quantity"] is None else count + part["quantity"]

    rows = []
    total = Decimal(0)
    for part in grouped.values():
        length, width, thickness, count = (part[k] for k in ("length_mm", "width_mm", "thickness_mm", "quantity"))
        standard = part["standard_rectangle"] and thickness == 4
        unit_price = line_total = None
        if standard and all(type(v) in (int, float) and isfinite(v) and v > 0 for v in (length, width, count)):
            a, b = Decimal(str(length)), Decimal(str(width))
            # Budget allowance covers stock, cut and tempering per m², full perimeter polish and piece handling.
            unit = a * b * Decimal(200) / 1_000_000 + 2 * (a + b) * Decimal(12) / 1000 + 8
            extended = (unit * Decimal(str(count))).quantize(_CENT, rounding=ROUND_HALF_UP)
            unit_price, line_total = float(unit.quantize(_CENT, rounding=ROUND_HALF_UP)), float(extended)
            total += extended
        processing = "Cut, polished edges, tempered" if line_total is not None else (
            "Tempered · quote required" if part["tempered"] else "Processing quote required"
        )
        rows.append({**part, "processing": processing, "unit_price": unit_price, "total": line_total})
    return {
        "parts": rows,
        "piece_count": sum(row["quantity"] for row in rows) if all(row["quantity"] is not None for row in rows) else None,
        "set_price": float(total) if rows and all(row["total"] is not None for row in rows) else None,
    }
