from copy import deepcopy
from hashlib import sha256
import json
import re
from types import SimpleNamespace

import pytest

import agents.estimation_understanding_agent as agent
from tests.test_estimation_module_understanding import setup


def test_front_count_prompt_revision_identity():
    # Change the revision and its fingerprint together when changing the prompt.
    expected = {'estimation_front_count_v6_2_r03':
        '81b49dc8d2dd4c33a7459d824178ea8601ba241370a401e530bed2748dab0bb0'}
    assert sha256(agent.FRONT_COUNT_PROMPT_PATH.read_text().strip().encode()).hexdigest() == expected[agent.FRONT_COUNT_PROMPT_VERSION]
    assert agent.FRONT_SUPPORTS_PROMPT_VERSION == 'estimation_front_count_v6_2_r05'
    assert sha256(agent.FRONT_SUPPORTS_PROMPT_PATH.read_text().strip().encode()).hexdigest() == 'a929fe8ce72fd7cf75c9c100f2ce48c1e1ab2a4da8cb9ce44a9ac16545e0affd'


def test_archived_r04_prompt_keeps_its_original_identity():
    archived = agent.FRONT_COUNT_PROMPT_PATH.parent / 'history' / 'estimation_front_count_v6_2_r04.md'
    assert sha256(archived.read_text().strip().encode()).hexdigest() == '52d6f563f94add159d2b9c457eedc4dd31bbe47011e293c8bf0b68e266b95a99'


def test_checkpoint_responses_preserve_success_and_failure():
    evidence = agent.FRONT_COUNT_PROMPT_PATH.parents[2] / 'notes' / 'evidence' / 'estimation-v6.2-front-count-2026-11-05'
    known = {f'p1-view-{n:03d}' for n in range(1, 5)}
    accepted = json.loads((evidence / 'r03-evidence.json').read_text())
    parsed = accepted['parsed_response']
    assert agent.validate_front_count(deepcopy(parsed), known, require_annotations=True) == parsed
    # Accepted with known visual errors, never a corrected ground-truth target.
    assert parsed['totals'] == dict(drawers=5, hinged_doors=17,
        lift_up_fronts=2, unresolved_fronts=0, total_fronts=24)
    rejected = json.loads((evidence / 'r04-evidence.json').read_text())
    assert rejected['original_status'] == 'failed'
    with pytest.raises(ValueError, match='invalid island classification'):
        agent.validate_front_count(rejected['parsed_response'], known, require_annotations=True)


def counted():
    return {
        'island_types': [{'view_id': 'p1-view-001', 'type': 'Front elevation'}],
        'front_groups': [{'location': 'Base drawer bank', 'type': 'drawer', 'count': 3,
            'count_basis': 'clear', 'view_ids': ['p1-view-001'], 'uncertainty': ''}],
        'totals': {'drawers': 3, 'hinged_doors': 0, 'lift_up_fronts': 0,
            'unresolved_fronts': 0, 'total_fronts': 3}}


def annotated():
    parsed = counted()
    parsed['front_groups'][0]['fronts'] = [
        {'id': f'F{i}', 'view_id': 'p1-view-001', 'bbox_1000': [100, 100 + i * 100, 500, 190 + i * 100]}
        for i in range(3)]
    parsed['excluded_surfaces'] = []
    return parsed


@pytest.mark.parametrize('bad', ['count', 'duplicate', 'foreign', 'reversed', 'outside', 'nan', 'boolean', 'excluded_id'])
def test_front_annotation_contract(bad):
    parsed = annotated()
    front = parsed['front_groups'][0]['fronts'][0]
    if bad == 'count': parsed['front_groups'][0]['fronts'].pop()
    if bad == 'duplicate': front['id'] = 'F1'
    if bad == 'foreign': front['view_id'] = 'other'
    if bad == 'reversed': front['bbox_1000'] = [500, 200, 100, 300]
    if bad == 'outside': front['bbox_1000'][2] = 1001
    if bad == 'nan': front['bbox_1000'][0] = float('nan')
    if bad == 'boolean': front['bbox_1000'][0] = False
    if bad == 'excluded_id': parsed['excluded_surfaces'] = [{**front, 'reason': 'fixed side'}]
    with pytest.raises(ValueError):
        agent.validate_front_count(parsed, {'p1-view-001'}, require_annotations=True)


def test_front_annotations_are_not_geometry_repaired():
    parsed = annotated()
    parsed['excluded_surfaces'] = [{'id': 'X1', 'view_id': 'p1-view-001',
        'bbox_1000': [900, 0, 999, 1000], 'reason': 'side'}]
    before = deepcopy(parsed)
    assert agent.validate_front_count(parsed, {'p1-view-001'}, require_annotations=True) == before


def test_front_count_validation_does_not_mutate_or_repair():
    parsed = counted()
    before = deepcopy(parsed)
    assert agent.validate_front_count(parsed, {'p1-view-001'}) == before
    assert parsed == before


@pytest.mark.parametrize('bad', ['sum', 'foreign', 'duplicate_ref', 'boolean',
    'fraction', 'zero_group', 'unknown_kind', 'estimated_without_reason',
    'null_clear', 'missing_island', 'extra_field', 'boolean_total'])
def test_invalid_front_contract(bad):
    parsed = counted()
    group = parsed['front_groups'][0]
    if bad == 'sum': parsed['totals']['total_fronts'] = 4
    if bad == 'foreign': group['view_ids'] = ['other']
    if bad == 'duplicate_ref': group['view_ids'] *= 2
    if bad == 'boolean': group['count'] = True
    if bad == 'fraction': group['count'] = 1.5
    if bad == 'zero_group': group['count'] = 0
    if bad == 'unknown_kind': group['type'] = 'drawer | hinged'
    if bad == 'estimated_without_reason': group['count_basis'] = 'estimated'
    if bad == 'null_clear': group['count'] = None
    if bad == 'missing_island': parsed['island_types'] = []
    if bad == 'extra_field': parsed['prices'] = []
    if bad == 'boolean_total': parsed['totals']['hinged_doors'] = False
    before = deepcopy(parsed)
    with pytest.raises(ValueError):
        agent.validate_front_count(parsed, {'p1-view-001'})
    assert parsed == before


def test_null_and_absence_are_distinct_and_totals_propagate_unknown():
    parsed = counted()
    parsed['front_groups'][0].update(count=None, count_basis='undetermined',
        uncertainty='Front boundaries are hidden')
    parsed['totals'].update(drawers=None, total_fronts=None)
    assert agent.validate_front_count(parsed, {'p1-view-001'})['totals']['hinged_doors'] == 0
    parsed['totals']['total_fronts'] = 0
    with pytest.raises(ValueError, match='totals'):
        agent.validate_front_count(parsed, {'p1-view-001'})


@pytest.mark.parametrize('include_supports', [False, True])
def test_one_combined_call_with_unchanged_evidence_and_english_prompt(monkeypatch, tmp_path, include_supports):
    row, pages, _ = setup(monkeypatch)
    content, _ = agent.prepare_content([row], pages)
    calls, records = [], []
    parsed = annotated()
    if include_supports:
        parsed['tabletop_supports'] = []
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason='end_turn', content=[
            SimpleNamespace(type='text', text=json.dumps(parsed))])
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', provider)
    result = agent.run_front_count(inputs=[row], page_bytes=pages,
        record=lambda stage, request, response: records.append(stage), include_supports=include_supports)
    assert result['front_count'] == parsed
    assert result['prompt_version'] == (agent.FRONT_SUPPORTS_PROMPT_VERSION if include_supports else agent.FRONT_COUNT_PROMPT_VERSION)
    assert result['prompt_sha256'] == sha256(calls[0]['system'].encode()).hexdigest()
    assert len(calls) == 1 and records == ['front_count']
    assert calls[0]['messages'] == [{'role': 'user', 'content': content}]
    assert calls[0]['model'] == 'claude-haiku-5-5'
    assert calls[0]['output_config'] == {'effort': 'low'}
    assert calls[0]['max_tokens'] == 10000
    assert 'tools' not in calls[0] and 'temperature' not in calls[0]
    assert not re.search('[А-Яа-яЁё]', calls[0]['system'])
    assert 'Count individual fronts, not cabinets or drawer banks.' in calls[0]['system']
    assert 'A rectangle in an elevation is only a candidate front.' not in calls[0]['system']
    assert 'a door closes an access opening; a side wall forms the fixed boundary' in calls[0]['system']
    assert 'unless the source explicitly identifies or' in calls[0]['system']
    assert 'not\n  from perspective foreshortening' in calls[0]['system']
    out = tmp_path / 'report.html'
    agent.export_report({'understanding': result, 'provider_responses': [
        {'stage': 'front_count', 'response_text': json.dumps(parsed)}]}, out)
    assert 'incomplete response' not in out.read_text()
    assert 'interpretation requires review' in out.read_text()


def test_single_object_bound_stops_before_call(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    with pytest.raises(ValueError, match='exactly one'):
        agent.run_front_count(inputs=[row, row], page_bytes=pages)
    assert not calls


def test_truncated_output_is_recorded_but_not_accepted(monkeypatch):
    row, pages, _ = setup(monkeypatch)
    records = []
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout',
        lambda *a, **kw: SimpleNamespace(stop_reason='max_tokens', content=[]))
    with pytest.raises(ValueError, match='finish normally'):
        agent.run_front_count(inputs=[row], page_bytes=pages,
            record=lambda stage, request, response: records.append(stage))
    assert records == ['front_count']
