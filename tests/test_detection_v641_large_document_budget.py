from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agents.anthropic_adapter import (
    _v644_validate_batch_core_geometry,
    _v641_reindex_batch_discovery_payload,
    _v641_validate_batch_page_coverage,
    _v8411_discovery_recovery_pages,
    _v8411_replace_discovery_pages,
    build_detection_v641_full_page_discovery_batches,
    build_detection_registry_content_blocks,
    run_detection_v845_global_batched_assembly_scope,
    select_detection_v641_discovery_overflow_target,
    select_detection_v641_review_page_context_images,
    should_use_detection_v845_global_batched_assembly_scope,
    should_use_detection_v641_budgeted_discovery,
)


def test_v641_batches_keep_every_full_page_once() -> None:
    # Invalid bytes use the deliberately conservative byte fallback.  The test
    # exercises transport partitioning, not JPEG decoding.
    batches, full_estimate = build_detection_v641_full_page_discovery_batches(
        page_images=[b"a" * 1_000, b"b" * 1_000, b"c" * 1_000],
        source_facts=[
            {"page_number": 1, "text": "A" * 100},
            {"page_number": 3, "text": "B" * 100},
        ],
        target_tokens=11_000,
    )

    assert [page for batch in batches for page in batch["page_numbers"]] == [1, 2, 3]
    assert full_estimate > 10_000
    assert all(batch["estimated_tokens"] >= 10_000 for batch in batches)


def test_v641_batch_reindex_preserves_absolute_page_coverage() -> None:
    payload = {
        "visual_groups": [
            {"group_id": "V1", "page_number": 7},
            {"group_id": "V2", "page_number": 8},
        ],
        "classifications": [
            {"group_id": "V1", "evidence_class": "object_evidence"},
            {"group_id": "V2", "evidence_class": "object_evidence"},
        ],
        "candidate_region_exceptions": [],
        "page_coverage": [
            {"page_number": 7, "visual_group_ids": ["V1"]},
            {"page_number": 8, "visual_group_ids": ["V2"]},
        ],
    }

    _v641_validate_batch_page_coverage(payload, expected_pages=[7, 8])
    result = _v641_reindex_batch_discovery_payload(payload, batch_number=2)

    assert [group["group_id"] for group in result["visual_groups"]] == [
        "v641-b02-001", "v641-b02-002",
    ]
    assert result["page_coverage"] == [
        {"page_number": 7, "visual_group_ids": ["v641-b02-001"]},
        {"page_number": 8, "visual_group_ids": ["v641-b02-002"]},
    ]


def test_v644_reconciles_valid_core_that_escapes_its_batch_envelope() -> None:
    payload = {
        "visual_groups": [{
            "group_id": "V1",
            "page_number": 7,
            "bbox": {
                "top_left_x": 100, "top_left_y": 100,
                "bottom_right_x": 300, "bottom_right_y": 300,
            },
            "core_bbox": {
                "top_left_x": 90, "top_left_y": 110,
                "bottom_right_x": 250, "bottom_right_y": 250,
            },
        }],
    }

    repairs = _v644_validate_batch_core_geometry(payload)

    assert payload["visual_groups"][0]["bbox"] == {
        "top_left_x": 100, "top_left_y": 100,
        "bottom_right_x": 300, "bottom_right_y": 300,
    }
    assert payload["visual_groups"][0]["core_bbox"] == payload["visual_groups"][0]["bbox"]
    assert repairs == [{
        "group_id": "V1",
        "reason": "valid_core_bbox_escaped_valid_evidence_bbox",
        "original_core_bbox": {
            "top_left_x": 90, "top_left_y": 110,
            "bottom_right_x": 250, "bottom_right_y": 250,
        },
        "bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 300, "bottom_right_y": 300,
        },
        "fallback_core_bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 300, "bottom_right_y": 300,
        },
    }]


def test_v644_still_rejects_structurally_invalid_core_geometry() -> None:
    payload = {
        "visual_groups": [{
            "group_id": "V1",
            "page_number": 7,
            "bbox": {
                "top_left_x": 100, "top_left_y": 100,
                "bottom_right_x": 300, "bottom_right_y": 300,
            },
            "core_bbox": {
                "top_left_x": 200, "top_left_y": 200,
                "bottom_right_x": 200, "bottom_right_y": 250,
            },
        }],
    }

    with pytest.raises(ValueError, match="V1.*has no positive area"):
        _v644_validate_batch_core_geometry(payload)


def test_registry_blocks_keep_supplied_page_numbers() -> None:
    blocks = build_detection_registry_content_blocks(
        file_name="large.pdf",
        file_bytes=b"pdf",
        user_text="context",
        page_images=[b"image-7", b"image-8"],
        page_image_numbers=[7, 8],
        regions=[],
    )

    assert blocks[0] == {"type": "text", "text": "PDF page 7"}
    assert blocks[2] == {"type": "text", "text": "PDF page 8"}


def test_v641_covers_both_existing_ordinary_registry_categories() -> None:
    for category in ("ordinary_object_set", "assembly_set"):
        assert should_use_detection_v641_budgeted_discovery(
            document_category=category,
            mistral_anchor_admission_active=False,
            full_estimated_input_tokens=150_001,
        )
    assert not should_use_detection_v641_budgeted_discovery(
        document_category="ada_sparse_multi_object",
        mistral_anchor_admission_active=True,
        full_estimated_input_tokens=300_000,
    )


def test_v641_assembled_request_budget_overrides_an_underestimated_page_plan():
    assert select_detection_v641_discovery_overflow_target(
        full_page_estimate=101_703,
        complete_estimate=145_000,
        exact_input_tokens=182_933,
    ) == 58_375

    assert select_detection_v641_discovery_overflow_target(
        full_page_estimate=123_971,
        complete_estimate=158_000,
        exact_input_tokens=125_071,
    ) is None

    assert select_detection_v641_discovery_overflow_target(
        full_page_estimate=101_703,
        complete_estimate=165_000,
        exact_input_tokens=None,
    ) == 64_720


def test_v845_scope_runs_only_for_a_batched_non_anchor_assembly_set() -> None:
    assert should_use_detection_v845_global_batched_assembly_scope(
        document_category="assembly_set",
        v641_budgeted_discovery_active=True,
        mistral_anchor_admission_active=False,
    )
    for category, batched, anchor in (
        ("ordinary_object_set", True, False),
        ("assembly_set", False, False),
        ("assembly_set", True, True),
    ):
        assert not should_use_detection_v845_global_batched_assembly_scope(
            document_category=category,
            v641_budgeted_discovery_active=batched,
            mistral_anchor_admission_active=anchor,
        )


def test_v845_scope_uses_complete_fixed_inventory_and_fails_closed() -> None:
    groups = [
        {
            "group_id": "v641-b01-001", "page_number": 1,
            "evidence_class": "object_evidence", "representation_kind": "elevation",
            "visual_description": "Kitchen overview elevation.",
            "bbox": {"top_left_x": 0, "top_left_y": 0,
                     "bottom_right_x": 100, "bottom_right_y": 100},
        },
        {
            "group_id": "v641-b02-001", "page_number": 2,
            "evidence_class": "object_evidence", "representation_kind": "section",
            "visual_description": "Kitchen carcass section.",
            "bbox": {"top_left_x": 0, "top_left_y": 0,
                     "bottom_right_x": 100, "bottom_right_y": 100},
        },
    ]
    crops = [
        {"group_id": group["group_id"], "page_number": group["page_number"], "bytes": b"crop"}
        for group in groups
    ]
    scope = {
        "classification": "assembly_set_candidate",
        "root_group_ids": ["v641-b01-001"],
        "witnesses": [{
            "kind": "overview_detail_hierarchy",
            "group_ids": ["v641-b01-001", "v641-b02-001"],
            "observation": "The section details the cited kitchen overview.",
        }],
    }
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(scope))],
        usage=SimpleNamespace(input_tokens=12, output_tokens=8),
        model="claude-haiku-4-5-20251001",
    )
    diagnostics = {
        "request_started_at": "2026-11-01T00:00:00+00:00",
        "request_finished_at": "2026-11-01T00:00:01+00:00",
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(response, diagnostics),
        ) as request,
    ):
        raw_scope, decision, error, audit = run_detection_v845_global_batched_assembly_scope(
            model="claude-haiku-4-5-20251001",
            visual_groups=groups,
            source_facts=[],
            view_crops=crops,
        )

    assert raw_scope == scope
    assert error is None
    assert decision is not None
    assert decision["decision"] == "assembly_set_candidate"
    assert audit["status"] == "confirmed"
    assert request.call_count == 1
    request_content = request.call_args.kwargs["messages"][0]["content"]
    assert all("full-page context" not in block.get("text", "") for block in request_content)

    invalid_scope = {
        **scope,
        "witnesses": [{
            **scope["witnesses"][0],
            "group_ids": ["v641-b01-001", "unknown"],
        }],
    }
    invalid_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text=json.dumps(invalid_scope))],
        usage=SimpleNamespace(input_tokens=12, output_tokens=8),
        model="claude-haiku-4-5-20251001",
    )
    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(invalid_response, diagnostics),
        ),
    ):
        raw_scope, decision, error, audit = run_detection_v845_global_batched_assembly_scope(
            model="claude-haiku-4-5-20251001",
            visual_groups=groups,
            source_facts=[],
            view_crops=crops,
        )

    assert raw_scope is None
    assert decision is None
    assert error == "V6.11 document scope witness references an unknown group"
    assert audit["status"] == "invalid"


def test_v641_review_keeps_all_view_crops_before_page_contexts() -> None:
    contexts, audit = select_detection_v641_review_page_context_images(
        view_crops=[{"group_id": f"V{index}"} for index in range(92)],
        page_context_images=[{"page_number": index} for index in range(22)],
    )

    assert contexts == []
    assert audit["contexts_suppressed"] is True
    assert audit["view_crop_count"] == 92


def test_discovery_coverage_recovers_graphic_pages_without_technical_islands():
    bbox = {"top_left_x": 5, "top_left_y": 5, "bottom_right_x": 30, "bottom_right_y": 30}
    groups = [
        {"group_id": "overview", "page_number": 1, "representation_kind": "floor_plan", "bbox": bbox},
        {"group_id": "render", "page_number": 2, "representation_kind": "presentation_render", "bbox": bbox},
        {"group_id": "technical", "page_number": 4, "representation_kind": "elevation", "bbox": bbox},
    ]
    payload = {
        "visual_groups": groups,
        "classifications": [
            {"group_id": "overview", "evidence_class": "document_context"},
            {"group_id": "render", "evidence_class": "object_evidence"},
            {"group_id": "technical", "evidence_class": "object_evidence"},
        ],
        "candidate_region_exceptions": [
            {"candidate_region_id": "C3-0", "reason": "Previous interpretation"},
            {"candidate_region_id": "C4-0", "reason": "Keep this exception"},
        ],
        "page_coverage": [
            {"page_number": page, "visual_group_ids": [
                row["group_id"] for row in groups if row["page_number"] == page
            ]} for page in range(1, 5)
        ],
    }
    candidates = [
        {"candidate_region_id": f"C{page}-{index}", "page_number": page,
         "basis": "mistral_graphic_region", "bbox": bbox}
        for page, count in enumerate([1, 2, 1, 1], start=1)
        for index in range(count)
    ]
    assert _v8411_discovery_recovery_pages(
        payload, candidate_regions=candidates, truncated_pages={2, 3},
    ) == [2, 3]
    recovered = {
        "visual_groups": [{"group_id": "new", "page_number": 3}],
        "classifications": [{"group_id": "new", "evidence_class": "object_evidence"}],
        "candidate_region_exceptions": [],
        "page_coverage": [{"page_number": 3, "visual_group_ids": ["new"]}],
    }
    _v8411_replace_discovery_pages(payload, recovered, pages={3}, candidate_regions=candidates)
    _v641_validate_batch_page_coverage(payload, expected_pages=[1, 2, 3, 4])
    assert [group["group_id"] for group in payload["visual_groups"]] == [
        "overview", "render", "new", "technical",
    ]
    assert payload["candidate_region_exceptions"] == [
        {"candidate_region_id": "C4-0", "reason": "Keep this exception"},
    ]
