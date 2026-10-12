"""Shared structured material and operation normalisation contract.

This module is intentionally independent of a specific ingestion route.  A
Price Source row, a company material, a global material and an Estimation
requirement may have different persistence schemas, but all must first reduce
to the same identity: entity, primary attribute, optional brand, then only
identity-bearing secondary attributes.  Raw source prose is evidence, never
an identity field.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from use_cases.hardware_product_system_registry import (
    HARDWARE_BRAND_SEEDS,
    PRODUCT_SYSTEM_SEEDS,
)


# This is an allowlist by design. A new key is a domain decision, not something
# a source parser may add because it happens to see another adjective.
IDENTITY_ATTRIBUTE_DEFAULTS: dict[str, Any] = {
    "thickness_mm": 0,
    "width_mm": 0,
    "length_mm": 0,
    "depth_mm": 0,
    "diameter_mm": 0,
    "primary_attribute": "",
    "brand": "",
    "brand_basis": "unknown",
    "product_system": "",
    "plywood_variant": "",
    "species": "",
    "substrate": "",
    "surface": "",
    "coating": "",
    "colour": "",
    "grade": "",
    "construction": "",
    "finish": "",
}

SECONDARY_ATTRIBUTE_ORDER: tuple[str, ...] = (
    "product_system", "grade", "species", "plywood_variant", "substrate", "construction", "finish", "surface",
    "coating", "colour",
)

_ENTITY_DISPLAY_OVERRIDES = {
    "abs sheet": "ABS Sheet",
    "mdf": "MDF",
    "hdf": "HDF",
    "osb": "OSB",
    "pvc": "PVC",
    "pvc sheet": "PVC Sheet",
    "petg sheet": "PETG Sheet",
    "pmma sheet": "PMMA Sheet",
}


def _product_system_key(value: object) -> str:
    """Compare a Product System independently of source capitalization."""
    return re.sub(r"[^\w]+", "", str(value or "").casefold(), flags=re.UNICODE)


def _title_case_catalog_label(value: object) -> str:
    """Give source-provided catalog labels one calm, uniform display case."""
    return " ".join(str(value or "").strip().title().split())


def _canonical_brand_name(value: object) -> str:
    """Resolve a known Hardware brand, then use uniform title case for display."""
    candidate = str(value or "").strip()
    key = _product_system_key(candidate)
    if not key:
        return ""
    for seed in HARDWARE_BRAND_SEEDS:
        if any(_product_system_key(alias) == key for alias in (seed.canonical_name, *seed.aliases)):
            return _title_case_catalog_label(seed.canonical_name)
    return _title_case_catalog_label(candidate)


def _canonical_product_system_name(value: object) -> str:
    """Return a curated Product System spelling when the value is recognised.

    This is formatting and identity normalisation only. An unknown user-supplied
    system remains intact rather than being guessed or silently discarded.
    """
    candidate = str(value or "").strip()
    key = _product_system_key(candidate)
    if not key:
        return ""
    for seed in PRODUCT_SYSTEM_SEEDS:
        if any(_product_system_key(alias) == key for alias in (seed.canonical_name, *seed.aliases)):
            return _title_case_catalog_label(seed.canonical_name)
    return _title_case_catalog_label(candidate)


def normalize_identity_attributes(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return only attributes allowed to affect a material identity.

    Dropped source words are deliberately not returned. Callers retain their
    immutable raw source/evidence separately if an agent needs the original
    wording later.
    """
    source = values or {}
    normalized = {
        field: source.get(field, default)
        for field, default in IDENTITY_ATTRIBUTE_DEFAULTS.items()
    }
    normalized["brand"] = _canonical_brand_name(normalized["brand"])
    normalized["product_system"] = _canonical_product_system_name(normalized["product_system"])
    return normalized


def display_entity(entity: object) -> str:
    value = " ".join(str(entity or "material").strip().split())
    if not value:
        return "Material"
    return _ENTITY_DISPLAY_OVERRIDES.get(value.casefold(), value.title())


def _display_mm(value: object) -> str:
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        return ""
    if numeric <= 0:
        return ""
    return str(int(numeric)) if numeric.is_integer() else str(numeric)


def _key_dimension_label(identity: Mapping[str, Any]) -> str:
    """Render proven physical dimensions as a universal second key attribute."""
    length = _display_mm(identity.get("length_mm"))
    width = _display_mm(identity.get("width_mm"))
    depth = _display_mm(identity.get("depth_mm"))
    diameter = _display_mm(identity.get("diameter_mm"))
    if length and width:
        return f"{length} × {width} mm"
    if length:
        return f"{length} mm"
    if width:
        return f"{width} mm"
    if depth:
        return f"{depth} mm"
    if diameter:
        return f"Ø{diameter} mm"
    return ""


def canonical_display_name(
    entity: object,
    attributes: Mapping[str, Any] | None,
    *,
    maximum_secondary_attributes: int = 4,
) -> str:
    """Render `entity -> primary -> brand -> meaningful secondaries`.

    The caller owns entity classification. This renderer never attempts to
    infer a category from brand or from discarded source prose.
    """
    identity = normalize_identity_attributes(attributes)
    parts = [display_entity(entity)]
    primary = str(identity["primary_attribute"] or "").strip()
    if not primary:
        thickness = _display_mm(identity.get("thickness_mm"))
        if thickness:
            primary = f"{thickness} mm"
    source = attributes or {}
    brand_basis = str(source.get("brand_basis") or "").strip().casefold()
    brand = "" if brand_basis == "candidate" else str(identity["brand"] or "").strip()
    key_dimension = _key_dimension_label(identity)
    if primary:
        parts.append(primary)
    if key_dimension and key_dimension != primary:
        parts.append(key_dimension)
    if brand:
        parts.append(brand)

    secondary: list[str] = []
    for field in SECONDARY_ATTRIBUTE_ORDER:
        value = str(identity[field] or "").strip()
        if not value or value.casefold() == str(entity or "").strip().casefold():
            continue
        if field in {"species", "plywood_variant"}:
            value = value.title()
        if value not in secondary:
            secondary.append(value)
        if len(secondary) >= maximum_secondary_attributes:
            break
    return " ".join(parts) + (f", {', '.join(secondary)}" if secondary else "")
