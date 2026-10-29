import pytest

from agents.anthropic_adapter import (
    apply_detection_v73_coverage_admission,
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


def _v73_coverage_target() -> dict:
    return {
        "candidate_region_id": "CR-P001-002", "page_number": 1,
        "bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 500, "bottom_right_y": 500,
        },
        "basis": "fusion_text_cluster", "role": "coverage_only",
        "source_fact_ids": ["SF-COV"],
    }


def _v73_coverage_payload(*, decision: dict, exceptions: list[dict] | None = None) -> dict:
    return {
        "visual_groups": [{
            "group_id": "VG-P001-002", "page_number": 1,
            "bbox": {
                "top_left_x": 180, "top_left_y": 180,
                "bottom_right_x": 420, "bottom_right_y": 420,
            },
            "core_bbox": {
                "top_left_x": 200, "top_left_y": 200,
                "bottom_right_x": 400, "bottom_right_y": 400,
            },
        }],
        "candidate_region_exceptions": exceptions or [],
        "coverage_region_decisions": [decision],
    }


def test_v73_coverage_accepts_an_independent_visual_island_without_copying_candidate_bbox():
    payload, audit = apply_detection_v73_coverage_admission(
        payload=_v73_coverage_payload(decision={
            "candidate_region_id": "CR-P001-002", "decision": "accept",
            "group_id": "VG-P001-002",
            "reason": "The page visibly shows a separate cabinet elevation in this region.",
            "source_fact_ids": ["SF-COV"],
        }),
        candidate_regions=[_v73_coverage_target()],
        source_facts=[{
            "fact_id": "SF-COV", "page_number": 1,
            "bbox": {
                "top_left_x": 250, "top_left_y": 250,
                "bottom_right_x": 270, "bottom_right_y": 270,
            },
        }],
    )

    assert payload["visual_groups"][0]["bbox"] != _v73_coverage_target()["bbox"]
    assert audit == [{
        "candidate_region_id": "CR-P001-002", "page_number": 1,
        "candidate_bbox": _v73_coverage_target()["bbox"], "decision": "accept",
        "group_id": "VG-P001-002",
        "reason": "The page visibly shows a separate cabinet elevation in this region.",
        "source_fact_ids": ["SF-COV"], "status": "accepted_visual_island",
        "island_bbox": payload["visual_groups"][0]["bbox"],
    }]
    assert "coverage_region_decisions" not in payload


def test_v73_coverage_rejection_requires_a_matching_non_island_exception():
    with pytest.raises(ValueError, match="matching exception"):
        apply_detection_v73_coverage_admission(
            payload=_v73_coverage_payload(decision={
                "candidate_region_id": "CR-P001-002", "decision": "reject",
                "group_id": "", "reason": "The region contains only a dimension annotation cluster.",
                "source_fact_ids": [],
            }),
            candidate_regions=[_v73_coverage_target()],
            source_facts=[],
        )


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


def test_dimension_halo_keeps_outer_numeric_dimension_when_one_island_is_nearby():
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
    assert packages[0]["dimension_halo_source_fact_ids"] == ["SF00407"]


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
    assert packages[0]["dimension_halo_source_fact_ids"] == []


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
