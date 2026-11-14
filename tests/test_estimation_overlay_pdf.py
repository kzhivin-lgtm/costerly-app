from io import BytesIO

from PIL import Image
import pymupdf
import pytest

from use_cases.estimation_overlay_pdf import _exterior_image, build_overlay_pdfs


def test_overlay_preserves_source_rotation_and_scopes_objects():
    with pymupdf.open() as source:
        page = source.new_page(width=200, height=100)
        page.set_rotation(90)
        page = source.new_page(width=200, height=100)
        page.insert_text((25, 25), "Second sheet")
        pdf = source.tobytes()

    view = {"view_id": "V1", "object_id": "a", "page": 1, "bbox_normalized": [.1, .2, .9, .8],
            "width": 1100, "height": 1650, "candidates": [
                {"id": "C1", "polygon": [(137.5, 275), (550, 275), (550, 1100), (137.5, 1100)]},
            ]}
    other = {**view, "view_id": "V2", "object_id": "b", "page": 2}
    face = {"role": "drawer", "view_id": "V1", "candidate_id": "C1", "bbox_px": [0, 0, 10, 10]}
    result = {"objects": {"a": {"front": {"faces": [face]}, "planner": {"blocks": []}},
                          "b": {"front": {"faces": [face]}, "planner": {"blocks": []}}}}
    (oid, layer, overlay), = build_overlay_pdfs(pdf, result, [view, other])
    assert (oid, layer) == ("a", "front")
    with pymupdf.open(stream=overlay, filetype="pdf") as document:
        assert len(document) == 1
        page = document[0]
        assert page.rect == pymupdf.Rect(0, 0, 100, 200)
        path, = page.get_drawings()
        assert tuple(path["rect"]) == pytest.approx((20, 60, 50, 120), abs=.1)


def test_block_outline_removes_shared_edges_and_preserves_concavity():
    rectangles = [[(0, 0), (100, 0), (100, 30), (0, 30)],
                  [(0, 30), (30, 30), (30, 100), (0, 100)]]
    png, (left, top, *_) = _exterior_image(rectangles, "#1D55A7")
    with Image.open(BytesIO(png)) as outline:
        def alpha_at(x, y):
            return outline.getpixel((x - left, y - top))[3]

        assert alpha_at(16, 30) == 0
        assert alpha_at(70, 75) == 0
        assert alpha_at(70, 30) > 0
        assert alpha_at(30, 75) > 0
