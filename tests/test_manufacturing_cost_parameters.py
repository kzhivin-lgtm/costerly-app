from pathlib import Path

from use_cases import machinery


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "db/sql/2026_09_28_manufacturing_cost_parameters.sql"
PLAN = ROOT / "notes/CNC_LASER_COSTING.md"
ESTIMATE_LEVEL_MIGRATION = ROOT / "db/sql/2026_09_28_cnc_estimate_levels.sql"


def test_cnc_laser_foundation_preserves_compact_machinery_profile():
    assert machinery.PROFILE_MACHINE_CODES == (
        "wood_cnc_router",
        "wood_panel_saw",
        "wood_edge_bander",
        "wood_veneer_press",
        "wood_solid_preparation",
        "wood_wide_belt_sander",
        "metal_sheet_laser",
        "metal_press_brake",
        "metal_punch_press",
        "metal_profile_bender",
        "metal_rolling_machine",
        "metal_profile_saw",
        "finish_wet_spray_booth",
        "finish_powder_booth",
        "finish_sandblast_booth",
        "finish_galvanizing",
    )
    assert "wood_boring_machine" not in machinery.PROFILE_MACHINE_CODES


def test_parameter_migration_is_additive_and_has_four_calculators():
    sql = MIGRATION.read_text().lower()
    for operation in ("drop table", "delete from", "truncate table", "on delete cascade"):
        assert operation not in sql
    for calculator in (
        "cnc_router_in_house",
        "cnc_router_subcontractor",
        "sheet_laser_in_house",
        "sheet_laser_subcontractor",
    ):
        assert f"'{calculator}'" in sql
    assert "value_low <= value_typical" in sql
    assert "value_typical <= value_high" in sql
    assert "supersedes_parameter_id" in sql
    assert "source_url is not null" in sql
    assert "approved_by is not null" in sql


def test_parameter_read_path_is_platform_staff_only_and_audited():
    sql = MIGRATION.read_text().lower()
    assert "platform_admin_manufacturing_cost_parameters" in sql
    assert "platform_admin" in sql
    assert "platform_viewer" in sql
    assert "manufacturing_cost_parameters_viewed" in sql
    assert "revoke all on public.manufacturing_cost_parameters from public, anon, authenticated" in sql
    assert "grant all on public.manufacturing_cost_parameters to service_role" in sql


def test_saved_plan_rejects_machinery_expansion_and_legacy_weights():
    plan = PLAN.read_text()
    assert "No machine is added for task 3.14.1" in plan
    assert "Boring machine` stays outside the profile" in plan
    assert "No use of legacy machining-point weights" in plan


def test_cnc_estimate_level_feedback_is_bounded_private_and_content_free():
    sql = ESTIMATE_LEVEL_MIGRATION.read_text().lower()
    assert "company_cnc_estimate_level_events" in sql
    assert "between 1 and 5" in sql
    assert "'in_house', 'subcontractor'" in sql
    assert "revoke all on public.company_cnc_estimate_level_events" in sql
    assert "to service_role" in sql
    for forbidden in ("estimate_cost", "customer_content", "file_name", "document_text"):
        assert forbidden not in sql


def test_cnc_plan_runs_only_the_required_exclusive_route():
    plan = PLAN.read_text()
    assert "does not run four calculations for every estimate" in plan
    assert "Both CNC strategies are never active at the same time" in plan
    assert "panel saw plus manual processing in-house" in plan
    assert "subcontracting is the default" in plan
    assert "Merely viewing or saving other Machinery data" in plan
    assert "does not turn that default into feedback" in plan
    assert "not statistically validated P10, P50, and P90 claims" in plan
    assert "refuses inputs for every" in plan
    assert "the nearest band is never used" in plan
    assert "two equally ranked records remain ambiguous" in plan
    assert "cannot be averaged or silently substituted" in plan
