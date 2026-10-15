from use_cases.catalog_aliases import (
    build_estimation_alias_context,
    build_price_source_alias_context,
    normalize_measurement_unit,
)


def test_estimation_context_uses_only_active_catalog_aliases_for_requested_families():
    context = build_estimation_alias_context(
        family_codes=("mdf_hdf", "metal_profile_angle_channel"),
        pricing_key_fields_by_family={
            "mdf_hdf": ("thickness_mm",),
            "metal_profile_angle_channel": ("profile_section", "metal_type"),
        },
        family_rows=[
            {"family_id": "mdf-id", "family_code": "mdf_hdf"},
            {"family_id": "profile-id", "family_code": "metal_profile_angle_channel"},
        ],
        family_alias_rows=[
            {"family_id": "mdf-id", "alias_text": "МДФ"},
            {"family_id": "profile-id", "alias_text": "профиль металлический"},
        ],
        pricing_key_alias_rows=[
            {"family_id": "mdf-id", "fact_field": "thickness_mm", "alias_text": "толщина"},
            {"family_id": "profile-id", "fact_field": "profile_section", "alias_text": "сечение"},
            {"family_id": "profile-id", "fact_field": "metal_type", "alias_text": "сталь"},
            {"family_id": "profile-id", "fact_field": "wall_thickness_mm", "alias_text": "стенка"},
        ],
    )

    assert context == {
        "mdf_hdf": {
            "catalog_family": "mdf_hdf",
            "family_aliases": ["МДФ"],
            "pricing_key_aliases": {"thickness_mm": ["толщина"]},
        },
        "metal_profile_angle_channel": {
            "catalog_family": "metal_profile_angle_channel",
            "family_aliases": ["профиль металлический"],
            "pricing_key_aliases": {
                "profile_section": ["сечение"],
                "metal_type": ["сталь"],
            },
        },
    }


def test_price_source_context_uses_catalog_rows_and_preserves_ambiguity():
    context = build_price_source_alias_context(
        family_rows=[
            {"family_id": "mdf-id", "family_code": "mdf_hdf", "category_name": "Wood panels"},
            {"family_id": "slide-id", "family_code": "hardware_drawer_slide", "category_name": "Hardware"},
        ],
        family_alias_rows=[{"family_id": "mdf-id", "alias_text": "МДФ"}],
        ambiguous_family_alias_rows=[{"alias_key": "laminated panel"}],
        attribute_value_alias_rows=[
            {"family_id": "mdf-id", "fact_field": "metal_type", "canonical_value": "carbon steel", "alias_text": "steel"},
            {"family_id": "mdf-id", "fact_field": "section_profile", "canonical_value": "square tube", "alias_text": "квадратная труба"},
        ],
        brand_rows=[{"brand_id": "blum-id", "canonical_name": "Blum"}],
        brand_alias_rows=[{"brand_id": "blum-id", "alias_key": "בלום"}],
        product_system_rows=[{
            "product_system_id": "movento-id", "canonical_name": "Movento", "brand_name": "Blum",
            "family_id": "slide-id",
        }],
        product_system_alias_rows=[{"product_system_id": "movento-id", "alias_key": "מובנטו"}],
        operation_rows=[{"operation_id": "cut-id", "operation_code": "panel_saw_cutting"}],
        operation_alias_rows=[{
            "operation_id": "cut-id", "alias_key": "חיתוך", "service_only": True,
        }],
        measurement_unit_alias_rows=[{
            "alias_key": "см", "unit_code": "mm", "dimension_code": "length", "conversion_factor": 10,
        }],
    )

    assert context.family_aliases == {"mdf_hdf": ("МДФ",)}
    assert context.family_categories == {
        "mdf_hdf": "Wood panels",
        "hardware_drawer_slide": "Hardware",
    }
    assert context.ambiguous_family_aliases == {"laminated panel"}
    assert context.attribute_value_aliases == {
        "mdf_hdf": {
            "metal_type": {"carbon steel": ("steel",)},
            "section_profile": {"square tube": ("квадратная труба",)},
        },
    }
    assert context.brand_aliases == {"בלום": "Blum"}
    assert context.product_system_aliases == {"מובנטו": ("Movento", "Blum", "hardware_drawer_slide")}
    assert context.operation_aliases == {
        "חיתוך": {"operation_code": "panel_saw_cutting", "service_only": True},
    }
    assert context.measurement_unit_aliases["cm"]["conversion_factor"] == 10
    assert normalize_measurement_unit("см", alias_context=context) == "mm"
    assert normalize_measurement_unit("unknown", alias_context=context) == ""
