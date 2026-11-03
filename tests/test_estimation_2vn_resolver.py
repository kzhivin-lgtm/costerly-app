from use_cases.estimation_2vn_resolver import TWO_VN_V1, resolve_2vn_geometry
from use_cases.estimation_dimension_graph import build_dimension_graph


REF = "storage://rfq-estimation-evidence/company/run/object/page-1.webp"
OCR = "ocr:event:p1:b0001"


def _input():
    return {
        "input_id": "input-1", "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Cabinet", "quantity": 1,
                       "evidence_pages": [{"page_number": 1, "regions": [{
                           "top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 400,
                       }]}]},
            "evidence": {"artifacts": [{"storage_ref": REF, "page_number": 1, "artifact_kind": "page"}],
                         "ocr_blocks": [{"page_number": 1, "block_ref": OCR, "text": "158", "source": "native_pdf_text",
                                         "bbox": {"top_left_x": 150, "top_left_y": 410, "bottom_right_x": 190, "bottom_right_y": 430}}],
                         "geometry_context": {"vector_line_segments": [{"segment_id": "vector:p1:l1", "page_number": 1,
                             "orientation": "horizontal", "start": {"x": 100, "y": 420}, "end": {"x": 400, "y": 420}}]}},
        },
    }


def _extraction(*, axis="width", projection="front_elevation", orientation="horizontal", resolution="direct"):
    return {
        "document_unit": {"unit": "cm", "basis": "document_convention_assumption", "evidence_refs": [], "assumption_reason": "Furniture scale."},
        "view_interpretations": [{"view_id": "p1-view-001", "projection": projection}],
        "dimension_bindings": [{"assembly_id": "lower", "axis": axis, "view_id": "p1-view-001",
                                "local_orientation": orientation, "dimension_id": "dimension-001", "resolution": resolution}],
        "assemblies": [{"assembly_id": "lower", "dimensions": {axis: {"value": 158, "basis": "derived", "evidence_refs": [OCR]}}}],
        "secondary_items": [], "omissions": [], "coverage": [],
    }


def test_2vn_promotes_only_a_matching_direct_axis_witness():
    resolved, audit = resolve_2vn_geometry(dimension_graph=build_dimension_graph(input_row=_input()), extraction=_extraction())

    dimension = resolved["assemblies"][0]["dimensions"]["width"]
    assert audit["contract_version"] == TWO_VN_V1
    assert dimension["basis"] == "source"
    assert dimension["value"] == 158.0
    assert audit["dimension_witnesses"][0]["verification"] == "direct"


def test_2vn_rejects_a_physical_axis_that_disagrees_with_the_projection():
    resolved, audit = resolve_2vn_geometry(
        dimension_graph=build_dimension_graph(input_row=_input()),
        extraction=_extraction(axis="depth", projection="front_elevation", orientation="horizontal"),
    )

    assert resolved["dimension_bindings"] == []
    assert audit["rejected_bindings"] == [{"assembly_id": "lower", "axis": "depth", "reason": "axis_projection_mismatch"}]
    assert resolved["assemblies"][0]["dimensions"]["depth"]["basis"] == "derived"


def test_2vn_keeps_an_incomplete_drawing_usable_with_cross_view_derivation():
    resolved, audit = resolve_2vn_geometry(
        dimension_graph=build_dimension_graph(input_row=_input()),
        extraction=_extraction(axis="depth", projection="side_elevation", orientation="horizontal", resolution="cross_view"),
    )

    assert resolved["assemblies"][0]["dimensions"]["depth"]["basis"] == "derived"
    assert audit["binding_outcomes"] == {"derived": 1}
