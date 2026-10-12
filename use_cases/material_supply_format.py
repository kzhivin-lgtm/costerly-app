"""Resolve the physical dimensions of one supplier offer.

A company material answers what the item is. A supplier offer answers the
price of a purchasable unit of that item. The physical dimensions belong to
that offer because a supplier can sell the same plywood in 2440 x 1220 and
1520 x 1520 sheets at different prices.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from use_cases.price_source_taxonomy import catalog_v2_taxonomy_for_family


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
    taxonomy = catalog_v2_taxonomy_for_family(str(row.get("material_family") or "")) or {}
    family_code = str(taxonomy.get("family_code") or "")
    attributes = row.get("identity_attributes")
    attributes = attributes if isinstance(attributes, Mapping) else {}
    literal = _normalised_dimensions(attributes)
    if len(literal) == 2:
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
