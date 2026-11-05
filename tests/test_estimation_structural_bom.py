import pytest

from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_structural_bom import build_structural_assembly_bom


REF = "storage://rfq-estimation-evidence/company/run/object/page-1.webp"
OCR_REF = "ocr:event:p1:b0001"


def _input():
    return {
        "input_id": "input-1", "object_input_revision": 1,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Locked Detection Name", "quantity": 1},
            "evidence": {
                "artifacts": [{"storage_ref": REF, "page_number": 1, "artifact_kind": "page"}],
                "ocr_blocks": [{"block_ref": OCR_REF, "page_number": 1, "text": "158 x 72 x 43", "bbox": {}}],
                "ocr_literal_items": [],
            },
        },
    }


def _dimension(value):
    return {"value": value, "basis": "source", "evidence_refs": [OCR_REF]}


@pytest.mark.parametrize('height_mm,hinges', [(600, 2), (601, 2), (1000, 2),
    (1001, 3), (1500, 3), (2000, 3), (2001, 4)])
def test_owner_hinge_height_thresholds_reach_material_demand(height_mm, hinges):
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=['mdf_hdf', 'melamine_faced_particleboard',
            'fibreboard_hardboard', 'hardware_hinge'],
        extraction={
            'document_unit': {'unit': 'cm', 'basis': 'explicit_source', 'evidence_refs': [OCR_REF]},
            'assemblies': [{
                'assembly_id': 'cabinet', 'assembly_role': 'box_carcass', 'quantity': 1,
                'evidence_refs': [REF],
                'dimensions': {'width': _dimension(60), 'height': _dimension(height_mm / 10),
                    'depth': _dimension(60)},
                'counts': {}, 'material_roles': [],
                'front_groups': [{'front_kind': 'hinged_facade', 'quantity': 1, 'arrangement': 'side_by_side'}],
            }],
            'secondary_items': [], 'omissions': [],
        })
    demands = [m for m in result['materials'] if m['family'] == 'hardware_hinge']
    assert len(demands) == 1
    assert demands[0]['quantity'] == hinges and demands[0]['unit'] == 'piece'
    assert result['assemblies'][0]['hardware'] == [
        {'role': 'hinge', 'quantity': hinges, 'purchase_unit': 'piece'}]


def test_structural_drawer_bank_expands_into_real_panels_and_discrete_slides():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["mdf_hdf", "melamine_faced_particleboard", "fibreboard_hardboard", "hardware_drawer_slide"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [{
                "assembly_id": "lower", "assembly_role": "drawer_bank", "quantity": 1, "evidence_refs": [REF],
                "dimensions": {"width": _dimension(158), "height": _dimension(43), "depth": _dimension(72)},
                "counts": {"drawers": 3},
                "material_roles": [
                    {"role": "visible_sheet", "source_name": "Veneered MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []},
                    {"role": "internal_sheet", "source_name": "Internal board", "family": "melamine_faced_particleboard", "basis": "construction_assumption", "evidence_refs": []},
                    {"role": "backing_sheet", "source_name": "Backing", "family": "fibreboard_hardboard", "basis": "construction_assumption", "evidence_refs": []},
                    {"role": "drawer_slide", "source_name": "Drawer slide", "family": "hardware_drawer_slide", "basis": "construction_assumption", "evidence_refs": []},
                ],
            }],
            "secondary_items": [], "omissions": ["unshown fasteners"],
        },
    )

    assert result["object_name"] == "Locked Detection Name"
    assert result["document_unit"]["unit"] == "cm"
    assert {part["component_role"] for part in result["parts"]} >= {
        "carcass_side", "carcass_top_bottom", "carcass_back", "drawer_front", "drawer_bottom", "drawer_side", "drawer_back",
    }
    assert next(part for part in result["parts"] if part["component_role"] == "carcass_side")["length_mm"] == 430
    slide = next(material for material in result["materials"] if material["family"] == "hardware_drawer_slide")
    assert slide["quantity"] == 3
    assert slide["unit"] == "set"
    assert slide["specification"]["depth_mm"] == 600
    drawer_front = next(part for part in result["parts"] if part["component_role"] == "drawer_front")
    assert (drawer_front["length_mm"], drawer_front["width_mm"]) == (1580, pytest.approx(143.333))
    assert result["omissions"] == ["unshown fasteners"]


def test_cabinet_block_composes_front_hardware_by_topology_and_purchase_unit():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=[
            "mdf_hdf", "melamine_faced_particleboard", "fibreboard_hardboard",
            "hardware_drawer_slide", "hardware_hinge", "hardware_lift_system",
        ],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [
                {
                    "assembly_id": "lower-drawers", "assembly_role": "drawer_bank", "quantity": 1,
                    "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(90), "height": _dimension(72), "depth": _dimension(65)},
                    "counts": {"drawers": 5},
                    "front_groups": [{"front_kind": "drawer_front", "quantity": 5, "arrangement": "stacked"}],
                    "material_roles": [],
                },
                {
                    "assembly_id": "upper", "assembly_role": "box_carcass", "quantity": 1,
                    "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(120), "height": _dimension(110), "depth": _dimension(35)},
                    "counts": {},
                    "front_groups": [
                        {"front_kind": "hinged_facade", "quantity": 3, "arrangement": "side_by_side"},
                        {"front_kind": "lift_up_facade", "quantity": 2, "arrangement": "side_by_side"},
                    ],
                    "exposure": {"left": True, "right": False},
                    "material_roles": [],
                },
            ],
            "secondary_items": [], "omissions": [],
        },
    )

    by_family = {material["family"]: material for material in result["materials"]}
    assert by_family["hardware_drawer_slide"]["quantity"] == 5
    assert by_family["hardware_drawer_slide"]["unit"] == "set"
    assert by_family["hardware_drawer_slide"]["specification"]["depth_mm"] == 500
    assert by_family["hardware_hinge"]["quantity"] == 9
    assert by_family["hardware_hinge"]["unit"] == "piece"
    assert by_family["hardware_lift_system"]["quantity"] == 2
    assert by_family["hardware_lift_system"]["unit"] == "set"
    assert any(part["component_role"] == "carcass_side_exposed" for part in result["parts"])
    upper = next(assembly for assembly in result["assemblies"] if assembly["assembly_id"] == "upper")
    assert upper["hardware"] == [
        {"role": "hinge", "quantity": 9, "purchase_unit": "piece"},
        {"role": "gas_lift", "quantity": 2, "purchase_unit": "set"},
    ]


def test_lev1_lower_drawers_are_not_confused_with_a_tall_fixed_screen():
    """Lev 1 has three lower drawers and a decorative fixed slat screen."""
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=[
            "mdf_hdf", "melamine_faced_particleboard", "fibreboard_hardboard",
            "hardware_drawer_slide", "hardware_hinge", "hardware_lift_system",
        ],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [
                {
                    "assembly_id": "lower-drawers", "assembly_role": "drawer_bank", "quantity": 1,
                    "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(158), "height": _dimension(43), "depth": _dimension(72)},
                    "counts": {"drawers": 3},
                    "front_groups": [{"front_kind": "drawer_front", "quantity": 3, "arrangement": "side_by_side"}],
                    "material_roles": [],
                },
                {
                    "assembly_id": "fixed-screen", "assembly_role": "vertical_panel", "quantity": 1,
                    "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(160), "height": _dimension(265), "depth": _dimension(2)},
                    "counts": {}, "front_groups": [], "material_roles": [],
                },
            ],
            "secondary_items": [], "omissions": [],
        },
    )

    by_family = {material["family"]: material for material in result["materials"]}
    assert by_family["hardware_drawer_slide"]["quantity"] == 3
    assert by_family["hardware_drawer_slide"]["unit"] == "set"
    assert by_family["hardware_drawer_slide"]["specification"]["depth_mm"] == 600
    assert "hardware_hinge" not in by_family
    assert "hardware_lift_system" not in by_family
    assert {part["component_role"] for part in result["parts"]} >= {
        "drawer_front", "drawer_bottom", "drawer_side", "drawer_back", "vertical_panel",
    }


def test_missing_cabinet_dimension_uses_auditable_peer_or_construction_default():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["melamine_faced_particleboard", "fibreboard_hardboard"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [
                {"assembly_id": "known", "assembly_role": "box_carcass", "quantity": 1, "evidence_refs": [REF],
                 "dimensions": {"width": _dimension(80), "height": _dimension(72), "depth": _dimension(65)},
                 "counts": {}, "material_roles": []},
                {"assembly_id": "peer", "assembly_role": "box_carcass", "quantity": 1, "evidence_refs": [REF],
                 "dimensions": {"width": _dimension(40), "height": _dimension(72)},
                 "counts": {}, "material_roles": []},
            ], "secondary_items": [], "omissions": [],
        },
    )

    peer = next(assembly for assembly in result["assemblies"] if assembly["assembly_id"] == "peer")
    assert peer["assembly_role"] == "box_carcass"
    assert any("peer depth: Derived from the only source-supported depth" in item for item in result["assumptions"])


def test_structural_composer_does_not_create_unused_sheet_demands_for_a_table():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["mdf_hdf"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [{
                "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [REF],
                "dimensions": {"width": _dimension(160), "depth": _dimension(115)}, "counts": {"top_layers": 2},
                "material_roles": [{"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []}],
            }], "secondary_items": [], "omissions": [],
        },
    )

    assert len(result["materials"]) == 1
    assert len(result["parts"]) == 1
    assert result["parts"][0]["quantity"] == 2


def test_unitless_document_convention_is_converted_consistently():
    row = _input()
    extraction = {
        "document_unit": {
            "unit": "cm", "basis": "document_convention_assumption", "evidence_refs": [],
            "assumption_reason": "A unitless drawing convention was selected.",
        },
        "assemblies": [{
            "assembly_id": "cabinet", "assembly_role": "box_carcass", "quantity": 1, "evidence_refs": [REF],
            "dimensions": {"width": _dimension(160), "height": _dimension(265), "depth": _dimension(158)},
            "counts": {}, "material_roles": [],
        }], "secondary_items": [], "omissions": [],
    }

    result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        allowed_material_families=["melamine_faced_particleboard", "fibreboard_hardboard"],
    )

    assert result["document_unit"] == {"unit": "cm", "evidence_refs": [], "resolution": "model_document_convention"}
    assert next(part for part in result["parts"] if part["component_role"] == "carcass_side")["length_mm"] == 2650

    extraction["document_unit"] = {
        "unit": "mm", "basis": "explicit_source", "evidence_refs": [OCR_REF], "assumption_reason": None,
    }
    explicit_result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        allowed_material_families=["melamine_faced_particleboard", "fibreboard_hardboard"],
    )
    assert explicit_result["document_unit"]["unit"] == "mm"


def test_unit_assumption_refs_are_discarded_and_audited_not_rejected():
    row = _input()
    extraction = {
        "document_unit": {
            "unit": "cm", "basis": "document_convention_assumption", "evidence_refs": [OCR_REF],
            "assumption_reason": "The drawing is unitless.",
        },
        "assemblies": [{
            "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [REF],
            "dimensions": {"width": _dimension(160), "depth": _dimension(115)}, "counts": {},
            "material_roles": [{"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []}],
        }], "secondary_items": [], "omissions": [],
    }

    result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        allowed_material_families=["mdf_hdf"],
    )

    assert result["status"] == "ready"
    assert result["document_unit"]["evidence_refs"] == []
    assert result["normalizations"] == ["document_unit_assumption_refs_discarded"]


def test_scale_gate_overrides_only_a_unitless_model_mm_convention():
    row = _input()
    row["input_payload"]["object"]["evidence_pages"] = [{
        "page_number": 1,
        "regions": [{"top_left_x": 1, "top_left_y": 1, "bottom_right_x": 10, "bottom_right_y": 10}],
    }]
    extraction = {
        "document_unit": {
            "unit": "mm", "basis": "document_convention_assumption", "evidence_refs": [],
            "assumption_reason": "Model convention.",
        },
        "assemblies": [{
            "assembly_id": "cabinet", "assembly_role": "box_carcass", "quantity": 1, "evidence_refs": [REF],
            "dimensions": {"width": _dimension(160), "height": _dimension(265), "depth": _dimension(158)},
            "counts": {}, "material_roles": [],
        }],
        "secondary_items": [], "omissions": [],
        "coverage": [{"region_id": "p1-region-001", "disposition": "assembly", "target_id": "cabinet", "reason": ""}],
    }

    result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        dimension_scale_gate={"decision": {"required_unit": "cm", "reason": "OCR scale witness."}},
        allowed_material_families=["melamine_faced_particleboard", "fibreboard_hardboard"],
    )

    assert result["document_unit"]["resolution"] == "ocr_scale_guard"
    assert result["document_unit"]["unit"] == "cm"
    assert result["document_unit"]["scale_gate"]["required_unit"] == "cm"
    assert next(part for part in result["parts"] if part["component_role"] == "carcass_side")["length_mm"] == 2650
    assert result["coverage"][0]["target_id"] == "cabinet"


def test_coverage_audits_an_unassigned_visible_region_without_suppressing_bom():
    row = _input()
    row["input_payload"]["object"]["evidence_pages"] = [{
        "page_number": 1,
        "regions": [{"top_left_x": 1, "top_left_y": 1, "bottom_right_x": 10, "bottom_right_y": 10}],
    }]
    extraction = {
        "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
        "assemblies": [{
            "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [REF],
            "dimensions": {"width": _dimension(160), "depth": _dimension(115)},
            "counts": {}, "material_roles": [{"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []}],
        }],
        "secondary_items": [], "omissions": [], "coverage": [],
    }

    result = build_structural_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        allowed_material_families=["mdf_hdf"],
    )

    assert result["status"] == "ready"
    assert result["coverage"] == []
    assert result["coverage_audit"] == {
        "status": "not_provided", "expected_region_count": 1,
        "covered_region_ids": [], "missing_region_ids": ["p1-region-001"], "invalid_entry_count": 0,
    }


def test_incomplete_secondary_assembly_is_composed_with_an_auditable_default():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["mdf_hdf"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [
                {
                    "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(160), "depth": _dimension(115)}, "counts": {},
                    "material_roles": [{"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []}],
                },
                {
                    "assembly_id": "incomplete-facades", "assembly_role": "facade_set", "quantity": 1, "evidence_refs": [REF],
                    "dimensions": {"width": _dimension(80)}, "counts": {"facades": 2}, "material_roles": [],
                },
            ],
            "secondary_items": [], "omissions": [],
        },
    )

    assert result["status"] == "ready"
    assert [assembly["assembly_id"] for assembly in result["assemblies"]] == ["table", "incomplete-facades"]
    assert any("incomplete-facades height: Default cabinet height" in item for item in result["assumptions"])
    assert result["structural_omissions"] == []


def test_optional_zero_counts_do_not_reject_a_usable_table_assembly():
    row = _input()
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["mdf_hdf", "purchased_fabricated_component"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [OCR_REF]},
            "assemblies": [{
                "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [REF],
                "dimensions": {"width": _dimension(160), "depth": _dimension(115)},
                "counts": {"top_layers": 0, "legs": 0},
                "material_roles": [
                    {"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "construction_assumption", "evidence_refs": []},
                    {"role": "leg", "source_name": "Furniture leg", "family": "purchased_fabricated_component", "basis": "construction_assumption", "evidence_refs": []},
                ],
            }], "secondary_items": [], "omissions": [],
        },
    )

    assert result["status"] == "ready"
    assert next(part for part in result["parts"] if part["component_role"] == "top")["quantity"] == 1
    assert next(material for material in result["materials"] if material["family"] == "purchased_fabricated_component")["quantity"] == 2


def test_invalid_model_citations_become_audited_assumptions_not_a_terminal_failure():
    row = _input()
    invalid_ref = "page-1"
    result = build_structural_assembly_bom(
        input_row=row,
        dimension_graph=build_dimension_graph(input_row=row),
        allowed_material_families=["mdf_hdf"],
        extraction={
            "document_unit": {"unit": "cm", "basis": "explicit_source", "evidence_refs": [invalid_ref]},
            "assemblies": [{
                "assembly_id": "table", "assembly_role": "table", "quantity": 1, "evidence_refs": [invalid_ref],
                "dimensions": {
                    "width": {"value": 160, "basis": "source", "evidence_refs": [invalid_ref]},
                    "depth": {"value": 115, "basis": "derived", "evidence_refs": [invalid_ref]},
                },
                "counts": {},
                "material_roles": [{"role": "visible_sheet", "source_name": "MDF", "family": "mdf_hdf", "basis": "source_evidence", "evidence_refs": [invalid_ref]}],
            }], "secondary_items": [], "omissions": [],
        },
    )

    assert result["status"] == "ready"
    assert result["document_unit"]["evidence_refs"] == []
    assert result["assemblies"][0]["evidence_refs"] == [REF]
    assert result["materials"][0]["basis"] == "construction_assumption"
    assert set(result["normalizations"]) >= {
        "document_unit_invalid_refs_downgraded",
        "assembly_invalid_refs_replaced_with_page_artifact",
        "dimension_invalid_refs_downgraded_to_assumption",
        "material_invalid_refs_downgraded_to_assumption",
    }
