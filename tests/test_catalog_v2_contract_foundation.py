from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "db/sql/2026_10_11_catalog_v2_contract_foundation.sql"


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_catalog_v2_foundation_has_canonical_taxonomy_and_case_local_contracts():
    sql = _sql()

    for table in (
        "reference_production_departments",
        "reference_entity_roles",
        "reference_material_categories_v2",
        "reference_material_families",
        "reference_material_family_attributes",
        "reference_material_family_department_affinities",
        "reference_material_family_operation_eligibilities",
        "reference_material_family_memberships",
        "estimate_case_assumptions",
        "catalog_gap_jobs",
        "catalog_gap_job_occurrences",
    ):
        assert f"create table if not exists public.{table}" in sql

    assert "'wood', 'metal', 'glass_plastics', 'stone', 'coating'" in sql
    assert "'material', 'hardware', 'consumable', 'packaging'" in sql
    assert "reference_material_family_one_primary_attribute_idx" in sql
    assert "reference_material_one_active_family_idx" in sql


def test_provisional_assumptions_cannot_mutate_canonical_catalog():
    sql = _sql()

    assert "case-local provisional assumptions" in sql
    assert "catalog_gap_jobs" in sql
    assert "insert into public.reference_materials" not in sql
    assert "update public.reference_materials" not in sql
    assert "delete from public.reference_materials" not in sql


def test_assumptions_are_company_readable_but_gap_queue_is_staff_only():
    sql = _sql()

    assert "estimate_case_assumptions_company_member_read" in sql
    assert "grant select on public.estimate_case_assumptions to authenticated" in sql
    assert "grant select on public.catalog_gap_jobs to authenticated" not in sql
    assert "public.catalog_gap_jobs," in sql
    assert "public.catalog_gap_job_occurrences\nto service_role" in sql
