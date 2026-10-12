from use_cases.material_normalization import (
    canonical_display_name,
    canonical_material_display_name,
    normalize_identity_attributes,
)


def test_identity_normalizer_retains_only_domain_attributes_not_source_prose():
    identity = normalize_identity_attributes({
        "thickness_mm": 17,
        "primary_attribute": "17 mm",
        "brand": "Egger",
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
        "depth_mm": 0,
        "diameter_mm": 0,
        "wall_thickness_mm": 0,
        "primary_attribute": "17 mm",
        "brand": "Egger",
        "brand_basis": "unknown",
        "product_system": "",
        "plywood_variant": "",
        "species": "",
        "substrate": "",
        "surface": "",
        "coating": "",
        "colour": "black",
        "grade": "",
        "construction": "double-sided",
        "finish": "",
        "metal_type": "",
        "section_profile": "",
        "stone_type": "",
        "coating_system": "",
        "chemistry_product_type": "",
        "component_type": "",
        "packaging_type": "",
    }


def test_shared_display_contract_is_entity_primary_brand_then_secondaries():
    name = canonical_display_name("plywood", {
        "primary_attribute": "17 mm",
        "brand": "Egger",
        "brand_basis": "catalog",
        "species": "okoume",
        "construction": "double-sided",
        "finish": "matte",
        "colour": "black",
        "seller_prose": "not included",
    })

    assert name == "Plywood 17 mm Egger, Okoume, double-sided, matte, black"


def test_shared_display_contract_adds_proven_second_key_dimension_before_brand():
    name = canonical_display_name("plywood", {
        "primary_attribute": "17 mm",
        "length_mm": 3100,
        "width_mm": 1220,
        "brand": "Egger",
        "brand_basis": "catalog",
        "plywood_variant": "twin",
    })

    assert name == "Plywood 17 mm 3100 × 1220 mm Egger, Twin"


def test_shared_display_contract_omits_unconfirmed_brand_candidate():
    name = canonical_display_name("plywood", {
        "primary_attribute": "17 mm",
        "brand": "Mario Box",
        "brand_basis": "candidate",
        "plywood_variant": "twin",
    })

    assert name == "Plywood 17 mm, Twin"


def test_shared_display_contract_title_cases_plywood_variant_once():
    name = canonical_display_name("plywood", {
        "primary_attribute": "17 mm",
        "plywood_variant": "twin",
    })

    assert name == "Plywood 17 mm, Twin"


def test_processed_material_projections_share_the_canonical_name_component():
    name = canonical_material_display_name(
        "drawer slide",
        {"brand": "BLUM", "product_system": "MOVENTO", "depth_mm": 750},
        fallback="מסילה למגירה בלום",
    )

    assert name == "Drawer Slide 750 mm Blum, Movento"
    assert canonical_material_display_name("other", {}, fallback="Supplier wording") == "Supplier wording"


def test_known_product_system_uses_one_canonical_display_spelling():
    identity = normalize_identity_attributes({"brand": "BLUM", "product_system": "MOVENTO"})

    assert identity["brand"] == "Blum"
    assert identity["product_system"] == "Movento"
