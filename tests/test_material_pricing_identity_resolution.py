from use_cases.material_pricing_identity_resolution import (
    resolve_material_pricing_identity,
)


def _identity(identity_id, **price_attributes):
    return {
        "pricing_identity_id": identity_id,
        "market_code": "IL",
        "status": "active",
        "price_attributes": price_attributes,
    }


def test_decor_and_colour_do_not_block_the_same_pricing_identity():
    result = resolve_material_pricing_identity(
        material_family="plywood",
        specifications={
            "thickness_mm": 4,
            "surface": "raw",
            "colour": "walnut decor 654",
            "decor": "supplier collection no. 91",
        },
        market_code="IL",
        pricing_identities=(
            _identity(
                "plywood_raw_4",
                material_family="plywood",
                thickness_mm=4,
                surface="raw",
            ),
        ),
    )

    assert result.status == "resolved"
    assert result.selected_pricing_identity_id == "plywood_raw_4"


def test_raw_plywood_does_not_become_an_arbitrary_birch_grade():
    result = resolve_material_pricing_identity(
        material_family="plywood",
        specifications={"thickness_mm": 4, "surface": "raw"},
        market_code="IL",
        pricing_identities=(
            _identity(
                "plywood_raw_4",
                material_family="plywood",
                thickness_mm=4,
                surface="raw",
            ),
            _identity(
                "birch_plywood_bbb_4",
                material_family="plywood",
                thickness_mm=4,
                surface="raw",
                species="birch",
                grade="B/B",
            ),
        ),
    )

    assert result.status == "resolved"
    assert result.selected_pricing_identity_id == "plywood_raw_4"


def test_price_bearing_construction_is_not_ignored():
    result = resolve_material_pricing_identity(
        material_family="plywood",
        specifications={"thickness_mm": 4, "surface": "formica"},
        market_code="IL",
        pricing_identities=(
            _identity(
                "plywood_raw_4",
                material_family="plywood",
                thickness_mm=4,
                surface="raw",
            ),
        ),
    )

    assert result.status == "needs_review"
    assert result.selected_pricing_identity_id is None


def test_ambiguous_price_classes_are_not_auto_linked():
    result = resolve_material_pricing_identity(
        material_family="plywood",
        specifications={"thickness_mm": 4},
        market_code="IL",
        pricing_identities=(
            _identity("plywood_raw_4", material_family="plywood", thickness_mm=4),
            _identity("plywood_raw_4_other", material_family="plywood", thickness_mm=4),
        ),
    )

    assert result.status == "shortlist"
    assert result.selected_pricing_identity_id is None


def test_missing_exact_thickness_never_uses_a_nearby_price_class():
    result = resolve_material_pricing_identity(
        material_family="birch plywood",
        specifications={"thickness_mm": 17, "surface": "raw"},
        market_code="IL",
        pricing_identities=(
            _identity(
                "plywood_raw_18",
                material_family="plywood",
                thickness_mm=18,
                surface="raw",
            ),
        ),
    )

    assert result.status == "needs_review"
    assert result.selected_pricing_identity_id is None


def test_butcher_block_is_an_alias_of_laminated_solid_wood_not_a_price_family():
    result = resolve_material_pricing_identity(
        material_family="solid timber butcher block",
        specifications={"thickness_mm": 20, "construction": "laminated", "species": "oak"},
        market_code="IL",
        pricing_identities=(
            _identity(
                "oak_laminated_panel_20",
                material_family="laminated solid wood panel",
                thickness_mm=20,
                construction="laminated",
                species="oak",
            ),
        ),
    )

    assert result.status == "resolved"
    assert result.selected_pricing_identity_id == "oak_laminated_panel_20"
