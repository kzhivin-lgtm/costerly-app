from ui.object_detail_view import _group_summary_value, _number_text, _quantity, _row_values, _table_html


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


def test_nan_values_do_not_crash_object_detail_number_rendering():
    assert _number_text(float("nan")) == ""
    assert _quantity(float("nan")) == "—"
    assert _group_summary_value("Qty", [{"qty": float("nan")}, {"qty": 2}]) == "2"
    assert _group_summary_value("Cost", [{"cost": float("nan")}, {"cost": 25}]) == "₪25"
