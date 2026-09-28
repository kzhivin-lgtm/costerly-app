from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "db/sql/2026_09_28_reference_catalog_foundation.sql"
TAXONOMY = ROOT / "db/sql/2026_09_28_reference_catalog_taxonomy_v1.sql"
LEGACY_MIGRATION = ROOT / "db/sql/2026_09_28_remove_legacy_machining_point_rules.sql"
REPOSITORIES = ROOT / "db/repositories.py"
PLAN = ROOT / "notes/ISRAEL_REFERENCE_CATALOG.md"
MASTER_CHECKLIST = ROOT / "notes/ISRAEL_REFERENCE_MASTER_CHECKLIST.md"
ALIASES = ROOT / "db/sql/2026_09_28_zz_israel_reference_material_aliases_v1.sql"
MATERIAL_ROUTING = ROOT / "notes/ISRAEL_REFERENCE_MATERIAL_ROUTING.md"


def test_israel_is_the_first_explicit_market_without_price_seeds():
    sql = MIGRATION.read_text()
    assert "values ('IL', 'Israel', 'ILS', 'he-IL')" in sql
    assert "estimation_market_code text not null default 'IL'" in sql
    assert "insert into public.market_material_offers" not in sql.lower()
    assert "insert into public.market_material_baselines" not in sql.lower()
    assert "insert into public.market_operation_models" not in sql.lower()


def test_global_identity_is_separate_from_market_data():
    sql = MIGRATION.read_text().lower()
    for table in (
        "reference_materials",
        "reference_material_categories",
        "market_material_profiles",
        "reference_material_aliases",
        "market_material_offers",
        "market_material_baselines",
        "reference_operations",
        "market_operation_models",
    ):
        assert f"public.{table}" in sql
    assert "foreign key (source_id, market_code)" in sql
    assert "references public.reference_sources(source_id, market_code)" in sql
    assert "source_channel text not null default 'other'" in sql
    assert "add column if not exists source_channel" in sql
    assert "reference_sources_source_channel_check" in sql
    for channel in ("'trade_supplier'", "'specialist_retailer'", "'diy_retail'"):
        assert channel in sql


def test_material_baseline_is_sourced_versioned_and_approved():
    sql = MIGRATION.read_text().lower()
    assert "price_low <= price_typical and price_typical <= price_high" in sql
    assert "market_material_baseline_evidence" in sql
    assert "foreign key (baseline_id, market_code, price_scope)" in sql
    assert "foreign key (market_offer_id, market_code, price_scope)" in sql
    assert "an active material baseline requires same-market same-scope offer evidence" in sql
    assert "methodology text not null" in sql
    assert "supersedes_baseline_id" in sql
    assert "status <> 'active' or (approved_by is not null and approved_at is not null)" in sql
    assert "vat_mode text not null default 'excluded'" in sql
    assert "'material_only', 'cut_to_size', 'fabricated_component', 'retail_package'" in sql
    assert "included_services text[] not null" in sql
    assert "delivery_included boolean" in sql


def test_operation_models_use_explicit_time_components_and_roles():
    sql = MIGRATION.read_text().lower()
    for component_type in ("'setup'", "'throughput'", "'auxiliary'", "'minimum_batch'"):
        assert component_type in sql
    for value_unit in ("'labor_minutes'", "'labor_minutes_per_unit'", "'units_per_hour'"):
        assert value_unit in sql
    assert "reference_labor_roles" in sql
    assert "reference_operation_roles" in sql
    assert "crew_size" in sql


def test_reference_tables_are_service_role_only():
    sql = MIGRATION.read_text().lower()
    tables = (
        "reference_markets",
        "reference_sources",
        "reference_material_categories",
        "reference_materials",
        "market_material_profiles",
        "reference_material_aliases",
        "market_material_offers",
        "market_material_baselines",
        "market_material_baseline_evidence",
        "reference_labor_roles",
        "reference_operation_drivers",
        "reference_operations",
        "market_operation_models",
        "market_operation_time_components",
        "reference_operation_roles",
        "reference_operation_driver_options",
    )
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on public.{table} from public, anon, authenticated" in sql
        assert f"grant all on public.{table} to service_role" in sql


def test_legacy_machining_points_are_removed_from_schema_and_runtime_fetch():
    cleanup = LEGACY_MIGRATION.read_text().lower()
    repositories = REPOSITORIES.read_text()
    assert "drop table if exists public.machining_point_rules" in cleanup
    assert 'fetch_table(client, "machining_point_rules"' not in repositories


def test_saved_contract_forbids_cross_market_fallback_and_agent_arithmetic():
    plan = PLAN.read_text()
    assert "no cross-market fallback is allowed" in plan
    assert "other countries are never silent substitutes" in plan
    assert "There is no machining-points abstraction" in plan
    assert "Estimation v2: feature extraction only" in plan


def test_taxonomy_has_no_prices_times_or_machining_points():
    sql = TAXONOMY.read_text().lower()
    assert "insert into public.reference_material_categories" in sql
    assert "insert into public.reference_labor_roles" in sql
    assert "insert into public.reference_operation_drivers" in sql
    assert "insert into public.reference_operations" in sql
    assert "insert into public.reference_operation_roles" in sql
    assert "insert into public.reference_operation_driver_options" in sql
    assert "machining_points" not in sql
    assert "market_material_offers" not in sql
    assert "market_material_baselines" not in sql
    assert "market_operation_models" not in sql


def test_labor_roles_match_the_existing_company_profile_vocabulary():
    sql = TAXONOMY.read_text()
    for role_code in (
        "owner_director",
        "general_manager",
        "project_manager",
        "production_manager",
        "accountant",
        "office_administrator",
        "estimator",
        "sales_manager",
        "designer_draftsperson",
        "carpenter",
        "welder",
        "cnc_operator",
        "painter_finisher",
        "installer",
        "general_worker",
    ):
        assert f"('{role_code}'," in sql


def test_specialist_roles_never_silently_match_broad_company_positions():
    foundation = MIGRATION.read_text()
    taxonomy = TAXONOMY.read_text()
    assert "company_match_policy in ('exact', 'requires_confirmation', 'none')" in foundation
    assert "('wood_machine_operator', 'Wood Machine Operator', 'wood', 'carpenter', 'requires_confirmation')" in taxonomy
    assert "('glass_fabricator', 'Glass Fabricator', 'general', null, 'none')" in taxonomy
    assert "('stone_fabricator', 'Stone Fabricator', 'general', null, 'none')" in taxonomy
    assert "('galvanizing_operator', 'Galvanizing Operator', 'coating', null, 'none')" in taxonomy


def test_physical_drivers_replace_material_specific_point_systems():
    sql = TAXONOMY.read_text()
    for driver_code in (
        "part_count",
        "cut_length_lm",
        "hole_count",
        "groove_length_lm",
        "pocket_count",
        "tool_change_count",
        "bend_count",
        "weld_length_lm",
        "finish_area_sqm",
    ):
        assert f"('{driver_code}'," in sql


def test_operation_taxonomy_spans_supported_fabrication_and_installation():
    sql = TAXONOMY.read_text()
    for operation_code in (
        "panel_saw_cutting",
        "cnc_router_profile_cutting",
        "edge_banding",
        "solid_wood_glueup",
        "carcass_assembly",
        "sheet_laser_cutting",
        "sheet_metal_bending",
        "mig_mag_welding",
        "glass_edge_processing",
        "stone_cutout",
        "acrylic_cnc_machining",
        "wood_lacquering",
        "powder_coating_application",
        "protective_packaging",
        "cabinet_installation",
    ):
        assert f"('{operation_code}'," in sql


def test_connector_taxonomy_separates_biscuits_from_concealed_systems():
    sql = TAXONOMY.read_text()
    assert "('biscuit_connector', 'Biscuits and loose connectors', 'hardware', 'fastener'" in sql
    assert "('concealed_connector', 'Concealed and knock-down connectors', 'hardware', 'fastener'" in sql


def test_master_checklist_is_a_fixed_unique_a_to_w_denominator():
    checklist = MASTER_CHECKLIST.read_text()
    cells = re.findall(r"^- \[[ x~]\] ([A-X]\d{2}) ", checklist, re.MULTILINE)
    assert len(cells) == 395
    assert len(cells) == len(set(cells))
    assert {cell[0] for cell in cells} == set("ABCDEFGHIJKLMNOPQRSTUVW")
    assert checklist.count("- [x]") == 2
    assert checklist.count("- [~]") == 79
    assert checklist.count("- [ ]") == 314


def test_furniture_core_uses_estimation_groups_and_documents_coverage():
    core = (ROOT / "notes/ISRAEL_REFERENCE_FURNITURE_CORE.md").read_text()
    cells = re.findall(r"^- \[[ x~]\] [A-Z][0-9]{2} ", core, re.MULTILINE)
    assert len(cells) == 72
    assert core.count("- [x]") == 12
    assert core.count("- [~]") == 59
    assert core.count("- [ ]") == 1
    assert "16.67%" in core
    assert "98.61%" in core
    assert "Ordinary screws are not estimated piece by piece" in core


def test_taxonomy_has_bulk_fastener_estimation_lanes():
    taxonomy = (ROOT / "db/sql/2026_09_28_reference_catalog_taxonomy_v1.sql").read_text()
    for category_code in (
        "bulk_wood_fastener",
        "bulk_machine_fastener",
        "bulk_nail_staple",
        "installation_fastener_allowance",
        "system_specific_screw",
    ):
        assert f"('{category_code}'" in taxonomy
    assert "('furniture_glide'" in taxonomy
    assert "('shelf_support'" in taxonomy
    assert "('veneer_faced_panel'" in taxonomy
    assert "('hpl_faced_panel'" in taxonomy


def test_alias_dictionary_is_market_scoped_secure_and_indexed():
    sql = MIGRATION.read_text().lower()
    assert "create table if not exists public.reference_material_aliases" in sql
    assert "normalize_reference_material_alias" in sql
    assert "reference_material_aliases_lookup_idx" in sql
    assert "foreign key (source_id, market_code)" in sql
    assert "alter table public.reference_material_aliases enable row level security" in sql
    assert "revoke all on public.reference_material_aliases from public, anon, authenticated" in sql
    assert "grant all on public.reference_material_aliases to service_role" in sql


def test_alias_seed_covers_every_active_identity_without_unit_alias_explosion():
    sql = ALIASES.read_text()
    assert sql.count("insert into public.reference_material_aliases") == 4
    assert "m.canonical_name" in sql
    assert "m.material_code" in sql
    assert "p.market_name" in sql
    assert "'canonical'" in sql
    assert "'technical_code'" in sql
    assert "'market_name'" in sql
    assert "where m.active" in sql
    assert "where p.active and m.active and p.market_code = 'IL'" in sql
    assert "and not exists (" in sql
    assert "'en-IL'" in sql
    assert "combinatorial aliases" in sql
    assert "having count(a.alias_id)" in sql


def test_exact_alias_fast_path_is_indexed_bounded_and_agent_free():
    sql = ALIASES.read_text()
    assert "find_reference_material_alias_matches" in sql
    assert "a.alias_key = public.normalize_reference_material_alias(p_alias_text)" in sql
    assert "limit least(greatest(p_limit, 1), 5)" in sql
    assert "grant execute on function public.find_reference_material_alias_matches" in sql
    assert "service_role" in sql


def test_material_routing_contract_never_scans_full_catalog_in_prompt():
    routing = MATERIAL_ROUTING.read_text()
    assert "must never receive or scan the full material or alias catalog" in routing
    assert "hard maximum of five results" in routing
    assert "return it without an agent call" in routing
    assert "Deduplicate identical normalized phrases" in routing
    assert "Company aliases remain company-scoped" in routing
    assert "The resolver selects identity only" in routing
