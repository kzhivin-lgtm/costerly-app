from use_cases.estimation_v3_material_facts import _pricing_key_fields_by_resolver_family


def test_v3_agent_context_omits_legacy_pricing_field_names_not_allowed_by_its_contract():
    fields = _pricing_key_fields_by_resolver_family(
        families={"sheet"},
        material_families=[{"family_id": "family-sheet", "family_code": "sheet", "active": True}],
        material_pricing_policies=[{
            "family_id": "family-sheet", "pricing_key_attribute_codes": ["thickness"],
            "purchase_format_policy": "required", "active": True,
        }],
    )

    assert fields == {"sheet": ("thickness_mm",)}


def test_v3_agent_context_exposes_the_approved_natural_stone_pricing_key():
    fields = _pricing_key_fields_by_resolver_family(
        families={"natural_stone_slab"},
        material_families=[{
            "family_id": "family-stone", "family_code": "natural_stone_slab", "active": True,
        }],
        material_pricing_policies=[{
            "family_id": "family-stone", "pricing_key_attribute_codes": ["thickness", "stone_type"],
            "purchase_format_policy": "required", "active": True,
        }],
    )

    assert fields == {"natural_stone_slab": ("thickness_mm", "stone_type")}


def test_drawer_slide_catalog_length_is_an_accepted_resolver_key_field():
    fields = _pricing_key_fields_by_resolver_family(
        families={"hardware_drawer_slide"},
        material_families=[{"family_id": "drawer", "family_code": "hardware_drawer_slide", "active": True}],
        material_pricing_policies=[{"family_id": "drawer", "pricing_key_attribute_codes": ["nominal_length"], "active": True}],
    )

    assert fields == {"hardware_drawer_slide": ("length_mm",)}


def test_purchased_component_type_is_an_accepted_resolver_key_field():
    fields = _pricing_key_fields_by_resolver_family(
        families={"purchased_fabricated_component"},
        material_families=[{
            "family_id": "component", "family_code": "purchased_fabricated_component", "active": True,
        }],
        material_pricing_policies=[{
            "family_id": "component", "pricing_key_attribute_codes": ["component_type"], "active": True,
        }],
    )

    assert fields == {"purchased_fabricated_component": ("component_type",)}
