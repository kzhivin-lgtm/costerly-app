from agents.schemas.detection_registry_schema import (
    compile_detection_v5_dimension_graph,
    compile_detection_v5_hypothesis_membership_edges,
    compile_detection_v637_hypothesis_coverage_components,
    compile_detection_v5_merge_edges,
    compile_detection_v5_membership_edges,
    compile_detection_v5_object_hypotheses,
    partition_detection_presentation_render_components,
    partition_detection_unattached_technical_views,
    derive_detection_v5_dominant_page_attachment_edges,
    compile_detection_v5_semantic_facts,
    validate_detection_v5_final_result,
)
from agents.detection_dimension_anchors import dimension_anchors
from agents import detection_ordinary_membership
from agents.anthropic_adapter import (
    _grounded_same_page_hypothesis_facts,
    build_detection_v5_dimension_fingerprints,
    infer_detection_v5_bare_dimension_unit,
)


VIEWS = [
    {"group_id": "view-001", "evidence_class": "object_evidence"},
    {"group_id": "view-002", "evidence_class": "object_evidence"},
]


def test_attached_technical_view_remains_product_evidence():
    published, excluded = partition_detection_unattached_technical_views(
        [["fixture", "elevation"], ["unattached"], ["fabrication-plan"]],
        visual_groups=[
            {"group_id": "fixture", "representation_kind": "technical_plan_detail"},
            {"group_id": "elevation", "representation_kind": "elevation"},
            {"group_id": "unattached", "representation_kind": "location_plan"},
            {"group_id": "fabrication-plan", "representation_kind": "plan"},
        ],
    )
    assert published == [["fixture", "elevation"], ["fabrication-plan"]]
    assert excluded == ["unattached"]


def test_presentation_render_components_require_a_technical_view():
    components, excluded, audit = partition_detection_presentation_render_components(
        [
            ["view-001"],
            ["view-002", "view-003"],
            ["view-004", "view-005"],
        ],
        visual_groups=[
            {"group_id": "view-001", "representation_kind": "presentation_render"},
            {"group_id": "view-002", "representation_kind": "presentation_render"},
            {"group_id": "view-003", "representation_kind": "presentation_render"},
            {"group_id": "view-004", "representation_kind": "presentation_render"},
            {"group_id": "view-005", "representation_kind": "technical_elevation"},
        ],
    )

    assert components == [["view-004", "view-005"]]
    assert excluded == ["view-001", "view-002", "view-003"]
    assert audit == [{
        "group_ids": ["view-001"],
        "disposition": "excluded_unattached_presentation_render",
        "reason": "Presentation render/photo has no proven technical View in its component.",
    }, {
        "group_ids": ["view-002", "view-003"],
        "disposition": "excluded_unattached_presentation_render",
        "reason": "Presentation render/photo has no proven technical View in its component.",
    }]


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


def test_v5_dimension_anchor_requires_a_preverified_pair_on_the_same_page():
    pair = ("view-001", "view-002")
    edge = {
        "group_id_a": pair[0], "group_id_b": pair[1],
        "dimension_similarity_score": 100.0,
        "evidence_facts": [{"evidence_type": "dimension_equality", "source_fact_ids": ["SF1", "SF2"]}],
    }
    views = [dict(view, page_number=1) for view in VIEWS]
    default, _ = compile_detection_v5_merge_edges([edge], [], visual_groups=views)
    verified, audit = compile_detection_v5_merge_edges(
        [edge], [], visual_groups=views, dimension_anchor_pairs={pair},
    )
    cross_page, _ = compile_detection_v5_merge_edges(
        [edge], [], visual_groups=[views[0], dict(views[1], page_number=2)], dimension_anchor_pairs={pair},
    )
    blocked, _ = compile_detection_v5_merge_edges(
        [edge], [], visual_groups=views, dimension_anchor_pairs={pair}, merge_blocked_pairs={pair: "conflict"},
    )

    assert default[0]["relationship"] == "supporting_relation"
    assert verified[0]["relationship"] == "same_object_view"
    assert audit["edges"][0]["dimension_anchor"] is True
    assert cross_page[0]["relationship"] == "supporting_relation"
    assert blocked[0]["relationship"] == "supporting_relation"


def test_v5_dimension_anchor_recognizes_repeated_sections_with_an_independent_total():
    def chain(prefix, total_centre=0.5):
        rows = [
            _occurrence(f"{prefix}-{index}", value, f"{prefix}-source-{index}")
            for index, value in enumerate([1840, 1840, 1840, 5510])
        ]
        for row, x, y in zip(rows, [0.25, 0.5, 0.75, total_centre], [0.8, 0.8, 0.8, 0.2], strict=True):
            row["normalized_bbox"] = {
                "top_left_x": x - 0.01, "bottom_right_x": x + 0.01,
                "top_left_y": y - 0.01, "bottom_right_y": y + 0.01,
            }
        return rows

    left, right = chain("left"), chain("right")
    inventory = _fingerprints(left, right)
    inventory.append({"group_id": "other", "occurrences": chain("other")[:3]})
    candidate = {
        "group_id_a": "view-001", "group_id_b": "view-002", "same_page": True,
        "dimension_similarity_score": 100, "features": [{"left_mm": "5510", "right_mm": "5510"}],
    }
    audit = {"dimension_inventory": inventory, "dimension_graph_audit": {"dimension_similarity_candidates": [candidate]}}
    eligible = {"view-001", "view-002"}
    proof, = dimension_anchors(audit, eligible)
    assert proof["corroborating_repeated_chains"] == [{"total_mm": "5510", "span_mm": "1840", "count": 3}]
    inventory[1]["occurrences"] = chain("right", total_centre=0.8)
    assert dimension_anchors(audit, eligible) == []
    inventory[1]["occurrences"] = chain("right")[:-2] + chain("right")[-1:]
    assert dimension_anchors(audit, eligible) == []
    inventory[1]["occurrences"] = left
    assert dimension_anchors(audit, eligible) == []


def test_common_large_extent_needs_a_matching_independent_dimension_sequence():
    def view(group, spans):
        occurrences = []
        for index, (value, x, y) in enumerate(spans):
            source = f"{group}-{index}"
            occurrence = _occurrence(source, value, source)
            occurrence["normalized_bbox"] = {
                "top_left_x": x - 0.01, "bottom_right_x": x + 0.01,
                "top_left_y": y - 0.01, "bottom_right_y": y + 0.01,
            }
            occurrences.append(occurrence)
        return {"group_id": group, "occurrences": occurrences}

    sequence = [(430, 0.2, 0.8), (860, 0.5, 0.8), (2700, 0.3, 0.2)]
    inventory = [view("a", sequence), view("b", sequence), view("c", sequence[-1:])]
    candidate = {
        "group_id_a": "a", "group_id_b": "b", "same_page": True,
        "dimension_similarity_score": 100, "features": [{"left_mm": "2700", "right_mm": "2700"}],
    }
    usage = {"dimension_inventory": inventory, "dimension_graph_audit": {"dimension_similarity_candidates": [candidate]}}
    proof, = dimension_anchors(usage, {"a", "b"})
    assert proof["rare_exact_extents_mm"] == []
    assert proof["requires_common_extent"]
    assert proof["corroborating_ordered_spans_mm"] == [["430", "860"]]

    inventory[1] = view("b", [sequence[0], (860, 0.5, 0.5), sequence[2]])
    assert dimension_anchors(usage, {"a", "b"}) == []


def test_common_extent_bridge_cannot_cancel_existing_rare_anchors(monkeypatch):
    def proof(left, right, common=False):
        return {
            "group_id_a": left, "group_id_b": right, "relationship": "same_object_view",
            "requires_common_extent": common,
        }

    existing = [proof("a", "b"), proof("c", "d")]
    bridge = proof("b", "c", common=True)
    independent = proof("e", "f", common=True)
    monkeypatch.setattr(
        detection_ordinary_membership, "dimension_anchors", lambda *_: [*existing, bridge, independent],
    )
    group_ids = list("abcdef")
    rare, common = detection_ordinary_membership.dimension_recovery_edges(
        {}, set(group_ids), [[group] for group in group_ids],
    )
    assert rare == existing
    assert common == [independent]


def test_short_view_requires_a_unique_confirmed_group_with_complementary_dimensions():
    views = [{"group_id": group, "page_number": 1} for group in ("a", "b", "c", "d", "short")]
    inventory = [
        {"group_id": group, "occurrences": [
            _occurrence(f"{group}-{i}", value, f"{group}-source-{i}")
            for i, value in enumerate(values)
        ]}
        for group, values in {
            "a": [600, 1750, 2000], "b": [1100, 1750, 2000],
            "c": [600, 1500, 2150], "d": [1100, 1500, 2150],
            "short": [600, 1100],
        }.items()
    ]
    edges, _ = compile_detection_v5_dimension_graph(inventory, visual_groups=views, allowed_pairs=set())
    def direct(left, right):
        return {
            "group_id_a": left, "group_id_b": right, "evidence_type": "explicit_document_relation",
            "strength": "direct", "observation": "Authored view reference", "source_fact_ids": ["reference"],
        }

    opts = {"visual_groups": views, "allow_short_fingerprint_attachment": True, "allow_batch_confirmation": False}
    _, accepted = compile_detection_v5_merge_edges(edges, [direct("a", "b")], **opts)
    attachments = [r["short_fingerprint_attachment"] for r in accepted["edges"] if "short_fingerprint_attachment" in r]
    assert len(attachments) == 1
    assert attachments[0]["distinct_exact_values_mm"] == ["600", "1100"]
    assert attachments[0]["supporting_pairs"] == [["a", "short"], ["b", "short"]]

    _, ambiguous = compile_detection_v5_merge_edges(edges, [direct("a", "b"), direct("c", "d")], **opts)
    assert not any("short_fingerprint_attachment" in row for row in ambiguous["edges"])
    _, blocked = compile_detection_v5_merge_edges(
        edges, [direct("a", "b")], merge_blocked_pairs={("b", "short"): "contradiction"}, **opts,
    )
    assert not any("short_fingerprint_attachment" in row for row in blocked["edges"])


def test_a_single_position_gets_the_strongest_short_fingerprint_weight():
    views = [{"group_id": group, "page_number": 1} for group in ("a", "b")]
    controls = []
    for i in range(4):
        group_id = f"control-{i}"
        views.append({"group_id": group_id, "page_number": i + 2})
        controls.append({
            "group_id": group_id, "occurrences": [_occurrence(group_id, 600, f"{group_id}-source")],
        })
    for position_count in range(1, 6):
        values = [600, *range(2500, 2500 + position_count - 1)]
        inventory = [
            {"group_id": "a", "occurrences": [
                _occurrence(f"a-{i}", value, f"a-source-{i}") for i, value in enumerate(values)
            ]},
            {"group_id": "b", "occurrences": [
                _occurrence(f"b-{i}", value, f"b-source-{i}")
                for i, value in enumerate([600, 1000, 1200, 1400, 1600])
            ]},
        ]
        _, audit = compile_detection_v5_dimension_graph(
            inventory + controls, visual_groups=views, allowed_pairs=set(),
        )
        candidate, = audit["dimension_similarity_candidates"]
        bonus = candidate.get("short_fingerprint_bonus")
        if position_count == 5:
            assert bonus is None
        else:
            assert bonus["shorter_position_count"] == position_count
            expected = 22.2 if position_count == 1 else round(25.6 / position_count, 3)
            assert bonus["added_points"] == expected


def test_one_large_near_match_needs_two_independent_peers_in_one_confirmed_group():
    def verify(*, confirmed=True, duplicate=False, competitor=False, blocked=False, outside_tolerance=False):
        values = {"a": [3450, 900], "b": [3450, 1300], "plan": [3490 if not outside_tolerance else 3600]}
        if competitor:
            values["other"] = [3450, 1800]
        views = [{"group_id": group, "page_number": 1} for group in values]
        inventory = [
            {"group_id": group, "occurrences": [
                _occurrence(
                    f"{group}-{i}", value,
                    "same-print" if duplicate and group in {"a", "b"} and i == 0 else f"{group}-source-{i}",
                )
                for i, value in enumerate(dimensions)
            ]}
            for group, dimensions in values.items()
        ]
        dim_edges, _ = compile_detection_v5_dimension_graph(inventory, visual_groups=views, allowed_pairs=set())
        facts = [{
            "group_id_a": "a", "group_id_b": "b", "evidence_type": "explicit_document_relation",
            "strength": "direct", "observation": "Authored view reference", "source_fact_ids": ["reference"],
        }] if confirmed else []
        _, audit = compile_detection_v5_merge_edges(
            dim_edges, facts, visual_groups=views, allow_short_fingerprint_attachment=True,
            merge_blocked_pairs={("b", "plan"): "contradiction"} if blocked else {},
        )
        return [
            (row, row["short_fingerprint_attachment"])
            for row in audit["edges"] if "short_fingerprint_attachment" in row
        ]

    (edge, witness), = verify()
    assert edge["dimension_similarity_score"] == 40
    assert witness["short_position_count"] == 1
    assert witness["base_score"] == 35
    assert witness["added_points"] == 5
    assert witness["supporting_pairs"] == [["a", "plan"], ["b", "plan"]]
    assert [match["peer_source_fact_ids"] for match in witness["single_position_matches"]] == [
        ["a-source-0"], ["b-source-0"],
    ]
    for control in (
        {"confirmed": False}, {"duplicate": True}, {"competitor": True},
        {"blocked": True}, {"outside_tolerance": True},
    ):
        assert verify(**control) == [], control


def test_v5_strong_cited_pair_in_a_hypothesis_keeps_its_witness():
    evidence = {
        "evidence_type": "unique_geometry", "strength": "standard",
        "observation": "Both elevations correspond to the legs of the corner on the plan.",
        "source_fact_ids": ["registry_view:raw-1", "registry_view:raw-2", "registry_view:raw-3"],
    }
    hypothesis = {"group_ids": ["plan", "left", "right", "render"], "evidence": [evidence]}
    candidate = {"group_id_a": "left", "group_id_b": "right", "same_page": True, "dimension_similarity_score": 100}
    mapping = {"raw-1": "plan", "raw-2": "left", "raw-3": "right"}
    options = {
        "group_id_mapping": mapping, "render_group_ids": {"render"},
        "source_fact_owners": {"SF1": "left", "SF2": "right", "SF3": "plan"},
    }
    assert _grounded_same_page_hypothesis_facts([hypothesis], [candidate], **options) == [
        {"group_id_a": "left", "group_id_b": "right", **evidence},
    ]
    assert _grounded_same_page_hypothesis_facts([hypothesis], [{**candidate, "same_page": False}], **options) == []
    assert _grounded_same_page_hypothesis_facts(
        [hypothesis], [{**candidate, "group_id_b": "render"}], **options,
    ) == []
    evidence["source_fact_ids"].pop()
    assert _grounded_same_page_hypothesis_facts([hypothesis], [candidate], **options) == []
    evidence["source_fact_ids"] = ["SF1", "SF2"]
    assert _grounded_same_page_hypothesis_facts([hypothesis], [candidate], **options) == [
        {"group_id_a": "left", "group_id_b": "right", **evidence},
    ]
    evidence["source_fact_ids"] = ["SF1", "SF3"]
    assert _grounded_same_page_hypothesis_facts([hypothesis], [candidate], **options) == []


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


def test_short_fingerprint_promotes_same_page_exact_match_to_support_only():
    views = [dict(view, page_number=1) for view in VIEWS]
    inventory = _fingerprints(
        [_occurrence("a1", 600, "SF1"), _occurrence("a2", 1100, "SF2")],
        [_occurrence("b1", 600, "SF3"), _occurrence("b2", 1660, "SF4")],
    )
    for i in range(4):
        group_id = f"control-{i}"
        views.append({"group_id": group_id, "page_number": i + 3})
        inventory.append({
            "group_id": group_id,
            "occurrences": [_occurrence(group_id, 600, f"SF{i + 5}")],
        })
    pair = ("view-001", "view-002")

    edges, audit = compile_detection_v5_dimension_graph(
        inventory, visual_groups=views, allowed_pairs={pair},
    )
    assert len(edges) == 1
    assert edges[0]["dimension_similarity_score"] == 25.6
    assert audit["dimension_similarity_candidates"][0]["short_fingerprint_bonus"] == {
        "shorter_position_count": 2, "exact_matched_positions": 1,
        "base_score": 12.8, "added_points": 12.8,
    }
    # Even an existing identity edge at one endpoint must not turn this
    # single shared dimension into a batch merge.
    existing = [{
        "group_id_a": "control-0", "group_id_b": "view-001",
        "evidence_type": "explicit_document_relation", "strength": "direct",
        "observation": "Explicit author reference", "source_fact_ids": ["SF1"],
    }]
    graph, _ = compile_detection_v5_merge_edges(edges, existing, visual_groups=views)
    assert [e["relationship"] for e in graph if (e["group_id_a"], e["group_id_b"]) == pair] == [
        "supporting_relation",
    ]

    cross_page_views = [views[0], dict(views[1], page_number=2), *views[2:]]
    cross_edges, _ = compile_detection_v5_dimension_graph(
        inventory, visual_groups=cross_page_views, allowed_pairs={pair},
    )
    assert cross_edges == []

    for row, start in zip(inventory[:2], (2500, 6000), strict=True):
        row["occurrences"].extend(
            _occurrence(f"{row['group_id']}-{i}", start + i * 140, f"extra-{start}-{i}")
            for i in range(13)
        )
    dense_edges, dense_audit = compile_detection_v5_dimension_graph(
        inventory, visual_groups=views, allowed_pairs={pair},
    )
    assert dense_edges == []
    assert dense_audit["dimension_similarity_candidates"][0]["dimension_similarity_score"] == 12.8


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


def test_v635_pair_local_semantic_fact_requires_both_view_sources():
    source_facts = [
        {"fact_id": "registry_view:view-001"},
        {"fact_id": "registry_view:view-002"},
        {"fact_id": "registry_view:view-003"},
    ]
    fact = {
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "matching_topology", "strength": "standard",
        "observation": "The same three-bay carcass and door order recur.",
        "source_fact_ids": ["registry_view:view-001", "registry_view:view-003"],
    }

    accepted, audit = compile_detection_v5_semantic_facts(
        [fact], visual_groups=VIEWS, source_facts=source_facts,
        require_pair_endpoint_visual_sources=True,
    )

    assert accepted == []
    assert audit["rejected"] == [{
        "index": 0,
        "reason": "pair_endpoint_visual_sources_missing",
        "required_source_fact_ids": [
            "registry_view:view-001", "registry_view:view-002",
        ],
        "source_fact_ids": [
            "registry_view:view-001", "registry_view:view-003",
        ],
    }]


def test_v635_document_relation_is_context_not_merge_evidence():
    fact = {
        "group_id_a": "view-001", "group_id_b": "view-002",
        "evidence_type": "explicit_document_relation", "strength": "direct",
        "observation": "The shared title block names a common project for both views.",
        "source_fact_ids": ["registry_view:view-001", "registry_view:view-002"],
    }

    accepted, audit = compile_detection_v5_semantic_facts(
        [fact], visual_groups=VIEWS,
        source_facts=[
            {"fact_id": "registry_view:view-001"},
            {"fact_id": "registry_view:view-002"},
        ],
        require_pair_endpoint_visual_sources=True,
        reject_document_relation_for_merge=True,
    )

    assert accepted == []
    assert audit["rejected"] == [{
        "index": 0,
        "reason": "document_relation_is_context_not_merge_evidence",
    }]


def test_v5_object_hypothesis_requires_distinct_non_overlapping_object_views():
    accepted, audit = compile_detection_v5_object_hypotheses([
        {"group_ids": ["view-001", "view-002"], "hypothesis_reason": "One cabinet in two projections.", "evidence": [{"evidence_type": "matching_topology"}]},
        {"group_ids": ["view-002", "view-003"], "hypothesis_reason": "Overlapping proposal.", "evidence": [{"evidence_type": "matching_topology"}]},
    ], visual_groups=[*VIEWS, {"group_id": "view-003", "evidence_class": "object_evidence"}])
    assert accepted[0]["group_ids"] == ["view-001", "view-002"]
    assert audit["rejected"][0]["reason"] == "object_hypothesis_overlaps"


def test_v847_star_hypotheses_coalesce_only_after_each_pair_has_local_proof():
    views = [
        {"group_id": "view-plan", "evidence_class": "object_evidence"},
        {"group_id": "view-left", "evidence_class": "object_evidence"},
        {"group_id": "view-right", "evidence_class": "object_evidence"},
    ]
    hypotheses, hypothesis_audit = compile_detection_v5_object_hypotheses([
        {
            "group_ids": ["view-plan", "view-left"],
            "hypothesis_reason": "The plan and left elevation share the corner run.",
            "evidence": [{"evidence_type": "matching_topology"}],
        },
        {
            "group_ids": ["view-plan", "view-right"],
            "hypothesis_reason": "The plan and right elevation share the tower run.",
            "evidence": [{"evidence_type": "unique_geometry"}],
        },
    ], visual_groups=views, allow_star_overlaps=True)
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-plan", "group_id_b": "view-left",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same corner cabinet run appears in both Views.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-plan", "group_id_b": "view-right",
            "evidence_type": "unique_geometry", "strength": "standard",
            "observation": "The same tall end unit appears in both Views.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    components, component_audit = compile_detection_v637_hypothesis_coverage_components(
        hypotheses, facts, visual_groups=views, allow_star_hypothesis_components=True,
    )

    assert len(hypotheses) == 2
    assert hypothesis_audit["star_overlap_components"] == [{
        "hypothesis_indexes": [0, 1],
        "shared_anchor_group_ids": ["view-plan"],
        "group_ids": ["view-left", "view-plan", "view-right"],
    }]
    assert components == [["view-left", "view-plan", "view-right"]]
    assert component_audit["star_hypothesis_components"]["components"] == [{
        "hypothesis_indexes": [0, 1],
        "shared_anchor_group_ids": ["view-plan"],
        "group_ids": ["view-left", "view-plan", "view-right"],
        "status": "coalesced_after_pair_local_proof",
    }]


def test_v847_does_not_promote_a_chain_of_overlapping_hypotheses_to_one_object():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence"}
        for index in range(1, 5)
    ]
    hypotheses, audit = compile_detection_v5_object_hypotheses([
        {
            "group_ids": ["view-001", "view-002"],
            "hypothesis_reason": "First pair.",
            "evidence": [{"evidence_type": "matching_topology"}],
        },
        {
            "group_ids": ["view-002", "view-003"],
            "hypothesis_reason": "Middle pair.",
            "evidence": [{"evidence_type": "matching_topology"}],
        },
        {
            "group_ids": ["view-003", "view-004"],
            "hypothesis_reason": "Last pair.",
            "evidence": [{"evidence_type": "matching_topology"}],
        },
    ], visual_groups=views, allow_star_overlaps=True)

    assert [item["group_ids"] for item in hypotheses] == [
        ["view-001", "view-002"], ["view-003", "view-004"],
    ]
    assert audit["star_overlap_components"] == []
    assert audit["rejected"] == [{
        "index": 1,
        "reason": "object_hypothesis_overlap_not_star_shaped",
        "group_ids": ["view-002"],
    }]


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
    assert all(
        edge["membership_basis"] == "registry_pair_local_connected_hypothesis"
        for edge in edges
    )
    assert audit["compiler_version"] == "v6_36_registry_pair_local_membership_tree"


def test_v636_membership_tree_keeps_only_the_model_cited_local_pairs():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence", "page_number": index}
        for index in range(1, 5)
    ]
    hypotheses, _ = compile_detection_v5_object_hypotheses([{
        "group_ids": ["view-001", "view-002", "view-003", "view-004"],
        "hypothesis_reason": "Four projections show the same cabinet.",
        "evidence": [{
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same bays recur.", "source_fact_ids": [],
        }],
    }], visual_groups=views)
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-001", "group_id_b": "view-004",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-002", "group_id_b": "view-003",
            "evidence_type": "unique_geometry", "strength": "standard",
            "observation": "The same offset circular cut-out and handle layout recur.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-003", "group_id_b": "view-004",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same shelf bays and return panel recur.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    edges, audit = compile_detection_v5_hypothesis_membership_edges(
        hypotheses, facts, visual_groups=views,
    )

    assert [(edge["group_id_a"], edge["group_id_b"]) for edge in edges] == [
        ("view-001", "view-004"),
        ("view-002", "view-003"),
        ("view-003", "view-004"),
    ]
    assert audit["rejected"] == []


def test_v636_membership_tree_rejects_disconnected_pair_local_evidence():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence", "page_number": index}
        for index in range(1, 5)
    ]
    hypotheses, _ = compile_detection_v5_object_hypotheses([{
        "group_ids": ["view-001", "view-002", "view-003", "view-004"],
        "hypothesis_reason": "Four projections show the same cabinet.",
        "evidence": [{
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same bays recur.", "source_fact_ids": [],
        }],
    }], visual_groups=views)
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-001", "group_id_b": "view-004",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-002", "group_id_b": "view-003",
            "evidence_type": "unique_geometry", "strength": "standard",
            "observation": "The same offset circular cut-out and handle layout recur.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    edges, audit = compile_detection_v5_hypothesis_membership_edges(
        hypotheses, facts, visual_groups=views,
    )

    assert edges == []
    assert audit["rejected"][0]["reason"] == (
        "membership_hypothesis_pair_local_graph_disconnected"
    )


def test_v637_hypothesis_coverage_accepts_complementary_disconnected_pairs():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence"}
        for index in range(1, 5)
    ]
    hypotheses, _ = compile_detection_v5_object_hypotheses([{
        "group_ids": ["view-001", "view-002", "view-003", "view-004"],
        "hypothesis_reason": "Complementary projections show one cabinet.",
        "evidence": [{
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same cabinet bays recur.", "source_fact_ids": [],
        }],
    }], visual_groups=views)
    facts, _ = compile_detection_v5_semantic_facts([
        {
            "group_id_a": "view-001", "group_id_b": "view-004",
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same three-bay carcass and door order recur.",
            "source_fact_ids": [],
        },
        {
            "group_id_a": "view-002", "group_id_b": "view-003",
            "evidence_type": "unique_geometry", "strength": "standard",
            "observation": "The same offset circular cut-out and handle layout recur.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    components, audit = compile_detection_v637_hypothesis_coverage_components(
        hypotheses, facts, visual_groups=views,
    )

    assert components == [["view-001", "view-002", "view-003", "view-004"]]
    assert audit["rejected"] == []


def test_v637_hypothesis_coverage_rejects_an_uncovered_view():
    views = [
        {"group_id": f"view-00{index}", "evidence_class": "object_evidence"}
        for index in range(1, 5)
    ]
    hypotheses, _ = compile_detection_v5_object_hypotheses([{
        "group_ids": ["view-001", "view-002", "view-003", "view-004"],
        "hypothesis_reason": "Complementary projections show one cabinet.",
        "evidence": [{
            "evidence_type": "matching_topology", "strength": "standard",
            "observation": "The same cabinet bays recur.", "source_fact_ids": [],
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
            "group_id_a": "view-002", "group_id_b": "view-003",
            "evidence_type": "unique_geometry", "strength": "standard",
            "observation": "The same offset circular cut-out and handle layout recur.",
            "source_fact_ids": [],
        },
    ], visual_groups=views, source_facts=[])

    components, audit = compile_detection_v637_hypothesis_coverage_components(
        hypotheses, facts, visual_groups=views,
    )

    assert components == []
    assert audit["rejected"] == [{
        "index": 0,
        "reason": "membership_hypothesis_pair_local_coverage_incomplete",
        "group_ids": ["view-001", "view-002", "view-003", "view-004"],
        "missing_group_ids": ["view-004"],
        "local_fact_pairs": [["view-001", "view-002"], ["view-002", "view-003"]],
    }]


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


def test_v5_impossible_numeric_reading_cannot_determine_the_document_unit():
    box = {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 100, "bottom_right_y": 50}
    packages = [{
        "visual_group_id": "view-001",
        "bbox": box,
        "source_facts": [
            {"text": "275", "fact_id": "SF001", "bbox": box},
            {"text": "999999999999", "fact_id": "SF002", "bbox": box},
        ],
    }]
    assert infer_detection_v5_bare_dimension_unit(packages, document_unit="unknown") == (
        "cm", "nonstandard_100_to_600_value",
    )
    fingerprint, = build_detection_v5_dimension_fingerprints(packages, document_unit="cm")
    assert [row["value_mm"] for row in fingerprint["occurrences"]] == ["2750"]
    assert fingerprint["excluded"] == [{"fact_id": "SF002", "reason": "implausible_object_span"}]


def test_v5_dimension_halo_reading_cannot_change_the_document_unit():
    box = {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 100, "bottom_right_y": 50}
    package = {
        "visual_group_id": "view-001", "bbox": box,
        "dimension_envelope_source_fact_ids": ["halo"],
        "source_facts": [
            {"text": "275", "fact_id": "inside", "bbox": box},
            {"text": "709", "fact_id": "halo", "bbox": box},
        ],
    }
    assert infer_detection_v5_bare_dimension_unit([package], document_unit="unknown") == (
        "cm", "nonstandard_100_to_600_value",
    )
    fingerprint, = build_detection_v5_dimension_fingerprints([package], document_unit="cm")
    assert [row["value_mm"] for row in fingerprint["occurrences"]] == ["2750", "7090"]


def test_v5_requires_more_than_ten_percent_large_bare_readings_for_mm():
    facts = [{"text": "275"}] * 18 + [{"text": "1250"}, {"text": "11000"}]
    assert infer_detection_v5_bare_dimension_unit([{"source_facts": facts}], document_unit="unknown") == (
        "cm", "nonstandard_100_to_600_value",
    )
    packages = [{"source_facts": facts[1:]}]
    assert infer_detection_v5_bare_dimension_unit(packages, document_unit="unknown") == (
        "mm", "bare_values_over_600_exceed_ten_percent",
    )
    assert infer_detection_v5_bare_dimension_unit(packages, document_unit="cm") == (
        "cm", "explicit_document_unit",
    )
    assert infer_detection_v5_bare_dimension_unit(
        [{"source_facts": [{"text": "275"}]}], document_unit="mm",
    ) == ("mm", "explicit_document_unit")


def test_v5_single_large_span_and_duplicate_ocr_do_not_choose_mm():
    view_box = {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 200, "bottom_right_y": 100}
    span = {"text": "1100", "fact_id": "native", "bbox": {
        "top_left_x": 10, "top_left_y": 10, "bottom_right_x": 40, "bottom_right_y": 20,
    }}
    duplicate = {**span, "fact_id": "ocr", "bbox": {**span["bbox"], "top_left_x": 12}}
    packages = [{"visual_group_id": "view", "page_number": 1, "bbox": view_box,
                 "source_facts": [span, duplicate, {"text": "275", "fact_id": "small", "bbox": view_box}]}]
    assert infer_detection_v5_bare_dimension_unit(packages, document_unit="unknown") == (
        "cm", "nonstandard_100_to_600_value",
    )
    fingerprint, = build_detection_v5_dimension_fingerprints(packages, document_unit="cm")
    assert [row["value_mm"] for row in fingerprint["occurrences"]] == ["11000", "2750"]

    another_label = {**span, "fact_id": "second", "bbox": {
        "top_left_x": 80, "top_left_y": 10, "bottom_right_x": 110, "bottom_right_y": 20,
    }}
    packages[0]["source_facts"].append(another_label)
    assert infer_detection_v5_bare_dimension_unit(packages, document_unit="unknown") == (
        "mm", "bare_values_over_600_exceed_ten_percent",
    )


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
