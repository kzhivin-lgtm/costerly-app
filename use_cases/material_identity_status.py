"""Deterministic canonical-path completeness for company materials."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal, Mapping, Sequence



IdentityTone = Literal["green", "yellow", "blue", "red"]


@dataclass(frozen=True)
class MaterialIdentityStatus:
    tone: IdentityTone
    label: str
    known_path: tuple[str, ...]
    missing: tuple[str, ...]
    detail: str


_FIELD_LABELS = {
    "board_type": "board type",
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
    "board_type": ("board_type",),
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
    "nominal_length": ("nominal_length_mm", "depth_mm", "length_mm", "length"),
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


def pricing_key_fact_fields(attribute_code: str) -> tuple[str, ...]:
    """Return accepted source-fact fields for one stable Pricing Key fact.

    This is deliberately the same bridge used by deterministic resolution.
    Extraction may use it to look for an evidenced fact, but cannot infer a
    value or expand the Pricing Key itself.
    """
    code = str(attribute_code or "")
    if code == "section_profile":
        return ("profile_section",)
    return _PRICING_KEY_FIELDS.get(code, (code,))


def _selection_value(value: Any) -> str:
    """Return a stable, comparison-safe representation of one Pricing Key fact."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return _display(value).casefold()
    return " ".join(str(value or "").strip().casefold().split())


def _canonical_section_profile(value: Any) -> Any:
    """Map source-facing tube wording to a live Israel Reference key.

    ``tube`` is round by default. A literal two-sided section is stronger
    evidence: a supplier may call 20 x 20 a tube, but it is a square profile.
    Only the three currently catalogued baseline sections are collapsed here;
    unknown explicit dimensions remain explicit rather than becoming a false
    purchasable candidate.
    """
    if not isinstance(value, str):
        return value
    text = " ".join(value.casefold().replace("×", "x").split())
    pairs = re.search(r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*x\s*(\d{1,3}(?:\.\d+)?)(?!\d)", text)
    if pairs:
        first, second = float(pairs.group(1)), float(pairs.group(2))
        if first == second == 20:
            return "square_tube_20x20"
        if {first, second} == {20, 40}:
            return "rectangular_tube_40x20"
        return text
    if re.search(r"(?:round|circular|\bø\s*20\b|\bd\s*20\b|кругл|עגול)", text):
        return "round_tube_d20"
    if re.search(r"(?:square|квадрат|מרובע)", text):
        return "square_tube_20x20"
    if re.search(r"(?:rectangular|прямоуголь|מלבני)", text):
        return "rectangular_tube_40x20"
    if text in {"tube", "metal tube", "steel tube", "pipe", "труба", "צינור"}:
        return "round_tube_d20"
    return text


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
            if code == "section_profile":
                value = _canonical_section_profile(value)
            return _selection_value(value)
    return None


def canonical_pricing_key_fact_value(
    specifications: Mapping[str, Any], attribute_code: str,
) -> str | None:
    """Return one Pricing Key value in the Resolver's comparison form.

    Default applicability must compare the same canonical section values as
    candidate selection, for example source ``20x20`` and catalog
    ``square_tube_20x20``.
    """
    return _pricing_key_value(specifications, attribute_code)


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
    # Object Facts can safely use a Global family code when that family has no
    # source-taxonomy alias (for example ``compact_laminate``).  A stale price
    # class such as ``stainless_steel`` still has no policy and is rejected.
    if not family_code and family in pricing_policies:
        family_code = family
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
    "mdf_hdf": ("board_type", "thickness_mm"),
    "particleboard": ("thickness_mm",),
    "fibreboard_hardboard": ("thickness_mm",),
    "osb": ("thickness_mm",),
    "melamine_faced_particleboard": ("thickness_mm",),
    "plywood": ("thickness_mm",),
    "timber_solid_wood_panel": ("species", "thickness_mm"),
    "wood_veneer": ("species",),
    "edge_banding": ("width_mm", "thickness_mm", "substrate"),
    "glass": ("thickness_mm",),
    "acrylic_pmma": ("thickness_mm",),
    "polycarbonate_petg_pvc_abs": ("thickness_mm",),
    "sheet_plastic": ("thickness_mm",),
    "aluminium_composite_panel": ("thickness_mm",),
    "composite_sandwich_panel": ("thickness_mm",),
    "vinyl_film": ("width_mm",),
    "natural_stone_slab": ("thickness_mm",),
    "engineered_quartz_mineral_hybrid": ("thickness_mm",),
    "sintered_ultra_compact_surface": ("thickness_mm",),
    "porcelain_ceramic_slab": ("thickness_mm",),
    "solid_surface": ("thickness_mm",),
    "terrazzo_engineered_agglomerate": ("thickness_mm",),
    "sheet_metal": ("metal_type", "thickness_mm"),
    # Furniture profiles use a technical default wall thickness of 1.5 mm
    # when the evidence does not state one.  It remains useful secondary
    # provenance when explicit, but never blocks material identity or pricing.
    "metal_tube": ("metal_type", "section_profile"),
    "metal_profile_angle_channel": ("metal_type", "section_profile"),
    "metal_round_bar_rod_wire": ("metal_type", "diameter_mm"),
    "powder_coating": ("coating_system",),
    "paint_lacquer_stain": ("coating_system",),
    "primer": ("coating_system",),
    "filler_hardener_thinner": ("coating_system",),
    "hardware_drawer_slide": ("depth_mm",),
    "hardware_drawer_system": (),
    "hardware_hinge": (),
    "hardware_lock_latch": (),
    "hardware_handle": (),
    "hardware_leg_caster": (),
    "hardware_mounting_part": (),
    "hardware_connector": (),
    "hardware_lift_system": (),
}


def _present(value: Any) -> bool:
    return value not in (None, "", 0, 0.0, [], {})


def _display(value: Any) -> str:
    return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)


def _family_code(item: Mapping[str, Any], specs: Mapping[str, Any]) -> str:
    explicit = str(
        specs.get("material_family")
        or specs.get("global_family_code")
        or item.get("material_family")
        or ""
    ).strip()
    return explicit


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
