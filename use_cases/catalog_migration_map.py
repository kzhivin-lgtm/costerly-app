"""Pure, reviewable classification of legacy catalog evidence for Catalog V2.

This module deliberately does not access Supabase and cannot create catalog
records. It turns an old ``reference_materials`` row plus its category evidence
into one of the only three legal migration outcomes. Persistence belongs to a
separate, later backfill step after the Global and Market seed records exist.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


MAPPED = "mapped"
EXCLUDED_BY_POLICY = "excluded_by_policy"
REVIEW_REQUIRED = "review_required"


def _key(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _code(value: object) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", _key(value))
    return value.strip("_")


@dataclass(frozen=True)
class LegacyMaterialDecision:
    status: str
    entity_role_code: str
    family_code: str | None
    production_department_code: str | None
    reason: str
    global_model_code: str | None
    israel_variant_code: str | None


_FAMILY_BY_CATEGORY_NAME = {
    "mdf and hdf": ("mdf_hdf", "material", "wood"),
    "faced mdf": ("faced_mdf", "material", "wood"),
    "particleboard": ("particleboard", "material", "wood"),
    "melamine-faced particleboard": ("melamine_faced_particleboard", "material", "wood"),
    "plywood": ("plywood", "material", "wood"),
    "special plywood": ("plywood_special", "material", "wood"),
    "oriented strand board": ("osb", "material", "wood"),
    "osb": ("osb", "material", "wood"),
    "fibreboard": ("fibreboard_hardboard", "material", "wood"),
    "hardboard and backing board": ("fibreboard_hardboard", "material", "wood"),
    "mdf": ("mdf_hdf", "material", "wood"),
    "edge banding": ("edge_banding", "material", "wood"),
    "edge band": ("edge_banding", "material", "wood"),
    "wood veneer": ("wood_veneer", "material", "wood"),
    "softwood": ("timber_solid_wood_panel", "material", "wood"),
    "hardwood": ("timber_solid_wood_panel", "material", "wood"),
    "glued wood panel": ("timber_solid_wood_panel", "material", "wood"),
    "lightweight and sandwich panels": ("lightweight_sandwich_panel", "material", "wood"),
    "hpl and cpl": ("hpl_cpl", "material", "wood"),
    "compact laminate": ("compact_laminate", "material", "wood"),
    "timber and solid wood panels": ("timber_solid_wood_panel", "material", "wood"),
    "glass": ("glass", "material", "glass_plastics"),
    "mirrors": ("mirror", "material", "glass_plastics"),
    "sheet plastics": ("sheet_plastic", "material", "glass_plastics"),
    "acrylic sheet": ("acrylic_pmma", "material", "glass_plastics"),
    "mirror": ("mirror", "material", "glass_plastics"),
    "natural stone": ("natural_stone_slab", "material", "stone"),
    "engineered quartz": ("engineered_quartz_mineral_hybrid", "material", "stone"),
    "sintered stone": ("sintered_ultra_compact_surface", "material", "stone"),
    "porcelain": ("porcelain_ceramic_slab", "material", "stone"),
    "solid surface": ("solid_surface", "material", "stone"),
    "wood coatings": ("paint_lacquer_stain", "material", "coating"),
    "metal coatings": ("powder_coating", "material", "coating"),
    "hinges": ("hardware_hinge", "hardware", None),
    "drawer runners": ("hardware_drawer_slide", "hardware", None),
    "counted furniture connectors": ("hardware_connector", "hardware", None),
    "concealed and knock-down connectors": ("hardware_connector", "hardware", None),
    "biscuits and loose connectors": ("hardware_connector", "hardware", None),
    "dowels and confirmats": ("hardware_connector", "hardware", None),
    "furniture systems and accessories": ("hardware_furniture_system", "hardware", None),
    "bulk fasteners": ("hardware_fastener", "hardware", None),
    "screws and bolts": ("hardware_fastener", "hardware", None),
    "hinge, runner and system-specific screws": ("hardware_fastener", "hardware", None),
    "bulk nails, brads and staples": ("hardware_fastener", "hardware", None),
    "mounting hardware": ("hardware_mounting_part", "hardware", None),
    "furniture glides and pads": ("hardware_mounting_part", "hardware", None),
    "shelf supports and pins": ("hardware_mounting_part", "hardware", None),
    "handles and pulls": ("hardware_handle", "hardware", None),
    "legs and casters": ("hardware_leg_caster", "hardware", None),
    "lift systems": ("hardware_lift_system", "hardware", None),
    "locks and latches": ("hardware_lock_latch", "hardware", None),
    "drawer systems": ("hardware_drawer_system", "hardware", None),
    "pull-out and specialist storage systems": ("hardware_storage_system", "hardware", None),
    "cabinet suspension hardware": ("hardware_mounting_part", "hardware", None),
    "connector cover caps and decorative plugs": ("hardware_mounting_part", "hardware", None),
    "furniture cable management": ("hardware_mounting_part", "hardware", None),
    "furniture ventilation hardware": ("hardware_mounting_part", "hardware", None),
    "sliding, folding and pocket-door systems": ("hardware_door_system", "hardware", None),
    "wardrobe rails and supports": ("hardware_mounting_part", "hardware", None),
    "installation fastener allowance": ("hardware_fastener", "hardware", None),
    "furniture electrical components": ("hardware_electrical_component", "hardware", None),
    "purchased specialist components": ("purchased_fabricated_component", "purchased_fabricated_component", None),
    "packaging materials": ("packaging_material", "packaging", None),
    "bubble wrap": ("packaging_material", "packaging", None),
    "cardboard": ("packaging_material", "packaging", None),
    "packing tapes and labels": ("packaging_material", "packaging", None),
    "protective film": ("packaging_material", "packaging", None),
    "stretch wrap": ("packaging_material", "packaging", None),
}


def _metal_family(name: str) -> str | None:
    if any(token in name for token in ("sheet", "plate")):
        return "sheet_metal"
    if any(token in name for token in ("tube", "pipe")):
        return "metal_tube"
    if any(token in name for token in ("profile", "angle", "channel", "section", "beam")):
        return "metal_profile_angle_channel"
    if "flat bar" in name:
        return "metal_flat_bar"
    if any(token in name for token in ("round bar", "rod", "wire")):
        return "metal_round_bar_rod_wire"
    if "expanded metal" in name:
        return "sheet_metal"
    return None


def _coating_family(name: str) -> str:
    if "primer" in name:
        return "primer"
    if "powder" in name:
        return "powder_coating"
    if any(token in name for token in ("filler", "hardener", "thinner", "solvent")):
        return "filler_hardener_thinner"
    return "paint_lacquer_stain"


def _model_codes(row: Mapping[str, Any]) -> tuple[str, str]:
    specifications = row.get("specifications") or {}
    global_identity = specifications.get("global_canonical_id") or row.get("material_code")
    global_model_code = _code(global_identity)
    if not global_model_code:
        raise ValueError("Legacy material row needs material_code or global_canonical_id.")
    return global_model_code, f"il_{_code(row.get('material_code') or global_model_code)}"


def classify_legacy_material(
    row: Mapping[str, Any],
    *,
    category_name: str | None,
) -> LegacyMaterialDecision:
    """Classify one legacy material row without guessing a missing family."""
    department = _key(row.get("department"))
    category = _key(category_name)
    canonical_name = _key(row.get("canonical_name"))

    if department == "consumable":
        return LegacyMaterialDecision(
            status=EXCLUDED_BY_POLICY,
            entity_role_code="consumable",
            family_code=None,
            production_department_code=None,
            reason="consumables_are_not_company_catalog_or_preliminary_estimate_items",
            global_model_code=None,
            israel_variant_code=None,
        )

    mapped = None
    if department == "coating":
        mapped = (_coating_family(canonical_name), "material", "coating")
    if mapped is None:
        mapped = _FAMILY_BY_CATEGORY_NAME.get(category)
    if mapped is None and department == "metal":
        family = _metal_family(canonical_name)
        if family:
            mapped = (family, "material", "metal")

    if mapped is None:
        return LegacyMaterialDecision(
            status=REVIEW_REQUIRED,
            entity_role_code="material",
            family_code=None,
            production_department_code=None,
            reason="legacy_category_or_geometry_does_not_prove_one_approved_family",
            global_model_code=None,
            israel_variant_code=None,
        )

    family_code, entity_role_code, production_department_code = mapped
    model_code, variant_code = _model_codes(row)
    return LegacyMaterialDecision(
        status=MAPPED,
        entity_role_code=entity_role_code,
        family_code=family_code,
        production_department_code=production_department_code,
        reason="approved_category_or_geometry_rule",
        global_model_code=model_code,
        israel_variant_code=variant_code,
    )
