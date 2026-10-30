import json

import pytest
import agents.anthropic_adapter as anthropic_adapter

from agents.anthropic_adapter import (
    apply_detection_v67_mistral_anchor_admission,
    build_detection_v69_reconciliation_matrix,
    build_detection_v68_pairwise_membership_matrix,
    build_detection_candidate_region_audit,
    build_detection_view_evidence_packages,
    normalize_detection_v69_pair_criteria_decisions,
    normalize_detection_v69_preliminary_links,
    normalize_detection_v69_reconciliation_decisions,
    normalize_detection_v610_evidence_review_decisions,
    normalize_detection_v68_pairwise_decisions,
)
from agents.detection_fusion_candidate_regions import (
    build_detection_fusion_candidate_regions,
    select_detection_candidate_graph_seeds,
)
from agents.detection_conflict_resolver import (
    apply_detection_conflict_admissions,
    build_detection_conflict_targets,
    demote_detection_conflict_full_page_plan,
    translate_detection_conflict_crop_decisions,
    validate_detection_conflict_decisions,
)


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


def test_fusion_adds_uncovered_native_pdf_cluster_beside_mistral_graphic_region():
    facts = [
        {"fact_id": "SF-IN", "page_number": 1, "source": "native_pdf_text", "text": "600", "bbox": {
            "top_left_x": 400, "top_left_y": 200,
            "bottom_right_x": 410, "bottom_right_y": 210,
        }},
        {"fact_id": "SF-OUT-1", "page_number": 1, "source": "native_pdf_text", "text": "600", "bbox": {
            "top_left_x": 1100, "top_left_y": 300,
            "bottom_right_x": 1110, "bottom_right_y": 310,
        }},
        {"fact_id": "SF-OUT-2", "page_number": 1, "source": "native_pdf_text", "text": "800", "bbox": {
            "top_left_x": 1300, "top_left_y": 300,
            "bottom_right_x": 1310, "bottom_right_y": 310,
        }},
        {"fact_id": "SF-OCR-ONLY", "page_number": 1, "source": "mistral_ocr", "bbox": {
            "top_left_x": 1500, "top_left_y": 300,
            "bottom_right_x": 1510, "bottom_right_y": 310,
        }},
        *[
            {"fact_id": f"SF-REV-{value}", "page_number": 1, "source": "native_pdf_text",
             "text": str(value), "bbox": {
                 "top_left_x": 100 + value * 20, "top_left_y": 1100,
                 "bottom_right_x": 110 + value * 20, "bottom_right_y": 1110,
             }}
            for value in range(1, 11)
        ],
        {"fact_id": "SF-TITLE-TEXT", "page_number": 1, "source": "native_pdf_text", "text": "PROJECT",
         "bbox": {"top_left_x": 100, "top_left_y": 1600, "bottom_right_x": 110, "bottom_right_y": 1610}},
        {"fact_id": "SF-TITLE-NUMBER", "page_number": 1, "source": "native_pdf_text", "text": "607",
         "bbox": {"top_left_x": 300, "top_left_y": 1600, "bottom_right_x": 310, "bottom_right_y": 1610}},
    ]

    candidates = build_detection_fusion_candidate_regions(_ocr_with_graphic_region(), facts)

    assert [(row["candidate_region_id"], row["basis"], row["source_fact_ids"])
            for row in candidates] == [
        ("CR-P001-001", "mistral_graphic_region", ["SF-IN"]),
        ("CR-P001-002", "fusion_text_cluster", ["SF-OUT-1", "SF-OUT-2"]),
    ]
    assert candidates[1]["role"] == "coverage_only"
    assert select_detection_candidate_graph_seeds(candidates) == [candidates[0]]


def test_v68_small_anchor_route_builds_complete_pair_matrix_only_through_ten_islands():
    groups = [
        {"group_id": f"view-{index:03d}", "evidence_class": "object_evidence"}
        for index in range(1, 11)
    ]

    pairs = build_detection_v68_pairwise_membership_matrix(groups)

    assert len(pairs) == 45
    assert pairs[0] == ("view-001", "view-002")
    assert pairs[-1] == ("view-009", "view-010")
    assert build_detection_v68_pairwise_membership_matrix(groups + [{
        "group_id": "view-011", "evidence_class": "object_evidence",
    }]) == []


def test_v68_pairwise_normalizer_requires_full_coverage_and_keeps_only_positive_facts():
    expected_pairs = [("raw-a", "raw-b"), ("raw-a", "raw-c"), ("raw-b", "raw-c")]
    decisions = [
        {
            "group_id_a": "raw-a", "group_id_b": "raw-b",
            "disposition": "same_object", "reason": "Unique matching return profile.",
            "evidence": [{
                "evidence_type": "unique_geometry", "strength": "standard",
                "observation": "The same uncommon return profile appears in both views.",
                "source_fact_ids": [],
            }, {
                "evidence_type": "matching_topology", "strength": "standard",
                "observation": "The same three-bay arrangement appears in both views.",
                "source_fact_ids": [],
            }],
        },
        {
            "group_id_a": "raw-a", "group_id_b": "raw-c",
            "disposition": "different_objects", "reason": "Different cabinet layouts.",
            "evidence": [],
        },
        {
            "group_id_a": "raw-b", "group_id_b": "raw-c",
            "disposition": "insufficient_evidence", "reason": "No reliable relation is visible.",
            "evidence": [],
        },
    ]

    facts, audit = normalize_detection_v68_pairwise_decisions(
        decisions, expected_pairs=expected_pairs,
        group_id_mapping={"raw-a": "view-001", "raw-b": "view-002", "raw-c": "view-003"},
    )

    assert {(fact["group_id_a"], fact["group_id_b"]) for fact in facts} == {
        ("view-001", "view-002"),
    }
    assert len(facts) == 2
    assert [row["disposition"] for row in audit] == [
        "same_object", "different_objects", "insufficient_evidence",
    ]


def _v69_criteria(*, topology: str, geometry: str, disposition: str = "same_object") -> list[dict]:
    return [
        {"criterion": "identifier", "assessment": "not_visible", "observation": "No literal object-specific identifier is visible in both views."},
        {"criterion": "topology", "assessment": topology, "observation": "The three-bay arrangement is visible in both compared views."},
        {"criterion": "geometry", "assessment": geometry, "observation": "The uncommon L-shaped return is visible in both compared views."},
        {"criterion": "dimensions", "assessment": "not_visible", "observation": "A second complete dimensional reading is not visible in this pair."},
        {"criterion": "construction", "assessment": "not_visible", "observation": "No separate physical continuity witness is visible for this pair."},
    ]


def _v69_evidence() -> list[dict]:
    return [{
        "evidence_type": "matching_topology", "strength": "standard",
        "observation": "Both views show the same three-bay arrangement ending at an L return.",
        "source_fact_ids": [],
    }, {
        "evidence_type": "unique_geometry", "strength": "standard",
        "observation": "Both views show the same uncommon L-shaped 1830 by 1188 return.",
        "source_fact_ids": [],
    }]


def test_v69_requires_all_criteria_before_a_preliminary_link_can_be_strong():
    facts, audit = normalize_detection_v69_pair_criteria_decisions([{
        "group_id_a": "a", "group_id_b": "b", "disposition": "same_object",
        "reason": "Two independent structural correspondences are visible.",
        "criteria": _v69_criteria(topology="supports_same_object", geometry="supports_same_object"),
        "evidence": _v69_evidence(),
    }], expected_pairs=[("a", "b")])

    assert len(facts) == 2
    assert audit[0]["computed_strength"] == "strong"

    with pytest.raises(ValueError, match="criteria"):
        normalize_detection_v69_pair_criteria_decisions([{
            "group_id_a": "a", "group_id_b": "b", "disposition": "same_object",
            "reason": "An incomplete evidence card cannot establish identity.",
            "criteria": _v69_criteria(topology="supports_same_object", geometry="not_visible")[:-1],
            "evidence": _v69_evidence(),
        }], expected_pairs=[("a", "b")])


def test_v69_allows_no_preliminary_links_instead_of_forcing_a_hallucinated_pair():
    assert normalize_detection_v69_preliminary_links([]) == []


def test_v610_combined_review_keeps_trigger_and_requires_complete_criteria():
    pairs, facts, audit = normalize_detection_v610_evidence_review_decisions([{
        "group_id_a": "left", "group_id_b": "right",
        "trigger_criterion": "geometry",
        "disposition": "same_object",
        "reason": "Two independent structural correspondences are visible.",
        "criteria": {
            "identifier": "not_visible",
            "topology": "supports_same_object",
            "geometry": "supports_same_object",
            "dimensions": "not_visible",
            "construction": "not_visible",
        },
        "evidence": _v69_evidence(),
    }], allowed_group_ids={"left", "right"})

    assert pairs == [("left", "right")]
    assert len(facts) == 2
    assert audit[0]["trigger_criterion"] == "geometry"
    assert audit[0]["computed_strength"] == "strong"

    with pytest.raises(ValueError, match="pair"):
        normalize_detection_v610_evidence_review_decisions([{
            "group_id_a": "left", "group_id_b": "unknown",
            "trigger_criterion": "geometry",
            "disposition": "same_object",
            "reason": "Two independent structural correspondences are visible.",
            "criteria": {
                "identifier": "not_visible",
                "topology": "supports_same_object",
                "geometry": "supports_same_object",
                "dimensions": "not_visible",
                "construction": "not_visible",
            },
            "evidence": _v69_evidence(),
        }], allowed_group_ids={"left", "right"})


def test_v610_allows_no_candidate_links_without_forcing_a_hallucinated_pair():
    pairs, facts, audit = normalize_detection_v610_evidence_review_decisions(
        [], allowed_group_ids={"left", "right"},
    )

    assert (pairs, facts, audit) == ([], [], [])


def test_v69_reconciles_every_unproven_island_against_each_proven_component():
    matrix, components = build_detection_v69_reconciliation_matrix(
        group_ids={"p1a", "p1b", "counter2", "counter3", "counter4", "l2", "l3", "l4"},
        criteria_audit=[
            {"group_id_a": "counter2", "group_id_b": "counter3", "disposition": "same_object", "computed_strength": "strong"},
            {"group_id_a": "counter3", "group_id_b": "counter4", "disposition": "same_object", "computed_strength": "strong"},
            {"group_id_a": "l2", "group_id_b": "l3", "disposition": "same_object", "computed_strength": "strong"},
            {"group_id_a": "l3", "group_id_b": "l4", "disposition": "same_object", "computed_strength": "strong"},
            {"group_id_a": "p1a", "group_id_b": "p1b", "disposition": "same_object", "computed_strength": "weak"},
        ],
    )

    assert sorted(components.values()) == [
        ["counter2", "counter3", "counter4"], ["l2", "l3", "l4"],
    ]
    assert {(row["candidate_group_id"], row["reference_component_id"]) for row in matrix} == {
        ("p1a", "RC001"), ("p1a", "RC002"), ("p1b", "RC001"), ("p1b", "RC002"),
    }

    facts, audit = normalize_detection_v69_reconciliation_decisions([{
        "candidate_group_id": "p1a", "reference_component_id": "RC002", "comparison_group_id": "l2",
        "disposition": "same_object", "reason": "The candidate matches the L-shaped component on two independent criteria.",
        "criteria": _v69_criteria(topology="supports_same_object", geometry="supports_same_object"),
        "evidence": _v69_evidence(),
    }], expected_matrix=[{"candidate_group_id": "p1a", "reference_component_id": "RC002"}],
       components=components)

    assert {(fact["group_id_a"], fact["group_id_b"]) for fact in facts} == {("l2", "p1a")}
    assert audit[0]["computed_strength"] == "strong"


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


def test_v75_conflict_targets_ignore_exception_and_require_visual_resolution():
    candidates = [
        {
            "candidate_region_id": "CR-P010-003", "page_number": 10,
            "role": "coverage_only", "basis": "fusion_text_cluster",
            "bbox": {"top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 400},
        },
        {
            "candidate_region_id": "CR-P011-002", "page_number": 11,
            "basis": "mistral_graphic_region",
            "bbox": {"top_left_x": 500, "top_left_y": 100, "bottom_right_x": 900, "bottom_right_y": 400},
        },
        {
            "candidate_region_id": "CR-P012-001", "page_number": 12,
            "basis": "mistral_graphic_region",
            "bbox": {"top_left_x": 100, "top_left_y": 500, "bottom_right_x": 400, "bottom_right_y": 900},
        },
    ]
    groups = [
        {
            "group_id": "VG-P011-002", "page_number": 11,
            "bbox": {"top_left_x": 500, "top_left_y": 100, "bottom_right_x": 900, "bottom_right_y": 400},
        },
        {
            "group_id": "VG-P012-001", "page_number": 12,
            "bbox": {"top_left_x": 100, "top_left_y": 500, "bottom_right_x": 400, "bottom_right_y": 900},
        },
    ]
    classifications = [
        {"group_id": "VG-P011-002", "evidence_class": "document_context"},
        {"group_id": "VG-P012-001", "evidence_class": "object_evidence"},
    ]

    assert build_detection_conflict_targets(
        candidate_regions=candidates, visual_groups=groups, classifications=classifications,
    ) == [
        {
            "target_id": "V75-C001", "page_number": 10,
            "bbox": {"top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 400},
            "trigger": "coverage_only_without_object_evidence",
            "candidate_region_ids": ["CR-P010-003"],
        },
        {
            "target_id": "V75-C002", "page_number": 11,
            "bbox": {"top_left_x": 500, "top_left_y": 100, "bottom_right_x": 900, "bottom_right_y": 400},
            "trigger": "graphic_region_without_object_evidence",
            "candidate_region_ids": ["CR-P011-002"],
        },
    ]


def test_v75_admission_is_visual_geometry_not_candidate_proxy():
    targets = [{
        "target_id": "V75-C001", "page_number": 10,
        "bbox": {"top_left_x": 100, "top_left_y": 100, "bottom_right_x": 400, "bottom_right_y": 400},
        "trigger": "coverage_only_without_object_evidence",
        "candidate_region_ids": ["CR-P010-003"],
    }]
    decisions = validate_detection_conflict_decisions(
        decisions=[{
            "target_id": "V75-C001", "disposition": "admit_object_evidence",
            "visual_witness": "A framed elevation with attached dimensions is visible.",
            "representation_kind": "elevation",
            "bbox": {"top_left_x": 120, "top_left_y": 120, "bottom_right_x": 360, "bottom_right_y": 360},
            "core_bbox": {"top_left_x": 140, "top_left_y": 140, "bottom_right_x": 340, "bottom_right_y": 340},
        }],
        targets=targets,
        page_frames={10: {"fusion_dimensions": {"width": 1000, "height": 1000}}},
    )
    payload, audit = apply_detection_conflict_admissions(
        payload={"visual_groups": [], "classifications": [], "candidate_region_exceptions": []},
        targets=targets,
        decisions=decisions,
    )

    assert payload["visual_groups"][0]["group_id"] == "v75-conflict-001"
    assert payload["visual_groups"][0]["bbox"] != targets[0]["bbox"]
    assert payload["classifications"] == [{
        "group_id": "v75-conflict-001",
        "evidence_class": "object_evidence",
        "classification_reason": "A framed elevation with attached dimensions is visible.",
    }]
    assert audit[0]["candidate_region_ids"] == ["CR-P010-003"]


def test_v75_translates_hidden_crop_coordinates_into_fusion_frame():
    decisions = translate_detection_conflict_crop_decisions(
        decisions=[{
            "target_id": "V75-C001", "disposition": "admit_object_evidence",
            "visual_witness": "A dimensioned elevation is visible.",
            "representation_kind": "elevation",
            "bbox": {"top_left_x": 100, "top_left_y": 50, "bottom_right_x": 300, "bottom_right_y": 150},
            "core_bbox": {"top_left_x": 120, "top_left_y": 70, "bottom_right_x": 280, "bottom_right_y": 130},
        }],
        crop_frames={"V75-C001": {
            "page_number": 10,
            "crop_dimensions": {"width": 400, "height": 200},
            "review_crop_bbox": {"top_left_x": 200, "top_left_y": 100, "bottom_right_x": 1000, "bottom_right_y": 500},
        }},
        page_frames={10: {"scale_x": 2.0, "scale_y": 2.0}},
    )

    assert decisions[0]["bbox"] == {
        "top_left_x": 200, "top_left_y": 100,
        "bottom_right_x": 400, "bottom_right_y": 200,
    }
    assert decisions[0]["core_bbox"] == {
        "top_left_x": 220, "top_left_y": 120,
        "bottom_right_x": 380, "bottom_right_y": 180,
    }


def test_v75_full_page_floor_plan_is_document_context_but_bounded_plan_is_not():
    target = {
        "target_id": "V75-C001", "page_number": 1,
        "bbox": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 1000, "bottom_right_y": 1000},
    }
    decision = {
        "target_id": "V75-C001", "disposition": "admit_object_evidence",
        "visual_witness": "A floor plan is visible.", "representation_kind": "floor_plan",
        "bbox": target["bbox"], "core_bbox": target["bbox"],
    }
    page_frames = {1: {"fusion_dimensions": {"width": 1000, "height": 1000}}}

    assert demote_detection_conflict_full_page_plan(
        decision=decision, target=target, page_frames=page_frames,
    )["disposition"] == "document_context"

    bounded_target = {**target, "bbox": {
        "top_left_x": 100, "top_left_y": 100, "bottom_right_x": 500, "bottom_right_y": 500,
    }}
    bounded_decision = {**decision, "bbox": bounded_target["bbox"], "core_bbox": bounded_target["bbox"]}
    assert demote_detection_conflict_full_page_plan(
        decision=bounded_decision, target=bounded_target, page_frames=page_frames,
    )["disposition"] == "admit_object_evidence"


def test_v75_invalid_target_does_not_discard_other_valid_batch_decisions(monkeypatch):
    targets = [
        {
            "target_id": "V75-C001", "page_number": 1,
            "bbox": {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 50, "bottom_right_y": 50},
            "trigger": "graphic_region_without_object_evidence",
            "candidate_region_ids": ["CR-P001-001"],
        },
        {
            "target_id": "V75-C002", "page_number": 1,
            "bbox": {"top_left_x": 60, "top_left_y": 10, "bottom_right_x": 100, "bottom_right_y": 50},
            "trigger": "graphic_region_without_object_evidence",
            "candidate_region_ids": ["CR-P001-002"],
        },
    ]
    provider_payloads = [
        {"decisions": [{
            "target_id": "V75-C001", "disposition": "document_context",
            "visual_witness": "Visible title block.", "document_context_kind": "title_block",
        }]},
        {"decisions": [{
            "target_id": "V75-C002", "disposition": "unresolved",
            "visual_witness": "The pixels are too indistinct to classify.",
        }]},
    ]

    def fake_images(*, targets, **_kwargs):
        return [
            {
                "target_id": target["target_id"], "page_number": 1, "bytes": b"crop",
                "crop_dimensions": {"width": 40, "height": 40},
                "review_crop_bbox": target["bbox"],
            }
            for target in targets
        ], {1: b"context"}, []

    monkeypatch.setattr(
        anthropic_adapter, "build_detection_v75_conflict_resolver_images", fake_images,
    )
    monkeypatch.setattr(anthropic_adapter, "get_anthropic_client", lambda: object())
    monkeypatch.setattr(
        anthropic_adapter,
        "create_claude_message_streamed",
        lambda *_args, **_kwargs: ({"payload": provider_payloads.pop(0)}, {}),
    )
    monkeypatch.setattr(
        anthropic_adapter,
        "extract_text_from_claude_response",
        lambda response: json.dumps(response["payload"]),
    )
    monkeypatch.setattr(
        anthropic_adapter, "summarize_detection_provider_call", lambda **_kwargs: {},
    )

    decisions, audit = anthropic_adapter.run_detection_v75_conflict_resolver(
        page_images=[b"page"], targets=targets,
        coordinate_frames={1: {"fusion_dimensions": {"width": 100, "height": 100}}},
        model="test-model",
    )

    assert [(row["target_id"], row["disposition"]) for row in decisions] == [
        ("V75-C001", "document_context"),
        ("V75-C002", "unresolved"),
    ], audit
    assert audit["batches"][0]["retry"] is not None


def _v67_anchor_payload(*, bbox: dict, core_bbox: dict, decision: dict) -> dict:
    return {
        "visual_groups": [{
            "group_id": "VG-P001-001", "page_number": 1,
            "bbox": bbox, "core_bbox": core_bbox,
        }],
        "candidate_region_exceptions": [],
        "candidate_region_decisions": [decision],
    }


def _v67_mistral_anchor() -> dict:
    return {
        "candidate_region_id": "CR-P001-001", "page_number": 1,
        "bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 300, "bottom_right_y": 300,
        },
        "basis": "mistral_graphic_region", "source_fact_ids": ["SF-IN"],
    }


def test_v67_accept_uses_mistral_graphic_anchor_over_model_bbox():
    model_bbox = {
        "top_left_x": 20, "top_left_y": 20,
        "bottom_right_x": 380, "bottom_right_y": 380,
    }
    payload, audit = apply_detection_v67_mistral_anchor_admission(
        payload=_v67_anchor_payload(
            bbox=model_bbox, core_bbox=model_bbox,
            decision={
                "candidate_region_id": "CR-P001-001", "decision": "accept",
                "group_id": "VG-P001-001", "reason": "The Mistral region exactly encloses the single elevation.",
                "source_fact_ids": ["SF-IN"],
            },
        ),
        candidate_regions=[_v67_mistral_anchor()],
        source_facts=[{
            "fact_id": "SF-IN", "page_number": 1,
            "bbox": {"top_left_x": 150, "top_left_y": 150,
                     "bottom_right_x": 160, "bottom_right_y": 160},
        }],
    )

    assert payload["visual_groups"][0]["bbox"] == _v67_mistral_anchor()["bbox"]
    assert payload["visual_groups"][0]["core_bbox"] == _v67_mistral_anchor()["bbox"]
    assert audit[0]["status"] == "accepted_anchor"
    assert "candidate_region_decisions" not in payload


def test_v67_unsupported_expansion_falls_back_to_mistral_anchor():
    proposed_bbox = {
        "top_left_x": 80, "top_left_y": 80,
        "bottom_right_x": 480, "bottom_right_y": 320,
    }
    foreign_anchor = {
        "candidate_region_id": "CR-P001-002", "page_number": 1,
        "bbox": {
            "top_left_x": 350, "top_left_y": 100,
            "bottom_right_x": 460, "bottom_right_y": 300,
        },
        "basis": "mistral_graphic_region", "source_fact_ids": [],
    }
    raw_payload = _v67_anchor_payload(
            bbox=proposed_bbox, core_bbox=proposed_bbox,
            decision={
                "candidate_region_id": "CR-P001-001", "decision": "expand",
                "group_id": "VG-P001-001", "reason": "The outer dimension is visibly attached to the elevation.",
                "source_fact_ids": ["SF-OUT"],
            },
        )
    raw_payload["candidate_region_decisions"].append({
        "candidate_region_id": "CR-P001-002", "decision": "reject",
        "group_id": "", "reason": "This small graphic region is a non-object annotation.",
        "source_fact_ids": [],
    })
    raw_payload["candidate_region_exceptions"] = [{
        "candidate_region_id": "CR-P001-002",
        "reason": "This small graphic region is a non-object annotation.",
    }]
    payload, audit = apply_detection_v67_mistral_anchor_admission(
        payload=raw_payload,
        candidate_regions=[_v67_mistral_anchor(), foreign_anchor],
        source_facts=[{
            "fact_id": "SF-OUT", "page_number": 1,
            "bbox": {"top_left_x": 320, "top_left_y": 180,
                     "bottom_right_x": 330, "bottom_right_y": 190},
        }],
    )

    assert payload["visual_groups"][0]["bbox"] == _v67_mistral_anchor()["bbox"]
    assert audit[0]["status"] == "rejected_to_mistral_fallback"


def test_v67_source_grounded_expansion_is_admitted_without_foreign_anchor():
    proposed_bbox = {
        "top_left_x": 80, "top_left_y": 80,
        "bottom_right_x": 340, "bottom_right_y": 320,
    }
    payload, audit = apply_detection_v67_mistral_anchor_admission(
        payload=_v67_anchor_payload(
            bbox=proposed_bbox,
            core_bbox={
                "top_left_x": 110, "top_left_y": 110,
                "bottom_right_x": 290, "bottom_right_y": 290,
            },
            decision={
                "candidate_region_id": "CR-P001-001", "decision": "expand",
                "group_id": "VG-P001-001", "reason": "The cited dimension baseline is attached outside the graphic region.",
                "source_fact_ids": ["SF-OUT"],
            },
        ),
        candidate_regions=[_v67_mistral_anchor()],
        source_facts=[{
            "fact_id": "SF-OUT", "page_number": 1,
            "bbox": {"top_left_x": 320, "top_left_y": 180,
                     "bottom_right_x": 330, "bottom_right_y": 190},
        }],
    )

    assert payload["visual_groups"][0]["bbox"] == proposed_bbox
    assert audit[0]["status"] == "accepted_sonnet_change"


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


def test_dimension_halo_expands_envelope_to_outer_numeric_dimension_when_unique():
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
    assert packages[0]["dimension_envelope_source_fact_ids"] == ["SF00407"]
    assert packages[0]["bbox"] == {
        "top_left_x": 100, "top_left_y": 100,
        "bottom_right_x": 500, "bottom_right_y": 592,
    }
    assert packages[0]["core_bbox"] == {
        "top_left_x": 100, "top_left_y": 100,
        "bottom_right_x": 500, "bottom_right_y": 500,
    }


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
    assert packages[0]["dimension_envelope_source_fact_ids"] == []
    assert packages[0]["bbox"] == {
        "top_left_x": 100, "top_left_y": 100,
        "bottom_right_x": 500, "bottom_right_y": 500,
    }


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
