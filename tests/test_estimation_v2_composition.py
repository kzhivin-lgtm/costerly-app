import copy
import json
from pathlib import Path

import pytest

from use_cases.estimation_v2_composition import (
    CONSTRUCTION_TEMPLATE_VALUES,
    ESTIMATION_REASON_CODE_VALUES,
    EstimationV2ContractError,
    compose_object_estimate,
    validate_object_facts,
)


FIXTURE_PATH = Path("tests/fixtures/estimation_v2/e01_complete_object.json")


def _fixture():
    return json.loads(FIXTURE_PATH.read_text())


def test_e01_complete_object_is_composed_without_llm_database_or_engine_calls():
    fixture = _fixture()

    first = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=fixture["cost_lines"],
        allowed_material_families=set(fixture["allowed_material_families"]),
    )
    second = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=fixture["cost_lines"],
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert first == second
    assert first["status"] == fixture["expected"]["status"]
    assert first["self_cost_unit"] == fixture["expected"]["self_cost_unit"]
    assert first["self_cost_total"] == fixture["expected"]["self_cost_total"]
    assert first["selling_price_unit_suggestion"] == fixture["expected"]["selling_price_unit_suggestion"]
    assert first["selling_price_markup_percent"] == 30.0
    assert first["reason_codes"] == []
    assert first["primary_preview_ref"].startswith("storage://rfq-estimation-evidence/")


def test_object_facts_reject_prices_hours_and_other_deterministic_outputs():
    fixture = _fixture()
    for forbidden_key in ("unit_price", "hours", "overhead", "sale_price"):
        facts = copy.deepcopy(fixture["facts"])
        facts["materials"][0][forbidden_key] = 1

        with pytest.raises(EstimationV2ContractError, match="owned by a deterministic engine"):
            validate_object_facts(
                facts,
                allowed_material_families=set(fixture["allowed_material_families"]),
            )


def test_missing_labor_result_keeps_self_cost_incomplete_with_exact_reason():
    fixture = _fixture()
    cost_lines = [line for line in fixture["cost_lines"] if line["section"] != "labor"]

    result = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=cost_lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert result["status"] == "review_required"
    assert result["reason_codes"] == ["labor_result_unavailable"]
    assert result["resolved_cost_subtotal"] == 615.0
    assert result["self_cost_unit"] is None
    assert result["self_cost_total"] is None
    assert result["selling_price_unit_suggestion"] is None


def test_e06_unresolved_material_price_stays_visible_but_blocks_self_cost():
    fixture = _fixture()
    lines = copy.deepcopy(fixture["cost_lines"])
    material = next(line for line in lines if line["section"] == "material")
    material["status"] = "review_required"
    material["amount"] = None
    material["reason_codes"] = ["material_price_unresolved"]

    result = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert result["status"] == "review_required"
    assert result["reason_codes"] == ["material_price_unresolved"]
    assert result["resolved_cost_subtotal"] == 975.0
    assert result["self_cost_total"] is None
    assert any(line["section"] == "material" for line in result["cost_lines"])


def test_object_facts_require_versioned_material_and_template_vocabularies():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["materials"][0]["family"] = "agent_invented_family"
    with pytest.raises(EstimationV2ContractError, match="versioned catalog"):
        validate_object_facts(facts, allowed_material_families={"birch_plywood"})

    facts = copy.deepcopy(fixture["facts"])
    facts["template"]["code"] = "agent_invented_template"
    with pytest.raises(EstimationV2ContractError, match="template.code is unsupported"):
        validate_object_facts(facts, allowed_material_families={"birch_plywood"})

    assert "base_cabinet_open" in CONSTRUCTION_TEMPLATE_VALUES
    assert "labor_result_unavailable" in ESTIMATION_REASON_CODE_VALUES


def test_object_facts_allow_exact_catalog_family_with_spaces():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["materials"][0]["family"] = "laminated solid wood panel"

    result = validate_object_facts(
        facts,
        allowed_material_families={"laminated solid wood panel"},
    )

    assert result["materials"][0]["family"] == "laminated solid wood panel"


def test_e05_review_facts_expose_missing_values_and_block_self_cost():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["status"] = "review_required"
    facts["quantity"] = None
    facts["template"] = {
        "code": None,
        "confidence": 0,
        "provenance": "explicit",
        "evidence_refs": [],
    }
    facts["dimensions_mm"] = {"width": None, "depth": None, "height": None}
    facts["materials"] = []
    facts["review_items"] = [
        {
            "code": "dimensions_missing",
            "severity": "blocking",
            "path": "dimensions_mm",
            "message": "Overall dimensions are not stated in the evidence.",
            "evidence_refs": ["ocr:ocr-1:p1:b0001"],
        }
    ]

    assert validate_object_facts(facts, allowed_material_families={"birch_plywood"})["status"] == "review_required"

    result = compose_object_estimate(
        facts=facts,
        cost_lines=[],
        allowed_material_families={"birch_plywood"},
    )
    assert result["status"] == "review_required"
    assert "dimensions_missing" in result["reason_codes"]
    assert result["self_cost_total"] is None

    facts["review_items"] = []
    with pytest.raises(EstimationV2ContractError, match="need at least one blocking review item"):
        validate_object_facts(facts, allowed_material_families={"birch_plywood"})


def test_currency_mismatch_never_publishes_self_cost():
    fixture = _fixture()
    lines = copy.deepcopy(fixture["cost_lines"])
    lines[0]["currency"] = "USD"

    result = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert result["status"] == "review_required"
    assert result["currency"] is None
    assert result["reason_codes"] == ["cost_currency_mismatch"]
    assert result["self_cost_total"] is None


def test_e07_external_fabrication_is_purchased_without_matching_machine_cost():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["purchased_components"] = [
        {
            "component_id": "stone-top-1",
            "component_type": "stone_countertop",
            "quantity": 1,
            "unit": "job",
            "specification": {
                "width_mm": 1200,
                "depth_mm": 560,
                "material": "engineered_stone",
                "finish": "polished",
                "cutout_count": 1,
                "installation_scope": "included",
            },
            "evidence_refs": ["ocr:ocr-1:p1:b0004"],
        }
    ]
    lines = copy.deepcopy(fixture["cost_lines"])
    lines.append({
        "line_id": "purchased-stone-1",
        "section": "purchased_component",
        "status": "resolved",
        "amount": 300,
        "currency": "ILS",
        "source_ref": "supplier-quote:stone-1",
        "reason_codes": [],
    })

    result = compose_object_estimate(
        facts=facts,
        cost_lines=lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert result["status"] == "complete"
    assert result["section_totals"]["purchased_component"] == 300.0
    assert result["section_totals"]["machinery"] == 0.0
    assert not any(line["section"] == "machinery" for line in result["cost_lines"])


def test_e08_manufacturing_feature_requires_one_resolved_machinery_cost():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["manufacturing_features"] = [
        {
            "feature_id": "cnc-1",
            "process": "cnc_router",
            "material_requirement_id": "material-e01-1",
            "measurements": {
                "thickness_mm": 18,
                "part_count": 7,
                "sheet_count": 2,
                "path_length_m": 18.5,
                "pass_count": 2,
                "hole_count": 24,
                "pocket_count": 0,
                "edge_banding_length_m": 7.2,
            },
            "flags": {
                "production_file_ready": "yes",
                "rectangular_parts_only": "yes",
                "single_face_processing": "yes",
                "standard_operations_only": "yes",
                "has_freeform_contours": "no",
                "has_internal_cutouts": "no",
                "has_pockets": "no",
                "has_horizontal_or_end_drilling": "no",
                "has_repeated_hole_patterns": "yes",
                "has_tight_positional_relationships": "yes",
                "straight_edge_to_edge_cuts_only": "yes",
                "rough_finish_acceptable": "no",
                "material_and_thickness_supported": "yes"
            },
            "evidence_refs": ["ocr:ocr-1:p1:b0005"],
        }
    ]
    lines = copy.deepcopy(fixture["cost_lines"])
    lines.append({
        "line_id": "machinery-cnc-1",
        "section": "machinery",
        "status": "resolved",
        "amount": 160,
        "currency": "ILS",
        "source_ref": "machinery-result:cnc-1",
        "reason_codes": [],
    })

    result = compose_object_estimate(
        facts=facts,
        cost_lines=lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert result["status"] == "complete"
    assert result["section_totals"]["machinery"] == 160.0
    assert result["self_cost_total"] == 1555.0


def test_e09_failed_object_does_not_invalidate_completed_object():
    fixture = _fixture()
    completed = compose_object_estimate(
        facts=fixture["facts"],
        cost_lines=fixture["cost_lines"],
        allowed_material_families=set(fixture["allowed_material_families"]),
    )
    failed_lines = copy.deepcopy(fixture["cost_lines"])
    labor = next(line for line in failed_lines if line["section"] == "labor")
    labor["status"] = "failed"
    labor["amount"] = None
    labor["reason_codes"] = ["deterministic_engine_failed"]
    failed = compose_object_estimate(
        facts={**fixture["facts"], "input_id": "input-e09-r1", "object_id": "cabinet-e09"},
        cost_lines=failed_lines,
        allowed_material_families=set(fixture["allowed_material_families"]),
    )

    assert completed["status"] == "complete"
    assert completed["self_cost_total"] == 1395.0
    assert failed["status"] == "failed"
    assert failed["self_cost_total"] is None


def test_ready_facts_reject_unknown_purchased_component_quantity():
    fixture = _fixture()
    facts = copy.deepcopy(fixture["facts"])
    facts["purchased_components"] = [{
        "component_id": "edge-1",
        "component_type": "perforated_metal_edging",
        "quantity": None,
        "unit": "job",
        "specification": {},
        "evidence_refs": ["ocr:ocr-1:p1:b0001"],
    }]

    with pytest.raises(EstimationV2ContractError, match="ready facts"):
        validate_object_facts(
            facts,
            allowed_material_families=set(fixture["allowed_material_families"]),
        )
