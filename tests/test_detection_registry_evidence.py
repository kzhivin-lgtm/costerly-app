from agents.detection_agent import (
    _enforce_shared_track_door_system_quantity,
    _merge_registry_evidence,
)


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
        "object_id": "object-001", "quantity": 1, "quantity_explicit": False,
        "estimation_evidence_pages": [1, 9, 10, 13],
    }]}

    merged = _merge_registry_evidence(result, registry)

    assert merged["detected_objects"][0]["evidence_pages"] == "1,9,10,13"
    assert merged["detected_objects"][0]["evidence_page_refs"] == [
        {"page_number": 1, "source_label": "1", "roles": ["identity", "construction"]},
        {"page_number": 9, "source_label": "9", "roles": ["overall_dimensions", "construction"]},
        {"page_number": 10, "source_label": "10", "roles": ["construction"]},
        {"page_number": 13, "source_label": "13", "roles": ["construction"]},
    ]


def test_registry_locks_complete_system_quantity_against_component_count():
    result = {
        "detected_objects": [{
            "object_id": "object-001", "quantity": 2, "quantity_explicit": True,
            "evidence_pages": "1", "evidence_page_refs": [],
        }],
    }
    registry = {"objects": [{
        "object_id": "object-001", "quantity": 1, "quantity_explicit": False,
        "estimation_evidence_pages": [1],
    }]}

    merged = _merge_registry_evidence(result, registry)

    assert merged["detected_objects"][0]["quantity"] == 1
    assert merged["detected_objects"][0]["quantity_explicit"] is False


def test_registry_resolves_shared_track_leaves_to_one_commercial_door_system():
    registry = {"objects": [{
        "object_id": "object-002",
        "transport_label": "Object 2",
        "quantity": 2,
        "quantity_explicit": False,
        "visual_identity": "Two sliding door leaves on an overhead track",
        "boundary_basis": "One continuous track forms one commercial door system",
        "identity_pages": [1],
        "dossier_pages": [1],
        "estimation_evidence_pages": [1],
    }]}

    resolved = _enforce_shared_track_door_system_quantity(registry)

    assert resolved["objects"][0]["quantity"] == 1
    assert resolved["objects"][0]["quantity_explicit"] is False
