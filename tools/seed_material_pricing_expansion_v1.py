#!/usr/bin/env python3
"""Add reviewed Israel price classes absent from the first V3 seed.

This is deliberately additive. It neither retires nor rewrites the existing
2,807 active identities. It restores MDF classes missed by the old shared
"MDF and HDF" taxonomy parsing, then adds only the exact classes agreed for
the Tsidky acceptance set. Every new resolver identity receives an active,
traceable price model.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.supabase_client import get_supabase_client
from tools.seed_material_pricing_identities import (
    CATALOG_VERSION,
    IDENTITY_NAMESPACE,
    MARKET_CODE,
    _identity_code,
    _price_payloads,
    _select_all,
    build_identities,
)


PANEL_CATEGORY = "gcm_872a62372adec333d2c0a62c"
EXPANSION_NAMESPACE = "https://costerly.ai/israel-catalog-expansion/v1/"

# Static entries are evidence-backed by the public Tsidky page imported in the
# acceptance source. Its listed prices include VAT, which is retained in model
# metadata rather than silently converted into an unsupported net-price claim.
SOLID_PANEL_MODELS = (
    ("pine", 18, "sheet", Decimal("369"), Decimal("410"), Decimal("451"), "Tsidky public listing, VAT included"),
    ("pine", 28, "sheet", Decimal("513"), Decimal("570"), Decimal("627"), "Tsidky public listing, VAT included"),
    ("oak", 20, "m2", Decimal("600"), Decimal("675"), Decimal("750"), "Tsidky public listing range, VAT included"),
    ("oak", 40, "m2", Decimal("855"), Decimal("950"), Decimal("1045"), "Tsidky public listing, VAT included"),
)


def _identity_payload(*, attributes: dict[str, Any], base_unit: str, canonical_name: str, canonical_name_he: str | None) -> dict[str, Any]:
    code = f"il_{_identity_code(attributes)}"
    return {
        "pricing_identity_id": str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + code)),
        "market_code": MARKET_CODE,
        "pricing_identity_code": code,
        "department": "wood",
        "canonical_name": canonical_name,
        "canonical_name_he": canonical_name_he,
        "base_unit": base_unit,
        "price_attributes": attributes,
        "status": "active",
    }


def _material_payload(*, code: str, name: str, name_he: str, unit: str, attributes: dict[str, Any]) -> dict[str, Any]:
    material_id = str(uuid5(NAMESPACE_URL, EXPANSION_NAMESPACE + f"material/{code}"))
    return {
        "material_id": material_id,
        "material_code": f"gcm_exp_{code}",
        "department": "wood",
        "category_code": PANEL_CATEGORY,
        "canonical_name": name,
        "base_unit": unit,
        "specifications": {
            "catalog_version": CATALOG_VERSION,
            "global_canonical_id": f"GCM-V1-EXP-{code.upper()}",
            "category_en": "Wood panels",
            "subcategory_en": "Solid wood panels" if attributes["material_family"] == "laminated solid wood panel" else "Wood panels",
            "canonical_name_he": name_he,
            **attributes,
        },
        "active": True,
    }


def _price_lookup(client: Any) -> dict[str, dict[str, Any]]:
    identities = _select_all(
        client.table("reference_material_pricing_identities")
        .select("pricing_identity_id,price_attributes")
        .eq("market_code", MARKET_CODE)
        .eq("status", "active")
    )
    prices = _select_all(
        client.table("market_material_pricing_identity_prices")
        .select("pricing_identity_id,price_low,price_typical,price_high,unit,currency,price_scope,confidence")
        .eq("status", "active")
    )
    prices_by_id = {str(row["pricing_identity_id"]): row for row in prices}
    return {
        str(row["pricing_identity_id"]): {**row, "price": prices_by_id.get(str(row["pricing_identity_id"]))}
        for row in identities
        if prices_by_id.get(str(row["pricing_identity_id"]))
    }


def _interpolate_price(
    lookup: dict[str, dict[str, Any]], *, family: str, construction: str, thickness: int | float
) -> dict[str, Any]:
    candidates = []
    for row in lookup.values():
        attributes = row.get("price_attributes") or {}
        if attributes.get("material_family") != family or attributes.get("construction") != construction:
            continue
        candidate_thickness = attributes.get("thickness_mm")
        if candidate_thickness is None:
            continue
        price = row["price"]
        if price["unit"] != "m2" or price["currency"] != "ILS" or price["price_scope"] != "material_only":
            continue
        candidates.append((Decimal(str(candidate_thickness)), price))
    candidates.sort(key=lambda item: item[0])
    target = Decimal(str(thickness))
    lower = [item for item in candidates if item[0] <= target]
    upper = [item for item in candidates if item[0] >= target]
    left, right = (lower[-1] if lower else candidates[0]), (upper[0] if upper else candidates[-1])
    if left[0] == right[0]:
        raise ValueError(f"No distinct anchors for {family}/{construction}/{thickness}")
    ratio = (target - left[0]) / (right[0] - left[0])
    return {
        key: (Decimal(str(left[1][key])) + (Decimal(str(right[1][key])) - Decimal(str(left[1][key]))) * ratio).quantize(Decimal("0.000001"))
        for key in ("price_low", "price_typical", "price_high")
    } | {
        "unit": "m2",
        "currency": "ILS",
        "price_scope": "material_only",
        "confidence": max(Decimal("10"), min(Decimal(str(left[1]["confidence"])), Decimal(str(right[1]["confidence"]))) - Decimal("8")),
        "formula": f"Linear interpolation or extrapolation between approved {family} {construction} thickness models {left[0]:g} and {right[0]:g} mm.",
    }


def _synthetic_sheet_specs() -> tuple[dict[str, Any], ...]:
    return (
        {"code": "plywood_raw_16", "name": "Plywood, raw, 16 mm", "he": "לביד גולמי, 16 מ״מ", "attributes": {"material_family": "plywood", "construction": "raw", "thickness_mm": 16}},
        {"code": "plywood_raw_17", "name": "Plywood, raw, 17 mm", "he": "לביד גולמי, 17 מ״מ", "attributes": {"material_family": "plywood", "construction": "raw", "thickness_mm": 17}},
        {"code": "plywood_laminate_17", "name": "Plywood, plastic laminate faced, 17 mm", "he": "לביד מצופה למינציה פלסטית, 17 מ״מ", "attributes": {"material_family": "plywood", "construction": "plastic_laminate_faced", "thickness_mm": 17}},
        {"code": "melamine_17", "name": "Melamine, melamine faced, 17 mm", "he": "לוח מלמין, 17 מ״מ", "attributes": {"material_family": "melamine", "construction": "melamine_faced", "thickness_mm": 17}},
        {"code": "melamine_27", "name": "Melamine, melamine faced, 27 mm", "he": "לוח מלמין, 27 מ״מ", "attributes": {"material_family": "melamine", "construction": "melamine_faced", "thickness_mm": 27}},
        {"code": "mdf_raw_17", "name": "MDF, raw, 17 mm", "he": "MDF גולמי, 17 מ״מ", "attributes": {"material_family": "mdf", "construction": "raw", "thickness_mm": 17}},
        {"code": "mdf_laminate_17", "name": "MDF, plastic laminate faced, 17 mm", "he": "MDF מצופה למינציה פלסטית, 17 מ״מ", "attributes": {"material_family": "mdf", "construction": "plastic_laminate_faced", "thickness_mm": 17}},
        {"code": "hardboard_raw_3_2", "name": "Hardboard, raw, 3.2 mm", "he": "מזוניט גולמי, 3.2 מ״מ", "attributes": {"material_family": "hardboard", "construction": "raw", "thickness_mm": 3.2}},
    )


def build_payloads(client: Any) -> dict[str, list[dict[str, Any]]]:
    materials = [
        row for row in _select_all(client.table("reference_materials").select(
            "material_id,department,category_code,canonical_name,base_unit,specifications,active"
        ).eq("active", True))
        if (row.get("specifications") or {}).get("catalog_version") == CATALOG_VERSION
    ]
    existing_codes = {
        str(row["pricing_identity_code"])
        for row in _select_all(client.table("reference_material_pricing_identities").select("pricing_identity_code"))
    }
    existing_prices = _select_all(client.table("market_material_model_prices").select(
        "material_id,price_low,price_typical,price_high,unit,currency,price_scope,confidence,status"
    ).eq("status", "active"))
    restored = [item for item in build_identities(materials) if item.pricing_identity_code not in existing_codes]
    identities = [
        {"pricing_identity_id": item.pricing_identity_id, "market_code": MARKET_CODE, "pricing_identity_code": item.pricing_identity_code, "department": item.department, "canonical_name": item.canonical_name, "canonical_name_he": item.canonical_name_he, "base_unit": item.base_unit, "price_attributes": item.price_attributes, "status": "active"}
        for item in restored
    ]
    members = [
        {"pricing_identity_id": item.pricing_identity_id, "material_id": material_id, "membership_basis": "exact_price_class"}
        for item in restored for material_id in item.members
    ]
    identity_prices = _price_payloads(restored, existing_prices)
    for row in identity_prices:
        row["status"] = "active"

    physical_materials: list[dict[str, Any]] = []
    material_prices: list[dict[str, Any]] = []
    lookup = _price_lookup(client)
    for spec in _synthetic_sheet_specs():
        attributes = spec["attributes"]
        material = _material_payload(code=spec["code"], name=spec["name"], name_he=spec["he"], unit="m2", attributes=attributes)
        identity = _identity_payload(attributes=attributes, base_unit="m2", canonical_name=spec["name"], canonical_name_he=spec["he"])
        price = _interpolate_price(lookup, family=attributes["material_family"], construction=attributes["construction"], thickness=attributes["thickness_mm"])
        physical_materials.append(material)
        identities.append(identity)
        members.append({"pricing_identity_id": identity["pricing_identity_id"], "material_id": material["material_id"], "membership_basis": "exact_price_class"})
        model = {"model_price_id": str(uuid5(NAMESPACE_URL, EXPANSION_NAMESPACE + f"model/{spec['code']}")), "material_id": material["material_id"], "market_code": MARKET_CODE, "catalog_version": CATALOG_VERSION, **{key: str(value) if isinstance(value, Decimal) else value for key, value in price.items() if key not in {"formula"}}, "pricing_method": "derived_from_israel_curve", "anchor_count": 2, "formula_description": price["formula"], "model_metadata": {"expansion": "pricing_identity_v1", "not_nearest_thickness_matching": True}, "effective_from": str(date.today()), "status": "active"}
        material_prices.append(model)
        identity_prices.append({"pricing_identity_price_id": str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + "price/" + identity["pricing_identity_code"])), "pricing_identity_id": identity["pricing_identity_id"], "catalog_version": CATALOG_VERSION, **{key: model[key] for key in ("price_low", "price_typical", "price_high", "unit", "currency", "price_scope", "pricing_method", "confidence", "formula_description", "model_metadata", "effective_from", "status")}, "source_material_id": material["material_id"]})

    for species, thickness, unit, low, typical, high, formula in SOLID_PANEL_MODELS:
        code = f"laminated_solid_{species}_{thickness}"
        attributes = {"material_family": "laminated solid wood panel", "construction": "laminated", "species": species, "thickness_mm": thickness}
        name = f"Laminated solid wood panel, {species}, {thickness} mm"
        name_he = f"לוח עץ מלא מודבק, {('אורן' if species == 'pine' else 'אלון')}, {thickness} מ״מ"
        material = _material_payload(code=code, name=name, name_he=name_he, unit=unit, attributes=attributes)
        identity = _identity_payload(attributes=attributes, base_unit=unit, canonical_name=name, canonical_name_he=name_he)
        physical_materials.append(material)
        identities.append(identity)
        members.append({"pricing_identity_id": identity["pricing_identity_id"], "material_id": material["material_id"], "membership_basis": "exact_price_class"})
        model = {"model_price_id": str(uuid5(NAMESPACE_URL, EXPANSION_NAMESPACE + f"model/{code}")), "material_id": material["material_id"], "market_code": MARKET_CODE, "catalog_version": CATALOG_VERSION, "price_low": str(low), "price_typical": str(typical), "price_high": str(high), "unit": unit, "currency": "ILS", "price_scope": "material_only", "pricing_method": "modeled_from_israel_anchor", "confidence": 55, "anchor_count": 1, "formula_description": formula, "model_metadata": {"public_source": "Tsidky materials and prices", "vat_included": True, "butcher_block_normalized_to": "laminated solid wood panel"}, "effective_from": str(date.today()), "status": "active"}
        material_prices.append(model)
        identity_prices.append({"pricing_identity_price_id": str(uuid5(NAMESPACE_URL, IDENTITY_NAMESPACE + "price/" + identity["pricing_identity_code"])), "pricing_identity_id": identity["pricing_identity_id"], "catalog_version": CATALOG_VERSION, **{key: model[key] for key in ("price_low", "price_typical", "price_high", "unit", "currency", "price_scope", "pricing_method", "confidence", "formula_description", "model_metadata", "effective_from", "status")}, "source_material_id": material["material_id"]})
    return {"identities": identities, "members": members, "identity_prices": identity_prices, "materials": physical_materials, "material_prices": material_prices}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    client = get_supabase_client()
    payloads = build_payloads(client)
    print({key: len(value) for key, value in payloads.items()} | {"mode": "apply" if args.apply else "dry_run"})
    if not args.apply:
        return
    client.table("reference_materials").upsert(payloads["materials"], on_conflict="material_id").execute()
    client.table("market_material_model_prices").upsert(payloads["material_prices"], on_conflict="material_id,market_code,catalog_version").execute()
    client.table("reference_material_pricing_identities").upsert(payloads["identities"], on_conflict="market_code,pricing_identity_code").execute()
    client.table("reference_material_pricing_identity_members").upsert(payloads["members"], on_conflict="pricing_identity_id,material_id").execute()
    client.table("market_material_pricing_identity_prices").upsert(payloads["identity_prices"], on_conflict="pricing_identity_id,catalog_version").execute()


if __name__ == "__main__":
    main()
