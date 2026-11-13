import pytest

from use_cases.estimation_door_hardware import add_push_latches


@pytest.mark.parametrize("note,expected", [
    ("", {"V1:C1"}),
    ("5. Pyku: Be3 pyuek.", {"V1:C1", "V1:C3"}),
    ("Петли: Blum без пружины с толкателем", {"V1:C1", "V1:C3"}),
    ("Drawers: no handles", {"V1:C1"}),
])
def test_one_push_latch_per_confirmed_door_leaf(note, expected):
    view = {"width": 100, "height": 100, "bbox_normalized": [0, 0, 1, 1]}
    faces = [
        {"view_id": "V1", "candidate_id": f"C{i}", "role": role, "bbox_px": [left, 0, left + 15, 50]}
        for i, (left, role) in enumerate([(0, "hinged_door"), (20, "hinged_door"),
                                          (40, "hinged_door"), (60, "drawer"), (80, "lift_up")], 1)
    ]
    readings = [
        {"role": role, "source": {"view_id": "V1", "bbox_normalized": box}}
        for role, box in [("door_without_handle", [0, 0, .15, .5]), ("door_with_pull", [.2, 0, .35, .5])]
    ]
    scope = {"parts": [
        {"role": role, "instance_ref": f"V1:C{i}", "quantity": 1}
        for i, role in enumerate(["door_front"] * 3 + ["drawer_front", "lift_up_front"], 1)
    ]}
    parts = {"objects": {"o": {"blocks": [scope], "shared_parts": []}}}
    analyze = {"objects": {"o": {"front": {"faces": faces, "door_opening_observations": readings}}}}
    inputs = [{"input_payload": {"object": {"object_id": "o"}, "evidence": {
        "ocr_blocks": [{"block_ref": "OCR", "text": note}],
    }}}]
    add_push_latches(parts, analyze, {"V1": view}, inputs)
    add_push_latches(parts, analyze, {"V1": view}, inputs)
    latches = [row for row in scope["parts"] if row["role"] == "push_latch"]
    assert {row["instance_ref"] for row in latches} == expected
    assert sum(row["quantity"] for row in latches) == len(expected)
    assert all(row["unit"] == "piece" for row in latches)
