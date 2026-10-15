from decimal import Decimal

from use_cases.metal_mass_calculator import kilograms_per_metre, kilograms_per_sheet


def test_metal_mass_calculator_uses_cross_section_and_catalog_density():
    assert kilograms_per_metre(
        family_code="metal_flat_bar",
        specifications={"metal_type": "carbon steel", "width_thickness": {"width_mm": 30, "thickness_mm": 1.5}},
    ) == Decimal("0.353250")


def test_metal_mass_calculator_uses_catalog_sheet_geometry():
    assert kilograms_per_sheet(
        specifications={"metal_type": "carbon steel", "thickness": 1.5},
        length_mm=3000, width_mm=1500,
    ) == Decimal("52.9875")
