import copy
import json
from pathlib import Path

import pytest

from use_cases.estimation_v2_labor_adapter import build_labor_input
from use_cases.labor_engine import BASELINES, estimate_labor


def _operation(
    operation_id,
    operation_code,
    quantity,
    *,
    route="in_house_manual",
    machine_code=None,
    unit="item",
):
    return {
        "operation_id": operation_id,
        "operation_code": operation_code,
        "route": route,
        "quantity": quantity,
        "unit": unit,
        "batch_key": f"batch-{operation_id}",
        "machine_code": machine_code,
        "material_requirement_ids": ["material-1"],
        "basis": "Derived from supplied part geometry",
        "provenance": "derived",
        "evidence_refs": ["evidence-1"],
        "confidence": 70,
    }


def _plan(*operations):
    return {
        "object_id": "object-1",
        "quantity": 1,
        "materials": [{"requirement_id": "material-1", "family": "mdf"}],
        "labor_operations": list(operations),
    }


def _context(*machines):
    return {
        "machines": [
            {"machine_code": code, "availability_status": "in_house"}
            for code in machines
        ]
    }


def _codes(result):
    return [line["operation_code"] for line in result["labor_lines"]]


def test_agent_created_operations_are_calculated_without_object_classification():
    plan = _plan(
        _operation(
            "cut",
            "panel_saw_cutting",
            11,
            route="in_house_machine",
            machine_code="wood_panel_saw",
            unit="cut_sequence",
        ),
        _operation("assembly", "carcass_assembly", 1, unit="assembly"),
        _operation("inspect", "quality_inspection", 1, unit="assembly"),
    )

    result = estimate_labor(plan, _context("wood_panel_saw"))

    assert result["status"] == "estimated"
    assert _codes(result) == ["panel_saw_cutting", "carcass_assembly", "quality_inspection"]
    assert all(line["role_allocations"][0]["hours"] > 0 for line in result["labor_lines"])


def test_machine_operation_requires_exact_available_company_capability():
    plan = _plan(_operation(
        "cut", "panel_saw_cutting", 4,
        route="in_house_machine", machine_code="wood_panel_saw",
    ))

    result = estimate_labor(plan, _context())

    assert result["status"] == "review_required"
    assert result["review_items"][0]["code"] == "machinery_unavailable:wood_panel_saw"


def test_manual_operation_cannot_claim_a_machine_route():
    plan = _plan(_operation(
        "assembly", "carcass_assembly", 1,
        route="in_house_machine", machine_code="wood_panel_saw",
    ))

    result = estimate_labor(plan, _context("wood_panel_saw"))

    assert result["status"] == "review_required"
    assert result["review_items"][0]["code"] == "manual_route_invalid:carcass_assembly"


def test_identical_operation_plans_produce_identical_labor_trace():
    plan = _plan(_operation("weld", "mig_mag_welding", 1.4, unit="weld_m"))
    assert estimate_labor(plan, _context()) == estimate_labor(plan, _context())


def test_estimation_ready_facts_adapt_without_object_classification():
    facts = json.loads(
        Path("tests/fixtures/estimation_v2/e01_complete_object.json").read_text()
    )["facts"]

    labor_input = build_labor_input(facts)
    result = estimate_labor(labor_input, _context("wood_panel_saw"))

    assert labor_input["labor_operations"] == facts["labor_operations"]
    assert result["status"] == "estimated"
    assert _codes(result) == ["panel_saw_cutting", "carcass_assembly"]


def test_labor_adapter_accepts_review_facts_for_approximate_costing():
    facts = json.loads(
        Path("tests/fixtures/estimation_v2/e01_complete_object.json").read_text()
    )["facts"]
    facts = copy.deepcopy(facts)
    facts["status"] = "review_required"

    labor_input = build_labor_input(facts)
    assert labor_input["labor_operations"] == facts["labor_operations"]


def test_delivery_and_site_installation_are_not_labor_baselines():
    assert not {
        "vehicle_loading", "delivery_trip", "manual_site_carry", "site_protection",
        "cabinet_installation", "metalwork_installation", "site_anchoring",
        "final_adjustment", "site_cleanup",
    } & set(BASELINES)
