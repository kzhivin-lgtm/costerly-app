from use_cases.catalog_migration_map import (
    EXCLUDED_BY_POLICY,
    MAPPED,
    REVIEW_REQUIRED,
    classify_legacy_material,
)


def _row(**overrides):
    row = {
        "material_code": "gcm_wood_panel_001",
        "department": "wood",
        "canonical_name": "Plywood, raw, 18 mm",
        "specifications": {"global_canonical_id": "GCM-V1-PLYWOOD-RAW-18"},
    }
    row.update(overrides)
    return row


def test_known_category_maps_to_global_family_model_and_israel_variant():
    decision = classify_legacy_material(_row(), category_name="Plywood")

    assert decision.status == MAPPED
    assert decision.family_code == "plywood"
    assert decision.production_department_code == "wood"
    assert decision.global_model_code == "gcm_v1_plywood_raw_18"
    assert decision.israel_variant_code == "il_gcm_wood_panel_001"


def test_metal_requires_shape_evidence_but_can_use_proven_geometry_words():
    decision = classify_legacy_material(
        _row(department="metal", canonical_name="Aluminium 1050, plate, anodized"),
        category_name="Aluminium",
    )
    assert decision.status == MAPPED
    assert decision.family_code == "sheet_metal"

    unresolved = classify_legacy_material(
        _row(department="metal", canonical_name="Aluminium 1050"),
        category_name="Aluminium",
    )
    assert unresolved.status == REVIEW_REQUIRED
    assert unresolved.family_code is None


def test_consumable_is_excluded_without_creating_a_catalog_identity():
    decision = classify_legacy_material(
        _row(department="consumable", canonical_name="Contact adhesive"),
        category_name="Adhesives, sealants and fillers",
    )
    assert decision.status == EXCLUDED_BY_POLICY
    assert decision.entity_role_code == "consumable"
    assert decision.global_model_code is None


def test_unknown_category_remains_explicitly_review_required():
    decision = classify_legacy_material(_row(department="wood"), category_name="Unproven category")
    assert decision.status == REVIEW_REQUIRED
    assert decision.reason == "legacy_category_or_geometry_does_not_prove_one_approved_family"
