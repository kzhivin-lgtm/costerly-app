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
        "reference_brands",
        "reference_material_family_brand_scopes",
        "reference_brand_aliases",
        "reference_material_models",
        "reference_material_model_attribute_values",
        "reference_market_material_variants",
        "reference_market_material_supply_formats",
        "reference_market_material_legacy_mappings",
        "company_material_item_market_variant_mappings",
        "estimate_case_assumptions",
        "catalog_gap_jobs",
        "catalog_gap_job_occurrences",
    ):
        assert f"create table if not exists public.{table}" in sql

    assert "'wood', 'metal', 'glass_plastics', 'stone', 'coating'" in sql
    assert "'material', 'hardware', 'consumable', 'packaging'" in sql
    assert "reference_material_family_one_primary_attribute_idx" in sql
    assert "reference_material_one_active_family_idx" in sql


def test_global_model_market_variant_and_company_offer_are_separate_contracts():
    sql = _sql()

    assert "global family, global material model, market listing and company offer are" in sql
    assert "market_code text not null references public.reference_markets(market_code)" in sql
    assert "family_id uuid not null references public.reference_material_families(family_id)" in sql
    assert "references public.reference_material_family_brand_scopes(family_id, brand_id)" in sql
    assert "create table if not exists public.reference_material_models" in sql
    assert "material_model_id uuid not null references public.reference_material_models(material_model_id)" in sql
    assert "legacy_material_id uuid not null unique references public.reference_materials(material_id)" in sql
    assert "classification_status in ('mapped', 'excluded_by_policy', 'review_required')" in sql
    assert "company_material_id uuid primary key" in sql
    assert "mapping_status in ('matched', 'no_market_match', 'review_required')" in sql
    assert "market_material_variant_id is not null" in sql


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
