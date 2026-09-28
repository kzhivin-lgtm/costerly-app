from pathlib import Path


SQL_PATH = (
    Path(__file__).parents[1]
    / "db/sql/2026_09_28_archive_company_price_source_v1.sql"
)


def test_archive_source_migration_is_transactional_and_recoverable():
    sql = SQL_PATH.read_text().lower()

    assert sql.startswith("-- 3.15.4")
    assert "begin;" in sql
    assert "commit;" in sql
    assert "create or replace function public.archive_company_price_source" in sql
    assert "set status = 'archived'" in sql
    assert "company_material_offers" in sql
    assert "company_price_sources" in sql
    assert "company_material_items" in sql
    assert "material_identity_resolution_events" not in sql.split("begin", 2)[-1]
    assert "delete from" not in sql


def test_archive_source_rpc_is_service_role_only():
    sql = SQL_PATH.read_text().lower()

    assert "security definer" in sql
    assert "from public, anon, authenticated" in sql
    assert "to service_role" in sql
