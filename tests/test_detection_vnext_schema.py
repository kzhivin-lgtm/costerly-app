from agents.anthropic_adapter import discard_degenerate_evidence_regions
from agents.schemas.detection_registry_schema import (
    DetectionRegistrySchemaError,
    validate_detection_registry,
)
from agents.schemas.detection_schema import validate_detection_result
from agents.schemas.detection_visual_map_schema import (
    normalize_detection_visual_map_group_ids,
    validate_detection_visual_map,
)


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


def test_visual_map_and_registry_keep_representation_identity_separate():
    visual_map = validate_detection_visual_map({
        "visual_groups": [
            {"group_id": "view-001", "page_number": 1, "location_hint": "lower left", "visual_description": "long storage console perspective", "representation_kind": "perspective", "related_group_ids": ["view-002"]},
            {"group_id": "view-002", "page_number": 1, "location_hint": "lower right", "visual_description": "long storage console alternate perspective", "representation_kind": "perspective", "related_group_ids": ["view-001"]},
        ],
    })
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001", "view-002"],
            "visual_identity": "one long storage console shown twice",
            "boundary_basis": "matching full-page structure and panel sequence",
        }],
    }

    assert validate_detection_registry(
        registry,
        visual_group_ids={group["group_id"] for group in visual_map["visual_groups"]},
    ) == registry


def test_visual_map_normalizes_provider_group_ids_before_strict_validation():
    visual_map = {
        "visual_groups": [
            {"group_id": "group_a", "page_number": 1, "location_hint": "left", "visual_description": "console view", "representation_kind": "perspective", "related_group_ids": ["group_b"]},
            {"group_id": "group_b", "page_number": 1, "location_hint": "right", "visual_description": "console view", "representation_kind": "elevation", "related_group_ids": ["group_a"]},
        ],
    }

    normalized = validate_detection_visual_map(
        normalize_detection_visual_map_group_ids(visual_map)
    )

    assert [group["group_id"] for group in normalized["visual_groups"]] == [
        "view-001", "view-002",
    ]
    assert normalized["visual_groups"][0]["related_group_ids"] == ["view-002"]


def test_registry_allows_a_shared_visual_group_when_it_supports_multiple_objects():
    registry = {
        "objects": [
            {"object_id": "object-001", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "first", "boundary_basis": "first"},
            {"object_id": "object-002", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"], "visual_identity": "second", "boundary_basis": "second"},
        ],
    }

    assert validate_detection_registry(
        registry, visual_group_ids={"view-001"}
    ) == registry


def test_registry_allows_unassigned_navigation_only_visual_groups():
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001"], "visual_identity": "cabinet",
            "boundary_basis": "one complete product",
        }],
    }

    assert validate_detection_registry(
        registry,
        visual_group_ids={"view-001", "view-002"},
    ) == registry
