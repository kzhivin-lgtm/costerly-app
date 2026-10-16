import pytest
from unittest.mock import patch

from agents.detection_agent import (
    _enforce_shared_track_door_system_quantity,
    _merge_registry_evidence,
    run_detection_agent,
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
        {"page_number": 1, "source_label": "1", "regions": []},
        {"page_number": 9, "source_label": "9", "regions": []},
        {"page_number": 10, "source_label": "10", "regions": []},
        {"page_number": 13, "source_label": "13", "regions": []},
    ]


def test_detection_runs_sonnet_review_only_for_same_page_complete_assembly_conflict():
    primary_registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1", "quantity": 1,
        "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1],
        "visual_group_ids": ["view-001", "view-002"], "visual_identity": "combined system",
        "boundary_basis": "combined system",
    }]}
    review_registry = {"objects": [
        {
            "object_id": "object-001", "transport_label": "Object 1", "quantity": 1,
            "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001"], "visual_identity": "cabinet",
            "boundary_basis": "separate cabinet envelope",
        },
        {
            "object_id": "object-002", "transport_label": "Object 2", "quantity": 1,
            "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-002"], "visual_identity": "mirror stand",
            "boundary_basis": "separate mirror-stand envelope",
        },
    ]}
    visual_map = {"visual_groups": [
        {"group_id": "view-001", "page_number": 1},
        {"group_id": "view-002", "page_number": 1},
    ]}
    primary_usage = {"raw_usage": {"complete_assembly_island_audit": [
        {"island_id": "island-001", "visual_group_id": "view-001"},
        {"island_id": "island-002", "visual_group_id": "view-002"},
    ]}}
    captured = {}

    def stop_after_capture(**kwargs):
        captured["registry"] = kwargs["locked_registry"]
        raise RuntimeError("captured reviewed registry")

    with (
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            return_value=(visual_map, primary_registry, primary_usage),
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_assembly_island_review_agent",
            return_value=(review_registry, {"event": "assembly_review"}),
        ) as review,
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_capture,
        ),
        pytest.raises(RuntimeError, match="captured reviewed registry"),
    ):
        run_detection_agent(
            file_name="adda.pdf", company_id="001", file_bytes=b"pdf", page_images=[b"page"],
        )

    review.assert_called_once()
    assert len(captured["registry"]["objects"]) == 2


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
        "estimation_evidence_pages": [1],
    }]}

    resolved = _enforce_shared_track_door_system_quantity(registry)

    assert resolved["objects"][0]["quantity"] == 1
    assert resolved["objects"][0]["quantity_explicit"] is False


def test_evidence_packer_receives_every_registry_evidence_page_without_a_dossier_cap():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1, 2, 3, 4, 5],
        "visual_group_ids": ["view-001"], "visual_identity": "one kitchen",
        "boundary_basis": "one integrated kitchen package",
    }]}
    captured: dict = {}

    def stop_after_capture(**kwargs):
        captured.update(kwargs)
        raise RuntimeError("captured evidence packer input")

    with (
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            return_value=({"visual_groups": []}, registry, {"event": "visual_registry"}),
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_capture,
        ),
        pytest.raises(RuntimeError, match="captured evidence packer input"),
    ):
        run_detection_agent(
            file_name="kitchen.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two", b"three", b"four", b"five"],
        )

    assert captured["page_image_numbers"] == [1, 2, 3, 4, 5]
    assert captured["page_images"] == [b"one", b"two", b"three", b"four", b"five"]
