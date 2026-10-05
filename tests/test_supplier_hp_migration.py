from pathlib import Path


SQL_PATH = Path(__file__).parents[1] / "db/sql/2026_10_05_supplier_hp.sql"


def test_supplier_hp_migration_is_additive_and_company_scoped():
    sql = SQL_PATH.read_text().lower()

    assert "add column if not exists supplier_hp text" in sql
    assert "company_suppliers (company_id, supplier_hp)" in sql
    assert "where supplier_hp is not null" in sql
