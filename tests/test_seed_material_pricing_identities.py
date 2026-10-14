from tools.seed_material_pricing_identities import (
    build_identities,
    build_policy_identities,
)
from tests.helpers.shared_alias_context import shared_alias_context


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


def test_concrete_mdf_name_wins_over_shared_mdf_and_hdf_subcategory():
    identities = build_identities(
        (
            _material(
                "mdf-4",
                "Standard MDF, raw, 4 mm",
                thickness=4,
                subcategory="MDF and HDF",
            ),
            _material(
                "hdf-4",
                "Standard HDF, raw, 4 mm",
                thickness=4,
                subcategory="MDF and HDF",
            ),
        )
    )

    assert {item.price_attributes["material_family"] for item in identities} == {"mdf", "hdf"}


def test_policy_seed_uses_current_family_code_and_only_approved_price_key_facts():
    materials = (
        {
            **_material("mdf-white", "MDF white 19 mm", thickness=19, subcategory="MDF and HDF"),
            "specifications": {"material_family": "mdf", "thickness_mm": 19, "colour": "white"},
        },
        {
            **_material("tube", "Stainless steel 304 tube 40 x 20 x 2 mm", thickness=None, subcategory="Metal"),
            "department": "metal",
            "base_unit": "m",
            "specifications": {"material_family": "metal tube"},
        },
        {
            **_material("tube-incomplete", "Stainless steel tube 40 x 20 mm", thickness=None, subcategory="Metal"),
            "department": "metal",
            "base_unit": "m",
            "specifications": {"material_family": "metal tube"},
        },
    )
    policies = {
        "faced_mdf": {"pricing_key_attribute_codes": ["thickness"]},
        "metal_tube": {"pricing_key_attribute_codes": ["metal_type", "section_profile", "wall_thickness"]},
    }

    identities = build_policy_identities(
        materials,
        pricing_policies=policies,
        alias_context=shared_alias_context(),
    )

    assert {item.price_attributes["material_family"] for item in identities} == {"faced_mdf", "metal_tube"}
    faced_mdf = next(item for item in identities if item.price_attributes["material_family"] == "faced_mdf")
    assert faced_mdf.price_attributes == {
        "material_family": "faced_mdf",
        "thickness_mm": 19,
        "construction": "plastic_laminate_faced",
    }
    tube = next(item for item in identities if item.price_attributes["material_family"] == "metal_tube")
    assert tube.price_attributes == {
        "material_family": "metal_tube",
        "metal_type": "stainless steel 304",
        "section_profile": "rectangular tube",
        "wall_thickness_mm": 2.0,
    }
