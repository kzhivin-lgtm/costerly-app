import pandas as pd

from ui.object_detail_view import (
    MATERIAL_PURCHASE_COLUMNS, _footer_html, _group_summary_value, _number_text, _quantity, _row_values, _table_html,
)
from use_cases import estimation
from use_cases.estimation import _material_rows_from_plan


def _section():
    return {
        "key": "material",
        "title": "Materials",
        "columns": ["Material", "Unit", "Material per item", "Unit cost", "Final cost"],
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
    assert "5%" in values[3]
    assert 'data-policy-percent="5"' in html


def test_material_cells_swap_quantity_and_unit_cost_without_changing_grid_shape():
    row = {
        "item": "MDF", "unit": "m²", "qty": 2.5, "unit_cost": 104,
        "cost": 260, "locked": False,
    }

    values = _row_values(_section(), row)

    assert len(values) == 5
    assert 'data-field="quantity"' in values[2]
    assert "2.5" in values[2]
    assert 'data-field="unit_cost"' in values[3]
    assert "₪104" in values[3]


def test_price_source_is_shown_as_minimal_marker_beside_editable_unit_cost():
    row = {
        "item": "Metal profile angle", "unit": "m", "qty": 6.59,
        "unit_cost": 31, "cost": 204, "price_source": "A",
    }

    values = _row_values(_section(), row)

    assert values[0] == "Metal profile angle"
    assert 'data-field="unit_cost"' in values[3]
    assert 'object-detail-material-source' in values[3]
    assert '>A</span>' in values[3]


def test_project_allocation_never_displays_an_effective_area_price():
    row = {
        "item": "LDSP 18 mm", "unit": "project allocation", "qty": None, "unit_cost": None,
        "cost": 212, "price_source": "I",
        "material_plan_allocation": {
            "purchase_quantity": 1, "purchase_unit": "sheet", "price_per_purchase_unit": 212,
        },
    }

    values = _row_values(_section(), row)

    assert "Project allocation" in values[1]
    assert "1 sheet" in values[2]
    assert "₪212" in values[3]
    assert "contenteditable" not in values[2]
    assert ">I</span>" in values[3]


def test_material_purchase_table_shows_demand_and_purchase_without_allocation_language():
    section = {
        "key": "material", "title": "Materials",
        "columns": MATERIAL_PURCHASE_COLUMNS,
        "rows": [{
            "item": "Veneered MDF 18 mm", "price_source": "A", "required_material_value": 5.2,
            "required_material_unit": "m²", "required_material_line_id": "__material_requirement__:mdf",
            "purchase_unit": "sheet 2440 × 1220 mm", "purchase_quantity_value": 2,
            "purchase_unit_cost": 199.75,
            "purchase_quantity_unit": "sheet", "purchase_quantity_line_id": "__material_purchase__:mdf", "total": 400,
        }],
    }

    values = _row_values(section, section["rows"][0])
    html = _table_html(section)

    assert ">A</span><span class=\"object-detail-material-name\">Veneered MDF 18 mm</span>" in values[0]
    assert "required_material" in values[1]
    assert '>5.2</div><span class="object-detail-material-input-unit">m²</span>' in values[1]
    assert "object-detail-purchase-unit" in values[2]
    assert "₪200" in values[3]
    assert 'data-original-value="5.2"' in values[1]
    assert "contenteditable" not in values[3]
    assert "purchase_quantity" in values[4]
    assert 'data-original-value="2"' in values[4]
    assert "sheet" not in values[4]
    assert html.index("Purchase<br> unit") < html.index("Unit<br> price") < html.index(">Purchase quantity<")
    assert "Project allocation" not in html
    assert "Project material plan" not in html


def test_material_purchase_table_shows_locked_profile_formula_without_purchase_inputs():
    section = {
        "key": "material", "title": "Materials",
        "columns": MATERIAL_PURCHASE_COLUMNS,
        "rows": [{
            "item": "Paint consumables", "locked": True, "policy_percent": 10,
            "policy_basis": "coatings", "total": 25,
        }],
    }

    values = _row_values(section, section["rows"][0])

    assert all("contenteditable" not in value for value in values)
    assert values[1] == "10% of coating materials"
    assert values[2] == "Formula"
    assert values[3] == "—"
    assert values[4] == "—"
    assert "₪25" in values[5]


def test_assumption_rows_hide_assembly_roles_but_preserve_net_demand_and_purchase():
    rows = _material_rows_from_plan({
        "lines": [{
            "authority": "assumption", "display_name": "Cabinet Carcass", "purchase_kind": "sheet",
            "purchasable_dimensions": {"length_mm": 2440, "width_mm": 1220},
            "purchase_quantity": 2, "total_cost": 400,
            "allocations": [{
                "object_id": "object-1", "material_requirement_id": "board", "length_mm": 2650,
                "width_mm": 430, "quantity": 2,
            }],
        }],
        "assumption_fallbacks": [{
            "material_requirement_id": "board", "source_name": "Cabinet Carcass",
            "material_family": "particleboard", "specification": {"thickness_mm": 18},
        }],
    }, object_id="object-1")

    assert [{key: row[key] for key in (
        "item", "price_source", "required_material_value", "required_material_unit",
        "required_material_line_id", "purchase_unit", "purchase_quantity_value",
        "purchase_quantity_unit", "purchase_quantity_line_id", "material_family", "total",
    )} for row in rows] == [{
        "item": "Particleboard 18 mm", "price_source": "A", "required_material_value": 2.279,
        "required_material_unit": "m²", "required_material_line_id": "__material_requirement__:board",
        "purchase_unit": "sheet 2440 × 1220 mm", "purchase_quantity_value": 2.0,
        "purchase_quantity_unit": "sheet", "purchase_quantity_line_id": "__material_purchase__:None",
        "material_family": "particleboard", "total": 400.0,
    }]


def test_nan_values_do_not_crash_object_detail_number_rendering():
    assert _number_text(float("nan")) == ""
    assert _quantity(float("nan")) == "—"
    assert _group_summary_value("Qty", [{"qty": float("nan")}, {"qty": 2}]) == "2"
    assert _group_summary_value("Cost", [{"cost": float("nan")}, {"cost": 25}]) == "₪25"


def test_v3_object_detail_loads_with_a_planned_material_plan(monkeypatch):
    monkeypatch.setattr(estimation, "company_auth_enabled", lambda: False)
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        estimation,
        "fetch_rfq_object_estimates",
        lambda *_args, **_kwargs: pd.DataFrame([{
            "object_id": "object-1", "run_id": "run-1", "company_id": "company-1",
            "object_name": "Cabinet", "quantity": 1, "approved": False,
        }]),
    )
    monkeypatch.setattr(
        estimation,
        "fetch_rfq_estimate_lines_for_object",
        lambda *_args, **_kwargs: pd.DataFrame([{
            "section": "material", "group_name": "Materials", "line_id": "line-1",
            "item_name": "MDF", "unit": "m²", "unit_cost": None, "quantity": 2,
            "cost": None, "source": "estimation_v3_material_facts", "raw_agent_json": {},
        }]),
    )
    monkeypatch.setattr(
        estimation,
        "fetch_rfq_estimate_material_plan",
        lambda *_args, **_kwargs: pd.DataFrame([{
            "plan_status": "planned", "plan_payload": {"status": "planned"},
        }]),
    )
    monkeypatch.setattr(
        estimation,
        "fetch_company_overhead_settings",
        lambda *_args, **_kwargs: pd.DataFrame([{"vat_percent": 18, "employer_load_percent": 25}]),
    )

    detail = estimation.load_object_detail_data(estimate_id="estimate-1", object_id="object-1")

    assert detail["material_plan_ready"] is True
    assert detail["material_plan_status"] == "planned"


def test_material_save_receipt_matches_detail_without_loading_preview_or_settings(monkeypatch):
    plan = {"status": "needs_review", "parts_check": {"object-1": {
        "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/preview.png",
        "unpriced_requirements": ["missing"],
        "materials": [{"requirement_id": "missing", "source_name": "Unpriced panel", "quantity": 1.5, "unit": "m2"}],
    }}}
    checks = []
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(estimation, "_assert_screen_estimate_access", lambda _client, estimate_id, **_: checks.append(estimate_id))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan", lambda *_: pd.DataFrame([{"plan_payload": plan}]))
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *_: pd.DataFrame([{
        "object_id": "object-1", "company_id": "company-1", "quantity": 2,
        "self_cost_ex_vat": 100, "vat_amount": 18, "self_cost_total": 118,
    }]))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines_for_object", lambda *_, **__: pd.DataFrame([{
        "section": "material", "source": "pricing_policy", "item_name": "Consumables",
        "cost": 5, "raw_agent_json": {"percent": 5, "basis": "materials"},
    }]))
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *_: pd.DataFrame())
    detail = estimation.load_object_detail_data(estimate_id="estimate-1", object_id="object-1")

    def unexpected(*_, **__):
        raise AssertionError("The save receipt does not need this read")

    monkeypatch.setattr(estimation, "_estimation_preview_url", unexpected)
    monkeypatch.setattr(estimation, "_element_rows_from_bom", unexpected)
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", unexpected)
    receipt = estimation.load_object_detail_material_receipt(estimate_id="estimate-1", object_id="object-1")
    assert checks == ["estimate-1", "estimate-1"]
    assert receipt["sections"][0]["rows"] == detail["sections"][0]["rows"]
    assert receipt["quantity"] == detail["quantity"] == 2
    assert receipt["self_cost"] == {key: detail["self_cost"][key] for key in ("excl_vat", "vat", "total")}


def test_object_detail_footer_has_approve_and_a_disabled_save_between_actions():
    footer = _footer_html("run-1", "estimate-1", "object-1")
    assert footer.index("Back to Objects") < footer.index("Save changes") < footer.index(">APPROVE<")
    assert 'object-detail-material-save" disabled' in footer
    assert 'data-streamlit-bridge-key="object_detail_approve_bridge"' in footer


def test_legacy_object_approval_uses_existing_costs(monkeypatch):
    approved = []
    monkeypatch.setattr(estimation, "company_auth_enabled", lambda: False)
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    def unexpected_recalculation(*_args, **_kwargs):
        raise AssertionError("Approval recalculated a saved total")

    monkeypatch.setattr(estimation, "_recalculate_object_estimate_totals", unexpected_recalculation)
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_approved", lambda _, **values: approved.append(values))

    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan", lambda *_a: pd.DataFrame())

    estimation.approve_object_estimate(estimate_id="estimate-1", object_id="object-1")

    assert approved == [{"estimate_id": "estimate-1", "object_id": "object-1", "approved": True}]


def test_quantity_and_material_draft_uses_new_quantity_in_one_scoped_job(monkeypatch):
    from use_cases import estimation_runtime

    writes = []
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(estimation, "company_auth_enabled", lambda: False)
    monkeypatch.setattr(estimation, "_object_material_context", lambda *_args, **_kwargs: {
        "quantity": 1, "company_id": "company-1", "run_id": "run-1",
    })
    plan = {"status": "planned", "parts_check_source": {"run_id": "run-1"}, "lines": [{
        "selection_key": "mdf", "allocations": [{"object_id": "object-1", "material_requirement_id": "mdf"}],
    }]}
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan",
                        lambda *_args: pd.DataFrame([{"plan_payload": plan}]))
    monkeypatch.setattr(estimation, "_material_norms_from_plan", lambda *_args: {("object-1", "mdf"): ("m2", 2)})
    monkeypatch.setattr(estimation_runtime, "queue_material_plan_recalculation", lambda **kwargs: writes.append(kwargs))

    estimation.save_object_detail_material_edits(estimate_id="estimate-1", object_id="object-1", edits=[
        {"field": "required_material", "lineId": "__material_requirement__:mdf", "value": "5.5"},
        {"field": "object_quantity", "lineId": "__object__", "value": "2"},
    ])

    (scoped_job,) = writes
    assert scoped_job["norm_edits"]["object-1", "mdf"]["quantity_per_item"] == 2.75
    assert scoped_job["norm_keys"] == {"mdf"}
    assert scoped_job["quantity_edits"] == {"object-1": 2}
    assert not scoped_job["purchase_keys"]


def test_required_runner_sets_are_saved_as_physical_pieces(monkeypatch):
    from use_cases import estimation_runtime

    queued = []
    selection = "hardware_drawer_slide|nominal_length=300"
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: object())
    monkeypatch.setattr(estimation, "company_auth_enabled", lambda: False)
    monkeypatch.setattr(estimation, "_object_material_context", lambda *_args, **_kwargs: {
        "quantity": 1, "company_id": "company-1", "run_id": "run-1",
    })
    plan = {"status": "planned", "parts_check_source": {"run_id": "run-1"}, "lines": [{
        "selection_key": selection, "purchase_kind": "piece", "package_quantity": 2,
        "allocations": [{"object_id": "object-1", "material_requirement_id": "runner", "quantity": 6}],
    }]}
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan",
                        lambda *_args: pd.DataFrame([{"plan_payload": plan}]))
    monkeypatch.setattr(estimation_runtime, "queue_material_plan_recalculation", lambda **kwargs: queued.append(kwargs))

    estimation.save_object_detail_material_edits(estimate_id="estimate-1", object_id="object-1", edits=[
        {"field": "required_material", "lineId": "__material_requirement__:runner", "value": "4"},
    ])

    job, = queued
    override = job["norm_edits"]["object-1", "runner"]
    assert (override["quantity_per_item"], override["unit"]) == (8, "piece")
    assert job["norm_keys"] == {selection}
    assert not job["purchase_keys"]


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


def test_material_table_only_shows_current_object_quantities_and_cost():
    section = {
        "key": "material", "title": "Materials", "columns": MATERIAL_PURCHASE_COLUMNS,
        "rows": [{
            "item": "Drawer runner", "required_material_value": 3, "required_material_unit": "set",
            "purchase_unit": "set", "purchase_quantity_value": 3, "purchase_unit_cost": 72,
            "purchase_quantity_line_id": "__material_purchase__:runner",
            "total": 216,
        }],
    }
    html = _table_html(section)
    assert "Purchase quantity" in html and ">Total<" in html
    assert "project" not in html.lower()
    assert 'data-original-value="3"' in html
    assert ">set<" in html and ">₪216</span>" in html


def test_continuous_material_quantities_round_in_both_columns_and_keep_exact_values():
    section = {
        "key": "material", "title": "Materials", "columns": MATERIAL_PURCHASE_COLUMNS,
        "rows": [{
            "item": "Mirror", "required_material_value": 3.460584, "required_material_unit": "m²",
            "required_material_line_id": "area-required", "purchase_quantity_line_id": "area-purchase",
            "purchase_kind": "area_direct", "purchase_unit": "m²", "purchase_quantity_value": 3.460584,
        }, {
            "item": "Profile", "required_material_value": 12.936, "required_material_unit": "m",
            "required_material_line_id": "length-required", "purchase_quantity_line_id": "bar-purchase",
            "purchase_kind": "linear_stock", "purchase_unit": "bar 2000 mm", "purchase_quantity_value": 7,
        }],
    }
    markup = _table_html(section)
    assert markup.count('data-original-value="3.460584">3.5<') == 2
    assert 'data-original-value="12.936">12.9<' in markup
    assert 'data-original-value="7">7<' in markup


def test_saved_led_label_uses_original_reference_price_metadata_without_changing_stored_plan():
    from types import SimpleNamespace

    price_id = "f59f2d3d-d1f1-4f45-a52f-df7d452dbb21"
    line = {"candidate_id": f"israel-reference:model:{price_id}:format:variant:4000K",
            "display_name": "LED strip standard output, 4000K, 6 W/m",
            "purchase_kind": "linear_stock", "purchasable_dimensions": {"length_mm": 5000}}
    calls = []

    class Query:
        def table(self, name):
            assert name == "market_material_model_prices"
            return self

        def select(self, columns):
            return self

        def in_(self, column, keys):
            calls.extend(keys)
            return self

        def execute(self):
            return SimpleNamespace(data=[{"model_price_id": price_id, "model_metadata": {"voltage_v": 24, "rated_w_per_m": 4.8}}])

    plan = {"lines": [line, {**line, "candidate_id": line["candidate_id"].replace("4000K", "3000K")}]}
    enriched = estimation._with_saved_led_catalog_specs(Query(), plan)
    assert calls == [price_id]
    assert "voltage_v" not in line["purchasable_dimensions"]
    actual = enriched["lines"][0]
    assert estimation._plan_material_display_label(actual, family="hardware_electrical_component",
                                                   name=actual["display_name"]) == "LED 4000 K 4.8 W/m 24 V"
