from io import BytesIO

import pytest

from agents.anthropic_adapter import (
    _compile_detection_v516_v561_consensus,
    _match_detection_v516_v561_object_groups,
    _normalize_source_degraded_registry_view_ids,
    build_detection_v5_source_degraded_boundary_candidates,
    consolidate_detection_v5_source_degraded_continuity_groups,
    validate_detection_v5_source_degraded_full_page_roles,
    validate_detection_v5_source_degraded_boundary_assessments,
    validate_detection_v5_source_degraded_role_resolutions,
)
from agents.detection_source_capability import (
    assess_detection_source_capability,
    drop_detection_visual_only_component_only_partitions,
    validate_detection_visual_only_partitions,
)
from agents.schemas.detection_registry_schema import (
    SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES,
    compile_detection_v5_merge_edges,
    compile_detection_v5_nested_duplicate_islands,
    compile_detection_v5_semantic_facts,
    compile_detection_v5_visual_dimension_conflicts,
)


def _fact(page, text, left, top, right, bottom):
    return {
        "page_number": page,
        "text": text,
        "bbox": {
            "top_left_x": left, "top_left_y": top,
            "bottom_right_x": right, "bottom_right_y": bottom,
        },
    }


def test_source_capability_routes_footer_and_single_note_only_document_visual_only():
    audit = assess_detection_source_capability(
        source_facts=[
            _fact(1, "ZE WORKROOM", 100, 1850, 400, 1880),
            _fact(1, "Project address", 500, 1880, 900, 1910),
            _fact(1, "Provide a cable opening", 900, 1200, 1200, 1240),
        ],
        page_count=1,
        page_dimensions={1: (2000, 2000)},
    )

    assert audit["route_eligible"] is True
    assert audit["route_reason"] == "all_pages_lack_usable_coordinate_evidence"
    assert audit["pages"][0]["localized_fact_position_count"] == 1


def _v516_group(group_id, left, top, right, bottom):
    return {
        "group_id": group_id,
        "page_number": 1,
        "evidence_class": "object_evidence",
        "visual_description": "One complete technical representation.",
        "bbox": {
            "top_left_x": left,
            "top_left_y": top,
            "bottom_right_x": right,
            "bottom_right_y": bottom,
        },
    }


def test_v516_matches_only_one_to_one_high_overlap_islands():
    mapping, audit = _match_detection_v516_v561_object_groups(
        [_v516_group("view-001", 0, 0, 100, 100)],
        [_v516_group("view-101", 5, 5, 105, 105)],
    )

    assert mapping == {"view-101": "view-001"}
    assert audit[0]["status"] == "accepted"


def test_v516_accepts_only_membership_present_in_both_proposals():
    proposal_a = {
        "object_groups": [
            _v516_group("view-001", 0, 0, 100, 100),
            _v516_group("view-002", 120, 0, 220, 100),
            _v516_group("view-003", 240, 0, 340, 100),
        ],
        "accepted_hypotheses": [{
            "group_ids": ["view-001", "view-002"],
            "hypothesis_reason": "Same unusual cabinet sequence.",
            "evidence": [{}],
        }],
    }
    proposal_b = {
        "object_groups": [
            _v516_group("view-101", 2, 0, 102, 100),
            _v516_group("view-102", 122, 0, 222, 100),
            _v516_group("view-103", 242, 0, 342, 100),
        ],
        "accepted_hypotheses": [{
            "group_ids": ["view-101", "view-102"],
            "hypothesis_reason": "Same unusual cabinet sequence.",
            "evidence": [{}],
        }],
    }

    result, audit = _compile_detection_v516_v561_consensus(
        primary=proposal_a,
        secondary=proposal_b,
    )

    assert audit["consensus_pairs"] == [["view-001", "view-002"]]
    assert [row["visual_group_ids"] for row in result["registry"]["objects"]] == [
        ["view-001", "view-002"], ["view-003"],
    ]


def test_source_capability_keeps_ordinary_v5_for_dimension_or_two_local_facts():
    audit = assess_detection_source_capability(
        source_facts=[
            _fact(1, "3310", 50, 90, 130, 120),
            _fact(2, "cabinet A", 200, 300, 380, 340),
            _fact(2, "cabinet B", 900, 700, 1080, 740),
        ],
        page_count=2,
        page_dimensions={1: (2000, 2000), 2: (2000, 2000)},
    )

    assert audit["route_eligible"] is False
    assert audit["capable_page_numbers"] == [1, 2]


def test_source_capability_does_not_route_mixed_document_into_visual_only_path():
    audit = assess_detection_source_capability(
        source_facts=[_fact(1, "3310", 50, 90, 130, 120)],
        page_count=2,
        page_dimensions={1: (2000, 2000), 2: (2000, 2000)},
    )

    assert audit["route_eligible"] is False
    assert audit["mixed_evidence_document"] is True
    assert audit["source_degraded_page_numbers"] == [2]


def test_source_degraded_role_resolution_keeps_component_out_of_object_graph():
    groups = [
        {
            "group_id": "view-001", "page_number": 1,
            "visual_role": "assembly_view", "evidence_class": "object_evidence",
        },
        {
            "group_id": "view-002", "page_number": 1,
            "visual_role": "assembly_view", "evidence_class": "object_evidence",
        },
    ]
    sources = [
        {"fact_id": "registry_view:view-001"},
        {"fact_id": "registry_view:view-002"},
    ]
    roles, audit = validate_detection_v5_source_degraded_role_resolutions(
        [
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "parent_group_id": "",
                "observation": "This is a complete independent fabrication view with one envelope.",
                "source_fact_ids": ["registry_view:view-001"],
            },
            {
                "group_id": "view-002", "visual_role": "component_detail",
                "parent_group_id": "view-001",
                "observation": "This cropped fragment is visibly part of the complete assembly view.",
                "source_fact_ids": [
                    "registry_view:view-002", "registry_view:view-001",
                ],
            },
        ],
        visual_groups=groups,
        source_facts=sources,
    )

    assert roles == {"view-001": "assembly_view", "view-002": "component_detail"}
    assert audit[1]["parent_group_id"] == "view-001"


def test_source_degraded_component_resolution_requires_assembly_parent():
    groups = [
        {
            "group_id": "view-001", "page_number": 1,
            "visual_role": "assembly_view", "evidence_class": "object_evidence",
        },
        {
            "group_id": "view-002", "page_number": 1,
            "visual_role": "assembly_view", "evidence_class": "object_evidence",
        },
    ]
    sources = [
        {"fact_id": "registry_view:view-001"},
        {"fact_id": "registry_view:view-002"},
    ]

    with pytest.raises(ValueError, match="assembly parent"):
        validate_detection_v5_source_degraded_role_resolutions(
            [
                {
                    "group_id": "view-001", "visual_role": "component_detail",
                    "parent_group_id": "view-002",
                    "observation": "This fragment belongs to the other complete view on the same page.",
                    "source_fact_ids": [
                        "registry_view:view-001", "registry_view:view-002",
                    ],
                },
                {
                    "group_id": "view-002", "visual_role": "component_detail",
                    "parent_group_id": "view-001",
                    "observation": "This second fragment belongs to the first incomplete fragment.",
                    "source_fact_ids": [
                        "registry_view:view-002", "registry_view:view-001",
                    ],
                },
            ],
            visual_groups=groups,
            source_facts=sources,
        )


def test_source_degraded_role_source_shorthand_is_normalized_deterministically():
    assert _normalize_source_degraded_registry_view_ids(
        ["VG001", "view-002", "registry_view:VG003", "SF001"],
        group_id_mapping={
            "VG001": "view-001", "VG003": "view-003",
            "view-001": "view-001", "view-002": "view-002", "view-003": "view-003",
        },
    ) == [
        "registry_view:view-001", "registry_view:view-002",
        "registry_view:view-003", "SF001",
    ]


def test_full_page_roles_require_one_final_role_per_visual_representation():
    roles, audit = validate_detection_v5_source_degraded_full_page_roles(
        [
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "classification_reason": "Complete independent shelving system with one visible envelope.",
            },
            {
                "group_id": "view-002", "visual_role": "component_detail",
                "classification_reason": "A cropped rail detail without an independent fabricated envelope.",
            },
        ],
        visual_groups=[
            {"group_id": "view-001"},
            {"group_id": "view-002"},
        ],
    )

    assert roles == {"view-001": "assembly_view", "view-002": "component_detail"}
    assert audit[1]["visual_role"] == "component_detail"


def _boundary_group(group_id, left, top, right, bottom):
    return {
        "group_id": group_id,
        "page_number": 1,
        "bbox": {
            "top_left_x": left, "top_left_y": top,
            "bottom_right_x": right, "bottom_right_y": bottom,
        },
        "core_bbox": {
            "top_left_x": left, "top_left_y": top,
            "bottom_right_x": right, "bottom_right_y": bottom,
        },
        "visual_description": f"Depiction {group_id}.",
        "representation_kind": "technical drawing",
    }


def test_source_degraded_boundary_ledger_requires_every_local_pair_to_be_explained():
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 80, 70, 180, 170),
        _boundary_group("view-003", 240, 0, 340, 100),
    ]
    candidates = build_detection_v5_source_degraded_boundary_candidates(groups)
    assert [candidate["group_ids"] for candidate in candidates] == [
        ["view-001", "view-002"],
        ["view-001", "view-003"],
        ["view-002", "view-003"],
    ]
    assert candidates[0]["reason"] == "same_page_zero_core_gap_requires_contour_witness"
    assert candidates[1]["reason"] == "same_page_local_core_neighbour_requires_contour_witness"
    assert candidates[0]["boundary_search_bbox"] == {
        "top_left_x": 82, "top_left_y": 77,
        "bottom_right_x": 98, "bottom_right_y": 93,
    }

    with pytest.raises(ValueError, match="omits a candidate"):
        validate_detection_v5_source_degraded_boundary_assessments(
            [], candidates=candidates,
        )

    continuity_groups, audit = validate_detection_v5_source_degraded_boundary_assessments(
        [{
            "group_ids": ["view-001", "view-002"],
            "relation": "physically_continuous",
            "boundary_kind": "continuous_geometry",
            "witness_bbox": {
                "top_left_x": 85, "top_left_y": 80,
                "bottom_right_x": 95, "bottom_right_y": 90,
            },
            "observation": "The angled panel visibly continues from the shelf frame without a gap.",
        }, {
            "group_ids": ["view-001", "view-003"],
            "relation": "physically_separate",
            "boundary_kind": "visible_background_gap",
            "witness_bbox": {
                "top_left_x": 160, "top_left_y": 45,
                "bottom_right_x": 180, "bottom_right_y": 55,
            },
            "observation": "A broad visible background gap separates the remote independent drawing.",
        }, {
            "group_ids": ["view-002", "view-003"],
            "relation": "physically_separate",
            "boundary_kind": "visible_background_gap",
            "witness_bbox": {
                "top_left_x": 200, "top_left_y": 80,
                "bottom_right_x": 220, "bottom_right_y": 90,
            },
            "observation": "A visible background gap separates the two independent construction drawings.",
        }],
        candidates=candidates,
    )
    assert audit[0]["relation"] == "physically_continuous"
    assert continuity_groups == [{
        "group_ids": ["view-001", "view-002"],
        "observation": "The angled panel visibly continues from the shelf frame without a gap.",
    }]


def test_source_degraded_boundary_ledger_rejects_semantic_projection_as_a_boundary():
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 105, 0, 205, 100),
    ]
    candidates = build_detection_v5_source_degraded_boundary_candidates(groups)

    with pytest.raises(ValueError, match="boundary assessment is invalid"):
        validate_detection_v5_source_degraded_boundary_assessments(
            [{
                "group_ids": ["view-001", "view-002"],
                "relation": "physically_separate",
                "boundary_kind": "independent_projection",
                "witness_bbox": {
                    "top_left_x": 98, "top_left_y": 45,
                    "bottom_right_x": 112, "bottom_right_y": 55,
                },
                "observation": "The two depictions use different orientation and dimensions only.",
            }],
            candidates=candidates,
        )


def test_source_degraded_boundary_continuity_requires_ink_at_the_local_witness():
    image_module = pytest.importorskip("PIL.Image")
    draw_module = pytest.importorskip("PIL.ImageDraw")
    image = image_module.new("L", (220, 120), color=255)
    draw_module.Draw(image).line((92, 50, 108, 50), fill=0, width=2)
    output = BytesIO()
    image.save(output, format="PNG")
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 100, 0, 200, 100),
    ]
    candidates = build_detection_v5_source_degraded_boundary_candidates(
        groups,
        page_frames={1: {"width": 220, "height": 120}},
    )
    continuity_groups, audit = validate_detection_v5_source_degraded_boundary_assessments(
        [{
            "group_ids": ["view-001", "view-002"],
            "relation": "physically_continuous",
            "boundary_kind": "continuous_geometry",
            "witness_bbox": {
                "top_left_x": 94, "top_left_y": 44,
                "bottom_right_x": 106, "bottom_right_y": 56,
            },
            "observation": "The black frame line visibly crosses from the shelf into the angled panel.",
        }],
        candidates=candidates,
        page_frames={1: {"width": 220, "height": 120}},
        page_images=[output.getvalue()],
    )

    assert audit[0]["pixel_audit"]["consistent"] is True
    assert continuity_groups[0]["group_ids"] == ["view-001", "view-002"]


def test_source_degraded_boundary_does_not_consolidate_a_continuity_witness_on_blank_paper():
    image_module = pytest.importorskip("PIL.Image")
    image = image_module.new("L", (220, 120), color=255)
    output = BytesIO()
    image.save(output, format="PNG")
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 100, 0, 200, 100),
    ]
    candidates = build_detection_v5_source_degraded_boundary_candidates(
        groups,
        page_frames={1: {"width": 220, "height": 120}},
    )
    continuity_groups, audit = validate_detection_v5_source_degraded_boundary_assessments(
        [{
            "group_ids": ["view-001", "view-002"],
            "relation": "physically_continuous",
            "boundary_kind": "continuous_geometry",
            "witness_bbox": {
                "top_left_x": 94, "top_left_y": 44,
                "bottom_right_x": 106, "bottom_right_y": 56,
            },
            "observation": "The alleged joint is deliberately placed on blank paper for this test only.",
        }],
        candidates=candidates,
        page_frames={1: {"width": 220, "height": 120}},
        page_images=[output.getvalue()],
    )

    assert audit[0]["pixel_audit"]["consistent"] is False
    assert continuity_groups == []


def test_source_degraded_boundary_ledger_unions_only_attested_continuity_before_roles():
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 80, 70, 180, 170),
        _boundary_group("view-003", 240, 0, 340, 100),
    ]
    effective, mapping, audit = consolidate_detection_v5_source_degraded_continuity_groups(
        groups,
        [{
            "group_ids": ["view-001", "view-002"],
            "observation": "The angled panel visibly continues from the shelf frame without a gap.",
        }],
    )
    assert mapping == {
        "view-001": "view-001", "view-002": "view-001", "view-003": "view-003",
    }
    assert [group["group_id"] for group in effective] == ["view-001", "view-003"]
    assert effective[0]["source_group_ids"] == ["view-001", "view-002"]
    assert audit[0]["canonical_group_id"] == "view-001"


def test_visual_only_partition_requires_exact_coverage_and_connected_visual_tree():
    result = validate_detection_visual_only_partitions([
        {
            "group_ids": ["view-001", "view-002"],
            "visual_basis": [{
                "evidence_type": "alternate_projection",
                "view_ids": ["view-001", "view-002"],
                "observation": "Both views show the same unique cabinet bay sequence.",
            }],
        },
        {
            "group_ids": ["view-003"],
            "visual_basis": [{
                "evidence_type": "complete_physical_envelope",
                "view_ids": ["view-003"],
                "observation": "One self-contained framed sliding door assembly.",
            }],
        },
    ], object_view_ids={"view-001", "view-002", "view-003"})

    assert [row["group_ids"] for row in result] == [
        ["view-001", "view-002"], ["view-003"],
    ]


def test_visual_only_partition_accepts_visible_compatible_dimensions():
    result = validate_detection_visual_only_partitions([
        {
            "group_ids": ["view-001", "view-002"],
            "visual_basis": [{
                "evidence_type": "compatible_dimensions",
                "view_ids": ["view-001", "view-002"],
                "observation": "The 1850 and 1760 measured console portions align across both depictions.",
            }],
        },
    ], object_view_ids={"view-001", "view-002"})

    assert result[0]["visual_basis"][0]["evidence_type"] == "compatible_dimensions"


def test_visual_only_partition_rejects_proximity_as_merge_evidence():
    with pytest.raises(ValueError, match="generic"):
        validate_detection_visual_only_partitions([
            {
                "group_ids": ["view-001", "view-002"],
                "visual_basis": [{
                    "evidence_type": "matching_unique_structure",
                    "view_ids": ["view-001", "view-002"],
                    "observation": "The views are nearby on the same page.",
                }],
            },
        ], object_view_ids={"view-001", "view-002"})


def test_component_only_partition_is_dropped_but_mixed_or_unknown_ids_are_retained_for_validation():
    partitions, audit = drop_detection_visual_only_component_only_partitions(
        [
            {
                "group_ids": ["view-003"],
                "visual_basis": [{
                    "evidence_type": "matching_unique_structure",
                    "view_ids": ["view-003", "view-004"],
                    "observation": "The component is visibly incorporated into view 004.",
                }],
            },
            {
                "group_ids": ["view-001"],
                "visual_basis": [{
                    "evidence_type": "complete_physical_envelope",
                    "view_ids": ["view-001"],
                    "observation": "One complete independent physical envelope.",
                }],
            },
            {
                "group_ids": ["view-002"],
                "visual_basis": [{
                    "evidence_type": "complete_physical_envelope",
                    "view_ids": ["view-002"],
                    "observation": "One complete independent physical envelope.",
                }],
            },
            {
                "group_ids": ["view-004"],
                "visual_basis": [{
                    "evidence_type": "complete_physical_envelope",
                    "view_ids": ["view-004"],
                    "observation": "One complete independent physical envelope.",
                }],
            },
        ],
        known_view_ids={"view-001", "view-002", "view-003", "view-004"},
        object_view_ids={"view-001", "view-002", "view-004"},
    )

    assert audit == [{
        "partition_index": 1,
        "dropped_group_ids": ["view-003"],
        "reason": "component_detail_cannot_own_visual_only_partition",
    }]
    assert [partition["group_ids"] for partition in partitions] == [
        ["view-001"], ["view-002"], ["view-004"],
    ]
    assert validate_detection_visual_only_partitions(
        partitions, object_view_ids={"view-001", "view-002", "view-004"},
    )


def test_direct_shared_structure_requires_specific_physical_witness():
    groups = [
        {"group_id": "view-001", "evidence_class": "object_evidence"},
        {"group_id": "view-002", "evidence_class": "object_evidence"},
        {"group_id": "view-003", "evidence_class": "object_evidence"},
    ]
    sources = [
        {"fact_id": f"registry_view:{group['group_id']}"}
        for group in groups
    ]
    accepted, audit = compile_detection_v5_semantic_facts(
        [{
            "group_id_a": "view-001",
            "group_id_b": "view-002",
            "evidence_type": "direct_shared_structure",
            "strength": "standard",
            "observation": "Both views use the same metal frame principle.",
            "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
        }],
        visual_groups=groups,
        source_facts=sources,
    )

    assert accepted == []
    assert audit["rejected"][0]["reason"] == (
        "direct_shared_structure_requires_physical_witness"
    )


def test_direct_shared_structure_accepts_a_cited_third_view_witness():
    groups = [
        {"group_id": "view-001", "evidence_class": "object_evidence"},
        {"group_id": "view-002", "evidence_class": "object_evidence"},
        {"group_id": "view-003", "evidence_class": "object_evidence"},
    ]
    sources = [
        {"fact_id": f"registry_view:{group['group_id']}"}
        for group in groups
    ]
    accepted, audit = compile_detection_v5_semantic_facts(
        [{
            "group_id_a": "view-001",
            "group_id_b": "view-002",
            "evidence_type": "direct_shared_structure",
            "strength": "standard",
            "observation": "The complete assembly view shows the side panel fastened to the shelf frame.",
            "source_fact_ids": ["registry_view:view-003"],
            "structural_witness": {
                "kind": "third_view_shows_both",
                "witness_view_id": "view-003",
                "joined_parts": ["side panel", "shelf frame"],
                "connection": "View 003 shows the panel mechanically fastened to the shelf frame.",
            },
        }],
        visual_groups=groups,
        source_facts=sources,
    )

    assert audit["rejected"] == []
    assert accepted[0]["structural_witness"]["witness_view_id"] == "view-003"


def test_visual_dimension_similarity_is_source_degraded_only_and_requires_readings():
    groups = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
    ]
    sources = [{"fact_id": "registry_view:view-001"}, {"fact_id": "registry_view:view-002"}]
    fact = {
        "group_id_a": "view-001",
        "group_id_b": "view-002",
        "evidence_type": "visual_dimension_similarity",
        "strength": "standard",
        "observation": "Both Views visibly show 1850 and 630 as the console dimensions.",
        "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
    }

    rejected, _ = compile_detection_v5_semantic_facts(
        [fact], visual_groups=groups, source_facts=sources,
    )
    accepted, audit = compile_detection_v5_semantic_facts(
        [fact],
        visual_groups=groups,
        source_facts=sources,
        allowed_evidence_types=SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES,
    )

    assert rejected == []
    assert audit["rejected"] == []
    assert accepted[0]["evidence_type"] == "visual_dimension_similarity"


def test_visual_dimension_similarity_needs_a_second_fact_and_conflict_blocks_merge():
    groups = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
    ]
    sources = [{"fact_id": "registry_view:view-001"}, {"fact_id": "registry_view:view-002"}]
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "evidence_type": "visual_dimension_similarity", "strength": "standard",
            "observation": "Both Views visibly show 1850 and 630 for the console.",
            "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
        },
    ], visual_groups=groups, source_facts=sources,
       allowed_evidence_types=SOURCE_DEGRADED_VISUAL_SEMANTIC_EVIDENCE_TYPES)
    edges, _ = compile_detection_v5_merge_edges(
        [], facts, visual_groups=groups, allow_batch_confirmation=False,
    )
    conflicts, conflict_audit = compile_detection_v5_visual_dimension_conflicts([
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "readings_a": ["950"], "readings_b": ["1760"],
            "observation": "The comparable widths are 950 and 1760, so they conflict.",
            "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
        },
    ], visual_groups=groups, source_facts=sources,
       allowed_pairs={("view-001", "view-002")})
    paired_facts = [
        *facts,
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same five-bay console order and offset support recur.",
            "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
        },
    ]
    unblocked_edges, _ = compile_detection_v5_merge_edges(
        [], paired_facts, visual_groups=groups, allow_batch_confirmation=False,
    )
    blocked_edges, blocked_audit = compile_detection_v5_merge_edges(
        [], paired_facts, visual_groups=groups,
        merge_blocked_pairs=conflicts, allow_batch_confirmation=False,
    )

    assert edges[0]["relationship"] == "supporting_relation"
    assert conflict_audit["rejected"] == []
    assert unblocked_edges[0]["relationship"] == "same_object_view"
    assert blocked_edges[0]["relationship"] == "supporting_relation"
    assert blocked_audit["edges"][0]["merge_blocked"]


def test_visual_dimension_conflict_requires_readings_from_both_views():
    groups = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
    ]
    sources = [{"fact_id": "registry_view:view-001"}, {"fact_id": "registry_view:view-002"}]
    conflicts, audit = compile_detection_v5_visual_dimension_conflicts([
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "readings_a": ["950"], "readings_b": [],
            "observation": "One View has a different category.",
            "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
        },
    ], visual_groups=groups, source_facts=sources,
       allowed_pairs={("view-001", "view-002")})

    assert conflicts == {}
    assert audit["rejected"][0]["reason"] == "dimension_conflict_not_grounded"


def test_nested_duplicate_requires_visual_decision_and_strong_same_page_containment():
    groups = [
        {
            "group_id": "view-001", "evidence_class": "object_evidence",
            "page_number": 1,
            "core_bbox": {
                "top_left_x": 100, "top_left_y": 100,
                "bottom_right_x": 500, "bottom_right_y": 500,
            },
        },
        {
            "group_id": "view-002", "evidence_class": "object_evidence",
            "page_number": 1,
            "core_bbox": {
                "top_left_x": 140, "top_left_y": 120,
                "bottom_right_x": 480, "bottom_right_y": 480,
            },
        },
        {
            "group_id": "view-003", "evidence_class": "object_evidence",
            "page_number": 1,
            "core_bbox": {
                "top_left_x": 460, "top_left_y": 100,
                "bottom_right_x": 700, "bottom_right_y": 400,
            },
        },
    ]
    sources = [{"fact_id": f"registry_view:{group['group_id']}"} for group in groups]
    duplicates, audit = compile_detection_v5_nested_duplicate_islands([
        {
            "child_group_id": "view-002", "parent_group_id": "view-001",
            "observation": "View 002 is only a visually contained fragment of the continuous View 001 drawing.",
            "source_fact_ids": ["registry_view:view-002", "registry_view:view-001"],
        },
        {
            "child_group_id": "view-003", "parent_group_id": "view-001",
            "observation": "View 003 is a separate framed drawing despite partial envelope overlap.",
            "source_fact_ids": ["registry_view:view-003", "registry_view:view-001"],
        },
    ], visual_groups=groups, source_facts=sources)

    assert duplicates == {"view-002": "view-001"}
    assert audit["rejected"][0]["reason"] == "nested_duplicate_geometry_insufficient"
