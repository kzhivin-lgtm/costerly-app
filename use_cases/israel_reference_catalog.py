"""Read purchasable Israel Reference positions for the Material Engine.

Runtime consumers receive one position per Family plus Pricing Key.  Storage
uses several normalized relations, but those relations must not leak into the
resolver contract or recreate the retired price-identity path.
"""

from __future__ import annotations

from typing import Any

from use_cases.material_normalization import material_catalog_display_label


def _rows(client: Any, table: str, *, filters: dict[str, Any], in_filter=None) -> list[dict[str, Any]]:
    if in_filter is not None:
        field, values = in_filter
        values = list(dict.fromkeys(values))
        if not values:
            return []
        if len(values) > 100:
            return [row for start in range(0, len(values), 100)
                    for row in _rows(client, table, filters=filters, in_filter=(field, values[start:start + 100]))]
    result: list[dict[str, Any]] = []
    start = 0
    while True:
        query = client.table(table).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        if in_filter is not None:
            query = query.in_(field, values)
        page = query.range(start, start + 999).execute().data or []
        result.extend(dict(row) for row in page)
        if len(page) < 1000:
            return result
        start += 1000


def load_active_israel_reference_positions(client: Any, *, family_codes=None, model_ids=None) -> list[dict[str, Any]]:
    """Return active Israel Reference positions, prices and purchase formats."""
    scoped = family_codes is not None or model_ids is not None
    families = _rows(client, "reference_material_families", filters={"active": True},
                     **({"in_filter": ("family_code", family_codes)} if family_codes is not None else {}))
    family_code_by_id = {
        str(row.get("family_id") or ""): str(row.get("family_code") or "")
        for row in families
    }
    def selected(table, filters, field, values):
        return _rows(client, table, filters=filters,
                     **({"in_filter": (field, values)} if scoped else {}))

    models = selected("reference_material_models", {"active": True},
                      "material_model_id" if model_ids is not None else "family_id",
                      model_ids if model_ids is not None else family_code_by_id)
    model_ids = {str(row.get("material_model_id") or "") for row in models}
    listings_by_model = {
        str(row.get("material_model_id") or ""): row
        for row in selected("reference_market_material_listings", {"market_code": "IL", "active": True},
                            "material_model_id", model_ids)
        if str(row.get("material_model_id") or "") in model_ids
    }
    attributes: dict[str, dict[str, Any]] = {}
    for row in selected("reference_material_model_attribute_values", {}, "material_model_id", model_ids):
        model_id = str(row.get("material_model_id") or "")
        if model_id in model_ids:
            attributes.setdefault(model_id, {})[str(row.get("attribute_code") or "")] = row.get("attribute_value")
    model_by_legacy_material = {
        str(row.get("legacy_material_id") or ""): str(row.get("material_model_id") or "")
        for row in selected("reference_market_material_legacy_mappings",
                            {"market_code": "IL", "classification_status": "mapped"}, "material_model_id", model_ids)
        if str(row.get("material_model_id") or "") in listings_by_model
    }
    prices: dict[str, list[dict[str, Any]]] = {}
    for row in selected("market_material_model_prices", {"market_code": "IL", "status": "active"},
                        "material_id", model_by_legacy_material):
        model_id = model_by_legacy_material.get(str(row.get("material_id") or ""))
        if model_id:
            prices.setdefault(model_id, []).append(row)
    formats: dict[str, list[dict[str, Any]]] = {}
    for row in selected("reference_market_material_supply_formats", {"active": True}, "market_material_listing_id",
                        [row["market_material_listing_id"] for row in listings_by_model.values()]):
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
