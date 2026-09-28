from pathlib import Path


SQL_PATH = (
    Path(__file__).parents[1]
    / "db/sql/2026_09_28_material_resolution_core_v1.sql"
)


def test_material_resolution_core_migration_has_shared_entities_and_guards():
    sql = SQL_PATH.read_text()
    lowered = sql.lower()

    assert lowered.startswith("-- 3.15.3")
    assert "begin;" in lowered
    assert "commit;" in lowered
    assert "create table if not exists public.material_resolver_versions" in lowered
    assert "create table if not exists public.company_material_aliases" in lowered
    assert "create table if not exists public.material_identity_candidates" in lowered
    assert "create table if not exists public.material_identity_resolution_events" in lowered
    assert "jsonb_array_length(candidate_materials) <= 5" in lowered
    assert "material_identity_candidates_review_check" in lowered
    assert "material_identity_candidates_selection_check" in lowered
    assert "reference_material_id uuid" in lowered
    assert "identity_confidence numeric(5, 2)" in lowered
    assert "conversion_confidence numeric(5, 2)" in lowered
    assert "eligibility_confidence numeric(5, 2)" in lowered
    assert "company_material_offers_price_scope_check" in lowered


def test_material_resolution_core_private_tables_have_rls_and_no_client_grants():
    sql = SQL_PATH.read_text().lower()
    tables = (
        "material_resolver_versions",
        "company_material_aliases",
        "material_identity_candidates",
        "material_identity_resolution_events",
    )
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on public.{table} from public, anon, authenticated" in sql
        assert f"grant all on public.{table} to service_role" in sql


def test_material_resolution_core_does_not_reprocess_or_auto_link_rows():
    sql = SQL_PATH.read_text().lower()

    assert "update public.company_material_items" not in sql
    assert "update public.company_price_source_rows" not in sql
    assert "insert into public.material_identity_candidates" not in sql
    assert "insert into public.material_identity_resolution_events" not in sql
