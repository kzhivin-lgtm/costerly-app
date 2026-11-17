import json
from decimal import Decimal

import pandas as pd

from use_cases.block_assembly import calculate_block_assembly


def test_assembly_uses_slide_pairs_and_once_per_block_setup():
    report = {"objects": {"one": {
        "blocks": [{"id": "B01"}, {"id": "B02"}],
        "parts": [
            {"block_id": "B01", "role": "pull_out_shelf", "quantity": 2},
            {"block_id": "B01", "role": "pull_out_shelf_slide", "quantity": 1, "unit": "pair", "scope_quantity": 2},
            {"block_id": "B01", "role": "glass_box_long_wall", "quantity": 4},
            {"block_id": "B02", "role": "mirror_mounting_panel", "quantity": 1},
        ],
    }}}
    result = calculate_block_assembly(report, object_id="one")
    first, second = result["blocks"]
    assert (first["active_minutes"], first["planned_minutes"], first["base_labor_ils"]) == (
        22, Decimal("34.375"), Decimal("28.65"),
    )
    assert not first["issues"]
    assert second["operations"] == []
    assert result["active_minutes"] == 22


def test_assembly_does_not_count_incomplete_drawer_boxes_or_duplicate_evidence():
    report = {"objects": {"one": {
        "blocks": [{"id": "B01"}],
        "inventory_issues": [{"reason": "duplicate_part_evidence", "role": "hinge", "source_ref": "view-1:C01"}],
        "parts": [
            {"block_id": "B01", "role": "drawer_box_side", "quantity": 2},
            {"block_id": "B01", "role": "drawer_box_end", "quantity": 1},
            {"block_id": "B01", "role": "drawer_box_bottom", "quantity": 1},
            {"block_id": "B01", "role": "drawer_slide", "quantity": 1, "unit": "piece"},
            {"block_id": "B01", "role": "hinge", "quantity": 2, "instance_ref": "view-1:C01"},
            {"role": "fixed_panel", "quantity": 1},
        ],
    }}}
    result = calculate_block_assembly(report, object_id="one")
    block, = result["blocks"]
    assert block["operations"] == []
    assert block["issues"] == [
        "hinge: duplicate part evidence", "Drawer panels do not form complete boxes",
        "Drawer boxes, fronts or slide pairs need review",
    ]
    assert result["common_roles_for_review"] == ["fixed_panel"]


def test_object_detail_calculates_assembly_from_one_parts_read_when_materials_are_pending(monkeypatch):
    from screens import estimation_labor_v1 as screen

    reads = []
    report = {"objects": {"one": {"blocks": [{"id": "B01"}],
                                 "parts": [{"block_id": "B01", "role": "fixed_panel", "quantity": 1}]}}}

    def parts(**scope):
        reads.append(scope)
        return {"status": "ready", "payload": json.dumps(report)}

    monkeypatch.setattr(screen, "load_parts_check", parts)
    monkeypatch.setattr(screen, "fetch_rfq_estimate_material_plan", lambda *_: pd.DataFrame())
    result = screen._calculate(object(), identity=("company", "run", "estimate", "one"))

    assert len(reads) == 1
    assert result["status"] == "waiting_for_materials"
    assert result["assembly"]["active_minutes"] == 12
