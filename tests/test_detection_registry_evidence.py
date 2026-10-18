import pytest
from unittest.mock import patch

from agents.detection_agent import (
    DEFAULT_CLAUDE_DETECTION_V4_MODEL,
    _apply_assembly_association_repairs,
    _enforce_shared_track_door_system_quantity,
    _merge_registry_evidence,
    _record_locked_evidence_handoff_audit,
    run_detection_agent,
)
from agents.anthropic_adapter import DetectionVisualRegistryValidationError
from use_cases.rfq_processing import process_uploaded_rfq


ONE_ASSEMBLY_VISUAL_MAP = {"visual_groups": [{
    "group_id": "view-001", "page_number": 1, "location_hint": "center",
    "visual_description": "one complete assembly", "representation_kind": "elevation",
    "commercial_role": "assembly_view",
}]}


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


def test_registry_source_transport_label_overrides_evidence_pass_name():
    result = {"detected_objects": [{
        "object_id": "object-001", "object_name": "Kitchen",
        "quantity": 1, "quantity_explicit": False,
        "evidence_page_refs": [{"page_number": 1, "source_label": "1", "regions": []}],
    }]}
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Kitchen N56",
        "quantity": 1, "quantity_explicit": False,
        "estimation_evidence_pages": [1],
    }]}

    merged = _merge_registry_evidence(result, registry)

    assert merged["detected_objects"][0]["object_name"] == "Kitchen N56"


def test_locked_evidence_handoff_audit_records_final_registry_invariants():
    event = {"raw_usage": {"attempt_label": "primary"}}
    registry = {"objects": [{
        "object_id": "object-001", "quantity": 1,
        "estimation_evidence_pages": [1, 3],
    }]}
    result = {"detected_objects": [{
        "object_id": "object-001", "quantity": 1,
        "evidence_page_refs": [
            {"page_number": 1, "regions": []},
            {"page_number": 3, "regions": []},
        ],
    }]}

    audited = _record_locked_evidence_handoff_audit(
        event, registry=registry, result=result,
    )

    assert audited["raw_usage"]["attempt_label"] == "primary"
    assert audited["raw_usage"]["locked_evidence_handoff_audit"] == {
        "registry_object_ids": ["object-001"],
        "result_object_ids": ["object-001"],
        "object_sequence_preserved": True,
        "registry_quantities": {"object-001": 1},
        "result_quantities": {"object-001": 1},
        "quantity_preserved": True,
        "registry_evidence_pages": {"object-001": [1, 3]},
        "result_evidence_pages": {"object-001": [1, 3]},
        "evidence_page_contract_preserved": True,
    }


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
    stages: list[str] = []

    def stop_after_capture(**kwargs):
        captured.update(kwargs)
        raise RuntimeError("captured evidence packer input")

    with (
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            return_value=(ONE_ASSEMBLY_VISUAL_MAP, registry, {"event": "visual_registry"}),
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
            stage_callback=stages.append,
        )

    assert captured["page_image_numbers"] == [1, 2, 3, 4, 5]
    assert captured["page_images"] == [b"one", b"two", b"three", b"four", b"five"]
    assert stages == [
        "Detection Registry started",
        "Detection Registry completed",
        "Detection Evidence handoff started",
    ]


def test_v42_routes_default_registry_and_evidence_packer_to_haiku():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}
    evidence_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return ONE_ASSEMBLY_VISUAL_MAP, registry, {"event": "visual_registry"}

    def stop_after_capture(**kwargs):
        evidence_call.update(kwargs)
        raise RuntimeError("captured evidence packer model")

    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_assembly_association_resolver",
            side_effect=AssertionError("resolver must not run without orphan views"),
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_capture,
        ),
        pytest.raises(RuntimeError, match="captured evidence packer model"),
    ):
        run_detection_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"],
        )

    assert registry_call["model"] == DEFAULT_CLAUDE_DETECTION_V4_MODEL
    assert evidence_call["primary_model_override"] == DEFAULT_CLAUDE_DETECTION_V4_MODEL


def test_v42_routes_only_adda_style_registry_to_sonnet():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}
    evidence_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return ONE_ASSEMBLY_VISUAL_MAP, registry, {"event": "visual_registry"}

    def stop_after_capture(**kwargs):
        evidence_call.update(kwargs)
        raise RuntimeError("captured evidence packer model")

    two_islands_page = {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 400, "bottom_right_y": 400},
            {"top_left_x": 500, "top_left_y": 0, "bottom_right_x": 900, "bottom_right_y": 400},
        ],
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_capture,
        ),
        pytest.raises(RuntimeError, match="captured evidence packer model"),
    ):
        run_detection_agent(
            file_name="adda.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"],
            ocr_package={"pages": [two_islands_page, two_islands_page]},
        )

    assert registry_call["model"] == "claude-sonnet-4-6"
    assert evidence_call["primary_model_override"] == DEFAULT_CLAUDE_DETECTION_V4_MODEL


def test_assembly_association_repair_creates_a_new_commercial_object_for_orphans():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "mirror console", "boundary_basis": "console envelope",
    }]}
    visual_map = {"visual_groups": [
        {"group_id": "view-001", "page_number": 1, "location_hint": "left", "visual_description": "console", "representation_kind": "elevation", "commercial_role": "assembly_view"},
        {"group_id": "view-002", "page_number": 1, "location_hint": "right", "visual_description": "display cabinet", "representation_kind": "elevation", "commercial_role": "assembly_view"},
    ]}
    association = {
        "attach_existing": [],
        "new_objects": [{
            "visual_group_ids": ["view-002"], "visual_identity": "display cabinet",
            "boundary_basis": "separate finished envelope and function", "quantity": 1,
            "quantity_explicit": False, "evidence_page_numbers": [1],
        }],
    }

    repaired = _apply_assembly_association_repairs(registry, visual_map, association)

    assert [item["object_id"] for item in repaired["objects"]] == [
        "object-001", "object-002",
    ]
    assert repaired["objects"][1]["visual_group_ids"] == ["view-002"]
    assert repaired["objects"][1]["quantity"] == 1
    assert repaired["objects"][1]["estimation_evidence_pages"] == [1]


def test_detection_agent_runs_association_resolver_only_for_orphan_assembly_views():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "mirror console", "boundary_basis": "console envelope",
    }]}
    visual_map = {"visual_groups": [
        {"group_id": "view-001", "page_number": 1, "location_hint": "left", "visual_description": "console", "representation_kind": "elevation", "commercial_role": "assembly_view"},
        {"group_id": "view-002", "page_number": 1, "location_hint": "right", "visual_description": "display cabinet", "representation_kind": "elevation", "commercial_role": "assembly_view"},
    ]}
    association = {
        "attach_existing": [],
        "new_objects": [{
            "visual_group_ids": ["view-002"], "visual_identity": "display cabinet",
            "boundary_basis": "separate finished envelope and function", "quantity": 1,
            "quantity_explicit": False, "evidence_page_numbers": [1],
        }],
    }
    resolver_call: dict = {}
    evidence_call: dict = {}

    def capture_resolver(**kwargs):
        resolver_call.update(kwargs)
        return association, {"event": "assembly_association"}

    def stop_after_capture(**kwargs):
        evidence_call.update(kwargs)
        raise RuntimeError("captured evidence packer after association")

    with (
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            return_value=(visual_map, registry, {"event": "visual_registry"}),
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_assembly_association_resolver",
            side_effect=capture_resolver,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_capture,
        ),
        pytest.raises(RuntimeError, match="captured evidence packer after association"),
    ):
        run_detection_agent(
            file_name="adda.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"],
        )

    assert resolver_call["orphan_group_ids"] == ["view-002"]
    assert resolver_call["page_images"] == [b"page"]
    assert [item["object_id"] for item in evidence_call["locked_registry"]["objects"]] == [
        "object-001", "object-002",
    ]


def test_processing_persists_visual_registry_validation_audit_before_reraising(monkeypatch):
    failure_event = {
        "company_id": "001", "run_id": None, "file_name": "drawing.pdf",
        "agent_name": "detection", "operation": "rfq_detection_visual_registry",
        "model": "test-model", "prompt_version": "test-prompt", "input_tokens": 1,
        "output_tokens": 1, "status": "failed", "raw_usage": {"audit": "payload"},
    }
    persisted: list[dict] = []
    ocr_package = {
        "model": "none", "contract_version": "ocr_v2", "status": "skipped",
        "pages": [], "evidence": {"text_blocks": [], "literal_items": []}, "usage": {},
        "processing_seconds": 0.0,
    }

    monkeypatch.setattr("use_cases.rfq_processing.get_supabase_client", lambda: object())
    monkeypatch.setattr("use_cases.rfq_processing.record_rfq_upload", lambda **_kwargs: None)
    monkeypatch.setattr("use_cases.rfq_processing.persist_estimation_original", lambda **_kwargs: None)
    monkeypatch.setattr("use_cases.rfq_processing.should_use_detection_page_images", lambda **_kwargs: False)
    monkeypatch.setattr("use_cases.rfq_processing._run_optional_ocr", lambda **_kwargs: (ocr_package, None))
    monkeypatch.setattr(
        "use_cases.rfq_processing.run_detection_agent",
        lambda **_kwargs: (_ for _ in ()).throw(
            DetectionVisualRegistryValidationError("registry invalid", usage_event=failure_event)
        ),
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda _client, event: persisted.append(event),
    )

    with pytest.raises(DetectionVisualRegistryValidationError, match="registry invalid"):
        process_uploaded_rfq(
            file_name="drawing.pdf", file_bytes=b"pdf", company_id="001",
        )

    assert persisted == [failure_event]
