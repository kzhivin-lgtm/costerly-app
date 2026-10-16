import io
import json
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from agents.anthropic_adapter import (
    build_detection_assembly_correspondence_content_blocks,
    run_anthropic_detection_assembly_correspondence_agent,
    run_anthropic_detection_assembly_correspondence_graph_agent,
    run_anthropic_detection_visual_registry_agent,
)
from agents.detection_page_images import build_detection_assembly_correspondence_regions
from agents.detection_agent import run_detection_agent
from agents.schemas.detection_assembly_correspondence_schema import (
    DetectionAssemblyCorrespondenceSchemaError,
    normalize_detection_assembly_candidate_ids,
    validate_detection_assembly_correspondence,
)
from agents.schemas.detection_assembly_correspondence_graph_schema import (
    derive_detection_assembly_correspondence,
    normalize_detection_assembly_graph,
    validate_detection_assembly_correspondence_graph,
)


class _Usage:
    input_tokens = 100
    output_tokens = 20


class _Response:
    usage = _Usage()


def _assembly_payload() -> dict:
    return {
        "assembly_candidates": [
            {
                "candidate_id": "assembly-001",
                "representation_ids": ["representation-001", "representation-003"],
                "visual_identity": "long low three-bay console in two views",
                "correspondence_basis": "same three-bay front and continuous low base",
            },
            {
                "candidate_id": "assembly-002",
                "representation_ids": ["representation-002", "representation-004"],
                "visual_identity": "tall separate cabinet block in two views",
                "correspondence_basis": "same tall frame and independent base",
            },
        ],
        "non_assembly_representation_ids": [],
    }


def _representation(representation_id: str, page_number: int) -> dict:
    return {
        "representation_id": representation_id,
        "page_number": page_number,
        "bbox": {"left": 0.1, "top": 0.1, "right": 0.4, "bottom": 0.6},
        "bytes": b"jpeg-bytes",
    }


def _graph_payload() -> dict:
    return {
        "representation_roles": [
            {"representation_id": "representation-001", "role": "complete_assembly", "visible_identity": "long low three-bay console"},
            {"representation_id": "representation-002", "role": "complete_assembly", "visible_identity": "tall separate cabinet"},
            {"representation_id": "representation-003", "role": "complete_assembly", "visible_identity": "long low three-bay console"},
            {"representation_id": "representation-004", "role": "complete_assembly", "visible_identity": "tall separate cabinet"},
        ],
        "pair_relations": [
            {"first_representation_id": "representation-001", "second_representation_id": "representation-002", "relation": "separate_assemblies", "basis": "independent low and tall envelopes"},
            {"first_representation_id": "representation-001", "second_representation_id": "representation-003", "relation": "same_assembly", "basis": "same three bays and continuous low base"},
            {"first_representation_id": "representation-001", "second_representation_id": "representation-004", "relation": "separate_assemblies", "basis": "different finished envelopes"},
            {"first_representation_id": "representation-002", "second_representation_id": "representation-003", "relation": "separate_assemblies", "basis": "different finished envelopes"},
            {"first_representation_id": "representation-002", "second_representation_id": "representation-004", "relation": "same_assembly", "basis": "same tall frame and independent base"},
            {"first_representation_id": "representation-003", "second_representation_id": "representation-004", "relation": "separate_assemblies", "basis": "independent low and tall envelopes"},
        ],
    }


def test_correspondence_schema_requires_an_exhaustive_non_overlapping_partition():
    payload = _assembly_payload()
    assert validate_detection_assembly_correspondence(
        payload,
        representation_ids={
            "representation-001",
            "representation-002",
            "representation-003",
            "representation-004",
        },
    ) == payload

    invalid = _assembly_payload()
    invalid["assembly_candidates"][1]["representation_ids"] = ["representation-003"]
    with pytest.raises(
        DetectionAssemblyCorrespondenceSchemaError,
        match="multiple correspondence outcomes",
    ):
        validate_detection_assembly_correspondence(
            invalid,
            representation_ids={
                "representation-001",
                "representation-002",
                "representation-003",
                "representation-004",
            },
        )


def test_correspondence_normalizes_provider_candidate_labels_without_changing_partition():
    payload = _assembly_payload()
    payload["assembly_candidates"][0]["candidate_id"] = "left_assembly"
    payload["assembly_candidates"][1]["candidate_id"] = "tall_unit"

    normalized = normalize_detection_assembly_candidate_ids(payload)

    assert [item["candidate_id"] for item in normalized["assembly_candidates"]] == [
        "assembly-001",
        "assembly-002",
    ]
    assert normalized["assembly_candidates"][0]["representation_ids"] == [
        "representation-001",
        "representation-003",
    ]


def test_pairwise_graph_derives_two_locked_candidates_from_explicit_matches():
    representation_ids = [
        "representation-001",
        "representation-002",
        "representation-003",
        "representation-004",
    ]
    graph = _graph_payload()
    graph["pair_relations"][0]["first_representation_id"] = "representation-002"
    graph["pair_relations"][0]["second_representation_id"] = "representation-001"

    validated = validate_detection_assembly_correspondence_graph(
        normalize_detection_assembly_graph(graph, representation_ids=representation_ids),
        representation_ids=representation_ids,
    )
    correspondence, status = derive_detection_assembly_correspondence(
        validated,
        representation_ids=representation_ids,
    )

    assert status == "graph_decisive"
    assert correspondence is not None
    assert [candidate["representation_ids"] for candidate in correspondence["assembly_candidates"]] == [
        ["representation-001", "representation-003"],
        ["representation-002", "representation-004"],
    ]


def test_pairwise_graph_abstains_when_any_relation_lacks_direct_evidence():
    representation_ids = [
        "representation-001",
        "representation-002",
        "representation-003",
        "representation-004",
    ]
    graph = _graph_payload()
    graph["pair_relations"][2]["relation"] = "insufficient"

    validated = validate_detection_assembly_correspondence_graph(
        graph,
        representation_ids=representation_ids,
    )
    correspondence, status = derive_detection_assembly_correspondence(
        validated,
        representation_ids=representation_ids,
    )

    assert correspondence is None
    assert status == "graph_abstained_incomplete_pairwise_evidence"


def test_correspondence_input_uses_one_masked_page_map_and_omits_file_and_ocr_context():
    first = _representation("representation-001", 1)
    first["page_map_bytes"] = b"masked-page-map"
    blocks, manifest = build_detection_assembly_correspondence_content_blocks([
        first,
        _representation("representation-002", 1),
    ])

    text = "\n".join(block["text"] for block in blocks if block["type"] == "text")
    assert [item["representation_id"] for item in manifest] == [
        "representation-001",
        "representation-002",
    ]
    assert "Adda" not in text
    assert "OCR" not in text
    assert "title block" not in text.casefold()
    assert "Masked figure-layout map" in text
    assert [block["type"] for block in blocks] == ["text", "image", "text", "image", "text", "image", "text"]


def test_correspondence_agent_records_the_isolated_stage_without_registry_context():
    captured = {}

    def fake_create(*_args, **kwargs):
        captured.update(kwargs)
        return _Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="sonnet"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_assembly_payload())),
    ):
        correspondence, usage = run_anthropic_detection_assembly_correspondence_agent(
            file_name="Adda.pdf",
            company_id="001",
            representations=[
                _representation("representation-001", 1),
                _representation("representation-002", 1),
                _representation("representation-003", 2),
                _representation("representation-004", 2),
            ],
            model=None,
        )

    request_text = "\n".join(
        block["text"]
        for block in captured["messages"][0]["content"]
        if block["type"] == "text"
    )
    assert correspondence == _assembly_payload()
    assert usage["operation"] == "rfq_detection_assembly_correspondence"
    assert usage["raw_usage"]["assembly_partition_audit"] == _assembly_payload()
    assert "Adda.pdf" not in request_text
    assert "Company ID" not in request_text


def test_graph_agent_records_graph_and_only_locks_a_decisive_partition():
    captured = {}

    def fake_create(*_args, **kwargs):
        captured.update(kwargs)
        return _Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="sonnet"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_graph_payload())),
    ):
        correspondence, usage = run_anthropic_detection_assembly_correspondence_graph_agent(
            file_name="Adda.pdf",
            company_id="001",
            representations=[
                _representation("representation-001", 1),
                _representation("representation-002", 1),
                _representation("representation-003", 2),
                _representation("representation-004", 2),
            ],
            model=None,
        )

    request_text = "\n".join(
        block["text"]
        for block in captured["messages"][0]["content"]
        if block["type"] == "text"
    )
    assert correspondence is not None
    assert [candidate["representation_ids"] for candidate in correspondence["assembly_candidates"]] == [
        ["representation-001", "representation-003"],
        ["representation-002", "representation-004"],
    ]
    assert usage["operation"] == "rfq_detection_assembly_correspondence"
    assert usage["raw_usage"]["assembly_graph_audit"] == _graph_payload()
    assert usage["raw_usage"]["assembly_partition_audit"] == correspondence
    assert usage["raw_usage"]["assembly_graph_status"] == "graph_decisive"
    assert "Adda.pdf" not in request_text
    assert "Company ID" not in request_text


def test_registry_must_keep_each_locked_assembly_candidate_in_a_separate_object():
    payload = {
        "visual_groups": [
            {
                "group_id": "left",
                "page_number": 1,
                "location_hint": "left",
                "visual_description": "long low console",
                "representation_kind": "elevation",
                "related_group_ids": [],
            },
            {
                "group_id": "right",
                "page_number": 1,
                "location_hint": "right",
                "visual_description": "tall cabinet",
                "representation_kind": "elevation",
                "related_group_ids": [],
            },
        ],
        "objects": [
            {
                "object_id": "object-001",
                "transport_label": "Object 1",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": [1],
                "visual_group_ids": ["left"],
                "visual_identity": "long low console",
                "boundary_basis": "one finished low envelope",
                "assembly_candidate_ids": ["assembly-001"],
            },
            {
                "object_id": "object-002",
                "transport_label": "Object 2",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": [1],
                "visual_group_ids": ["right"],
                "visual_identity": "tall cabinet",
                "boundary_basis": "one independent tall envelope",
                "assembly_candidate_ids": ["assembly-002"],
            },
        ],
        "page_coverage": [
            {
                "page_number": 1,
                "object_ids": ["object-001", "object-002"],
                "evidence_reason": "both assemblies are shown",
            },
        ],
    }
    correspondence = _assembly_payload()

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="haiku"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        _visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf",
            company_id="001",
            file_bytes=b"pdf",
            page_images=[b"page"],
            regions=[],
            ocr_package=None,
            model="haiku",
            assembly_correspondence=correspondence,
        )

    assert len(registry["objects"]) == 2
    assert usage["raw_usage"]["locked_assembly_candidate_count"] == 2
    assert usage["raw_usage"]["attempt_label"] == "visual_registry_with_locked_assemblies"


def test_geometry_yields_separate_crop_targets_for_two_disconnected_drawings():
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 120, 430, 560), fill="black")
    draw.rectangle((710, 120, 1050, 560), fill="black")
    output = io.BytesIO()
    image.save(output, format="JPEG")

    regions = build_detection_assembly_correspondence_regions([output.getvalue()])

    assert [region["representation_id"] for region in regions] == [
        "representation-001",
        "representation-002",
    ]
    assert {region["page_number"] for region in regions} == {1}


def test_masked_figure_crop_excludes_neighbour_ink_inside_an_overlapping_bbox():
    image = Image.new("RGB", (1200, 800), "white")
    draw = ImageDraw.Draw(image)
    # Two disconnected L-shaped figures. Their rectangular envelopes overlap,
    # but their actual ink does not. This is the Ada failure mode.
    draw.rectangle((100, 100, 200, 600), fill="black")
    draw.rectangle((200, 500, 600, 600), fill="black")
    draw.rectangle((400, 100, 1000, 200), fill="black")
    draw.rectangle((800, 200, 900, 650), fill="black")
    output = io.BytesIO()
    image.save(output, format="JPEG")

    regions = build_detection_assembly_correspondence_regions([output.getvalue()])
    left_figure = min(regions, key=lambda region: region["bbox"]["left"])
    crop = Image.open(io.BytesIO(left_figure["bytes"])).convert("L")
    source_left = max(0.0, left_figure["bbox"]["left"] - 0.025)
    source_top = max(0.0, left_figure["bbox"]["top"] - 0.025)
    x = int((500 / 1200 - source_left) / (1 - source_left - max(0.0, 1 - (left_figure["bbox"]["right"] + 0.025))) * crop.width)
    y = int((150 / 800 - source_top) / (1 - source_top - max(0.0, 1 - (left_figure["bbox"]["bottom"] + 0.025))) * crop.height)

    assert len(regions) == 2
    assert "page_map_bytes" in left_figure
    assert crop.getpixel((x, y)) > 240


def test_pairwise_graph_bypasses_large_figure_sets_without_truncation():
    image = Image.new("RGB", (1200, 800), "white")
    ImageDraw.Draw(image).rectangle((150, 120, 850, 600), fill="black")
    output = io.BytesIO()
    image.save(output, format="JPEG")

    regions = build_detection_assembly_correspondence_regions([output.getvalue()] * 13)

    assert regions == []


def test_detection_passes_the_locked_partition_to_registry_before_evidence_packing():
    correspondence = _assembly_payload()
    registry = {
        "objects": [
            {
                "object_id": "object-001",
                "transport_label": "Object 1",
                "quantity": 1,
                "quantity_explicit": False,
                "identity_pages": [1],
                "estimation_evidence_pages": [1],
                "visual_group_ids": ["view-001"],
                "visual_identity": "one console",
                "boundary_basis": "one finished envelope",
            },
        ],
    }
    captured = {}

    def capture_registry(**kwargs):
        captured.update(kwargs)
        return {"visual_groups": []}, registry, {"event": "visual-registry"}

    def stop_after_evidence_packer(**kwargs):
        captured["evidence_packer"] = kwargs
        raise RuntimeError("stop after evidence packer input")

    with (
        patch(
            "agents.detection_agent.build_detection_assembly_correspondence_regions",
            return_value=[_representation("representation-001", 1)],
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_assembly_correspondence_graph_agent",
            return_value=(correspondence, {"event": "correspondence"}),
        ),
        patch("agents.detection_agent.build_detection_registry_regions", return_value=[]),
        patch(
            "agents.detection_agent.run_anthropic_detection_visual_registry_agent",
            side_effect=capture_registry,
        ),
        patch(
            "agents.detection_agent.run_anthropic_detection_agent_with_fallback",
            side_effect=stop_after_evidence_packer,
        ),
        pytest.raises(RuntimeError, match="stop after evidence packer input"),
    ):
        run_detection_agent(
            file_name="drawing.pdf",
            company_id="001",
            file_bytes=b"pdf",
            page_images=[b"page"],
        )

    assert captured["assembly_correspondence"] == correspondence
    assert captured["evidence_packer"]["page_image_numbers"] == [1]
