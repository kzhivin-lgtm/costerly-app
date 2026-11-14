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
        "board_type": "",
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


def test_material_catalog_display_names_preserve_purchase_identity_facts():
    from use_cases.material_normalization import material_catalog_display_label

    examples = [
        ("Plywood, 16 mm, raw", {}, "Plywood 16 mm"),
        ("Plywood 18 mm 1220 x 2440 millimetres", {"purchase_kind": "sheet"}, "Plywood 18 mm"),
        ("Plywood 18 mm 1220 × 2440 mm", {}, "Plywood 18 mm"),
        ("HDF, 6 mm, High-density fibreboard, raw", {}, "HDF 6 mm"),
        ("Aluminium Angle 100 × 50 mm", {}, "Aluminium Angle 100 × 50 mm"),
        ("Mirror, 4 mm, Low-iron", {}, "Mirror 4 mm"),
        ("Glass, 4 mm, Tempered safety", {}, "Glass 4 mm Tempered safety"),
        ("Side-mount roller runner, 300 mm, 25 kg class", {}, "Side-mount roller runner 300 mm 25 kg class"),
        ("LED aluminium U-profile with diffuser", {}, "LED aluminium U-profile with diffuser"),
        ("LED strip connector, 24 V", {}, "LED strip connector 24 V"),
        ("LED strip standard output, 4000K, 6 W/m", {"specifications": {"voltage_v": 24}}, "LED 4000 K 6 W/m 24 V"),
        ("LED strip 3000K 4,8 W/m 12 V", {}, "LED 3000 K 4.8 W/m 12 V"),
    ]
    for name, kwargs, label in examples:
        assert material_catalog_display_label(name, **kwargs) == label
        assert material_catalog_display_label(label, **kwargs) == label
