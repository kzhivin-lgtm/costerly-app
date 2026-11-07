from copy import deepcopy
import json

import pytest

from agents import estimation_analyze_v7_2_agent as agent
from tests.test_estimation_analyze_v7_2 import setup
from tools.probe_estimation_v7_2_front_landmarks import landmark_request, validate_landmark_result
from tools.probe_estimation_v7_2_thinking import front_pixels_request
from use_cases.estimation_detection_context_v7 import digest


def test_checkpoint_request_preserves_evidence_settings_and_other_sections(monkeypatch):
    monkeypatch.setattr('tools.probe_estimation_v7_2_thinking.front_crop_sizes',
        lambda _: {'view-001': (750, 592)})
    saved = dict(version=agent.VERSION, provider_response=dict(stop_reason='end_turn'), stop_reason='end_turn',
        detection_context=dict(contract_version='estimation_detection_context_v7_2'),
        provider_request=dict(model='saved-model', max_tokens=14000, thinking={'type': 'disabled'},
            output_config={'effort': 'medium'}, system=agent.prompt(),
            messages=[dict(role='user', content=['unchanged image/OCR/Detection'])]))
    saved['provider_request'] = front_pixels_request(saved)
    saved['request_sha256'] = digest(saved['provider_request'])
    before = deepcopy(saved)
    request = landmark_request(saved)
    assert saved == before and {**request, 'system': before['provider_request']['system']} == before['provider_request']
    old, new = [json.loads(r['system'].split('SINGLE AUTHORITATIVE RESPONSE TEMPLATE\n')[1])['objects'][0]
                for r in (saved['provider_request'], request)]
    assert new['understanding'] == old['understanding'] and new['planner'] == old['planner']
    assert set(new['islands'][0]) == {'island_id', 'projection', 'elevation_index', 'content_role'}
    assert set(new['front']['front_groups'][0]['fronts'][0]) == {'id', 'view_id', 'landmark', 'bbox_px'}
    assert 'including estimated, the number of individual front entries' in request['system']


@pytest.fixture
def unlocalized():
    row, ctx, result = setup()
    obj = result['objects'][0]
    obj['islands'][0].pop('observation')
    obj['front']['front_groups'] = [dict(location='base', type='drawer', count=1,
        count_basis='estimated', view_ids=['view-001'], uncertainty='boundary not resolved',
        fronts=[dict(id='F01', view_id='view-001', landmark='leftmost drawer under top', bbox_px=None)])]
    obj['front']['totals'].update(drawers=1, total_fronts=1)
    obj['planner']['blocks'][0]['front_ids'] = ['F01']
    return result, dict(detection_context=ctx, inputs=[row], front_crop_sizes_px={'view-001': (750, 592)})


def test_named_unlocalized_face_remains_unlocalized(unlocalized):
    raw, witness = unlocalized
    before = deepcopy(raw)
    result = validate_landmark_result(raw, witness)
    assert raw == before
    entry = result['objects'][0]['front']['front_groups'][0]['fronts'][0]
    assert entry['bbox_1000'] is None and entry['landmark'] == 'leftmost drawer under top'


@pytest.mark.parametrize('problem', ['comment', 'landmark', 'view', 'count'])
def test_diagnostic_does_not_accept_extra_comment_or_incomplete_front_entry(unlocalized, problem):
    raw, witness = unlocalized
    obj = raw['objects'][0]
    group = obj['front']['front_groups'][0]
    if problem == 'comment':
        obj['islands'][0]['observation'] = 'unwanted comment'
    elif problem == 'landmark':
        group['fronts'][0]['landmark'] = ''
    elif problem == 'view':
        group['fronts'][0]['view_id'] = 'other-object'
    else:
        group['count'] = 2
        obj['front']['totals'].update(drawers=2, total_fronts=2)
    with pytest.raises(ValueError):
        validate_landmark_result(raw, witness)
