"""Load supplier-observed lighting prices into Israel Reference."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from db.supabase_client import get_supabase_client


EVIDENCE = Path(__file__).resolve().parents[1] / "notes/evidence/estimation-v9.31-led/prices.json"
PROFILE_NAME = "LED aluminium U-profile with diffuser"
STRIP_NAME = "LED strip standard output"
MARKET = "IL"


def identifier(kind, code):
    return str(uuid5(NAMESPACE_URL, f"https://costerly.ai/israel-reference/led/{kind}/{code}"))


def one(client, table, **filters):
    query = client.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    row, = query.execute().data
    return row


def upsert(client, table, rows, conflict):
    if rows:
        client.table(table).upsert(rows, on_conflict=conflict).execute()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    data = json.loads(EVIDENCE.read_text())
    db = get_supabase_client()
    version = one(db, "reference_catalog_versions", market_code=MARKET, status="active")["catalog_version"]
    family = one(db, "reference_material_families", family_code="hardware_electrical_component", active=True)["family_id"]
    strip_model = one(db, "reference_material_models", family_id=family, canonical_name=STRIP_NAME, active=True)
    strip_mapping = one(db, "reference_market_material_legacy_mappings",
                        material_model_id=strip_model["material_model_id"], market_code=MARKET,
                        classification_status="mapped")
    strip_material = one(db, "reference_materials", material_id=strip_mapping["legacy_material_id"])
    strip_price = one(db, "market_material_model_prices", material_id=strip_material["material_id"],
                      market_code=MARKET, catalog_version=version)
    one(db, "reference_market_material_supply_formats",
        market_material_listing_id=strip_mapping["market_material_listing_id"], supply_format_code="spool_5000mm",
        purchase_unit="linear_stock", active=True)
    models, materials, listings, mappings, formats, prices = [], [], [], [], [], []
    multiplier = Decimal(1) + Decimal(data["vat_percent"]) / 100
    date = data["observed_on"]
    sources = [{"source_id": identifier("source", key), "market_code": MARKET, "source_type": "retailer",
                "source_channel": "specialist_retailer", "source_name": supplier, "source_url": url,
                "source_date": date, "language_code": "he", "evidence": {"supplier_sku": sku}}
               for key, (supplier, url, sku) in data["sources"].items()]

    def add_price(material_id, price_id, source, gross, unit, *, metres=1, metadata=None):
        source_url = data["sources"][source][1]
        net = str((Decimal(str(gross)) / multiplier / metres).quantize(Decimal("0.000001")))
        prices.append({
            "model_price_id": price_id, "material_id": material_id, "market_code": MARKET,
            "catalog_version": version, "unit": unit, "currency": "ILS", "price_scope": "retail_package",
            "price_low": net, "price_typical": net, "price_high": net, "status": "active",
            "pricing_method": "derived_from_israel_anchor", "confidence": 85, "anchor_count": 1,
            "formula_description": "Published retail price excluding VAT and normalized to the catalog unit.",
            "effective_from": date,
            "model_metadata": {"source_id": identifier("source", source), "source_url": source_url,
                               "published_gross_ils": gross, "vat_percent": data["vat_percent"],
                               "normalization_metres": metres, **(metadata or {})},
        })

    def add_position(code, name, unit, source, gross, *, metres=1, metadata=None):
        model_id = identifier("model", code)
        material_id = identifier("material", code)
        listing_id = identifier("listing", code)
        models.append({"material_model_id": model_id, "family_id": family, "material_model_code": code,
                       "canonical_name": name})
        materials.append({"material_id": material_id, "material_code": code, "department": "hardware",
                          "category_code": strip_material["category_code"], "canonical_name": name,
                          "base_unit": unit, "specifications": metadata or {}})
        listings.append({"market_material_listing_id": listing_id, "market_code": MARKET,
                         "material_model_id": model_id, "listing_code": code, "canonical_market_name": name,
                         "availability_status": "common"})
        mappings.append({"legacy_material_id": material_id, "market_code": MARKET, "family_id": family,
                         "material_model_id": model_id, "market_material_listing_id": listing_id,
                         "classification_status": "mapped", "classification_basis": "catalog_seed"})
        add_price(material_id, identifier("price", code), source, gross, unit, metres=metres, metadata=metadata)
        return listing_id

    for source, model, watts, base, delta in data["drivers"]:
        code = f"il_ledmaster_{source}_{watts}w"
        add_position(code, f"Constant-voltage LED driver, {model}, 24 V", "ea", source, base + delta,
                     metadata={"led_driver_watts": watts, "voltage_v": 24,
                               "option_delta_ils": delta, "supplier_model": model})
    profile = data["profile"]
    listing = add_position("il_led_aluminium_u_profile_with_diffuser", PROFILE_NAME, "m",
                           profile["source"], profile["displayed_ils"] * profile["stock_m"],
                           metres=profile["stock_m"], metadata={"displayed_unit": "m",
                                                              "displayed_price_ils": profile["displayed_ils"]})
    formats.append({"market_material_listing_id": listing, "supply_format_code": "stock_2000mm",
                    "purchase_unit": "linear_stock", "minimum_purchase_quantity": 1,
                    "purchasable_dimensions": {"length_mm": 2000, "format_source": "estimate_purchase_rule"}})
    strip = data["strip"]
    add_price(strip_material["material_id"], strip_price["model_price_id"], strip["source"], strip["displayed_ils"],
              "m", metres=strip["stock_m"], metadata={
                  "additional_source_id": identifier("source", strip["additional_source"]),
                  "additional_source_url": data["sources"][strip["additional_source"]][1],
                  "rated_w_per_m": strip["rated_w_per_m"], "colour_temperatures_k": [3000, 4000],
                  "voltage_v": strip["voltage"],
              })

    print(f"{len(models)} new or updated positions, {len(prices)} price records, {len(sources)} source pages.")
    if not args.apply:
        return
    for table, rows, conflict in (
        ("reference_sources", sources, "source_id"),
        ("reference_material_models", models, "material_model_id"),
        ("reference_materials", materials, "material_id"),
        ("reference_market_material_listings", listings, "market_material_listing_id"),
        ("reference_market_material_supply_formats", formats, "market_material_listing_id,supply_format_code"),
        ("reference_market_material_legacy_mappings", mappings, "legacy_material_id"),
        ("market_material_model_prices", prices, "model_price_id"),
    ):
        upsert(db, table, rows, conflict)
    expected_ids = [row["model_price_id"] for row in prices]
    checked = db.table("market_material_model_prices").select("model_price_id,price_typical,status").in_(
        "model_price_id", expected_ids).execute().data
    expected = {row["model_price_id"]: Decimal(row["price_typical"]) for row in prices}
    actual = {row["model_price_id"]: Decimal(str(row["price_typical"])) for row in checked if row["status"] == "active"}
    if actual != expected:
        raise RuntimeError("Israel Reference readback did not match the LED price seed")
    print(f"Verified {len(actual)} active price records.")


if __name__ == "__main__":
    main()
