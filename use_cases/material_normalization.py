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
from typing import Any


# This is an allowlist by design. A new key is a domain decision, not something
# a source parser may add because it happens to see another adjective.
IDENTITY_ATTRIBUTE_DEFAULTS: dict[str, Any] = {
    "thickness_mm": 0,
    "width_mm": 0,
    "length_mm": 0,
    "diameter_mm": 0,
    "primary_attribute": "",
    "brand": "",
    "brand_basis": "unknown",
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
    "grade", "species", "substrate", "construction", "finish", "surface",
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


def normalize_identity_attributes(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return only attributes allowed to affect a material identity.

    Dropped source words are deliberately not returned. Callers retain their
    immutable raw source/evidence separately if an agent needs the original
    wording later.
    """
    source = values or {}
    return {
        field: source.get(field, default)
        for field, default in IDENTITY_ATTRIBUTE_DEFAULTS.items()
    }


def display_entity(entity: object) -> str:
    value = " ".join(str(entity or "material").strip().split())
    if not value:
        return "Material"
    return _ENTITY_DISPLAY_OVERRIDES.get(value.casefold(), value.title())


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
    brand = str(identity["brand"] or "").strip()
    if primary:
        parts.append(primary)
    if brand:
        parts.append(brand)

    secondary: list[str] = []
    for field in SECONDARY_ATTRIBUTE_ORDER:
        value = str(identity[field] or "").strip()
        if not value or value.casefold() == str(entity or "").strip().casefold():
            continue
        if field == "species":
            value = value.title()
        if value not in secondary:
            secondary.append(value)
        if len(secondary) >= maximum_secondary_attributes:
            break
    return " ".join(parts) + (f", {', '.join(secondary)}" if secondary else "")
