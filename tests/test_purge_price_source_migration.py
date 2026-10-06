from pathlib import Path


SQL_PATH = (
    Path(__file__).parents[1]
    / "db/sql/2026_10_06_purge_company_price_source.sql"
)


def test_purge_source_migration_is_transactional_and_deletes_source_owned_data():
    sql = SQL_PATH.read_text(encoding="utf-8").lower()

    assert sql.startswith("-- 3.16.7")
    assert "begin;" in sql
    assert "commit;" in sql
    assert "create or replace function public.purge_company_price_source" in sql
    assert "delete from public.company_service_offers" in sql
    assert "set identity_candidate_id = null" in sql
    assert "candidate.source_row_id = any(source_row_ids)" in sql
    assert "delete from public.company_material_offers" in sql
    assert "delete from public.company_supplier_operation_offers" in sql
    assert "delete from public.company_supplier_aliases" in sql
    assert "delete from public.material_identity_resolution_events" in sql
    assert "delete from public.material_identity_candidates" in sql
    assert "delete from public.company_material_aliases" in sql
    assert "delete from public.company_price_source_rows" in sql
    assert "delete from public.company_price_sources" in sql


def test_purge_source_preserves_materials_still_used_elsewhere_and_is_service_only():
    sql = SQL_PATH.read_text(encoding="utf-8").lower()

    assert "not exists" in sql
    assert "company_material_offers" in sql
    assert "set created_from_source_id = null" in sql
    assert "security definer" in sql
    assert "from public, anon, authenticated" in sql
    assert "to service_role" in sql
