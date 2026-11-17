"""Record priced finished-glass evidence in Israel Reference; default is dry run."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from db.supabase_client import get_supabase_client

EVIDENCE = Path(__file__).resolve().parents[1] / (
    "notes/evidence/glass-mirrors-il/agan-barzel-2026-11-17.json"
)
SEED = "https://costerly.ai/israel-reference/glass-mirrors/agan-barzel"
MARKET = "IL"
SUPPLIER = "Agan Barzel"


def identifier(key):
    return str(uuid5(NAMESPACE_URL, f"{SEED}/{key}"))


def build_reference_rows(evidence):
    date = evidence["observed_on"]
    vat_rate = Decimal(1) + Decimal(evidence["vat_percent"]) / 100
    sources, offers = [], []
    for name, source in evidence["sources"].items():
        source_id = identifier(f"source/{name}/{date}")
        sources.append({
            "source_id": source_id, "market_code": MARKET, "source_type": "retailer",
            "source_channel": "specialist_retailer", "source_name": f"{SUPPLIER}: {name}",
            "source_url": source["url"], "source_date": date, "language_code": "he",
            "evidence": {"date_basis": "observed", "vat_percent": evidence["vat_percent"], **source},
        })
        if name == "tempered":
            specs = [
                (thickness, grade, base, (source["extra_clear_surcharge_ils_m2"] if grade == "extra_clear" else 0))
                for thickness, base in source["base_rate_by_thickness_mm"].items()
                for grade in ("clear", "extra_clear")
            ]
        else:
            specs = [(source["thickness_mm"], "silver", source["gross_rate_ils_m2"], 0)]
        for thickness, grade, base, premium in specs:
            identity = {
                "clear": "Glass, {} mm, Tempered safety",
                "extra_clear": "Glass, {} mm, Low-iron extra-clear",
                "silver": "Mirror, {} mm, Silver",
            }[grade].format(thickness)
            term = Decimal(base) * Decimal(str(source.get("area_surcharge_rate_fraction", 0)))
            gross = Decimal(base + premium) + term  # Exact public calculator at 1000 × 1000 mm.
            billing = (
                {"min_billable_m2_per_piece": source["min_billable_m2_per_piece"]}
                if name == "tempered"
                else {"min_gross_ils_per_piece": source["min_gross_ils_per_piece"]}
            )
            offers.append((identity, {
                "market_offer_id": identifier(f"offer/{grade}/{thickness}/{date}"),
                "market_code": MARKET, "source_id": source_id, "supplier_name": SUPPLIER,
                "supplier_sku": source["source_sku"],
                "source_price": str(gross), "source_currency": "ILS",
                "source_unit": "finished_rectangle_1000x1000_mm", "price_scope": "fabricated_component",
                "included_services": source["coverage"], "delivery_included": False,
                "package_quantity": 1, "vat_mode": "included", "valid_from": date,
                # Pricing is nonlinear. A normalized area rate would be mistaken for a raw stock baseline.
                "normalized_unit": None, "normalized_price_ex_vat": None,
                "confidence": 100, "status": "candidate",
                "conversion_basis": {
                    "offer_usage": "supplier_specific_retail_benchmark",
                    "pricing_basis": "per_finished_piece_using_its_area",
                    "base_gross_rate_ils_m2": base, "optical_surcharge_gross_ils_m2": premium,
                    "gross_area_surcharge_ils_m2": float(term), "vat_percent": evidence["vat_percent"],
                    "price_reference_net_ils": str((gross / vat_rate).quantize(Decimal("0.000001"))),
                    "dimensions_mm": source["dimensions_mm"], "shape": "rectangle",
                    "grade": grade, "thickness_mm": int(thickness),
                    "heat_treatment": "tempered" if name == "tempered" else None,
                    "special_features_included": False, "installation_included": False,
                    **billing,
                },
            }))
    return sources, offers


def resolve_material_ids(client, names):
    # Live model IDs are authoritative; offers still reference the linked legacy material IDs.
    models = client.table("reference_material_models").select(
        "material_model_id,canonical_name"
    ).in_("canonical_name", sorted(names)).eq("active", True).execute().data
    result = {}
    for name in names:
        [model_id] = [m["material_model_id"] for m in models if m["canonical_name"] == name]
        [mapping] = client.table("reference_market_material_legacy_mappings").select(
            "legacy_material_id"
        ).eq("material_model_id", model_id).eq("market_code", MARKET).eq(
            "classification_status", "mapped"
        ).execute().data
        result[name] = mapping["legacy_material_id"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    sources, specs = build_reference_rows(json.loads(EVIDENCE.read_text()))
    client = get_supabase_client()
    ids = resolve_material_ids(client, {identity for identity, _ in specs})
    offers = [dict(offer, material_id=ids[identity]) for identity, offer in specs]
    print(f"{len(sources)} supplier sources; {len(offers)} fabricated-component candidates, no baseline changes.")
    if not args.apply:
        return
    for table, rows, key in (
        ("reference_sources", sources, "source_id"),
        ("market_material_offers", offers, "market_offer_id"),
    ):
        client.table(table).upsert(rows, on_conflict=key, ignore_duplicates=True).execute()
        saved = client.table(table).select("*").in_(key, [row[key] for row in rows]).execute().data
        by_id = {row[key]: row for row in saved}
        for expected in rows:
            actual = by_id[expected[key]]
            for field, value in expected.items():
                observed = actual[field]
                if field == "source_price":
                    observed, value = Decimal(str(observed)), Decimal(str(value))
                if observed != value:
                    raise ValueError(f"Israel Reference readback differs for {table}.{field}: {expected[key]}")
    print(f"Readback verified {len(offers)} offers and {len(sources)} sources.")


if __name__ == "__main__":
    main()
