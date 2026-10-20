import pytest

from agents.anthropic_adapter import (
    DETECTION_VISUAL_REGISTRY_JSON_SCHEMA,
    discard_degenerate_evidence_regions,
)
from agents.schemas.detection_registry_schema import (
    DETECTION_REGISTRY_JSON_SCHEMA,
    DetectionRegistrySchemaError,
    compile_detection_dimension_graph,
    derive_detection_pairwise_merge_proofs_from_parent_links,
    derive_detection_package_decision_audit,
    derive_detection_proof_components,
    derive_detection_standalone_package_group_ids,
    normalize_empty_detection_envelope_chains,
    partition_detection_relation_edges,
    validate_detection_dimension_inventory,
    validate_detection_pairwise_merge_proofs,
    validate_detection_registry,
    validate_detection_shared_reference_group_ids,
)
from agents.schemas.detection_schema import validate_detection_result
from agents.schemas.detection_visual_map_schema import (
    normalize_detection_visual_map_group_ids,
    validate_detection_visual_map,
)


def _fact(evidence_type, observation, pages=(1,)):
    return {
        "evidence_type": evidence_type,
        "evidence_pages": list(pages),
        "observation": observation,
    }


def _proof(left, right, facts):
    return {
        "group_id_a": min(left, right),
        "group_id_b": max(left, right),
        "relationship": "same_object_view",
        "evidence_facts": facts,
        "commercial_inseparability": "The cited construction evidence establishes one quote line.",
    }


def _reference_link(first_group, second_group, facts):
    return {
        "group_id_a": min(first_group, second_group),
        "group_id_b": max(first_group, second_group),
        "relationship": "reference_link",
        "evidence_facts": facts,
        "commercial_inseparability": (
            "The general and product views are related, but not a merge."
        ),
    }


def _root(reason="No positive relation to an earlier group is evidenced.", blocked_merge=None):
    root = {
        "decision": "new_object_root",
        "parent_group_id": "ROOT",
        "relationship": "new_object_root",
        "evidence_facts": [],
        "decision_reason": reason,
    }
    if blocked_merge is not None:
        root["blocked_merge"] = blocked_merge
    return root


def _attach(parent_group_id, facts, reason="The cited evidence proves one quote line."):
    return {
        "decision": "attach_to_group",
        "parent_group_id": parent_group_id,
        "relationship": "same_object_view",
        "evidence_facts": facts,
        "decision_reason": reason,
    }


def _group(group_id, proof_parent):
    return {"group_id": group_id, "proof_parent": proof_parent}


def test_v4_schema_accepts_evidence_regions_and_ui_only_preview_bbox():
    result = validate_detection_result({
        "rfq_run": {
            "run_id": "run-1", "company_id": "company-1", "project_name": "Project",
            "file_name": "drawing.pdf", "source_type": "pdf", "design_partner": "unknown",
            "client": "unknown", "author": "unknown", "document_date": "unknown",
            "pages_detected": 1, "language": "en", "file_quality_level": 3,
            "file_quality_label": "detailed_drawings", "file_quality_confidence": 90,
            "file_quality_notes": "", "status": "intake_parsed", "created_at": "unknown",
        },
        "detected_objects": [{
            "run_id": "run-1", "company_id": "company-1", "object_id": "object-001",
            "object_name": "Object 1", "quantity": 1, "quantity_explicit": False,
            "review_required": False, "evidence_pages": "1", "approved": False,
            "created_at": "unknown", "evidence_page_refs": [{
                "page_number": 1, "source_label": "A-01",
                "regions": [{"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40}],
                "presentation_preview_bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            }],
        }],
    })

    assert result["detected_objects"][0]["evidence_page_refs"][0]["regions"]


def test_degenerate_evidence_regions_are_dropped_but_the_page_is_preserved():
    normalized = discard_degenerate_evidence_regions({
        "detected_objects": [{"evidence_page_refs": [{
            "page_number": 3,
            "regions": [{"top_left_x": 20, "top_left_y": 10, "bottom_right_x": 20, "bottom_right_y": 50}],
            "presentation_preview_bbox": {"top_left_x": 5, "top_left_y": 5, "bottom_right_x": 5, "bottom_right_y": 30},
        }]}],
    })

    reference = normalized["detected_objects"][0]["evidence_page_refs"][0]
    assert reference["page_number"] == 3
    assert reference["regions"] == []
    assert "presentation_preview_bbox" not in reference


def test_proof_graph_derives_one_component_from_two_evidence_backed_edges():
    groups = {"view-001", "view-002", "view-003"}
    proofs = [
        _proof("view-001", "view-002", [
            _fact("matching_topology", "The same three leaves recur."),
            _fact("unique_geometry", "The offset handle sequence recurs."),
        ]),
        _proof("view-002", "view-003", [
            _fact("dimension_transform", "The elevation width matches the plan after axis change.", (1, 2)),
            _fact("matching_topology", "The bay and leaf order matches.", (1, 2)),
        ]),
    ]

    assert validate_detection_pairwise_merge_proofs(
        proofs, visual_group_ids=groups, page_count=2
    ) == proofs
    assert derive_detection_proof_components(proofs, visual_group_ids=groups) == [
        ["view-001", "view-002", "view-003"],
    ]


def test_v4_44_envelope_compiler_retains_one_equality_and_merges_two_independent_equalities():
    groups = [
        {"group_id": "view-001", "page_number": 1, "representation_kind": "elevation"},
        {"group_id": "view-002", "page_number": 1, "representation_kind": "section"},
        {"group_id": "view-003", "page_number": 2, "representation_kind": "elevation"},
    ]
    inventory = validate_detection_dimension_inventory([
        {"group_id": "view-001", "envelope_chains": [
            {"chain_id": "G1-h", "axis": "horizontal", "segments": [], "direct_total": "358"},
            {"chain_id": "G1-v", "axis": "vertical", "segments": [], "direct_total": "245"},
        ]},
        {"group_id": "view-002", "envelope_chains": [
            {"chain_id": "G2-h", "axis": "horizontal", "segments": [], "direct_total": "358"},
        ]},
        {"group_id": "view-003", "envelope_chains": [
            {"chain_id": "G3-h", "axis": "horizontal", "segments": [], "direct_total": "358"},
            {"chain_id": "G3-v", "axis": "vertical", "segments": [], "direct_total": "245"},
        ]},
    ], visual_group_ids={group["group_id"] for group in groups})

    compiled_edges, conflicts, audit = compile_detection_dimension_graph(
        inventory, visual_groups=groups, page_drawing_codes={},
    )

    edges, accepted_merges, reference_links, rejected = (
        partition_detection_relation_edges(
            compiled_edges,
            visual_group_ids={group["group_id"] for group in groups},
            page_count=2,
        )
    )

    assert [row["group_id"] for row in inventory] == [
        "view-001", "view-002", "view-003",
    ]
    assert len(edges) == 3
    assert edges[0]["relationship"] == "supporting_relation"
    assert accepted_merges[0]["group_id_a"] == "view-001"
    assert accepted_merges[0]["group_id_b"] == "view-003"
    assert reference_links == []
    assert rejected == []
    assert conflicts == []
    assert audit["pairs_checked"] == 3
    assert derive_detection_proof_components(
        accepted_merges, visual_group_ids={group["group_id"] for group in groups}
    ) == [["view-001", "view-003"], ["view-002"]]


def test_v4_49_dimension_inventory_allows_multiple_chains_on_one_axis():
    inventory = validate_detection_dimension_inventory([
        {"group_id": "view-001", "envelope_chains": [
            {"chain_id": "G1-horizontal-top", "axis": "horizontal", "segments": [], "direct_total": "331"},
            {"chain_id": "G1-horizontal-bottom", "axis": "horizontal", "segments": ["63", "61", "46", "47", "77", "64"], "direct_total": "358"},
        ]},
    ], visual_group_ids={"view-001"})

    assert [chain["chain_id"] for chain in inventory[0]["envelope_chains"]] == [
        "G1-horizontal-top", "G1-horizontal-bottom",
    ]


def test_v4_44_envelope_compiler_never_uses_source_code_as_a_graph_edge():
    groups = [
        {"group_id": "view-001", "page_number": 1, "representation_kind": "elevation"},
        {"group_id": "view-002", "page_number": 1, "representation_kind": "elevation"},
    ]
    inventory = validate_detection_dimension_inventory([
        {"group_id": "view-001", "envelope_chains": [{
            "chain_id": "G1-h", "axis": "horizontal", "segments": [], "direct_total": "358",
        }]},
        {"group_id": "view-002", "envelope_chains": [{
            "chain_id": "G2-h", "axis": "horizontal", "segments": [], "direct_total": "349",
        }]},
    ], visual_group_ids={group["group_id"] for group in groups})

    edges, conflicts, audit = compile_detection_dimension_graph(
        inventory, visual_groups=groups, page_drawing_codes={1: "N57"},
    )

    assert edges == []
    assert conflicts == []
    assert audit["source_root_merge_edge_count"] == 0
    assert audit["source_codes_used_for_graph"] is False


def test_v4_44_envelope_compiler_records_cross_axis_matches_as_equality_only():
    groups = [
        {"group_id": "view-001", "page_number": 1, "representation_kind": "elevation"},
        {"group_id": "view-002", "page_number": 2, "representation_kind": "plan"},
    ]
    inventory = validate_detection_dimension_inventory([
        {"group_id": "view-001", "envelope_chains": [
            {"chain_id": "G1-h", "axis": "horizontal", "segments": [], "direct_total": "358"},
            {"chain_id": "G1-v", "axis": "vertical", "segments": [], "direct_total": "245"},
        ]},
        {"group_id": "view-002", "envelope_chains": [
            {"chain_id": "G2-h", "axis": "horizontal", "segments": [], "direct_total": "245"},
            {"chain_id": "G2-v", "axis": "vertical", "segments": [], "direct_total": "358"},
        ]},
    ], visual_group_ids={group["group_id"] for group in groups})

    edges, conflicts, audit = compile_detection_dimension_graph(
        inventory, visual_groups=groups, page_drawing_codes={},
    )
    _, accepted_merges, _, rejected = partition_detection_relation_edges(
        edges, visual_group_ids={group["group_id"] for group in groups}, page_count=2,
    )

    assert conflicts == []
    assert [fact["evidence_type"] for fact in edges[0]["evidence_facts"]] == [
        "dimension_equality", "dimension_equality",
    ]
    assert len(accepted_merges) == 1
    assert rejected == []
    assert audit["dimension_transform_fact_count"] == 0


def test_v4_44_envelope_compiler_uses_a_larger_segment_sum_and_near_equality():
    groups = [
        {"group_id": "view-001", "page_number": 1, "representation_kind": "elevation"},
        {"group_id": "view-002", "page_number": 2, "representation_kind": "elevation"},
    ]
    inventory = validate_detection_dimension_inventory([
        {"group_id": "view-001", "envelope_chains": [{
            "chain_id": "G1-h", "axis": "horizontal",
            "direct_total": "338", "segments": ["64", "203", "81"],
        }]},
        {"group_id": "view-002", "envelope_chains": [{
            "chain_id": "G2-h", "axis": "horizontal",
            "direct_total": "347", "segments": [],
        }]},
    ], visual_group_ids={group["group_id"] for group in groups})

    edges, conflicts, audit = compile_detection_dimension_graph(
        inventory, visual_groups=groups, page_drawing_codes={}, document_dimension_unit="cm",
    )

    assert conflicts == []
    assert edges[0]["relationship"] == "supporting_relation"
    assert "total 348 (segmented_sum)" in edges[0]["evidence_facts"][0]["observation"]
    assert audit["near_envelope_equality_fact_count"] == 1
    assert audit["document_dimension_unit"] == "cm"


def test_v4_40_relation_graph_preserves_positive_dimension_facts_and_isolates_weak_merge():
    edges = [
        _proof("view-001", "view-002", [
            _fact("dimension_equality", "Overall width 358 cm is literal on both views."),
            _fact("dimension_equality", "Overall height 245 cm is literal on both views."),
        ]),
        _proof("view-001", "view-003", [
            _fact(
                "dimension_transform",
                "1180 mm elevation width equals 1180 mm plan depth after axis remapping.",
            ),
        ]),
        _proof("view-002", "view-003", [
            _fact("dimension_equality", "Overall width 358 cm is literal on both views."),
            _fact("matching_topology", "The same three cabinet bays recur."),
        ]),
        _proof("view-002", "view-004", [
            _fact("dimension_equality", "A local 600 mm dimension occurs on both views."),
        ]),
        _reference_link("view-003", "view-004", [
            _fact("explicit_document_relation", "The plan locates the separate cabinet."),
        ]),
    ]

    relation_edges, accepted_merges, reference_links, rejected = (
        partition_detection_relation_edges(
            edges,
            visual_group_ids={"view-001", "view-002", "view-003", "view-004"},
            page_count=1,
        )
    )

    assert len(relation_edges) == 5
    assert len(accepted_merges) == 3
    assert len(reference_links) == 1
    assert rejected == [{
        "edge_index": 3,
        "group_id_a": "view-002",
        "group_id_b": "view-004",
        "relationship": "same_object_view",
        "rejection_stage": "merge_threshold",
        "reason": "merge needs an explicit document relation, an exact dimension transform, or two independent evidence facts",
        "evidence_facts": [
            _fact("dimension_equality", "A local 600 mm dimension occurs on both views."),
        ],
        "commercial_inseparability": "The cited construction evidence establishes one quote line.",
    }]
    assert derive_detection_proof_components(
        accepted_merges,
        visual_group_ids={"view-001", "view-002", "view-003", "view-004"},
    ) == [["view-001", "view-002", "view-003"], ["view-004"]]


def test_shared_reference_evidence_is_undirected_and_not_a_package_component():
    groups = {"overview", "view-001", "view-002"}
    proofs = [
        _reference_link("overview", "view-001", [
            _fact("explicit_document_relation", "The plan locates object N57."),
        ]),
        _reference_link("view-002", "overview", [
            _fact("explicit_document_relation", "The plan locates object N58."),
        ]),
    ]

    validated = validate_detection_pairwise_merge_proofs(
        proofs, visual_group_ids=groups, page_count=1
    )
    assert validate_detection_shared_reference_group_ids(
        ["overview"],
        proofs=validated,
        visual_group_ids=groups,
        commercial_components=[["view-001"], ["view-002"]],
    ) == ["overview"]
    assert derive_detection_proof_components(
        validated, visual_group_ids=groups
    ) == [["overview"], ["view-001"], ["view-002"]]


def test_shared_reference_evidence_needs_multiple_reference_links_and_no_merge():
    groups = {"overview", "view-001", "view-002", "view-003"}
    one_link = validate_detection_pairwise_merge_proofs([
        _reference_link("overview", "view-001", [
            _fact("explicit_document_relation", "The plan locates object N57."),
        ]),
    ], visual_group_ids=groups, page_count=1)

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="shared reference evidence must connect at least two distinct proven packages without a merge",
    ):
        validate_detection_shared_reference_group_ids(
            ["overview"],
            proofs=one_link,
            visual_group_ids=groups,
            commercial_components=[["view-001"], ["view-002"], ["view-003"]],
        )

    merge_and_references = validate_detection_pairwise_merge_proofs([
        _reference_link("overview", "view-001", [
            _fact("explicit_document_relation", "The plan locates object N57."),
        ]),
        _reference_link("overview", "view-002", [
            _fact("explicit_document_relation", "The plan locates object N58."),
        ]),
        _proof("overview", "view-003", [
            _fact("explicit_document_relation", "A leader explicitly ties the view to N57."),
        ]),
    ], visual_group_ids=groups, page_count=1)

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="shared reference evidence cannot participate in a merge proof",
    ):
        validate_detection_shared_reference_group_ids(
            ["overview"],
            proofs=merge_and_references,
            visual_group_ids=groups,
            commercial_components=[["view-001"], ["view-002"], ["view-003"]],
        )


def test_shared_reference_evidence_cannot_link_two_views_of_one_package():
    groups = {"overview", "view-001", "view-002"}
    proofs = validate_detection_pairwise_merge_proofs([
        _proof("view-001", "view-002", [
            _fact("explicit_document_relation", "N76B labels both object views."),
        ]),
        _reference_link("overview", "view-001", [
            _fact("explicit_document_relation", "The overview shows N76B."),
        ]),
        _reference_link("overview", "view-002", [
            _fact("explicit_document_relation", "The overview shows N76B."),
        ]),
    ], visual_group_ids=groups, page_count=1)

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="shared reference evidence must connect at least two distinct proven packages without a merge",
    ):
        validate_detection_shared_reference_group_ids(
            ["overview"],
            proofs=proofs,
            visual_group_ids=groups,
            commercial_components=[["view-001", "view-002"]],
        )


def test_proof_graph_rejects_a_lone_direct_structure_claim():
    proof = _proof("view-001", "view-002", [
        _fact("direct_shared_structure", "An L-shaped junction is drawn."),
    ])

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="needs an explicit document relation, a dimension transform, or two independent evidence facts",
    ):
        validate_detection_pairwise_merge_proofs(
            [proof], visual_group_ids={"view-001", "view-002"}, page_count=1
        )


def test_proof_graph_accepts_two_distinct_dimension_facts():
    proof = _proof("view-001", "view-002", [
        _fact("dimension_transform", "The 1180 mm elevation width matches the section width.", (1, 2)),
        _fact("dimension_transform", "The 2450 mm elevation height matches the section height.", (1, 2)),
    ])

    assert validate_detection_pairwise_merge_proofs(
        [proof], visual_group_ids={"view-001", "view-002"}, page_count=2
    ) == [proof]


def test_proof_graph_accepts_two_independent_equal_dimensions():
    proof = _proof("view-001", "view-002", [
        _fact(
            "dimension_equality",
            "The overall width is 358 cm on both groups.",
            (1, 2),
        ),
        _fact(
            "dimension_equality",
            "The overall height is 260 cm on both groups.",
            (1, 2),
        ),
    ])

    assert validate_detection_pairwise_merge_proofs(
        [proof], visual_group_ids={"view-001", "view-002"}, page_count=2
    ) == [proof]


def test_one_equal_dimension_needs_an_independent_supporting_fact():
    proof = _proof("view-001", "view-002", [
        _fact(
            "dimension_equality",
            "The overall width is 358 cm on both groups.",
            (1, 2),
        ),
        _fact(
            "direct_shared_structure",
            "Both depictions show the same continuous carcass.",
            (1, 2),
        ),
    ])

    assert validate_detection_pairwise_merge_proofs(
        [proof], visual_group_ids={"view-001", "view-002"}, page_count=2
    ) == [proof]

    with pytest.raises(
        DetectionRegistrySchemaError,
        match="needs an explicit document relation, a dimension transform, or two independent evidence facts",
    ):
        validate_detection_pairwise_merge_proofs(
            [_proof("view-001", "view-002", [
                _fact(
                    "dimension_equality",
                    "The overall width is 358 cm on both groups.",
                    (1, 2),
                ),
            ])],
            visual_group_ids={"view-001", "view-002"},
            page_count=2,
        )


def test_proof_graph_accepts_one_exact_dimension_transform():
    proof = _proof("view-001", "view-002", [
        _fact(
            "dimension_transform",
            "The 1180 mm elevation width on page 1 equals the 1180 mm plan depth on page 2 after the axis change.",
            (1, 2),
        ),
    ])

    assert validate_detection_pairwise_merge_proofs(
        [proof], visual_group_ids={"view-001", "view-002"}, page_count=2
    ) == [proof]


def test_root_can_record_a_dimension_conflict_that_prevents_a_merge():
    groups = [
        _group("view-001", _root("First complete cabinet elevation.")),
        _group("view-002", _root(
            "view-001 states overall width 1180 mm; this elevation states 1450 mm.",
            blocked_merge={
                "candidate_parent_group_id": "view-001",
                "conflict_type": "dimension_conflict",
                "observation": "1180 mm and 1450 mm both claim the overall width.",
            },
        )),
    ]

    assert derive_detection_pairwise_merge_proofs_from_parent_links(
        groups, page_count=1
    ) == []


def test_blocked_dimension_merge_must_target_an_earlier_group():
    groups = [
        _group("view-001", _root(
            blocked_merge={
                "candidate_parent_group_id": "view-002",
                "conflict_type": "dimension_conflict",
                "observation": "1180 mm and 1450 mm both claim the overall width.",
            },
        )),
    ]

    with pytest.raises(DetectionRegistrySchemaError, match="root blocked-merge evidence is invalid"):
        derive_detection_pairwise_merge_proofs_from_parent_links(groups, page_count=1)


def test_attachment_cannot_carry_a_blocked_dimension_merge():
    groups = [
        _group("view-001", _root()),
        _group("view-002", {
            **_attach("view-001", [_fact("explicit_document_relation", "N76B links both depictions.")]),
            "blocked_merge": {
                "candidate_parent_group_id": "view-001",
                "conflict_type": "dimension_conflict",
                "observation": "1180 mm and 1450 mm both claim the overall width.",
            },
        }),
    ]

    with pytest.raises(DetectionRegistrySchemaError, match="attachment proof-parent is invalid"):
        derive_detection_pairwise_merge_proofs_from_parent_links(groups, page_count=1)


def test_proof_graph_rejects_repeated_facts_and_self_links():
    fact = _fact("dimension_transform", "The 1180 mm width matches.")
    repeated = _proof("view-001", "view-002", [fact, fact])
    self_link = _proof("view-001", "view-001", [
        _fact("explicit_document_relation", "N76B labels both depictions."),
    ])

    with pytest.raises(DetectionRegistrySchemaError, match="evidence facts are invalid"):
        validate_detection_pairwise_merge_proofs(
            [repeated], visual_group_ids={"view-001", "view-002"}, page_count=1
        )
    with pytest.raises(DetectionRegistrySchemaError, match="proof groups are invalid"):
        validate_detection_pairwise_merge_proofs(
            [self_link], visual_group_ids={"view-001"}, page_count=1
        )


def test_proof_graph_rejects_cycles_instead_of_deriving_ambiguous_membership():
    proofs = [
        _proof("view-001", "view-002", [_fact("explicit_document_relation", "N76B labels both views.")]),
        _proof("view-002", "view-003", [_fact("explicit_document_relation", "N76B labels both views.")]),
        _proof("view-003", "view-001", [_fact("explicit_document_relation", "N76B labels both views.")]),
    ]

    with pytest.raises(DetectionRegistrySchemaError, match="minimal proof tree"):
        validate_detection_pairwise_merge_proofs(
            proofs, visual_group_ids={"view-001", "view-002", "view-003"}, page_count=1
        )


def test_singleton_visual_group_becomes_a_singleton_component_without_placeholder():
    groups = {"view-001", "view-002"}

    assert validate_detection_pairwise_merge_proofs(
        [], visual_group_ids=groups, page_count=1
    ) == []
    assert derive_detection_proof_components([], visual_group_ids=groups) == [
        ["view-001"], ["view-002"],
    ]


def test_every_commercial_visual_group_has_a_graph_derived_package_outcome():
    components = [["view-001", "view-002"], ["view-003"]]
    assert derive_detection_standalone_package_group_ids(components) == ["view-003"]
    assert derive_detection_package_decision_audit(components) == [
        {
            "group_id": "view-001",
            "package_disposition": "part_of_proven_component",
            "component_anchor_group_id": "view-001",
        },
        {
            "group_id": "view-002",
            "package_disposition": "part_of_proven_component",
            "component_anchor_group_id": "view-001",
        },
        {
            "group_id": "view-003",
            "package_disposition": "standalone_package",
            "component_anchor_group_id": "view-003",
        },
    ]


def test_reference_links_do_not_merge_products_or_create_directional_chains():
    groups = {"view-001", "view-002", "view-003", "view-004"}
    proofs = [
        _reference_link("view-001", "view-002", [
            _fact("matching_topology", "The overview visibly locates the kitchen."),
        ]),
        _reference_link("view-001", "view-003", [
            _fact("matching_topology", "The overview visibly locates the island."),
        ]),
        _reference_link("view-001", "view-004", [
            _fact("matching_topology", "The overview visibly locates the cabinet."),
        ]),
    ]

    assert validate_detection_pairwise_merge_proofs(
        proofs, visual_group_ids=groups, page_count=1
    ) == proofs
    assert derive_detection_proof_components(proofs, visual_group_ids=groups) == [
        ["view-001"], ["view-002"], ["view-003"], ["view-004"],
    ]

def test_document_only_upload_needs_no_proof_graph_or_object_package():
    assert validate_detection_pairwise_merge_proofs(
        [], visual_group_ids=set(), page_count=1
    ) == []
    assert derive_detection_proof_components([], visual_group_ids=set()) == []


def test_every_visual_group_must_make_a_reasoned_root_or_parent_decision():
    groups = [
        _group("view-001", _root("This is the first depiction of the cabinet.")),
        _group("view-002", _attach("view-001", [
            _fact("dimension_transform", "The plan and elevation have matching 1200 mm width."),
            _fact("matching_topology", "Both views show three bays and the same handle order."),
        ], "The matching dimensions and bay sequence prove an alternate view.")),
        _group("view-003", _root("The different enclosure and function have no proved link to the cabinet.")),
    ]

    proofs = derive_detection_pairwise_merge_proofs_from_parent_links(
        groups, page_count=1
    )

    assert [(proof["group_id_a"], proof["group_id_b"]) for proof in proofs] == [
        ("view-001", "view-002"),
    ]
    assert derive_detection_proof_components(
        proofs, visual_group_ids={"view-001", "view-002", "view-003"}
    ) == [["view-001", "view-002"], ["view-003"]]


def test_parent_decision_rejects_missing_reason_and_later_parent():
    missing_reason = [_group("view-001", {
        **_root(), "decision_reason": "",
    })]
    later_parent = [
        _group("view-001", _attach("view-002", [
            _fact("explicit_document_relation", "D01 labels both views."),
        ])),
        _group("view-002", _root()),
    ]

    with pytest.raises(DetectionRegistrySchemaError, match="requires a factual reason"):
        derive_detection_pairwise_merge_proofs_from_parent_links(
            missing_reason, page_count=1
        )
    with pytest.raises(DetectionRegistrySchemaError, match="attachment proof-parent is invalid"):
        derive_detection_pairwise_merge_proofs_from_parent_links(
            later_parent, page_count=1
        )


def test_v4_43_registry_schema_contains_only_model_extracted_facts():
    group_properties = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]["visual_groups"]["items"]["properties"]
    dimension_properties = DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]["dimension_inventory"]["items"]["properties"]

    assert "owner_object_ids" not in group_properties
    assert "evidence_class" not in group_properties
    assert "classification_reason" not in group_properties
    assert "standalone_package_group_ids" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "objects" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["required"]
    assert "objects" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "relation_edges" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "page_coverage" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "pair_relation_runs" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "pair_relation_states" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "pair_relation_facts" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "dimension_inventory" in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "classifications" in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "envelope_chains" in dimension_properties
    assert "proof_edges" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]
    assert "merge_proofs" not in DETECTION_VISUAL_REGISTRY_JSON_SCHEMA["properties"]


def test_empty_envelope_chain_is_canonicalized_without_losing_other_measurements():
    normalized, empty_group_ids = normalize_empty_detection_envelope_chains([
        {"group_id": "view-001", "envelope_chains": [{
            "chain_id": "G1-horizontal", "axis": "horizontal",
            "segments": [], "direct_total": "",
        }]},
        {"group_id": "view-002", "envelope_chains": [{
            "chain_id": "G2-horizontal", "axis": "horizontal",
            "segments": ["64", "203", "64"], "direct_total": "358",
        }]},
    ])

    assert empty_group_ids == ["view-001"]
    assert normalized[0]["envelope_chains"] == []
    assert validate_detection_dimension_inventory(
        normalized, visual_group_ids={"view-001", "view-002"},
    )[1]["envelope_chains"][0]["direct_total"] == "358"


def test_final_registry_requires_every_object_evidence_group_once():
    registry = {"objects": [{
        "object_id": "object-001", "transport_label": "N76B", "quantity": 1,
        "quantity_explicit": False, "identity_pages": [11],
        "estimation_evidence_pages": [11], "visual_group_ids": ["view-001"],
        "visual_identity": "slatted partition", "boundary_basis": "dimensioned elevation",
    }]}

    assert validate_detection_registry(
        registry, visual_group_ids={"view-001"}, object_evidence_group_ids={"view-001"}
    ) == registry
    with pytest.raises(DetectionRegistrySchemaError, match="must account for every object-evidence group"):
        validate_detection_registry(
            registry, visual_group_ids={"view-001", "view-002"},
            object_evidence_group_ids={"view-001", "view-002"},
        )


def test_visual_map_normalizes_provider_group_ids_before_strict_validation():
    visual_map = validate_detection_visual_map(normalize_detection_visual_map_group_ids({
        "visual_groups": [
            {"group_id": "group_a", "page_number": 1, "location_hint": "left", "visual_description": "console view", "representation_kind": "perspective"},
            {"group_id": "group_b", "page_number": 1, "location_hint": "right", "visual_description": "console view", "representation_kind": "elevation"},
        ],
    }))

    assert [group["group_id"] for group in visual_map["visual_groups"]] == ["view-001", "view-002"]


def test_final_registry_schema_still_requires_nonempty_visual_packages():
    visual_group_ids = DETECTION_REGISTRY_JSON_SCHEMA["properties"]["objects"]["items"]["properties"]["visual_group_ids"]

    assert visual_group_ids["minItems"] == 1
