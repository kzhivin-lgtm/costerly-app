from copy import deepcopy
from types import SimpleNamespace
import json

import pytest

from agents import estimation_analyze_v7_agent as agent
from use_cases.estimation_detection_context_v7 import build_context


def fixture():
    box = dict(top_left_x=10, top_left_y=10, bottom_right_x=100, bottom_right_y=100)
    row = dict(input_id="input-1", input_payload=dict(contract_version="estimation_input_v4", run_id="run-1", company_id="610",
        object=dict(object_id="object-001", quantity=1, evidence_pages=[dict(page_number=1, regions=[box])]),
        evidence=dict(ocr_blocks=[], ocr_literal_items=[])))
    fact = dict(evidence_type="matching_topology", observation="Same distinctive three bays.",
                source_fact_ids=["registry_view:view-001"])
    audit = dict(view_evidence_packages=[dict(visual_group_id="view-001",page_number=1,bbox=box)],
        registry_decision_audit=dict(visual_groups=[dict(group_id="original-1",page_number=1,bbox=box)]),
        semantic_ledger_audit=dict(accepted=[dict(fact,group_id_a="view-001",group_id_b="view-001")],
            object_hypotheses=dict(accepted=[dict(group_ids=["view-001"],evidence=[fact],hypothesis_reason="Distinctive structure.")])))
    event = dict(id="event-1",run_id="run-1",company_id="610",raw_usage=audit)
    return row, event


def result():
    return dict(objects=[dict(object_id="object-001",islands=[dict(island_id="view-001",
        projection="Front elevation",content_role="technical_drawing",observation="Three visible bays.")],
        understanding=dict(name="Display counter",type_code="display_counter",proposed_type=None,
            description="A straight counter.",characteristics=[dict(statement="Three bays.",basis="inferred",island_ids=["view-001"],source_refs=[])],
            materials=[dict(part="Carcass",material="LDSP",finish="unknown",thickness_mm=17,
                basis="default",island_ids=["view-001"],source_refs=[],reason="No source specification.")],
            assumptions=[],conflicts=[]))])


def test_hypothesis_export_without_merge_edges_is_lossless_and_scoped():
    row,event=fixture()
    original=deepcopy((row,event))
    context=build_context(inputs=[row],event=event)
    assert (row,event)==original
    obj=context["objects"][0]
    assert obj["islands"][0]["island_id"]=="view-001"
    assert obj["observation_aliases"]=={"original-1":"view-001"}
    assert obj["accepted_hypotheses"][0]["evidence"]==event["raw_usage"]["semantic_ledger_audit"]["object_hypotheses"]["accepted"][0]["evidence"]


def test_render_attachment_completes_membership_without_becoming_technical_hypothesis():
    row,event=fixture();audit=event["raw_usage"]
    second=dict(top_left_x=110,top_left_y=10,bottom_right_x=190,bottom_right_y=100)
    row["input_payload"]["object"]["evidence_pages"][0]["regions"].append(second)
    audit["view_evidence_packages"].append(dict(visual_group_id="view-002",page_number=1,bbox=second))
    audit["semantic_ledger_audit"]["v7_11_presentation_render"]={"decisions":[dict(
        disposition="attach",render_group_id="view-002",technical_group_id="view-001",
        evidence_type="matching_topology",visual_witness="Matching asymmetric arrangement.")]}
    context=build_context(inputs=[row],event=event)
    obj=context["objects"][0]
    assert len(obj["islands"])==2 and len(obj["presentation_render_decisions"])==1
    assert obj["accepted_hypotheses"][0]["group_ids"]==["view-001"]
    audit["semantic_ledger_audit"]["v7_11_presentation_render"]["decisions"][0]["technical_group_id"]="foreign"
    with pytest.raises(ValueError,match="cover frozen membership"):
        build_context(inputs=[row],event=event)


def test_source_fact_mapping_requires_exact_ocr_match(monkeypatch):
    row,event=fixture();box=dict(top_left_x=12,top_left_y=12,bottom_right_x=20,bottom_right_y=20)
    item=dict(block_ref="ocr:event-ocr:p1:b0001",page_number=1,text="40",bbox=box)
    row["input_payload"]["evidence"]["ocr_blocks"]=[item]
    event["raw_usage"]["semantic_ledger_audit"]["object_hypotheses"]["accepted"][0]["evidence"][0]["source_fact_ids"].append("SF00001")
    monkeypatch.setattr("agents.anthropic_adapter.build_detection_page_evidence_inventory",lambda package:
        [dict(fact_id="SF00001",page_number=1,text="40",bbox=box)])
    context=build_context(inputs=[row],event=event,ocr_package={})
    assert context["objects"][0]["source_fact_mapping"]=={"SF00001":item["block_ref"]}
    item["text"]="41"
    with pytest.raises(ValueError,match="unmapped Detection source fact"):
        build_context(inputs=[row],event=event,ocr_package={})


@pytest.mark.parametrize("problem",["foreign_run","duplicate_bbox","foreign_ref","incomplete_hypothesis"])
def test_context_rejects_unverifiable_mapping(problem):
    row,event=fixture()
    if problem=="foreign_run": event["run_id"]="other"
    if problem=="duplicate_bbox": event["raw_usage"]["view_evidence_packages"].append(dict(event["raw_usage"]["view_evidence_packages"][0],visual_group_id="view-002"))
    h=event["raw_usage"]["semantic_ledger_audit"]["object_hypotheses"]["accepted"][0]
    if problem=="foreign_ref": h["evidence"][0]["source_fact_ids"]=["registry_view:foreign"]
    if problem=="incomplete_hypothesis": h["group_ids"]=["foreign"]
    with pytest.raises(ValueError): build_context(inputs=[row],event=event)


@pytest.mark.parametrize("problem",["foreign_island","missing_island","foreign_source","long_name","wrong_type","nan_thickness"])
def test_result_rejects_cross_object_refs_and_bad_contract(problem):
    row,event=fixture(); context=build_context(inputs=[row],event=event); value=result()
    u=value["objects"][0]["understanding"]
    if problem=="foreign_island": u["characteristics"][0]["island_ids"]=["view-other"]
    if problem=="missing_island": value["objects"][0]["islands"]=[]
    if problem=="foreign_source": u["materials"][0]["source_refs"]=["ocr:foreign"]
    if problem=="long_name": u["name"]="A very long counter name"
    if problem=="wrong_type": u["type_code"]="invented"
    if problem=="nan_thickness": u["materials"][0]["thickness_mm"]=float("nan")
    with pytest.raises(ValueError): agent.validate_result(value,detection_context=context,inputs=[row])


def test_one_shared_call_records_raw_before_validation_without_continuation(monkeypatch):
    row,event=fixture(); context=build_context(inputs=[row],event=event)
    monkeypatch.setattr(agent,"prepare_content",lambda **kwargs: [{"type":"text","text":"saved evidence"}])
    options=[]; requests=[]; records=[]
    monkeypatch.setattr(agent.existing,"get_anthropic_client",lambda:SimpleNamespace(with_options=lambda **kwargs:options.append(kwargs)))
    monkeypatch.setattr(agent.existing,"_create_message_with_hard_timeout",lambda *a,**kwargs:
        requests.append(kwargs) or SimpleNamespace(stop_reason="end_turn",content=[SimpleNamespace(type="text",text=json.dumps(result()))]))
    value=agent.run_analyze(inputs=[row],page_bytes={},detection_context=context,record=lambda stage,*args:records.append(stage))
    assert len(requests)==1 and records==["request","response"]
    assert options==[dict(timeout=120,max_retries=0)] and len(value["objects"])==1
    monkeypatch.setattr(agent,"validate_result",lambda *a,**k:(_ for _ in ()).throw(ValueError("invalid")))
    records.clear()
    with pytest.raises(ValueError): agent.run_analyze(inputs=[row],page_bytes={},detection_context=context,record=lambda stage,*args:records.append(stage))
    assert records==["request","response"]


def test_source_crop_ownership_uses_explicit_global_ids():
    from io import BytesIO
    from PIL import Image
    from agents.estimation_visual_evidence import page_content
    row,_=fixture(); payload=row["input_payload"]
    payload["evidence"]["geometry_context"]={"rendering":{"dpi":200},"page_profiles":[{"page_number":1,"width":200,"height":200}]}
    # Use the same coordinate-frame contract as existing visual-evidence tests.
    from tests.test_estimation_visual_evidence import payload as make_payload
    payload=make_payload()
    payload["object"]["object_id"]="object-001"
    buffer=BytesIO();Image.new("RGB",(1000,1000),"white").save(buffer,format="WEBP")
    view=dict(view_id="view-global",page_number=1,object_id="object-001",bbox={"top_left_x":100,"top_left_y":100,"bottom_right_x":300,"bottom_right_y":300})
    blocks,count=page_content(page_bytes=buffer.getvalue(),storage_ref="ref",page_number=1,payloads=[payload],views=[view],include_single_detail=True)
    assert count==1 and any("view-global" in b.get("text","") for b in blocks)
    view["object_id"]="other"
    _,count=page_content(page_bytes=buffer.getvalue(),storage_ref="ref",page_number=1,payloads=[payload],views=[view],include_single_detail=True)
    assert count==0


def test_detection_frame_overrides_portrait_profile_without_guessing_rotation():
    from io import BytesIO
    from PIL import Image
    from agents.estimation_visual_evidence import page_content
    from tests.test_estimation_visual_evidence import payload as make_payload
    payload=make_payload();payload["object"]["object_id"]="object-001"
    buffer=BytesIO();Image.new("RGB",(2000,1414),"white").save(buffer,format="WEBP")
    view=dict(view_id="view-001",page_number=1,object_id="object-001",
        coordinate_frame_pixels=[2339,1654],bbox=dict(top_left_x=819,top_left_y=79,bottom_right_x=2140,bottom_right_y=859))
    blocks,count=page_content(page_bytes=buffer.getvalue(),storage_ref="ref",page_number=1,payloads=[payload],views=[view],include_single_detail=True)
    metadata=json.loads(blocks[0]["text"])
    assert count==1
    region=metadata["view_regions"][0]
    assert region["coordinate_frame_pixels"]==[2339,1654]
    assert region["bbox_normalized"]==pytest.approx([819/2339,79/1654,2140/2339,859/1654])


def test_failed_contract_report_displays_original_without_promoting_or_html_injection():
    from tools.probe_estimation_analyze_v7 import render_report
    value=result();value["objects"][0]["understanding"]["name"]="A long name <script>"
    witness=dict(status="failed",error="name exceeds limit",raw_response_text=json.dumps(value))
    original=deepcopy(witness)
    html=render_report(witness)
    assert "FORMAT FAILURE" in html and "&lt;script&gt;" in html
    assert "<script>" not in html and witness==original and "result" not in witness
