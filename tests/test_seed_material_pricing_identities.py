from tools.seed_material_pricing_identities import build_identities


def _material(material_id, name, *, thickness, subcategory="Plywood"):
    return {
        "material_id": material_id,
        "department": "wood",
        "category_code": "plywood",
        "canonical_name": name,
        "base_unit": "m2",
        "specifications": {"subcategory_en": subcategory, "thickness_mm": thickness},
    }


def test_sheet_colours_and_decorative_names_collapse_but_construction_does_not():
    identities = build_identities(
        (
            _material("raw-a", "Plywood raw white decor A, 4 mm", thickness=4),
            _material("raw-b", "Plywood raw walnut decor B, 4 mm", thickness=4),
            _material("hpl", "Plywood HPL faced, 4 mm", thickness=4),
        )
    )

    assert len(identities) == 2
    raw = next(item for item in identities if item.price_attributes["construction"] == "raw")
    hpl = next(item for item in identities if item.price_attributes["construction"] == "plastic_laminate_faced")
    assert raw.members == ("raw-a", "raw-b")
    assert hpl.members == ("hpl",)
