"""Resolve the physical dimensions of one supplier offer.

A company material answers what the item is. A supplier offer answers the
price of a purchasable unit of that item. The physical dimensions belong to
that offer because a supplier can sell the same plywood in 2440 x 1220 and
1520 x 1520 sheets at different prices.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence



def _positive_mm(value: object) -> int:
    try:
        parsed = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return int(round(parsed)) if parsed > 0 else 0


def _normalised_dimensions(value: Mapping[str, Any] | None) -> dict[str, int]:
    value = value or {}
    length = _positive_mm(value.get("length_mm"))
    width = _positive_mm(value.get("width_mm"))
    if length and width:
        return {"length_mm": max(length, width), "width_mm": min(length, width)}
    if length:
        return {"length_mm": length}
    return {}


def _metric_mm(value: str, unit: str) -> int:
    parsed = float(value.replace(",", "."))
    multiplier = {"mm": 1, "cm": 10, "m": 1000, "ft": 304.8}[unit]
    # Trade sheet formats are normally written nominally: 4 ft is catalogued
    # as 1220 mm, 5 ft as 1525 mm, not 1219.2 and 1524.0.
    return int(round((parsed * multiplier) / 5) * 5)


def _source_dimensions(
    text: object,
    *,
    allow_compact_sheet_span: bool,
    allow_linear_length: bool,
) -> dict[str, int]:
    """Extract a literal two-dimensional format from supplier wording.

    Supports mm, cm, metres and feet, including the common 4x8 notation. The
    A source-proved Israeli sheet notation such as ``3-100`` is read as
    3100 mm only for a family that is already known to be a sheet family.
    """
    value = str(text or "").casefold().replace("×", "x")
    # A linear profile can contain a cross-section such as ``40 x 20 x 2 mm``
    # alongside its purchasable stock length. Read the explicitly labelled
    # length first so the cross-section is never mistaken for a sheet format.
    if allow_linear_length:
        linear = re.search(
            r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(mm|cm|m|ft|feet|foot|')\s*"
            r"(?:length|long|אורך)(?!\w)",
            value,
        )
        if linear:
            unit = {"feet": "ft", "foot": "ft", "'": "ft"}.get(linear.group(2), linear.group(2))
            return {"length_mm": _metric_mm(linear.group(1), unit)}
    unit_pattern = r"(?P<unit>mm|cm|m|ft|feet|foot|')"
    number = r"(?P<left>\d+(?:[.,]\d+)?)"
    right = r"(?P<right>\d+(?:[.,]\d+)?)"
    explicit = re.search(
        rf"{number}\s*{unit_pattern}\s*x\s*{right}\s*(?P=unit)", value
    )
    if not explicit:
        explicit = re.search(
            rf"{number}\s*x\s*{right}\s*(?P<unit>mm|cm|m|ft|feet|foot|')", value
        )
    if explicit:
        unit = str(explicit.group("unit"))
        unit = {"feet": "ft", "foot": "ft", "'": "ft"}.get(unit, unit)
        left = _metric_mm(explicit.group("left"), unit)
        right_value = _metric_mm(explicit.group("right"), unit)
        return _normalised_dimensions({"length_mm": left, "width_mm": right_value})

    nominal_feet = re.search(r"(?<!\d)([3-8])\s*x\s*(1[0-2]|[3-9])(?!\d)", value)
    if nominal_feet:
        return _normalised_dimensions(
            {
                "length_mm": _metric_mm(nominal_feet.group(1), "ft"),
                "width_mm": _metric_mm(nominal_feet.group(2), "ft"),
            }
        )

    # Explicit millimetre formats may omit the unit between the dimensions,
    # and invoice strings commonly place thickness first: 18x1220x2440 mm.
    millimetres = [
        int(number)
        for number in re.findall(r"(?<!\d)(\d{4})(?!\d)", value)
    ]
    if len(millimetres) >= 2:
        return _normalised_dimensions(
            {"length_mm": millimetres[-1], "width_mm": millimetres[-2]}
        )

    # Israeli supplier catalogues often abbreviate the familiar 1220x2440
    # form as 122x244 and state centimetres elsewhere on the page.
    centimetres = re.search(r"(?<!\d)(\d{2,3})\s*x\s*(\d{2,3})(?!\d)", value)
    if centimetres:
        return _normalised_dimensions(
            {
                "length_mm": int(centimetres.group(1)) * 10,
                "width_mm": int(centimetres.group(2)) * 10,
            }
        )
    if allow_compact_sheet_span:
        compact_span = re.search(r"(?<!\d)([2-4])\s*[-‐–]\s*(\d{3})(?!\d)", value)
        if compact_span:
            return {"length_mm": int(compact_span.group(1)) * 1000 + int(compact_span.group(2))}
    return {}


def purchasable_dimensions_for_row(
    row: Mapping[str, Any],
    *,
    formats_by_family_code: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, int]:
    """Return a complete format only when the registry determines it uniquely.

    One printed sheet side is evidence, not a licence to assume 1220 mm. It is
    completed only when exactly one active family format contains that side.
    With several candidates it stays unresolved for now.
    """
    family_code = str(row.get("material_family") or "").strip()
    attributes = row.get("identity_attributes")
    attributes = attributes if isinstance(attributes, Mapping) else {}
    literal = _normalised_dimensions(attributes)
    source_dimensions = _source_dimensions(
        " ".join(
            str(value or "")
            for value in (row.get("raw_description"), row.get("_source_table_evidence"))
        ),
        allow_compact_sheet_span=bool(formats_by_family_code.get(family_code)),
        allow_linear_length=family_code in {
            "metal_tube", "metal_profile_angle_channel", "metal_flat_bar",
            "metal_round_bar_rod_wire",
        },
    )
    if source_dimensions:
        literal = source_dimensions
    if len(literal) == 2:
        return literal

    # Stock length is itself a complete purchasable format for profiles. It is
    # not a one-side sheet clue that needs a second dimension from the registry.
    if literal and family_code in {
        "metal_tube", "metal_profile_angle_channel", "metal_flat_bar",
        "metal_round_bar_rod_wire",
    }:
        return literal

    raw_formats = formats_by_family_code.get(family_code, ())
    formats = [
        (_normalised_dimensions(candidate.get("purchasable_dimensions")), candidate)
        for candidate in raw_formats
        if candidate.get("active", True)
    ]
    formats = [(dimensions, candidate) for dimensions, candidate in formats if dimensions]
    if literal:
        known_side = next(iter(literal.values()))
        matches = [
            dimensions for dimensions, _candidate in formats
            if known_side in dimensions.values()
        ]
        unique_matches = {
            tuple(sorted(candidate.items())): candidate for candidate in matches
        }
        return next(iter(unique_matches.values())) if len(unique_matches) == 1 else {}

    defaults = [dimensions for dimensions, candidate in formats if candidate.get("is_default")]
    unique_defaults = {
        tuple(sorted(candidate.items())): candidate for candidate in defaults
    }
    return next(iter(unique_defaults.values())) if len(unique_defaults) == 1 else {}


def apply_price_source_purchasable_dimensions(
    result: dict[str, Any],
    *,
    formats_by_family_code: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Attach an offer-only, fully resolved format to source candidates."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("item_kind") != "material":
            continue
        row["purchasable_dimensions"] = purchasable_dimensions_for_row(
            row,
            formats_by_family_code=formats_by_family_code,
        )
    return result
