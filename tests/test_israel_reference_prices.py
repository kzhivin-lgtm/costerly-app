from pathlib import Path
from decimal import Decimal
import re


ROOT = Path(__file__).parents[1]
PANELS = ROOT / "db/sql/2026_09_28_israel_reference_prices_panels_v1.sql"
HARDWARE = ROOT / "db/sql/2026_09_28_israel_reference_prices_hardware_v1.sql"
METAL = ROOT / "db/sql/2026_09_28_israel_reference_prices_metal_v1.sql"
COATINGS = ROOT / "db/sql/2026_09_28_israel_reference_prices_coatings_consumables_v1.sql"
SOLID_WOOD = ROOT / "db/sql/2026_09_28_israel_reference_prices_solid_wood_v1.sql"
WOOD_SURFACES = ROOT / "db/sql/2026_09_28_israel_reference_prices_wood_surfaces_v1.sql"
PLASTICS = ROOT / "db/sql/2026_09_28_israel_reference_prices_plastics_v1.sql"


def test_panel_batch_is_israel_only_and_candidate_only():
    sql = PANELS.read_text()
    assert sql.count("'IL'") >= 10
    assert "'active'" not in sql
    assert "'candidate'" in sql


def test_panel_batch_preserves_vat_and_service_inclusion_evidence():
    sql = PANELS.read_text()
    assert "'unknown'" in sql
    assert "'excluded'" in sql
    assert "'material_only'" in sql
    assert "'cut_to_size'" in sql
    assert "'{\"cutting\"}'" in sql
    assert "'{\"precision_cutting\"}'" in sql
    assert '"normalization_blocked_by":"sheet dimensions not stated"' in sql


def test_panel_batch_has_no_unsourced_baseline_or_agent_arithmetic():
    sql = PANELS.read_text().lower()
    assert "market_material_baselines" not in sql
    assert "price_low" not in sql
    assert "price_typical" not in sql
    assert "price_high" not in sql


def test_camisa_sheet_area_is_auditable():
    sql = PANELS.read_text()
    assert '"dimensions_mm":[2440,1220]' in sql
    assert '"sheet_area_sqm":2.9768' in sql
    assert "'sheet_2440x1220'" in sql


def test_panel_batch_uses_idempotent_stable_ids():
    sql = PANELS.read_text().lower()
    assert "on conflict (source_id) do update" in sql
    assert "on conflict (material_code) do update" in sql
    assert "on conflict (material_id, market_code, language_code) do update" in sql
    assert "on conflict (market_offer_id) do update" in sql


def test_hardware_batch_uses_only_fixed_prices_and_stays_candidate():
    sql = HARDWARE.read_text()
    assert "starting from" in sql
    assert "intentionally omitted" in sql
    assert "'candidate'" in sql
    assert "'active'" not in sql
    assert "market_material_baselines" not in sql
    assert sql.count("'candidate')") == 16


def test_hardware_batch_preserves_vat_evidence_and_normalization():
    sql = HARDWARE.read_text()
    assert '"vat_rate":0.18' in sql
    assert "'included'" in sql
    assert "'retail_package'" in sql
    assert "'displayed_item'" in sql
    assert "'ea'" in sql
    assert "vat_evidence_source_id" in sql
    assert "rate_evidence_source_id" in sql


def test_hardware_batch_is_idempotent_and_market_scoped():
    sql = HARDWARE.read_text().lower()
    assert sql.count("'il'") >= 10
    assert "on conflict (source_id) do update" in sql
    assert "on conflict (material_code) do update" in sql
    assert "on conflict (material_id, market_code, language_code) do update" in sql
    assert "on conflict (market_offer_id) do update" in sql


def test_hardware_vat_normalization_examples_are_correct():
    samples = {
        Decimal("5.00"): Decimal("4.237288"),
        Decimal("49.00"): Decimal("41.525424"),
        Decimal("550.00"): Decimal("466.101695"),
        Decimal("36.70"): Decimal("31.101695"),
    }
    for gross, normalized in samples.items():
        expected = (gross / Decimal("1.18")).quantize(Decimal("0.000001"))
        assert normalized == expected


def test_metal_batch_preserves_stock_length_and_excludes_services():
    sql = METAL.read_text()
    assert "20x20x1_5mm" in sql
    assert "'stock_length_6m'" in sql
    assert '"stock_length_m":6' in sql
    assert '"cutting":"excluded"' in sql
    assert '"delivery":"excluded"' in sql
    assert "9.293785" in sql
    assert sql.count("'candidate'") == 1
    assert "market_material_baselines" not in sql


def test_coatings_batch_preserves_package_vat_and_use_boundaries():
    sql = COATINGS.read_text()
    assert sql.count("'candidate'") == 5
    assert "'included'" in sql
    assert "'unknown'" in sql
    assert "normalization_blocked_by" in sql
    assert '"purpose":"cleaning only"' in sql
    assert "container_0_5l" in sql
    assert "container_3_7l" in sql
    assert "container_5l" in sql
    assert "market_material_baselines" not in sql


def test_solid_wood_batch_keeps_nominal_actual_and_package_geometry():
    sql = SOLID_WOOD.read_text()
    assert sql.count("'candidate'") == 14
    assert '"nominal_mm"' in sql
    assert '"actual_mm"' in sql
    assert sql.count('"sheet_area_sqm":2.9768') == 5
    assert "'lm'" in sql
    assert "'sqm'" in sql
    assert "market_material_baselines" not in sql


def test_solid_wood_batch_has_hebrew_market_names():
    sql = SOLID_WOOD.read_text()
    assert "עץ אורן פיני מוקצע" in sql
    assert "לוח OSB" in sql
    assert "פלטת עץ אורן פיני מודבק" in sql
    assert "select material_id,'IL',canonical_name,'he-IL'" not in sql


def test_wood_surface_batch_preserves_roll_geometry_and_vat_math():
    sql = WOOD_SURFACES.read_text()
    assert sql.count("'candidate'") == 9
    assert '"dimensions_mm":[1.1,22]' in sql
    assert '"roll_length_m":100' in sql
    assert "'roll_100m'" in sql
    assert "'lm'" in sql
    assert "'included'" in sql
    assert '"vat_evidence_source_id"' in sql
    assert "market_material_baselines" not in sql


def test_wood_surface_batch_has_hebrew_market_names():
    sql = WOOD_SURFACES.read_text()
    assert "קנט PVC" in sql
    assert "פשתן" in sql
    assert "אלון מבוקע" in sql


def test_plastics_batch_separates_raw_sheet_from_cut_scope():
    sql = PLASTICS.read_text()
    assert sql.count("'candidate'") == 16
    assert sql.count("'material_only'") == 8
    assert sql.count("'cut_to_size'") == 8
    assert sql.count("'sheet_1220x2440'") == 8
    assert sql.count("'piece_1000x1000'") == 8
    assert sql.count('"sheet_area_sqm":2.9768') == 8
    assert sql.count('"laser_rectangle_cut"') == 8
    assert "market_material_baselines" not in sql


def test_plastics_batch_has_all_verified_thicknesses_and_hebrew_names():
    sql = PLASTICS.read_text()
    for thickness in (2, 3, 4, 5, 6, 8, 10, 15):
        assert f"'acrylic_cast_clear_{thickness}mm'" in sql
    assert "פרספקס שקוף יצוק סוג א׳" in sql


def test_reference_price_batches_do_not_reuse_source_ids():
    files = (
        PANELS,
        HARDWARE,
        METAL,
        COATINGS,
        SOLID_WOOD,
        WOOD_SURFACES,
        PLASTICS,
    )
    all_source_ids = []
    for path in files:
        source_section = path.read_text().lower().split("on conflict", 1)[0]
        all_source_ids.extend(re.findall(r"\('([0-9a-f-]{36})'", source_section))
    assert len(all_source_ids) == len(set(all_source_ids))
