import pytest

from tools.estimation_worktop_geometry import worktop_geometry


def test_worktop_joins_linked_plan_faces_and_requires_finish_evidence_to_split():
    main = [(0, 0), (500, 0), (500, 100), (100, 100), (100, 500), (0, 500)]
    end = [(0, 500), (100, 500), (100, 510), (30, 600), (0, 600)]
    plan = {"view_id": "plan", "width": 600, "height": 700, "candidates": [
        {"id": "main", "polygon": main, "bbox": [0, 0, 500, 500]},
        {"id": "end", "polygon": end, "bbox": [0, 500, 100, 600]},
    ]}
    views = {"plan": plan, "render": {"view_id": "render"}}
    projections = {"plan": "Top view", "render": "Render"}
    proxies = [
        {"view_id": "plan", "axis": axis, "value_mm": 400, "contour_ids": ids,
         "bounds_1000": [0, 100 * 1000 / size],
         "projection_binding": {"plan_frontage_axis": frontage, "mapped_frontage_px": [100, extent]}}
        for axis, size, frontage, extent, ids in [
            ("x", 600, "y", 600, ["main", "end"]),
            ("y", 700, "x", 500, ["main"]),
        ]
    ]
    blocks = [{"measurements": {"depth_proxy": proxy}} for proxy in proxies]
    printed = {"plan": [
        {"axis": axis, "bounds": [0, 1000], "value_mm": size * 4, "source_id": axis + "-scale"}
        for axis, size in [("x", 600), ("y", 700)]
    ]}
    outline = worktop_geometry(blocks, views, printed, {}, projections)
    assert outline["outer"]["area_m2"] == pytest.approx(1.5496)
    assert [surface["area_m2"] for surface in outline["surfaces"]] == pytest.approx([1.5496])

    reading = {"name": "Fitted kitchen", "characteristics": ["Beveled worktop end has a contrasting finish."]}
    split = worktop_geometry(blocks, views, printed, reading, projections)
    assert [surface["area_m2"] for surface in split["surfaces"]] == pytest.approx([1.44, .1096])
    assert split["seam_source_refs"] == ["plan:end", "plan:main"]
    assert split["finish_evidence"]["view_id"] == "render"
    ambiguous = worktop_geometry(blocks, {"plan": plan}, printed, reading, projections)
    assert ambiguous["outer"]["area_m2"] == split["outer"]["area_m2"]
    assert ambiguous["surfaces"] == []
