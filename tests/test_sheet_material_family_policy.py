from use_cases.sheet_material_family_policy import (
    HPL_FACED,
    RAW,
    STANDARD_FACED,
    VENEER_FACED,
    sheet_estimation_specifications,
)


def test_plywood_variants_keep_source_identity_but_normalize_to_raw_estimation_class():
    for source_attributes in (
        {"thickness_mm": 17, "plywood_variant": "twin"},
        {"thickness_mm": 17, "plywood_variant": "combi"},
        {"thickness_mm": 17, "species": "okoume"},
    ):
        resolved = sheet_estimation_specifications(
            material_family="plywood", extracted_specifications=source_attributes
        )

        assert resolved["construction"] == RAW
        assert "plywood_variant" not in resolved
        assert "species" not in resolved


def test_mdf_policy_keeps_actual_facing_classes_separate():
    assert sheet_estimation_specifications(
        material_family="mdf", extracted_specifications={"thickness_mm": 19, "colour": "white"}
    )["construction"] == STANDARD_FACED
    assert sheet_estimation_specifications(
        material_family="mdf", extracted_specifications={"thickness_mm": 19, "coating": "formica"}
    )["construction"] == HPL_FACED
    assert sheet_estimation_specifications(
        material_family="mdf", extracted_specifications={"thickness_mm": 19, "coating": "veneer"}
    )["construction"] == VENEER_FACED
