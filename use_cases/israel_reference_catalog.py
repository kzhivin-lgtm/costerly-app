"""Read purchasable Israel Reference positions for the Material Engine.

Runtime consumers receive one position per Family plus Pricing Key.  Storage
uses several normalized relations, but those relations must not leak into the
resolver contract or recreate the retired price-identity path.
"""

from __future__ import annotations

from typing import Any

from use_cases.material_normalization import material_catalog_display_label


def _rows(client: Any, table: str, *, filters: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    start = 0
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        page = query.range(start, start + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        start += 1000


def load_active_israel_reference_positions(client: Any) -> list[dict[str, Any]]:
    """Return active Israel Reference positions, prices and purchase formats."""
    families = _rows(client, "reference_material_families", filters={"active": True})
    family_code_by_id = {
        str(row.get("family_id") or ""): str(row.get("family_code") or "")
        for row in families
    }
    models = _rows(client, "reference_material_models", filters={"active": True})
    model_ids = {str(row.get("material_model_id") or "") for row in models}
    listings_by_model = {
        str(row.get("material_model_id") or ""): row
        for row in _rows(
            client, "reference_market_material_listings", filters={"market_code": "IL", "active": True}
        )
        if str(row.get("material_model_id") or "") in model_ids
    }
    attributes: dict[str, dict[str, Any]] = {}
    for row in _rows(client, "reference_material_model_attribute_values", filters={}):
        model_id = str(row.get("material_model_id") or "")
        if model_id in model_ids:
            attributes.setdefault(model_id, {})[str(row.get("attribute_code") or "")] = row.get("attribute_value")
    model_by_legacy_material = {
        str(row.get("legacy_material_id") or ""): str(row.get("material_model_id") or "")
        for row in _rows(
            client,
            "reference_market_material_legacy_mappings",
            filters={"market_code": "IL", "classification_status": "mapped"},
        )
        if str(row.get("material_model_id") or "") in listings_by_model
    }
    prices: dict[str, list[dict[str, Any]]] = {}
    for row in _rows(client, "market_material_model_prices", filters={"market_code": "IL", "status": "active"}):
        model_id = model_by_legacy_material.get(str(row.get("material_id") or ""))
        if model_id:
            prices.setdefault(model_id, []).append(row)
    formats: dict[str, list[dict[str, Any]]] = {}
    for row in _rows(client, "reference_market_material_supply_formats", filters={"active": True}):
        formats.setdefault(str(row.get("market_material_listing_id") or ""), []).append(row)
    positions = []
    for model in models:
        model_id = str(model.get("material_model_id") or "")
        listing = listings_by_model.get(model_id)
        if listing is None:
            continue
        family_id = str(model.get("family_id") or "")
        family_code = family_code_by_id.get(family_id, "")
        model_specs = attributes.get(model_id, {})
        model_prices = prices.get(model_id, [])
        model_formats = formats.get(str(listing.get("market_material_listing_id") or ""), [])
        label_specs = dict(model_specs)
        if len(model_prices) == 1:
            label_specs.update(model_prices[0].get("model_metadata") or {})
        positions.append({
            # Resolver treats the normalized storage model ID as an opaque position.
            "reference_position_id": model_id,
            "family_id": family_id,
            "family_code": family_code,
            "canonical_name": str(model.get("canonical_name") or ""),
            "display_label": material_catalog_display_label(
                model.get("canonical_name"), family=family_code, specifications=label_specs,
                purchase_kind="sheet" if any(row.get("purchase_unit") == "sheet" for row in model_formats) else "",
            ),
            "specifications": model_specs,
            "prices": model_prices,
            "supply_formats": model_formats,
        })
    return positions
