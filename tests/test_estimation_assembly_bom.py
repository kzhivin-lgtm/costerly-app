import pytest

from use_cases.estimation_assembly_bom import ASSEMBLY_BOM_V1, build_assembly_bom
from use_cases.estimation_dimension_graph import build_dimension_graph


REF = "storage://rfq-estimation-evidence/company/run/object/page-1.webp"
OCR_REF = "ocr:event:p1:b0001"


def _input():
    return {
        "input_id": "input-1", "object_input_revision": 1,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Name from Detection", "quantity": 1, "evidence_pages": []},
            "evidence": {
                "artifacts": [{"storage_ref": REF, "page_number": 1, "artifact_kind": "page"}],
                "ocr_blocks": [{"block_ref": OCR_REF, "page_number": 1, "text": "1600 x 600", "bbox": {}}],
                "ocr_literal_items": [],
            },
        },
    }


def _extraction(*, material_basis="construction_assumption", material_refs=None):
    return {
        "assemblies": [{
            "assembly_id": "base", "evidence_refs": [REF], "components": [{
                "component_id": "top", "component_role": "horizontal_panel", "quantity": 1,
                "length_value": 160, "width_value": 60, "dimension_unit": "cm", "dimension_unit_basis": "explicit_source",
                "geometry_basis": "evidence", "geometry_evidence_refs": [OCR_REF], "assumption_reason": None,
                "material": {
                    "source_name": "assumed MDF", "family": "mdf", "specification": {"thickness_mm": 18},
                    "basis": material_basis, "evidence_refs": material_refs or [],
                },
            }],
        }],
        "omissions": ["unshown fasteners"],
    }


def test_assembly_bom_preserves_detection_identity_and_never_uses_object_kind_recipe():
    row = _input()
    result = build_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=_extraction(),
        allowed_material_families=["mdf", "ldsp"],
    )

    assert result["contract_version"] == ASSEMBLY_BOM_V1
    assert result["object_name"] == "Name from Detection"
    assert "object_kind" not in result
    assert result["assemblies"] == [{"assembly_id": "base", "evidence_refs": [REF], "part_ids": ["base:top"]}]
    assert result["materials"] == [{
        "requirement_id": "material-001", "source_name": "assumed MDF", "family": "mdf",
        "specification": {"thickness_mm": 18}, "basis": "construction_assumption", "evidence_refs": [],
        "quantity": None, "unit": None,
    }]
    assert result["parts"][0]["length_mm"] == 1600
    assert result["omissions"] == ["unshown fasteners"]


def test_assembly_bom_rejects_assumption_that_claims_source_evidence():
    row = _input()
    with pytest.raises(ValueError, match="assumption material may not claim source evidence"):
        build_assembly_bom(
            input_row=row, dimension_graph=build_dimension_graph(input_row=row),
            extraction=_extraction(material_refs=[OCR_REF]), allowed_material_families=["mdf"],
        )


def test_assembly_bom_rejects_unknown_material_family():
    row = _input()
    with pytest.raises(ValueError, match="unsupported material"):
        build_assembly_bom(
            input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=_extraction(),
            allowed_material_families=["plywood"],
        )


def test_assembly_bom_converts_explicit_document_unit_assumption_deterministically():
    row = _input()
    extraction = _extraction()
    component = extraction["assemblies"][0]["components"][0]
    component["geometry_basis"] = "derived"
    component["dimension_unit_basis"] = "document_convention_assumption"
    component["assumption_reason"] = "Unitless drawing dimensions follow centimetre convention."

    result = build_assembly_bom(
        input_row=row, dimension_graph=build_dimension_graph(input_row=row), extraction=extraction,
        allowed_material_families=["mdf"],
    )

    assert result["parts"][0]["length_mm"] == 1600
    assert result["parts"][0]["dimension_unit"] == "cm"
    assert result["assumptions"] == [
        "Dimension unit assumption: Unitless drawing dimensions follow centimetre convention."
    ]
