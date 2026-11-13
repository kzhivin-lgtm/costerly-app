from tools.estimation_block_geometry import supported_extension_dimensions
from tools.probe_cb_block_boundaries import matched_frame_pairs, supported_extensions
from tools.probe_estimation_v8_3 import structural_front


def _rect(cid, box):
    left, top, right, bottom = box
    return {"id": cid, "bbox": box, "area": (right - left) * (bottom - top),
            "polygon": [(left, top), (right, top), (right, bottom), (left, bottom)]}


def _view(vid, candidates):
    return {"view_id": vid, "object_id": "assembly", "page": 1, "width": 1000,
            "height": 1000, "candidates": candidates}


def _frame(vid):
    frame = {"id": "frame", "bbox": [0, 0, 100, 100], "area": 2400,
             "polygon": [(0, 0), (100, 0), (100, 100), (90, 100), (90, 10), (70, 10),
                         (70, 100), (60, 100), (60, 10), (40, 10), (40, 100),
                         (30, 100), (30, 10), (10, 10), (10, 100), (0, 100)]}
    openings = [_rect(str(left), [left, 10, left + 20, 100]) for left in (10, 40, 70)]
    return _view(vid, [frame, *openings, _rect("rail", [0, 100, 100, 105])])


def test_detail_with_matching_structural_frame_filters_openings_but_preserves_marked_door():
    views = {vid: _frame(vid) for vid in ("main", "detail")}
    projections = {"main": "Front elevation", "detail": "Detail"}
    observations = [{"view_id": "main", "candidate_id": "10", "role": "hinged_door"}]
    context = {"objects": [{"object_id": "assembly", "accepted_observations": []}]}
    pairs = matched_frame_pairs(views, projections)
    assert len(pairs) == 1
    assert structural_front(views, projections, observations, context, frame_pairs=pairs)[0] == []
    protected = matched_frame_pairs(views, projections, {("main", "10")})
    assert protected == []
    assert structural_front(views, projections, observations, context, frame_pairs=protected)[0] == observations
    assert not matched_frame_pairs(views, {"main": "Detail", "detail": "Detail"})


def test_supported_extension_requires_contact_on_side_and_plan():
    front = _view("main", [])
    side = _view("side", [
        _rect("body", [100, 100, 400, 800]), _rect("top", [400, 300, 800, 320]),
        _rect("leg", [730, 320, 750, 900]),
    ])
    plan = _view("plan", [_rect("top", [400, 100, 800, 700]), _rect("host", [100, 100, 400, 700])])
    views = {v["view_id"]: v for v in (front, side, plan)}
    projections = {"main": "Front elevation", "side": "Side view", "plan": "Top view"}
    printed = {
        "main": [{"axis": "x", "bounds": [100, 700], "value_mm": 600}],
        "side": [{"axis": "x", "bounds": [100, 400], "value_mm": 300},
                 {"axis": "y", "bounds": [300, 900], "value_mm": 600}],
        "plan": [{"axis": "x", "bounds": [400, 800], "value_mm": 400},
                 {"axis": "y", "bounds": [100, 700], "value_mm": 600}],
    }
    bank = {"view_id": "main", "bbox": [100, 500, 700, 700], "frame": "drawer-bank"}
    extension, = supported_extensions(side)
    assert supported_extension_dimensions(views, projections, printed, bank, extension)["depth"]["value_mm"] == 400
    plan["candidates"][-1] = _rect("host", [100, 100, 390, 700])
    assert supported_extension_dimensions(views, projections, printed, bank, extension) is None
    side["candidates"][0] = _rect("body", [100, 100, 390, 800])
    assert supported_extensions(side) == []
