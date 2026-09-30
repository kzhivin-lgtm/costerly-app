from pathlib import Path


def test_estimation_evidence_migration_is_additive_and_private():
    sql = Path("db/sql/2026_09_30_estimation_v2_evidence_foundation.sql").read_text()

    assert "create table if not exists public.rfq_estimation_object_inputs" in sql
    assert "create table if not exists public.rfq_estimation_evidence_artifacts" in sql
    assert "references public.agent_usage_events(id)" in sql
    assert "original_file_ref" in sql
    assert "original_content_sha256" in sql
    assert "'rfq-estimation-originals'" in sql
    assert "contract_version = 'estimation_input_v2'" in sql
    assert "'rfq-estimation-evidence'" in sql
    assert "false," in sql
    assert "alter table public.rfq_detected_objects" not in sql
    assert "alter table public.rfq_estimate_lines" not in sql


def test_detection_evidence_migration_adds_page_refs_and_exact_anchors():
    sql = Path("db/sql/2026_09_30_detection_evidence_page_refs.sql").read_text()

    assert "alter table public.rfq_detected_objects" in sql
    assert "add column if not exists evidence_page_refs jsonb" in sql
    assert "add column if not exists evidence_anchors jsonb" in sql
    assert "jsonb_typeof(evidence_page_refs) = 'array'" in sql
    assert "jsonb_typeof(evidence_anchors) = 'array'" in sql
