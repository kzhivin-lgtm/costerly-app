import pytest

from tools.probe_estimation_v7_4_visual_front import bind_island_faces, bind_visual_roles


def test_same_view_faces_are_preserved_without_reporting_a_physical_total():
    frame = {"size": (40, 20), "contours": {"C01": [0, 0, 20, 20], "C02": [20, 0, 40, 20]}}
    item = {
        "role": "drawer", "evidence": "two adjacent rectangles",
        "appearances": [
            {"view_id": "view-001", "candidate_id": "C01", "bbox_px": None},
            {"view_id": "view-001", "candidate_id": "C02", "bbox_px": None},
        ],
    }
    bound = bind_visual_roles({"items": [item]}, {"view-001": frame})
    assert bound["counts"] is None
    assert [a["candidate_id"] for a in bound["items"][0]["appearances"]] == ["C01", "C02"]
    assert bound["issues"] == [{"item": 1, "view_id": "view-001", "candidate_id": "C02",
                                "reason": "multiple faces from one view grouped into one item"}]


def test_one_face_per_view_can_describe_one_physical_item():
    frame = {"size": (40, 20), "contours": {"C01": [0, 0, 20, 20]}}
    item = {
        "role": "drawer", "evidence": "same front in two views",
        "appearances": [
            {"view_id": "view-001", "candidate_id": "C01", "bbox_px": None},
            {"view_id": "view-002", "candidate_id": "C01", "bbox_px": None},
        ],
    }
    bound = bind_visual_roles({"items": [item]}, {"view-001": frame, "view-002": frame})
    assert bound["counts"] == {"drawer": 1}
    assert not bound["issues"]


def test_per_island_records_keep_adjacent_faces_and_repeated_views_separate():
    frame = {"size": (40, 20), "contours": {"C01": [0, 0, 20, 20], "C02": [20, 0, 40, 20]}}
    identities = [("view-001", "C01"), ("view-001", "C02"), ("view-002", "C01")]
    readings = {"faces": [
        {"view_id": view, "candidate_id": ident, "bbox_px": None, "role": "drawer", "evidence": "gap"}
        for view, ident in identities
    ]}

    bound = bind_island_faces(readings, {"view-001": frame, "view-002": frame})

    assert [(row["view_id"], row["candidate_id"]) for row in bound["faces"]] == identities
    assert bound["faces"][1]["bbox_px"] == [20, 0, 40, 20]
    assert not bound["issues"]
    assert "counts" not in bound


def test_per_island_contract_rejects_nested_appearance_groups():
    readings = {"faces": [{"role": "drawer", "evidence": "gap", "appearances": []}]}
    with pytest.raises(ValueError, match="independent Island face records"):
        bind_island_faces(readings, {})
