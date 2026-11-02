import pytest

from use_cases.estimation_approximate_bom import compose_approximate_bom_v1
from use_cases.estimation_object_to_estimate_contract import (
    OBJECT_TO_ESTIMATE_V1,
    validate_object_to_estimate_v1,
)


REF = "storage://rfq-estimation-evidence/company/run/object/revision/page-2.webp"


def _measurement(value, *, basis="evidence", rule=None):
    return {
        "value_mm": value, "basis": basis,
        "evidence_refs": [REF] if basis == "evidence" else [],
        "assumption_rule": rule,
    }


def _count(value, *, basis="evidence", rule=None):
    return {
        "value": value, "basis": basis,
        "evidence_refs": [REF] if basis == "evidence" else [],
        "assumption_rule": rule,
    }


def _brief(**overrides):
    brief = {
        "contract_version": OBJECT_TO_ESTIMATE_V1,
        "input_id": "input-1", "object_input_revision": 1, "run_id": "run-1",
        "company_id": "company-1", "object_id": "object-1", "object_name": "Wardrobe",
        "quantity": 2, "status": "ready", "object_kind": "wardrobe",
        "dimensions_mm": {
            "width": _measurement(2400), "depth": _measurement(600), "height": _measurement(2600),
        },
        "counts": {"bay_count": _count(4), "door_count": _count(4)},
        "material_roles": [{
            "role": "visible_facade", "source_name": "Paint Nirlat IS0011W",
            "family": "mdf_hdf", "specification": {"board_type": "mdf", "thickness_mm": 18},
            "evidence_refs": [REF],
        }],
        "assumptions": [], "review_items": [], "primary_preview_ref": REF,
    }
    brief.update(overrides)
    return brief


def test_construction_brief_keeps_evidence_and_assumption_measurements_distinct():
    brief = _brief(dimensions_mm={
        "width": _measurement(2400),
        "depth": _measurement(600, basis="assumption", rule="default_carcass_thickness_18mm"),
        "height": _measurement(2600),
    })

    result = validate_object_to_estimate_v1(brief)

    assert result["dimensions_mm"]["width"]["evidence_refs"] == [REF]
    assert result["dimensions_mm"]["depth"] == {
        "value_mm": 600.0, "basis": "assumption", "evidence_refs": [],
        "assumption_rule": "default_carcass_thickness_18mm",
    }


def test_construction_brief_rejects_assumption_claiming_evidence():
    brief = _brief(dimensions_mm={
        "width": _measurement(2400, basis="assumption", rule="default_carcass_thickness_18mm"),
        "depth": _measurement(600), "height": _measurement(2600),
    })
    brief["dimensions_mm"]["width"]["evidence_refs"] = [REF]

    with pytest.raises(ValueError, match="assumption may not claim evidence"):
        validate_object_to_estimate_v1(brief)


def test_wardrobe_recipe_composes_approximate_parts_without_source_claims():
    bom = compose_approximate_bom_v1(_brief())

    assert bom["status"] == "review_required"
    assert bom["recipe_version"] == "wardrobe_carcass_v1"
    assert {item["requirement_id"] for item in bom["materials"]} == {
        "visible_facade", "internal_carcass", "backing",
    }
    assert {item["part_id"] for item in bom["parts"]} == {
        "facade_doors", "carcass_sides", "carcass_top_bottom", "carcass_shelves", "backing_panels",
    }
    sides = next(item for item in bom["parts"] if item["part_id"] == "carcass_sides")
    assert sides["quantity"] == 16
    assert sides["length_mm"] == 2600
    assert sides["width_mm"] == 600
    assert all(item["basis"] == "approximate_recipe" for item in bom["parts"])
    assert "default_internal_melamine_faced_particleboard" in bom["assumptions"]
    assert "default_backing_hardboard" in bom["assumptions"]


def test_wardrobe_recipe_rejects_impossible_carcass_geometry():
    brief = _brief(dimensions_mm={
        "width": _measurement(100), "depth": _measurement(600), "height": _measurement(2600),
    })

    with pytest.raises(ValueError, match="incompatible with carcass thickness"):
        compose_approximate_bom_v1(brief)
