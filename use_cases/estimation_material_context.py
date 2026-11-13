"""Read-only catalog context consumed by Estimation V3 Material Engine."""

from __future__ import annotations

from typing import Any, Mapping

from db.repositories import fetch_estimation_resolver_material_families
from use_cases.catalog_aliases import build_estimation_alias_context
from use_cases.israel_reference_catalog import load_active_israel_reference_positions


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
    families = fetch_estimation_resolver_material_families(client)
    family_rows = _rows(client, "reference_material_families", filters={"active": True})
    family_alias_context = build_estimation_alias_context(
        family_codes=families, pricing_key_fields_by_family={}, family_rows=family_rows,
        family_alias_rows=_rows(client, "reference_material_family_aliases", filters={"active": True}),
        pricing_key_alias_rows=(),
    )
    return {
        "company_id": company_id,
        "families": families,
        "family_alias_context": family_alias_context,
        "catalogs": {
            "items": _rows(client, "company_material_items", filters={"company_id": company_id}),
            "offers": _rows(client, "company_material_offers", filters={"company_id": company_id}),
            "supplier_operation_offers": _optional_rows(
                client, "company_supplier_operation_offers", filters={"company_id": company_id, "status": "active"},
            ),
            "operations": _optional_rows(client, "reference_operations", filters={"active": True}),
            "israel_operation_prices": _optional_rows(
                client, "market_operation_service_prices", filters={"market_code": "IL", "status": "active"},
            ),
            "reference_positions": load_active_israel_reference_positions(client),
            "material_families": family_rows,
            "material_pricing_policies": _rows(client, "reference_material_family_pricing_policies", filters={"active": True}),
            "material_default_variants": _optional_rows(
                client,
                "reference_material_family_default_variants",
                filters={"active": True},
            ),
        },
    }
