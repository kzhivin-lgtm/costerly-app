"""Read-only catalog context consumed by Estimation V3 Material Engine."""

from __future__ import annotations

from typing import Any, Mapping

from db.repositories import fetch_estimation_resolver_material_families


def _rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    page_size, start, result = 1_000, 0, []
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(start, start + page_size - 1).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < page_size:
            return result
        start += page_size


def _optional_rows(client: Any, table: str, *, filters: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read a newly introduced catalog extension without breaking a staged deploy."""
    try:
        return _rows(client, table, filters=filters)
    except Exception as exc:
        # PostgREST can expose either PostgreSQL 42P01 or PGRST205 while the
        # application deploy arrives before its additive migration. Do not
        # conceal any other catalog read failure.
        message = str(exc)
        if table in message and ("42P01" in message or "PGRST205" in message or "does not exist" in message):
            return []
        raise


def build_estimation_material_context(client: Any, company_id: str) -> dict[str, Any]:
    """Load only catalog data needed for deterministic material purchasing."""
    return {
        "families": fetch_estimation_resolver_material_families(client),
        "catalogs": {
            "items": _rows(client, "company_material_items", filters={"company_id": company_id}),
            "offers": _rows(client, "company_material_offers", filters={"company_id": company_id}),
            "identities": _rows(client, "reference_material_pricing_identities", filters={"market_code": "IL", "status": "active"}),
            "prices": _rows(client, "market_material_pricing_identity_prices", filters={"status": "active"}),
            "material_families": _rows(client, "reference_material_families", filters={"active": True}),
            "material_pricing_policies": _rows(client, "reference_material_family_pricing_policies", filters={"active": True}),
            "family_supply_formats": _rows(client, "reference_material_family_supply_formats", filters={"active": True}),
            "material_default_variants": _optional_rows(
                client,
                "reference_material_family_default_variants",
                filters={"active": True},
            ),
        },
    }
