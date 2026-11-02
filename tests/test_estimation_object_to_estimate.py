import pytest

from use_cases.estimation_approximate_bom import compose_approximate_bom_v1
from use_cases.estimation_object_to_estimate import build_object_to_estimate_brief
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
            "quantity": None, "unit": None,
            "evidence_refs": [REF],
        }],
        "assumptions": [], "primary_preview_ref": REF,
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


def test_unitless_technical_furniture_drawing_normalises_the_model_100x_error():
    input_row = {
        "input_id": "input-1", "object_input_revision": 1,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Cabinet", "quantity": 1},
            "evidence": {"artifacts": [{"storage_ref": REF}], "ocr_blocks": [], "ocr_literal_items": []},
        },
    }
    extraction = {
        "object_kind": "cabinet",
        "dimensions": [
            {"key": "width", "value": 160000, "confidence": 90, "evidence_refs": [REF]},
            {"key": "depth", "value": 72000, "confidence": 90, "evidence_refs": [REF]},
            {"key": "height", "value": 265000, "confidence": 90, "evidence_refs": [REF]},
        ],
        "counts": [], "material_roles": [],
    }

    brief = build_object_to_estimate_brief(input_row=input_row, extraction=extraction)

    assert {axis: brief["dimensions_mm"][axis]["value_mm"] for axis in ("width", "depth", "height")} == {
        "width": 1600.0, "depth": 720.0, "height": 2650.0,
    }
    assert "unitless_technical_drawing_centimetre_interpretation" in brief["assumptions"]


def test_wardrobe_recipe_composes_approximate_parts_without_source_claims():
    bom = compose_approximate_bom_v1(_brief())

    assert bom["status"] == "ready"
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


def test_wardrobe_recipe_preserves_explicit_hardware_quantity_as_project_demand():
    brief = _brief(material_roles=[{
        "role": "hardware", "source_name": "Domicile handle AL100",
        "family": "hardware_handle", "specification": {}, "quantity": 6, "unit": "piece",
        "evidence_refs": [REF],
    }])

    bom = compose_approximate_bom_v1(brief)

    hardware = next(item for item in bom["materials"] if item["requirement_id"] == "hardware_handle")
    assert hardware["quantity"] == 12.0
    assert hardware["unit"] == "piece"


def test_wardrobe_recipe_prices_paint_once_as_finish_and_keeps_fittings_separate():
    brief = _brief(material_roles=[
        {
            "role": "finish", "source_name": "Paint Nirlat ISO 11V",
            "family": "paint_lacquer_stain", "specification": {}, "quantity": None, "unit": None,
            "evidence_refs": [REF],
        },
        {
            "role": "hardware", "source_name": "Handle 160 mm",
            "family": "hardware_handle", "specification": {}, "quantity": 4, "unit": "piece",
            "evidence_refs": [REF],
        },
        {
            "role": "hardware", "source_name": "Hinge",
            "family": "hardware_hinge", "specification": {}, "quantity": 8, "unit": "piece",
            "evidence_refs": [REF],
        },
    ])

    bom = compose_approximate_bom_v1(brief)

    by_requirement = {item["requirement_id"]: item for item in bom["materials"]}
    assert by_requirement["visible_facade"]["family"] == "mdf_hdf"
    assert by_requirement["paint_lacquer_stain"]["quantity"] == 2.0
    assert by_requirement["paint_lacquer_stain"]["unit"] == "piece"
    assert by_requirement["hardware_handle"]["quantity"] == 8.0
    assert by_requirement["hardware_hinge"]["quantity"] == 16.0
    assert "default_paint_finish_kit_per_finished_object" in bom["assumptions"]
