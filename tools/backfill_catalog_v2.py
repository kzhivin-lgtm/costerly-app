"""Backfill legacy reference materials into Catalog V2.

Default mode is read-only. ``--apply`` writes only V2 models, listings,
attributes and legacy mappings. It never mutates legacy catalog, prices,
supplier offers, Price Source records, or UI-facing readers.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client
from use_cases.catalog_migration_map import MAPPED, classify_legacy_material
from use_cases.catalog_v2_backfill_payloads import build_catalog_v2_backfill_payload
from use_cases.catalog_v2_backfill_preview import preview_legacy_material_backfill


BATCH_SIZE = 200
MARKET_CODE = "IL"


def _chunks(items: list[Any], size: int = BATCH_SIZE) -> Iterable[list[Any]]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _active_legacy_rows(client: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for start in range(0, 10_000, 1_000):
        page = (
            client.table("reference_materials")
            .select("material_id,material_code,department,canonical_name,base_unit,specifications,reference_material_categories(category_name)")
            .eq("active", True)
            .range(start, start + 999)
            .execute()
            .data
            or []
        )
        rows.extend(page)
        if len(page) < 1_000:
            break
    return rows


def _category_name(row: dict[str, Any]) -> str | None:
    return (row.get("reference_material_categories") or {}).get("category_name")


def build_plan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = [classify_legacy_material(row, category_name=_category_name(row)) for row in rows]
    previews = [
        preview_legacy_material_backfill(row, category_name=_category_name(row))
        for row in rows
    ]
    mapped_previews = [preview for preview in previews if preview is not None]
    model_codes = [preview.global_model_code for preview in mapped_previews]
    listing_codes = [preview.israel_listing_code for preview in mapped_previews]
    return {
        "rows": rows,
        "decisions": decisions,
        "previews": mapped_previews,
        "status_counts": Counter(decision.status for decision in decisions),
        "reason_counts": Counter(decision.reason for decision in decisions),
        "model_code_collisions": sum(count - 1 for count in Counter(model_codes).values() if count > 1),
        "listing_code_collisions": sum(count - 1 for count in Counter(listing_codes).values() if count > 1),
    }


def _assert_safe_plan(plan: dict[str, Any], family_codes: set[str]) -> None:
    if plan["model_code_collisions"] or plan["listing_code_collisions"]:
        raise RuntimeError("Backfill plan has model or listing code collisions.")
    missing_families = sorted({preview.family_code for preview in plan["previews"]} - family_codes)
    if missing_families:
        raise RuntimeError(f"Backfill plan refers to unseeded families: {missing_families}")
    if any(preview.primary_attribute_value is None for preview in plan["previews"]):
        raise RuntimeError("Mapped plan contains a missing required primary attribute.")


def _fetch_by_codes(client: Any, table: str, field: str, codes: list[str], columns: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chunk in _chunks(codes):
        rows.extend(client.table(table).select(columns).in_(field, chunk).execute().data or [])
    return rows


def apply_plan(client: Any, plan: dict[str, Any]) -> dict[str, int]:
    families = client.table("reference_material_families").select("family_id,family_code").eq("active", True).execute().data or []
    family_ids = {row["family_code"]: row["family_id"] for row in families}
    _assert_safe_plan(plan, set(family_ids))

    payloads = [build_catalog_v2_backfill_payload(preview) for preview in plan["previews"]]
    for chunk in _chunks(payloads):
        client.table("reference_material_models").upsert(
            [{
                "family_id": family_ids[payload.material_model["family_code"]],
                "brand_id": None,
                "material_model_code": payload.material_model["material_model_code"],
                "canonical_name": payload.material_model["canonical_name"],
                "active": True,
            } for payload in chunk],
            on_conflict="material_model_code",
        ).execute()

    model_rows = _fetch_by_codes(
        client, "reference_material_models", "material_model_code",
        [payload.material_model["material_model_code"] for payload in payloads],
        "material_model_id,family_id,material_model_code",
    )
    model_ids = {row["material_model_code"]: row for row in model_rows}
    if len(model_ids) != len(payloads):
        raise RuntimeError("Model persistence did not return every requested model.")

    for chunk in _chunks(payloads):
        client.table("reference_material_model_attribute_values").upsert(
            [{
                "material_model_id": model_ids[payload.model_attribute_value["material_model_code"]]["material_model_id"],
                "family_id": model_ids[payload.model_attribute_value["material_model_code"]]["family_id"],
                "attribute_code": payload.model_attribute_value["attribute_code"],
                "attribute_value": payload.model_attribute_value["attribute_value"],
            } for payload in chunk],
            on_conflict="material_model_id,attribute_code",
        ).execute()
        client.table("reference_market_material_listings").upsert(
            [{
                "market_code": MARKET_CODE,
                "material_model_id": model_ids[payload.market_listing["material_model_code"]]["material_model_id"],
                "listing_code": payload.market_listing["listing_code"],
                "canonical_market_name": payload.market_listing["canonical_market_name"],
                "availability_status": "unknown",
                "active": True,
            } for payload in chunk],
            on_conflict="market_code,material_model_id",
        ).execute()

    listing_rows = _fetch_by_codes(
        client, "reference_market_material_listings", "material_model_id",
        [row["material_model_id"] for row in model_rows],
        "market_material_listing_id,material_model_id",
    )
    listing_ids = {row["material_model_id"]: row["market_material_listing_id"] for row in listing_rows}
    if len(listing_ids) != len(payloads):
        raise RuntimeError("Listing persistence did not return every requested listing.")

    mapped_by_legacy = {payload.legacy_mapping["legacy_material_id"]: payload for payload in payloads}
    mapping_rows = []
    for row, decision in zip(plan["rows"], plan["decisions"], strict=True):
        payload = mapped_by_legacy.get(str(row["material_id"]))
        if payload is None:
            mapping_rows.append({
                "legacy_material_id": row["material_id"],
                "market_code": MARKET_CODE,
                "family_id": None,
                "material_model_id": None,
                "market_material_listing_id": None,
                "classification_status": decision.status,
                "classification_basis": "deterministic_rule",
                "classification_evidence": {"reason": decision.reason, "primary_attribute_code": decision.primary_attribute_code},
            })
        else:
            model = model_ids[payload.material_model["material_model_code"]]
            mapping_rows.append({
                "legacy_material_id": row["material_id"],
                "market_code": MARKET_CODE,
                "family_id": model["family_id"],
                "material_model_id": model["material_model_id"],
                "market_material_listing_id": listing_ids[model["material_model_id"]],
                "classification_status": "mapped",
                "classification_basis": "deterministic_rule",
                "classification_evidence": payload.legacy_mapping["classification_evidence"],
            })
    for chunk in _chunks(mapping_rows):
        client.table("reference_market_material_legacy_mappings").upsert(chunk, on_conflict="legacy_material_id").execute()

    return {"models": len(payloads), "listings": len(payloads), "mappings": len(mapping_rows)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write V2 rows after integrity gates pass.")
    args = parser.parse_args()
    client = get_supabase_client()
    plan = build_plan(_active_legacy_rows(client))
    print({
        "mode": "apply" if args.apply else "dry_run",
        "rows": len(plan["rows"]),
        "status_counts": dict(sorted(plan["status_counts"].items())),
        "reason_counts": dict(sorted(plan["reason_counts"].items())),
        "model_code_collisions": plan["model_code_collisions"],
        "listing_code_collisions": plan["listing_code_collisions"],
    })
    if args.apply:
        print(apply_plan(client, plan))


if __name__ == "__main__":
    main()
