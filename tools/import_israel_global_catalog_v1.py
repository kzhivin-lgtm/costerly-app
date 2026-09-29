#!/usr/bin/env python3
"""Atomically install the approved Israel Global Catalog V1 into production."""

from __future__ import annotations

import argparse
import hashlib
import re
import uuid
from collections import OrderedDict
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from openpyxl import load_workbook
from psycopg.types.json import Jsonb


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = Path(
    "/Users/qb/Documents/ChatGPT/Costerly/outputs/01a0e6ca-de59-7263-a24f-1c3e9210bdfc/"
    "ISRAEL_PRICING_MODEL_V1_3_PURCHASED_COMPONENTS_FULL_2026_09_29.xlsx"
)
FOUNDATION_SQL = ROOT / "db/sql/2026_09_29_israel_global_catalog_v1_foundation.sql"
CONNECTION_FILE = ROOT / "tmp/production_db_url.env"
CATALOG_VERSION = "israel_global_catalog_v1"
FINGERPRINT = "IL:global_catalog_v1:4436:8872:2026-09-29"

DEPARTMENTS = {
    "Wood panels": "wood",
    "Decorative surfaces": "wood",
    "Solid wood": "wood",
    "Metals": "metal",
    "Glass and mirrors": "glass_stone_plastic",
    "Stone and mineral surfaces": "glass_stone_plastic",
    "Plastics and composites": "glass_stone_plastic",
    "Coatings and finishes": "coating",
    "Furniture hardware": "hardware",
    "Fasteners and connectors": "hardware",
    "Electrical and lighting": "hardware",
    "Specialist components": "hardware",
    "Upholstery": "consumable",
    "Adhesives and sealants": "consumable",
    "Abrasives and shop consumables": "consumable",
    "Installation materials": "consumable",
    "Packaging": "packaging",
}


def stable_uuid(value: str) -> uuid.UUID:
    digest = list(hashlib.sha1(value.encode("utf-8")).hexdigest()[:32])
    digest[12] = "5"
    digest[16] = "89ab"[int(digest[16], 16) % 4]
    return uuid.UUID("".join(digest))


def category_code(name: str) -> str:
    return f"gcm_{hashlib.sha1(name.encode('utf-8')).hexdigest()[:24]}"


def load_connection_url() -> str:
    contents = CONNECTION_FILE.read_text()
    match = re.search(r"^SUPABASE_DB_URL='(.*)'$", contents, re.MULTILINE)
    if not match or not match.group(1):
        raise RuntimeError("tmp/production_db_url.env is not configured")
    return match.group(1)


def load_payload() -> tuple[list[tuple], list[tuple], list[tuple], list[tuple]]:
    workbook = load_workbook(WORKBOOK, read_only=True, data_only=True)
    sheet = workbook["Catalog Pricing"]
    rows = sheet.values
    header = next(rows)
    index = {str(value): position for position, value in enumerate(header)}
    required = {
        "canonical_id", "category_en", "subcategory_en", "canonical_name_en",
        "canonical_name_he", "pricing_rule_id", "pricing_method", "price_low_ils",
        "price_central_ils", "price_high_ils", "normalized_unit", "confidence",
        "anchor_count", "formula_description", "effective_date", "market_code",
        "currency", "status",
    }
    if required - index.keys():
        raise RuntimeError(f"Workbook columns missing: {sorted(required - index.keys())}")

    categories: OrderedDict[str, tuple] = OrderedDict()
    materials: list[tuple] = []
    aliases: list[tuple] = []
    prices: list[tuple] = []
    for row in rows:
        value = lambda key: row[index[key]]
        global_id = str(value("canonical_id")).strip()
        category = str(value("category_en")).strip()
        subcategory = str(value("subcategory_en")).strip()
        english = str(value("canonical_name_en")).strip()
        hebrew = str(value("canonical_name_he") or "").strip()
        if not global_id or not english or category not in DEPARTMENTS:
            raise RuntimeError(f"Invalid catalog row: {global_id or english or category}")
        material_id = stable_uuid(f"global-canonical-material-v1:{global_id}")
        category_id = category_code(subcategory)
        categories.setdefault(
            category_id, (category_id, subcategory, DEPARTMENTS[category], len(categories) + 1)
        )
        specifications = {
            "catalog_version": CATALOG_VERSION,
            "global_canonical_id": global_id,
            "category_en": category,
            "subcategory_en": subcategory,
            "canonical_name_he": hebrew,
        }
        thickness = re.search(r"(?:^|\s)(\d+(?:\.\d+)?)\s*mm\b", english, re.IGNORECASE)
        if thickness:
            specifications["thickness_mm"] = float(thickness.group(1))
        materials.append((
            material_id, f"gcm_{hashlib.sha1(global_id.encode('utf-8')).hexdigest()[:32]}",
            DEPARTMENTS[category], category_id, english, str(value("normalized_unit") or "ea"),
            Jsonb(specifications),
        ))
        for language, alias_text, alias_kind in (("en-IL", english, "canonical"), ("he-IL", hebrew, "market_name")):
            if alias_text:
                aliases.append((
                    stable_uuid(f"global-canonical-material-v1:{global_id}:{language}:{alias_text}"),
                    material_id, "IL", language, alias_text, alias_kind, True, Decimal("100"),
                ))
        effective = value("effective_date")
        effective_date = effective if isinstance(effective, date) else date.fromisoformat(str(effective))
        prices.append((
            material_id, "IL", CATALOG_VERSION, Decimal(str(value("price_low_ils"))),
            Decimal(str(value("price_central_ils"))), Decimal(str(value("price_high_ils"))),
            str(value("normalized_unit")), str(value("currency")), "material_only",
            str(value("pricing_method")), Decimal(str(value("confidence"))),
            int(value("anchor_count")), str(value("formula_description")),
            Jsonb({"pricing_rule_id": str(value("pricing_rule_id")), "source_status": str(value("status"))}),
            effective_date,
        ))
    if len(materials) != 4436 or len(aliases) != 8872 or len(prices) != 4436:
        raise RuntimeError(f"Unexpected payload sizes: {len(materials)=}, {len(aliases)=}, {len(prices)=}")
    return list(categories.values()), materials, aliases, prices


def copy_rows(cursor, statement: str, rows: list[tuple]) -> None:
    with cursor.copy(statement) as copy:
        for row in rows:
            copy.write_row(row)


def install(*, apply: bool) -> None:
    categories, materials, aliases, prices = load_payload()
    print({"categories": len(categories), "materials": len(materials), "aliases": len(aliases), "prices": len(prices), "mode": "apply" if apply else "dry-run"})
    if not apply:
        return
    url = load_connection_url()
    with psycopg.connect(url, connect_timeout=20) as connection:
        with connection.cursor() as cursor:
            cursor.execute(FOUNDATION_SQL.read_text())
        connection.commit()
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute("""
                    create temporary table _gcm_categories (
                        category_code text, category_name text, department text, sort_order integer
                    ) on commit drop;
                    create temporary table _gcm_materials (
                        material_id uuid, material_code text, department text, category_code text,
                        canonical_name text, base_unit text, specifications jsonb
                    ) on commit drop;
                    create temporary table _gcm_aliases (
                        alias_id uuid, material_id uuid, market_code text, language_code text,
                        alias_text text, alias_kind text, exact_identity boolean, confidence numeric
                    ) on commit drop;
                    create temporary table _gcm_prices (
                        material_id uuid, market_code text, catalog_version text, price_low numeric,
                        price_typical numeric, price_high numeric, unit text, currency text,
                        price_scope text, pricing_method text, confidence numeric, anchor_count integer,
                        formula_description text, model_metadata jsonb, effective_from date
                    ) on commit drop;
                """)
                copy_rows(cursor, "copy _gcm_categories from stdin", categories)
                copy_rows(cursor, "copy _gcm_materials from stdin", materials)
                copy_rows(cursor, "copy _gcm_aliases from stdin", aliases)
                copy_rows(cursor, "copy _gcm_prices from stdin", prices)
                cursor.execute("""
                    insert into public.reference_catalog_versions (
                        catalog_version, market_code, catalog_name, catalog_fingerprint, status
                    ) values (%s, 'IL', 'Israel Global Catalog V1', %s, 'candidate')
                    on conflict (catalog_version) do update set
                        catalog_name = excluded.catalog_name,
                        catalog_fingerprint = excluded.catalog_fingerprint,
                        status = 'candidate', updated_at = now()
                """, (CATALOG_VERSION, FINGERPRINT))
                cursor.execute("""
                    insert into public.reference_material_categories (
                        category_code, category_name, department, active, sort_order
                    ) select category_code, category_name, department, true, sort_order from _gcm_categories
                    on conflict (category_code) do update set
                        category_name = excluded.category_name, department = excluded.department,
                        active = true, sort_order = excluded.sort_order
                """)
                cursor.execute("""
                    insert into public.reference_materials (
                        material_id, material_code, department, category_code, canonical_name,
                        base_unit, specifications, active
                    ) select material_id, material_code, department, category_code, canonical_name,
                        base_unit, specifications, true from _gcm_materials
                    on conflict (material_code) do update set
                        department = excluded.department, category_code = excluded.category_code,
                        canonical_name = excluded.canonical_name, base_unit = excluded.base_unit,
                        specifications = excluded.specifications, active = true, updated_at = now()
                """)
                cursor.execute("""
                    insert into public.reference_material_aliases (
                        alias_id, material_id, market_code, language_code, alias_text, alias_key,
                        alias_kind, exact_identity, confidence, active
                    ) select alias_id, material_id, market_code, language_code, alias_text,
                        public.normalize_reference_material_alias(alias_text), alias_kind,
                        exact_identity, confidence, true from _gcm_aliases
                    on conflict (material_id, market_code, language_code, alias_key) do update set
                        alias_text = excluded.alias_text, alias_kind = excluded.alias_kind,
                        exact_identity = excluded.exact_identity, confidence = excluded.confidence,
                        active = true, updated_at = now()
                """)
                cursor.execute("""
                    insert into public.market_material_model_prices (
                        material_id, market_code, catalog_version, price_low, price_typical, price_high,
                        unit, currency, price_scope, pricing_method, confidence, anchor_count,
                        formula_description, model_metadata, effective_from, status
                    ) select material_id, market_code, catalog_version, price_low, price_typical, price_high,
                        unit, currency, price_scope, pricing_method, confidence, anchor_count,
                        formula_description, model_metadata, effective_from, 'active' from _gcm_prices
                    on conflict (material_id, market_code, catalog_version) do update set
                        price_low = excluded.price_low, price_typical = excluded.price_typical,
                        price_high = excluded.price_high, unit = excluded.unit, currency = excluded.currency,
                        price_scope = excluded.price_scope, pricing_method = excluded.pricing_method,
                        confidence = excluded.confidence, anchor_count = excluded.anchor_count,
                        formula_description = excluded.formula_description,
                        model_metadata = excluded.model_metadata, effective_from = excluded.effective_from,
                        status = 'active', updated_at = now()
                """)
                cursor.execute("""
                    update public.company_material_items set reference_material_id = null
                    where reference_material_id in (
                        select material_id from public.reference_materials
                        where specifications->>'catalog_version' is distinct from %s
                    )
                """, (CATALOG_VERSION,))
                legacy_updates = (
                    "update public.company_material_aliases set active = false, updated_at = now()",
                    "update public.reference_material_aliases set active = false, updated_at = now()",
                    "update public.market_material_profiles set active = false, updated_at = now()",
                    "update public.market_material_offers set status = 'archived'",
                    "update public.market_material_baselines set status = 'archived'",
                    "update public.reference_materials set active = false, updated_at = now()",
                )
                for statement in legacy_updates:
                    cursor.execute(
                        statement + """
                            where material_id in (
                                select material_id from public.reference_materials
                                where specifications->>'catalog_version' is distinct from %s
                            )
                        """ + (" and status <> 'archived'" if "status" in statement else ""),
                        (CATALOG_VERSION,),
                    )
                cursor.execute("""
                    update public.reference_material_categories set active = false
                    where category_code not in (select category_code from _gcm_categories)
                """)
                cursor.execute("""
                    update public.reference_catalog_versions set status = 'retired'
                    where market_code = 'IL' and status = 'active' and catalog_version <> %s
                """, (CATALOG_VERSION,))
                cursor.execute("""
                    update public.reference_catalog_versions set status = 'active', activated_at = now(), updated_at = now()
                    where catalog_version = %s
                """, (CATALOG_VERSION,))
                cursor.execute("""
                    update public.material_resolver_versions set status = 'retired'
                    where market_code = 'IL' and status = 'active' and resolver_version <> 'material_identity_v2'
                """)
                cursor.execute("""
                    insert into public.material_resolver_versions (
                        resolver_version, market_code, algorithm_version, catalog_fingerprint, status, activated_at
                    ) values ('material_identity_v2', 'IL', 'deterministic_v2', %s, 'active', now())
                    on conflict (resolver_version) do update set
                        algorithm_version = excluded.algorithm_version,
                        catalog_fingerprint = excluded.catalog_fingerprint,
                        status = 'active', activated_at = now()
                """, (FINGERPRINT,))
                cursor.execute("""
                    select
                        (select count(*) from public.reference_materials where active) as active_materials,
                        (select count(*) from public.reference_material_aliases where active and market_code = 'IL') as active_aliases,
                        (select count(*) from public.market_material_model_prices where status = 'active') as active_model_prices,
                        (select count(*) from public.reference_materials where not active) as archived_materials,
                        (select resolver_version from public.material_resolver_versions where market_code = 'IL' and status = 'active') as active_resolver
                """)
                print(dict(zip([column.name for column in cursor.description], cursor.fetchone())))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write the catalog to production")
    install(apply=parser.parse_args().apply)
