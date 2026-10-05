from pathlib import Path


def test_archive_source_also_archives_supplier_operation_offers():
    sql = (
        Path(__file__).resolve().parents[1]
        / "db/sql/2026_10_05_archive_supplier_operation_offers.sql"
    ).read_text(encoding="utf-8")

    assert "create or replace function public.archive_company_price_source" in sql
    assert "update public.company_supplier_operation_offers offer" in sql
    assert "set status = 'archived'" in sql
    assert "'archived_operation_offers'" in sql
