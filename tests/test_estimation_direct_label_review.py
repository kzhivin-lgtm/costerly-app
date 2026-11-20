from copy import deepcopy
from io import BytesIO
import json

import pytest

from tools.estimation_direct_label_review import reconcile_direct_labels, render_panel_tiles
from tools.probe_estimation_v7_4_front_evidence import bind_front_roles

LABEL = {"id": "panel", "role": "mirror", "source_text": "Mirror"}
CUE = {"role": "mirror", "source": {"view_id": "v", "source_text": "Mirror"}}
REQUEST = {"messages": [{"role": "user", "content": [{"type": "text", "text": str(i)} for i in range(9)]}]}
TILE = {"id": "panel", "png": b"source pixels", "image_sha256": "fixture"}


def bind(raw):
    bound = bind_front_roles(raw, leaders={}, contours={"panel": [0, 0, 10, 10], "other": [10, 0, 20, 10]}, stroke_ids={})
    return {"readings": raw, "items": bound["items"], "issues": bound["issues"]}


def initial(labels=()):
    return bind({"leader_readings": [], "stroke_readings": [], "direct_labels": list(labels)})


def review(labels=(), ids=("panel",), unresolved=()):
    return {"direct_labels": list(labels), "reviewed_contour_ids": list(ids),
            "unresolved_contour_ids": list(unresolved)}


def test_without_native_faces_there_is_no_extra_request():
    start = initial()
    def forbidden(*_args):
        raise AssertionError("Unexpected model request")
    assert reconcile_direct_labels(forbidden, REQUEST, start, bind, view_id="v", findings=[], panel_tiles=[]) is start


def test_panel_owned_transcription_restores_an_empty_initial_reading():
    start = initial(); original = deepcopy(start); calls = []
    def invoke(stage, request, validate):
        calls.append(stage)
        assert json.loads(request["messages"][0]["content"][4]["text"])["contour_ids"] == ["panel"]
        return validate(review([LABEL]))
    result = reconcile_direct_labels(invoke, REQUEST, start, bind, view_id="v", findings=[CUE], panel_tiles=[TILE])
    assert calls == ["direct-label-review-v-001"]
    assert result["items"][0]["candidate_id"] == "panel"
    assert result["direct_label_review"]["initial_readings"]["direct_labels"] == []
    assert result["readings"]["leader_readings"] == original["readings"]["leader_readings"]
    assert start == original and len(REQUEST["messages"][0]["content"]) == 9


def test_wrong_neighbour_binding_is_superseded_but_its_original_evidence_is_retained():
    wrong = {**LABEL, "id": "other"}
    result = reconcile_direct_labels(lambda stage, request, validate: validate(review([LABEL], ("panel", "other"))),
        REQUEST, initial([wrong]), bind, view_id="v", findings=[CUE], panel_tiles=[TILE, {**TILE, "id": "other"}])
    assert result["readings"]["direct_labels"] == [LABEL]
    assert result["direct_label_review"]["initial_readings"]["direct_labels"] == [wrong]
    assert result["direct_label_review"]["source_findings"] == [CUE]


def test_persistent_ambiguity_is_pending_without_a_retry_loop():
    calls = []
    def invoke(stage, request, validate):
        calls.append(stage); return validate(review(unresolved=["panel"]))
    result = reconcile_direct_labels(invoke, REQUEST, initial(), bind, view_id="v", findings=[CUE], panel_tiles=[TILE])
    assert len(calls) == 1 and result["readings"]["direct_labels"] == []
    assert result["issues"][0]["reason"] == "front_role_review_pending"


def test_an_empty_panel_does_not_invent_a_label_from_an_external_callout():
    result = reconcile_direct_labels(lambda stage, request, validate: validate(review()),
        REQUEST, initial(), bind, view_id="v", findings=[CUE], panel_tiles=[TILE])
    assert result["readings"]["direct_labels"] == [] and result["issues"] == []


def test_additional_transcribed_information_is_retained_without_turning_it_into_a_mirror():
    shelf = {**LABEL, "role": "open_shelf", "source_text": "Open shelf"}
    result = reconcile_direct_labels(lambda stage, request, validate: validate(review([shelf])),
        REQUEST, initial(), bind, view_id="v", findings=[], panel_tiles=[TILE])
    assert result["readings"]["direct_labels"] == []
    assert result["direct_label_review"]["other_transcriptions"] == [shelf]


@pytest.mark.parametrize("response", [review([LABEL], ids=[]), review([LABEL], ids=["panel", "panel"]),
    review([{**LABEL, "id": "unknown"}]), review([{**LABEL, "source_text": ""}]),
    review([LABEL], unresolved=["panel"]), review(unresolved=["unknown"])])
def test_missing_coverage_unowned_labels_and_conflicts_cannot_pass(response):
    with pytest.raises(ValueError):
        reconcile_direct_labels(lambda stage, request, validate: validate(response), REQUEST, initial(), bind,
                                view_id="v", findings=[], panel_tiles=[TILE])


def test_large_views_are_fully_covered_in_bounded_batches_without_dropping_contours():
    tiles = [{**TILE, "id": f"P{i}"} for i in range(91)]; seen = []
    def invoke(stage, request, validate):
        ids = json.loads(request["messages"][0]["content"][4]["text"])["contour_ids"]
        seen.extend(ids)
        assert len(ids) <= 90
        return validate(review(ids=ids))
    result = reconcile_direct_labels(invoke, REQUEST, initial(), bind, view_id="v", findings=[], panel_tiles=tiles)
    assert seen == [tile["id"] for tile in tiles]
    assert len(result["direct_label_review"]["reviews"]) == 2


def test_native_polygon_mask_preserves_owned_pixels_and_excludes_neighbour_pixels():
    import pymupdf
    from PIL import Image

    with pymupdf.open() as document:
        page = document.new_page(width=100, height=100)
        page.draw_rect(pymupdf.Rect(10, 10, 40, 40), fill=(1, 0, 0), color=None)
        page.draw_rect(pymupdf.Rect(60, 60, 90, 90), fill=(0, 0, 1), color=None)
        view = {"bbox_normalized": [0, 0, 1, 1], "candidates": [{"id": "triangle",
            "bbox": [0, 0, 1100, 1100], "polygon": [(0, 0), (1100, 0), (0, 1100)]}]}
        tile, = render_panel_tiles(page, view)
    pixels = Image.open(BytesIO(tile["png"])).convert("RGB").getdata()
    assert any(r > 200 and g < 50 and b < 50 for r, g, b in pixels)
    assert not any(b > 200 and r < 50 and g < 50 for r, g, b in pixels)


def test_visual_request_stays_concise_while_saved_binding_keeps_contact_proof(monkeypatch):
    from tools import probe_estimation_v8_3 as pipeline
    from tools import estimation_direct_label_review as ownership
    from tools.probe_estimation_v7_4_front_evidence import DIRECT_LABEL_CHECK

    monkeypatch.setattr(pipeline, "typed_map", lambda *_args: {"type": "text", "text": "neutral map"})
    monkeypatch.setattr(pipeline, "render_caption_image", lambda *_args: None)
    monkeypatch.setattr(pipeline, "render_stroke_image", lambda *_args: b"stroke fixture")
    monkeypatch.setattr(ownership, "render_panel_tiles", lambda *_args: [TILE])
    view = {"view_id": "v", "candidates": [{"id": "panel", "bbox": [0, 0, 10, 10]}],
            "arrows": [{"root": [5, 20], "tips": [{"xy": [5, 10], "hits": ["panel"],
                "binding_basis": "boundary_contact", "contact_hits": ["panel"], "interior_hits": []}]}]}
    seen = []
    def invoke(stage, request, validate):
        seen.append(request)
        if stage.startswith("direct-label-review-"):
            return validate(review())
        return validate({"leader_readings": [{"id": "A01", "role": "other", "source_text": "note"}],
                         "stroke_readings": [], "direct_labels": []})
    result, _ = pipeline.read_marked(invoke, view, None,
        {"v": [{"type": "text", "text": "v"}, {"type": "image", "source": {"data": ""}}]}, [])
    content = seen[0]["messages"][0]["content"]
    model_tip = json.loads(content[4]["text"])["leader_groups"]["A01"]["tips"][0]
    assert set(model_tip) == {"xy_px", "contours"}
    assert content[-1]["text"] == DIRECT_LABEL_CHECK
    assert result["leaders"]["A01"]["tips"][0]["contact_contours"] == ["panel"]
