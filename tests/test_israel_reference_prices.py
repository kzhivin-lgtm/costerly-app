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
PANELS_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_panels_v2.sql"
HARDWARE_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_hardware_v2.sql"
FASTENERS = ROOT / "db/sql/2026_09_28_israel_reference_prices_fasteners_v1.sql"
FASTENERS_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_fasteners_v2.sql"
FASTENERS_V3 = ROOT / "db/sql/2026_09_28_israel_reference_prices_fasteners_v3.sql"
PACKAGING = ROOT / "db/sql/2026_09_28_israel_reference_prices_packaging_v1.sql"
ADHESIVES_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_adhesives_v2.sql"
COMPARISONS = ROOT / "db/sql/2026_09_28_israel_reference_price_comparisons_v1.sql"
CONNECTORS = ROOT / "db/sql/2026_09_28_israel_reference_prices_connectors_v1.sql"
FURNITURE_CORE = ROOT / "db/sql/2026_09_28_israel_reference_prices_furniture_core_v1.sql"
FURNITURE_CORE_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_furniture_core_v2.sql"
FURNITURE_CORE_V3 = ROOT / "db/sql/2026_09_28_israel_reference_prices_furniture_core_v3.sql"
RAPID_CORE_V1 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v1.sql"
RAPID_CORE_V2 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v2.sql"
RAPID_CORE_V3 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v3.sql"
RAPID_CORE_V4 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v4.sql"
RAPID_CORE_V5 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v5.sql"
RAPID_CORE_V6 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v6.sql"
RAPID_CORE_V7 = ROOT / "db/sql/2026_09_28_israel_reference_prices_rapid_core_v7.sql"
ALL_PRICE_FILES = (
    PANELS,
    HARDWARE,
    METAL,
    COATINGS,
    SOLID_WOOD,
    WOOD_SURFACES,
    PLASTICS,
    PANELS_V2,
    HARDWARE_V2,
    FASTENERS,
    FASTENERS_V2,
    FASTENERS_V3,
    PACKAGING,
    ADHESIVES_V2,
    COMPARISONS,
    CONNECTORS,
    FURNITURE_CORE,
    FURNITURE_CORE_V2,
    FURNITURE_CORE_V3,
    RAPID_CORE_V1,
    RAPID_CORE_V2,
    RAPID_CORE_V3,
    RAPID_CORE_V4,
    RAPID_CORE_V5,
    RAPID_CORE_V6,
    RAPID_CORE_V7,
)


def _split_sql_values(value_block: str) -> list[list[str]]:
    rows = []
    row_start = None
    depth = 0
    in_string = False
    index = 0
    while index < len(value_block):
        character = value_block[index]
        if character == "'":
            if in_string and index + 1 < len(value_block) and value_block[index + 1] == "'":
                index += 2
                continue
            in_string = not in_string
        elif not in_string:
            if character == "(":
                if depth == 0:
                    row_start = index + 1
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and row_start is not None:
                    row = value_block[row_start:index]
                    fields = []
                    field_start = 0
                    field_depth = 0
                    field_in_string = False
                    field_index = 0
                    while field_index < len(row):
                        field_character = row[field_index]
                        if field_character == "'":
                            if (
                                field_in_string
                                and field_index + 1 < len(row)
                                and row[field_index + 1] == "'"
                            ):
                                field_index += 2
                                continue
                            field_in_string = not field_in_string
                        elif not field_in_string:
                            if field_character in "([":
                                field_depth += 1
                            elif field_character in ")]":
                                field_depth -= 1
                            elif field_character == "," and field_depth == 0:
                                fields.append(row[field_start:field_index].strip())
                                field_start = field_index + 1
                        field_index += 1
                    fields.append(row[field_start:].strip())
                    rows.append(fields)
                    row_start = None
        index += 1
    return rows


def _sql_literal(value: str) -> str | None:
    value = value.strip()
    if value.lower() == "null":
        return None
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def _insert_rows(path: Path, table: str, conflict_column: str):
    conflict_pattern = r"\s*,\s*".join(
        re.escape(column.strip()) for column in conflict_column.split(",")
    )
    pattern = re.compile(
        rf"insert into public\.{table}\s*\((.*?)\)\s*values\s*(.*?)"
        rf"on conflict\s*\({conflict_pattern}\)",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(path.read_text()):
        columns = [column.strip() for column in match.group(1).split(",")]
        for values in _split_sql_values(match.group(2)):
            assert len(values) == len(columns), (
                f"{path.name} has {len(values)} values for {len(columns)} columns "
                f"in public.{table}"
            )
            yield dict(zip(columns, map(_sql_literal, values)))


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
    all_source_ids = []
    for path in ALL_PRICE_FILES:
        source_section = path.read_text().lower().split("on conflict", 1)[0]
        all_source_ids.extend(re.findall(r"\('([0-9a-f-]{36})'", source_section))
    assert len(all_source_ids) == len(set(all_source_ids))


def test_reference_price_batches_use_the_canonical_source_contract():
    forbidden_fragments = (
        "public.market_sources",
        "commercial_channel",
        "evidence_metadata",
        "'consumer_retail'",
        "'trade_retail'",
        "'cut_to_size_retail'",
        "'timber_yard_retail'",
        "'fabricator_retailer'",
        "'catalog'",
        "'trade_package'",
        "'trade_price_unit'",
        "'catalog_package'",
        "'temporarily_unavailable'",
    )
    for path in ALL_PRICE_FILES:
        sql = path.read_text()
        for fragment in forbidden_fragments:
            assert fragment not in sql, f"{path.name} uses obsolete source field/value {fragment}"


def test_every_offer_row_satisfies_foundation_enum_constraints():
    offers = [
        row
        for path in ALL_PRICE_FILES
        for row in _insert_rows(path, "market_material_offers", "market_offer_id")
    ]
    assert len(offers) == 320
    assert {row["price_scope"] for row in offers} <= {
        "material_only",
        "cut_to_size",
        "fabricated_component",
        "retail_package",
    }
    assert {row["vat_mode"] for row in offers} <= {
        "included",
        "excluded",
        "exempt",
        "unknown",
    }
    assert {row["status"] for row in offers} <= {
        "candidate",
        "reviewed",
        "active",
        "archived",
    }
    assert all(re.fullmatch(r"[A-Z]{3}", row["source_currency"]) for row in offers)
    assert all(Decimal(row["source_price"]) >= 0 for row in offers)
    assert all(
        row["package_quantity"] is None or Decimal(row["package_quantity"]) > 0
        for row in offers
    )
    assert all(
        row["minimum_order_quantity"] is None
        or Decimal(row["minimum_order_quantity"]) >= 0
        for row in offers
    )
    assert all(Decimal(row["confidence"]) >= 0 for row in offers)
    assert all(Decimal(row["confidence"]) <= 100 for row in offers)
    assert all(
        row["normalized_price_ex_vat"] is None or row["normalized_unit"] is not None
        for row in offers
    )
    assert all(
        row.get("valid_to") is None
        or row.get("valid_from") is None
        or row["valid_from"] <= row["valid_to"]
        for row in offers
    )


def test_every_source_and_material_row_satisfies_foundation_enum_constraints():
    sources = [
        row
        for path in ALL_PRICE_FILES
        for row in _insert_rows(path, "reference_sources", "source_id")
    ]
    materials = [
        row
        for path in ALL_PRICE_FILES
        for row in _insert_rows(path, "reference_materials", "material_code")
    ]
    assert len(sources) == 99
    assert len(materials) == 280
    assert {row["source_type"] for row in sources} <= {
        "official",
        "supplier",
        "manufacturer",
        "retailer",
        "industry",
        "research",
        "platform_observation",
    }
    assert {row.get("source_channel", "other") for row in sources} <= {
        "manufacturer",
        "importer_distributor",
        "trade_supplier",
        "specialist_retailer",
        "diy_retail",
        "marketplace",
        "public_procurement",
        "other",
    }
    assert {row["department"] for row in materials} <= {
        "wood",
        "metal",
        "glass_stone_plastic",
        "coating",
        "hardware",
        "consumable",
        "packaging",
    }


def test_market_profiles_cover_every_material_and_use_valid_availability_statuses():
    material_id_to_code = {}
    profiled_codes = set()
    availability_statuses = set()
    allowed_statuses = {"common", "limited", "special_order", "unavailable"}
    for path in ALL_PRICE_FILES:
        for row in _insert_rows(path, "reference_materials", "material_code"):
            material_id_to_code[row["material_id"]] = row["material_code"]

    for path in ALL_PRICE_FILES:
        sql = path.read_text()
        for row in _insert_rows(
            path,
            "market_material_profiles",
            "material_id,market_code,language_code",
        ):
            profiled_codes.add(material_id_to_code[row["material_id"]])
            availability_statuses.add(row["availability_status"])

        for match in re.finditer(
            r"insert into public\.market_material_profiles.*?"
            r"on conflict\s*\(material_id\s*,\s*market_code\s*,\s*language_code\)",
            sql,
            re.DOTALL | re.IGNORECASE,
        ):
            statement = match.group(0)
            for code_list in re.findall(
                r"where (?:m\.)?material_code in\s*\((.*?)\)",
                statement,
                re.DOTALL,
            ):
                profiled_codes.update(re.findall(r"'([^']+)'", code_list))
            profiled_codes.update(
                re.findall(
                    r"where (?:m\.)?material_code\s*=\s*'([^']+)'", statement
                )
            )
            availability_statuses.update(
                re.findall(r"::jsonb\s*,\s*'([^']+)'\s+from", statement)
            )
            availability_statuses.update(
                value
                for pair in re.findall(
                    r"then\s*'([^']+)'\s+else\s*'([^']+)'\s+end\s+from",
                    statement,
                )
                for value in pair
            )

    assert len(material_id_to_code) == 280
    assert profiled_codes == set(material_id_to_code.values())
    assert availability_statuses <= allowed_statuses


def test_explicit_supplier_aliases_satisfy_alias_constraints():
    aliases = [
        row
        for path in ALL_PRICE_FILES
        for row in _insert_rows(
            path,
            "reference_material_aliases",
            "material_id,market_code,language_code,alias_key",
        )
    ]
    assert len(aliases) == 11
    assert {row["alias_kind"] for row in aliases} <= {
        "canonical",
        "market_name",
        "supplier_listing",
        "technical_code",
        "synonym",
    }
    assert all(Decimal(row["confidence"]) >= 0 for row in aliases)
    assert all(Decimal(row["confidence"]) <= 100 for row in aliases)


def test_documented_catalog_totals_have_unique_material_and_offer_ids():
    material_ids = []
    material_codes = []
    offer_ids = []
    for path in ALL_PRICE_FILES:
        sql = path.read_text()
        material_section = re.search(
            r"insert into public\.reference_materials.*?values\s*(.*?)on conflict\s*\(material_code\)",
            sql,
            re.DOTALL,
        )
        offer_section = re.search(
            r"insert into public\.market_material_offers.*?values\s*(.*?)on conflict\s*\(market_offer_id\)",
            sql,
            re.DOTALL,
        )
        if material_section:
            material_ids.extend(re.findall(r"\(\s*'([0-9a-f-]{36})'", material_section.group(1)))
            material_codes.extend(
                re.findall(
                    r"\(\s*'[0-9a-f-]{36}'\s*,\s*'([^']+)'",
                    material_section.group(1),
                )
            )
        if offer_section:
            offer_ids.extend(re.findall(r"\(\s*'([0-9a-f-]{36})'", offer_section.group(1)))
    assert len(material_ids) == len(set(material_ids)) == 280
    assert len(material_codes) == len(set(material_codes)) == 280
    assert len(offer_ids) == len(set(offer_ids)) == 320


def test_furniture_core_batch_adds_22_exact_candidate_offers():
    sql = FURNITURE_CORE.read_text()
    assert sql.count("'candidate')") == 22
    assert sql.count("'pair','retail_package'") == 6
    assert "'pack_24'" in sql
    assert '"package_quantity":24' in sql
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 22
    assert "market_material_baselines" not in sql
    assert "'active'" not in sql


def test_furniture_core_batch_covers_runners_supports_and_glides():
    sql = FURNITURE_CORE.read_text()
    assert sql.count("'hardware','drawer_runner'") == 6
    assert sql.count("'hardware','shelf_support'") == 6
    assert sql.count("'hardware','furniture_glide'") == 10
    for length in (300, 350, 400, 450, 500, 550):
        assert f"drawer_runner_basic_pair_{length}mm" in sql
    assert "מסילה בסיסית למגירה 30 ס״מ, זוג" in sql
    assert "תומך מדף דופלו מתכת 5×7.5 מ״מ" in sql
    assert "מחליק טפלון מלבני 100×25 מ״מ" in sql


def test_furniture_core_v2_adds_17_exact_candidate_offers():
    sql = FURNITURE_CORE_V2.read_text()
    material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    offer_section = sql.split("insert into public.market_material_offers", 1)[1].split("on conflict(market_offer_id)", 1)[0]
    material_ids = re.findall(r"\('([0-9a-f-]{36})'", material_section)
    offer_ids = re.findall(r"\('([0-9a-f-]{36})'", offer_section)
    assert len(material_ids) == len(set(material_ids)) == 17
    assert len(offer_ids) == len(set(offer_ids)) == 17
    assert sql.count("'candidate')") == 17
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 17
    assert "market_material_baselines" not in sql


def test_furniture_core_v2_preserves_connector_and_package_semantics():
    sql = FURNITURE_CORE_V2.read_text()
    assert "'confirmat_screw_7x50mm'" in sql
    assert "'minifix_bolt_direct_wood_16_15_short_neck'" in sql
    assert "'minifix_cam_flat_15mm_board16'" in sql
    assert "'pack_12'" in sql
    assert "'per_1000'" in sql
    assert "'pack_100'" in sql
    assert '"price_basis":"per 1000 explicitly stated"' in sql
    for force in (80, 100, 120):
        assert f"'gas_spring_{force}n'" in sql
    assert "out-of-stock microwave gas springs" in sql


def test_furniture_core_v3_adds_count_priced_nail_and_staple_evidence():
    sql = FURNITURE_CORE_V3.read_text()
    assert sql.count("'candidate')") == 8
    assert sql.count("'hardware','bulk_nail_staple'") == 8
    assert sql.count("'pack_2500'") == 5
    assert "'pack_3600'" in sql
    assert "'pack_5700'" in sql
    assert "'pack_5000'" in sql
    assert '"kilogram_normalization_blocked_by":"package mass not stated"' in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v1_adds_six_pricing_behaviours_with_ten_offers():
    sql = RAPID_CORE_V1.read_text()
    assert sql.count("'candidate')") == 10
    for category in ("hinge", "masking_material", "packing_tape", "wood_primer", "wood_paint", "wood_filler"):
        assert f"'{category}'" in sql
    assert "source_title_conflicts_with_description_length" in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v2_adds_six_functional_hardware_behaviours():
    sql = RAPID_CORE_V2.read_text()
    assert sql.count("'candidate')") == 10
    for category in ("drawer_system", "door_system", "cabinet_suspension", "cable_management", "ventilation_hardware", "storage_system", "connector_cover_cap"):
        assert f"'{category}'" in sql
    assert "'complete_drawer'" in sql
    assert "'complete_set'" in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v3_adds_three_previously_empty_behaviours():
    sql = RAPID_CORE_V3.read_text()
    assert sql.count("'candidate')") == 5
    for category in ("wardrobe_rail", "mirror_adhesive", "wood_oil_wax"):
        assert f"'{category}'" in sql
    assert '"mirror_backing_safe_stated":true' in sql
    assert '"promotion":"VAT-free site price"' in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v4_adds_installation_tooling_and_indoor_oil_evidence():
    sql = RAPID_CORE_V4.read_text()
    assert sql.count("'candidate')") == 3
    for category in ("installation_fastener_allowance", "tooling_consumable", "wood_oil_wax"):
        assert f"'{category}'" in sql
    assert '"piece_count":175' in sql
    assert '"wear_allowance_requires":"verified tool life by material and operation"' in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v5_adds_hardboard_edge_hotmelt_and_mirror_evidence():
    sql = RAPID_CORE_V5.read_text()
    assert sql.count("'candidate')") == 8
    for category in ("hardboard", "hot_melt_edge_adhesive", "mirror"):
        assert f"'{category}'" in sql
    assert sql.count('"price_is_configurable_minimum":true') == 2
    assert '"gross_price_per_sqm_ils":136.111111' in sql
    assert '"gross_price_per_sqm_ils":158.730159' in sql
    assert '"gross_price_per_sqm_ils":251.322751' in sql
    assert "market_material_baselines" not in sql


def test_second_large_price_batch_counts_and_candidate_boundary():
    expected = {PANELS_V2: 13, HARDWARE_V2: 19, FASTENERS: 1, PACKAGING: 8}
    for path, offer_count in expected.items():
        sql = path.read_text()
        assert sql.count("'candidate')") == offer_count
        assert "market_material_baselines" not in sql
        assert "on conflict(material_code) do update" in sql
        assert "on conflict(market_offer_id) do update" in sql


def test_second_large_price_batch_preserves_unknowns_instead_of_inventing_values():
    panels = PANELS_V2.read_text()
    packaging = PACKAGING.read_text()
    hardware = HARDWARE_V2.read_text()
    assert panels.count('"normalization_blocked_by":"sheet dimensions not stated"') == 12
    assert '"normalization_blocked_by":"VAT status not stated"' in panels
    assert packaging.count('"normalization_blocked_by":"VAT status not stated"') == 4
    assert '"normalization_blocked_for_area":"length not stated"' in packaging
    assert '"pair_not_assumed":true' in hardware


def test_second_large_price_batch_has_40_unique_material_identities_and_41_offers():
    files = (PANELS_V2, HARDWARE_V2, FASTENERS, PACKAGING)
    material_ids = []
    offer_ids = []
    for path in files:
        sql = path.read_text()
        material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
        offer_section = sql.split("insert into public.market_material_offers", 1)[1].split("on conflict(market_offer_id)", 1)[0]
        material_ids.extend(re.findall(r"\('([0-9a-f-]{36})'", material_section))
        offer_ids.extend(re.findall(r"\('([0-9a-f-]{36})'", offer_section))
    assert len(material_ids) == len(set(material_ids)) == 40
    assert len(offer_ids) == len(set(offer_ids)) == 41


def test_adhesive_batch_adds_29_exact_packages_without_false_net_prices():
    sql = ADHESIVES_V2.read_text()
    assert sql.count("'candidate')") == 29
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 29
    assert "market_material_baselines" not in sql
    assert "'active'" not in sql
    assert "on conflict(material_code) do update" in sql
    assert "on conflict(market_offer_id) do update" in sql


def test_comparison_batch_adds_only_existing_identities_and_exact_aliases():
    sql = COMPARISONS.read_text()
    assert "insert into public.reference_materials" not in sql
    assert sql.count("'candidate')") == 11
    assert sql.count("'supplier_listing'") == 11
    assert "source_channel" in sql
    for channel in ("'trade_supplier'", "'specialist_retailer'", "'diy_retail'"):
        assert channel in sql
    assert "DIY retail is retained as a channel, not a baseline" in sql
    assert "market_material_baselines" not in sql


def test_fastener_matrix_adds_16_identities_and_33_offers():
    sql = FASTENERS_V2.read_text()
    material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    offer_section = sql.split("insert into public.market_material_offers", 1)[1].split("on conflict(market_offer_id)", 1)[0]
    material_ids = re.findall(r"\('([0-9a-f-]{36})'", material_section)
    offer_ids = re.findall(r"\('([0-9a-f-]{36})'", offer_section)
    assert len(material_ids) == len(set(material_ids)) == 16
    assert len(offer_ids) == len(set(offer_ids)) == 33
    assert sql.count("'candidate')") == 33
    assert "market_material_baselines" not in sql


def test_fastener_identity_excludes_supplier_package_size():
    old_sql = FASTENERS.read_text()
    new_sql = FASTENERS_V2.read_text()
    assert "'chipboard_screw_3x20mm'" in old_sql
    assert "wood_screw_3x20mm_pack100" not in old_sql
    assert '"package_quantity":100' not in old_sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    material_section = new_sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    assert "package_quantity" not in material_section
    assert "pack_50" in new_sql
    assert "pack_100" in new_sql
    assert "pack_1000" in new_sql


def test_fastener_matrix_preserves_vat_unknowns_and_flags_outlier():
    sql = FASTENERS_V2.read_text()
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 17
    assert sql.count('"calculation":') == 16
    assert '"price_outlier_review_required":true' in sql
    assert "'unknown',null,'ea'" in sql
    assert "'included',0.040678,'ea'" in sql


def test_dowel_and_handle_screw_batch_adds_16_identities_and_17_offers():
    sql = FASTENERS_V3.read_text()
    material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    offer_section = sql.split("insert into public.market_material_offers", 1)[1].split("on conflict(market_offer_id)", 1)[0]
    material_ids = re.findall(r"\('([0-9a-f-]{36})'", material_section)
    offer_ids = re.findall(r"\('([0-9a-f-]{36})'", offer_section)
    assert len(material_ids) == len(set(material_ids)) == 16
    assert len(offer_ids) == len(set(offer_ids)) == 17
    assert sql.count("'candidate')") == 17


def test_dowel_batch_keeps_stock_form_and_package_semantics_separate():
    sql = FASTENERS_V3.read_text()
    material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    assert "package_quantity" not in material_section
    assert '"form":"pre-cut fluted"' in material_section
    assert '"form":"round rod"' in material_section
    assert "'ea'" in material_section
    assert "'lm'" in material_section
    assert '"package_quantity_not_confirmed":true' in sql


def test_dowel_batch_preserves_vat_and_promotion_boundaries():
    sql = FASTENERS_V3.read_text()
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 11
    assert sql.count("'excluded'") >= 6
    assert sql.count("'2026-10-04'") == 6
    assert "'excluded',9.24,'lm'" in sql
    assert "source_channel" in sql


def test_system_connector_batch_adds_13_exact_identities_and_offers():
    sql = CONNECTORS.read_text()
    material_section = sql.split("insert into public.reference_materials", 1)[1].split("on conflict(material_code)", 1)[0]
    offer_section = sql.split("insert into public.market_material_offers", 1)[1].split("on conflict(market_offer_id)", 1)[0]
    material_ids = re.findall(r"\('([0-9a-f-]{36})'", material_section)
    offer_ids = re.findall(r"\('([0-9a-f-]{36})'", offer_section)
    assert len(material_ids) == len(set(material_ids)) == 13
    assert len(offer_ids) == len(set(offer_ids)) == 13
    assert sql.count("'candidate')") == 13


def test_system_connector_batch_keeps_model_geometry_and_package_boundaries():
    sql = CONNECTORS.read_text()
    for code in (
        "lamello_biscuit_0_4x15x47mm",
        "lamello_tenso_p14_66x27x9_7mm",
        "lamello_clamex_p10_52x19x9_7mm",
        "lamello_divario_p18_75x25x9_7mm",
        "lamello_cabineo_186316_m6_8mm",
        "qfix_white_20mm_screw_7_5mm_cover_set",
    ):
        assert f"'{code}'" in sql
    assert "'pack_1000'" in sql
    assert "'pack_300'" in sql
    assert "'pack_200'" in sql
    assert "'pack_100'" in sql
    assert sql.count('"normalization_blocked_by":"VAT status not stated"') == 13
    assert "market_material_baselines" not in sql


def test_comparison_batch_preserves_promotion_package_and_vat_boundaries():
    sql = COMPARISONS.read_text()
    assert "'2026-10-04'" in sql
    assert '"unit_count":12' in sql
    assert '"normalization_blocked_by":"VAT status not stated"' in sql
    assert '"calculation":"45 / 12.5"' in sql
    assert '"calculation":"21.60 / 1.18 / 14"' in sql


def test_rapid_core_v6_adds_system_specific_euro_screw_evidence():
    sql = RAPID_CORE_V6.read_text()
    assert sql.count("'hardware','system_specific_screw'") == 3
    assert sql.count("'candidate')") == 3
    assert sql.count("'pack_1000'") == 3
    assert '"price_is_starting_from":true' in sql
    assert sql.count('"availability":"unavailable at retrieval"') == 2
    assert '"gross_price_per_piece_ils":0.086' in sql
    assert '"gross_price_per_piece_ils":0.18429' in sql
    assert '"gross_price_per_piece_ils":0.1616' in sql
    assert "market_material_baselines" not in sql


def test_rapid_core_v7_adds_hardwood_and_faced_panel_evidence():
    sql = RAPID_CORE_V7.read_text()
    assert sql.count("'candidate')") == 5
    assert sql.count("'wood','hardwood'") == 2
    assert "'wood','hpl_faced_panel'" in sql
    assert "'wood','veneer_faced_panel'" in sql
    assert '"profile_mm":[19,90]' in sql
    assert '"profile_mm":[19,140]' in sql
    assert '"gross_price_per_sqm_ils":158.895458' in sql
    assert '"displayed_price_range_ils":[575.30,1031.80]' in sql
    assert '"price_is_configurable_minimum":true' in sql
    assert "market_material_baselines" not in sql
