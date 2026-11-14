import json

from use_cases.estimation import _element_groups, _element_rows_from_bom, _with_saved_element_ownership
from use_cases.estimation_structural_bom import _hinges_per_facade


def test_object_detail_keeps_parts_and_sums_identical_panels_across_blocks():
    rows = _element_rows_from_bom({
        "assemblies": [{"assembly_id": "drawer-bank", "front_groups": [{"front_kind": "drawer_front", "quantity": 3}]}],
        "parts": [
            {"assembly_id": "drawer-bank", "component_role": "drawer_side", "quantity": 6, "length_mm": 500, "width_mm": 180},
            {"assembly_id": "drawer-bank", "component_role": "drawer_bottom", "quantity": 3, "length_mm": 500, "width_mm": 400},
            {"assembly_id": "left", "component_role": "vertical_panel", "quantity": 1,
             "length_mm": 2650, "width_mm": 200, "thickness_mm": 18},
            {"assembly_id": "right", "component_role": "vertical_panel", "quantity": 2,
             "length_mm": 2650, "width_mm": 200, "thickness_mm": 18, "estimated_dimensions": {"width": {}}},
            {"assembly_id": "right", "component_role": "vertical_panel", "quantity": 1,
             "length_mm": 2650, "width_mm": 200, "thickness_mm": 16},
            {"component_role": "vertical_panel", "quantity": 1, "length_mm": 2650, "thickness_mm": 16},
            {"component_role": "vertical_panel", "quantity": 1, "length_mm": 2650, "thickness_mm": 16},
            {"component_role": "drawer_slide", "quantity": 2, "length_mm": 300},
        ],
    })

    assert rows == [
        {"label": "Drawer side", "quantity": 6, "size": "500 × 180 mm"},
        {"label": "Drawer bottom", "quantity": 3, "size": "500 × 400 mm"},
        {"label": "Vertical panel", "quantity": 3, "size": "≈ 2650 × 200 × 18 mm"},
        {"label": "Vertical panel", "quantity": 1, "size": "2650 × 200 × 16 mm"},
        {"label": "Vertical panel", "quantity": 1, "size": "2650 × — × 16 mm"},
        {"label": "Vertical panel", "quantity": 1, "size": "2650 × — × 16 mm"},
        {"label": "Drawer slide", "quantity": 2, "size": "300 mm"},
    ]



def test_elements_group_matching_drawer_parts_only_inside_their_block():
    front = {"component_role": "drawer_front", "length_mm": 590, "width_mm": 220,
             "thickness_mm": 17, "quantity": 1}
    sides = {"component_role": "drawer_box_side", "length_mm": 500, "width_mm": 180,
             "thickness_mm": 17, "quantity": 2}
    groups = _element_groups({
        "blocks": [{"id": "B01", "name": "Drawer bank"}, {"id": "B02"}],
        "parts": [
            *({**front, "block_id": "B01"} for _ in range(3)),
            *({**sides, "block_id": "B01"} for _ in range(3)),
            {**front, "block_id": "B02", "scope_quantity": 2},
            {"component_role": "shared_worktop", "block_id": None, "quantity": 1, "thickness_mm": 30},
        ],
    })
    assert [group["label"] for group in groups] == ["B01 · Drawer bank", "B02 · Drawer cabinet", "Common parts"]
    assert [[row["quantity"] for row in group["rows"]] for group in groups] == [[3, 6], [2], [1]]


def test_legacy_element_ownership_uses_only_the_matching_immutable_report(monkeypatch):
    checked = {"parts": [{"component_role": "drawer_front", "length_mm": 500, "quantity": 1}]}
    source = {"run_id": "run", "estimate_id": "estimate", "source_audit_sha256": "digest"}
    object_row = {"run_id": "run", "company_id": "company"}
    report = {"source_audit_sha256": "digest", "objects": {"object": {
        "blocks": [{"id": "B01"}],
        "parts": [{"role": "drawer_front", "quantity": 1, "dimensions": {"length": {"mm": 500}},
                   "block_id": "B01"}],
    }}}
    calls = []

    def load(**kwargs):
        calls.append(kwargs)
        return {"status": "ready", "payload": json.dumps(report)}

    monkeypatch.setattr("use_cases.estimation_parts_check_runtime.load_parts_check", load)
    scope = {"estimate_id": "estimate", "object_id": "object"}
    enriched = _with_saved_element_ownership(None, checked, source, object_row, **scope)
    assert enriched["parts"][0]["block_id"] == "B01"
    assert _with_saved_element_ownership(None, enriched, source, object_row, **scope) is enriched
    assert len(calls) == 1
    assert calls[0]["company_id"] == "company"

    report["objects"]["object"]["parts"][0]["dimensions"]["length"]["mm"] = 501
    fallback = _with_saved_element_ownership(None, checked, source, object_row, **scope)
    assert fallback is checked
    assert _element_groups(fallback)[0]["label"] == ""


def test_hinge_thresholds_include_800_and_2000_mm():
    assert [_hinges_per_facade(height) for height in (799, 800, 801, 1999, 2000, 2001)] == [2, 2, 3, 3, 3, 4]
