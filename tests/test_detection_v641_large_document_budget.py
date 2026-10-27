from __future__ import annotations

from agents.anthropic_adapter import (
    _v641_reindex_batch_discovery_payload,
    _v641_validate_batch_page_coverage,
    build_detection_v641_full_page_discovery_batches,
    build_detection_registry_content_blocks,
    select_detection_v641_review_page_context_images,
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


def test_v641_review_keeps_all_view_crops_before_page_contexts() -> None:
    contexts, audit = select_detection_v641_review_page_context_images(
        view_crops=[{"group_id": f"V{index}"} for index in range(92)],
        page_context_images=[{"page_number": index} for index in range(22)],
    )

    assert contexts == []
    assert audit["contexts_suppressed"] is True
    assert audit["view_crop_count"] == 92
