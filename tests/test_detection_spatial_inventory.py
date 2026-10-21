from agents.anthropic_adapter import build_detection_candidate_region_audit
from agents.detection_fusion_candidate_regions import build_detection_fusion_candidate_regions


def _ocr_with_graphic_region() -> dict:
    return {"pages": [{"page_number": 1, "blocks": [
        {
            "type": "image", "content": "graphical drawing",
            "top_left_x": 300, "top_left_y": 100,
            "bottom_right_x": 900, "bottom_right_y": 800,
        },
        {
            "type": "text", "content": "sidebar note",
            "top_left_x": 0, "top_left_y": 0,
            "bottom_right_x": 200, "bottom_right_y": 900,
        },
    ]}]}


def test_fusion_candidate_region_enriches_graphic_bbox_with_source_facts():
    facts = [{
        "fact_id": "SF00001", "page_number": 1, "source": "native_pdf_text",
        "bbox": {"top_left_x": 400, "top_left_y": 200, "bottom_right_x": 500, "bottom_right_y": 250},
    }]
    assert build_detection_fusion_candidate_regions(_ocr_with_graphic_region(), facts) == [{
        "candidate_region_id": "CR-P001-001", "page_number": 1,
        "bbox": {
            "top_left_x": 300, "top_left_y": 100,
            "bottom_right_x": 900, "bottom_right_y": 800,
        },
        "basis": "mistral_graphic_region",
        "source_fact_ids": ["SF00001"],
    }]


def test_candidate_region_without_island_requires_a_registry_explanation_in_audit():
    candidates = [{
        "candidate_region_id": "CR-P001-001", "page_number": 1,
        "bbox": {"top_left_x": 300, "top_left_y": 100, "bottom_right_x": 900, "bottom_right_y": 800},
        "basis": "mistral_graphic_region", "source_fact_ids": [],
    }]
    audit = build_detection_candidate_region_audit(
        candidate_regions=candidates,
        candidate_region_exceptions=[{
            "candidate_region_id": "CR-P001-001", "reason": "title block",
        }],
        visual_groups=[], group_bboxes={}, group_id_mapping={},
    )
    assert audit[0]["status"] == "explained_non_island"
