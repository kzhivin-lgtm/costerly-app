from use_cases.estimation_dimension_graph import DIMENSION_GRAPH_V1, build_dimension_graph


REF = "storage://rfq-estimation-evidence/company/run/object/page-1.webp"


def _input():
    return {
        "input_id": "input-1", "object_input_revision": 3,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {
                "object_id": "object-1", "object_name": "Fixed object name", "quantity": 2,
                "evidence_pages": [{"page_number": 1, "regions": [
                    {"top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 400},
                    {"top_left_x": 500, "top_left_y": 100, "bottom_right_x": 800, "bottom_right_y": 400},
                ]}],
            },
            "evidence": {
                "artifacts": [{"storage_ref": REF, "page_number": 1, "artifact_kind": "page"}],
                "ocr_blocks": [
                    {"page_number": 1, "block_ref": "ocr:event:p1:b0001", "text": "72", "source": "native_pdf_text",
                     "bbox": {"top_left_x": 430, "top_left_y": 230, "bottom_right_x": 470, "bottom_right_y": 260}},
                    {"page_number": 1, "block_ref": "ocr:event:p1:b0002", "text": "solid wood", "source": "mistral_ocr",
                     "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                ],
                "ocr_literal_items": [],
                "geometry_context": {"page_profiles": [{
                    "page_number": 1, "representation": "mixed", "coordinate_evidence": "usable",
                    "eligible_mechanisms": ["ocr", "native_anchor_recall"],
                    "raw_metrics": {"native_text_span_count": 4, "vector_primitive_count": 21, "vector_summary_status": "exact"},
                }]},
            },
        },
    }


def test_dimension_graph_keeps_fixed_object_identity_and_records_only_source_numbers():
    graph = build_dimension_graph(input_row=_input())

    assert graph["contract_version"] == DIMENSION_GRAPH_V1
    assert graph["object_name"] == "Fixed object name"
    assert graph["quantity"] == 2
    assert graph["dimension_numbers"] == [{
        "dimension_id": "dimension-001", "page_number": 1, "raw_text": "72", "numeric_value": 72.0,
        "printed_unit": None,
        "bbox": {"top_left_x": 430.0, "top_left_y": 230.0, "bottom_right_x": 470.0, "bottom_right_y": 260.0},
        "evidence_refs": ["ocr:event:p1:b0001"], "source": "native_pdf_text",
    }]
    assert graph["relations"][0]["relation"] == "nearest_view_candidate"
    assert graph["relations"][0]["basis"] == "coordinate_proximity"
    assert graph["page_capabilities"][0]["vector_primitive_count"] == 21
    assert "construction" in graph["limitations"][1]


def test_dimension_graph_does_not_require_vector_capability_or_invent_a_relation():
    input_row = _input()
    input_row["input_payload"]["object"]["evidence_pages"][0]["regions"] = []
    input_row["input_payload"]["evidence"]["geometry_context"] = {}

    graph = build_dimension_graph(input_row=input_row)

    assert len(graph["dimension_numbers"]) == 1
    assert graph["relations"] == []
    assert graph["page_capabilities"] == []


def test_dimension_graph_preserves_native_vector_line_only_as_a_candidate():
    input_row = _input()
    input_row["input_payload"]["evidence"]["geometry_context"]["vector_line_segments"] = [{
        "segment_id": "vector:p1:l00001", "page_number": 1, "orientation": "horizontal",
        "start": {"x": 400, "y": 270}, "end": {"x": 500, "y": 270},
        "coordinate_basis": "native_pdf_vector_rendered_pixels",
    }]

    graph = build_dimension_graph(input_row=input_row)

    assert graph["vector_line_candidates"][0]["segment_id"] == "vector:p1:l00001"
    relation = next(item for item in graph["relations"] if item["relation"] == "number_to_vector_line_candidate")
    assert relation["basis"] == "source_vector_line_proximity"
    assert "axis" not in relation
