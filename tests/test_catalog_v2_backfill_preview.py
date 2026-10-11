from use_cases.catalog_v2_backfill_preview import (
    ISRAEL_MARKET_CODE,
    preview_legacy_material_backfill,
)


def _row(**overrides):
    row = {
        "material_id": "00000000-0000-0000-0000-000000000001",
        "material_code": "gcm_wood_panel_001",
        "department": "wood",
        "canonical_name": "Plywood, raw, 18 mm",
        "base_unit": "m2",
        "specifications": {
            "global_canonical_id": "GCM-V1-PLYWOOD-RAW-18",
            "thickness_mm": 18,
        },
    }
    row.update(overrides)
    return row


def test_mapped_legacy_row_projects_to_distinct_global_and_israel_layers():
    preview = preview_legacy_material_backfill(_row(), category_name="Plywood")

    assert preview is not None
    assert preview.family_code == "plywood"
    assert preview.global_model_code == "gcm_v1_plywood_raw_18"
    assert preview.primary_attribute_code == "thickness"
    assert preview.primary_attribute_value == 18
    assert preview.market_code == ISRAEL_MARKET_CODE
    assert preview.israel_listing_code == "il_gcm_wood_panel_001"
    assert preview.global_canonical_name == preview.israel_canonical_name


def test_excluded_or_reviewed_rows_never_receive_a_v2_projection():
    assert preview_legacy_material_backfill(
        _row(department="consumable", canonical_name="Contact adhesive"),
        category_name="Adhesives, sealants and fillers",
    ) is None
    assert preview_legacy_material_backfill(
        _row(canonical_name="Plywood, raw", specifications={}),
        category_name="Plywood",
    ) is None
