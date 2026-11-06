from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from agents.estimation_understanding_agent import prepare_content, CB_RULEBOOK
from tests.test_cb_parts_v4 import setup, compose
from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_measurement_packet import (
    build_measurement_packet, resolve_measured_dimensions, source_to_detail,
    _single_label_supported,
)


def measured(monkeypatch):
    row, pages, scope, raw = setup(monkeypatch)
    scope['parts_version'] = 'CB Parts V4.1'
    for i,f in enumerate(scope['front']['front_groups'][0]['fronts']):
        f['bbox_1000']=[100+i*500,200,400+i*500,800]
    view = raw['runs'][0]['view_id']
    packet = dict(input_id=scope['input_id'], dimensions=[])
    for index, d in enumerate(raw['dimensions'][:2]):
        sid = f's{index}'
        packet['dimensions'].append(dict(source_id=sid,label=str(d['value']/10),value_mm=d['value'],
            unit_basis='scale_policy_assumption',evidence_refs=['p'],locations=[dict(view_id=view)],
            candidates=[dict(candidate_id=sid,view_id=view,orientation='horizontal',
                endpoints_1000=[index*500,100,(index+1)*500,100])]))
        raw['dimensions'][index] = dict(id=d['id'],source_id=sid,candidate_id=sid,view_id=view,reason='Source span.')
    for i in (2,3):
        d=raw['dimensions'][i];raw['dimensions'][i]=dict(id=d['id'],value_mm=d['value'],reason=d['reason'])
    return row,pages,scope,raw,packet


def test_copy_values_and_preserve_raw_and_provenance(monkeypatch):
    row,_,scope,raw,packet=measured(monkeypatch)
    before=deepcopy((raw,packet,scope))
    converted,audit=resolve_measured_dimensions(raw,packet=packet,scope=scope)
    assert (raw,packet,scope)==before
    assert [d['value'] for d in converted['dimensions']]==[600,400,800,720]
    assert not audit['dimensions'][0]['ownership_verified']
    assert audit['dimensions'][0]['unit_basis']=='scale_policy_assumption'
    assert compose(row,scope,converted)['geometry_scheme']['runs']['R1']['width_mm']==1000


@pytest.mark.parametrize('change', ['number_override','source','candidate','view','duplicate','duplicate_source',
    'null_scale','negative','gap','overlap','outside','foreign_packet','not_object'])
def test_invalid_measurements_fail_without_repair(monkeypatch,change):
    _,_,scope,raw,packet=measured(monkeypatch)
    d=raw['dimensions'][0]; c=packet['dimensions'][0]['candidates'][0]
    if change=='number_override':d['value_mm']=999
    if change=='source':d['source_id']='foreign'
    if change=='candidate':d['candidate_id']='foreign'
    if change=='view':d['view_id']='foreign'
    if change=='duplicate':raw['dimensions'].append(deepcopy(d))
    if change=='duplicate_source':raw['dimensions'][1].update(source_id='s0',candidate_id='s0')
    if change=='null_scale':packet['dimensions'][0]['value_mm']=None
    if change=='negative':raw['dimensions'][2]['value_mm']=-1
    if change=='gap':c['endpoints_1000'][2]=450
    if change=='overlap':c['endpoints_1000'][2]=550
    if change=='outside':
        scope['front']['front_groups'][0]['fronts'][0]['bbox_1000']=[0,0,100,100]
        c['endpoints_1000'][0]=200
    if change=='foreign_packet':packet['input_id']='foreign'
    if change=='not_object':raw['dimensions'][0]=1
    with pytest.raises(ValueError):resolve_measured_dimensions(raw,packet=packet,scope=scope)


@pytest.mark.parametrize('change',['no_candidate','different_view','assumption'])
def test_unanchored_is_not_certified(monkeypatch,change):
    _,_,scope,raw,packet=measured(monkeypatch)
    if change=='no_candidate':raw['dimensions'][0]['candidate_id']=None
    if change=='different_view':raw['runs'][0]['view_id']='other'
    if change=='assumption':raw['dimensions'][0]=dict(id='D1',value_mm=600,reason='Estimate.')
    _,audit=resolve_measured_dimensions(raw,packet=packet,scope=scope)
    assert audit['run_checks'][0]['status']=='no_complete_same_view_width_anchor'


def test_transform_includes_actual_scale_crop_and_header():
    f=dict(source_frame=[800,400],page_size=[400,200],detail_size=[250,150],crop_origin=[80,40],header=32)
    assert source_to_detail(dict(x=200,y=116),f)==[80,333.333]


def test_missing_front_box_is_explicitly_unchecked(monkeypatch):
    _,_,scope,raw,packet=measured(monkeypatch)
    del scope['front']['front_groups'][0]['fronts'][0]['bbox_1000']
    _,audit=resolve_measured_dimensions(raw,packet=packet,scope=scope)
    assert audit['run_checks'][0]['unchecked_front_ids']==['F01']
    assert audit['run_checks'][0]['status']=='partial_front_interval_check'


def test_chain_with_multiple_labels_or_missing_endpoints_is_not_promoted():
    def number(id,x):return dict(dimension_id=id,bbox=dict(top_left_x=x-5,top_left_y=80,bottom_right_x=x+5,bottom_right_y=100))
    a,b=number('a',100),number('b',200)
    line=dict(orientation='horizontal',start=dict(x=50,y=100),end=dict(x=250,y=100),endpoint_crossing_candidates=[['x'],['y']])
    assert not _single_label_supported(a,line,[a,b])
    line['end']['x']=150
    assert _single_label_supported(a,line,[a,b])
    line['endpoint_crossing_candidates'][1]=[]
    assert not _single_label_supported(a,line,[a,b])


def test_packet_real_raster_reuses_source_units_and_is_immutable():
    from tests.test_estimation_evidence_map import fixture
    row,pages=fixture(); before=deepcopy(row)
    packet=build_measurement_packet(input_row=row,page_bytes=pages,content=[],front={'front_groups':[]})
    assert packet['dimensions'][0]['value_mm']==720
    assert row==before
    assert packet['dimensions'][0]['locations']==[]  # no invented image/frame


def test_single_call_preserves_evidence_and_raw_uses_new_contract(monkeypatch):
    row,pages,scope,raw,packet=measured(monkeypatch)
    content,_=prepare_content([row],pages);calls=[];records=[]
    monkeypatch.setattr('use_cases.estimation_measurement_packet.build_measurement_packet',lambda **kw:packet)
    monkeypatch.setattr(agent,'get_anthropic_client',lambda:SimpleNamespace(with_options=lambda **kw:object()))
    monkeypatch.setattr(agent,'build_agent_usage_event',lambda **kw:{})
    def provider(*args,**kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason='end_turn',content=[SimpleNamespace(type='text',text=json.dumps(raw))])
    monkeypatch.setattr(agent,'_create_message_with_hard_timeout',provider)
    result=agent.run_estimation_assembly_bom_agent(input_row=row,evidence_page_bytes_by_ref=pages,
        dimension_graph=build_dimension_graph(input_row=row),dimension_scale_gate={},allowed_material_families=['ldsp','mdf'],
        cb_parts_scope=scope,record=lambda stage,*args:records.append(stage))
    assert len(calls)==1 and calls[0]['model']=='claude-haiku-5-5'
    assert calls[0]['system'].splitlines()[0]=='CB Parts V4.1'
    assert calls[0]['messages'][0]['content'][:-1]==content
    assert json.loads(calls[0]['messages'][0]['content'][-1]['text'])['measurement_packet']==packet
    assert records==['calculation_request','calculation']
    assert result['extraction']==raw and result['bom']['parts']
    assert result['status']==result['bom']['status']=='cb_parts_v4_1_requires_review'
    assert result['bom']['prompt_version']=='CB Parts V4.1'
    assert result['upstream_status']['front']=='failed'
    assert CB_RULEBOOK['parts']['version']=='CB Parts V3'


def test_live_failures_are_retained_and_source_numbers_are_not_model_values():
    from agents.estimation_v4_1_material_facts_agent import _json_object
    root=Path(__file__).resolve().parents[1]
    record=json.loads((root/'notes/evidence/cb-parts-v4-1-2026-11-06/three-object-trials.json').read_text())
    prompt=(root/'agents/prompts/cb_parts_v4_1.md').read_text().strip()
    assert record['accepted_count']==0 and not record['production_promoted']
    trials=record['trials']
    assert [t['front_coverage_audit']['assigned_count'] for t in trials]==[11,3,13]
    for t in trials:
        assert t['status']=='failed' and t['stop_reason']=='end_turn' and t['provider_calls']==1
        assert t['source_evidence_unchanged'] and not t['accepted']
        assert t['prompt_sha256']==sha256(prompt.encode()).hexdigest()
        for d in t['source_reference_audit']:
            if d['valid'] and 'source_id' in d['audit']:
                source=next(s for s in t['measurement_packet']['dimensions'] if s['source_id']==d['audit']['source_id'])
                assert d['resolved']['value']==source['value_mm']
                assert not d['audit']['ownership_verified']
    lev2=trials[0]
    d=next(d for d in lev2['measurement_packet']['dimensions'] if d['label']=='151')
    assert len(d['candidates'])==1
    assert d['candidates'][0]['front_centres_inside_x']==['F20','F21','F22','F23','F24']
    assert lev2['single_span_contradictions'][1]['outside_front_ids']==['F18','F19']
    lev1=_json_object(trials[1]['raw_response_text'])
    assert len(lev1['runs'][0]['bays'])==3
    dims={d['dimension_id']:d['resolved']['value'] for d in trials[1]['source_reference_audit']}
    assert [dims[x] for x in ['D_WIDTH','D_SEAT_H','D_DEPTH']]==[1580,430,720]
    assert dims['D_TOP_DEPTH']==1150  # deliberately wrong leg diameter remains raw
    assert lev1['explicit_assemblies'][1]['parts'][1]['width_ref']=='D_TOP_DEPTH'
