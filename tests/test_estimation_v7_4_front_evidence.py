from tools.probe_estimation_v7_4_front_evidence import bind_front_roles


def test_label_stays_with_its_leader_tip_and_stroke_stays_with_its_leaf():
    contours = {
        "C1": [0, 0, 15, 10],
        "C2": [15, 0, 30, 10],
        "C3": [30, 0, 45, 10],
    }
    leaders = {
        "A1": {"tips": [
            {"xy_px": [5, 5], "contours": ["C1"]},
            {"xy_px": [6, 5], "contours": ["C1"]},
        ]},
        "A2": {"tips": [{"xy_px": [20, 5], "contours": ["C2"]}]},
    }
    readings = {
        "leader_readings": [
            {"id": "A1", "role": "drawer", "source_text": "Drawer"},
            {"id": "A2", "role": "pull_out_shelf", "source_text": "Pull-out shelf"},
        ],
        "stroke_readings": [{"id": "C3", "role": "hinged_door"}],
        "direct_labels": [],
    }

    result = bind_front_roles(readings, leaders=leaders, contours=contours, stroke_ids={"C3"})

    assert {item["candidate_id"]: item["role"] for item in result["items"]} == {
        "C1": "drawer", "C2": "pull_out_shelf", "C3": "hinged_door",
    }
    assert result["counts"] == {"drawer": 1, "pull_out_shelf": 1, "hinged_door": 1}
    assert not result["issues"]


def test_conflicting_roles_and_ambiguous_tips_are_excluded_from_counts():
    contours = {"C1": [0, 0, 15, 10], "C2": [15, 0, 30, 10]}
    leaders = {
        "A1": {"tips": [{"xy_px": [5, 5], "contours": ["C1"]}]},
        "A2": {"tips": [{"xy_px": [15, 5], "contours": ["C1", "C2"]}]},
    }
    readings = {
        "leader_readings": [
            {"id": "A1", "role": "drawer", "source_text": "Drawer"},
            {"id": "A2", "role": "pull_out_shelf", "source_text": "Pull-out shelf"},
        ],
        "stroke_readings": [{"id": "C1", "role": "cut_or_fixed"}],
        "direct_labels": [],
    }

    result = bind_front_roles(readings, leaders=leaders, contours=contours, stroke_ids={"C1"})

    assert not result["counts"]
    assert {issue["reason"] for issue in result["issues"]} == {
        "conflicting evidence", "no unique target contour",
    }
