from copy import deepcopy
from types import SimpleNamespace
import json

import pytest

from agents import estimation_analyze_v7_2_agent as agent
from tests.test_estimation_analyze_v7 import fixture, result
from use_cases.estimation_detection_context_v7 import build_context


def setup():
    row, event = fixture()
    context = build_context(inputs=[row], event=event)
    context["contract_version"] = "estimation_detection_context_v7_2"
    context["objects"][0]["dimension_inventory"] = [dict(group_id="view-001", occurrences=[dict(
        occurrence_id="view-001-D001", original_text="4", value_mm="40", unit_basis="cm")])]
    value = result()
    obj = value["objects"][0]
    obj["islands"][0]["elevation_index"] = 1
    obj["understanding"]["materials"][0].update(material_kind="sheet", thickness_measurement_id=None)
    obj["front"] = dict(front_groups=[], excluded_surfaces=[], tabletop_supports=[],
        totals=dict(drawers=0, hinged_doors=0, lift_up_fronts=0, unresolved_fronts=0, total_fronts=0))
    obj["planner"] = dict(summary="One counter.", blocks=[dict(id="B01",name="Counter",contains="Carcass.",
        reason="One continuous carcass.",front_ids=[],view_ids=["view-001"],
        region=dict(view_id="view-001",bbox_1000=[100,100,900,900]))],shared_parts=[],front_conflicts=[],uncertainties=[])
    return row, context, value


def test_combined_response_reuses_reference_validators_without_mutating_raw():
    row,context,value=setup(); original=deepcopy(value)
    assert agent.validate_result(value,detection_context=context,inputs=[row])==original
    assert value==original
    assert agent.hardware_preview(value)["object-001"]["lift_system_sets"]==0


@pytest.mark.parametrize("problem",["wrong_thickness","missing_sheet_thickness","bad_index","front_arithmetic","omitted_front","foreign_measurement","foreign_island"])
def test_blocks_front_and_measurements_are_gated(problem):
    row,context,value=setup();obj=value["objects"][0];m=obj["understanding"]["materials"][0]
    if problem=="wrong_thickness":m.update(thickness_measurement_id="view-001-D001",thickness_mm=4)
    if problem=="missing_sheet_thickness":m["thickness_mm"]=None
    if problem=="bad_index":obj["islands"][0]["elevation_index"]=2
    if problem=="front_arithmetic":obj["front"]["totals"]["drawers"]=1
    if problem=="omitted_front":
        obj["front"]["front_groups"]=[dict(location="base",type="drawer",count=1,count_basis="clear",view_ids=["view-001"],uncertainty="",
            fronts=[dict(id="F01",view_id="view-001",bbox_1000=[100,100,200,200])])]
        obj["front"]["totals"].update(drawers=1,total_fronts=1)
    if problem=="foreign_measurement":m["thickness_measurement_id"]="foreign"
    if problem=="foreign_island":obj["planner"]["blocks"][0]["view_ids"]=["foreign"]
    with pytest.raises(ValueError):agent.validate_result(value,detection_context=context,inputs=[row])


def test_source_thickness_uses_normalized_value_and_honors_provenance():
    row,context,value=setup();m=value["objects"][0]["understanding"]["materials"][0]
    m.update(thickness_mm=40,thickness_measurement_id="view-001-D001",source_refs=["view-001-D001"])
    agent.validate_result(value,detection_context=context,inputs=[row])


def test_export_copies_saved_normalization_without_reinferring_units(monkeypatch):
    row,event=fixture();box=dict(top_left_x=12,top_left_y=12,bottom_right_x=20,bottom_right_y=20)
    row["input_payload"]["evidence"]["ocr_blocks"]=[dict(block_ref="ocr:x:p1:b0001",page_number=1,text="4",bbox=box)]
    monkeypatch.setattr("agents.anthropic_adapter.build_detection_page_evidence_inventory",lambda package:
        [dict(fact_id="SF00001",page_number=1,text="4",bbox=box)])
    event["raw_usage"].update(dimension_inventory_valid=True,
        dimension_inventory=[dict(group_id="view-001",occurrences=[dict(occurrence_id="view-001-D001",original_text="4",value_mm="40",unit_basis="cm",source_fact_ids=["SF00001"])])],
        dimension_graph_audit=dict(effective_document_dimension_unit="cm",effective_document_dimension_unit_reason="saved_decision"),
        document_dimension_unit_profile=dict(unit="unknown"))
    before=deepcopy(event)
    context=build_context(inputs=[row],event=event,ocr_package={},include_measurements=True)
    assert event==before
    assert context["unit_context"]["effective_unit"]=="cm"
    measurement=context["objects"][0]["dimension_inventory"][0]["occurrences"][0]
    assert measurement["value_mm"]=="40" and measurement["unit_basis"]=="cm"
    assert measurement["source_refs"]==["ocr:x:p1:b0001"]
    event["raw_usage"]["dimension_inventory"][0]["occurrences"][0]["source_fact_ids"]=["SF_UNKNOWN"]
    with pytest.raises(ValueError,match="unmapped OCR"):
        build_context(inputs=[row],event=event,ocr_package={},include_measurements=True)


def test_all_sections_use_one_provider_call_and_preserve_raw_before_rejection(monkeypatch):
    row,context,value=setup();calls=[];records=[];options=[]
    monkeypatch.setattr(agent.previous,"prepare_content",lambda **kwargs:[dict(type="text",text="saved input")])
    monkeypatch.setattr(agent.existing,"get_anthropic_client",lambda:SimpleNamespace(with_options=lambda **kwargs:options.append(kwargs)))
    monkeypatch.setattr(agent.existing,"_create_message_with_hard_timeout",lambda *a,**kwargs:
        calls.append(kwargs) or SimpleNamespace(stop_reason="end_turn",content=[SimpleNamespace(type="text",text=json.dumps(value))]))
    agent.run_analyze(inputs=[row],page_bytes={},detection_context=context,record=lambda stage,*args:records.append(stage))
    assert len(calls)==1 and records==["request","response"]
    assert options==[dict(timeout=120,max_retries=0)]
    assert calls[0]["thinking"]==dict(type="disabled") and calls[0]["model"]=="claude-haiku-5-5"
    value["objects"][0]["planner"]["blocks"][0]["front_ids"]=["F_FOREIGN"]
    records.clear()
    with pytest.raises(ValueError):agent.run_analyze(inputs=[row],page_bytes={},detection_context=context,record=lambda stage,*args:records.append(stage))
    assert records==["request","response"]


def test_prompt_uses_existing_policies_and_one_output_template():
    text=agent.prompt()
    assert text.count("SINGLE AUTHORITATIVE RESPONSE TEMPLATE")==1
    assert "CB Planner V7" in text and "COUNT PHYSICAL OPERATING FRONTS" in text
    assert '"island_types"' not in text
    assert '"planner"' in text and '"front"' in text
