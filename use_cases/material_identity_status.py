"""Deterministic canonical-path completeness for company materials."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from use_cases.price_source_taxonomy import catalog_v2_taxonomy_for_family


IdentityTone = Literal["green", "yellow", "blue", "red"]


@dataclass(frozen=True)
class MaterialIdentityStatus:
    tone: IdentityTone
    label: str
    known_path: tuple[str, ...]
    missing: tuple[str, ...]
    detail: str


_FIELD_LABELS = {
    "thickness_mm": "thickness",
    "species": "species",
    "width_mm": "width",
    "substrate": "substrate",
    "metal_type": "base metal",
    "section_profile": "section profile",
    "wall_thickness_mm": "wall thickness",
    "diameter_mm": "diameter",
    "coating_system": "coating system",
    "depth_mm": "nominal length",
}


# The Pricing Key registry uses stable Global attribute codes.  Company items
# retain the source-facing attribute names, so this is the one explicit bridge
# between the two contracts.  It is intentionally not another per-family
# endpoint table.
_PRICING_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "thickness": ("thickness_mm", "thickness"),
    "species": ("species",),
    "width": ("width_mm", "width"),
    "width_thickness": ("width_mm", "width", "thickness_mm", "thickness"),
    "dimensions": ("length_mm", "width_mm", "depth_mm", "diameter_mm"),
    "metal_type": ("metal_type",),
    "section_profile": ("section_profile",),
    "wall_thickness": ("wall_thickness_mm", "wall_thickness"),
    "diameter": ("diameter_mm", "diameter"),
    "coating_system": ("coating_system",),
    "stone_type": ("stone_type",),
    "chemistry_product_type": ("chemistry_product_type",),
    "nominal_length": ("nominal_length_mm", "depth_mm", "length_mm"),
    "component_type": ("component_type",),
    "packaging_type": ("packaging_type",),
}

_PRICING_KEY_LABELS = {
    "width_thickness": "width and thickness",
    "dimensions": "dimensions",
    "nominal_length": "nominal length",
    "chemistry_product_type": "product type",
    "component_type": "component type",
    "packaging_type": "packaging type",
}


def _selection_value(value: Any) -> str:
    """Return a stable, comparison-safe representation of one Pricing Key fact."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return _display(value).casefold()
    return " ".join(str(value or "").strip().casefold().split())


def _pricing_key_value(specifications: Mapping[str, Any], code: str) -> str | None:
    fields = _PRICING_KEY_FIELDS.get(code, (code,))
    # The estimation-facts contract calls this ``profile_section`` while the
    # catalog family registry calls it ``section_profile``. They are one fact,
    # not a reason to split otherwise compatible stock.
    if code == "section_profile":
        fields = ("section_profile", "profile_section")
    for field in fields:
        value = specifications.get(field)
        if _present(value):
            return _selection_value(value)
    return None


def material_pricing_selection_key(
    *,
    material_family: str,
    specifications: Mapping[str, Any] | None,
    pricing_policies: Mapping[str, Mapping[str, Any]],
) -> str | None:
    """Build the minimum completed Pricing Key used to group Engine demands.

    This is intentionally smaller than a display name. Decorative labels,
    supplier SKU, brand and product system do not fragment a purchasable
    material group unless the active family policy explicitly makes them a
    price-bearing fact.
    """
    specs = dict(specifications or {})
    family = str(material_family or specs.get("material_family") or "").strip()
    if not family:
        return None
    item = {"specifications": {**specs, "material_family": family}}
    family_code = _family_code(item, item["specifications"])
    policy = pricing_policies.get(family_code)
    if policy is None:
        return None
    values: list[str] = []
    for code in policy.get("pricing_key_attribute_codes") or ():
        text = _pricing_key_value(specs, str(code))
        if text is None:
            return None
        values.append(f"{code}={text}")
    return "|".join((family_code, *values))


# Required V1 endpoint facts. Brand and Product System enrich the canonical
# path but deliberately never block preliminary estimation on their own.
_REQUIRED_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "mdf": ("thickness_mm",),
    "particleboard": ("thickness_mm",),
    "hardboard": ("thickness_mm",),
    "osb": ("thickness_mm",),
    "laminated panel": ("thickness_mm",),
    "plywood": ("thickness_mm",),
    "solid timber": ("species", "thickness_mm"),
    "veneer": ("species",),
    "edge banding": ("width_mm", "thickness_mm", "substrate"),
    "glass": ("thickness_mm",),
    "acrylic sheet": ("thickness_mm",),
    "abs sheet": ("thickness_mm",),
    "polycarbonate sheet": ("thickness_mm",),
    "petg sheet": ("thickness_mm",),
    "pvc sheet": ("thickness_mm",),
    "plastic sheet": ("thickness_mm",),
    "aluminium composite panel": ("thickness_mm",),
    "composite sandwich panel": ("thickness_mm",),
    "vinyl film": ("width_mm",),
    "natural stone": ("thickness_mm",),
    "engineered quartz": ("thickness_mm",),
    "sintered stone": ("thickness_mm",),
    "porcelain": ("thickness_mm",),
    "solid surface": ("thickness_mm",),
    "terrazzo": ("thickness_mm",),
    "metal sheet": ("metal_type", "thickness_mm"),
    "metal tube": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal angle": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal channel": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal profile": ("metal_type", "section_profile", "wall_thickness_mm"),
    "metal bar": ("metal_type", "diameter_mm"),
    "powder coating": ("coating_system",),
    "epoxy coating": ("coating_system",),
    "polyurethane coating": ("coating_system",),
    "primer": ("coating_system",),
    "lacquer": ("coating_system",),
    "paint": ("coating_system",),
    "coating material": ("coating_system",),
    "drawer slide": ("depth_mm",),
    "drawer system": (),
    "hinge": (),
    "door closure": (),
    "handle": (),
    "furniture leg": (),
    "caster": (),
    "plinth profile": (),
    "drilling fixture": (),
    "furniture connector": (),
    "lift mechanism": (),
}


def _present(value: Any) -> bool:
    return value not in (None, "", 0, 0.0, [], {})


def _display(value: Any) -> str:
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def _family_code(item: Mapping[str, Any], specs: Mapping[str, Any]) -> str:
    explicit = str(
        specs.get("catalog_v2_family_code")
        or specs.get("global_family_code")
        or item.get("catalog_v2_family_code")
        or ""
    ).strip()
    if explicit:
        return explicit
    taxonomy = catalog_v2_taxonomy_for_family(str(specs.get("material_family") or ""))
    return str((taxonomy or {}).get("family_code") or "")


def pricing_policy_by_family_code(
    policies: Sequence[Mapping[str, Any]],
    *,
    families: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Mapping[str, Any]]:
    """Index active Pricing Key policies by stable Global family code."""
    family_codes_by_id = {
        str(row.get("family_id") or ""): str(row.get("family_code") or "")
        for row in families
        if str(row.get("family_id") or "") and str(row.get("family_code") or "")
    }
    indexed: dict[str, Mapping[str, Any]] = {}
    for policy in policies:
        if policy.get("active") is False:
            continue
        nested = policy.get("reference_material_families")
        nested_code = nested.get("family_code") if isinstance(nested, Mapping) else ""
        family_code = str(
            policy.get("family_code")
            or nested_code
            or family_codes_by_id.get(str(policy.get("family_id") or ""), "")
        ).strip()
        if family_code:
            indexed[family_code] = policy
    return indexed


def _format_is_complete(policy: Mapping[str, Any], dimensions: Mapping[str, Any] | None) -> bool:
    mode = str(policy.get("purchase_format_policy") or "not_required")
    if mode == "not_required":
        return True
    dimensions = dimensions or {}
    positive = {
        key for key, value in dimensions.items()
        if key in {"length_mm", "width_mm", "depth_mm", "diameter_mm"} and _present(value)
    }
    # Sheet policies require two sides. Linear profiles and non-sheet stock
    # have a meaningful single purchase length, so the generic required policy
    # accepts one proven physical dimension.
    return len(positive) >= (2 if mode == "standard_sheet_2400x1220" else 1)


def _policy_missing(
    specs: Mapping[str, Any], policy: Mapping[str, Any], dimensions: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    missing: list[str] = []
    for code in policy.get("pricing_key_attribute_codes") or ():
        fields = _PRICING_KEY_FIELDS.get(str(code), (str(code),))
        if code == "width_thickness":
            present = all(_present(specs.get(field)) for field in ("width_mm", "thickness_mm"))
        elif code == "dimensions":
            present = any(_present(specs.get(field)) for field in fields) or bool(dimensions)
        else:
            present = any(_present(specs.get(field)) for field in fields)
        if not present:
            missing.append(_PRICING_KEY_LABELS.get(str(code), _FIELD_LABELS.get(str(code), str(code).replace("_", " "))))
    if not _format_is_complete(policy, dimensions):
        missing.append("purchase format")
    return tuple(missing)


def material_identity_status(
    item: Mapping[str, Any],
    *,
    pricing_policies: Mapping[str, Mapping[str, Any]] | None = None,
    purchasable_dimensions: Mapping[str, Any] | None = None,
) -> MaterialIdentityStatus:
    """Assess canonical-path depth without mutating source or catalog data."""
    specs = dict(item.get("specifications") or {})
    family = str(specs.get("material_family") or "").strip()
    if not family or family.casefold() in {"other", "unclassified", "unknown"}:
        return MaterialIdentityStatus("red", "Identity unresolved", (), ("material family",), "Material family is not established")

    policy = (pricing_policies or {}).get(_family_code(item, specs))
    required = _REQUIRED_BY_FAMILY.get(family, ())
    missing = (
        _policy_missing(specs, policy, purchasable_dimensions)
        if policy is not None
        else tuple(_FIELD_LABELS[field] for field in required if not _present(specs.get(field)))
    )
    path = [family]
    for field, label in (("brand", "brand"), ("product_system", "system"), *[(field, _FIELD_LABELS[field]) for field in required]):
        value = specs.get(field)
        if _present(value):
            unit = " mm" if field.endswith("_mm") else ""
            path.append(f"{label}: {_display(value)}{unit}")

    if missing:
        return MaterialIdentityStatus("yellow", "Canonical path incomplete", tuple(path), missing, f"Add {', '.join(missing)} to complete the canonical path")
    if not str(item.get("reference_material_id") or ""):
        return MaterialIdentityStatus("blue", "Israel reference link missing", tuple(path), (), "Canonical endpoint is known, but no Israel reference material is linked yet")
    return MaterialIdentityStatus("green", "Canonical link complete", tuple(path), (), "Canonical endpoint and Israel reference material are linked")
