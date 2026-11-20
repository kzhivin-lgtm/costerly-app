from copy import deepcopy

from tools.estimation_v83_locator import ground_native_shell_proposal


def face(cid, box):
    x, y, u, v = box
    return {"id": cid, "bbox": box, "area": (u - x) * (v - y),
            "polygon": [(x, y), (u, y), (u, v), (x, v)]}


def source(extra):
    view = {"view_id": "v", "candidates": [face("display", [0, 20, 100, 80]),
            face("door", [200, 20, 250, 80]), extra]}
    plan = {"blocks": [
        {"id": "display", "basis": "drawer_and_pull_out_bay", "appearances": {"v": ["display"]}},
        {"id": "return", "basis": "return_door_band", "appearances": {"v": ["door"]}, "positions": [["door"]]},
    ], "object_parts": []}
    proposal = {"add": {"display": [], "return": [extra["id"]]}, "plinth": [], "unresolved": []}
    return view, plan, proposal


def test_unsupported_claim_cannot_occupy_another_cabinets_native_plane():
    view, plan, proposal = source(face("cap", [0, 0, 100, 20])); before = deepcopy(proposal)
    result = ground_native_shell_proposal(plan, view, proposal)
    assert "cap" not in result["add"]["return"]
    assert "cap" in result["add"]["display"]
    assert result["grounding_review"][0]["claimed_block_id"] == "return"
    assert result["grounding_review"][0]["grounded_block_ids"] == ["display"]
    assert proposal == before


def test_positive_native_side_contact_is_kept_even_outside_the_face_band():
    view, plan, proposal = source(face("side", [250, 20, 255, 80]))
    result = ground_native_shell_proposal(plan, view, proposal)
    assert "side" in result["add"]["return"]
    assert result["grounding_review"] == []
