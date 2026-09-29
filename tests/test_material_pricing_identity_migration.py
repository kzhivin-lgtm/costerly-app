from pathlib import Path


MIGRATION = Path("db/sql/2026_09_29_material_pricing_identity_v1.sql")


def test_pricing_identity_migration_is_additive_and_keeps_detail_separate():
    sql = MIGRATION.read_text()

    assert "create table if not exists public.reference_material_pricing_identities" in sql
    assert "create table if not exists public.reference_material_pricing_identity_members" in sql
    assert "create table if not exists public.market_material_pricing_identity_prices" in sql
    assert "add column if not exists pricing_identity_id" in sql
    assert "delete from public.reference_materials" not in sql
    assert "update public.company_material_items" not in sql
    assert "material_identity_v3" not in sql


def test_pricing_identity_migration_protects_catalog_and_private_company_data():
    sql = MIGRATION.read_text()

    for table in (
        "reference_material_pricing_identities",
        "reference_material_pricing_identity_members",
        "market_material_pricing_identity_prices",
    ):
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on public.{table} from public, anon, authenticated" in sql
        assert f"grant all on public.{table} to service_role" in sql


def test_pricing_identity_explicitly_ignores_decorative_variation():
    sql = MIGRATION.read_text()

    for ignored_field in (
        "colour",
        "color",
        "decor",
        "pattern",
        "supplier_sku",
        "supplier_name",
    ):
        assert f"'{ignored_field}'" in sql
