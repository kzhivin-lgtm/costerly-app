from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace

from PIL import Image
import pytest
import agents.estimation_understanding_agent as agent


def fixture():
    b = BytesIO(); Image.new('RGB', (100, 100), 'white').save(b, format='WEBP')
    row = {'input_id': 'i', 'input_payload': {'contract_version': 'estimation_input_v4', 'company_id': 'c', 'run_id': 'r',
        'object': {'object_id': 'o', 'object_name': 'hint', 'evidence_pages': [{'page_number': 1, 'regions': []}]},
        'evidence': {'artifacts': [{'artifact_kind': 'page', 'page_number': 1, 'storage_ref': 'page'}]},
        'document_context': {'ocr_blocks': [{'block_ref': 'legend', 'text': 'VN11 oak'}]}}}
    obj = {'input_id': 'i', 'summary': 'whole', 'construction_summary': 'assumed board',
        'views': [{'id': v, 'page_number': 1, 'location': v, 'observation': 'feature'} for v in ['a', 'b']],
        'components': [{'id': 'c', 'name': 'part', 'function': 'attached', 'quantity': 1, 'operation': 'fixed',
            'material_hypothesis': 'assumed board', 'basis': 'visual_interpretation', 'view_ids': ['a','b']}],
        'cross_view_links': [{'component_id': 'c', 'view_ids': ['a','b'], 'correspondence': 'same corner'}],
        'uncertainties': ['finish unknown']}
    return row, {'page': b.getvalue()}, {'objects': [obj]}


def test_content_keeps_whole_source_and_legend_and_does_not_mutate():
    row, pages, _ = fixture(); before = deepcopy(row)
    content, manifests = agent.prepare_content([row], pages)
    assert row == before and 'object_name' not in manifests[0]
    assert 'hint' not in content[-1]['text']
    assert sum(c['type']=='image' for c in content) == 1
    assert 'VN11 oak' in content[-1]['text']
    assert 'dimension_context' not in content[-1]['text']


def test_one_haiku_request_and_explicit_review_status(monkeypatch):
    row, pages, parsed = fixture(); calls = []
    monkeypatch.setattr(agent, 'get_anthropic_client', lambda: SimpleNamespace(with_options=lambda **kw: object()))
    response = SimpleNamespace(content=[SimpleNamespace(type='text', text=json.dumps(parsed))])
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', lambda *a, **kw: calls.append(kw) or response)
    result = agent.run_understanding(inputs=[row], page_bytes=pages)
    assert result['status'] == 'interpretation_requires_review'
    assert len(calls) == 1 and calls[0]['model'] == 'claude-haiku-4-5-20251001'


@pytest.mark.parametrize('bad', ['foreign_object','missing_object','duplicate_object','foreign_view','bad_operation','bad_quantity','false_pair','foreign_component'])
def test_invalid_references_are_not_semantic_success(bad):
    row, pages, parsed = fixture(); _, manifests = agent.prepare_content([row], pages)
    obj = parsed['objects'][0]
    if bad == 'foreign_object': obj['input_id'] = 'foreign'
    elif bad == 'missing_object': parsed['objects'] = []
    elif bad == 'duplicate_object': parsed['objects'].append(deepcopy(obj))
    elif bad == 'foreign_view': obj['components'][0]['view_ids'] = ['foreign']
    elif bad == 'bad_operation': obj['components'][0]['operation'] = 'guess'
    elif bad == 'bad_quantity': obj['components'][0]['quantity'] = True
    elif bad == 'false_pair': obj['cross_view_links'][0]['view_ids'] = ['a','a']
    else: obj['cross_view_links'][0]['component_id'] = 'foreign'
    with pytest.raises(ValueError): agent.validate_understanding(parsed, manifests)


def test_known_views_cannot_be_omitted_or_reassigned():
    row, pages, parsed = fixture(); _, manifests = agent.prepare_content([row], pages)
    manifests[0]['known_views'] = [{'view_id': v,'page_number':1} for v in ['a','b','c']]
    with pytest.raises(ValueError, match='omitted source view'): agent.validate_understanding(parsed, manifests)
    manifests[0]['known_views'] = [{'view_id':'a','page_number':2},{'view_id':'b','page_number':1}]
    with pytest.raises(ValueError, match='changed source view'): agent.validate_understanding(parsed, manifests)


def test_cross_object_reference_and_mixed_run_are_rejected():
    row, pages, parsed = fixture(); other = deepcopy(row); other['input_id'] = 'j'
    other['input_payload']['run_id'] = 'other'
    with pytest.raises(ValueError, match='one company'): agent.prepare_content([row,other], pages)
    with pytest.raises(ValueError, match='unique'): agent.prepare_content([row,row], pages)


def test_local_report_escapes_model_html():
    _, _, parsed = fixture(); parsed['objects'][0]['summary'] = '<script>bad()</script>'
    html = agent.report_html(parsed)
    assert '<script>' not in html and '&lt;script&gt;' in html


def test_first_cycle_cli_does_not_reach_calculation_or_database(monkeypatch, tmp_path):
    import base64
    from tools import replay_estimation_v6 as replay
    row, pages, parsed = fixture()
    prior = tmp_path / 'prior.json'
    prior.write_text(json.dumps({'inputs':[row], 'source_pages_base64':{k:base64.b64encode(v).decode() for k,v in pages.items()}}))
    out = tmp_path / 'out.json'
    monkeypatch.setattr('sys.argv',['replay','i','--replay',str(prior),'--understanding-only','--output',str(out)])
    monkeypatch.setattr(replay,'get_supabase_client',lambda:pytest.fail('database'))
    monkeypatch.setattr(replay,'run_estimation_assembly_bom_agent',lambda **kw:pytest.fail('Calculation'))
    monkeypatch.setattr(agent,'run_understanding',lambda **kw:parsed)
    replay.main()
    assert json.loads(out.read_text())['version'] == 'v6.2'
    assert out.with_suffix('.html').exists()


def test_failed_response_report_is_readable_and_explicit(tmp_path):
    _, _, parsed = fixture()
    w = {'status':'failed','error':'foreign input','evidence_origin':'<script>',
         'provider_responses':[{'stage':'understanding','response_text':json.dumps(parsed)}]}
    path = tmp_path / 'report.html'; agent.export_report(w,path)
    text = path.read_text()
    assert 'whole' in text and 'foreign input' in text and '<script>' not in text
    w['provider_responses'][0]['response_text'] = '<script>malformed'
    agent.export_report(w,path)
    assert '&lt;script&gt;malformed' in path.read_text()


def test_two_objects_are_one_request_with_separate_membership(monkeypatch):
    row, pages, parsed = fixture(); other = deepcopy(row); other['input_id'] = 'j'
    other['input_payload']['object']['object_id'] = 'other'
    second = deepcopy(parsed['objects'][0]); second['input_id'] = 'j'
    parsed['objects'].append(second)
    monkeypatch.setattr(agent,'get_anthropic_client',lambda:SimpleNamespace(with_options=lambda **kw:object()))
    calls=[]
    response=SimpleNamespace(content=[SimpleNamespace(type='text',text=json.dumps(parsed))])
    monkeypatch.setattr(agent,'_create_message_with_hard_timeout',lambda *a,**kw:calls.append(kw) or response)
    result=agent.run_understanding(inputs=[row,other],page_bytes=pages)
    assert len(result['objects'])==2 and len(calls)==1
    assert sum(c['type']=='image' for c in calls[0]['messages'][0]['content'])==1
