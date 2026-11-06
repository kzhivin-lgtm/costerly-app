from copy import deepcopy
import base64
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents import estimation_understanding_agent as existing
from agents import estimation_cb_cycle_v5_agent as agent
from tests.test_estimation_module_understanding import setup
from tests.test_estimation_understanding import fixture as understanding_fixture
from tests.test_cb_front_supports import supported
from tests.test_cb_planner import plan
from use_cases.estimation_cb_cycle_v5 import validate_front, validate_plan, parts_scope


def fixture(monkeypatch):
    row,pages,_=setup(monkeypatch)
    _,manifests=existing.prepare_content([row],pages)
    u=understanding_fixture()[2]['objects'][0]
    u['views']=[dict(id='p1-view-001',page_number=1,location='centre',observation='Whole object.')]
    u['components'][0]['view_ids']=['p1-view-001'];u['cross_view_links']=[]
    u['components'].append({**deepcopy(u['components'][0]),'id':'fixed','name':'Fixed screen'})
    front=supported()
    result=dict(understanding=u,front=front,
        front_components=[dict(front_id=f['id'],component_id='c') for g in front['front_groups'] for f in g['fronts']],
        support_components=[dict(support_id='T01',component_id='c')])
    p=plan();p['blocks'][0]['front_ids']=[x['front_id'] for x in result['front_components']]
    p['blocks'].append({**deepcopy(p['blocks'][0]),'id':'B02','name':'Fixed screen','front_ids':[]})
    planner=dict(plan=p,component_blocks=[dict(component_id='c',block_ids=['B01']),dict(component_id='fixed',block_ids=['B02'])],interpretation_conflicts=[])
    return row,pages,manifests,result,planner


def test_interpretation_links_preserved_to_parts_without_rewriting(monkeypatch):
    _,_,m,f,p=fixture(monkeypatch);before=deepcopy((f,p))
    validate_front(f,m);validate_plan(p,front_result=f,manifests=m)
    scope=parts_scope(front_result=f,planner_result=p,manifests=m,upstream_status={'front':'requires_review'})
    assert scope['parts_version']=='CB Parts V3.3'
    assert scope['analysis_contract']=='CB Cycle V5'
    assert scope['understanding']==f['understanding']
    assert scope['planner']==p['plan'] and scope['component_blocks']==p['component_blocks']
    assert (f,p)==before
    scope['understanding']['summary']='Changed copy'
    assert f['understanding']['summary']=='whole'


@pytest.mark.parametrize('change',['missing_understanding','wrong_object','missing_view','foreign_component','missing_front',
    'duplicate_front','wrong_member_view','missing_support','missing_component','unmapped_block','wrong_block',
    'changed_owner','foreign_conflict','no_reason','unsupported_drop'])
def test_no_silent_scope_loss_or_reparenting(monkeypatch,change):
    _,_,m,f,p=fixture(monkeypatch)
    if change=='missing_understanding':del f['understanding']
    if change=='wrong_object':f['understanding']['input_id']='other'
    if change=='missing_view':f['understanding']['views']=[]
    if change=='foreign_component':f['front_components'][0]['component_id']='other'
    if change=='missing_front':f['front_components'].pop()
    if change=='duplicate_front':f['front_components'][1]=f['front_components'][0]
    if change=='wrong_member_view':f['understanding']['components'][0]['view_ids']=['other']
    if change=='missing_support':f['support_components']=[]
    if change=='missing_component':p['component_blocks'].pop()
    if change=='unmapped_block':p['component_blocks'][1]['block_ids']=['B01']
    if change=='wrong_block':p['component_blocks'][1]['block_ids']=['other']
    if change=='changed_owner':p['component_blocks'][0]['block_ids']=['B02'];p['component_blocks'][1]['block_ids']=['B01']
    if change=='foreign_conflict':p['interpretation_conflicts']=[dict(component_id='other',view_ids=['p1-view-001'],reason='Conflict.')]
    if change=='no_reason':p['interpretation_conflicts']=[dict(component_id='c',view_ids=['p1-view-001'],reason='')]
    if change=='unsupported_drop':p['component_blocks'][1]['block_ids']=[]
    with pytest.raises(ValueError):validate_plan(p,front_result=f,manifests=m)


def test_conflict_visible_and_stops_calculate(monkeypatch):
    _,_,m,f,p=fixture(monkeypatch)
    p['interpretation_conflicts']=[dict(component_id='fixed',view_ids=['p1-view-001'],reason='Screen may be another depiction.')]
    p['plan']['blocks'].pop();p['component_blocks'][1]['block_ids']=[]
    assert validate_plan(p,front_result=f,manifests=m)==p
    with pytest.raises(ValueError,match='review before Calculate'):
        parts_scope(front_result=f,planner_result=p,manifests=m,upstream_status={})


def test_two_explicit_calls_keep_evidence_and_raw_no_hidden_understanding_call(monkeypatch):
    row,pages,m,f,p=fixture(monkeypatch);calls=[];records=[]
    content,_=existing.prepare_content([row],pages)
    def provider(*args,**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason='end_turn',content=[SimpleNamespace(type='text',text=json.dumps(f if len(calls)==1 else p))])
    monkeypatch.setattr(existing,'_create_message_with_hard_timeout',provider)
    record=lambda stage,*args:records.append(stage)
    first=agent.run_front_count(inputs=[row],page_bytes=pages,record=record)
    assert len(calls)==1 and first['front_count']==f
    second=agent.run_assembly_plan(inputs=[row],page_bytes=pages,front_result=f,front_status=first['status'],record=record)
    assert len(calls)==2 and second['assembly_plan']==p
    assert calls[0]['messages'][0]['content']==content
    assert calls[1]['messages'][0]['content'][:-1]==content
    assert json.loads(calls[1]['messages'][0]['content'][-1]['text'])['saved_interpretation']==f
    assert records==['front_request','front_count','planner_request','assembly_plan']
    assert all(c['model']=='claude-haiku-5-5' and c['thinking']=={'type':'disabled'} for c in calls)
    assert existing.CB_RULEBOOK['front']['name']=='CB Front V2' and existing.PLANNER_PROMPT_VERSION=='CB Planner V4'


def test_bad_understanding_stops_planner_before_provider(monkeypatch):
    row,pages,m,f,p=fixture(monkeypatch);f['front_components']=[]
    calls=[];monkeypatch.setattr(existing,'_create_message_with_hard_timeout',lambda *a,**kw:calls.append(kw))
    with pytest.raises(ValueError):agent.run_assembly_plan(inputs=[row],page_bytes=pages,front_result=f,front_status='failed')
    assert not calls


@pytest.mark.parametrize('bad',['incomplete','schema'])
def test_raw_captured_before_rejection(monkeypatch,bad):
    row,pages,m,f,p=fixture(monkeypatch);records=[]
    monkeypatch.setattr(existing,'_create_message_with_hard_timeout',lambda *a,**kw:SimpleNamespace(
        stop_reason='max_tokens' if bad=='incomplete' else 'end_turn',content=[SimpleNamespace(type='text',text='{}')]))
    with pytest.raises(ValueError):agent.run_front_count(inputs=[row],page_bytes=pages,record=lambda stage,*a:records.append(stage))
    assert records==['front_request','front_count']


def test_calculate_consumes_same_interpretation_and_rejects_regrouping(monkeypatch):
    import agents.estimation_assembly_bom_agent as calc
    from use_cases.estimation_dimension_graph import build_dimension_graph
    row,pages,m,f,p=fixture(monkeypatch)
    scope=parts_scope(front_result=f,planner_result=p,manifests=m,upstream_status={'front':'requires_review'})
    calls=[]
    monkeypatch.setattr(calc,'get_anthropic_client',lambda:SimpleNamespace(with_options=lambda **kw:object()))
    monkeypatch.setattr(calc,'_create_message_with_hard_timeout',lambda *a,**kw:calls.append(kw) or SimpleNamespace(
        stop_reason='end_turn',content=[SimpleNamespace(type='text',text='{}')]))
    kwargs=dict(input_row=row,evidence_page_bytes_by_ref=pages,dimension_graph=build_dimension_graph(input_row=row),
        dimension_scale_gate={},allowed_material_families=['ldsp'],cb_parts_scope=scope)
    with pytest.raises(ValueError):calc.run_estimation_assembly_bom_agent(**kwargs)
    assert len(calls)==1
    context=json.loads(calls[0]['messages'][0]['content'][-1]['text'])['calculation_scope']
    assert context['understanding']==f['understanding'] and context['component_blocks']==p['component_blocks']
    assert 'do not restart recognition or regroup' in calls[0]['system']
    scope['parts_version']='CB Parts V4.1'
    with pytest.raises(ValueError,match='regrouping is not enabled'):calc.run_estimation_assembly_bom_agent(**kwargs)
    assert len(calls)==1


@pytest.mark.parametrize('change',[None,'evidence','context','raw','version'])
def test_saved_v5_scope_loader_checks_exact_chain(monkeypatch,tmp_path,change):
    from tools.probe_cb_parts import load_v5_scope
    row,pages,m,f,p=fixture(monkeypatch)
    source=dict(inputs=[row],source_pages_base64={k:base64.b64encode(v).decode() for k,v in pages.items()},status='interpretation_requires_review')
    def record(stage,version,raw):
        text=json.dumps(raw)
        return dict(stage=stage,prompt_version=version,response_text=text,response=dict(stop_reason='end_turn',content=[dict(type='text',text=text)]))
    fr=record('front_count',agent.FRONT_VERSION,f);pr=record('assembly_plan',agent.PLANNER_VERSION,p)
    pr['request']=dict(messages=[dict(content=[dict(type='text',text=json.dumps(dict(saved_front_status=source['status'],saved_interpretation=f)))])])
    a={**deepcopy(source),'provider_responses':[fr]};b={**deepcopy(source),'provider_responses':[pr]}
    if change=='evidence':b['inputs'][0]['input_id']='other'
    if change=='context':pr['request']['messages'][0]['content'][0]['text']='{}'
    if change=='raw':fr['response_text']='{}'
    if change=='version':fr['prompt_version']='old'
    fp,pp=tmp_path/'front.json',tmp_path/'planner.json';fp.write_text(json.dumps(a));pp.write_text(json.dumps(b))
    if change:
        with pytest.raises(ValueError):load_v5_scope(fp,pp)
    else:
        prior,scope=load_v5_scope(fp,pp)
        assert prior==b and scope['understanding']==f['understanding'] and scope['planner']==p['plan']


def test_first_live_understanding_failure_is_preserved_not_repaired():
    path=Path(__file__).resolve().parents[1]/'notes/evidence/cb-cycle-v5-2026-11-06/adda-object-001-trial.json'
    r=json.loads(path.read_text())
    assert r['status']=='failed' and not r['accepted'] and not r['production_promoted']
    assert r['provider_calls']==1 and r['planner_calls']==r['calculate_calls']==0
    assert r['source_evidence_unchanged'] and r['image_count']==4
    assert r['prompt_sha256']==sha256(agent.prompt('front').encode()).hexdigest()
    raw=existing._json_object(r['raw_response_text'])
    assert 'central glazed display run' in raw['understanding']['summary']
    assert raw['front']['count']==3 and 'front_groups' not in raw['front']
    with pytest.raises(ValueError,match='invalid front-count fields'):
        existing.validate_front_count(raw['front'],{v['view_id'] for v in r['source_preflight']['views']},require_annotations=True,require_supports=True)


@pytest.mark.parametrize('index',[0,1])
def test_simple_file_live_failures_preserve_missing_front_contract(index):
    path=Path(__file__).resolve().parents[1]/'notes/evidence/cb-cycle-v5-2026-11-06/simple-object-trials.json'
    r=json.loads(path.read_text())['trials'][index]
    assert r['status']=='failed' and not r['accepted'] and not r['production_promoted']
    assert r['provider_calls']==1 and r['planner_calls']==r['calculate_calls']==0
    assert r['source_evidence_unchanged'] and r['request_evidence_matches_preparation']
    assert r['stop_reason']=='end_turn'
    assert r['prompt_sha256']==sha256(agent.prompt('front').encode()).hexdigest()
    raw=existing._json_object(r['raw_response_text'])
    if r['file']=='lev1':
        assert raw['front']['drawers']['count']==3
        assert len(raw['front_components'])==3
    else:
        assert raw['front']['groups']==[]
        assert all(v is None for v in raw['front']['totals'].values())
    assert 'front_groups' not in raw['front']
    with pytest.raises(ValueError,match='invalid front-count fields'):
        existing.validate_front_count(raw['front'],{v['id'] for v in raw['understanding']['views']},require_annotations=True,require_supports=True)
