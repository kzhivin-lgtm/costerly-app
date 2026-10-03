import pandas as pd

from ui.object_detail_view import _group_summary_value, _number_text, _quantity, _row_values, _table_html
from use_cases import estimation


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


def test_server_material_edit_recalculates_line_and_object_totals(monkeypatch):
    lines = [
        {
            "line_id": "material-1", "section": "material", "source": "catalog",
            "unit_cost": 100.0, "quantity": 2.0, "cost": 200.0,
            "raw_agent_json": {},
        },
        {
            "line_id": "consumables", "section": "material", "source": "pricing_policy",
            "cost": 10.0, "raw_agent_json": {"percent": 5, "basis": "materials"},
        },
    ]
    totals = {}

    monkeypatch.setattr(estimation, "company_auth_enabled", lambda: False)
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        estimation,
        "fetch_rfq_estimate_lines_for_object",
        lambda *_args, **_kwargs: pd.DataFrame(lines),
    )
    monkeypatch.setattr(
        estimation,
        "fetch_rfq_object_estimates",
        lambda *_args, **_kwargs: pd.DataFrame([
            {"object_id": "object-1", "company_id": "company-1"}
        ]),
    )
    monkeypatch.setattr(
        estimation,
        "fetch_company_overhead_settings",
        lambda *_args, **_kwargs: pd.DataFrame([
            {"vat_percent": 18, "employer_load_percent": 25}
        ]),
    )

    def update_line(_client, *, line_id, values, **_kwargs):
        row = next(item for item in lines if item["line_id"] == line_id)
        row.update(values)

    monkeypatch.setattr(estimation, "update_rfq_estimate_line", update_line)
    monkeypatch.setattr(
        estimation,
        "update_rfq_object_estimate_totals",
        lambda _client, **values: totals.update(values),
    )

    estimation.apply_object_detail_line_edit(
        estimate_id="estimate-1",
        object_id="object-1",
        line_id="material-1",
        field="unit_cost",
        value="200",
    )

    assert lines[0]["cost"] == 400.0
    assert lines[1]["cost"] == 20.0
    assert totals["self_cost_ex_vat"] == 420.0
    assert totals["vat_amount"] == 75.6
    assert totals["self_cost_total"] == 495.6
