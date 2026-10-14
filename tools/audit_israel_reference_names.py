#!/usr/bin/env python3
"""Read-only structural audit for Israel Reference canonical names.

The Israel catalog has a different job from raw source evidence.  Every active
model and its Israel Listing must show the same human-facing name, while the
raw original description remains in the legacy evidence record.  This tool
checks the invariants before any catalog-name migration is applied.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.supabase_client import get_supabase_client


OUTPUT = ROOT / "notes" / "ISRAEL_REFERENCE_NAME_AUDIT_3_17_4_1.md"


def _rows(client: Any, table: str, fields: str, **filters: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = client.table(table).select(fields)
        for column, value in filters.items():
            query = query.eq(column, value)
        page = query.range(offset, offset + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        offset += 1000


def _first_examples(rows: list[dict[str, Any]], *, limit: int = 3) -> str:
    return "<br>".join(str(row["canonical_name"]) for row in rows[:limit]) or "none"


def main() -> int:
    client = get_supabase_client()
    families = _rows(client, "reference_material_families", "family_id,family_code,family_name", active=True)
    models = _rows(
        client,
        "reference_material_models",
        "material_model_id,family_id,material_model_code,canonical_name",
        active=True,
    )
    listings = _rows(
        client,
        "reference_market_material_listings",
        "material_model_id,listing_code,canonical_market_name",
        active=True,
        market_code="IL",
    )

    family_by_id = {str(row["family_id"]): row for row in families}
    listing_by_model = {str(row["material_model_id"]): row for row in listings}
    code_counts = Counter(str(row["material_model_code"]) for row in models)
    name_counts = Counter(str(row["canonical_name"]).casefold() for row in models)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for model in models:
        family = family_by_id.get(str(model["family_id"]), {})
        by_family[str(family.get("family_code") or "unassigned")].append(model)

    missing_listing = [row for row in models if str(row["material_model_id"]) not in listing_by_model]
    mismatched_listing = [
        row for row in models
        if str(row["material_model_id"]) in listing_by_model
        and str(row["canonical_name"]) != str(listing_by_model[str(row["material_model_id"])]["canonical_market_name"])
    ]
    non_unique_codes = sum(count - 1 for count in code_counts.values() if count > 1)
    non_unique_names = sum(count - 1 for count in name_counts.values() if count > 1)
    underscored_names = [row for row in models if "_" in str(row["canonical_name"])]
    blank_names = [row for row in models if not str(row["canonical_name"]).strip()]

    lines = [
        "# Israel Reference Canonical Name Audit, 3.17.4.1",
        "",
        "Status: read-only. This verifies technical name integrity before the canonical-order migration.",
        "",
        "## Technical integrity",
        "",
        f"- Active Global Models: {len(models)}",
        f"- Active Israel Listings: {len(listings)}",
        f"- Models without an Israel Listing: {len(missing_listing)}",
        f"- Model and Listing display-name mismatches: {len(mismatched_listing)}",
        f"- Duplicate model codes: {non_unique_codes}",
        f"- Duplicate display names: {non_unique_names}",
        f"- Blank display names: {len(blank_names)}",
        f"- Display names with underscores: {len(underscored_names)}",
        "",
        "## Required canonical order",
        "",
        "`Entity → every Pricing Key attribute in Family-policy order → confirmed brand → ordered secondary attributes`.",
        "Raw supplier/source text is evidence only and is not allowed to determine word order.",
        "",
        "## Current samples by Family",
        "",
        "| Family | Active models | Sample current names |",
        "| --- | ---: | --- |",
    ]
    for family_code, rows in sorted(by_family.items()):
        lines.append(f"| {family_code} | {len(rows)} | {_first_examples(sorted(rows, key=lambda row: str(row['canonical_name'])))} |")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"models={len(models)} listings={len(listings)} missing_listing={len(missing_listing)} mismatches={len(mismatched_listing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
