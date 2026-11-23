from copy import deepcopy

import pytest

from use_cases.estimation_cb_material_demand import build_cb_material_facts, calculate_cb_materials
from use_cases.estimation_front_panels import preserve_front_norms, validate_front_choices
from ui.object_detail_view import front_panels_html


def source():
    parts = [{"role": role, "owner_id": "B01", "block_id": "B01", "quantity": 1,
              "dimensions": {axis: {"mm": value, "basis": "source_dimension", "refs": ["dimension"]}
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


@pytest.mark.parametrize("basis", [None, "unknown", "construction_assumption", "israel_reference_default"])
def test_switch_does_not_promote_an_assumed_thickness_to_a_new_stock_requirement(basis):
    report, inputs, context = source()
    for part in report["objects"]["one"]["parts"]:
        part["dimensions"]["thickness"] = {"mm": 17, "basis": basis, "refs": []}
    original = deepcopy(report)
    base = build_cb_material_facts(parts_report=report, input_rows=inputs, catalog_context=context)["one"]
    group, = base["front_panel_groups"]
    result = build_cb_material_facts(parts_report=report, input_rows=inputs, catalog_context=context,
                                    front_panel_choices={"one": {group["id"]: "veneered_mdf"}})["one"]
    front = next(row for row in result["materials"] if row.get("material_class") == "front_panels")
    assert front["specification"] == {"board_type": "mdf", "surface": "veneer_two_sided"}
    assert not front.get("identity_hint")
    assert all(part["measurements"]["thickness"]["mm"] is None for part in front["part_sources"])
    body = next(row for row in result["materials"] if row["requirement_id"] == group["id"] + "-body")
    assert body["specification"]["thickness_mm"] == 17
    assert report == original


@pytest.mark.parametrize("spec,expected", [
    ({"board_type": "mdf", "surface": "raw"}, {"board_type": "mdf", "surface": "raw", "thickness": 17}),
    ({"board_type": "mdf", "surface": "raw", "thickness_mm": 20}, None),
    ({"board_type": "hdf", "surface": "raw"}, None),
])
def test_existing_catalog_default_fills_only_missing_matching_stock_facts(spec, expected):
    from use_cases.material_engine_adapter import _active_default_specifications

    default = {"board_type": "mdf", "surface": "raw", "thickness": 17}
    result, trace = _active_default_specifications(
        material_family="mdf_hdf", specifications=spec,
        material_default_variants=[{"family_id": "mdf", "reference_position_id": "raw-17",
                                    "default_specifications": default, "priority": 10}],
        reference_positions=[{"family_code": "mdf_hdf", "reference_position_id": "raw-17",
                              "specifications": default, "prices": [{"status": "active",
                                  "price_scope": "material_only", "price_typical": 100}]}],
        material_pricing_policies=[{"family_id": "mdf", "active": True,
                                   "pricing_key_attribute_codes": ["board_type", "surface", "thickness"]}],
        material_families=[{"family_id": "mdf", "family_code": "mdf_hdf", "active": True}],
    )
    assert result == (expected or spec)
    assert bool(trace) == bool(expected)



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
    assert all(label in rendered for label in ("LDSP", "MDF Veneered", "MDF Raw", "Plywood"))


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


def _stub_scoped_runtime(monkeypatch, snapshot):
    import pandas as pd
    from use_cases import estimation_front_panels as fronts, estimation_front_material_patch as patch
    from use_cases import estimation_material_context as context
    from db import repositories
    monkeypatch.setattr(fronts, "front_panel_controls", lambda *a: [{"id": "group", "choice": "source", "family": "mdf_hdf", "part_sources": [{}], "part_ids": []}])
    monkeypatch.setattr(context, "build_front_material_context", lambda *a, **k: {})
    monkeypatch.setattr(repositories, "fetch_rfq_estimate_lines_for_object", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(patch, "front_group_material", lambda *a, **k: ({"specification": {}}, []))
    monkeypatch.setattr(patch, "patch_front_material_plan", lambda *a, **k: (snapshot, {}, {("one", "front")}))


def test_automatic_preview_has_no_persistence_or_full_cycle_side_effects(monkeypatch):
    import pandas as pd
    from use_cases import estimation_runtime as runtime

    previous = {"front_panel_choices": {}}
    snapshot = {"lines": [], "object_material_costs": []}
    _stub_scoped_runtime(monkeypatch, snapshot)
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([{"plan_payload": previous}]))
    monkeypatch.setattr(runtime, "fetch_rfq_object_estimates", lambda *a: pd.DataFrame([{"object_id": "one", "quantity": 1}]))
    def forbidden(*a, **kw):
        raise AssertionError("Front preview attempted persistence or a full cycle")
    for name in ("_saved_material_inputs", "_calculate_material_plan", "build_estimation_material_context",
                 "upsert_rfq_estimate_material_plan", "upsert_rfq_estimate_material_norm_overrides",
                 "upsert_rfq_estimate_material_purchase_overrides", "update_rfq_object_estimate_quantity",
                 "update_rfq_detected_object", "_build_and_persist_material_plan"):
        monkeypatch.setattr(runtime, name, forbidden)
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


def test_front_save_preserves_unedited_objects_approvals(monkeypatch):
    import pandas as pd
    from use_cases import estimation_runtime as runtime, estimation

    snapshot = {"lines": [], "status": "planned", "object_material_costs": []}
    _stub_scoped_runtime(monkeypatch, snapshot)
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([{"plan_payload": {}}]))
    monkeypatch.setattr(runtime, "fetch_rfq_object_estimates", lambda *a: pd.DataFrame([
        {"object_id": "one", "quantity": 1}, {"object_id": "two", "quantity": 1},
    ]))
    published = []
    monkeypatch.setattr(estimation, "apply_material_plan_allocations", lambda *a, **kw: published.append(kw))
    monkeypatch.setattr(runtime, "upsert_rfq_estimate_material_plan", lambda *a, **kw: None)
    runtime._recalculate_front_panel_materials(
        None, estimate_id="estimate", run_id="run", company_id="company", choices={("one", "group"): "mdf"},
        quantity_edits={}, norm_edits={}, purchase_edits={},
    )
    assert published[0]["protected_approval_objects"] == {"two"}


def _patch_witness():
    report, inputs, context = source()
    for part in report['objects']['one']['parts']:
        part['dimensions']['thickness'] = {'mm': 17, 'basis': 'construction_assumption', 'refs': []}
    families, policies, defaults, positions = [], [], [], []
    for family in ['melamine_faced_particleboard', 'mdf_hdf', 'plywood']:
        families.append({'family_id': family, 'family_code': family, 'active': True})
        policies.append({'family_id': family, 'active': True, 'purchase_format_policy': 'standard_sheet_2400x1220',
                         'pricing_key_attribute_codes': ['board_type', 'surface', 'thickness'] if family == 'mdf_hdf' else ['thickness']})
        specs = [{'thickness': 17}]
        if family == 'mdf_hdf':
            specs = [{'board_type': 'mdf', 'surface': 'raw', 'thickness': 17},
                     {'board_type': 'mdf', 'surface': 'veneer_two_sided', 'thickness': 18}]
        for index, spec in enumerate(specs):
            identity = family + str(index)
            positions.append({'reference_position_id': identity, 'family_code': family, 'specifications': spec,
                'canonical_name': family + str(spec), 'prices': [{'model_price_id': identity, 'status': 'active',
                    'currency': 'ILS', 'price_scope': 'material_only', 'unit': 'sqm', 'price_typical': 50 + index * 10}],
                'supply_formats': [{'supply_format_id': identity, 'active': True,
                                    'purchasable_dimensions': {'length_mm': 2440, 'width_mm': 1220}}]})
            defaults.append({'default_variant_id': identity, 'family_id': family, 'reference_position_id': identity,
                             'default_specifications': spec, 'applicability_specifications': (
                                 {k: v for k, v in spec.items() if k != 'thickness'} if index else {}),
                             'priority': index, 'active': True})
    context['families'] = {'melamine_faced_particleboard', 'mdf_hdf', 'plywood'}
    context['catalogs'] = {'material_families': families, 'material_pricing_policies': policies,
                           'material_default_variants': defaults, 'reference_positions': positions}
    result = calculate_cb_materials(parts_report=report, input_rows=inputs, catalog_context=context)
    facts = result['facts_by_object']['one']
    lines = [{'section': 'material', 'raw_agent_json': {'facts': material}} for material in facts['materials']]
    return result['material_plan'], lines, context


@pytest.mark.parametrize('choice,family', [('mdf', 'mdf_hdf'), ('veneered_mdf', 'mdf_hdf'), ('plywood', 'plywood')])
def test_scoped_replacement_preserves_unrelated_baskets_parts_and_restores_original(choice, family):
    from use_cases.estimation_front_material_patch import patch_front_material_plan

    previous, lines, context = _patch_witness()
    original = deepcopy(previous)
    group = previous['front_panel_groups']['one'][0]
    selected, materials, owners = patch_front_material_plan(previous, object_id='one', source_lines=lines,
        choices={group['id']: choice}, contexts={family: context})
    changed_keys = set(selected['front_material_patch']['affected_stock_keys'])
    assert len(changed_keys) == 2
    assert len(materials) == 1  # the existing V3.3 body requirement is already separate
    assert selected['parts_check']['one']['parts'] == previous['parts_check']['one']['parts']
    assert previous == original
    assert all(next((r for r in selected['lines'] if r['selection_key'] == old['selection_key']), None) == old
               for old in previous['lines'] if old['selection_key'] not in changed_keys)
    updated_lines = [r for r in lines if r['raw_agent_json']['facts']['requirement_id'] not in materials]
    updated_lines.extend({'section': 'material', 'raw_agent_json': {'facts': m}} for m in materials.values())
    restored, _, _ = patch_front_material_plan(selected, object_id='one', source_lines=updated_lines,
        choices={group['id']: 'ldsp'}, contexts={'melamine_faced_particleboard': context})
    signature = lambda p: sorted((r['selection_key'], r['purchase_quantity'], r['price_per_purchase_unit'], r['total_cost']) for r in p['lines'])
    assert signature(restored) == signature(previous)


def test_front_receipt_reuses_saved_labor_without_running_its_calculation(monkeypatch):
    import pandas as pd
    from use_cases import estimation

    saved = {'labor_basis_sha256': 'saved', 'basis_sha256': 'old', 'labor': {'hours': 2, 'total': 100, 'partial': False},
             'labor_blocks': {'sheet_processing': {'hours': 1}, 'assembly': {'hours': 1}}, 'previous_totals': {}}
    lines = pd.DataFrame([{'source': estimation._FULL_COST_SOURCE, 'raw_agent_json': saved}])
    monkeypatch.setattr(estimation, '_object_detail_material_rows', lambda *a: [{'total': 200}])
    monkeypatch.setattr(estimation, '_material_rows_from_plan', lambda *a, **kw: [{'total': 200}])
    def forbidden(*a, **kw):
        raise AssertionError('Front material selection reran Labor')
    monkeypatch.setattr(estimation, 'load_object_labor', forbidden)
    monkeypatch.setattr(estimation, 'estimate_object_overhead', lambda **kw: {'cost': 20, 'status': 'ready'})
    context = {'plan': {}, 'machinery': {}, 'parts': {}, 'settings': {'vat_percent': 18}, 'monthly': {}, 'preserve_labor': True}
    summary, _ = estimation._full_cost_summary(None, estimate_id='estimate',
        obj={'object_id': 'one', 'company_id': 'company', 'quantity': 1}, lines=lines,
        material_batch=200, context=context, persist=False)
    assert summary['labor'] == saved['labor']
    assert summary['labor_blocks'] == saved['labor_blocks']
    assert summary['self_cost_ex_vat'] == 320


def test_scoped_switch_retains_a_previously_edited_front_norm():
    from use_cases.estimation_front_material_patch import patch_front_material_plan
    from use_cases.material_engine_adapter import replan_material_norm_snapshot, material_review_purchases

    previous, lines, context = _patch_witness()
    group = previous['front_panel_groups']['one'][0]
    requirement = group['requirement_ids'][0]
    norm = {('one', requirement): {'quantity_per_item': 2, 'unit': 'm2'}}
    keys = {line['selection_key'] for line in previous['lines'] if any(
        a['material_requirement_id'] == requirement for a in line['allocations'])}
    edited, _ = replan_material_norm_snapshot(previous, norm, {'one': 1}, {}, changed_keys=keys)
    edited = material_review_purchases(edited, changed_keys=keys)
    selected, _, _ = patch_front_material_plan(edited, object_id='one', source_lines=lines,
        choices={group['id']: 'mdf'}, contexts={'mdf_hdf': context})
    front_area = sum(a['area_mm2'] for line in selected['lines'] for a in line['allocations']
                     if a['material_requirement_id'] == requirement)
    assert front_area == 2_000_000
    assert selected['parts_check']['one']['parts'] == previous['parts_check']['one']['parts']


@pytest.mark.parametrize('fresh', [True, False])
def test_reusing_a_trusted_preview_skips_catalog_and_rejects_stale_base(monkeypatch, fresh):
    import pandas as pd
    from db import repositories
    from use_cases import estimation_runtime as runtime, estimation_material_context as context
    from use_cases.estimation_front_material_patch import patch_front_material_plan
    from use_cases.estimation_front_panels import front_plan_revision

    previous, lines, catalog = _patch_witness()
    group = previous['front_panel_groups']['one'][0]
    cached, _, owners = patch_front_material_plan(previous, object_id='one', source_lines=lines,
        choices={group['id']: 'mdf'}, contexts={'mdf_hdf': catalog})
    cached['_front_preview_base'] = front_plan_revision(previous) if fresh else 'stale'
    cached['_front_preview_publications'] = []
    cached['_front_preview_owners'] = [list(owner) for owner in owners]
    reads = []
    monkeypatch.setattr(runtime, 'fetch_rfq_estimate_material_plan', lambda *a: pd.DataFrame([{'plan_payload': previous}]))
    monkeypatch.setattr(runtime, 'fetch_rfq_object_estimates', lambda *a: pd.DataFrame([{'object_id': 'one', 'quantity': 1}]))
    monkeypatch.setattr(repositories, 'fetch_rfq_estimate_lines_for_object', lambda *a, **kw: pd.DataFrame(lines))
    monkeypatch.setattr(context, 'build_front_material_context', lambda *a, **kw: reads.append(a[-1]) or catalog)
    result = runtime._recalculate_front_panel_materials(None, estimate_id='estimate', run_id='run', company_id='company',
        choices={('one', group['id']): 'mdf'}, quantity_edits={}, norm_edits={}, purchase_edits={},
        preview=True, front_preview=cached)
    assert len(reads) == (0 if fresh else 1)
    assert result['front_panel_choices']['one'][group['id']] == 'mdf'
    assert result['_front_preview_base'] == front_plan_revision(previous)
    assert not previous.get('front_panel_choices')


def test_new_purchase_row_can_be_edited_before_the_front_choice_is_saved(monkeypatch):
    import pandas as pd
    from concurrent.futures import Future
    from use_cases import estimation, estimation_runtime as runtime
    from use_cases.estimation_front_material_patch import patch_front_material_plan
    from use_cases.estimation_front_panels import front_plan_revision

    previous, lines, catalog = _patch_witness()
    group = previous['front_panel_groups']['one'][0]
    cached, _, owners = patch_front_material_plan(previous, object_id='one', source_lines=lines,
        choices={group['id']: 'mdf'}, contexts={'mdf_hdf': catalog})
    cached['_front_preview_base'] = front_plan_revision(previous)
    key = next(line['selection_key'] for line in cached['lines'] if line['selection_key'].startswith('mdf_hdf|'))
    monkeypatch.setattr(estimation, 'get_supabase_client', lambda: None)
    monkeypatch.setattr(estimation, '_assert_screen_estimate_access', lambda *a: None)
    monkeypatch.setattr(estimation, 'fetch_rfq_object_estimates', lambda *a: pd.DataFrame([
        {'object_id': 'one', 'company_id': 'company', 'run_id': 'run', 'quantity': 1}]))
    monkeypatch.setattr(estimation, 'fetch_rfq_estimate_material_plan', lambda *a: pd.DataFrame([{'plan_payload': previous}]))
    monkeypatch.setattr(estimation, 'fetch_rfq_estimate_lines_for_object', lambda *a, **kw: pd.DataFrame(lines))
    monkeypatch.setattr(estimation, 'upsert_rfq_estimate_lines', lambda *a, **kw: None)
    submitted = []
    def queue(**kwargs):
        submitted.append(kwargs)
        result = Future(); result.set_result(cached); return result
    monkeypatch.setattr(runtime, 'queue_material_plan_recalculation', queue)
    estimation.save_object_detail_material_edits(estimate_id='estimate', object_id='one', front_preview=cached,
        edits=[{'field': 'front_material', 'lineId': '__front_panels__:' + group['id'], 'value': 'mdf'},
               {'field': 'purchase_quantity', 'lineId': '__material_purchase__:' + key, 'value': '4'}])
    assert submitted[0]['front_preview'] is cached
    assert list(submitted[0]['purchase_edits'].values()) == [4]
