from pathlib import Path


SQL_PATH = (
    Path(__file__).parents[1]
    / "db/sql/2026_09_29_purchased_fabricated_components_v1.sql"
)


def test_purchased_component_migration_adds_explicit_economic_fields_and_guards():
    sql = SQL_PATH.read_text().lower()

    assert "add column if not exists economic_classification text" in sql
    assert "add column if not exists price_scope text" in sql
    assert "'purchased_fabricated_component'" in sql
    assert "'fabricated_component'" in sql
    assert "section = 'material'" in sql
    assert "rfq_estimate_lines_purchased_component_check" in sql


def test_purchased_component_migration_preserves_in_house_manufacturing_classification():
    sql = SQL_PATH.read_text().lower()

    assert "source = 'manufacturing_engine'" in sql
    assert "then 'in_house_manufacturing'" in sql
    assert "then 'in_house_labor'" in sql
    assert "then 'overhead'" in sql
