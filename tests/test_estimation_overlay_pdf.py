import pymupdf
import pytest

from use_cases.estimation_overlay_geometry import exterior_rings, separate_seams, volume_edges
from use_cases.estimation_overlay_pdf import _covering_views, build_overlay_pdfs


def test_overlay_preserves_source_rotation_and_scopes_objects():
    with pymupdf.open() as source:
        page = source.new_page(width=200, height=100)
        page.insert_text((77, 62), "AB")
        page.set_rotation(90)
        source.new_page(width=200, height=100).insert_text((25, 25), "Second sheet")
        pdf = source.tobytes()

    view = {"view_id": "view-001", "object_id": "a", "page": 1, "bbox_normalized": [.1, .2, .9, .8],
            "width": 1100, "height": 1650, "candidates": [
                {"id": "C1", "polygon": [(137.5, 275), (550, 275), (550, 1100), (137.5, 1100)]},
            ]}
    other = {**view, "view_id": "view-002", "object_id": "b", "page": 2}
    face = {"role": "drawer", "view_id": "view-001", "candidate_id": "C1", "bbox_px": [0, 0, 10, 10]}
    result = {"islands": {"view-001": "Axonometric view"}, "objects": {
        oid: {"front": {"faces": [face]}, "planner": {"blocks": []}} for oid in ("a", "b")}}
    files = {(oid, layer): data for oid, layer, data in build_overlay_pdfs(pdf, result, [view, other])}
    assert set(files) == {(oid, layer) for oid in ("a", "b") for layer in ("front", "block")}
    with pymupdf.open(stream=files["a", "front"], filetype="pdf") as document:
        assert len(document) == 1
        page = document[0]
        text = page.get_text()
        assert "V01" in text and "Drawers  1" in text and "AB" in text
        assert "Second sheet" not in text
        path, = [p for p in page.get_drawings() if p["width"] == 2]
        assert path["rect"].height / path["rect"].width == pytest.approx(2)
        match, = page.search_for("AB")
        assert path["rect"].intersects(match)
    with pymupdf.open(stream=files["b", "front"], filetype="pdf") as document:
        assert "No localized elements" in document[0].get_text()


def test_selecting_views_prioritizes_coverage_then_axonometry_and_front():
    views = {vid: {"number": n} for n, vid in enumerate(("front", "axon", "side"))}
    projections = {"front": "Front elevation", "axon": "Axonometric view", "side": "Side view"}
    marks = {vid: [[[], "blue", False, "B01"]] for vid in views}
    assert _covering_views(views, projections, marks, layer="block") == ["axon"]
    marks["axon"][0][2] = True
    assert _covering_views(views, projections, marks, layer="block") == ["front"]
    marks["front"] = []
    assert _covering_views(views, projections, marks, layer="block") == ["side"]
    marks["side"].append([[], "blue", False, "B02"])
    marks["axon"][0][2] = False
    assert _covering_views(views, projections, marks, layer="block") == ["side"]
    marks["side"].pop(0)
    assert _covering_views(views, projections, marks, layer="block") == ["axon", "side"]


def test_two_complete_elevations_take_precedence_over_three_partial_views():
    views = {vid: {} for vid in ("axon", "front", "side", "detail")}
    projections = {"axon": "Axonometric view", "front": "Front elevation", "side": "Side view"}
    marks = {
        vid: [[[], "blue", False, label] for label in labels]
        for vid, labels in {
            "axon": ("B02", "B03"), "front": ("B01", "B02"), "side": ("B03", "B04"),
            "detail": ("B05",),
        }.items()
    }
    marks["front"].append([[], "blue", False, "B05"])
    assert _covering_views(views, projections, marks, layer="block") == ["front", "side"]


def test_complementary_views_in_one_pdf_per_layer():
    with pymupdf.open() as source:
        for label in ("First wing", "Second wing"):
            source.new_page(width=220, height=100).insert_text((30, 22), label)
        pdf = source.tobytes()

    views = [
        {"view_id": vid, "object_id": "a", "page": page, "bbox_normalized": [0, 0, 1, 1],
         "width": 1100, "height": 500, "candidates": []}
        for page, vid in enumerate(("view-001", "view-002"), start=1)
    ]
    contour = [(100, 80), (680, 80), (680, 370), (100, 370)]
    blocks = [
        {"id": f"B0{index}", "appearances": [], "envelopes": {view["view_id"]: {"polygons_px": [contour]}}}
        for index, view in enumerate(views, start=1)
    ]
    faces = [
        {"role": "drawer", "view_id": view["view_id"], "bbox_px": [100 * i, 90, 100 * i + 90, 370]}
        for count, view in zip((2, 3), views)
        for i in range(1, count + 1)
    ]
    result = {"islands": {"view-001": "Front elevation", "view-002": "Side view"},
              "objects": {"a": {"front": {"faces": faces}, "planner": {"blocks": blocks}}}}
    files = {layer: data for _, layer, data in build_overlay_pdfs(pdf, result, views)}
    assert set(files) == {"front", "block"}
    with pymupdf.open(stream=files["front"], filetype="pdf") as document:
        assert len(document) == 2
        first, second = [page.get_text() for page in document]
        assert all(text in first for text in ("View 1 of 2", "First wing", "Drawers  2"))
        assert all(text in second for text in ("View 2 of 2", "Second wing", "Drawers  3"))
        assert "Second wing" not in first and "First wing" not in second
    with pymupdf.open(stream=files["block"], filetype="pdf") as document:
        assert len(document) == 2
        for label, page in zip(("B01", "B02"), document):
            assert label in page.get_text()
            assert "2 of 2 blocks shown in this PDF." in page.get_text()


def test_block_outline_removes_shared_edges_and_preserves_concavity():
    rectangles = [[(0, 0), (100, 0), (100, 30), (0, 30)],
                  [(0, 30), (30, 30), (30, 100), (0, 100)]]
    ring, = exterior_rings(rectangles)
    assert len(ring) == 6
    assert any(abs(x - 30) < 3 and abs(y - 30) < 3 for x, y in ring)
    assert all(x < 40 or y < 40 for x, y in ring)


def test_cuboid_uses_visible_source_ridges_and_keeps_both_seam_strokes():
    ring = [(0, 30), (30, 10), (130, 15), (130, 130), (31, 152), (0, 135)]
    junction = (31, 45)
    ridges = [(junction, ring[index]) for index in (0, 2, 4)]
    # A short interior line might represent a shelf or door boundary.
    ridges.append(((50, 65), (100, 65)))
    assert not volume_edges(ring, ridges[1:])
    assert len(ring) + len(volume_edges(ring, ridges)) == 9
    upper = [(0, 0), (80, 0), (80, 40), (0, 40)]
    lower = [(0, 40), (80, 40), (80, 80), (0, 80)]
    assert separate_seams(upper, [lower], 5)[2:] == [(80, 35), (0, 35)]
    assert separate_seams(lower, [upper], 5)[:2] == [(0, 45), (80, 45)]
