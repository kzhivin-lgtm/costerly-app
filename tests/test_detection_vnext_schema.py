from agents.schemas.detection_schema import validate_detection_result


def test_vnext_schema_accepts_page_roles_and_isolated_preview_bbox():
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
            "quantity_confidence": 80, "confidence": 90, "evidence_pages": "1",
            "dimensions_json": {"unit": "mm", "width": 100, "depth": 0, "height": 200,
                                "thickness": 0, "diameter": 0, "profile_size": "unknown", "raw_text": "W 100 x H 200 mm"},
            "notes": "", "approved": False, "created_at": "unknown",
            "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "roles": ["identity", "overall_dimensions"],
                "preview_bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            }],
            "evidence_anchors": [],
        }],
    })

    assert result["detected_objects"][0]["evidence_page_refs"][0]["roles"] == ["identity", "overall_dimensions"]
