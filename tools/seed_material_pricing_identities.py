#!/usr/bin/env python3
"""Build and, only when explicitly requested, seed Israel pricing identities.

The script reads the active global catalog and its existing active model prices.
It does not invent procurement facts. For sheet goods, it groups detailed
variants into an estimation class by family, construction, and thickness. For
other material families it deliberately keeps the detailed item as the class
until that family's pricing axes are reviewed.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

# Support the documented direct invocation from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.supabase_client import get_supabase_client
from use_cases.material_identity_resolution import normalize_material_phrase
from use_cases.price_source_taxonomy import (
    apply_material_taxonomy,
    catalog_v2_taxonomy_for_family,
)
from use_cases.sheet_material_family_policy import sheet_estimation_specifications


PAGE_SIZE = 1_000
CATALOG_VERSION = "israel_global_catalog_v1"
MARKET_CODE = "IL"
IDENTITY_NAMESPACE = "https://costerly.ai/material-pricing-identity/v1/"
SHEET_FAMILIES = {
    "plywood", "mdf", "hdf", "particleboard", "melamine", "osb",
    "hardboard", "fibreboard", "compact_laminate", "hpl", "cpl",
    "veneer", "sheet_plastic", "solid_surface",
}

# The Global Family policy is the source of truth for the minimum pricing
# facts.  These are the concrete normalized-field names used by the resolver
# and Price Source, rather than the human-facing V2 attribute labels stored in
# the policy registry.
_POLICY_ATTRIBUTE_FIELDS: dict[str, tuple[str, ...]] = {
    "thickness": ("thickness_mm",),
    "metal_type": ("metal_type",),
    "section_profile": ("section_profile",),
    "wall_thickness": ("wall_thickness_mm",),
    "width_thickness": ("width_mm", "thickness_mm"),
    "diameter": ("diameter_mm",),
    "dimensions": ("width_mm", "length_mm"),
    "species": ("species",),
    "stone_type": ("stone_type",),
    "width": ("width_mm",),
    "coating_system": ("coating_system",),
    "chemistry_product_type": ("chemistry_product_type",),
    "component_type": ("component_type",),
    "packaging_type": ("packaging_type",),
    "nominal_length": ("depth_mm",),
}


@dataclass(frozen=True)
class SeedIdentity:
    pricing_identity_id: str
    pricing_identity_code: str
    department: str
    canonical_name: str
    canonical_name_he: str | None
    base_unit: str
    price_attributes: dict[str, Any]
    members: tuple[str, ...]


def _select_all(query: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0
    while True:
        page = query.range(start, start + PAGE_SIZE - 1).execute().data or []
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.casefold())).strip("_")


def _family(material: dict[str, Any]) -> str:
    name = str(material["canonical_name"]).casefold()
    subcategory = str((material.get("specifications") or {}).get("subcategory_en") or "").casefold()
    haystack = f"{name} {subcategory}"
    # Catalog subcategory "MDF and HDF" is shared. The concrete material name
    # must decide the family before that broad label is consulted.
    if re.search(r"\bmdf\b", name):
        return "mdf"
    if re.search(r"\bhdf\b", name):
        return "hdf"
    if "plywood" in haystack:
        return "plywood"
    if "melamine" in haystack:
        return "melamine"
    if "hdf" in haystack:
        return "hdf"
    if "mdf" in haystack:
        return "mdf"
    if "particleboard" in haystack or "chipboard" in haystack:
        return "particleboard"
    if "hardboard" in haystack:
        return "hardboard"
    if "fibreboard" in haystack or "fiberboard" in haystack:
        return "fibreboard"
    if re.search(r"\bosb\b", haystack):
        return "osb"
    if "compact laminate" in haystack:
        return "compact_laminate"
    if re.search(r"\bhpl\b", haystack):
        return "hpl"
    if re.search(r"\bcpl\b", haystack):
        return "cpl"
    if "veneer" in haystack:
        return "veneer"
    if "solid surface" in haystack:
        return "solid_surface"
    if "acrylic" in haystack or "plexiglass" in haystack:
        return "acrylic_sheet"
    if "polycarbonate" in haystack:
        return "polycarbonate_sheet"
    if re.search(r"\bpvc\b", haystack):
        return "pvc_sheet"
    if re.search(r"\babs\b", haystack):
        return "abs_sheet"
    if re.search(r"\bpetg\b", haystack):
        return "petg_sheet"
    if "plastic" in haystack:
        return "sheet_plastic"
    return _slug(subcategory or str(material.get("category_code") or "material"))


def _construction(material: dict[str, Any], family: str) -> str | None:
    name = str(material["canonical_name"]).casefold()
    if family not in SHEET_FAMILIES:
        return None
    if "veneer" in name:
        return "veneer_faced"
    if any(token in name for token in ("formica", "hpl", "plastic faced", "laminate faced")):
        return "plastic_laminate_faced"
    if family == "melamine" or "melamine faced" in name:
        return "melamine_faced"
    if "film faced" in name:
        return "film_faced"
    return "raw"


def _attributes(material: dict[str, Any]) -> dict[str, Any]:
    family = _family(material)
    specifications = dict(material.get("specifications") or {})
    attributes: dict[str, Any] = {"material_family": family}
    thickness = specifications.get("thickness_mm")
    if thickness is not None:
        attributes["thickness_mm"] = thickness
    construction = _construction(material, family)
    if construction:
        attributes["construction"] = construction
    # Outside reviewed sheet classes, preserve physical detail until a later
    # category-specific rule can safely collapse it.
    if family not in SHEET_FAMILIES:
        attributes["detail_material_id"] = str(material["material_id"])
    # Wood veneer and an unspecified plastic sheet can span radically different
    # price classes. Keep them detailed until the sheet family is explicit.
    if family in {"veneer", "sheet_plastic"}:
        attributes["detail_material_id"] = str(material["material_id"])
    return attributes


def _identity_code(attributes: dict[str, Any]) -> str:
    return _slug("_".join(f"{key}_{value}" for key, value in sorted(attributes.items())))


def _identity_name(attributes: dict[str, Any]) -> str:
    family = str(attributes["material_family"]).replace("_", " ").title()
    construction = str(attributes.get("construction") or "").replace("_", " ")
    thickness = attributes.get("thickness_mm")
    if "detail_material_id" in attributes:
        return "Detailed price class"
    pieces = [family]
    if construction:
        pieces.append(construction)
    if thickness is not None:
        pieces.append(f"{thickness:g} mm" if isinstance(thickness, float) else f"{thickness} mm")
    return ", ".join(pieces)


def _has_value(value: Any) -> bool:
    return value not in (None, "", 0, 0.0, [], {})


def _policy_family_and_facts(
    material: dict[str, Any],
    *,
    pricing_policies: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Project a priced Global material onto one approved V2 Pricing Key.

    The previous seed treated every non-sheet material as a detailed SKU
    identity. That made the pricing resolver unable to use the new Family
    Registry. This projection never infers a missing key. A material with an
    incomplete policy key is simply not promoted into a new price class.
    """
    specifications = dict(material.get("specifications") or {})
    source_family = normalize_material_phrase(specifications.get("material_family"))
    projection = catalog_v2_taxonomy_for_family(source_family)

    taxonomy_row = {
        "item_kind": "material",
        "raw_description": str(material.get("canonical_name") or ""),
        "normalized_name": str(material.get("canonical_name") or ""),
        "identity_attributes": {},
        "status": "ready",
        "reason_codes": [],
    }
    apply_material_taxonomy(taxonomy_row)
    parsed_family = normalize_material_phrase(taxonomy_row.get("material_family"))
    projection = projection or catalog_v2_taxonomy_for_family(parsed_family)
    family_code = str((projection or {}).get("family_code") or "")
    if not family_code and source_family in pricing_policies:
        family_code = source_family

    facts = {
        **dict(taxonomy_row.get("identity_attributes") or {}),
        **specifications,
    }
    # A catalog name such as ``MDF white 19 mm`` denotes the established
    # faced class.  The exact decor remains supplier evidence, not a price
    # class.  Plywood variants likewise collapse only for the pricing class.
    pricing_source_family = source_family or parsed_family
    if pricing_source_family:
        facts = sheet_estimation_specifications(
            material_family=pricing_source_family,
            extracted_specifications=facts,
        )
    construction = normalize_material_phrase(facts.get("construction"))
    if family_code == "mdf_hdf" and construction.replace("_", " ") == "plastic laminate faced":
        family_code = "faced_mdf"
    policy = pricing_policies.get(family_code)
    if not policy:
        return None

    attributes: dict[str, Any] = {"material_family": family_code}
    for policy_attribute in policy.get("pricing_key_attribute_codes") or ():
        concrete_fields = _POLICY_ATTRIBUTE_FIELDS.get(str(policy_attribute), ())
        if not concrete_fields:
            raise ValueError(f"Unsupported Pricing Key attribute: {policy_attribute}")
        for field in concrete_fields:
            value = facts.get(field)
            if not _has_value(value):
                return None
            attributes[field] = value
    # Construction is a real price-bearing boundary for sheet families even
    # where the V2 Family separates only the ordinary faced MDF case.
    if construction and family_code in {"mdf_hdf", "faced_mdf", "plywood"}:
        attributes["construction"] = construction
    return attributes


def build_policy_identities(
    materials: Iterable[dict[str, Any]],
    *,
    pricing_policies: dict[str, dict[str, Any]],
) -> list[SeedIdentity]:
    """Build only policy-complete Global classes from already priced material data."""
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    attributes_by_group: dict[tuple[str, str, str], dict[str, Any]] = {}
    for material in materials:
        attributes = _policy_family_and_facts(material, pricing_policies=pricing_policies)
        if not attributes:
            continue
        key = (
            str(material["department"]),
            str(material["base_unit"]),
            _identity_code(attributes),
        )
        grouped[key].append(material)
        attributes_by_group[key] = attributes

    identities: list[SeedIdentity] = []
    for (department, base_unit, code), members in sorted(grouped.items()):
        attributes = attributes_by_group[(department, base_unit, code)]
        stable_code = f"il_v2_{code}"
        identities.append(
            SeedIdentity(
                pricing_identity_id=str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + stable_code)),
                pricing_identity_code=stable_code,
                department=department,
                canonical_name=_identity_name(attributes),
                canonical_name_he=None,
                base_unit=base_unit,
                price_attributes=attributes,
                members=tuple(sorted(str(row["material_id"]) for row in members)),
            )
        )
    return identities


def build_identities(materials: Iterable[dict[str, Any]]) -> list[SeedIdentity]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for material in materials:
        attributes = _attributes(material)
        grouped[(str(material["department"]), str(material["base_unit"]), _identity_code(attributes))].append(material)
    identities: list[SeedIdentity] = []
    for (department, base_unit, code), members in sorted(grouped.items()):
        attributes = _attributes(members[0])
        stable_code = f"il_{code}"
        identities.append(
            SeedIdentity(
                pricing_identity_id=str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + stable_code)),
                pricing_identity_code=stable_code,
                department=department,
                canonical_name=_identity_name(attributes),
                canonical_name_he=None,
                base_unit=base_unit,
                price_attributes=attributes,
                members=tuple(sorted(str(row["material_id"]) for row in members)),
            )
        )
    return identities


def _price_payloads(
    identities: Iterable[SeedIdentity], model_prices: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    prices_by_material = {str(row["material_id"]): row for row in model_prices}
    payloads: list[dict[str, Any]] = []
    for identity in identities:
        rows = [prices_by_material[member] for member in identity.members if member in prices_by_material]
        if not rows:
            continue
        typicals = [Decimal(str(row["price_typical"])) for row in rows]
        lows = [Decimal(str(row["price_low"])) for row in rows]
        highs = [Decimal(str(row["price_high"])) for row in rows]
        confidences = [Decimal(str(row["confidence"])) for row in rows]
        # A broad class is intentionally a range. The range exposes variation
        # rather than silently pretending that a decor-specific price is exact.
        payloads.append(
            {
                "pricing_identity_price_id": str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + "price/" + identity.pricing_identity_code)),
                "pricing_identity_id": identity.pricing_identity_id,
                "catalog_version": CATALOG_VERSION,
                "price_low": str(min(lows)),
                "price_typical": str(median(typicals)),
                "price_high": str(max(highs)),
                "unit": str(rows[0]["unit"]),
                "currency": str(rows[0]["currency"]),
                "price_scope": str(rows[0]["price_scope"]),
                "pricing_method": "modeled_from_israel_anchor",
                "confidence": str(min(confidences)),
                "source_material_id": str(rows[0]["material_id"]),
                "formula_description": "Median of active detailed Israel catalog model prices within the reviewed pricing identity.",
                "model_metadata": {"member_count": len(rows), "aggregation": "min_low_median_typical_max_high"},
                "effective_from": str(date.today()),
                "status": "candidate",
            }
        )
    return payloads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write candidate identities to production")
    args = parser.parse_args()
    client = get_supabase_client()
    materials = [
        row for row in _select_all(client.table("reference_materials").select(
            "material_id,department,category_code,canonical_name,base_unit,specifications,active"
        ).eq("active", True))
        if (row.get("specifications") or {}).get("catalog_version") == CATALOG_VERSION
    ]
    prices = _select_all(client.table("market_material_model_prices").select(
        "material_id,price_low,price_typical,price_high,unit,currency,price_scope,confidence,status"
    ).eq("status", "active"))
    policy_rows = _select_all(
        client.table("reference_material_family_pricing_policies")
        .select(
            "pricing_key_attribute_codes,reference_material_families!inner(family_code)"
        )
        .eq("active", True)
    )
    pricing_policies = {
        str((row.get("reference_material_families") or {}).get("family_code") or ""): dict(row)
        for row in policy_rows
        if str((row.get("reference_material_families") or {}).get("family_code") or "")
    }
    identities = build_policy_identities(materials, pricing_policies=pricing_policies)
    identity_rows = [
        {
            "pricing_identity_id": item.pricing_identity_id,
            "market_code": MARKET_CODE,
            "pricing_identity_code": item.pricing_identity_code,
            "department": item.department,
            "canonical_name": item.canonical_name,
            "canonical_name_he": item.canonical_name_he,
            "base_unit": item.base_unit,
            "price_attributes": item.price_attributes,
            "status": "candidate",
        }
        for item in identities
    ]
    member_rows = [
        {
            "pricing_identity_id": identity.pricing_identity_id,
            "material_id": material_id,
            "membership_basis": "exact_price_class",
        }
        for identity in identities
        for material_id in identity.members
    ]
    price_rows = _price_payloads(identities, prices)
    sheet_identity_count = sum(
        1 for row in identities if row.price_attributes.get("material_family") in SHEET_FAMILIES
    )
    identities_by_family = defaultdict(int)
    priced_by_family = defaultdict(int)
    priced_identity_ids = {str(row["pricing_identity_id"]) for row in price_rows}
    for identity in identities:
        family = str(identity.price_attributes.get("material_family") or "")
        identities_by_family[family] += 1
        if identity.pricing_identity_id in priced_identity_ids:
            priced_by_family[family] += 1
    policy_coverage = {
        family: {
            "policy_complete_classes": identities_by_family.get(family, 0),
            "classes_with_active_model_price": priced_by_family.get(family, 0),
        }
        for family in sorted(pricing_policies)
    }
    print({
        "catalog_materials": len(materials),
        "pricing_identities": len(identities),
        "sheet_pricing_identities": sheet_identity_count,
        "active_pricing_policies": len(pricing_policies),
        "policy_coverage": policy_coverage,
        "members": len(member_rows),
        "candidate_prices": len(price_rows),
        "mode": "apply" if args.apply else "dry_run",
    })
    if not args.apply:
        return
    client.table("reference_material_pricing_identities").upsert(
        identity_rows, on_conflict="market_code,pricing_identity_code"
    ).execute()
    client.table("reference_material_pricing_identity_members").upsert(
        member_rows, on_conflict="pricing_identity_id,material_id"
    ).execute()
    client.table("market_material_pricing_identity_prices").upsert(
        price_rows, on_conflict="pricing_identity_id,catalog_version"
    ).execute()


if __name__ == "__main__":
    main()
