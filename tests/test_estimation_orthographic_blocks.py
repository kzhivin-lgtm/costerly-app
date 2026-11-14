import pytest

from tools.estimation_orthographic_geometry import resolve_orthographic_group
from tools.probe_cb_block_boundaries import build_report
from tools.probe_estimation_v8_native_blocks import attach_native_sides


def rectangle(ident, box):
    left, top, right, bottom = box
    return {"id": ident, "bbox": box, "area": (right - left) * (bottom - top),
            "polygon": [(left, top), (right, top), (right, bottom), (left, bottom)]}


@pytest.mark.parametrize("relation", ["matching_topology", "unique_geometry", "same_material"])
def test_plan_alignment_requires_supported_detection_relation(relation):
    views = {vid: {"object_id": "object", "page": 1, "bbox_normalized": [0, 0, 1, 1],
                   "candidates": []} for vid in ("elevation", "plan")}
    islands = [{"island_id": vid, "page_number": 1, "coordinate_frame_pixels": [100, 100],
                "bbox": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 100, "bottom_right_y": 100}}
               for vid in views]
    relation_row = {"group_id_a": "plan", "group_id_b": "elevation", "evidence_type": relation}
    detection = {"objects": [{"object_id": "object", "islands": islands, "accepted_observations": [relation_row]}]}
    if relation == "same_material":
        with pytest.raises(ValueError, match="no accepted Detection observation"):
            build_report(views, [], detection, ["elevation"], "plan", "elevation")
        return
    report = build_report(views, [], detection, ["elevation"], "plan", "elevation")
    assert report["detection_topology_observations"] == [relation_row]


@pytest.mark.parametrize("reserved,expected", [(False, ["side"]), (True, [])])
def test_native_side_recovery_requires_full_height_and_unclaimed_contour(reserved, expected):
    block = {"id": "B01", "positions": [["door"]],
             "appearances": [{"view_id": "elevation", "bbox": [21, 0, 81, 120]}]}
    plan = {"aligned_elevation_id": "elevation", "blocks": [block]}
    views = {"elevation": {"candidates": [
        rectangle("side", [0, 0, 20, 120]),
        rectangle("door", [21, 0, 81, 120]),
        rectangle("short", [81, 0, 101, 70]),
        rectangle("seam", [101, 0, 102, 120]),
    ]}}
    faces = [{"view_id": "elevation", "candidate_id": "side"}] if reserved else []

    attach_native_sides(plan, views, faces)

    assert [row["contour_id"] for row in block.get("fixed_extensions", [])] == expected


@pytest.mark.parametrize("secondary_witness,expected", [
    ("unique_geometry", {"B01", "B02"}), ("same_material", {"B01"}),
])
def test_linked_return_can_measure_its_elevation_without_claiming_depth(secondary_witness, expected):
    views = {
        vid: {"view_id": vid, "page": 1, "width": 100, "height": 100,
              "candidates": [rectangle("c", [0, 0, 100, 100])]}
        for vid in ("plan", "main", "return")
    }
    projections = {"plan": "Top view", "main": "Front elevation", "return": "Side view"}
    plan = {"object_parts": [], "blocks": [
        {"id": block, "positions": [["c"]], "basis": "visible_front_band",
         "appearances": [{"view_id": vid, "bbox": [0, 0, 100, 100]}]}
        for block, vid in (("B01", "main"), ("B02", "return"))
    ]}
    observations = [
        {"group_id_a": "plan", "group_id_b": "main", "evidence_type": "matching_topology"},
        {"group_id_a": "return", "group_id_b": "main", "evidence_type": secondary_witness},
    ]
    printed = {vid: [{"axis": "x", "bounds": (0, 500), "value_mm": 300}] for vid in views}
    result = resolve_orthographic_group(
        plan, views, projections, printed, observations,
        span=lambda view, axis, ends, *_: {"view_id": view["view_id"], "axis": axis,
                                          "bounds_1000": tuple(10 * end for end in ends)},
        bind_dimension=lambda boundary, printed: {**boundary, "value_mm": None},
        elevations={"Front elevation", "Side view"}, edge_tolerance=3,
    )
    assert set(result) == expected
    if "B02" in result:
        assert result["B02"]["width"]["value_mm"] == 600
        assert result["B02"]["depth"]["value_mm"] is None
