from copy import deepcopy
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from use_cases.estimation_shelf_recovery import recover_fixed_shelves


def _shelf_case(count):
    image = Image.new("L", (400, 360), 255)
    draw = ImageDraw.Draw(image)
    for i in range(count):
        y = 85 + i * 42
        draw.polygon([(75, y), (95, y - 12), (115, y), (95, y + 12)], fill=150, outline=0, width=2)
    draw.polygon([(119, 38), (165, 65), (165, 299), (119, 272)], fill=100, outline=0, width=2)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    target = {"view_id": "R", "bbox_normalized": [65 / 400, 55 / 360, 134 / 400, 277 / 360]}
    issue = {"role": "fixed_open_shelf", "reason": "ownership_pending"}
    finding = {"role": issue["role"], "status": issue["reason"], "source": target}
    coverage = {"objects": {"o": {"inventory_issues": [issue]}}}
    inventory = {"objects": {"o": {"source_review_findings": [finding], "observations": [],
                                   "items": [{"id": "B", "kind": "block", "children": []}]}},
                 "sheets": [{"review_status": "reviewed"}], "unassigned_source_findings": []}
    front = {"id": "D", "bbox": [51, 10, 96, 250]}
    extension = {"view_id": "E", "contour_id": "C", "bbox": [0, 10, 50, 250]}
    block = {"id": "B", "fixed_extensions": [extension]}
    analyze = {"islands": {"R": "Render"}, "objects": {"o": {"planner": {"blocks": [block]}}}}
    views = {"R": {"bbox_normalized": [0, 0, 1, 1], "page": 1}, "E": {"candidates": [front]}}
    rows = [{"role": "door_front", "instance_ref": "E:D", "dimensions": {
        "length": {"mm": 250, "refs": ["E:D"]}, "width": {"mm": 1100}}},
            {"role": "fixed_panel", "instance_ref": "E:C", "dimensions": {"width": {"mm": 145}}},
            {"role": "carcass_side", "dimensions": {"thickness": {"mm": 17}}}]
    parts = {"objects": {"o": {"blocks": [{"block_id": "B", "parts": rows}]}}}
    return coverage, inventory, parts, analyze, views, lambda _: buffer.getvalue()


@pytest.mark.parametrize("count", [2, 4])
def test_repairs_each_visible_shelf_once(count):
    args = _shelf_case(count)
    assert recover_fixed_shelves(*args) == [{"object_id": "o", "block_id": "B", "role": "fixed_open_shelf",
                                          "quantity": count}]
    rows = args[2]["objects"]["o"]["blocks"][0]["parts"]
    shelves = [row for row in rows if row["role"] == "fixed_open_shelf"]
    assert len({row["instance_ref"] for row in shelves}) == count
    assert all(row["quantity"] == 1 and all(d["mm"] for d in row["dimensions"].values()) for row in shelves)
    assert recover_fixed_shelves(*args) == []


def test_leaves_ambiguous_ownership_unresolved():
    args = _shelf_case(3)
    for rows, key in [(args[1]["objects"]["o"]["items"], "id"),
                      (args[2]["objects"]["o"]["blocks"], "block_id"),
                      (args[3]["objects"]["o"]["planner"]["blocks"], "id")]:
        rows.append({**deepcopy(rows[0]), key: "other"})
    before = deepcopy(args[1:3])
    assert recover_fixed_shelves(*args) == []
    assert args[1:3] == before
