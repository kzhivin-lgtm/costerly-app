from use_cases.material_normalization import (
    canonical_display_name,
    normalize_identity_attributes,
)


def test_identity_normalizer_retains_only_domain_attributes_not_source_prose():
    identity = normalize_identity_attributes({
        "thickness_mm": 17,
        "primary_attribute": "17 mm",
        "brand": "EGGER",
        "construction": "double-sided",
        "colour": "black",
        "seller_prose": "special offer while stocks last",
        "marketing_phrase": "premium furniture board",
        "sku": "U999",
    })

    assert identity == {
        "thickness_mm": 17,
        "width_mm": 0,
        "length_mm": 0,
        "diameter_mm": 0,
        "primary_attribute": "17 mm",
        "brand": "EGGER",
        "brand_basis": "unknown",
        "species": "",
        "substrate": "",
        "surface": "",
        "coating": "",
        "colour": "black",
        "grade": "",
        "construction": "double-sided",
        "finish": "",
    }


def test_shared_display_contract_is_entity_primary_brand_then_secondaries():
    name = canonical_display_name("plywood", {
        "primary_attribute": "17 mm",
        "brand": "EGGER",
        "species": "okoume",
        "construction": "double-sided",
        "finish": "matte",
        "colour": "black",
        "seller_prose": "not included",
    })

    assert name == "Plywood 17 mm EGGER, Okoume, double-sided, matte, black"
