from use_cases.estimation import _element_rows_from_bom


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
