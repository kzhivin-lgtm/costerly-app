from agents.anthropic_adapter import format_detection_v5_membership_handoff


def test_v5102_membership_handoff_marks_literal_source_ids_unambiguously():
    handoff = format_detection_v5_membership_handoff(
        visual_groups=[{
            "group_id": "VG-001",
            "page_number": 1,
            "evidence_class": "object_evidence",
            "representation_kind": "elevation",
            "visual_description": "Cabinet elevation",
            "bbox": {
                "top_left_x": 0, "top_left_y": 0,
                "bottom_right_x": 100, "bottom_right_y": 100,
            },
        }],
        source_facts=[{
            "fact_id": "SF00001",
            "page_number": 1,
            "text": "3310",
            "bbox": {
                "top_left_x": 10, "top_left_y": 10,
                "bottom_right_x": 20, "bottom_right_y": 20,
            },
        }],
    )

    assert "SRC=registry_view:VG-001;[SF00001] \"3310\"" in handoff
    assert "SF00001:3310" not in handoff


def test_membership_handoff_keeps_directly_owned_outer_dimension_reading():
    handoff = format_detection_v5_membership_handoff(
        visual_groups=[{
            "group_id": "VG-001",
            "page_number": 1,
            "evidence_class": "object_evidence",
            "representation_kind": "elevation",
            "visual_description": "Cabinet elevation",
            "bbox": {
                "top_left_x": 100, "top_left_y": 100,
                "bottom_right_x": 300, "bottom_right_y": 300,
            },
        }],
        source_facts=[{
            "fact_id": "VISDIM00001",
            "page_number": 1,
            "text": "3310",
            "visual_group_id": "VG-001",
            "bbox": {
                "top_left_x": 30, "top_left_y": 120,
                "bottom_right_x": 70, "bottom_right_y": 140,
            },
        }],
    )

    assert "[VISDIM00001] \"3310\"" in handoff
