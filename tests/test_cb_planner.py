from copy import deepcopy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

import agents.estimation_understanding_agent as agent
from tests.test_estimation_module_understanding import setup


def plan():
    return {'summary': 'Cabinet with two fronts', 'blocks': [{
        'id': 'B01', 'name': 'Shared carcass', 'contains': 'Two fronted compartments',
        'reason': 'One practical assembly; boundary assumed', 'front_ids': ['F01', 'F02'],
        'view_ids': ['p1-view-001'],
        'region': {'view_id': 'p1-view-001', 'bbox_1000': [100, 100, 800, 800]}}],
        'shared_parts': [], 'front_conflicts': [], 'uncertainties': []}


def front():
    return {'island_types': [{'view_id': 'p1-view-001', 'type': 'front_elevation'}],
        'front_groups': [{'fronts': [
            {'id': fid, 'view_id': 'p1-view-001'} for fid in ('F01', 'F02')]}]}


def test_rulebook_preserves_front_identity_and_versions_planner():
    assert agent.CB_RULEBOOK['front']['name'] == 'CB Front V1'
    assert agent.CB_RULEBOOK['front']['candidate']['name'] == 'CB Front V2'
    assert agent.CB_RULEBOOK['planner']['name'] == 'CB Planner V4'
    protected_front = agent.FRONT_COUNT_PROMPT_PATH.with_name('estimation_front_count_v6_2.md')
    assert sha256(protected_front.read_text().strip().encode()).hexdigest() == '81b49dc8d2dd4c33a7459d824178ea8601ba241370a401e530bed2748dab0bb0'
    prompt = agent.PLANNER_PROMPT_PATH.read_text()
    assert sha256(prompt.strip().encode()).hexdigest() == '3f6ae0ff17c071066ba1ea46bfcf954949c4d1cc370ab6ecad46b8767de4a749'
    assert prompt.startswith('CB Planner V4')
    assert 'Do not invent hidden partitions' in prompt
    assert 'No target block count' in prompt
    assert 'THREE front positions' in prompt
    assert 'Four is a rare exception' in prompt
    assert 'across BOTH wings together' in prompt
    assert 'a stack of drawers occupies one horizontal position' in prompt
    assert 'full-height block' in prompt
    assert 'EXACTLY ONE SECTION wide' in prompt
    assert 'Identify these columns FIRST' in prompt
    assert 'do not bridge an open workspace' in prompt
    assert 'turn a fixed side/frame into a' in prompt
    v3 = agent.PLANNER_PROMPT_PATH.with_name('cb_planner_v3.md').read_text()
    assert sha256(v3.strip().encode()).hexdigest() == '28ddc60a1e8b5c6385cb13f738cc98b40d7a9414e86b6aa43e53b685f0e6dac5'
    assert 'ALWAYS list a worktop as a separate element' in prompt
    previous = agent.PLANNER_PROMPT_PATH.with_name('cb_planner_v2.md').read_text()
    assert sha256(previous.strip().encode()).hexdigest() == 'd5e1b0de71d1053f89ba97cfeecc2352ac4ee126b54f9e8b245ce8df733c7335'


def test_planner_one_call_retains_images_and_fallible_front_without_repair(monkeypatch):
    row, pages, _ = setup(monkeypatch)
    content, _ = agent.prepare_content([row], pages)
    calls, records = [], []
    saved = front(); before = deepcopy(saved)
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason='end_turn', content=[
            SimpleNamespace(type='text', text=json.dumps(plan()))])
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', provider)
    result = agent.run_assembly_plan(inputs=[row], page_bytes=pages,
        front_result=saved, front_status='failed', record=lambda *args: records.append(args[0]))
    assert saved == before
    assert len(calls) == 1 and records == ['assembly_plan']
    request = calls[0]
    assert request['messages'][0]['content'][:-1] == content
    context = json.loads(request['messages'][0]['content'][-1]['text'])
    assert context == {'saved_front_status': 'failed', 'fallible_front_reference': saved}
    assert request['model'] == 'claude-haiku-5-5'
    assert request['max_tokens'] == 6000 and request['output_config'] == {'effort': 'low'}
    assert 'tools' not in request and 'temperature' not in request
    assert result['assembly_plan'] == plan()
    assert result['prompt_sha256'] == sha256(request['system'].encode()).hexdigest()


@pytest.mark.parametrize('bad', ['missing', 'duplicate', 'foreign', 'empty', 'box', 'nan', 'bool',
    'island', 'region', 'shared', 'self_shared', 'conflict_duplicate', 'unknown_conflict', 'extra'])
def test_planner_contract_rejects_invalid_ownership_without_repair(bad):
    p = plan(); b = p['blocks'][0]
    if bad == 'missing': b['front_ids'].pop()
    if bad == 'duplicate': p['blocks'].append({**deepcopy(b), 'id': 'B02'})
    if bad == 'foreign': b['front_ids'] = ['other']
    if bad == 'empty': p['blocks'] = []
    if bad == 'box': b['region']['bbox_1000'] = [900, 0, 100, 300]
    if bad == 'nan': b['region']['bbox_1000'][0] = float('nan')
    if bad == 'bool': b['region']['bbox_1000'][0] = True
    if bad == 'island': b['view_ids'] = ['foreign']
    if bad == 'region': b['region']['view_id'] = 'foreign'
    if bad in {'shared', 'self_shared'}:
        p['shared_parts'] = [{'id': 'S01', 'name': 'Worktop', 'block_ids': ['B01', 'B02'] if bad == 'shared' else ['B01', 'B01'],
            'view_ids': b['view_ids'], 'region': b['region']}]
    if bad in {'conflict_duplicate', 'unknown_conflict'}:
        p['front_conflicts'] = [{'front_id': 'F01' if bad == 'conflict_duplicate' else 'foreign', 'reason': 'fixed'}]
    if bad == 'extra': p['materials'] = []
    with pytest.raises(ValueError):
        agent.validate_assembly_plan(p, {'p1-view-001'}, {'F01', 'F02'})


def test_explicit_front_conflict_is_not_silently_dropped():
    p = plan(); p['blocks'][0]['front_ids'] = ['F01']
    p['front_conflicts'] = [{'front_id': 'F02', 'reason': 'Fixed outer side in overall view'}]
    before = deepcopy(p)
    assert agent.validate_assembly_plan(p, {'p1-view-001'}, {'F01', 'F02'}) == before


def test_v3_recorded_outputs_retain_partial_improvement_and_rejection():
    root = agent.PLANNER_PROMPT_PATH.parents[2] / 'notes' / 'evidence' / 'cb-planner-v3-2026-11-05'
    lev1 = json.loads((root / 'lev1-evidence.json').read_text())
    lev2 = json.loads((root / 'lev2-evidence.json').read_text())
    for witness in (lev1, lev2):
        assert witness['changed_request_fields_vs_v2'] == ['system']
        assert witness['prompt_version'] == 'CB Planner V3'
    p1 = lev1['parsed_response']
    assert len(p1['blocks']) == 3
    assert agent.validate_assembly_plan(p1, {f'p1-view-{i:03d}' for i in range(1, 7)}, {'F01', 'F02', 'F03'}) == p1
    assert lev2['original_status'] == 'failed'
    assert len(lev2['parsed_response']['blocks']) == 9
    with pytest.raises(ValueError, match='front assigned twice'):
        agent.validate_assembly_plan(lev2['parsed_response'], {f'p1-view-{i:03d}' for i in range(1, 5)},
            {f'F{i:02d}' for i in range(1, 25)})


def test_v4_recorded_output_groups_column_but_retains_semantic_limits():
    path = agent.PLANNER_PROMPT_PATH.parents[2] / 'notes' / 'evidence' / 'cb-planner-v4-2026-11-05' / 'lev2-evidence.json'
    witness = json.loads(path.read_text())
    assert witness['changed_request_fields_vs_v3'] == ['system']
    assert witness['original_status'] == 'assembly_plan_requires_review'
    p = witness['parsed_response']
    assert agent.validate_assembly_plan(p, {f'p1-view-{i:03d}' for i in range(1, 5)},
        {f'F{i:02d}' for i in range(1, 25)}) == p
    by_id = {b['id']: b for b in p['blocks']}
    assert set(by_id['B06']['front_ids']) == {'F09', 'F06', 'F07', 'F08'}
    assert len(p['blocks']) == 10 and len(p['shared_parts']) == 1
    # Record observed limitations, not desired semantics or benchmark counts.
    assert by_id['B01']['front_ids'] == ['F24']
    assert 'U-shaped' in p['summary']
    assert witness['review']['classification'] == 'partial improvement, not accepted checkpoint'


def test_v4_lev1_preserves_grouping_without_hiding_content_errors():
    path = agent.PLANNER_PROMPT_PATH.parents[2] / 'notes' / 'evidence' / 'cb-planner-v4-2026-11-05' / 'lev1-evidence.json'
    witness = json.loads(path.read_text())
    assert witness['changed_request_fields_vs_v3'] == ['system']
    assert witness['front_status'] == 'failed'  # Historical Front enums, no repair.
    assert witness['original_status'] == 'assembly_plan_requires_review'
    p = witness['parsed_response']
    assert agent.validate_assembly_plan(p, {f'p1-view-{i:03d}' for i in range(1, 7)},
        {'F01', 'F02', 'F03'}) == p
    assert len(p['blocks']) == 3 and not p['shared_parts']
    assert p['blocks'][0]['front_ids'] == ['F01', 'F02', 'F03']
    # Preserve observed errors, not desired facts or production acceptance.
    assert 'single pedestal leg' in p['summary']
    assert '158 mm' in p['blocks'][0]['reason']
    assert '75 mm' in p['blocks'][2]['contains']


def test_shared_worktop_has_two_existing_parents_and_single_record():
    p = plan(); first = p['blocks'][0]; first['front_ids'] = ['F01']
    p['blocks'].append({**deepcopy(first), 'id': 'B02', 'front_ids': ['F02']})
    p['shared_parts'] = [{'id': 'S01', 'name': 'Continuous worktop', 'block_ids': ['B01', 'B02'],
        'view_ids': first['view_ids'], 'region': first['region']}]
    assert agent.validate_assembly_plan(p, {'p1-view-001'}, {'F01', 'F02'}) == p


@pytest.mark.parametrize('bad', ['duplicate', 'foreign'])
def test_invalid_front_reference_stops_before_paid_call(monkeypatch, bad):
    row, pages, calls = setup(monkeypatch)
    f = front()
    if bad == 'duplicate': f['front_groups'][0]['fronts'][1]['id'] = 'F01'
    else: f['front_groups'][0]['fronts'][0]['view_id'] = 'other'
    with pytest.raises(ValueError):
        agent.run_assembly_plan(inputs=[row], page_bytes=pages, front_result=f, front_status='failed')
    assert calls == []


def test_truncated_response_is_recorded_but_not_accepted(monkeypatch):
    row, pages, _ = setup(monkeypatch)
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', lambda *a, **kw:
        SimpleNamespace(stop_reason='max_tokens', content=[]))
    records = []
    with pytest.raises(ValueError, match='did not finish'):
        agent.run_assembly_plan(inputs=[row], page_bytes=pages, front_result=front(), front_status='failed',
            record=lambda *args: records.append(args[0]))
    assert records == ['assembly_plan']


def test_planner_overlay_uses_saved_regions_without_editing_witness(monkeypatch, tmp_path):
    from tools.render_estimation_front_overlay import render_planner_overlays
    import base64
    row, pages, _ = setup(monkeypatch)
    # The minimal agent fixture lacks an OCR coordinate frame and intentionally
    # has no image crops. Supply the renderer's real labelled-image contract.
    image = {'type': 'image', 'source': {'data': base64.b64encode(pages['page']).decode()}}
    region = {'view_id': 'p1-view-001', 'bbox_normalized': [.1, .1, .9, .9]}
    content = [
        {'type': 'text', 'text': json.dumps({'source_evidence_ref': 'page',
            'view_regions': [region], 'displayed_image_pixels': [100, 100]})}, image,
        {'type': 'text', 'text': json.dumps({'source_evidence_ref': 'page',
            'detail_of_existing_view': region, 'generated_header_height_px': 32})}, image]
    content.append({'type': 'text', 'text': json.dumps({'fallible_front_reference': front()})})
    witness = tmp_path / 'witness.json'
    witness.write_text(json.dumps({'provider_responses': [{'stage': 'assembly_plan',
        'prompt_version': 'CB Planner V2', 'request': {'messages': [{'role': 'user', 'content': content}]},
        'response_text': json.dumps(plan())}]}))
    original = witness.read_bytes()
    result = render_planner_overlays(witness, tmp_path / 'overlay')
    from pathlib import Path
    coordinates = json.loads(Path(result['coordinates']).read_text())
    assert coordinates['model_totals'] == {'blocks': 1, 'shared_parts': 0}
    assert coordinates['annotations'][0]['bbox_1000'] == plan()['blocks'][0]['region']['bbox_1000']
    assert coordinates['annotations'][0]['kind'] == 'block'
    assert witness.read_bytes() == original
    with pytest.raises(ValueError, match='overwrite'):
        render_planner_overlays(witness, tmp_path / 'overlay')
