from agents.schemas.detection_registry_schema import (
    compile_detection_v5_dimension_graph,
    compile_detection_v5_merge_edges,
    compile_detection_v5_semantic_facts,
    validate_detection_v5_final_result,
)


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


def test_v5_generic_semantic_fact_is_rejected_without_stopping_graph():
    accepted, audit = compile_detection_v5_semantic_facts([
        {"group_id_a": "view-001", "group_id_b": "view-002", "evidence_type": "matching_topology", "strength": "standard", "observation": "Both are elevations on the same page.", "source_fact_ids": []},
    ], visual_groups=VIEWS, source_facts=[])
    assert accepted == []
    assert audit["rejected"][0]["reason"] == "generic_observation"


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
