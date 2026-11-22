from copy import deepcopy

import pytest

from use_cases.estimation_cb_material_demand import build_cb_material_facts, calculate_cb_materials
from use_cases.estimation_front_panels import preserve_front_norms, validate_front_choices
from ui.object_detail_view import front_panels_html


def source():
    parts = [{"role": role, "owner_id": "B01", "block_id": "B01", "quantity": 1,
              "dimensions": {axis: {"mm": value, "refs": []}
                             for axis, value in (("length", 700), ("width", 400), ("thickness", 17))}}
             for role in ("door_front", "drawer_front", "lift_up_front", "fixed_panel", "carcass_side")]
    report = {"stage": "Parts Check", "run_id": "run", "objects": {"one": {"parts": parts}}}
    inputs = [{"input_id": "input", "input_payload": {"run_id": "run", "company_id": "company",
               "object": {"object_id": "one", "object_name": "Kitchen", "quantity": 1}}}]
    context = {"company_id": "company", "families": {"melamine_faced_particleboard", "mdf_hdf", "plywood", "edge_banding"}, "catalogs": {}}
    return report, inputs, context


def facts(choices=None):
    report, inputs, context = source()
    return build_cb_material_facts(parts_report=report, input_rows=inputs, catalog_context=context,
                                   front_panel_choices=choices)["one"]


def test_front_class_separates_only_operating_fronts_and_keeps_body_ids():
    item = facts()
    group, = item["front_panel_groups"]
    assert group["mixed"]
    assert len(group["part_ids"]) == 3
    fronts = next(row for row in item["materials"] if row.get("material_class") == "front_panels")
    assert {row["role"] for row in fronts["part_sources"]} == {"door_front", "drawer_front", "lift_up_front"}
    assert len({row["requirement_id"] for row in item["materials"]}) == len(item["materials"])
    assert len(item["parts"]) == 5


@pytest.mark.parametrize("choice,surface", [("mdf", "raw"), ("veneered_mdf", "veneer_two_sided")])
def test_switch_updates_only_front_stock_and_its_edge_tape(choice, surface):
    baseline = facts()
    group = baseline["front_panel_groups"][0]
    selected = facts({"one": {group["id"]: choice}})
    assert len({row["requirement_id"] for row in selected["materials"]}) == len(selected["materials"])
    front = next(row for row in selected["materials"] if row.get("material_class") == "front_panels")
    assert front["family"] == "mdf_hdf"
    assert front["specification"] == {"board_type": "mdf", "surface": surface, "thickness_mm": 17}
    before_body = {row["requirement_id"]: row for row in baseline["materials"]
                   if row.get("material_role") in {"visible_sheet", "carcass_sheet"}
                   and row.get("material_class") != "front_panels"}
    after_body = {row["requirement_id"]: row for row in selected["materials"] if row["requirement_id"] in before_body}
    assert before_body == after_body
    assert [(p["part_id"], p["quantity"], p["length_mm"], p["width_mm"]) for p in selected["parts"]] == [
        (p["part_id"], p["quantity"], p["length_mm"], p["width_mm"]) for p in baseline["parts"]]
    assert sum(run["metres"] for run in selected["edge_runs"] if run["tape_kind"] == "melamine") < sum(
        run["metres"] for run in baseline["edge_runs"] if run["tape_kind"] == "melamine")
    assert bool([run for run in selected["edge_runs"] if run["tape_kind"] == "veneer"]) == (choice == "veneered_mdf")


def test_restore_source_keeps_source_report_and_exact_materials():
    report, inputs, context = source()
    frozen = deepcopy(report)
    initial = calculate_cb_materials(parts_report=report, input_rows=inputs, catalog_context=context)
    group = initial["facts_by_object"]["one"]["front_panel_groups"][0]
    restored = calculate_cb_materials(parts_report=report, input_rows=inputs, catalog_context=context,
                                       front_panel_choices={"one": {group["id"]: "ldsp"}})
    assert initial["facts_by_object"]["one"]["materials"] == restored["facts_by_object"]["one"]["materials"]
    assert report == frozen
    assert initial["material_plan"]["input_fingerprint"] != restored["material_plan"]["input_fingerprint"]


def test_legacy_joint_norm_is_divided_between_fronts_and_fixed_panel():
    item = facts()
    group = item["front_panel_groups"][0]
    legacy = {("one", group["id"]): {"quantity_per_item": 4, "unit": "m²"}}
    migrated = preserve_front_norms({"one": item}, legacy)
    assert migrated[("one", group["id"] + "-front")]["quantity_per_item"] == 3
    assert migrated[("one", group["id"] + "-body")]["quantity_per_item"] == 1
    assert legacy == {("one", group["id"]): {"quantity_per_item": 4, "unit": "m²"}}


def test_catalog_type_selector_rejects_other_groups_and_materials():
    group = facts()["front_panel_groups"][0]
    for selection in ({"other": "mdf"}, {group["id"]: "stone"}):
        with pytest.raises(ValueError):
            validate_front_choices([group], selection)
    assert front_panels_html([]) == ""


def test_selector_has_four_mvp_material_types_for_an_existing_ldsp_group():
    from use_cases.estimation_front_panels import front_panel_controls

    group = facts()["front_panel_groups"][0]
    controls = front_panel_controls({"front_panel_groups": {"one": [group]}}, [], "one")
    rendered = front_panels_html(controls)
    assert rendered.count('<option ') == 4
    assert 'aria-label="Front panels"' in rendered
    assert all(label in rendered for label in ("LDSP", "Veneered MDF", "MDF", "Plywood"))


def test_explicit_metal_keeps_original_and_all_four_replacement_options():
    from use_cases.estimation_front_panels import front_panel_controls

    group = {**facts()["front_panel_groups"][0], "source_name": "Steel sheet 2 mm",
             "source_choice": None, "family": "sheet_steel", "thickness_mm": 2}
    controls = front_panel_controls({"front_panel_groups": {"one": [group]}}, [], "one")
    rendered = front_panels_html(controls)
    assert rendered.count('<option ') == 5
    assert '<option value="source" selected>Steel sheet 2 mm</option>' in rendered


def test_plywood_is_selected_for_existing_special_plywood_without_replacing_its_spec():
    from use_cases.estimation_front_panels import front_material_groups, front_panel_controls

    material = next(row for row in facts()["materials"] if row.get("material_class") == "front_panels")
    material = {**material, "family": "plywood_special", "source_name": "Birch plywood 18 mm"}
    group, = front_material_groups([material])
    assert validate_front_choices([group], {group["id"]: "plywood"}) == {}
    controls = front_panel_controls({"front_panel_groups": {"one": [group]}}, [], "one")
    assert '<option value="plywood" selected>Plywood</option>' in front_panels_html(controls)


def test_automatic_preview_has_no_persistence_side_effects(monkeypatch):
    import pandas as pd
    from use_cases import estimation_runtime as runtime

    previous = {"front_panel_choices": {}}
    snapshot = {"front_panel_groups": {"one": [{"id": "group", "requirement_ids": ["front"]}]},
                "object_material_costs": [{"object_id": "one", "material_requirement_id": "front"}]}
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([{"plan_payload": previous}]))
    monkeypatch.setattr(runtime, "fetch_rfq_object_estimates", lambda *a: pd.DataFrame([{"object_id": "one", "quantity": 1}]))
    monkeypatch.setattr(runtime, "_saved_material_inputs", lambda *a: ({}, []))
    monkeypatch.setattr(runtime, "_calculate_material_plan", lambda **kw: {"material_plan": snapshot})
    def no_write(*a, **kw):
        raise AssertionError("Preview attempted a persistence write")
    for name in ("upsert_rfq_estimate_material_plan", "upsert_rfq_estimate_material_norm_overrides",
                 "upsert_rfq_estimate_material_purchase_overrides", "update_rfq_object_estimate_quantity",
                 "update_rfq_detected_object", "_build_and_persist_material_plan"):
        monkeypatch.setattr(runtime, name, no_write)
    result = runtime._recalculate_front_panel_materials(
        None, estimate_id="estimate", run_id="run", company_id="company", choices={("one", "group"): "mdf"},
        quantity_edits={}, norm_edits={}, purchase_edits={}, preview=True,
    )
    assert result is snapshot and previous == {"front_panel_choices": {}}


def test_multiple_edge_tape_requirements_keep_their_own_ids():
    from use_cases.estimation_front_panels import classify_front_materials

    materials = [
        {"requirement_id": "edge-melamine-24", "material_role": "edge_banding", "unit": "m", "part_sources": []},
        {"requirement_id": "edge-melamine-45", "material_role": "edge_banding", "unit": "m", "part_sources": []},
        {"requirement_id": "edge-veneer-24", "material_role": "edge_banding", "unit": "m", "part_sources": []},
    ]
    base = {"materials": materials, "parts": []}
    result = classify_front_materials(base, deepcopy(base), [], {})
    assert [row["requirement_id"] for row in result["materials"]] == [
        "edge-melamine-24", "edge-melamine-45", "edge-veneer-24",
    ]


def test_several_surfaces_of_one_part_retain_separate_material_identities():
    from use_cases.estimation_front_panels import classify_front_materials

    materials = [{"requirement_id": surface, "material_role": "worktop_sheet", "unit": "m2",
                  "part_sources": [{"part_id": "top", "surface": {"id": surface}}]}
                 for surface in ("main", "contrast")]
    base = {"materials": materials, "parts": []}
    result = classify_front_materials(base, deepcopy(base), [], {})
    assert [row["requirement_id"] for row in result["materials"]] == ["main", "contrast"]
