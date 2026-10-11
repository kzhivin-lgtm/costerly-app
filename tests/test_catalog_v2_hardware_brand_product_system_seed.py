from pathlib import Path

from use_cases.hardware_product_system_registry import (
    HARDWARE_BRAND_SEEDS,
    PRODUCT_SYSTEM_SEEDS,
)
from use_cases.price_source_taxonomy import BRAND_RULES


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "db/sql/2026_10_11_catalog_v2_hardware_brand_product_system_seed.sql"


def _sql() -> str:
    return SEED.read_text(encoding="utf-8").lower()


def test_hardware_brand_seed_contains_all_source_agent_hardware_brands():
    sql = _sql()

    assert len(HARDWARE_BRAND_SEEDS) == 15
    for brand in HARDWARE_BRAND_SEEDS:
        assert f"'{brand.code}'" in sql
        assert f"'{brand.canonical_name.lower()}'" in sql

    source_agent_hardware = {
        rule.brand: rule.aliases for rule in BRAND_RULES if rule.categories == ("Hardware",)
    }
    seeded_hardware = {seed.canonical_name: seed.aliases for seed in HARDWARE_BRAND_SEEDS}
    assert seeded_hardware == source_agent_hardware


def test_product_system_seed_is_global_and_never_a_supplier_sku_crosswalk():
    sql = _sql()

    assert "reference_brand_product_systems" in sql
    assert "reference_brand_product_system_aliases" in sql
    assert "references public.reference_material_family_brand_scopes(family_id, brand_id)" in sql
    assert "supplier_sku" not in sql
    assert "company_material" not in sql
    assert "reference_market_material_listings" not in sql
    assert "insert into public.reference_material_models" not in sql
    assert "insert into public.reference_brands" in sql

    assert len(PRODUCT_SYSTEM_SEEDS) >= 100
    for system in PRODUCT_SYSTEM_SEEDS:
        assert f"'{system.code}'" in sql
        assert f"'{system.canonical_name.lower()}'" in sql


def test_hardware_family_attribute_contract_can_hold_system_without_inventing_variant():
    sql = _sql()

    for family in (
        "hardware_drawer_slide",
        "hardware_drawer_system",
        "hardware_hinge",
        "hardware_lift_system",
        "hardware_door_system",
        "hardware_storage_system",
        "hardware_connector",
    ):
        assert f"('{family}', 'product_system'" in sql
