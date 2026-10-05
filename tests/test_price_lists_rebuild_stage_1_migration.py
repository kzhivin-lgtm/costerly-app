from pathlib import Path


SQL_PATH = (
    Path(__file__).parents[1]
    / "db/sql/2026_10_05_price_lists_rebuild_stage_1.sql"
)


def test_stage_1_keeps_supplier_operation_offers_separate_from_material_offers():
    sql = SQL_PATH.read_text().lower()

    assert sql.startswith("-- 3.16.7")
    assert "begin;" in sql
    assert "commit;" in sql
    assert "create table if not exists public.company_supplier_operation_offers" in sql
    assert "operation_id uuid not null references public.reference_operations(operation_id)" in sql
    assert "source_row_id uuid not null references public.company_price_source_rows(row_id)" in sql
    assert "unique (source_row_id)" in sql
    assert "pricing_basis text not null check" in sql
    assert "'supplier_defined'" in sql
    assert "insert into public.company_material_offers" not in sql
    assert "insert into public.company_material_items" not in sql


def test_stage_1_preserves_source_evidence_and_supplier_aliases():
    sql = SQL_PATH.read_text().lower()

    assert "add column if not exists source_supplier_name text" in sql
    assert "add column if not exists row_kind text not null default 'material'" in sql
    assert "add column if not exists reference_operation_id uuid" in sql
    assert "'operation_service'" in sql
    assert "create table if not exists public.company_supplier_aliases" in sql
    assert "alias_kind in ('source_observed', 'manual')" in sql
    assert "unique (company_id, normalized_name)" in sql
    assert "company_price_sources_source_supplier_name_check" in sql
    assert "company_price_source_rows_row_kind_check" in sql
    assert "from pg_constraint" in sql


def test_stage_1_adds_the_supplier_bundle_without_changing_estimation_contracts():
    sql = SQL_PATH.read_text().lower()

    assert "'supplier_cut_and_edge_banding'" in sql
    assert "'supplier_service_unit_count'" in sql
    assert "supplier-defined service unit count" in sql
    assert "alter table public.company_supplier_aliases enable row level security" in sql
    assert "alter table public.company_supplier_operation_offers enable row level security" in sql
    assert "update public.company_price_source_rows" not in sql
    assert "delete from public.company_" not in sql
