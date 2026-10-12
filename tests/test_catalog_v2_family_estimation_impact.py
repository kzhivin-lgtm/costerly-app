from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/sql/2026_10_12_catalog_v2_family_estimation_impact.sql"


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_family_estimation_impact_is_a_constrained_global_family_property():
    sql = _sql()

    assert "alter table public.reference_material_families" in sql
    assert "add column if not exists estimation_impact" in sql
    assert "estimation_impact in ('low', 'medium', 'high')" in sql
    assert "default 'high'" in sql


def test_initial_impact_backfill_is_conservative_and_explicit():
    sql = _sql()

    assert "set estimation_impact = 'high'" in sql
    assert "set estimation_impact = 'medium'" in sql
    assert "set estimation_impact = 'low'" in sql
    assert "'hardware_leg_caster'" in sql
    assert "'hardware_drawer_slide'" not in sql
