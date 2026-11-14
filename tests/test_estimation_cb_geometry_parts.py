from copy import deepcopy
import json

from tools.estimation_block_geometry import path_spans
from tools.probe_estimation_v8_3 import classify_islands
from use_cases.estimation_cb_geometry_parts import (
    _compatible_frame_stock, dimension, equal_drawer_run, finish_visible_parts, stock, visible_grain_evidence,
)


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


def test_parts_recovers_missing_finish_from_observed_characteristic():
    upright = {"role": "frame_side", "dimensions": {"thickness": dimension(40, "printed_dimension", ["printed"])}}
    seat = {"role": "seat_cover", "dimensions": {"thickness": dimension(39, "scaled_projection", ["projection"])}}
    understanding = {
        "characteristics": ["Wood-grain finish visible on slat panel and seat cover",
                            "Tabletop shows no visible grain"],
        "wood_grain": [{"role": "frame_side", "view_id": "v1", "material": "veneered_mdf", "finish_group": "oak"}],
    }
    finish_visible_parts({"blocks": [{"block_id": "A", "parts": [upright]},
                                     {"block_id": "B", "parts": [seat]}], "shared_parts": []}, understanding)
    assert seat["dimensions"]["thickness"]["mm"] == 40
    assert seat["dimensions"]["thickness"]["projected_mm"] == 39
    assert seat["visual_stock"]["refs"] == ["understanding:characteristic:1"]
    assert "tabletop" not in visible_grain_evidence(understanding)


def test_part_stock_reuse_preserves_printed_thickness_and_separate_finishes():
    shared = stock(20)
    drawer = {"role": "drawer_front", "dimensions": {"thickness": shared}}
    cabinet_side = {"role": "frame_side", "dimensions": {"thickness": dimension(30, "scaled_projection", ["v1:C1"])}}
    explicit = {"role": "drawer_front", "dimensions": {"thickness": dimension(19, "printed_dimension", ["v1:D1"])}}
    contrast = {"role": "tabletop", "dimensions": {"thickness": shared}}
    cues = [{"role": role, "view_id": "v1", "material": "veneered_mdf", "finish_group": group}
            for role, group in (("drawer_front", "oak"), ("frame_side", "oak"), ("tabletop", "ash"),
                                ("carcass_side", "oak"), ("frame_backing", "oak"), ("frame_cap", "ash"))]
    understanding = {"wood_grain": cues}
    finish_visible_parts({"blocks": [{"block_id": "A", "parts": [drawer, explicit, cabinet_side]},
                                     {"block_id": "B", "parts": [contrast]}], "shared_parts": []}, understanding)
    assert drawer["dimensions"]["thickness"]["mm"] == 30
    assert explicit["dimensions"]["thickness"]["mm"] == 19
    assert contrast["dimensions"]["thickness"]["mm"] == 20
    assert shared["mm"] == 20
    shared_stock = _compatible_frame_stock(visible_grain_evidence(understanding))
    assert set(shared_stock) == {"frame_backing"}
    assert shared_stock["frame_backing"]["mm"] == 17


def test_understanding_binds_solid_wood_only_to_a_literal_source_note():
    views = {"view-1": {"object_id": "object-1"}}
    note = "Door fronts: solid oak, 20 mm."
    data = {"input_payload": {"object": {"object_id": "object-1"}, "evidence": {"ocr_blocks": [
        {"block_ref": "ocr-1", "text": note},
        {"block_ref": "ocr-2", "text": "Fixed panel: solid wood effect melamine."},
    ]}}}

    def invoke(stage, request, validate):
        assert stage == "island-map"
        assert "choose veneered MDF" in request["system"]
        context = json.loads(request["messages"][0]["content"][0]["text"])
        assert context["material_notes"]["object-1"]["ocr-1"] == [note]
        return validate({"islands": {"view-1": "Front elevation"}, "understanding": {"object-1": {"wood_grain": [
            {"role": "door_front", "view_id": "view-1", "material": "solid_wood",
             "source_ref": "ocr-1", "source_quote": note},
            {"role": "fixed_panel", "view_id": "view-1", "material": "solid_wood",
             "source_ref": "ocr-2", "source_quote": "Fixed panel: solid wood effect melamine."},
            {"role": "vertical_rib", "view_id": "view-1", "material": "solid_wood",
             "source_ref": "ocr-1", "source_quote": "Ribs: solid oak."},
            {"role": "drawer_front", "view_id": "view-1", "material": "veneered_mdf"},
        ]}}})

    understanding = classify_islands(invoke, views, {}, {}, include_worktop_cutouts=True,
                                     inputs=[data])["understanding"]["object-1"]
    assert [(row["role"], row["material"]) for row in understanding["wood_grain"]] == [
        ("door_front", "solid_wood"), ("drawer_front", "veneered_mdf"),
    ]
    door, drawer = ({"role": role, "dimensions": {}} for role in ("door_front", "drawer_front"))
    finish_visible_parts({"blocks": [{"block_id": "B1", "parts": [door, drawer]}], "shared_parts": []}, understanding)
    assert door["material_note"]["refs"] == ["ocr-1"]
    assert drawer["visual_stock"]["material"] == "veneered_mdf"
    assert "material_note" not in drawer
