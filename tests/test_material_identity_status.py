from use_cases.material_identity_status import (
    material_identity_status,
    material_pricing_selection_key,
)


_DRAWER_SLIDE_POLICY = {
    "hardware_drawer_slide": {
        "pricing_key_attribute_codes": ["nominal_length"],
        "purchase_format_policy": "not_required",
        "active": True,
    }
}


def test_drawer_slide_without_nominal_length_is_yellow_not_review_or_red():
    status = material_identity_status({
        "specifications": {
            "material_family": "drawer slide",
            "brand": "Blum",
            "product_system": "Movento",
        },
    }, pricing_policies=_DRAWER_SLIDE_POLICY)

    assert status.tone == "yellow"
    assert status.missing == ("nominal length",)
    assert status.known_path == ("drawer slide", "brand: Blum", "system: Movento")


def test_complete_endpoint_without_israel_link_is_blue():
    status = material_identity_status({
        "specifications": {"material_family": "drawer slide", "depth_mm": 600},
    }, pricing_policies=_DRAWER_SLIDE_POLICY)

    assert status.tone == "blue"
    assert status.label == "Israel reference link missing"


def test_complete_endpoint_with_israel_link_is_green():
    status = material_identity_status({
        "reference_material_id": "reference-slide-600",
        "specifications": {"material_family": "drawer slide", "depth_mm": 600},
    }, pricing_policies=_DRAWER_SLIDE_POLICY)

    assert status.tone == "green"
    assert status.missing == ()


def test_missing_family_is_red():
    status = material_identity_status({"specifications": {"brand": "Blum"}})

    assert status.tone == "red"
    assert status.missing == ("material family",)


def test_legacy_other_bucket_is_red():
    status = material_identity_status({"specifications": {"material_family": "other"}})

    assert status.tone == "red"
    assert status.missing == ("material family",)


def test_sheet_policy_requires_two_sided_offer_format():
    policy = {
        "plywood": {
            "pricing_key_attribute_codes": ["thickness"],
            "purchase_format_policy": "standard_sheet_2400x1220",
            "active": True,
        }
    }
    item = {"specifications": {"material_family": "plywood", "thickness_mm": 18}}

    incomplete = material_identity_status(
        item, pricing_policies=policy, purchasable_dimensions={"length_mm": 3100},
    )
    complete = material_identity_status(
        item,
        pricing_policies=policy,
        purchasable_dimensions={"length_mm": 3100, "width_mm": 1220},
    )

    assert incomplete.tone == "yellow"
    assert incomplete.missing == ("purchase format",)
    assert complete.tone == "blue"


def test_global_family_code_is_a_valid_resolver_family_without_source_alias():
    key = material_pricing_selection_key(
        material_family="compact_laminate",
        specifications={"thickness_mm": 20},
        pricing_policies={
            "compact_laminate": {"pricing_key_attribute_codes": ["thickness"]}
        },
    )

    assert key == "compact_laminate|thickness=20"


def test_furniture_profile_identity_does_not_require_wall_thickness():
    status = material_identity_status({
        "specifications": {
            "material_family": "metal tube",
            "metal_type": "steel",
            "section_profile": "20 x 20 mm",
        },
    }, pricing_policies={
        "metal_tube": {
            "pricing_key_attribute_codes": ["metal_type", "section_profile"],
            "purchase_format_policy": "required",
            "active": True,
        },
    })

    assert status.tone == "yellow"
    assert status.missing == ("purchase format",)
