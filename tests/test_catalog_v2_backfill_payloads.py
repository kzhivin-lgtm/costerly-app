from use_cases.catalog_v2_backfill_payloads import build_catalog_v2_backfill_payload
from use_cases.catalog_v2_backfill_preview import CatalogV2BackfillPreview


def test_payload_keeps_global_identity_market_listing_and_legacy_mapping_separate():
    payload = build_catalog_v2_backfill_payload(
        CatalogV2BackfillPreview(
            legacy_material_id="00000000-0000-0000-0000-000000000001",
            family_code="plywood",
            global_model_code="gcm_v1_plywood_raw_18",
            global_canonical_name="Plywood, raw, 18 mm",
            primary_attribute_code="thickness",
            primary_attribute_value=18,
            market_code="IL",
            israel_listing_code="il_gcm_wood_panel_001",
            israel_canonical_name="Plywood, raw, 18 mm",
        )
    )

    assert payload.material_model["family_code"] == "plywood"
    assert payload.model_attribute_value["attribute_value"] == 18
    assert payload.market_listing["market_code"] == "IL"
    assert payload.market_listing["availability_status"] == "unknown"
    assert "purchase_unit" not in payload.market_listing
    assert payload.legacy_mapping["classification_status"] == "mapped"
