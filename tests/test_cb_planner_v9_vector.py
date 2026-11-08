from tools.probe_cb_planner_v9_vector import bind_plan


def plan_with_region(view_id, scope, ids):
    return {
        "summary": "Assembly plan",
        "blocks": [{
            "id": "B01", "name": "Base", "contains": "Carcass", "reason": "Visible boundary",
            "front_ids": [], "view_ids": [view_id],
            "region": {"view_id": view_id, "bbox_1000": [100, 200, 500, 600],
                       "geometry_scope": scope, "contour_ids": ids},
        }],
        "shared_parts": [], "front_conflicts": [], "uncertainties": [],
    }


def test_preserves_source_vertices_and_raw_plan():
    polygon = [[0, 0], [23, 0], [35, 12], [0, 12]]
    geometry = {"V01": {"contours": {"C01": polygon}}}
    raw = plan_with_region("V01", "partial", ["C01"])
    result = bind_plan(raw, geometry=geometry, front_ids=set())

    assert result["bindings"]["B01"]["polygons"] == [polygon]
    assert result["bindings"]["B01"]["scope"] == "partial"
    assert not result["geometry_issues"] and result["planner_structure_error"] is None
    assert raw["blocks"][0]["region"]["contour_ids"] == ["C01"]


def test_contour_from_another_island_never_binds():
    geometry = {"V01": {"contours": {"C01": [[0, 0], [20, 0], [20, 10]]}},
                "V02": {"contours": {}}}
    result = bind_plan(plan_with_region("V02", "complete", ["C01"]),
                       geometry=geometry, front_ids=set())

    assert result["bindings"] == {}
    assert result["geometry_issues"][0]["id"] == "B01"
    assert result["planner_structure_error"] is None
