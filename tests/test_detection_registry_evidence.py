import pytest
from unittest.mock import patch
from io import BytesIO

from PIL import Image

from agents.detection_agent import (
    DEFAULT_CLAUDE_DETECTION_V4_MODEL,
    _build_v621_naming_source_crops,
    _compile_confirmed_assembly_set_registry,
    _enforce_shared_track_door_system_quantity,
    _build_v619_naming_annotated_pages,
    _merge_registry_evidence,
    _record_locked_evidence_handoff_audit,
    _registry_to_detection_result,
    run_detection_agent,
)
from agents.anthropic_adapter import DetectionVisualRegistryValidationError
from agents.schemas.detection_schema import validate_detection_result
from use_cases.rfq_processing import (
    _persist_detection_audit_before_file_review,
    process_uploaded_rfq,
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


def test_registry_metadata_fallback_marks_only_that_graph_package_for_review():
    result = {
        "detected_objects": [{
            "object_id": "object-001", "review_required": False,
            "quantity": 3, "quantity_explicit": True,
            "evidence_page_refs": [],
        }],
    }
    registry = {"objects": [{
        "object_id": "object-001", "quantity": 1,
        "quantity_explicit": False, "estimation_evidence_pages": [1],
    }]}

    merged = _merge_registry_evidence(
        result,
        registry,
        review_required_object_ids={"object-001"},
    )

    assert merged["detected_objects"][0]["quantity"] == 1
    assert merged["detected_objects"][0]["review_required"] is True


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
        "fallback_review_required_object_ids": [],
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


def test_registry_only_result_materializes_every_registry_package_without_handoff():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1, 2, 3, 4, 5],
        "visual_group_ids": ["view-001"], "visual_identity": "one kitchen",
        "boundary_basis": "one integrated kitchen package",
    }]}
    result = _registry_to_detection_result(
        registry, company_id="001", file_name="kitchen.pdf", page_count=5,
    )

    assert result["detected_objects"][0]["evidence_pages"] == "1,2,3,4,5"
    assert result["detected_objects"][0]["evidence_page_refs"] == [
        {"page_number": page, "source_label": f"P{page}", "regions": []}
        for page in range(1, 6)
    ]
    assert validate_detection_result(result) == result


def test_v626_confirmed_assembly_scope_compiles_one_document_wide_evidence_package():
    registry = {"objects": [
        {
            "object_id": "object-001", "transport_label": "Door",
            "quantity": 1, "quantity_explicit": False,
            "identity_pages": [1], "estimation_evidence_pages": [1, 2],
            "visual_group_ids": ["overview", "door-detail"],
            "visual_identity": "door views", "boundary_basis": "proof graph",
        },
        {
            "object_id": "object-002", "transport_label": "Shelving",
            "quantity": 1, "quantity_explicit": False,
            "identity_pages": [5], "estimation_evidence_pages": [5, 6],
            "visual_group_ids": ["cabinet", "shelf-detail"],
            "visual_identity": "shelving views", "boundary_basis": "proof graph",
        },
    ]}
    visual_map = {"_registry_owned_evidence": [
        {"group_id": "overview", "page_number": 1},
        {"group_id": "door-detail", "page_number": 2},
        {"group_id": "cabinet", "page_number": 5},
        {"group_id": "shelf-detail", "page_number": 6},
    ]}
    scope = {
        "decision": "assembly_set_candidate",
        "root_group_ids": ["overview"],
        "witnesses": [{"kind": "overview_detail_hierarchy"}],
    }

    compiled, audit = _compile_confirmed_assembly_set_registry(
        registry, visual_map=visual_map, document_scope=scope, page_count=6,
    )

    assert audit["applied"] is True
    assert audit["retained_visual_group_ids"] == [
        "overview", "door-detail", "cabinet", "shelf-detail",
    ]
    assert compiled == {"objects": [{
        "object_id": "object-001",
        "transport_label": "Built-in joinery set",
        "quantity": 1,
        "quantity_explicit": False,
        "identity_pages": [1],
        "estimation_evidence_pages": [1, 2, 3, 4, 5, 6],
        "visual_group_ids": ["overview", "door-detail", "cabinet", "shelf-detail"],
        "visual_identity": (
            "One confirmed built-in joinery assembly set with overview "
            "and connected component evidence."
        ),
        "boundary_basis": (
            "V6.26 confirmed document scope: cited overview/root views "
            "and connected component witnesses. All Registry-owned "
            "Islands and uploaded sheets are retained for Estimation."
        ),
    }]}
    result = _registry_to_detection_result(
        compiled, company_id="001", file_name="set.pdf", page_count=6,
        visual_map=visual_map,
    )
    assert result["detected_objects"][0]["evidence_pages"] == "1,2,3,4,5,6"
    assert validate_detection_result(result) == result


def test_v626_keeps_original_registry_without_a_confirmed_scope():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}

    compiled, audit = _compile_confirmed_assembly_set_registry(
        registry,
        visual_map={"_registry_owned_evidence": [{
            "group_id": "view-001", "page_number": 1,
        }]},
        document_scope={"decision": "ordinary_object_set", "root_group_ids": []},
        page_count=1,
    )

    assert compiled is registry
    assert audit["applied"] is False
    assert audit["reason"] == "document_scope_not_confirmed"


def test_v616_registry_materializes_only_registry_owned_bbox_regions():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "N57",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one cabinet", "boundary_basis": "one envelope",
    }]}
    result = _registry_to_detection_result(
        registry, company_id="001", file_name="cabinet.pdf", page_count=1,
        visual_map={"_registry_owned_evidence": [{
            "group_id": "view-001", "page_number": 1,
            "bbox": {
                "top_left_x": 10, "top_left_y": 20,
                "bottom_right_x": 300, "bottom_right_y": 400,
            },
        }]},
    )

    assert result["detected_objects"][0]["evidence_page_refs"][0]["regions"] == [{
        "top_left_x": 10.0, "top_left_y": 20.0,
        "bottom_right_x": 300.0, "bottom_right_y": 400.0,
    }]
    assert result["detected_objects"][0]["evidence_page_refs"][0]["presentation_preview_bbox"] == {
        "top_left_x": 10.0, "top_left_y": 20.0,
        "bottom_right_x": 300.0, "bottom_right_y": 400.0,
    }


def test_registry_selects_elevation_for_preview_and_naming_source_crop():
    def page() -> bytes:
        output = BytesIO()
        Image.new("RGB", (1000, 700), "white").save(output, format="JPEG")
        return output.getvalue()

    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False,
        "estimation_evidence_pages": [1],
        "visual_group_ids": ["section", "elevation"],
    }]}
    visual_map = {"_registry_owned_evidence": [
        {"group_id": "section", "page_number": 1, "representation_kind": "section", "bbox": {
            "top_left_x": 10, "top_left_y": 10, "bottom_right_x": 900, "bottom_right_y": 600,
        }},
        {"group_id": "elevation", "page_number": 1, "representation_kind": "elevation", "bbox": {
            "top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 500,
        }},
    ]}
    ocr = {"pages": [{"page_number": 1, "dimensions": {"width": 1000, "height": 700}}]}

    result = _registry_to_detection_result(
        registry, company_id="001", file_name="cabinet.pdf", page_count=1,
        visual_map=visual_map,
    )
    preview = result["detected_objects"][0]["evidence_page_refs"][0]["presentation_preview_bbox"]
    assert preview == {
        "top_left_x": 100.0, "top_left_y": 100.0,
        "bottom_right_x": 400.0, "bottom_right_y": 500.0,
    }

    crops, audit = _build_v621_naming_source_crops(
        registry=registry, visual_map=visual_map, ocr_package=ocr, page_images=[page()],
    )
    assert crops["object-001"]["group_id"] == "elevation"
    assert crops["object-001"]["representation_kind"] == "elevation"
    assert isinstance(crops["object-001"]["bytes"], bytes)
    assert audit["selected_group_ids"] == {"object-001": "elevation"}


def test_v619_naming_uses_one_annotated_page_per_registry_island_page():
    def page() -> bytes:
        output = BytesIO()
        Image.new("RGB", (1000, 700), "white").save(output, format="JPEG")
        return output.getvalue()

    registry = {"objects": [
        {"object_id": "object-001", "visual_group_ids": ["view-001", "view-003"]},
        {"object_id": "object-002", "visual_group_ids": ["view-002"]},
    ]}
    visual_map = {"_registry_owned_evidence": [
        {"group_id": "view-001", "page_number": 1, "bbox": {
            "top_left_x": 10, "top_left_y": 20, "bottom_right_x": 210, "bottom_right_y": 220,
        }},
        {"group_id": "view-002", "page_number": 1, "bbox": {
            "top_left_x": 500, "top_left_y": 20, "bottom_right_x": 800, "bottom_right_y": 220,
        }},
        {"group_id": "view-003", "page_number": 2, "bbox": {
            "top_left_x": 20, "top_left_y": 250, "bottom_right_x": 300, "bottom_right_y": 600,
        }},
    ]}
    ocr = {"pages": [
        {"page_number": 1, "dimensions": {"width": 1000, "height": 700}},
        {"page_number": 2, "dimensions": {"width": 1000, "height": 700}},
    ]}

    pages, audit = _build_v619_naming_annotated_pages(
        registry=registry,
        visual_map=visual_map,
        ocr_package=ocr,
        page_images=[page(), page()],
    )

    assert set(pages) == {1, 2}
    assert audit["annotated_page_count"] == 2
    assert audit["overlay_view_count"] == 3
    first_page_labels = {
        item["label"] for item in audit["overlay_audit"][0]["overlays"]
    }
    assert first_page_labels == {"object-001", "object-002"}


def test_v49_routes_default_registry_to_haiku_without_evidence_handoff():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return {"visual_groups": []}, registry, {"event": "visual_registry"}

    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]) as regions_builder,
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
    ):
        result = run_detection_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf", page_images=[b"page"],
            ocr_package={"evidence": {"text_blocks": [
                {"page_number": 1, "text": "Cabinet", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                {"page_number": 1, "text": "Detail", "bbox": {"top_left_x": 400, "top_left_y": 400, "bottom_right_x": 480, "bottom_right_y": 420}},
            ]}},
        )

    assert registry_call["model"] == DEFAULT_CLAUDE_DETECTION_V4_MODEL
    assert registry_call["regions"] == []
    assert registry_call["mistral_anchor_admission"] is False
    regions_builder.assert_not_called()
    assert len(result["_agent_usage_events"]) == 1


def test_v627_scope_scout_routes_single_assembly_candidate_to_haiku_registry():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one assembly", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return {"visual_groups": []}, registry, {"event": "visual_registry"}

    def capture_scope_scout(**_kwargs):
        return (
            {
                "classification": "single_assembly_candidate",
                "evidence_pages": [1, 2],
                "rationale": "overview followed by connected details",
            },
            {"event": "scope_scout"},
        )

    two_islands_page = {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 400, "bottom_right_y": 400},
            {"top_left_x": 500, "top_left_y": 0, "bottom_right_x": 900, "bottom_right_y": 400},
        ],
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch(
            "agents.detection_agent.assess_detection_source_capability",
            return_value={"route_eligible": False, "route_reason": "ordinary", "page_count": 2},
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_v627_scope_scout",
            side_effect=capture_scope_scout,
        ),
    ):
        result = run_detection_agent(
            file_name="stair.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], ocr_package={
                "pages": [two_islands_page, two_islands_page],
                "evidence": {"text_blocks": [
                    {"page_number": 1, "text": "overview", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                    {"page_number": 2, "text": "detail", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                ]},
            },
        )

    assert registry_call["model"] == "claude-haiku-4-5-20251001"
    assert registry_call["mistral_anchor_admission"] is False
    route = result["_agent_usage_events"][1]["raw_usage"]["detection_v6_12_document_category"]
    assert route["category"] == "assembly_set"
    assert route["decision"] == "assembly_set_scope_scout"


def test_v65_routes_adda_style_registry_to_sonnet_without_static_discovery_crops():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return {"visual_groups": []}, registry, {"event": "visual_registry"}

    def capture_scope_scout(**_kwargs):
        return (
            {
                "classification": "multi_object_risk",
                "evidence_pages": [1],
                "rationale": "two independent systems are shown",
            },
            {"event": "scope_scout"},
        )

    two_islands_page = {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 400, "bottom_right_y": 400},
            {"top_left_x": 500, "top_left_y": 0, "bottom_right_x": 900, "bottom_right_y": 400},
        ],
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch(
            "agents.detection_agent.build_detection_registry_regions",
        ) as regions_builder,
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_v627_scope_scout",
            side_effect=capture_scope_scout,
        ),
    ):
        result = run_detection_agent(
            file_name="adda.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], ocr_package={
                "pages": [two_islands_page, two_islands_page],
                "evidence": {"text_blocks": [
                    {"page_number": 1, "text": "Object A", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                    {"page_number": 1, "text": "Object B", "bbox": {"top_left_x": 400, "top_left_y": 400, "bottom_right_x": 480, "bottom_right_y": 420}},
                    {"page_number": 2, "text": "Object A", "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 80, "bottom_right_y": 30}},
                    {"page_number": 2, "text": "Object B", "bbox": {"top_left_x": 400, "top_left_y": 400, "bottom_right_x": 480, "bottom_right_y": 420}},
                ]},
            },
        )

    assert registry_call["model"] == "claude-sonnet-4-6"
    assert registry_call["regions"] == []
    assert registry_call["mistral_anchor_admission"] is True
    regions_builder.assert_not_called()
    assert len(result["_agent_usage_events"]) == 2


def test_v629_sparse_native_graphics_preserve_adda_before_scope_scout():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one object", "boundary_basis": "one envelope",
    }]}
    registry_call: dict = {}

    def capture_registry(**kwargs):
        registry_call.update(kwargs)
        return {"visual_groups": []}, registry, {"event": "visual_registry"}

    two_islands_page = {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 400, "bottom_right_y": 400},
            {"top_left_x": 500, "top_left_y": 0, "bottom_right_x": 900, "bottom_right_y": 400},
        ],
    }
    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch(
            "agents.detection_agent.assess_detection_source_capability",
            return_value={
                "route_eligible": False,
                "route_reason": "ordinary",
                "page_count": 2,
                "source_fact_count": 5,
            },
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_v627_scope_scout",
            side_effect=AssertionError("sparse native graphics must not call the scope scout"),
        ),
    ):
        result = run_detection_agent(
            file_name="graphic-pack.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], ocr_package={
                "pages": [two_islands_page, two_islands_page],
                "evidence": {
                    "graphic_regions": [
                        {"source": "native_pdf_image_xobject"}
                        for _ in range(24)
                    ],
                },
            },
        )

    assert registry_call["model"] == "claude-sonnet-4-6"
    assert registry_call["mistral_anchor_admission"] is True
    route = result["_agent_usage_events"][0]["raw_usage"]["detection_v6_12_document_category"]
    assert route["decision"] == "ada_boundary_risk_sparse_native_graphics"
    assert "v6_29_sparse_native_graphics_preserve_ada" in route["reasons"]


def test_source_degraded_route_uses_v532_pairwise_structural_admission_audit_and_forces_the_base_model():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "Object 1",
        "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
        "estimation_evidence_pages": [1], "visual_group_ids": ["view-001"],
        "visual_identity": "one visual object", "boundary_basis": "one envelope",
    }]}
    source_degraded_call: dict = {}

    def capture_source_degraded(**kwargs):
        source_degraded_call.update(kwargs)
        return {"route": "v5_32", "registry": registry}, {"raw_usage": {}}

    with (
        patch("agents.detection_agent.get_secret", side_effect=lambda _name, default: default),
        patch(
            "agents.detection_agent.run_anthropic_detection_v5_source_degraded_pairwise_structural_admission_audit",
            side_effect=capture_source_degraded,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=AssertionError("ordinary V5 must not run for source-degraded input"),
        ),
    ):
        result = run_detection_agent(
            file_name="scan.png", company_id="001", file_bytes=b"image",
            page_images=[b"page"], ocr_package={"evidence": {"text_blocks": []}},
        )

    assert "post_discovery_view_crops" not in source_degraded_call
    assert "component_only_partition_repair" not in source_degraded_call
    assert source_degraded_call["model"] == DEFAULT_CLAUDE_DETECTION_V4_MODEL
    assert result["detected_objects"][0]["object_id"] == "object-001"
    assert result["_agent_usage_events"][0]["raw_usage"]["detection_v6_12_document_category"]["category"] == "source_degraded_visual"


def test_detection_audit_is_persisted_synchronously_and_must_succeed(monkeypatch):
    persisted: list[dict] = []
    event = {
        "company_id": "001", "run_id": "run-001", "file_name": "drawing.pdf",
        "agent_name": "detection", "operation": "rfq_detection_visual_registry",
        "model": "test-model", "prompt_version": "detection_v5_19",
        "status": "succeeded", "raw_usage": {"route": "source_degraded"},
    }
    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda _client, received: persisted.append(received),
    )

    _persist_detection_audit_before_file_review(
        client=object(), usage_events=[event],
    )

    assert persisted == [event]

    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("database unavailable")),
    )
    with pytest.raises(RuntimeError, match="Detection audit could not be saved"):
        _persist_detection_audit_before_file_review(
            client=object(), usage_events=[event],
        )


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
