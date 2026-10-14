from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db/sql/2026_10_14_shared_material_aliases.sql"
SEED = ROOT / "db/sql/2026_10_14_shared_material_aliases_seed.sql"


def test_shared_alias_schema_is_catalog_data_and_staff_only():
    sql = SCHEMA.read_text(encoding="utf-8").lower()

    for table in (
        "reference_material_family_aliases",
        "reference_material_family_ambiguous_aliases",
        "reference_material_family_ambiguous_alias_candidates",
        "reference_material_pricing_key_aliases",
        "reference_material_pricing_key_value_aliases",
        "reference_measurement_unit_aliases",
        "reference_operation_aliases",
    ):
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"public.{table}" in sql

    assert "only unambiguous aliases may" in sql
    assert "conversion_factor numeric" in sql
    assert "price, purchase format or company catalog item" in sql


def test_seed_populates_every_family_and_common_measurement_units():
    sql = SEED.read_text(encoding="utf-8").lower()

    assert "insert into public.reference_material_family_aliases" in sql
    assert "insert into public.reference_material_pricing_key_aliases" in sql
    assert "insert into public.reference_material_pricing_key_value_aliases" in sql
    assert "insert into public.reference_measurement_unit_aliases" in sql
    assert "reference_material_family_pricing_policies policy" in sql
    for family in ("mdf_hdf", "plywood", "metal_tube", "hardware_hinge", "packaging_material"):
        assert f"'{family}'" in sql
    for unit in ("'mm'", "'sqm'", "'piece'", "'sheet'", "'roll'"):
        assert unit in sql
