from agents.anthropic_adapter import discard_degenerate_evidence_regions
from agents.schemas.detection_schema import validate_detection_result


def test_v4_schema_accepts_evidence_regions_and_ui_only_preview_bbox():
    result = validate_detection_result({
        "rfq_run": {
            "run_id": "run-1", "company_id": "company-1", "project_name": "Project",
            "file_name": "drawing.pdf", "source_type": "pdf", "design_partner": "unknown",
            "client": "unknown", "author": "unknown", "document_date": "unknown",
            "pages_detected": 1, "language": "en", "file_quality_level": 3,
            "file_quality_label": "detailed_drawings", "file_quality_confidence": 90,
            "file_quality_notes": "", "status": "intake_parsed", "created_at": "unknown",
        },
        "detected_objects": [{
            "run_id": "run-1", "company_id": "company-1", "object_id": "object-001",
            "object_name": "Object 1", "quantity": 1, "quantity_explicit": False,
            "review_required": False, "evidence_pages": "1", "approved": False, "created_at": "unknown",
            "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "regions": [{"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40}],
                "presentation_preview_bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            }],
        }],
    })

    assert result["detected_objects"][0]["evidence_page_refs"][0]["regions"]


def test_degenerate_evidence_regions_are_dropped_but_the_page_is_preserved():
    result = {
        "detected_objects": [{
            "evidence_page_refs": [{
                "page_number": 3,
                "source_label": "Detail",
                "regions": [
                    {"top_left_x": 20, "top_left_y": 10, "bottom_right_x": 20, "bottom_right_y": 50},
                ],
                "presentation_preview_bbox": {"top_left_x": 5, "top_left_y": 5, "bottom_right_x": 5, "bottom_right_y": 30},
            }],
        }],
    }

    normalized = discard_degenerate_evidence_regions(result)
    ref = normalized["detected_objects"][0]["evidence_page_refs"][0]

    assert ref["page_number"] == 3
    assert ref["regions"] == []
    assert "presentation_preview_bbox" not in ref
