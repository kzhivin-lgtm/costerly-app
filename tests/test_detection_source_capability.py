from io import BytesIO

import pytest

from agents.anthropic_adapter import (
    _compile_detection_v5_source_degraded_direct_registry_payload,
    _compile_detection_v5_source_degraded_pairwise_registry_payload,
    assess_detection_v5_source_degraded_structural_edge_admissibility,
    _compile_detection_v516_v561_consensus,
    _match_detection_v516_v561_object_groups,
    _normalize_source_degraded_registry_view_ids,
    build_detection_v5_source_degraded_boundary_candidates,
    complete_detection_v5_source_degraded_missing_pair_ledger_rows,
    consolidate_detection_v5_source_degraded_continuity_groups,
    resolve_detection_v5_source_degraded_pairwise_roles,
    validate_detection_v5_source_degraded_direct_roles,
    validate_detection_v5_source_degraded_pair_ledger,
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


def test_direct_roles_require_a_same_page_assembly_owner_for_every_detail():
    groups = [
        {"group_id": "view-001", "page_number": 1},
        {"group_id": "view-002", "page_number": 1},
        {"group_id": "view-003", "page_number": 1},
    ]
    roles, owners, audit = validate_detection_v5_source_degraded_direct_roles(
        [
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "owner_group_id": "",
                "classification_reason": "Complete independent shelving assembly with its envelope.",
            },
            {
                "group_id": "view-002", "visual_role": "component_detail",
                "owner_group_id": "view-001",
                "classification_reason": "Visible close-up of the same shelving assembly frame joint.",
            },
            {
                "group_id": "view-003", "visual_role": "document_context",
                "owner_group_id": "",
                "classification_reason": "Project title block and drawing administration only.",
            },
        ],
        visual_groups=groups,
    )

    assert roles["view-001"] == "assembly_view"
    assert owners == {"view-002": "view-001"}
    assert audit[1]["owner_group_id"] == "view-001"


def test_direct_roles_ignore_a_spurious_owner_for_an_assembly_view():
    roles, owners, audit = validate_detection_v5_source_degraded_direct_roles(
        [
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "owner_group_id": "view-002",
                "classification_reason": "Complete independent shelving assembly with its envelope.",
            },
            {
                "group_id": "view-002", "visual_role": "assembly_view",
                "owner_group_id": "",
                "classification_reason": "Complete independent door system with its own finished envelope.",
            },
        ],
        visual_groups=[
            {"group_id": "view-001", "page_number": 1},
            {"group_id": "view-002", "page_number": 1},
        ],
        allow_non_detail_owner=True,
    )

    assert roles["view-001"] == "assembly_view"
    assert owners == {}
    assert audit[0]["owner_group_id"] is None
    assert audit[0]["ignored_owner_group_id"] == "view-002"


def test_legacy_direct_roles_reject_a_spurious_owner_for_an_assembly_view():
    with pytest.raises(ValueError, match="assembly/context cannot have an owner"):
        validate_detection_v5_source_degraded_direct_roles(
            [{
                "group_id": "view-001", "visual_role": "assembly_view",
                "owner_group_id": "view-002",
                "classification_reason": "Complete independent shelving assembly with its envelope.",
            }, {
                "group_id": "view-002", "visual_role": "assembly_view",
                "owner_group_id": "",
                "classification_reason": "Complete independent door system with its own finished envelope.",
            }],
            visual_groups=[
                {"group_id": "view-001", "page_number": 1},
                {"group_id": "view-002", "page_number": 1},
            ],
        )


def test_direct_roles_reject_a_detail_without_a_same_page_assembly_owner():
    with pytest.raises(ValueError, match="component detail needs one same-page assembly owner"):
        validate_detection_v5_source_degraded_direct_roles(
            [
                {
                    "group_id": "view-001", "visual_role": "assembly_view",
                    "owner_group_id": "",
                    "classification_reason": "Complete independent shelving assembly with its envelope.",
                },
                {
                    "group_id": "view-002", "visual_role": "component_detail",
                    "owner_group_id": "",
                    "classification_reason": "An incomplete technical fragment with no named assembly.",
                },
            ],
            visual_groups=[
                {"group_id": "view-001", "page_number": 1},
                {"group_id": "view-002", "page_number": 1},
            ],
        )


def test_pair_ledger_requires_every_same_page_technical_pair():
    groups = [
        {"group_id": "view-001", "page_number": 1},
        {"group_id": "view-002", "page_number": 1},
        {"group_id": "view-003", "page_number": 1},
    ]
    roles = {
        "view-001": "assembly_view",
        "view-002": "assembly_view",
        "view-003": "assembly_view",
    }
    complete_ledger = [
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "relation": "same_object", "evidence_type": "alternate_projection",
            "separation_kind": "none",
            "observation": "Both drawings show the same finished console from distinct projections.",
            "identity_witnesses": [
                {
                    "witness_type": "finished_envelope",
                    "observation": "Both show the full horizontal console envelope from opposite projections.",
                },
                {
                    "witness_type": "internal_layout",
                    "observation": "Both preserve the left-to-right order of the open bay and enclosed end module.",
                },
            ],
        },
        {
            "group_id_a": "view-001", "group_id_b": "view-003",
            "relation": "different_object", "evidence_type": "none",
            "separation_kind": "different_finished_envelope",
            "observation": "One complete console and one separate enclosed shelving assembly are shown.",
            "identity_witnesses": [],
        },
        {
            "group_id_a": "view-002", "group_id_b": "view-003",
            "relation": "different_object", "evidence_type": "none",
            "separation_kind": "different_finished_envelope",
            "observation": "The alternate console view and the separate shelving assembly have distinct envelopes.",
            "identity_witnesses": [],
        },
    ]

    ledger = validate_detection_v5_source_degraded_pair_ledger(
        complete_ledger,
        visual_groups=groups,
        roles_by_id=roles,
    )

    assert [(row["group_id_a"], row["group_id_b"]) for row in ledger] == [
        ("view-001", "view-002"),
        ("view-001", "view-003"),
        ("view-002", "view-003"),
    ]
    with pytest.raises(ValueError, match="must decide every same-page technical pair"):
        validate_detection_v5_source_degraded_pair_ledger(
            complete_ledger[:-1],
            visual_groups=groups,
            roles_by_id=roles,
        )
    with pytest.raises(ValueError, match="must decide every same-page technical pair"):
        validate_detection_v5_source_degraded_pair_ledger(
            [complete_ledger[1]],
            visual_groups=groups,
            roles_by_id={
                "view-001": "assembly_view",
                "view-002": "component_detail",
                "view-003": "assembly_view",
            },
        )


def test_pair_ledger_completion_records_only_an_inconclusive_missing_pair():
    groups = [
        {"group_id": "view-001", "page_number": 1},
        {"group_id": "view-002", "page_number": 1},
    ]
    completed, completion_audit = (
        complete_detection_v5_source_degraded_missing_pair_ledger_rows(
            [],
            visual_groups=groups,
            roles_by_id={
                "view-001": "assembly_view",
                "view-002": "assembly_view",
            },
        )
    )

    assert completion_audit == [{
        "group_id_a": "view-001",
        "group_id_b": "view-002",
        "repair": "runtime_completed_missing_pair_ledger_row",
        "reason": "provider_omitted_required_pair_decision",
    }]
    assert validate_detection_v5_source_degraded_pair_ledger(
        completed,
        visual_groups=groups,
        roles_by_id={
            "view-001": "assembly_view",
            "view-002": "assembly_view",
        },
    ) == [{
        "group_id_a": "view-001",
        "group_id_b": "view-002",
        "relation": "inconclusive",
        "evidence_type": "none",
        "separation_kind": "insufficient_visual_evidence",
        "observation": (
            "Provider omitted this required pair decision; runtime supplies no "
            "identity or separation claim."
        ),
        "identity_witnesses": [],
    }]


def test_pair_ledger_rejects_generic_different_object_reasoning():
    with pytest.raises(ValueError, match="different-object ledger evidence is invalid"):
        validate_detection_v5_source_degraded_pair_ledger(
            [{
                "group_id_a": "view-001", "group_id_b": "view-002",
                "relation": "different_object", "evidence_type": "none",
                "separation_kind": "physical_separation",
                "observation": "Different configuration and detailed labeling make the views unrelated.",
                "identity_witnesses": [],
            }],
            visual_groups=[
                {"group_id": "view-001", "page_number": 1},
                {"group_id": "view-002", "page_number": 1},
            ],
            roles_by_id={
                "view-001": "assembly_view",
                "view-002": "assembly_view",
            },
        )


def test_pairwise_role_resolver_promotes_an_unproven_component_detail():
    roles, owners, audit, repairs = resolve_detection_v5_source_degraded_pairwise_roles(
        roles_by_id={
            "view-001": "assembly_view",
            "view-002": "component_detail",
        },
        owner_by_detail_id={"view-002": "view-001"},
        role_audit=[
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "owner_group_id": None,
                "classification_reason": "Complete independent finished cabinet.",
            },
            {
                "group_id": "view-002", "visual_role": "component_detail",
                "owner_group_id": "view-001",
                "classification_reason": "Panel view treated as an incomplete component.",
            },
        ],
        pair_ledger=[{
            "group_id_a": "view-001", "group_id_b": "view-002",
            "relation": "different_object", "evidence_type": "none",
            "separation_kind": "different_finished_envelope",
            "observation": "One enclosed cabinet and one separately finished door system are shown.",
            "identity_witnesses": [],
        }],
        admitted_same_object_pairs=set(),
    )

    assert roles["view-002"] == "assembly_view"
    assert owners == {}
    assert audit[1]["owner_group_id"] is None
    assert repairs == [{
        "group_id": "view-002",
        "prior_owner_group_id": "view-001",
        "repair": "promoted_to_assembly_view",
        "reason": "component_owner_lacks_admitted_structural_proof",
        "ledger_relation": "different_object",
        "ledger_evidence_type": "none",
    }]


def test_pairwise_role_resolver_promotes_detail_when_its_raw_direct_continuity_is_rejected():
    roles, owners, _audit, repairs = resolve_detection_v5_source_degraded_pairwise_roles(
        roles_by_id={
            "view-001": "assembly_view",
            "view-002": "component_detail",
        },
        owner_by_detail_id={"view-002": "view-001"},
        role_audit=[
            {
                "group_id": "view-001", "visual_role": "assembly_view",
                "owner_group_id": None,
                "classification_reason": "Complete independent finished cabinet.",
            },
            {
                "group_id": "view-002", "visual_role": "component_detail",
                "owner_group_id": "view-001",
                "classification_reason": "Elevation proposed as an owned component.",
            },
        ],
        pair_ledger=[{
            "group_id_a": "view-001", "group_id_b": "view-002",
            "relation": "same_object", "evidence_type": "direct_continuity",
            "separation_kind": "none",
            "observation": "The elevation is claimed to be a component within the nearby cabinet.",
            "identity_witnesses": [
                {
                    "witness_type": "direct_continuity",
                    "observation": "The elevation is claimed to be integrated into the nearby cabinet.",
                },
                {
                    "witness_type": "finished_envelope",
                    "observation": "Both show the full rectangular panel envelope of the proposed component.",
                },
            ],
        }],
        admitted_same_object_pairs=set(),
    )

    assert roles["view-002"] == "assembly_view"
    assert owners == {}
    assert repairs[0]["reason"] == "component_owner_lacks_admitted_structural_proof"


def test_structural_pair_admission_requires_two_original_assemblies_and_typed_witnesses():
    admitted, rejected = assess_detection_v5_source_degraded_structural_edge_admissibility(
        [
            {
                "group_id_a": "view-001",
                "group_id_b": "view-002",
                "relation": "same_object",
                "evidence_type": "alternate_projection",
                "identity_witnesses": [
                    {
                        "witness_type": "finished_envelope",
                        "observation": "Both show the full cabinet envelope from opposite viewpoints.",
                    },
                    {
                        "witness_type": "continuous_structure",
                        "observation": "Both show the continuous base rail below the cabinet.",
                    },
                ],
            },
            {
                "group_id_a": "view-003",
                "group_id_b": "view-004",
                "relation": "same_object",
                "evidence_type": "alternate_projection",
                "identity_witnesses": [
                    {
                        "witness_type": "finished_envelope",
                        "observation": "Both show the full horizontal console envelope from opposite projections.",
                    },
                    {
                        "witness_type": "internal_layout",
                        "observation": "Both preserve the left-to-right order of the open bay and enclosed end module.",
                    },
                ],
            },
        ],
        original_roles_by_id={
            "view-001": "assembly_view",
            "view-002": "component_detail",
            "view-003": "assembly_view",
            "view-004": "assembly_view",
        },
    )

    assert admitted == {("view-003", "view-004")}
    assert rejected == [{
        "group_id_a": "view-001",
        "group_id_b": "view-002",
        "relation": "same_object",
        "evidence_type": "alternate_projection",
        "identity_witnesses": [
            {
                "witness_type": "finished_envelope",
                "observation": "Both show the full cabinet envelope from opposite viewpoints.",
            },
            {
                "witness_type": "continuous_structure",
                "observation": "Both show the continuous base rail below the cabinet.",
            },
        ],
        "reasons": ["same_object_requires_two_original_assembly_views"],
    }]


def test_structural_pair_admission_rejects_an_alternate_projection_without_envelope_witness():
    admitted, rejected = assess_detection_v5_source_degraded_structural_edge_admissibility(
        [{
            "group_id_a": "view-001",
            "group_id_b": "view-002",
            "relation": "same_object",
            "evidence_type": "alternate_projection",
            "identity_witnesses": [
                {
                    "witness_type": "internal_layout",
                    "observation": "Both preserve the left-to-right order of the open bay and enclosed end module.",
                },
                {
                    "witness_type": "continuous_structure",
                    "observation": "Both show the continuous base rail below the cabinet.",
                },
            ],
        }],
        original_roles_by_id={
            "view-001": "assembly_view",
            "view-002": "assembly_view",
        },
    )

    assert admitted == set()
    assert rejected[0]["reasons"] == [
        "alternate_projection_requires_finished_envelope_witness",
    ]


def test_pairwise_audit_compiles_partitions_from_same_object_edges_only():
    raw_groups = [
        {
            "group_id": "draft-console-front", "page_number": 1,
            "location_hint": "lower left", "visual_description": "Complete console front elevation.",
            "representation_kind": "technical assembly",
            "bbox": {
                "top_left_x": 10, "top_left_y": 10,
                "bottom_right_x": 200, "bottom_right_y": 200,
            },
            "core_bbox": {
                "top_left_x": 10, "top_left_y": 10,
                "bottom_right_x": 200, "bottom_right_y": 200,
            },
        },
        {
            "group_id": "draft-console-perspective", "page_number": 1,
            "location_hint": "lower right", "visual_description": "Complete console perspective.",
            "representation_kind": "technical assembly",
            "bbox": {
                "top_left_x": 210, "top_left_y": 10,
                "bottom_right_x": 400, "bottom_right_y": 200,
            },
            "core_bbox": {
                "top_left_x": 210, "top_left_y": 10,
                "bottom_right_x": 400, "bottom_right_y": 200,
            },
        },
        {
            "group_id": "draft-shelf", "page_number": 1,
            "location_hint": "upper left", "visual_description": "Complete shelving assembly.",
            "representation_kind": "technical assembly",
            "bbox": {
                "top_left_x": 10, "top_left_y": 210,
                "bottom_right_x": 200, "bottom_right_y": 400,
            },
            "core_bbox": {
                "top_left_x": 10, "top_left_y": 210,
                "bottom_right_x": 200, "bottom_right_y": 400,
            },
        },
    ]
    compiled = _compile_detection_v5_source_degraded_pairwise_registry_payload(
        {
            "roles": [
                {
                    "group_id": "view-001", "visual_role": "assembly_view",
                    "owner_group_id": "",
                    "classification_reason": "Complete finished console front elevation.",
                },
                {
                    "group_id": "view-002", "visual_role": "assembly_view",
                    "owner_group_id": "",
                    "classification_reason": "Complete perspective representation of the finished console.",
                },
                {
                    "group_id": "view-003", "visual_role": "assembly_view",
                    "owner_group_id": "view-001",
                    "classification_reason": "Complete independent shelving fabrication envelope.",
                },
            ],
            "pair_ledger": [
                {
                    "group_id_a": "view-001", "group_id_b": "view-002",
                    "relation": "same_object", "evidence_type": "alternate_projection",
                    "separation_kind": "none",
                    "observation": "Both views show the same finished console through front and perspective projections.",
                    "identity_witnesses": [
                        {
                            "witness_type": "finished_envelope",
                            "observation": "Both show the full horizontal console envelope from opposite projections.",
                        },
                        {
                            "witness_type": "internal_layout",
                            "observation": "Both preserve the left-to-right order of the open bay and enclosed end module.",
                        },
                    ],
                },
                {
                    "group_id_a": "view-001", "group_id_b": "view-003",
                    "relation": "different_object", "evidence_type": "none",
                    "separation_kind": "different_finished_envelope",
                    "observation": "The console and shelving are separately finished fabricated envelopes.",
                    "identity_witnesses": [],
                },
                {
                    "group_id_a": "view-002", "group_id_b": "view-003",
                    "relation": "different_object", "evidence_type": "none",
                    "separation_kind": "different_finished_envelope",
                    "observation": "The console perspective and shelving are separately finished fabricated envelopes.",
                    "identity_witnesses": [],
                },
            ],
        },
        raw_visual_groups=raw_groups,
        raw_page_coverage=[{
            "page_number": 1,
            "visual_group_ids": [
                "draft-console-front", "draft-console-perspective", "draft-shelf",
            ],
        }],
        page_count=1,
        page_frames={1: {"width": 500, "height": 500}},
    )

    assert [item["visual_group_ids"] for item in compiled["registry"]["objects"]] == [
        ["view-001", "view-002"], ["view-003"],
    ]
    assert len(compiled["positive_relation_edges"]) == 1
    assert compiled["detail_role_repairs"] == []
    assert compiled["role_audit"][2]["ignored_owner_group_id"] == "view-001"


def test_direct_inventory_compiles_only_the_final_audited_partition():
    compiled = _compile_detection_v5_source_degraded_direct_registry_payload(
        {
            "visual_groups": [
                {
                    "group_id": "draft-shelf", "page_number": 1,
                    "location_hint": "upper left",
                    "visual_description": "Complete shelving assembly.",
                    "representation_kind": "technical assembly",
                    "bbox": {
                        "top_left_x": 10, "top_left_y": 10,
                        "bottom_right_x": 200, "bottom_right_y": 200,
                    },
                    "core_bbox": {
                        "top_left_x": 10, "top_left_y": 10,
                        "bottom_right_x": 200, "bottom_right_y": 200,
                    },
                },
            ],
            "page_coverage": [
                {"page_number": 1, "visual_group_ids": ["draft-shelf"]},
            ],
            "roles": [
                {
                    "group_id": "draft-shelf", "visual_role": "assembly_view",
                    "owner_group_id": "",
                    "classification_reason": "Complete independent shelving fabrication.",
                },
            ],
            "partitions": [
                {
                    "group_ids": ["draft-shelf"],
                    "visual_basis": [
                        {
                            "evidence_type": "complete_physical_envelope",
                            "view_ids": ["draft-shelf"],
                            "observation": "Complete independent shelving fabrication.",
                        },
                    ],
                },
            ],
        },
        page_count=1,
        page_frames={1: {"width": 500, "height": 500}},
    )

    assert compiled["registry"]["objects"][0]["visual_group_ids"] == ["view-001"]
    assert compiled["owner_by_detail_id"] == {}


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
    ]
    assert candidates[0]["reason"] == "same_page_core_overlap_requires_contour_witness"
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
        }],
        candidates=candidates,
    )
    assert audit[0]["relation"] == "physically_continuous"
    assert continuity_groups == [{
        "group_ids": ["view-001", "view-002"],
        "observation": "The angled panel visibly continues from the shelf frame without a gap.",
    }]


def test_source_degraded_boundary_ledger_clips_a_broad_witness_to_its_corridor():
    candidates = [{
        "group_ids": ["view-003", "view-005"],
        "page_number": 1,
        "boundary_search_bbox": {
            "top_left_x": 897, "top_left_y": 407,
            "bottom_right_x": 913, "bottom_right_y": 423,
        },
    }]
    continuity_groups, audit = validate_detection_v5_source_degraded_boundary_assessments(
        [{
            "group_ids": ["view-003", "view-005"],
            "relation": "physically_separate",
            "boundary_kind": "visible_background_gap",
            "witness_bbox": {
                "top_left_x": 850, "top_left_y": 380,
                "bottom_right_x": 920, "bottom_right_y": 450,
            },
            "observation": "A visible white background gap separates the two local drawings.",
        }],
        candidates=candidates,
    )

    assert continuity_groups == []
    assert audit[0]["witness_bbox"] == {
        "top_left_x": 850, "top_left_y": 380,
        "bottom_right_x": 920, "bottom_right_y": 450,
    }
    assert audit[0]["effective_witness_bbox"] == {
        "top_left_x": 897, "top_left_y": 407,
        "bottom_right_x": 913, "bottom_right_y": 423,
    }


def test_source_degraded_boundary_ledger_rejects_a_trivial_corridor_overlap():
    candidates = [{
        "group_ids": ["view-001", "view-002"],
        "page_number": 1,
        "boundary_search_bbox": {
            "top_left_x": 100, "top_left_y": 100,
            "bottom_right_x": 116, "bottom_right_y": 116,
        },
    }]

    with pytest.raises(ValueError, match="does not materially overlap"):
        validate_detection_v5_source_degraded_boundary_assessments(
            [{
                "group_ids": ["view-001", "view-002"],
                "relation": "physically_continuous",
                "boundary_kind": "continuous_geometry",
                "witness_bbox": {
                    "top_left_x": 97, "top_left_y": 100,
                    "bottom_right_x": 103, "bottom_right_y": 116,
                },
                "observation": "The alleged joint only grazes the corridor and is not local evidence.",
            }],
            candidates=candidates,
        )


def test_source_degraded_boundary_ledger_rejects_semantic_projection_as_a_boundary():
    groups = [
        _boundary_group("view-001", 0, 0, 100, 100),
        _boundary_group("view-002", 80, 0, 180, 100),
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


def test_source_degraded_boundary_queue_always_includes_historical_shelf_overlap():
    # Page23's V5.21 failure split a shelf and its attached angled panel into
    # these overlapping cores. The pair must stay mandatory even if each core
    # has nearer or equally near neighbours elsewhere on the page.
    groups = [
        _boundary_group("view-001", 80, 30, 500, 360),
        _boundary_group("view-002", 560, 40, 1150, 360),
        _boundary_group("view-003", 90, 300, 500, 500),
        _boundary_group("view-004", 85, 510, 500, 730),
        _boundary_group("view-005", 570, 410, 1150, 730),
    ]

    candidates = build_detection_v5_source_degraded_boundary_candidates(groups)
    shelf_panel = next(
        candidate for candidate in candidates
        if candidate["group_ids"] == ["view-001", "view-003"]
    )

    assert shelf_panel["core_distance_px"] == 0.0
    assert "same_page_core_overlap_requires_contour_witness" in shelf_panel["reason"]


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
