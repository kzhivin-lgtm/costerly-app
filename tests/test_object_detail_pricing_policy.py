from ui.object_detail_view import _row_values, _table_html


def _section():
    return {
        "key": "material",
        "title": "Materials",
        "columns": ["Material", "Unit", "Unit cost", "Qty", "Cost"],
        "rows": [],
    }


def test_pricing_policy_material_row_is_locked_and_exposes_formula_percent():
    row = {
        "group": "Materials", "line_id": "object-1_material_policy_consumables",
        "item": "Consumables", "unit": "% of materials", "unit_cost": 5,
        "qty": 1, "cost": 25, "locked": True, "policy_percent": 5,
    }

    values = _row_values(_section(), row)
    html = _table_html({**_section(), "rows": [row]})

    assert all("contenteditable" not in value for value in values)
    assert "5%" in values[2]
    assert 'data-policy-percent="5"' in html
