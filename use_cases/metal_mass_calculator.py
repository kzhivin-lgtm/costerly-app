"""Deterministic mass conversion for Israel Reference metal prices per kg."""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Any, Mapping


_DENSITY_KG_PER_M3 = {
    "carbon steel": Decimal("7850"), "stainless steel": Decimal("8000"),
    "aluminium": Decimal("2700"), "copper": Decimal("8960"), "brass": Decimal("8500"),
}
_DEFAULT_WALL_MM = Decimal("1.5")


def _positive(value: Any) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except Exception:
        return None
    return number if number > 0 else None


def _numbers(value: Any) -> tuple[Decimal, ...]:
    return tuple(Decimal(item) for item in re.findall(r"\d+(?:\.\d+)?", str(value or "")))


def _width_thickness(specifications: Mapping[str, Any]) -> tuple[Decimal, Decimal] | None:
    value = specifications.get("width_thickness")
    if isinstance(value, Mapping):
        width, thickness = _positive(value.get("width_mm")), _positive(value.get("thickness_mm"))
        if width is not None and thickness is not None:
            return width, thickness
    return None


def kilograms_per_metre(*, family_code: str, specifications: Mapping[str, Any]) -> Decimal | None:
    """Return exact geometric mass per metre, or None when geometry is absent."""
    density = _DENSITY_KG_PER_M3.get(str(specifications.get("metal_type") or "").casefold())
    if density is None:
        return None
    area_mm2: Decimal | None = None
    if family_code == "metal_flat_bar":
        dimensions = _width_thickness(specifications)
        if dimensions:
            area_mm2 = dimensions[0] * dimensions[1]
    elif family_code == "metal_round_bar_rod_wire":
        diameter = _positive(specifications.get("diameter"))
        if diameter is not None:
            area_mm2 = Decimal("3.141592653589793") * diameter * diameter / Decimal("4")
    elif family_code in {"metal_tube", "metal_profile_angle_channel"}:
        section = str(specifications.get("section_profile") or "")
        values = _numbers(section)
        wall = _positive(specifications.get("wall_thickness")) or _DEFAULT_WALL_MM
        if section.startswith("round_tube_d") and values:
            outer = values[0]
            if outer > wall * 2:
                area_mm2 = Decimal("3.141592653589793") * (outer * outer - (outer - wall * 2) ** 2) / Decimal("4")
        elif (section.startswith("square_tube_") or section.startswith("rectangular_tube_")) and len(values) >= 2:
            outer_a, outer_b = values[:2]
            if outer_a > wall * 2 and outer_b > wall * 2:
                area_mm2 = outer_a * outer_b - (outer_a - wall * 2) * (outer_b - wall * 2)
        elif section.startswith("angle_") and len(values) >= 2:
            area_mm2 = wall * (values[0] + values[1] - wall)
    if area_mm2 is None:
        return None
    return area_mm2 * Decimal("1000") * density / Decimal("1000000000")


def kilograms_per_sheet(*, specifications: Mapping[str, Any], length_mm: Any, width_mm: Any) -> Decimal | None:
    density = _DENSITY_KG_PER_M3.get(str(specifications.get("metal_type") or "").casefold())
    thickness = _positive(specifications.get("thickness"))
    length, width = _positive(length_mm), _positive(width_mm)
    if density is None or thickness is None or length is None or width is None:
        return None
    return length * width * thickness * density / Decimal("1000000000")
