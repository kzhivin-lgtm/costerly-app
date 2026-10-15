from tools.audit_material_pipeline import audit_material_pipeline


def test_catalog_driven_audit_reports_v3_and_israel_contract_gaps_without_inventing_data():
    rows = audit_material_pipeline(
        material_families=[{"family_id": "f-1", "family_code": "sheet", "active": True}],
        material_pricing_policies=[{
            "family_id": "f-1", "pricing_key_attribute_codes": ["thickness"],
            "purchase_format_policy": "required", "active": True,
        }],
        price_source_family_aliases={"sheet": ("sheet",)},
        estimation_alias_context={"sheet": {"family_aliases": ["sheet"]}},
        reference_positions=[{
            "reference_position_id": "sheet-18", "family_code": "sheet",
            "specifications": {"thickness_mm": 18},
            "prices": [{
                "model_price_id": "price-1", "status": "active", "currency": "ILS",
                "price_scope": "material_only", "unit": "sqm", "price_typical": "50",
            }],
            "supply_formats": [{
                "supply_format_id": "format-1", "active": True,
                "purchasable_dimensions": {"length_mm": 2440, "width_mm": 1220},
            }],
        }],
    )

    assert rows == [{
        "family_code": "sheet", "resolution_scope": "resolver", "pricing_key_fields": ("thickness_mm",),
        "israel_positions": 1, "resolver_eligible_israel_positions": 1,
        "ineligible_reference_reasons": (),
        "issues": (),
    }]


def test_catalog_driven_audit_reports_an_unknown_v3_pricing_field():
    rows = audit_material_pipeline(
        material_families=[{"family_id": "f-1", "family_code": "drawer", "active": True}],
        material_pricing_policies=[{
            "family_id": "f-1", "pricing_key_attribute_codes": ["unmodeled_catalog_field"],
            "purchase_format_policy": "not_required", "active": True,
        }],
        price_source_family_aliases={}, estimation_alias_context={}, reference_positions=[],
    )

    assert rows[0]["issues"] == (
        "v3_contract_missing:unmodeled_catalog_field",
        "price_source_family_alias_missing",
        "estimation_family_alias_missing",
    )


def test_catalog_driven_audit_excludes_formula_overhead_families_from_resolver_gaps():
    rows = audit_material_pipeline(
        material_families=[{"family_id": "f-1", "family_code": "packaging_material", "active": True}],
        material_pricing_policies=[{
            "family_id": "f-1", "pricing_key_attribute_codes": ["packaging_type"],
            "purchase_format_policy": "not_required", "active": True,
        }],
        price_source_family_aliases={}, estimation_alias_context={}, reference_positions=[],
    )

    assert rows[0]["resolution_scope"] == "formula_overhead"
    assert rows[0]["issues"] == ()
