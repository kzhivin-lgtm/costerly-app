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



# This is an allowlist by design. A new key is a domain decision, not something
# a source parser may add because it happens to see another adjective.
IDENTITY_ATTRIBUTE_DEFAULTS: dict[str, Any] = {
    "thickness_mm": 0,
    "width_mm": 0,
    "length_mm": 0,
    "depth_mm": 0,
    "diameter_mm": 0,
    "wall_thickness_mm": 0,
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
    # Price-bearing facts outside the sheet-material vocabulary.  These stay
    # explicitly allowlisted: a source may not promote arbitrary prose into
    # an identity merely because it is a descriptive adjective.
    "metal_type": "",
    "section_profile": "",
    "stone_type": "",
    "coating_system": "",
    "chemistry_product_type": "",
    "component_type": "",
    "packaging_type": "",
}

SECONDARY_ATTRIBUTE_ORDER: tuple[str, ...] = (
    "product_system", "grade", "species", "plywood_variant", "substrate", "construction", "finish", "surface",
    "coating", "metal_type", "section_profile", "wall_thickness_mm",
    "stone_type", "coating_system", "colour",
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


def _title_case_catalog_label(value: object) -> str:
    """Give source-provided catalog labels one calm, uniform display case."""
    return " ".join(str(value or "").strip().title().split())


def _canonical_brand_name(value: object) -> str:
    """Format source-proven brand text without maintaining a second alias list.

    Catalog recognition happens in the shared alias context.  The normalizer
    must not quietly recognise another spelling before that deterministic
    catalog pass has run.
    """
    return _title_case_catalog_label(value)


def _canonical_product_system_name(value: object) -> str:
    """Format source-proven system text without maintaining a second alias list."""
    return _title_case_catalog_label(value)


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


def _secondary_attribute_display(field: str, value: object) -> str:
    """Render the small set of non-sheet pricing facts without source prose."""
    text = str(value or "").strip()
    if not text:
        return ""
    if field == "wall_thickness_mm":
        dimension = _display_mm(value)
        return f"{dimension} mm wall" if dimension else ""
    if field in {"metal_type", "section_profile", "stone_type"}:
        return _title_case_catalog_label(text)
    if field == "substrate" and text.casefold() in {"abs", "pvc", "hpl", "petg", "pmma"}:
        return text.upper()
    return text


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
    # A profile or edge band already renders its compound physical key as the
    # primary attribute (for example ``40×20 mm`` or ``22×2 mm``). Do not
    # repeat its first side as an unrelated second key dimension.
    if "×" in primary or "x" in primary.casefold():
        key_dimension = ""
    if primary:
        parts.append(primary)
    if key_dimension and key_dimension != primary:
        parts.append(key_dimension)
    if brand:
        parts.append(brand)

    secondary: list[str] = []
    for field in SECONDARY_ATTRIBUTE_ORDER:
        value = _secondary_attribute_display(field, identity[field])
        if not value or value.casefold() == str(entity or "").strip().casefold():
            continue
        if field == "coating_system" and value.casefold() in display_entity(entity).casefold():
            continue
        if field == "grade" and value.casefold() in str(identity.get("metal_type") or "").casefold():
            continue
        if field in {"species", "plywood_variant"}:
            value = value.title()
        if value not in secondary:
            secondary.append(value)
        if len(secondary) >= maximum_secondary_attributes:
            break
    return " ".join(parts) + (f", {', '.join(secondary)}" if secondary else "")


def canonical_material_display_name(
    entity: object,
    attributes: Mapping[str, Any] | None,
    *,
    fallback: object = "",
) -> str:
    """Return the one display name for every processed material projection.

    A recognised material family must always render through the canonical
    entity/attributes formatter, regardless of whether it is shown in the
    catalog, Review, a source-detail row, or a later estimation projection.
    An unknown family cannot truthfully be reformatted, so its persisted
    normalized label remains the explicit fallback until the row is resolved.
    """
    family = " ".join(str(entity or "").strip().split())
    if family and family.casefold() not in {"other", "unclassified", "unknown"}:
        return canonical_display_name(family, attributes)
    return " ".join(str(fallback or "Material").strip().split()) or "Material"
