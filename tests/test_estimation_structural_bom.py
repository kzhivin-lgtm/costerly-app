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
    assert next(material for material in result["materials"] if material["family"] == "hardware_drawer_slide")["quantity"] == 3
    assert result["omissions"] == ["unshown fasteners"]


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
