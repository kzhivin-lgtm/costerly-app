"""Offer-level physical purchase-format normalisation.

The company material identifies *what* the supplier sells.  The active offer
records *how that supplier sells it*.  This distinction is essential for sheet
goods: the same plywood may be available as 2440 x 1220 or 3100 x 1220 sheets,
with materially different purchasable cost and nesting.
"""
from __future__ import annotations

from typing import Any, Mapping

from use_cases.price_source_taxonomy import catalog_v2_taxonomy_for_family


SHEET_FORMAT_CODES = {"sheet", "panel", "board"}
_LINEAR_UNITS = {"mm", "cm", "m", "linear_m"}
_AREA_UNITS = {"cm2", "m2"}
_MASS_UNITS = {"g", "kg", "ton"}


def supply_format_code_for_unit(unit: object) -> str:
    """Return a compact physical purchase class for a canonical unit."""
    normalized = str(unit or "").strip().casefold()
    if normalized in SHEET_FORMAT_CODES:
        return "sheet"
    if normalized in _LINEAR_UNITS:
        return "linear_stock"
    if normalized in _AREA_UNITS:
        return "area"
    if normalized in _MASS_UNITS:
        return "mass"
    if normalized == "roll":
        return "roll"
    if normalized in {"set", "pair", "dozen"}:
        return "set"
    if normalized in {"piece", "pack", "box", "carton", "bag", "bucket", "can", "tube", "pallet"}:
        return "piece"
    return "unknown"


def _positive_mm(value: object) -> int:
    try:
        parsed = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return int(round(parsed)) if parsed > 0 else 0


def _sheet_dimensions(attributes: Mapping[str, Any]) -> tuple[int, int]:
    """Normalise literal source dimensions into length x width millimetres."""
    first = _positive_mm(attributes.get("length_mm"))
    second = _positive_mm(attributes.get("width_mm"))
    if first and second:
        return max(first, second), min(first, second)
    return first or second, 0


def supply_format_for_row(
    row: Mapping[str, Any],
    *,
    policies_by_family_code: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the persisted offer format, without mutating raw source evidence.

    A missing policy deliberately remains ``unknown``.  It is not silently
    upgraded to a default format, because that would invent a purchasable item.
    """
    taxonomy = catalog_v2_taxonomy_for_family(str(row.get("material_family") or "")) or {}
    family_code = str(taxonomy.get("family_code") or "")
    policy = policies_by_family_code.get(family_code)
    format_code = supply_format_code_for_unit(row.get("purchase_unit"))
    payload: dict[str, Any] = {
        "family_code": family_code or None,
        "supply_format_code": format_code,
        "purchasable_dimensions": {},
        "minimum_purchase_quantity": 1,
        "format_basis": "not_applicable",
    }
    if not policy:
        payload["format_basis"] = "unknown"
        return payload

    purchase_format_policy = str(policy.get("purchase_format_policy") or "not_required")
    if purchase_format_policy == "not_required":
        return payload

    # A family requiring a purchase format is a sheet/panel family in the
    # current registry.  Preserve its physical meaning even when an invoice
    # used the generic word "panel" or omitted the unit entirely.
    payload["supply_format_code"] = "sheet"
    attributes = row.get("identity_attributes")
    attributes = attributes if isinstance(attributes, Mapping) else {}
    length_mm, width_mm = _sheet_dimensions(attributes)
    if length_mm and width_mm:
        payload["purchasable_dimensions"] = {"length_mm": length_mm, "width_mm": width_mm}
        payload["format_basis"] = "explicit"
        return payload

    default_dimensions = policy.get("default_purchasable_dimensions")
    default_dimensions = default_dimensions if isinstance(default_dimensions, Mapping) else {}
    default_length = _positive_mm(default_dimensions.get("length_mm"))
    default_width = _positive_mm(default_dimensions.get("width_mm"))
    if purchase_format_policy == "standard_sheet_2400x1220" and default_length and default_width:
        if length_mm:
            payload["purchasable_dimensions"] = {
                "length_mm": length_mm,
                "width_mm": min(default_length, default_width),
            }
            payload["format_basis"] = "inferred_standard_width"
        else:
            payload["purchasable_dimensions"] = {
                "length_mm": max(default_length, default_width),
                "width_mm": min(default_length, default_width),
            }
            payload["format_basis"] = "standard_default"
        return payload

    payload["format_basis"] = "incomplete"
    return payload


def apply_price_source_supply_formats(
    result: dict[str, Any],
    *,
    policies_by_family_code: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Attach derived physical purchase formats to persisted-source candidates."""
    for row in result.get("rows") or []:
        if not isinstance(row, dict) or row.get("item_kind") != "material":
            continue
        row["supply_format"] = supply_format_for_row(
            row,
            policies_by_family_code=policies_by_family_code,
        )
    return result
