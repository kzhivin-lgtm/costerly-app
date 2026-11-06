from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_parts import fixture
from use_cases.estimation_cb_v4 import compose_cb_v4
from use_cases.estimation_dimension_graph import build_dimension_graph


def setup(monkeypatch):
    row, pages, scope, _ = fixture(monkeypatch)
    scope["parts_version"] = "CB Parts V4"
    view = scope["front"]["island_types"][0]["view_id"]
    def dim(id, value):
        return dict(id=id, value=value, unit="mm", basis="assumption", view_id=None, label="", reason="Coarse estimate.")
    raw = dict(summary="Two adjacent drawer sections with a separate worktop.",
        materials=[dict(id="M1", name="LDSP", family="ldsp", stock_thickness_mm=17, layers=1,
            finish="laminated", edge_treatment="matching edge", basis="construction_assumption", evidence_refs=[], reason="Unspecified board fallback."),
            dict(id="M2", name="MDF top", family="mdf", stock_thickness_mm=30, layers=1,
            finish="painted", edge_treatment="painted", basis="construction_assumption", evidence_refs=[], reason="Assumed top.")],
        dimensions=[dim("D1",600),dim("D2",400),dim("H",800),dim("D",720)],
        runs=[dict(id="R1", name="Whole straight base run", view_id=view, width_ids=["D1","D2"], height_id="H",depth_id="D",
            bays=[dict(id="Q1",width_weight=1,shelves=0,opening_weight=0,fronts=[dict(id="F01",height_weight=1)]),
                dict(id="Q2",width_weight=1,shelves=0,opening_weight=0,fronts=[dict(id="F02",height_weight=1)])])],
        blocks=[dict(id="NEW", name="Joined base carcass",run_id="R1",bay_ids=["Q1","Q2"],
            body_material_id="M1",front_material_id="M1",drawer_material_id="M1",reason="Shared drawer mounting wall.")],
        explicit_assemblies=[dict(id="TOP",name="Separate top",parts=[dict(id="P1",name="Worktop",role="worktop",quantity=1,
            length_ref="R1.width",width_ref="R1.depth",material_id="M2",reason="Entire supporting run footprint.")])], uncertainties=[])
    return row, pages, scope, raw


def compose(row, scope, raw):
    return compose_cb_v4(raw, scope=scope,input_row=row,dimension_graph=build_dimension_graph(input_row=row),allowed_material_families=["ldsp","mdf","solid_wood"])


def test_geometry_then_grouping_then_material_parts(monkeypatch):
    row, _, scope, raw = setup(monkeypatch)
    before = deepcopy((row,scope,raw))
    bom = compose(row,scope,raw)
    assert (row,scope,raw) == before
    assert bom["status"] == "cb_parts_v4_requires_review"
    assert bom["geometry_scheme"]["runs"]["R1"]["width_mm"] == 1000
    assert [b["width"] for b in bom["geometry_scheme"]["bays"].values()] == [500,500]
    assert {a["assembly_id"] for a in bom["assemblies"]} == {"NEW","TOP"}
    parts = {p["name"]:p for p in bom["parts"]}
    assert parts["Carcass top"]["length_mm"] == parts["Worktop"]["length_mm"] == 1000
    assert parts["Shared mounting partition"]["quantity"] == 1
    assert parts["Drawer body side"]["length_mm"] == 600
    assert parts["Drawer body side"]["width_mm"] == 250  # coarse body policy cap
    assert parts["Drawer bottom"]["quantity"] == 2
    assert parts["Worktop"]["thickness_mm"] == 30
    assert all(p["palette_material_id"] and p["part_id"] and p["dimension_dependencies"] for p in bom["parts"])
    assert bom["upstream_status"]["front"] == "failed"


def test_regrouping_does_not_reestimate_bay_geometry(monkeypatch):
    row,_,scope,raw=setup(monkeypatch)
    a=compose(row,scope,raw)
    b=deepcopy(raw["blocks"][0]); raw["blocks"][0]["bay_ids"]=["Q1"]
    b.update(id="SECOND",bay_ids=["Q2"]); raw["blocks"].append(b)
    out=compose(row,scope,raw)
    assert a["geometry_scheme"] == out["geometry_scheme"]
    assert [b["size_mm"][0] for b in out["resolved_blocks"]] == [500,500]
    assert sum(p["quantity"] for p in out["parts"] if p["component_role"]=="side") == 4


def test_vertical_stack_and_open_space_share_height(monkeypatch):
    row,_,scope,raw=setup(monkeypatch)
    q=raw["runs"][0]["bays"][0]
    q["fronts"].append(raw["runs"][0]["bays"].pop()["fronts"][0]);q["opening_weight"]=2
    raw["blocks"][0]["bay_ids"]=["Q1"]
    out=compose(row,scope,raw);bay=out["geometry_scheme"]["bays"]["Q1"]
    assert bay["width"]==1000 and bay["opening_height_mm"]==400
    assert [f["height"] for f in bay["fronts"]]==[200,200]
    assert not any(p["component_role"]=="partition" for p in out["parts"])


def test_finished_layers_and_material_override_do_not_change_hidden_board(monkeypatch):
    row,_,scope,raw=setup(monkeypatch)
    raw["materials"][1].update(name="Veneered MDF",stock_thickness_mm=20,layers=2,finish="oak veneer",edge_treatment="veneer edge")
    raw["blocks"][0]["front_material_id"]="M2"
    out=compose(row,scope,raw)
    assert {p["thickness_mm"] for p in out["parts"] if p["component_role"]=="facade"}=={40}
    assert {p["thickness_mm"] for p in out["parts"] if p["component_role"]=="drawer_side"}=={17}
    total=next(t for t in out["material_area_per_object"] if t["palette_material_id"]=="M2")
    assert total["stock_area_m2"]==total["finished_area_m2"]*2
    assert next(m for m in out["materials"] if m["family"]=="mdf")["specification"]["edge_treatment"]=="veneer edge"


def test_non_cabinet_explicit_object_and_support_no_sheet_area(monkeypatch):
    row,_,scope,raw=setup(monkeypatch)
    scope["front"]["front_groups"]=[];raw["runs"]=[];raw["blocks"]=[]
    raw["materials"]=raw["materials"][:1];raw["materials"][0].update(family="solid_wood",name="Round wood stock",stock_thickness_mm=40)
    p=raw["explicit_assemblies"][0]["parts"][0];p.update(role="support",quantity=2,length_ref="H",width_ref="D2",material_id="M1")
    out=compose(row,scope,raw)
    assert len(out["parts"])==1 and out["parts"][0]["quantity"]==2
    assert out["material_area_per_object"][0]["stock_area_m2"]==0


@pytest.mark.parametrize("change", ["missing_front","duplicate_front","unknown_front","missing_bay","duplicate_bay","unknown_run","foreign_bay","unknown_material","unused_material","nan","bad_unit","duplicate_dimension","duplicate_width_ref","unknown_ref","empty_stack","negative_opening","float_shelves","extra_field","bad_layers","foreign_evidence","false_source","duplicate_part","expression_ref"])
def test_invalid_graph_fails_without_repair(monkeypatch,change):
    row,_,scope,raw=setup(monkeypatch); r=raw["runs"][0]; q=r["bays"][0]; b=raw["blocks"][0]
    if change=="missing_front": q["fronts"]=[];q["opening_weight"]=1
    if change=="duplicate_front":q["fronts"].append(deepcopy(q["fronts"][0]))
    if change=="unknown_front":q["fronts"][0]["id"]="UNKNOWN"
    if change=="missing_bay":b["bay_ids"].pop()
    if change=="duplicate_bay":r["bays"][1]["id"]="Q1"
    if change=="unknown_run":b["run_id"]="UNKNOWN"
    if change=="foreign_bay":b["bay_ids"]=["UNKNOWN"]
    if change=="unknown_material":b["body_material_id"]="UNKNOWN"
    if change=="unused_material":raw["materials"].append({**raw["materials"][0],"id":"UNUSED"})
    if change=="nan":q["width_weight"]=float("nan")
    if change=="bad_unit":raw["dimensions"][0]["unit"]="inch"
    if change=="duplicate_dimension":raw["dimensions"].append(deepcopy(raw["dimensions"][0]))
    if change=="duplicate_width_ref":r["width_ids"]=["D1","D1"]
    if change=="unknown_ref":r["height_id"]="UNKNOWN"
    if change=="empty_stack":q["fronts"]=[]
    if change=="negative_opening":q["opening_weight"]=-1
    if change=="float_shelves":q["shelves"]=0.5
    if change=="extra_field":q["width"]=500
    if change=="bad_layers":raw["materials"][0]["layers"]=0
    if change=="foreign_evidence":raw["materials"][0].update(basis="source_evidence",evidence_refs=["foreign"])
    if change=="false_source":raw["materials"][0]["basis"]="source_evidence"
    if change=="duplicate_part":raw["explicit_assemblies"][0]["parts"]*=2
    if change=="expression_ref":raw["explicit_assemblies"][0]["parts"][0]["length_ref"]="D1+D2"
    before=deepcopy(raw)
    with pytest.raises(ValueError):compose(row,scope,raw)
    if change!="nan":assert raw==before


def test_single_call_hides_planner_keeps_all_images_and_raw(monkeypatch):
    row,pages,scope,raw=setup(monkeypatch)
    from agents.estimation_understanding_agent import prepare_content,CB_RULEBOOK
    content,_=prepare_content([row],pages); calls=[]
    scope["planner"]={"untrusted_old_grouping":"do not transmit or require its schema"}
    monkeypatch.setattr(agent,"get_anthropic_client",lambda:SimpleNamespace(with_options=lambda **kw:object()))
    monkeypatch.setattr(agent,"build_agent_usage_event",lambda **kw:{})
    def provider(*args,**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn",content=[SimpleNamespace(type="text",text=json.dumps(raw))])
    monkeypatch.setattr(agent,"_create_message_with_hard_timeout",provider)
    result=agent.run_estimation_assembly_bom_agent(input_row=row,evidence_page_bytes_by_ref=pages,
        dimension_graph=build_dimension_graph(input_row=row),dimension_scale_gate={},allowed_material_families=["ldsp","mdf"],cb_parts_scope=scope)
    assert len(calls)==1 and calls[0]["model"]=="claude-haiku-5-5"
    assert calls[0]["system"].splitlines()[0]=="CB Parts V4"
    assert calls[0]["messages"][0]["content"][:-1]==content
    supplied=json.loads(calls[0]["messages"][0]["content"][-1]["text"])
    assert "planner" not in supplied["calculation_scope"]
    assert supplied["calculation_scope"]["front"]==scope["front"]
    assert result["extraction"]==raw and result["bom"]["parts"]
    assert CB_RULEBOOK["parts"]["version"]=="CB Parts V3"  # opt-in, no promotion


def test_source_claim_stays_auditable_without_certifying_visual_material(monkeypatch):
    row,_,scope,raw=setup(monkeypatch)
    ref=row["input_payload"]["evidence"]["artifacts"][0]["storage_ref"]
    raw["materials"][0].update(basis="source_evidence",evidence_refs=[ref])
    out=compose(row,scope,raw)
    assert out["material_interpretations"][0]["evidence_refs"]==[ref]
    assert all(m["basis"]=="construction_assumption" for m in out["materials"])


@pytest.mark.parametrize("change",[None,"incomplete","text","multiple_objects"])
def test_v4_front_loader_does_not_require_previous_planner(monkeypatch,tmp_path,change):
    from tools.probe_cb_parts import load_v4_scope
    row,_,scope,_=setup(monkeypatch)
    text=json.dumps(scope["front"])
    record={"stage":"front_count","response_text":text,"response":{"stop_reason":"end_turn","content":[{"type":"text","text":text}]}}
    w={"inputs":[row],"status":"failed","provider_responses":[record]}
    if change=="incomplete":record["response"]["stop_reason"]="max_tokens"
    if change=="text":record["response_text"]="{}"
    if change=="multiple_objects":w["inputs"]*=2
    path=tmp_path/"front.json";path.write_text(json.dumps(w))
    if change:
        with pytest.raises(ValueError):load_v4_scope(path)
    else:
        prior,loaded=load_v4_scope(path)
        assert prior==w and loaded["front"]==scope["front"]
        assert "planner" not in loaded and loaded["upstream_status"]["front"]=="failed"


def test_three_live_failures_preserve_complete_raw_and_do_not_claim_acceptance():
    from agents.estimation_v4_1_material_facts_agent import _json_object
    from hashlib import sha256
    root=Path(__file__).resolve().parents[1]
    record=json.loads((root/"notes/evidence/cb-parts-v4-2026-11-06/three-object-trials.json").read_text())
    prompt=(root/"agents/prompts/cb_parts_v4.md").read_text().strip()
    assert not record["production_promoted"]
    trials=record["trials"]
    assert [len(t["front_coverage_audit"]["missing_front_ids"]) for t in trials]==[9,0,13]
    for t in trials:
        assert t["status"]=="failed" and not t["accepted"] and t["provider_calls"]==1
        assert t["stop_reason"]=="end_turn" and t["source_evidence_unchanged"]
        assert t["prompt_sha256"]==sha256(prompt.encode()).hexdigest()
        assert "planner" not in t["outgoing_context"]["calculation_scope"]
        raw=_json_object(t["raw_response_text"])
        expected={f["id"] for g in t["outgoing_context"]["calculation_scope"]["front"]["front_groups"] for f in g["fronts"]}
        actual=[f["id"] for r in raw["runs"] for b in r["bays"] for f in b["fronts"]]
        assert sorted(expected-set(actual))==t["front_coverage_audit"]["missing_front_ids"]
    lev1=_json_object(trials[1]["raw_response_text"])
    assert len(lev1["runs"][0]["bays"])==1  # wrong vertical stack retained
    assert lev1["dimensions"][0]["value"]==160 and lev1["dimensions"][0]["unit"]=="mm"
    assert lev1["materials"][-1]["stock_thickness_mm"]==lev1["materials"][-1]["layers"]==0
