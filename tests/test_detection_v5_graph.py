from agents.schemas.detection_registry_schema import (
    compile_detection_v5_dimension_graph,
    compile_detection_v5_hypothesis_membership_edges,
    compile_detection_v5_merge_edges,
    compile_detection_v5_membership_edges,
    compile_detection_v5_object_hypotheses,
    derive_detection_v5_dominant_page_attachment_edges,
    compile_detection_v5_semantic_facts,
    validate_detection_v5_final_result,
)
from agents.anthropic_adapter import infer_detection_v5_bare_dimension_unit


VIEWS = [
    {"group_id": "view-001", "evidence_class": "object_evidence"},
    {"group_id": "view-002", "evidence_class": "object_evidence"},
]


def _fingerprints(left, right):
    return [
        {"group_id": "view-001", "occurrences": left},
        {"group_id": "view-002", "occurrences": right},
    ]


def _occurrence(identifier, value, source):
    return {"occurrence_id": identifier, "value_mm": str(value), "source_fact_ids": [source]}


def test_v5_rare_exact_large_dimension_is_very_strong_but_not_a_merge_alone():
    edges, _ = compile_detection_v5_dimension_graph(
        _fingerprints([_occurrence("a", 3310, "SF1")], [_occurrence("b", 3310, "SF2")]),
        visual_groups=VIEWS,
    )
    assert edges[0]["dimension_similarity_score"] == 87.5
    merged, _ = compile_detection_v5_merge_edges(edges, [])
    assert merged[0]["relationship"] == "supporting_relation"


def test_v5_repeated_typical_dimension_is_counted_one_to_one():
    edges, _ = compile_detection_v5_dimension_graph(
        _fingerprints(
            [_occurrence("a1", 600, "SF1"), _occurrence("a2", 600, "SF2"), _occurrence("a3", 600, "SF3")],
            [_occurrence("b1", 600, "SF4"), _occurrence("b2", 600, "SF5")],
        ),
        visual_groups=VIEWS,
    )
    assert edges[0]["dimension_similarity_score"] == 35.0
    assert "2 paired occurrence(s)" in edges[0]["evidence_facts"][0]["observation"]


def test_v5_dimension_queue_scores_every_same_page_pair_before_cross_page():
    views = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-003", "evidence_class": "object_evidence", "page_number": 1},
    ]
    edges, audit = compile_detection_v5_dimension_graph([
        {"group_id": "view-001", "occurrences": [_occurrence("a", 3310, "SF1")]},
        {"group_id": "view-002", "occurrences": [_occurrence("b", 3310, "SF2")]},
        {"group_id": "view-003", "occurrences": [_occurrence("c", 3310, "SF3")]},
    ], visual_groups=views)
    assert [(edge["group_id_a"], edge["group_id_b"], edge["cycle"]) for edge in edges] == [
        ("view-001", "view-002", "same_page_all_to_all"),
        ("view-001", "view-003", "same_page_all_to_all"),
        ("view-002", "view-003", "same_page_all_to_all"),
    ]
    assert audit["dimension_edge_threshold"] == 25.0
    assert audit["compiler_version"] == "v5_10_4_same_page_all_pairs_threshold_25"
    assert audit["provisional_components"] == [["view-001", "view-002", "view-003"]]


def test_v5_final_dimension_scores_all_same_page_pairs_despite_candidate_q():
    views = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-003", "evidence_class": "object_evidence", "page_number": 1},
    ]
    inventory = [
        {"group_id": "view-001", "occurrences": [_occurrence("a", 3310, "SF1")]},
        {"group_id": "view-002", "occurrences": [_occurrence("b", 3310, "SF2")]},
        {"group_id": "view-003", "occurrences": [_occurrence("c", 3310, "SF3")]},
    ]
    edges, audit = compile_detection_v5_dimension_graph(
        inventory, visual_groups=views,
        allowed_pairs={("view-001", "view-002")},
    )
    assert [(edge["group_id_a"], edge["group_id_b"], edge["cycle"]) for edge in edges] == [
        ("view-001", "view-002", "same_page_all_to_all"),
        ("view-001", "view-003", "same_page_all_to_all"),
        ("view-002", "view-003", "same_page_all_to_all"),
    ]
    assert audit["compiler_version"] == "v5_10_6_final_same_page_all_pairs_q_cross_page_threshold_25"


def test_v5_merge_does_not_inspect_pairs_without_existing_q_evidence():
    views = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-003", "evidence_class": "object_evidence", "page_number": 1},
    ]
    edges, audit = compile_detection_v5_merge_edges([], [{
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "explicit_document_relation", "strength": "direct",
        "observation": "Author callout A-3 identifies both views.", "source_fact_ids": ["SF1"],
    }], visual_groups=views)
    assert [(edge["group_id_a"], edge["group_id_b"]) for edge in edges] == [
        ("view-001", "view-002"),
    ]
    assert all({row["group_id_a"], row["group_id_b"]} != {"view-001", "view-003"} for row in audit["edges"])


def test_v5_generic_semantic_fact_is_rejected_without_stopping_graph():
    accepted, audit = compile_detection_v5_semantic_facts([
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "Both are elevations on the same page.", "source_fact_ids": []},
    ], visual_groups=VIEWS, source_facts=[])
    assert accepted == []
    assert audit["rejected"][0]["reason"] == "generic_observation"


def test_v5_document_relation_requires_direct_or_single_sheet_strength():
    accepted, audit = compile_detection_v5_semantic_facts([{
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "explicit_document_relation", "strength": "standard",
        "observation": "The material list specifies plywood and veneer for the cabinet.",
        "source_fact_ids": ["SF-001"],
    }], visual_groups=VIEWS, source_facts=[{"fact_id": "SF-001"}])
    assert accepted == []
    assert audit["rejected"][0]["reason"] == "document_relation_requires_direct_strength"


def test_v5103_known_bracketed_source_id_is_canonicalized_and_audited():
    accepted, audit = compile_detection_v5_semantic_facts([{
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "matching_topology", "strength": "standard",
        "observation": "The same 358mm two-bay carcass recurs in both views.",
        "source_fact_ids": ["[SF00202]"],
    }], visual_groups=VIEWS, source_facts=[{"fact_id": "SF00202"}])

    assert accepted[0]["source_fact_ids"] == ["SF00202"]
    assert audit["source_id_normalizations"] == [{
        "index": 0,
        "group_id_a": "view-001",
        "group_id_b": "view-002",
        "original_source_fact_id": "[SF00202]",
        "canonical_source_fact_id": "SF00202",
        "reason": "known_source_id_display_wrapper",
    }]


def test_v5103_unknown_bracketed_source_id_remains_rejected():
    accepted, audit = compile_detection_v5_semantic_facts([{
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "matching_topology", "strength": "standard",
        "observation": "The same 358mm two-bay carcass recurs in both views.",
        "source_fact_ids": ["[SF00999]"],
    }], visual_groups=VIEWS, source_facts=[{"fact_id": "SF00202"}])

    assert accepted == []
    assert audit["rejected"][0]["reason"] == "unknown_source_fact"
    assert audit["source_id_normalizations"] == []


def test_v5_object_hypothesis_requires_distinct_non_overlapping_object_views():
    accepted, audit = compile_detection_v5_object_hypotheses([
        {"group_ids": ["view-001", "view-002"], "hypothesis_reason": "One cabinet in two projections.", "evidence": [{"evidence_type": "matching_topology"}]},
        {"group_ids": ["view-002", "view-003"], "hypothesis_reason": "Overlapping proposal.", "evidence": [{"evidence_type": "matching_topology"}]},
    ], visual_groups=[*VIEWS, {"group_id": "view-003", "evidence_class": "object_evidence"}])
    assert accepted[0]["group_ids"] == ["view-001", "view-002"]
    assert audit["rejected"][0]["reason"] == "object_hypothesis_overlaps"


def test_v571_single_concrete_visual_fact_builds_membership_proof_tree():
    edges, audit = compile_detection_v5_membership_edges(
        [{
            "group_id_a": "view-001", "group_id_b": "view-002",
            "membership_reason": "Two projections show the same three-bay cabinet.",
            "evidence": [{
                "evidence_type": "matching_topology", "strength": "standard",
                "observation": "The same three-bay carcass and door order recur.",
                "source_fact_ids": [],
            }],
        }],
        visual_groups=VIEWS, source_facts=[],
    )
    assert [(edge["group_id_a"], edge["group_id_b"]) for edge in edges] == [
        ("view-001", "view-002"),
    ]
    assert edges[0]["relationship"] == "same_object_view"
    assert edges[0]["membership_basis"] == "registry_full_page_membership_edge"
    assert audit["rejected"] == []


def test_v571_membership_edge_without_validated_fact_stays_unmerged():
    edges, audit = compile_detection_v5_membership_edges(
        [{
            "group_id_a": "view-001", "group_id_b": "view-002",
            "membership_reason": "One cabinet in two projections.",
            "evidence": [{"evidence_type": "matching_topology"}],
        }],
        visual_groups=VIEWS, source_facts=[],
    )
    assert edges == []
    assert audit["rejected"][0]["reason"] == (
        "membership_edge_has_no_validated_visual_fact"
    )


def test_v572_complete_hypothesis_is_deterministically_adapted_to_tree():
    views = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-003", "evidence_class": "object_evidence", "page_number": 1},
    ]
    hypotheses, _ = compile_detection_v5_object_hypotheses([{
        "group_ids": ["view-001", "view-002", "view-003"],
        "hypothesis_reason": "Three projections show one three-bay cabinet.",
        "evidence": [{
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        }],
    }], visual_groups=views)
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-001", "group_id_b": "view-002",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-001", "group_id_b": "view-003",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    edges, audit = compile_detection_v5_hypothesis_membership_edges(
        hypotheses, facts, visual_groups=views,
    )

    assert [(edge["group_id_a"], edge["group_id_b"]) for edge in edges] == [
        ("view-001", "view-002"), ("view-001", "view-003"),
    ]
    assert all(edge["membership_basis"] == "registry_full_page_hypothesis" for edge in edges)
    assert audit["compiler_version"] == "v5_7_registry_membership_proof_tree"


def test_v571_supporting_graph_cannot_override_registry_membership():
    facts = [
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "The same three-bay carcass and door order recur.", "source_fact_ids": []},
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "unique_geometry", "strength": "standard", "observation": "The same offset circular cut-out and handle layout recur.", "source_fact_ids": []},
    ]
    edges, audit = compile_detection_v5_merge_edges(
        [], facts, visual_groups=VIEWS, allow_runtime_merges=False,
    )
    assert edges[0]["relationship"] == "supporting_relation"
    assert audit["compiler_version"] == "v5_7_supporting_graph_only"


def test_v561_dominant_page_attaches_only_one_orphan():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence", "page_number": 1}
        for index in range(1, 8)
    ]
    base_components = [[view["group_id"] for view in views[:-1]], [views[-1]["group_id"]]]
    edges, attachment_audit = derive_detection_v5_dominant_page_attachment_edges(
        base_components, visual_groups=views,
    )
    assert [(edge["group_id_a"], edge["group_id_b"]) for edge in edges] == [("view-001", "view-007")]
    assert attachment_audit[0]["attached_group_ids"] == ["view-007"]


def test_v561_dominant_page_does_not_attach_with_competing_package_or_orphans():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence", "page_number": 1}
        for index in range(1, 9)
    ]
    edges, audit = derive_detection_v5_dominant_page_attachment_edges(
        [["view-001", "view-002", "view-003", "view-004", "view-005", "view-006"], ["view-007"], ["view-008"]],
        visual_groups=views,
    )
    assert edges == []
    assert audit[0]["attached_group_ids"] == []


def test_v5_direct_shared_structure_cannot_be_generic_material_or_hardware():
    accepted, audit = compile_detection_v5_semantic_facts([
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "direct_shared_structure", "strength": "standard", "observation": "Both use the same material and hardware specification.", "source_fact_ids": []},
    ], visual_groups=VIEWS, source_facts=[])
    assert accepted == []
    assert audit["rejected"][0]["reason"] == "direct_shared_structure_requires_physical_witness"


def test_v5_concrete_topology_is_not_rejected_for_saying_both_elevations():
    accepted, audit = compile_detection_v5_semantic_facts([
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "Both elevations share a 358mm width and the same two-bay carcass.", "source_fact_ids": []},
    ], visual_groups=VIEWS, source_facts=[])
    assert audit["rejected"] == []
    assert len(accepted) == 1


def test_v5_large_dimension_plus_topology_is_merge_grade():
    dimension_edges, _ = compile_detection_v5_dimension_graph(
        _fingerprints([_occurrence("a", 3310, "SF1")], [_occurrence("b", 3310, "SF2")]),
        visual_groups=VIEWS,
    )
    semantic, _ = compile_detection_v5_semantic_facts([
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "The same two-bay carcass and door order recur.", "source_fact_ids": []},
    ], visual_groups=VIEWS, source_facts=[])
    edges, _ = compile_detection_v5_merge_edges(dimension_edges, semantic)
    assert edges[0]["relationship"] == "same_object_view"


def test_v5_standard_document_relation_is_identity_support_not_an_extra_weight():
    edges, _ = compile_detection_v5_merge_edges([], [{
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "explicit_document_relation", "strength": "standard",
        "observation": "Plan callout A-3 references the elevation.", "source_fact_ids": ["SF1"],
    }])
    assert edges[0]["edge_score"] == 0
    assert edges[0]["relationship"] == "supporting_relation"


def test_v5_two_independent_semantic_facts_merge_without_dimension_overlap():
    facts = [
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "The same three-bay carcass and door order recur.", "source_fact_ids": []},
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "unique_geometry", "strength": "standard", "observation": "The same offset circular cut-out and handle layout recur.", "source_fact_ids": []},
    ]
    edges, audit = compile_detection_v5_merge_edges([], facts, visual_groups=VIEWS)
    assert edges[0]["relationship"] == "same_object_view"
    assert audit["compiler_version"] == "v5_5_global_semantic_proof_forest"


def test_v5_progressive_merge_queue_skips_redundant_internal_pair():
    views = [
        {"group_id": "view-001", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-002", "evidence_class": "object_evidence", "page_number": 1},
        {"group_id": "view-003", "evidence_class": "object_evidence", "page_number": 1},
    ]
    facts = [
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "explicit_document_relation", "strength": "direct", "observation": "Author label A identifies both views.", "source_fact_ids": ["SF1"]},
        {"group_id_a": "view-001", "group_id_b": "view-003", "evidence_type": "explicit_document_relation", "strength": "direct", "observation": "Author label A identifies the third view.", "source_fact_ids": ["SF2"]},
        {"group_id_a": "view-002", "group_id_b": "view-003", "evidence_type": "matching_topology", "strength": "standard", "observation": "Same two-bay carcass.", "source_fact_ids": []},
    ]
    edges, audit = compile_detection_v5_merge_edges([], facts, visual_groups=views)
    assert {(edge["group_id_a"], edge["group_id_b"]) for edge in edges} == {
        ("view-001", "view-002"), ("view-001", "view-003"),
    }
    assert any(row.get("skipped") == "internal_package_pair" for row in audit["edges"])


def test_v5_infers_centimetres_from_nonstandard_bare_object_dimension():
    unit, reason = infer_detection_v5_bare_dimension_unit([
        {"source_facts": [{"text": "331"}, {"text": "60"}]},
    ], document_unit="unknown")
    assert (unit, reason) == ("cm", "nonstandard_100_to_600_value")


def test_v5_leaves_common_only_bare_values_unresolved():
    unit, reason = infer_detection_v5_bare_dimension_unit([
        {"source_facts": [{"text": "600"}, {"text": "60"}]},
    ], document_unit="unknown")
    assert (unit, reason) == ("unknown", "insufficient_bare_dimension_context")


def test_v5_final_validation_accepts_singleton_packages_and_supporting_edge():
    registry = {"objects": [
        {"object_id": "object-001", "transport_label": "View 1", "quantity": 1,
         "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1],
         "visual_group_ids": ["view-001"], "visual_identity": "view", "boundary_basis": "standalone"},
        {"object_id": "object-002", "transport_label": "View 2", "quantity": 1,
         "quantity_explicit": False, "identity_pages": [1], "estimation_evidence_pages": [1],
         "visual_group_ids": ["view-002"], "visual_identity": "view", "boundary_basis": "standalone"},
    ]}
    assert validate_detection_v5_final_result(
        registry, visual_groups=VIEWS,
        graph_edges=[{"group_id_a": "view-001", "group_id_b": "view-002", "relationship": "supporting_relation", "evidence_facts": [{"source_fact_ids": []}]}],
        source_facts=[],
    ) == registry
