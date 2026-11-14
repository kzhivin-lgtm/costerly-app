from base64 import b64encode
from copy import deepcopy
from io import BytesIO
import json

import pytest
from PIL import Image

from tools.estimation_block_geometry import path_spans
from tools.probe_estimation_v8_3 import MAX_FINISH_SURFACES, classify_islands, write_finish_overlays
from use_cases.estimation_cb_geometry_parts import (
    _compatible_frame_stock, _structural_finish_links, dimension, equal_drawer_run, finish_visible_parts, stock,
    visible_grain_evidence,
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
    same_faces, narrower_box = equal_drawer_run(
        view, printed, ["A", "B"], width, sheet, side_sheet=dimension(20, "construction_assumption"),
    )
    assert same_faces == faces and narrower_box["mm"] == 466
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


def test_structural_finish_links_fill_missing_surfaces_and_respect_conflicts():
    frame = {"id": "A", "basis": "matched_framed_panel",
             "appearances": [{"view_id": "front", "bbox": [0, 10, 150, 71]}]}
    drawers = {"id": "D", "basis": "shared_drawer_frame",
               "appearances": [{"view_id": "front", "bbox": [1, 72, 149, 98]}]}
    distant = {"id": "F", "basis": "shared_drawer_frame",
               "appearances": [{"view_id": "front", "bbox": [200, 72, 350, 98]}]}
    surfaces = [{"role": role, "view_id": "axon", "finish": "wood_grain", "finish_group": "oak"}
                for role in ("frame_cap", "vertical_rib", "drawer_front")]
    understanding = {"finish_surfaces": surfaces}
    links = _structural_finish_links([frame, drawers, distant], understanding, visible_grain_evidence(understanding))
    assert set(links) == {("A", "frame_side"), ("D", "seat_cover")}
    assert links["D", "seat_cover"]["refs"] == ["axon", "front"]

    understanding["wood_grain"] = [{"role": "tabletop", "view_id": "axon", "finish_group": "oak"},
                                   {"role": "frame_backing", "view_id": "axon", "finish_group": "oak"}]
    surfaces.extend({"role": role, "view_id": "axon", "finish": "plain", "finish_group": "paint"}
                    for role in ("seat_cover", "tabletop"))
    grain = visible_grain_evidence(understanding)
    assert "tabletop" not in grain
    assert grain["frame_backing"]["material"] == "veneered_mdf"
    assert set(_structural_finish_links([frame, drawers], understanding, grain)) == {("A", "frame_side")}


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


def test_finish_surfaces_keep_two_fronts_with_different_finishes_separate(tmp_path):
    views = {"v1": {"object_id": "o", "width": 1000, "height": 1000, "candidates": [
        {"id": "C1", "bbox": [20, 20, 200, 100]}, {"id": "C2", "bbox": [220, 20, 400, 100]},
    ]}}
    sample = {"role": "drawer_front", "view_id": "v1", "finish": "wood_grain", "evidence": "grain lines",
              "finish_group": "oak", "bbox_crop_1000": [20, 20, 200, 100]}

    def bind(rows):
        return classify_islands(lambda _stage, _request, validate: validate({
            "islands": {"v1": "Front elevation"}, "understanding": {"o": {"finish_surfaces": rows}},
        }), views, {}, {}, include_worktop_cutouts=True)["understanding"]["o"]

    assert len(bind([sample] * (MAX_FINISH_SURFACES - 1))["finish_surfaces"]) == MAX_FINISH_SURFACES - 1
    assert len(bind([sample] * MAX_FINISH_SURFACES)["finish_surfaces"]) == MAX_FINISH_SURFACES
    with pytest.raises(ValueError, match="finish surfaces"):
        bind([sample] * (MAX_FINISH_SURFACES + 1))
    understanding = bind([sample,
                          {**sample, "finish": "plain", "bbox_crop_1000": [220, 20, 400, 100]},
                          {**sample, "view_id": "v2"}, {**sample, "bbox_crop_1000": [0, 10, 1001, 50]}])
    assert understanding["finish_surface_audit"] == {"supplied": 4, "accepted": 2, "limit": MAX_FINISH_SURFACES}
    first, second = ({"role": "drawer_front", "instance_ref": f"v1:C{i}", "dimensions": {}} for i in (1, 2))
    finish_visible_parts({"blocks": [{"block_id": "B1", "parts": [first, second]}], "shared_parts": []}, understanding)
    assert first["visual_stock"]["material"] == "veneered_mdf"
    assert first["finish_surfaces"][0]["contour_ref"] == "v1:C1"
    assert second["finish_surfaces"][0]["finish"] == "plain"
    assert "visual_stock" not in second
    image = BytesIO()
    Image.new("RGB", (1000, 1000), "white").save(image, format="PNG")
    write_finish_overlays({"o": understanding}, {"v1": [None, {"source": {
        "data": b64encode(image.getvalue()).decode(),
    }}]}, tmp_path)
    overlay = tmp_path / "finish-overlays"
    assert (overlay / "v1.png").is_file()
    legend = json.loads((overlay / "legend.json").read_text())
    assert [(row["label"], row["contour_ref"]) for row in legend["v1"]] == [(1, "v1:C1"), (2, "v1:C2")]
