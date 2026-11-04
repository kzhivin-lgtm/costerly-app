from copy import deepcopy
import json

import pytest

from agents.estimation_composition_analyze_agent import _content, _page_manifest
from use_cases.estimation_construction_plan import normalize_palette, normalize_construction_scope, with_shared_document_context, validate_thickness_witnesses
from use_cases.estimation_composition_scope import validate_composition_scope, apply_composition_scope, geometry_scope
from use_cases.estimation_structural_bom import build_structural_assembly_bom
from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_2vn_resolver import resolve_2vn_geometry

REF = "storage://rfq-estimation-evidence/c/r/o/page.webp"
LEGEND = "ocr:event:p2:b0001"
FAMILIES = ["mdf_hdf", "melamine_faced_particleboard", "edge_banding", "hardware_drawer_slide", "purchased_fabricated_component", "paint_lacquer_stain"]


def input_row():
    return {"input_id": "i1", "object_input_revision": 1, "input_payload": {
        "contract_version": "estimation_input_v4", "run_id": "r", "company_id": "c", "object": {"object_id": "o", "object_name": "Entrance unit", "quantity": 1},
        "evidence": {"artifacts": [{"artifact_kind": "page", "page_number": 1, "storage_ref": REF}], "ocr_blocks": []},
        "document_context": {"ocr_blocks": [{"block_ref": LEGEND, "page_number": 2, "text": "VN11 oak veneer"}]},
    }}


def palette():
    return normalize_palette([
        {"material_id": "V", "source_name": "Veneered MDF", "family": "mdf_hdf", "specification": {"thickness_mm": 20, "surface": "veneer_two_sided"}, "basis": "visual_assumption", "evidence_chain": [{"ref": REF, "observation": "wood grain"}]},
        {"material_id": "L", "source_name": "LDSP", "family": "melamine_faced_particleboard", "specification": {"thickness_mm": 20}, "basis": "construction_default"},
        {"material_id": "E", "source_name": "Veneer edge band", "family": "edge_banding", "specification": {"width_mm": 40}},
        {"material_id": "P", "source_name": "Furniture leg", "family": "purchased_fabricated_component", "specification": {"diameter_mm": 40}},
        {"material_id": "F", "source_name": "Paint", "family": "paint_lacquer_stain", "specification": {}},
    ], allowed_refs={REF, LEGEND}, families=FAMILIES)


def scope(zones):
    raw = {"contract_version": "estimation_composition_scope_v1", "input_id": "i1", "object_id": "o", "zones": zones}
    return validate_composition_scope(scope=normalize_construction_scope(raw, palette=palette(), allowed_refs={REF, LEGEND}), input_id="i1")


def zone(role="drawer_bank", **overrides):
    return {"scope_id": "z", "assembly_role": role, "operability": "drawer" if role == "drawer_bank" else "fixed",
            "counts": {"drawers": 3} if role == "drawer_bank" else {}, "evidence_refs": [REF],
            "front_groups": [{"front_kind": "drawer_front", "quantity": 3, "arrangement": "side_by_side"}] if role == "drawer_bank" else [],
            "material_assignments": [{"role": "visible_sheet", "material_id": "V", "layer_count": 2, "finished_thickness_mm": 40, "edge_material_id": "E"},
                                     {"role": "carcass_sheet", "material_id": "V", "layer_count": 2, "finished_thickness_mm": 40},
                                     {"role": "internal_sheet", "material_id": "V", "alternative_material_ids": ["L"]},
                                     {"role": "backing_sheet", "material_id": "V"}], **overrides}


def compose(locked, assemblies):
    extraction = apply_composition_scope(extraction={"assemblies": assemblies, "document_unit": {
        "unit": "mm", "basis": "document_convention_assumption", "assumption_reason": "Test scale", "evidence_refs": []}}, scope=locked)
    return build_structural_assembly_bom(input_row=input_row(), dimension_graph=build_dimension_graph(input_row=input_row()),
                                        extraction=extraction, allowed_material_families=FAMILIES)


def dims(**values):
    return {k: {"value": v, "basis": "assumption", "evidence_refs": [], "assumption_reason": "Visual estimate"} for k, v in values.items()}


def test_first_pass_preserves_text_context_and_deduplicates_page_aliases():
    a = input_row()
    b = deepcopy(a)
    b["input_id"] = "i2"
    b["input_payload"]["evidence"]["artifacts"][0]["storage_ref"] = "storage://alias"
    pages, objects = _page_manifest([a, b], {REF: b"same", "storage://alias": b"same"})
    assert len(pages) == 1 and len(objects) == 2
    assert pages[0]["source_aliases"] == [REF, "storage://alias"]
    content = _content(inputs=[a, b], page_bytes_by_ref={REF: b"same", "storage://alias": b"same"}, allowed_material_families=FAMILIES)
    assert len(json.loads(content[-1]["text"])["source_text"]) == 1


def test_shared_legacy_context_preserves_cross_object_legend_without_expanding_geometry():
    a, b = input_row(), input_row()
    a["input_payload"].pop("document_context")
    b["input_id"] = "i2"
    b["input_payload"]["object"]["object_id"] = "other"
    original = deepcopy(a)
    hydrated = with_shared_document_context([a, b])
    assert hydrated[0]["input_payload"]["document_context"]["ocr_blocks"][0]["block_ref"] == LEGEND
    assert hydrated[0]["input_payload"]["object"] == a["input_payload"]["object"]
    assert hydrated[0]["input_payload"]["evidence"] == a["input_payload"]["evidence"]
    assert a == original
    b["input_payload"]["run_id"] = "different-file-run"
    with pytest.raises(ValueError, match="one company/file run"):
        with_shared_document_context([a, b])


def test_linked_material_requires_both_callout_and_definition():
    raw = {"material_id": "V", "family": "mdf_hdf", "basis": "linked_source", "evidence_chain": [
        {"ref": REF, "kind": "callout", "observation": "VN11"}, {"ref": LEGEND, "kind": "definition", "observation": "oak veneer"}]}
    result = normalize_palette([raw], allowed_refs={REF, LEGEND}, families=FAMILIES)["V"]
    assert result["basis"] == "source_evidence" and result["evidence_refs"] == [REF, LEGEND]
    result = normalize_palette([raw], allowed_refs={REF}, families=FAMILIES)["V"]
    assert result["basis"] == "construction_assumption" and result["evidence_refs"] == []


@pytest.mark.parametrize("number,printed_unit,expected", [(4, None, "source"), (19, None, "assumption"), (40, "mm", "source")])
def test_thickness_source_respects_numeric_units_without_changing_selected_stock(number, printed_unit, expected):
    locked = scope([zone()])
    role = locked["zones"][0]["material_roles"][0]
    role.update(thickness_basis="source", thickness_evidence_refs=[REF])
    result = validate_thickness_witnesses(locked, dimension_graph={"dimension_numbers": [
        {"numeric_value": number, "printed_unit": printed_unit, "evidence_refs": [REF]}]},
        dimension_scale_gate={"decision": {"required_unit": "cm"}})
    checked = result["zones"][0]["material_roles"][0]
    assert checked["thickness_basis"] == expected
    assert checked["finished_thickness_mm"] == 40 and checked["layer_count"] == 2
    assert role["thickness_basis"] == "source"  # The input contract is not mutated.
    if expected == "assumption":
        assert checked["thickness_evidence_refs"] == []
        assert "contradicted_thickness_source_downgraded" in checked["normalizations"]


def test_drawers_lock_materials_arrangement_layers_and_hardware():
    locked = scope([zone()])
    result = compose(locked, [{"assembly_id": "z", "assembly_role": "facade_set", "dimensions": dims(width=1580, height=430, depth=720),
                              "material_roles": [{"role": "visible_sheet", "family": "fibreboard_hardboard"}]}])
    assert result["composition_version"] == "structural_bom_v6_1"
    front = next(p for p in result["parts"] if p["component_role"] == "drawer_front")
    assert front["quantity"] == 6 and front["layer_count"] == 2
    assert front["finished_thickness_mm"] == 40
    assert front["length_mm"] == pytest.approx(1580 / 3, abs=.001) and front["width_mm"] == 430
    assert front["basis"] == "assumption"
    internal = next(p for p in result["parts"] if p["component_role"] == "drawer_bottom")
    assert internal["quantity"] == 3 and internal["layer_count"] == 1
    side = next(p for p in result["parts"] if p["component_role"] == "carcass_side")
    assert side["quantity"] == 2 and side["layer_count"] == 2
    materials = result["materials"]
    assert not any(m["family"] == "fibreboard_hardboard" for m in materials)
    slide = next(m for m in materials if m["family"] == "hardware_drawer_slide")
    assert slide["quantity"] == 3 and slide["specification"]["depth_mm"] == 600
    edge = next(m for m in materials if m["family"] == "edge_banding")
    assert edge["quantity"] == pytest.approx(2 * (1580 / 3 + 430) * 3 / 1000)
    assert result["primary_preview_ref"] == REF


def test_missing_hidden_roles_reuse_stock_not_new_hardboard_family():
    z = zone(material_assignments=[{"role": "visible_sheet", "material_id": "V", "layer_count": 2}])
    assignments = scope([z])["zones"][0]["material_roles"]
    assert {m["family"] for m in assignments} == {"mdf_hdf"}
    assert next(m for m in assignments if m["role"] == "internal_sheet")["layer_count"] == 1


def test_assumed_edge_width_covers_both_layers_but_source_edge_conflict_fails():
    p = palette()
    p["E"]["specification"]["width_mm"] = 22
    raw = {"zones": [zone()]}
    result = normalize_construction_scope(raw, palette=p, allowed_refs={REF, LEGEND})
    edge = result["zones"][0]["material_roles"][0]["edge_material"]
    assert edge["specification"]["width_mm"] == 40
    assert "assumed_edge_width_covers_finished_panel" in edge["normalizations"]
    assert p["E"]["specification"]["width_mm"] == 22
    p["E"]["basis"] = "source_evidence"
    with pytest.raises(ValueError, match="specified edge width"):
        normalize_construction_scope(raw, palette=p, allowed_refs={REF, LEGEND})


def test_geometry_handoff_shares_material_descriptions_without_mutating_locked_scope():
    locked = scope([zone()])
    original = deepcopy(locked)
    compact = geometry_scope(locked)
    assert locked == original
    assert len(json.dumps(compact)) < len(json.dumps(locked)) * .7
    roles = compact["zones"][0]["material_roles"]
    assert next(r for r in roles if r["role"] == "visible_sheet")["finished_thickness_mm"] == 40
    assert all("specification" not in r and "alternatives" not in r for r in roles)
    assert compact["material_palette"]["V"]["specification"]["thickness_mm"] == 20
    assert compact["zones"][0]["front_groups"] == locked["zones"][0]["front_groups"]


def test_assumed_finished_thickness_follows_stock_but_source_conflict_is_not_silently_rewritten():
    z = zone(material_assignments=[{"role": "visible_sheet", "material_id": "V", "finished_thickness_mm": 16}])
    material = scope([z])["zones"][0]["material_roles"][0]
    assert material["finished_thickness_mm"] == 20
    assert "assumed_finished_thickness_aligned_to_selected_stock_layers" in material["normalizations"]
    z["material_assignments"][0].update(thickness_basis="source", thickness_evidence_refs=[REF])
    with pytest.raises(ValueError, match="contradicts purchased stock"):
        scope([z])


@pytest.mark.parametrize("group", [
    {"type": "drawer_front", "quantity": 3, "arrangement": "side_by_side"},
    {"front_kind": "drawer_front", "quantity": 3},
])
def test_v6_invalid_front_schema_cannot_silently_turn_horizontal_drawers_into_stacked(group):
    with pytest.raises(ValueError, match="construction front group"):
        scope([zone(front_groups=[group])])


def test_top_layers_are_not_doubled_twice_and_finish_excludes_buried_faces():
    z = zone("countertop", counts={"top_layers": 2}, material_assignments=[
        {"role": "worktop_sheet", "material_id": "V", "layer_count": 2, "finished_thickness_mm": 40},
        {"role": "finish", "material_id": "F", "applies_to_roles": ["worktop_sheet"]}])
    result = compose(scope([z]), [{"assembly_id": "z", "dimensions": dims(width=1000, depth=1000)}])
    assert result["parts"][0]["quantity"] == 2
    paint = next(m for m in result["materials"] if m["family"] == "paint_lacquer_stain")
    assert paint["quantity"] == 2 and paint["unit"] == "m2"


def test_repeated_fixed_panel_groups_and_supports_are_counted_once():
    z = zone("vertical_panel", panel_groups=[{"group_id": "r", "component_role": "rib", "quantity": 7, "material_role": "visible_sheet"}])
    leg = zone("support", scope_id="legs", quantity=2, construction="purchased", material_assignments=[{"role": "leg", "material_id": "P"}])
    result = compose(scope([z, leg]), [{"assembly_id": "z", "dimensions": dims(width=1600, height=2600),
        "panel_groups": [{"group_id": "r", "quantity": 999, "dimensions": dims(width=60, height=2600)}]}, {"assembly_id": "legs", "dimensions": {}}])
    assert len(result["parts"]) == 1 and result["parts"][0]["quantity"] == 14
    assert result["parts"][0]["width_mm"] == 60
    assert next(m for m in result["materials"] if m["family"] == "purchased_fabricated_component")["quantity"] == 2
    assert not any(m["family"].startswith("hardware_") for m in result["materials"])


def test_only_explicitly_fixed_decorative_facade_groups_can_use_panel_composer():
    z = zone("facade_set", counts={}, front_groups=[], panel_groups=[
        {"group_id": "r", "component_role": "rib", "quantity": 7, "material_role": "visible_sheet"}])
    assert scope([z])["zones"][0]["assembly_role"] == "vertical_panel"
    z["operability"] = "hinged"
    with pytest.raises(ValueError, match="fixed panel assembly"):
        scope([z])


def test_v6_2vn_downgrades_unbound_source_without_losing_estimate():
    extraction = {"composition_scope": {"construction_version": "estimation_construction_v6_1"},
                  "assemblies": [{"assembly_id": "z", "dimensions": {"width": {"value": 1580, "basis": "source", "evidence_refs": [REF]}}}]}
    resolved, audit = resolve_2vn_geometry(dimension_graph=build_dimension_graph(input_row=input_row()), extraction=extraction)
    assert resolved["assemblies"][0]["dimensions"]["width"]["basis"] == "assumption"
    assert audit["scope_policy"] == "explicit_zone_links_only"


@pytest.mark.parametrize("resolution", ["direct", "cross_view", "linked_zone"])
def test_v6_2vn_rejects_numeric_mismatch_for_all_binding_modes(resolution):
    graph = {"contract_version": "estimation_dimension_graph_v1", "views": [{"view_id": "v"}],
             "dimension_numbers": [{"dimension_id": "d", "numeric_value": 72, "printed_unit": "cm", "evidence_refs": [REF]}],
             "relations": [{"from_dimension_id": "d", "relation": "nearest_view_candidate", "to_view_id": "v"}]}
    extraction = {"composition_scope": {"construction_version": "estimation_construction_v6_1"},
                  "view_interpretations": [{"view_id": "v", "projection": "side_elevation"}],
                  "dimension_bindings": [{"assembly_id": "z", "axis": "depth", "view_id": "v", "local_orientation": "horizontal", "dimension_id": "d", "resolution": resolution}],
                  "assemblies": [{"assembly_id": "z", "dimensions": {"depth": {"value": 43, "unit": "cm", "basis": "source"}}}]}
    resolved, audit = resolve_2vn_geometry(dimension_graph=graph, extraction=extraction)
    assert "depth" not in resolved["assemblies"][0]["dimensions"]
    assert audit["binding_outcomes"]["rejected_numeric_mismatch"] == 1


@pytest.mark.parametrize("reuse_second", [False, True])
def test_runtime_one_analyze_then_one_calculation_per_uncached_object(monkeypatch, reuse_second):
    from use_cases import estimation_object_to_estimate_runtime as runtime
    first, second = input_row(), input_row()
    second["input_id"] = "i2"
    second["input_payload"]["object"]["object_id"] = "o2"
    calls, downloads, persisted = [], [], []
    monkeypatch.setattr(runtime, "fetch_estimation_fact_result", lambda _client, input_id, agent_version:
        {"facts_payload": {"composition_scope": scope([zone()])}} if reuse_second and input_id == "i2" and agent_version == runtime.ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION else None)
    monkeypatch.setattr(runtime, "insert_agent_usage_event_returning_id", lambda *_args, **_kwargs: "usage")
    monkeypatch.setattr(runtime, "insert_estimation_fact_result", lambda _client, **kwargs: persisted.append(kwargs) or "fact")
    monkeypatch.setattr(runtime, "_record_stage_event", lambda **_kwargs: None)
    monkeypatch.setattr(runtime, "download_evidence_artifact", lambda **kw: downloads.append(kw["storage_ref"]) or b"page")
    def analyze(**kwargs):
        calls.append("analyze")
        assert len(kwargs["context_inputs"]) == int(reuse_second)
        return {"usage_event": {}, "scopes_by_input": {row["input_id"]: {**scope([zone()]), "input_id": row["input_id"], "object_id": row["input_payload"]["object"]["object_id"]} for row in kwargs["inputs"]}}
    def calculate(**kwargs):
        calls.append("calculation")
        return {"usage_event": {}, "extraction": {"document_unit": {"unit": "mm", "basis": "document_convention_assumption", "evidence_refs": [], "assumption_reason": "Fixture"},
            "assemblies": [{"assembly_id": "z", "dimensions": dims(width=1580, height=430, depth=720)}]}}
    monkeypatch.setattr(runtime, "run_estimation_composition_analyze_agent", analyze)
    monkeypatch.setattr(runtime, "run_estimation_assembly_bom_agent", calculate)
    result = runtime.run_assembly_first_bom_batch(client=object(), inputs=[first, second], allowed_material_families=FAMILIES)
    assert result["failed"] == {}
    assert calls == ["analyze"] + ["calculation"] * (1 if reuse_second else 2)
    assert downloads == [REF]
    boms = [row["facts_payload"] for row in persisted if row["agent_version"] == runtime.ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION]
    assert all(bom["composition_scope"]["construction_version"] == "estimation_construction_v6_1" for bom in boms)
