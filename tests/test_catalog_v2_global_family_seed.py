from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "db/sql/2026_10_11_catalog_v2_global_family_seed.sql"


def _sql() -> str:
    return SEED.read_text(encoding="utf-8").lower()


def test_global_family_seed_is_additive_and_does_not_backfill_legacy_rows():
    sql = _sql()

    assert "global family registry seed" in sql
    assert "reference_material_categories_v2" in sql
    assert "reference_material_families" in sql
    assert "reference_material_family_attributes" in sql
    assert "reference_material_family_operation_eligibilities" in sql
    assert "insert into public.reference_materials" not in sql
    assert "update public.reference_materials" not in sql
    assert "delete from public.reference_materials" not in sql
    assert "reference_market_material_legacy_mappings" not in sql


def test_seed_covers_accepted_departments_roles_and_stone_without_unapproved_operation():
    sql = _sql()

    for family in (
        "mdf_hdf",
        "sheet_metal",
        "glass",
        "natural_stone_slab",
        "paint_lacquer_stain",
        "hardware_hinge",
        "packaging_material",
    ):
        assert f"'{family}'" in sql

    assert "'stone_edge_profiling'" not in sql
    assert "'consumable'" in sql
    assert "'packaging'" in sql


def test_seed_only_links_to_existing_reference_operation_codes():
    sql = _sql()

    assert "join public.reference_operations operation using (operation_code)" in sql
    assert "where operation.active" in sql
    assert "on conflict (family_id, operation_id) do update set active = true" in sql
