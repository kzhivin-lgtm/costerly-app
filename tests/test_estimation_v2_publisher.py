import pytest
from decimal import Decimal
from types import SimpleNamespace

import use_cases.estimation_v2_publisher as publisher


def _ready_facts():
    return {
        "contract_version": "estimation_object_facts_v2",
        "input_id": "input-1",
        "object_input_revision": 1,
        "run_id": "run-1",
        "company_id": "company-1",
        "object_id": "object-1",
        "object_name": "Object 1",
        "quantity": 1,
        "status": "ready",
        "dimensions_mm": {"width": 1000, "depth": 500, "height": 700},
        "materials": [{
            "requirement_id": "m1", "source_name": "MDF", "family": "mdf",
            "specification": {}, "quantity": 2, "unit": "sqm",
            "evidence_refs": ["ref"],
        }],
        "features": {},
        "manufacturing_features": [],
        "purchased_components": [],
        "labor_operations": [{
            "operation_id": "op-1", "operation_code": "panel_saw_cutting",
            "route": "in_house_machine", "quantity": 5, "unit": "cut_sequence",
            "batch_key": "mdf-panel-saw", "machine_code": "wood_panel_saw",
            "material_requirement_ids": ["m1"], "basis": "Five visible cuts",
            "provenance": "derived", "evidence_refs": ["ref"], "confidence": 70,
        }],
        "source_facts": [],
        "review_items": [],
        "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp",
    }


def test_company_offer_price_uses_deterministic_median_and_removes_vat():
    class Resolution:
        offer_ids = ("offer-1", "offer-2", "offer-3")

    price, source = publisher._company_offer_price(
        Resolution(),
        [
            {"offer_id": "offer-1", "normalized_price": "118", "normalized_unit": "sqm", "vat_included": True},
            {"offer_id": "offer-2", "normalized_price": "90", "normalized_unit": "sqm", "vat_included": False},
            {"offer_id": "offer-3", "normalized_price": "120", "normalized_unit": "sqm", "vat_included": False},
        ],
        requested_unit="sqm",
        vat_percent=18,
    )

    assert price == 100.0
    assert source == "company-offer:offer-1"


def test_sheet_thickness_normalization_is_visible_and_auditable(monkeypatch):
    resolution = SimpleNamespace(
        status="resolved", authority="israel_pricing", price_typical=Decimal("200"),
        pricing_identity_price_id="price-22", offer_ids=(),
        thickness_policy="next_higher_sheet_thickness",
        requested_thickness_mm=Decimal("20"), priced_thickness_mm=Decimal("22"),
        resolved_material_name="MDF, raw, 22 mm",
    )
    monkeypatch.setattr(
        publisher, "resolve_estimate_material_requirement", lambda **_kwargs: resolution
    )
    facts = _ready_facts()
    facts["estimate_id"] = "estimate-1"
    facts["materials"][0].update({
        "source_name": "MDF 20 mm", "quantity": 3, "unit": "sqm",
    })

    rows, costs = publisher._material_rows_and_costs(
        facts=facts,
        catalogs={
            "items": [], "offers": [], "identities": [], "prices": [],
            "reference_materials": [], "reference_aliases": [],
            "pricing_identity_members": [],
        },
        vat_percent=18,
    )

    assert rows[0]["item_name"] == "MDF, raw, 22 mm"
    assert rows[0]["catalog_match_query"] == "MDF 20 mm"
    assert "Requested 20 mm" in rows[0]["notes"]
    assert rows[0]["cost"] == 600
    assert costs[0]["amount"] == 600


def test_role_rate_uses_company_profile_position_mapping():
    rate, matched = publisher._role_rate(
        "wood_machine_operator",
        [{"position_code": "cnc_operator", "gross_hourly_rate": 40, "deleted_at": None}],
        176,
    )
    assert rate == 40
    assert matched == "cnc_operator"


def test_role_rate_falls_back_to_production_department_average_only():
    rate, matched = publisher._role_rate(
        "draftsperson",
        [
            {"position_code": "carpenter", "department": "Production", "gross_hourly_rate": 40, "deleted_at": None},
            {"position_code": "welder", "department": "production", "gross_hourly_rate": 60, "deleted_at": None},
            {"position_code": "office_manager", "department": "Office", "gross_hourly_rate": 200, "deleted_at": None},
        ],
        176,
    )
    assert rate == 50
    assert matched == "company_average_production"


def test_role_rate_never_uses_office_or_management_average():
    rate, matched = publisher._role_rate(
        "welder",
        [
            {"position_code": "office_manager", "department": "Office", "gross_hourly_rate": 200, "deleted_at": None},
            {"position_code": "general_manager", "department": "Management", "gross_hourly_rate": 300, "deleted_at": None},
        ],
        176,
    )

    assert rate is None
    assert matched is None


def test_unresolved_material_does_not_receive_invented_unit_price(monkeypatch):
    resolution = SimpleNamespace(
        status="unresolved", authority=None, price_typical=None,
        pricing_identity_price_id=None, offer_ids=(), thickness_policy=None,
        requested_thickness_mm=None, priced_thickness_mm=None,
        resolved_material_name=None,
    )
    monkeypatch.setattr(
        publisher, "resolve_estimate_material_requirement", lambda **_kwargs: resolution
    )
    facts = _ready_facts()
    facts["estimate_id"] = "estimate-1"
    rows, costs = publisher._material_rows_and_costs(
        facts=facts,
        catalogs={
            "items": [], "offers": [], "identities": [], "prices": [], "baselines": [],
            "reference_materials": [], "reference_aliases": [],
            "pricing_identity_members": [],
        },
        vat_percent=18,
    )

    assert rows[0]["cost"] is None
    assert rows[0]["unit_cost"] is None
    assert rows[0]["needs_price"] is True
    assert rows[0]["needs_review"] is True
    assert rows[0]["raw_agent_json"]["fallback"]["rule"] == "no_evidence_based_price"
    assert costs[0]["status"] == "review_required"
    assert costs[0]["amount"] is None


def test_material_family_without_price_evidence_has_no_fixed_allowance():
    catalogs = {"identities": [], "prices": [], "baselines": [], "reference_materials": []}
    abrasive, abrasive_rule, _ = publisher._fallback_material_unit_cost(
        {"family": "abrasives", "unit": "sheet", "specification": {}}, catalogs
    )
    fastener, fastener_rule, _ = publisher._fallback_material_unit_cost(
        {"family": "counted_furniture_connectors", "unit": "pcs", "specification": {}}, catalogs
    )

    assert (abrasive, abrasive_rule) == (None, "no_evidence_based_price")
    assert (fastener, fastener_rule) == (None, "no_evidence_based_price")


def test_square_tube_defaults_to_1_5_mm_and_uses_only_square_tube_kg_price():
    catalogs = {
        "identities": [
            {"pricing_identity_id": "square", "price_attributes": {
                "material_family": "carbon_steel", "detail_material_id": "mat-square"}},
            {"pricing_identity_id": "sheet", "price_attributes": {
                "material_family": "carbon_steel", "detail_material_id": "mat-sheet"}},
        ],
        "prices": [
            {"pricing_identity_id": "square", "unit": "kg", "price_typical": 11.21},
            {"pricing_identity_id": "sheet", "unit": "kg", "price_typical": 100},
        ],
        "baselines": [],
        "reference_materials": [
            {"material_id": "mat-square", "canonical_name": "Carbon steel S235, square tube, mill finish"},
            {"material_id": "mat-sheet", "canonical_name": "Carbon steel S235, sheet, mill finish"},
        ],
    }

    price, rule, details = publisher._fallback_material_unit_cost(
        {"family": "carbon_steel", "source_name": "Square tube 20x20 mm",
         "unit": "m", "specification": {"profile_section": "20x20mm"}},
        catalogs,
    )

    assert rule == "steel_profile_length_to_weight"
    assert details["wall_thickness_mm"] == 1.5
    assert details["wall_thickness_policy"] == "furniture_profile_default_1_5_mm"
    assert details["kg_price"] == 11.21
    assert details["kg_per_m"] == pytest.approx(0.87135)
    assert price == pytest.approx(10.7446)


def test_profile_section_dimensions_infer_square_tube_when_name_is_generic():
    geometry = publisher._steel_profile_geometry({
        "family": "carbon_steel", "source_name": "metal profile",
        "specification": {"profile_section": "20x20"},
    })

    assert geometry["material_form"] == "square tube"
    assert geometry["wall_thickness_mm"] == 1.5


def test_perforated_metal_sheet_is_normalized_from_coating_to_carbon_steel():
    material = publisher._material_for_pricing({
        "family": "metal_coatings",
        "source_name": "перфорированный металлический лист",
        "unit": "m²",
    })

    assert material["family"] == "carbon_steel"
    assert material["pricing_normalization"] == "perforated_metal_sheet_is_carbon_steel"

    price, rule, details = publisher._fallback_material_unit_cost(
        {**material, "specification": {"thickness_mm": 5}},
        {
            "identities": [{"pricing_identity_id": "sheet", "price_attributes": {
                "material_family": "carbon_steel", "detail_material_id": "mat-sheet",
            }}],
            "prices": [{"pricing_identity_id": "sheet", "unit": "kg", "price_typical": 10}],
            "reference_materials": [{
                "material_id": "mat-sheet", "canonical_name": "Carbon steel sheet",
            }],
            "baselines": [],
        },
    )

    assert rule == "steel_sheet_area_to_weight"
    assert details["kg_per_m2"] == 39.25
    assert price == 431.75


@pytest.mark.parametrize(
    ("family", "source_unit", "expected_unit"),
    (
        ("mdf", "м²", "m²"),
        ("mdf", "шт", "sheet"),
        ("carbon_steel", "м", "m"),
        ("wood_coatings", "л", "l"),
    ),
)
def test_extracted_cyrillic_units_are_normalized_for_pricing(
    family, source_unit, expected_unit,
):
    material = publisher._material_for_pricing({
        "family": family, "source_name": "material", "unit": source_unit,
    })

    assert material["unit"] == expected_unit
    assert material["source_unit"] == source_unit


def test_sheet_piece_quantity_with_dimensions_is_converted_to_area():
    material = publisher._material_for_pricing({
        "family": "plywood", "source_name": "door panel", "unit": "шт",
        "quantity": 2, "specification": {"width_mm": 880, "height_mm": 630},
    })

    assert material["unit"] == "m²"
    assert material["quantity"] == pytest.approx(1.1088)
    assert material["pricing_normalization"] == "sheet_piece_dimensions_to_area"


def test_localized_material_name_is_rendered_in_english_from_canonical_family():
    assert publisher._english_material_name({
        "family": "galvanized_steel", "source_name": "металлический каркас",
        "specification": {"profile_section": "20x20 mm"},
    }) == "Galvanized Steel, 20x20 mm"


def test_aluminium_profile_uses_aluminium_density_and_family_price():
    catalogs = {
        "identities": [{"pricing_identity_id": "al-profile", "price_attributes": {
            "material_family": "aluminium", "detail_material_id": "al-square",
        }}],
        "prices": [{"pricing_identity_id": "al-profile", "unit": "kg", "price_typical": 100}],
        "reference_materials": [{
            "material_id": "al-square", "canonical_name": "Aluminium square tube",
        }],
        "baselines": [],
    }

    price, rule, details = publisher._fallback_material_unit_cost(
        {"family": "aluminium", "source_name": "square profile", "unit": "m",
         "specification": {"profile_section": "20x20"}},
        catalogs,
    )

    assert rule == "steel_profile_length_to_weight"
    assert details["kg_per_m"] == pytest.approx(0.2997)
    assert price == pytest.approx(32.967)


def test_angle_defaults_to_1_5_mm_but_explicit_wall_is_preserved():
    defaulted = publisher._steel_profile_geometry({
        "family": "carbon_steel", "source_name": "Steel angle 30x30", "specification": {},
    })
    explicit = publisher._steel_profile_geometry({
        "family": "carbon_steel", "source_name": "Steel angle 30x30x3", "specification": {},
    })

    assert defaulted["material_form"] == "angle"
    assert defaulted["wall_thickness_mm"] == 1.5
    assert explicit["wall_thickness_mm"] == 3
    assert explicit["wall_thickness_policy"] == "explicit"


def test_locked_material_policy_rows_include_consumables_and_packaging():
    facts = _ready_facts()
    facts["estimate_id"] = "estimate-1"

    rows, costs = publisher._material_policy_rows_and_costs(
        facts=facts, primary_material_total=500,
    )

    assert rows[0]["item_name"] == "Consumables"
    assert rows[0]["cost"] == 25
    assert rows[0]["raw_agent_json"]["percent"] == 5
    assert costs[0]["amount"] == 25
    assert costs[0]["status"] == "resolved"
    assert rows[1]["item_name"] == "Packaging"
    assert rows[1]["cost"] == 5
    assert rows[1]["raw_agent_json"]["percent"] == 1
    assert all(row["source"] == "pricing_policy" for row in rows)
    assert all(row["raw_agent_json"]["locked"] is True for row in rows)


def test_routine_consumables_are_not_priced_as_separate_material_rows(monkeypatch):
    monkeypatch.setattr(
        publisher, "resolve_estimate_material_requirement",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("routine consumable must bypass resolver")),
    )
    facts = _ready_facts()
    facts["estimate_id"] = "estimate-1"
    facts["materials"][0].update({
        "source_name": "Common screws", "family": "bulk_fasteners", "unit": "lot",
    })

    rows, costs = publisher._material_rows_and_costs(
        facts=facts,
        catalogs={"items": [], "offers": [], "identities": [], "prices": []},
        vat_percent=18,
    )

    assert rows == []
    assert costs == []


def test_manufacturing_features_are_routed_through_existing_cost_engine(monkeypatch):
    facts = _ready_facts()
    facts["materials"][0]["specification"] = {"thickness_mm": 5}
    facts["materials"][0]["family"] = "carbon_steel"
    facts["manufacturing_features"] = [{
        "feature_id": "laser-1", "process": "sheet_laser",
        "material_requirement_id": "m1",
        "measurements": {"path_length_m": 12},
        "flags": {"production_file_ready": "yes"},
        "evidence_refs": ["ref"],
    }]
    captured = {}

    def _build(**kwargs):
        captured.update(kwargs)
        return [{
            "line_id": "laser-line", "section": "material", "cost": 450,
            "raw_agent_json": {"calculator": "sheet_laser_subcontractor"},
        }]

    monkeypatch.setattr(publisher, "build_manufacturing_cost_lines", _build)
    rows, costs = publisher._manufacturing_rows_and_costs(
        facts={**facts, "estimate_id": "estimate-1"},
        production_context={"machines": []}, parameter_rows=[{"parameter_id": "p1"}],
    )

    feature = captured["estimation_result"]["manufacturing"][0]
    assert feature["material_family"] == "carbon_steel"
    assert feature["thickness_mm"] == 5
    assert feature["path_length_m"] == 12
    assert rows[0]["cost"] == 450
    assert costs[0]["section"] == "machinery"
    assert costs[0]["amount"] == 450


def test_publisher_writes_agent_materials_operations_totals_and_completed_status(monkeypatch):
    facts = _ready_facts()
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(publisher, "validate_object_facts", lambda *_args, **_kwargs: facts)
    monkeypatch.setattr(publisher, "_settings", lambda *_args: ({"vat_percent": 18}, {}))
    monkeypatch.setattr(publisher, "_catalogs", lambda *_args: {})
    monkeypatch.setattr(publisher, "_material_rows_and_costs", lambda **_kwargs: ([{"line_id": "m", "cost": 100}], [{"line_id": "mc", "section": "material", "status": "resolved", "amount": 100, "currency": "ILS", "source_ref": "source", "reason_codes": []}]))

    def _labor(**kwargs):
        assert kwargs["facts"]["labor_operations"] == facts["labor_operations"]
        return ([{"line_id": "l", "cost": 50}], [{"line_id": "lc", "section": "labor", "status": "resolved", "amount": 62.5, "currency": "ILS", "source_ref": "source", "reason_codes": []}], 1, 62.5)

    monkeypatch.setattr(publisher, "_labor_rows_and_costs", _labor)
    monkeypatch.setattr(publisher, "build_overhead_lines", lambda **_kwargs: [{"line_id": "o", "cost": 10}])
    monkeypatch.setattr(publisher, "compose_object_estimate", lambda **_kwargs: {"status": "complete", "self_cost_unit": 172.5})
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object", lambda *_args, **kwargs: events.append(("lines", kwargs["lines"])))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_totals", lambda *_args, **kwargs: events.append(("totals", kwargs)))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress", lambda *_args, **kwargs: events.append(("status", kwargs["status"])))

    result = publisher.publish_estimation_v2_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-1", "object_id": "object-1"},
        context={"families": {"mdf"}, "settings": {"vat_percent": 18},
                 "overhead_monthly": {}, "catalogs": {}, "employees": [],
                 "production_context": {}},
    )

    assert result["status"] == "complete"
    assert [event[0] for event in events] == ["status", "lines", "totals", "status"]
    assert events[-1] == ("status", "completed")
    assert events[2][1]["self_cost_ex_vat"] == 172.5
    assert events[2][1]["vat_amount"] == 31.05


def test_publisher_preserves_review_required_without_fake_totals(monkeypatch):
    facts = {
        "status": "review_required", "company_id": "company-1", "object_id": "object-1",
        "review_items": [{"code": "dimensions_missing", "severity": "blocking"}],
    }
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(publisher, "validate_object_facts", lambda *_args, **_kwargs: facts)
    monkeypatch.setattr(publisher, "_material_rows_and_costs", lambda **_kwargs: ([{"line_id": "m1"}], []))
    monkeypatch.setattr(publisher, "_purchased_component_rows_and_costs", lambda _facts, _catalogs: ([], []))
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object", lambda *_args, **kwargs: events.append({"lines": kwargs["lines"]}))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_totals", lambda *_args, **kwargs: events.append({"totals": kwargs}))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress", lambda *_args, **kwargs: events.append(kwargs))

    result = publisher.publish_estimation_v2_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-1", "object_id": "object-1"},
        context={"families": {"mdf"}, "catalogs": {}, "settings": {}},
    )

    assert result["status"] == "review_required"
    assert result["reason_codes"] == ["dimensions_missing"]
    assert [row["line_id"] for row in events[0]["lines"]] == [
        "m1", "object-1_material_policy_consumables", "object-1_material_policy_packaging",
    ]
    assert events[1:] == [{"totals": {
        "estimate_id": "estimate-1", "object_id": "object-1",
        "self_cost_ex_vat": None, "vat_amount": None, "self_cost_total": None,
    }}, {
        "estimate_id": "estimate-1", "object_id": "object-1",
        "status": "review_required", "progress_percent": 100,
        "progress_label": "object_facts_review_required",
    }]
