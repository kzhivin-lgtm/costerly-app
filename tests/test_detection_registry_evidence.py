from agents.detection_agent import _merge_registry_evidence
from agents.detection_agent import _remove_uncertain_envelope_axes


def test_registry_evidence_keeps_full_estimation_set_not_only_visual_dossier():
    result = {
        "detected_objects": [{
            "object_id": "object-001",
            "evidence_pages": "1,9",
            "evidence_page_refs": [
                {"page_number": 1, "source_label": "1", "roles": ["identity"]},
                {"page_number": 9, "source_label": "9", "roles": ["overall_dimensions"]},
            ],
        }],
    }
    registry = {"objects": [{
        "object_id": "object-001", "estimation_evidence_pages": [1, 9, 10, 13],
    }]}

    merged = _merge_registry_evidence(result, registry)

    assert merged["detected_objects"][0]["evidence_pages"] == "1,9,10,13"
    assert merged["detected_objects"][0]["evidence_page_refs"] == [
        {"page_number": 1, "source_label": "1", "roles": ["identity", "construction"]},
        {"page_number": 9, "source_label": "9", "roles": ["overall_dimensions", "construction"]},
        {"page_number": 10, "source_label": "10", "roles": ["construction"]},
        {"page_number": 13, "source_label": "13", "roles": ["construction"]},
    ]


def test_explicitly_approximate_depth_is_not_passed_as_an_external_dimension():
    result = _remove_uncertain_envelope_axes({"detected_objects": [{
        "notes": "Total depth ~1100 mm varies by block.",
        "dimensions_json": {"width": 2965, "depth": 1100, "height": 1800},
    }]})

    assert result["detected_objects"][0]["dimensions_json"]["depth"] == 0
