from use_cases.catalog_aliases import build_estimation_alias_context


def test_estimation_context_uses_only_active_catalog_aliases_for_requested_families():
    context = build_estimation_alias_context(
        source_family_to_catalog_family={
            "mdf": "mdf_hdf",
            "metal profile": "metal_profile_angle_channel",
        },
        pricing_key_fields_by_family={
            "mdf": ("thickness_mm",),
            "metal profile": ("profile_section", "metal_type"),
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
        "mdf": {
            "catalog_family": "mdf_hdf",
            "family_aliases": ["МДФ"],
            "pricing_key_aliases": {"thickness_mm": ["толщина"]},
        },
        "metal profile": {
            "catalog_family": "metal_profile_angle_channel",
            "family_aliases": ["профиль металлический"],
            "pricing_key_aliases": {
                "profile_section": ["сечение"],
                "metal_type": ["сталь"],
            },
        },
    }
