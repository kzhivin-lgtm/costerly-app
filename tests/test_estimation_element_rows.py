from use_cases.estimation import _element_rows_from_bom


def test_object_detail_groups_matching_panels_and_exposes_drawers_as_boxes():
    rows = _element_rows_from_bom({
        "assemblies": [{"assembly_id": "drawer-bank", "front_groups": [{"front_kind": "drawer_front", "quantity": 3}]}],
        "parts": [
            {"assembly_id": "drawer-bank", "component_role": "drawer_side", "quantity": 6, "length_mm": 500, "width_mm": 180},
            {"assembly_id": "drawer-bank", "component_role": "drawer_bottom", "quantity": 3, "length_mm": 500, "width_mm": 400},
            {"assembly_id": "screen", "component_role": "vertical_panel", "quantity": 1, "length_mm": 2650, "width_mm": 200},
            {"assembly_id": "screen", "component_role": "vertical_panel", "quantity": 1, "length_mm": 2650, "width_mm": 200},
        ],
    })

    assert rows == [
        {"label": "Drawer box", "quantity": 3, "size": ""},
        {"label": "Element", "quantity": 2, "size": "2650 × 200 mm"},
    ]
