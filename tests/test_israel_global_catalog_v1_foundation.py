from pathlib import Path


SQL_PATH = Path("db/sql/2026_09_29_israel_global_catalog_v1_foundation.sql")


def test_model_prices_are_separate_from_evidence_backed_baselines():
    sql = SQL_PATH.read_text().lower()

    assert "create table if not exists public.reference_catalog_versions" in sql
    assert "create table if not exists public.market_material_model_prices" in sql
    assert "alter table public.market_material_model_prices enable row level security" in sql
    assert "derived_from_israel_curve" in sql
    assert "modeled_fallback" in sql
    assert "market_material_baselines" not in sql
