from copy import deepcopy

from use_cases.estimation_dimension_relations import dimension_relations, projection_hypotheses, reconcile_projection_assumptions, MAX_RELATIONS


def dimension(did, view, value, a, b, orientation="horizontal", page=1):
    axis, other = ("x", "y") if orientation == "horizontal" else ("y", "x")
    return {"dimension_id": did, "view_candidates": [view], "interpreted_value_mm": value,
        "page_number": page, "line_candidates": [{"segment_id": did + "-line", "orientation": orientation,
        "start": {axis: a, other: 10}, "end": {axis: b, other: 10},
        "endpoint_crossing_candidates": [["a"], ["b"]]}]}


def fixture():
    return {"pages": [{"page_number": 1, "coordinate_frame": [1000, 1000]}], "dimensions": [
        dimension("total", "v1", 1000, 100, 600), dimension("part1", "v2", 400, 100, 300),
        dimension("part2", "v1", 600, 300, 600), dimension("equal1", "v1", 800, 100, 500),
        dimension("equal2", "v3", 800, 200, 600, "vertical")]}


def test_printed_sum_requires_geometry_and_equal_values_keep_axis_rotation_candidate():
    evidence = fixture()
    before = deepcopy(evidence)
    result = dimension_relations(evidence)
    assert {r["relation"] for r in result["relations"]} == {
        "aligned_printed_sum_total_then_parts", "equal_printed_value_and_span"}
    assert all("not_physical_ownership" in r["status"] for r in result["relations"])
    assert evidence == before


def test_coincidental_sum_without_aligned_boundaries_is_not_a_relation():
    evidence = fixture()
    evidence["dimensions"][1] = dimension("part1", "v2", 400, 120, 320)
    assert not any(r["relation"].startswith("aligned") for r in dimension_relations(evidence)["relations"])


def test_same_number_different_pixel_scale_is_unresolved_not_relabelled():
    evidence = fixture()
    evidence["dimensions"][-1] = dimension("equal2", "v3", 800, 200, 800, "vertical")
    assert not any(r["relation"].startswith("equal") for r in dimension_relations(evidence)["relations"])


def test_cross_page_unknown_frame_ambiguous_view_or_missing_crossing_cannot_join():
    for mutation in ("page", "frame", "view", "crossing"):
        evidence = fixture()
        item = evidence["dimensions"][-1]
        if mutation == "page":
            item["page_number"] = 2
            evidence["pages"].append({"page_number": 2, "coordinate_frame": [1000, 1000]})
        elif mutation == "frame":
            evidence["pages"][0]["coordinate_frame"] = None
        elif mutation == "view":
            item["view_candidates"].append("v4")
        else:
            item["line_candidates"][0]["endpoint_crossing_candidates"][1] = []
        assert not any(r["relation"].startswith("equal") for r in dimension_relations(evidence)["relations"])


def test_dense_repeated_numbers_are_bounded_and_explicitly_truncated():
    evidence = fixture()
    evidence["dimensions"] = [dimension(f"d{i}", f"v{i}", 800, 100, 500) for i in range(300)]
    result = dimension_relations(evidence)
    assert result["truncated"] is True
    assert len(result["relations"]) == MAX_RELATIONS


def relation(a, axis_a, b, axis_b):
    return {"members": [{"view_id": a, "orientation": axis_a}, {"view_id": b, "orientation": axis_b}]}


def test_rotated_equal_axes_give_conditional_plan_not_absolute_width_depth():
    result = projection_hypotheses([relation("a", "horizontal", "b", "vertical"),
                                   relation("c", "horizontal", "b", "horizontal")])
    b = next(v for v in result["views"] if v["view_id"] == "b")
    assert b["projection_candidates"] == ["top_plan"]
    assert {v["horizontal_axis"] for v in b["axis_candidates"]} == {"width", "depth"}
    assert "rotated elevation" in result["assumptions"][2]
    assert result["authority"] == "conditional_geometric_hypothesis_not_source_fact"


def test_same_orientation_does_not_decide_projection():
    result = projection_hypotheses([relation("a", "horizontal", "b", "horizontal")])
    assert all(len(v["projection_candidates"]) == 3 for v in result["views"])


def test_inconsistent_directions_empty_domains_instead_of_fabricating_projection():
    result = projection_hypotheses([relation("a", "horizontal", "b", "horizontal"),
        relation("a", "horizontal", "b", "vertical"), relation("a", "vertical", "b", "horizontal")])
    assert result["status"] == "inconsistent_assumptions"
    assert all(not v["projection_candidates"] for v in result["views"])


def reconciliation_fixture():
    evidence = fixture()
    evidence["dimensions"][3] = dimension("equal1", "v3", 800, 100, 500)
    evidence["dimensions"][4] = dimension("equal2", "v1", 800, 200, 600, "vertical")
    evidence["view_readings"] = [
        {"view_id": "v1", "projection": "front_elevation", "horizontal_axis": "width"},
        {"view_id": "v2", "projection": "side_elevation", "horizontal_axis": "depth"},
        {"view_id": "v3", "projection": "front_elevation", "horizontal_axis": "width"}]
    evidence["dimension_readings"] = [{"dimension_id": "total", "view_id": "v1", "scope_id": "box",
        "axis": "width", "ownership_status": "visual_interpretation", "numeric_value": 1000}]
    return evidence


def test_unique_minimal_edit_is_assumption_and_invalidates_old_physical_ownership():
    evidence = reconciliation_fixture()
    before = deepcopy(evidence)
    result = reconcile_projection_assumptions(evidence)
    assert result["projection_assumption_audit"]["status"] == "applied_as_assumption"
    assert result["view_readings"][0] == {"view_id": "v1", "projection": "top_plan", "horizontal_axis": "depth"}
    reading = result["dimension_readings"][0]
    assert reading["scope_id"] is None and reading["axis"] is None
    assert reading["ownership_status"] == "conflicting"
    assert reading["numeric_value"] == 1000
    assert reading["prior_visual_ownership"] == {"scope_id": "box", "axis": "width"}
    assert result["status"] == "needs_review" and evidence == before


def test_ambiguous_minimal_edit_does_not_choose_width_depth_arbitrarily():
    evidence = reconciliation_fixture()
    evidence["view_readings"][1].update(projection="front_elevation", horizontal_axis="width")
    result = reconcile_projection_assumptions(evidence)
    assert result["projection_assumption_audit"]["best_assignment_count"] > 1
    assert result["view_readings"] == evidence["view_readings"]
    assert result["dimension_readings"] == evidence["dimension_readings"]


def test_incomplete_assignment_search_never_applies_a_partial_answer(monkeypatch):
    monkeypatch.setattr("use_cases.estimation_dimension_relations.MAX_ASSIGNMENT_STATES", 2)
    evidence = reconciliation_fixture()
    result = reconcile_projection_assumptions(evidence)
    assert result["projection_assumption_audit"]["status"] == "not_applied"
    assert result["view_readings"] == evidence["view_readings"]


def test_isometric_relation_does_not_enter_orthographic_reconciliation():
    evidence = reconciliation_fixture()
    evidence["view_readings"][1]["projection"] = "isometric"
    assert reconcile_projection_assumptions(evidence)["view_readings"] == evidence["view_readings"]


def test_section_without_axis_is_unanchored_not_a_front_elevation_fact():
    evidence = reconciliation_fixture()
    evidence["view_readings"][1].update(projection="section", horizontal_axis=None)
    result = reconcile_projection_assumptions(evidence)
    assert result["view_readings"][0]["projection"] == "top_plan"
    assert result["view_readings"][0]["horizontal_axis"] == "depth"
    assert result["view_readings"][1]["projection"] == "side_elevation"
    assert result["projection_assumption_audit"]["authority"] == "estimating_assumption_not_source"


def test_fresh_measurement_withdraws_dependent_ownership_but_preserves_source_and_audit():
    from use_cases.estimation_composition_scope import geometry_scope
    evidence = reconciliation_fixture()
    result = reconcile_projection_assumptions(evidence, reobserve_ownership=True)
    assert result["dimension_readings"] == []
    assert result["superseded_interpretation"]["dimension_readings"] == evidence["dimension_readings"]
    assert result["dimensions"] == evidence["dimensions"]
    transport = geometry_scope({"construction_version": "v6", "evidence_map": result})["evidence_map"]
    assert "superseded_interpretation" not in transport
    assert transport["dimension_readings"] == []


def test_axis_candidates_do_not_turn_height_into_depth_or_certify_ownership():
    from use_cases.estimation_dimension_relations import dimension_axis_candidates
    evidence = reconciliation_fixture()
    evidence["dimensions"].append(dimension("height", "v3", 1200, 50, 650, "vertical"))
    result = reconcile_projection_assumptions(evidence, reobserve_ownership=True)
    axes = dimension_axis_candidates(result)
    assert axes["total"] == ["depth"]
    assert axes["equal2"] == ["width"]
    assert axes["height"] == ["height"]
    assert not result["dimension_readings"]


def test_alternative_line_orientations_are_not_deduplicated_into_false_uniqueness():
    evidence = reconciliation_fixture()
    alternative = dimension("equal2", "v1", 800, 200, 600)["line_candidates"][0]
    alternative["segment_id"] = "different-horizontal-candidate"
    evidence["dimensions"][4]["line_candidates"].append(alternative)
    relations = dimension_relations(evidence)
    assert len([r for r in relations["relations"] if r["relation"].startswith("equal")]) == 2
    result = reconcile_projection_assumptions(evidence)
    assert result["projection_assumption_audit"]["status"] == "not_applied"
    assert result["view_readings"] == evidence["view_readings"]
