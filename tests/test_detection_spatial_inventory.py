from agents.anthropic_adapter import (
    build_detection_candidate_region_audit,
    build_detection_view_evidence_packages,
)
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


def test_fusion_text_clusters_are_recall_fallback_when_no_graphic_region_exists():
    ocr = {"pages": [{
        "page_number": 1,
        "dimensions": {"width": 2000, "height": 2000},
        "blocks": [{
            "type": "text", "content": "OCR saw text, but no graphic block",
            "top_left_x": 0, "top_left_y": 0,
            "bottom_right_x": 100, "bottom_right_y": 100,
        }],
    }]}
    facts = [
        {"fact_id": "SF001", "page_number": 1, "bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 110, "bottom_right_y": 110,
        }},
        {"fact_id": "SF002", "page_number": 1, "bbox": {
            "top_left_x": 280, "top_left_y": 110,
            "bottom_right_x": 290, "bottom_right_y": 120,
        }},
        {"fact_id": "SF003", "page_number": 1, "bbox": {
            "top_left_x": 1000, "top_left_y": 1000,
            "bottom_right_x": 1010, "bottom_right_y": 1010,
        }},
        {"fact_id": "SF004", "page_number": 1, "bbox": {
            "top_left_x": 1200, "top_left_y": 1000,
            "bottom_right_x": 1210, "bottom_right_y": 1010,
        }},
    ]

    candidates = build_detection_fusion_candidate_regions(ocr, facts)

    assert [(row["candidate_region_id"], row["basis"], row["source_fact_ids"])
            for row in candidates] == [
        ("CR-P001-001", "fusion_text_cluster", ["SF001", "SF002"]),
        ("CR-P001-002", "fusion_text_cluster", ["SF003", "SF004"]),
    ]
    assert all(
        row["bbox"]["bottom_right_x"] > row["bbox"]["top_left_x"]
        and row["bbox"]["bottom_right_y"] > row["bbox"]["top_left_y"]
        for row in candidates
    )


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


def test_evidence_envelope_keeps_external_dimension_with_its_single_island():
    envelope = {
        "top_left_x": 100, "top_left_y": 100,
        "bottom_right_x": 500, "bottom_right_y": 540,
    }
    packages = build_detection_view_evidence_packages(
        visual_groups=[{
            "group_id": "view-001", "page_number": 1,
            "evidence_class": "object_evidence",
        }],
        group_bboxes={"view-001": envelope},
        group_core_bboxes={"view-001": {
            "top_left_x": 120, "top_left_y": 120,
            "bottom_right_x": 480, "bottom_right_y": 480,
        }},
        source_facts=[{
            "fact_id": "SF00001", "page_number": 1, "text": "407",
            "bbox": {
                "top_left_x": 350, "top_left_y": 505,
                "bottom_right_x": 380, "bottom_right_y": 525,
            },
        }],
    )

    assert packages[0]["source_fact_ids"] == ["SF00001"]
    assert packages[0]["core_bbox"]["bottom_right_y"] == 480


def test_evidence_envelope_overlap_uses_core_and_never_duplicates_a_fact():
    packages = build_detection_view_evidence_packages(
        visual_groups=[
            {"group_id": "left", "page_number": 1, "evidence_class": "object_evidence"},
            {"group_id": "right", "page_number": 1, "evidence_class": "object_evidence"},
        ],
        group_bboxes={
            "left": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 100, "bottom_right_y": 100},
            "right": {"top_left_x": 80, "top_left_y": 0, "bottom_right_x": 180, "bottom_right_y": 100},
        },
        group_core_bboxes={
            "left": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 90, "bottom_right_y": 100},
            "right": {"top_left_x": 100, "top_left_y": 0, "bottom_right_x": 180, "bottom_right_y": 100},
        },
        source_facts=[{
            "fact_id": "SF00001", "page_number": 1, "text": "407",
            "bbox": {"top_left_x": 82, "top_left_y": 10, "bottom_right_x": 88, "bottom_right_y": 20},
        }],
    )

    assert packages[0]["source_fact_ids"] == ["SF00001"]
    assert packages[1]["source_fact_ids"] == []


def test_dimension_halo_keeps_outer_numeric_dimension_when_one_island_is_nearby():
    packages = build_detection_view_evidence_packages(
        visual_groups=[{
            "group_id": "view-001", "page_number": 1,
            "evidence_class": "object_evidence",
        }],
        group_bboxes={"view-001": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 500, "bottom_right_y": 500,
        }},
        source_facts=[{
            "fact_id": "SF00407", "page_number": 1, "text": "407",
            "bbox": {
                "top_left_x": 320, "top_left_y": 550,
                "bottom_right_x": 350, "bottom_right_y": 572,
            },
        }],
    )

    assert packages[0]["source_fact_ids"] == ["SF00407"]
    assert packages[0]["dimension_halo_source_fact_ids"] == ["SF00407"]


def test_dimension_halo_does_not_capture_small_revision_numbers():
    packages = build_detection_view_evidence_packages(
        visual_groups=[{
            "group_id": "view-001", "page_number": 1,
            "evidence_class": "object_evidence",
        }],
        group_bboxes={"view-001": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 500, "bottom_right_y": 500,
        }},
        source_facts=[{
            "fact_id": "SF00010", "page_number": 1, "text": "10",
            "bbox": {
                "top_left_x": 320, "top_left_y": 550,
                "bottom_right_x": 340, "bottom_right_y": 572,
            },
        }],
    )

    assert packages[0]["source_fact_ids"] == []
    assert packages[0]["dimension_halo_source_fact_ids"] == []


def test_dimension_halo_leaves_numeric_fact_unowned_when_two_islands_overlap():
    packages = build_detection_view_evidence_packages(
        visual_groups=[
            {"group_id": "left", "page_number": 1, "evidence_class": "object_evidence"},
            {"group_id": "right", "page_number": 1, "evidence_class": "object_evidence"},
        ],
        group_bboxes={
            "left": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 100, "bottom_right_y": 100},
            "right": {"top_left_x": 180, "top_left_y": 0, "bottom_right_x": 280, "bottom_right_y": 100},
        },
        source_facts=[{
            "fact_id": "SF00407", "page_number": 1, "text": "407",
            "bbox": {"top_left_x": 136, "top_left_y": 40, "bottom_right_x": 144, "bottom_right_y": 60},
        }],
    )

    assert [package["source_fact_ids"] for package in packages] == [[], []]
