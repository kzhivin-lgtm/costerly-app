#!/usr/bin/env python3
"""Apply the November 2026 Israel Reference tape evidence; dry run by default."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client
from use_cases.israel_reference_catalog import load_active_israel_reference_positions

CHECKED_DATE = "2026-11-16"
SRYA = "https://sryawood.co.il/collections/חומרי-גלם-ציפויים-ומשטחים-קנטים-קנט-פורניר"
SRYA_TAX = "https://sryawood.co.il/policies/terms-of-service"
DOMICILE = "https://www.domicile.co.il/wp-content/uploads/2020/07/KVE_infopage_01.pdf"
TWIZERS = "https://www.twizers.com/edges/"
MAKOR = "https://makorhaformaika.co.il/catalogs/melamine/"
BANDS = {24: "up to 24 mm wide", 45: "25-45 mm wide", 65: "46-65 mm wide"}
TAPES = ("Melamine edge band", "Real wood veneer edge band")


def srya_offer(sku, species, width, thickness, pack_m, pack_ils):
    return dict(source=SRYA, sku=sku, species=species, width_mm=width,
                tape_thickness_mm=thickness, pack_m=pack_m, posted_pack_ils=pack_ils,
                adhesive="not_declared", tax_terms_source=SRYA_TAX)


NARROW = [
    srya_offer("KVE123172", "white oak", 23, 1, 100, 331.20),
    srya_offer("KVE123152", "American walnut", 23, 1, 100, 404.80),
]
WIDE = [
    srya_offer("KVE134172", "white oak", 34, 1, 50, 257.60),
    srya_offer("KVE134152", "walnut", 34, 1, 50, 303.60),
    srya_offer("KVE1540172", "white oak", 40, 1.5, 100, 680),
    srya_offer("KVE1540152", "walnut", 40, 1.5, 100, 680),
]


def price_update(price, tape, width):
    is_veneer = tape == TAPES[1]
    evidence = dict(checked_on=CHECKED_DATE, estimate_unit="m", nominal_roll_m=50)
    metadata = dict(price["model_metadata"])
    patch = {}
    if is_veneer:
        offers = NARROW if width == 24 else WIDE
        if width == 24:
            low, typical, high = 3.31, 3.68, 4.05
            formula = "Mean of two posted 23 mm × 1 mm roll prices per metre; proxy for the 24 mm band."
        elif width == 45:
            low, typical, high = 5.15, 6.80, 7.65
            formula = ("Posted 40 mm × 1.5 mm roll price per metre as a proxy for the 45 mm band. "
                       "Lower bound from the 34 mm oak offer; upper bound scales 40 mm to 45 mm.")
        else:
            low, typical, high = 7.44, 9.82, 11.05
            formula = "45 mm band estimate scaled by 65/45; no local offer confirmed for the 65 mm band."
        evidence.update(status="nearest_width_price_proxy" if width < 65 else "extrapolated_quote_required",
                        price_observations=offers,
                        purchase_note="Nominal roll is for estimating only. Use the supplier's actual pack for buying.")
        if width <= 45:
            evidence["unpriced_offers"] = [
                dict(source=DOMICILE, species=["white oak", "American walnut"],
                     width_mm=22 if width == 24 else 34, tape_thickness_mm=0.6,
                     pack_m=50, adhesive="pre_glued"),
                dict(source=TWIZERS, species=["natural oak V30", "American walnut V30"],
                     width_mm=23 if width == 24 else 50, tape_thickness_mm=0.8,
                     adhesive="not_declared", pack_m=None),
            ]
        patch.update(price_low=low, price_typical=typical, price_high=high, anchor_count=len(offers),
                     pricing_method="modeled_from_israel_anchor", formula_description=formula,
                     confidence=55 if width == 24 else 45 if width == 45 else 25)
    else:
        evidence.update(status="existing_allowance_no_current_public_quote", market_source=MAKOR,
                        purchase_note="Matched edging exists. Melamine tape price, adhesive and supplier pack unverified.")
    metadata["edge_market_evidence"] = evidence
    return dict(patch, model_metadata=metadata)


def updates(positions):
    for tape in TAPES:
        for width, band in BANDS.items():
            name = f"Edge banding, {width} × 0.8 mm, {tape}, 0.8 mm, {band}"
            hits = [p for p in positions if p["family_code"] == "edge_banding" and p["canonical_name"] == name]
            if len(hits) != 1:
                raise ValueError(f"Expected one active position: {name}")
            (price,) = hits[0]["prices"]
            (roll,) = hits[0]["supply_formats"]
            dimensions = roll["purchasable_dimensions"]
            if (price["market_code"], price["status"], price["unit"], price["currency"], price["price_scope"],
                roll["purchase_unit"], dimensions["length_mm"], dimensions["format_source"]) != (
                "IL", "active", "m", "ILS", "material_only", "roll", 50000, "owner_approved_roll_meter_pricing"
            ):
                raise ValueError(f"Unexpected active price or roll format: {name}")
            if (dimensions["width_mm"] not in {24, width} or dimensions["thickness_mm"] != 0.8
                    or roll["supply_format_code"] not in {"standard_roll_50000x24", f"standard_roll_50000x{width}"}):
                raise ValueError(f"Refusing to rewrite a different supply format: {name}")
            yield name, "reference_market_material_supply_formats", "supply_format_id", roll, dict(
                supply_format_code=f"standard_roll_50000x{width}",
                purchasable_dimensions=dict(dimensions, width_mm=width),
            )
            yield name, "market_material_model_prices", "model_price_id", price, price_update(price, tape, width)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the verified changes to Israel Reference")
    args = parser.parse_args()
    client = get_supabase_client()
    try:
        plan = list(updates(load_active_israel_reference_positions(client)))
        for name, table, pk, row, patch in plan:
            if all(row[key] == val for key, val in patch.items()):
                print(f"Current: {name} ({table})")
                continue
            if pk == "model_price_id":
                print(f"{name}: ₪{row['price_typical']} -> ₪{patch.get('price_typical', row['price_typical'])}/m")
            else:
                print(f"{name}: roll width {row['purchasable_dimensions']['width_mm']} -> "
                      f"{patch['purchasable_dimensions']['width_mm']} mm")
            if args.apply:
                stamp = datetime.now(timezone.utc).isoformat()
                result = (client.table(table).update(dict(patch, updated_at=stamp)).eq(pk, row[pk])
                          .eq("updated_at", row["updated_at"]).execute().data)
                if len(result) != 1 or any(result[0][key] != val for key, val in patch.items()):
                    raise ValueError(f"Write not verified: {name}")
        if args.apply:
            for name, _, _, row, patch in updates(load_active_israel_reference_positions(client)):
                if any(row[key] != val for key, val in patch.items()):
                    raise ValueError(f"Read-back not verified: {name}")
            print("Verified six active Israel Reference positions after update.")
    except ValueError:
        raise
    except Exception as exc:
        raise SystemExit(f"Catalog refresh failed: {type(exc).__name__} ({getattr(exc, 'code', '')})") from None


if __name__ == "__main__":
    main()
