from copy import deepcopy

from tools.estimation_block_geometry import path_spans
from use_cases.estimation_cb_geometry_parts import dimension, equal_drawer_run, finish_visible_parts


def test_equal_horizontal_drawers_preserve_individual_dimension_or_stack():
    view = {"view_id": "view-1", "width": 1000, "height": 1000, "candidates": [
        {"id": "A", "bbox": [10, 10, 130, 60]},
        {"id": "B", "bbox": [132, 10, 250, 60]},
        {"id": "C", "bbox": [132, 62, 250, 112]},
    ]}
    printed = {"view-1": [
        {"axis": "x", "bounds": [0, 260], "value_mm": 1040, "source_id": "run-width"},
        {"axis": "y", "bounds": [0, 130], "value_mm": 520, "source_id": "overall-height"},
    ]}
    width = dimension(1040, "printed_dimension", ["run-width"])
    sheet = dimension(17, "construction_assumption")

    faces, box = equal_drawer_run(view, printed, ["A", "B"], width, sheet)
    assert [item["mm"] for item in faces] == [476, 200]
    assert box["mm"] == 468
    assert equal_drawer_run(view, printed, ["B", "C"], width, sheet) == (None, None)

    printed["view-1"].append({"axis": "x", "bounds": [10, 130], "value_mm": 480, "source_id": "front-width"})
    assert equal_drawer_run(view, printed, ["A", "B"], width, sheet) == (None, None)


def test_projected_thickness_borrows_printed_value_only_with_matching_finish_and_scale():
    def panel(role, thickness, basis, ref):
        return {"role": role, "dimensions": {"thickness": dimension(thickness, basis, [ref])}}

    stile = panel("frame_side", 40, "printed_dimension", "dimension-1")
    seat = panel("seat_cover", 39, "scaled_projection", "seat-gap")
    rib = panel("vertical_rib", 36, "scaled_projection", "rib-gap")
    cap = panel("frame_cap", 31, "scaled_projection", "cap-gap")
    table = panel("tabletop", 38, "scaled_projection", "table-gap")
    result = {"blocks": [{"block_id": "A", "parts": [stile, rib, cap]},
                         {"block_id": "B", "parts": [seat, table]}], "shared_parts": []}
    understanding = {"wood_grain": [
        {"role": role, "view_id": "view-1", "finish_group": "table" if role == "tabletop" else "frame"}
        for role in ("frame_side", "seat_cover", "vertical_rib", "frame_cap", "tabletop")
    ]}
    before = deepcopy(stile["dimensions"])
    finish_visible_parts(result, understanding)
    assert stile["dimensions"] == before
    assert [row["dimensions"]["thickness"]["mm"] for row in (stile, seat, rib, cap, table)] == [40, 40, 40, 31, 38]
    assert seat["dimensions"]["thickness"]["refs"] == ["seat-gap", "dimension-1"]
    assert seat["dimensions"]["thickness"]["basis"] == "construction_assumption"
    assert seat["dimensions"]["thickness"]["projected_mm"] == 39


def test_external_caption_keeps_short_arrow_to_arrow_measurement():
    tips = {(0, (100, 300)), (0, (115, 300))}
    span, = path_spans([((80, 300), (300, 300))], tips)
    assert span["bounds"] == [100, 115]
    assert span["caption_bounds"] == [80, 300]
