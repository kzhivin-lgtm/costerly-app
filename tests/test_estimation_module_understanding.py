import json
import re
from types import SimpleNamespace

import pytest
from tests.test_estimation_understanding import fixture
import agents.estimation_understanding_agent as agent


def island(vid='p1-view-001'):
    return {'view_id': vid, 'type': 'Front elevation'}


def setup(monkeypatch, *, tool=True, foreign=False):
    row, pages, parsed = fixture()
    row['input_payload']['object']['evidence_pages'][0]['regions'] = [
        {'top_left_x': 0, 'top_left_y': 0, 'bottom_right_x': 50, 'bottom_right_y': 50}]
    obj = parsed['objects'][0]
    obj['views'] = [{'id': 'p1-view-001', 'page_number': 1, 'location': 'left', 'observation': 'cabinet'}]
    obj['components'][0]['view_ids'] = ['p1-view-001']
    obj['cross_view_links'] = []
    arg = {'input_id': 'i', 'whole_object': 'шкаф', 'applicable_assemblies': ['корпус'],
        'excluded_assemblies': [], 'view_ids': ['foreign' if foreign else 'p1-view-001'],
        'island_types': [island()]}
    first = SimpleNamespace(stop_reason='tool_use' if tool else 'end_turn', content=[
        SimpleNamespace(type='tool_use', id='tool1', name='apply_cabinet_block', input=arg)
        if tool else SimpleNamespace(type='text', text='No applicable module')])
    final = SimpleNamespace(stop_reason='end_turn', content=[SimpleNamespace(type='text', text=json.dumps(parsed))])
    calls = []
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return first if len(calls) == 1 else final
    monkeypatch.setattr(agent, 'get_anthropic_client', lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', provider)
    return row, pages, calls


def test_module_is_selected_before_rules_are_delivered(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    records = []
    result = agent.run_understanding_with_modules(inputs=[row], page_bytes=pages,
        record=lambda stage, request, response: records.append(stage))
    assert len(calls) == 2 and records == ['module_selection', 'understanding']
    assert all(c['model'] == agent.MODEL for c in calls)
    assert 'Cabinet Block operability policy' not in json.dumps(calls[0])
    assert 'Cabinet Block operability policy' in json.dumps(calls[1])
    assert calls[0]['tool_choice'] == {'type': 'auto'}
    assert calls[1]['tool_choice'] == {'type': 'none'}
    assert calls[1]['max_tokens'] == 6000
    assert calls[0]['messages'][0] == calls[1]['messages'][0]
    assert calls[1]['messages'][2]['content'][0]['tool_use_id'] == 'tool1'
    assert result['module_applications'][0]['whole_object'] == 'шкаф'
    assert 'Choose exactly one' in calls[0]['system']
    assert all(c['model'] == 'claude-haiku-5-5' and 'temperature' not in c for c in calls)
    assert all(c['output_config'] == {'effort': 'low'} for c in calls)
    assert not re.search('[А-Яа-яЁё]', calls[0]['system'])
    assert 'All generated text must be English' in calls[0]['system']
    fields = calls[0]['tools'][0]['input_schema']['properties']['island_types']['items']['properties']
    assert set(fields) == {'view_id', 'type'}
    scope = json.loads(calls[1]['messages'][2]['content'][0]['content'])['scope']
    assert scope['island_types'] == result['module_applications'][0]['island_types'] == [island()]
    final_contract = calls[1]['messages'][2]['content'][1]['text']
    assert 'All human-readable text must be English' in final_contract
    assert not re.search('[А-Яа-яЁё]', final_contract)
    html = agent.report_html(result)
    assert 'Island types' in html and 'Front elevation' in html


@pytest.mark.parametrize('tool,foreign,error', [
    (False, False, 'no applicable'), (True, True, 'foreign views'),
])
def test_invalid_selection_never_runs_second_call(monkeypatch, tool, foreign, error):
    row, pages, calls = setup(monkeypatch, tool=tool, foreign=foreign)
    with pytest.raises(ValueError, match=error):
        agent.run_understanding_with_modules(inputs=[row], page_bytes=pages)
    assert len(calls) == 1


@pytest.mark.parametrize('case,error', [
    ('missing', 'omitted island'), ('duplicate', 'duplicate island'),
    ('foreign', 'foreign/duplicate'), ('extra_field', 'type fields'),
    ('invalid_enum', 'classification'), ('non_string_type', 'classification'),
])
def test_island_types_reject_invalid_contract(case, error):
    entries = [island('a'), island('b')]
    if case == 'missing': entries.pop()
    if case == 'duplicate': entries[1]['view_id'] = 'a'
    if case == 'foreign': entries[1]['view_id'] = 'c'
    if case == 'extra_field': entries[0]['correspondences'] = []
    if case == 'invalid_enum': entries[0]['type'] = 'Top view|Side view'
    if case == 'non_string_type': entries[0]['type'] = []
    with pytest.raises(ValueError, match=error):
        agent.validate_island_types(entries, {'a', 'b'})


def test_island_types_allow_undetermined_without_invented_correspondences():
    entries = [island('a'), island('b')]
    entries[1]['type'] = 'Undetermined'
    assert agent.validate_island_types(entries, {'a', 'b'}) == entries


def test_invalid_map_prevents_policy_continuation(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    def reject(*args):
        raise ValueError('omitted island')
    monkeypatch.setattr(agent, 'validate_island_types', reject)
    with pytest.raises(ValueError, match='omitted island'):
        agent.run_understanding_with_modules(inputs=[row], page_bytes=pages)
    assert len(calls) == 1


def test_no_detection_islands_stops_before_provider(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    row['input_payload']['object']['evidence_pages'][0]['regions'] = []
    with pytest.raises(ValueError, match='Detection-owned islands'):
        agent.run_understanding_with_modules(inputs=[row], page_bytes=pages)
    assert calls == []


def test_map_report_escapes_provider_text():
    item = island()
    item['type'] = '<script>alert(1)</script>'
    html = agent.report_html({'objects': [], 'module_applications': [
        {'input_id': '<unsafe>', 'island_types': [item]}]})
    assert '<script>' not in html and '&lt;script&gt;' in html and '&lt;unsafe&gt;' in html


@pytest.mark.parametrize('foreign', [False, True])
def test_isolated_map_uses_same_evidence_and_one_call_without_module(monkeypatch, foreign):
    row, pages, _ = setup(monkeypatch)
    expected_content, _ = agent.prepare_content([row], pages)
    label = 'foreign' if foreign else 'p1-view-001'
    calls, records = [], []
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason='end_turn', content=[
            SimpleNamespace(type='text', text=f'{label}: Front elevation')])
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', provider)
    if foreign:
        with pytest.raises(ValueError, match='foreign/duplicate'):
            agent.run_island_types_only(inputs=[row], page_bytes=pages)
    else:
        result = agent.run_island_types_only(inputs=[row], page_bytes=pages,
            record=lambda stage, request, response: records.append(stage))
        assert result['classifications'] == [{'input_id': 'i', 'island_types': [island()]}] and not result['objects']
        assert records == ['island_types']
        assert 'Island types' in agent.report_html(result)
    assert len(calls) == 1 and 'tools' not in calls[0]
    assert calls[0]['messages'][0]['content'] == expected_content
    assert not re.search('[А-Яа-яЁё]', calls[0]['system'])


@pytest.mark.parametrize('answer', [
    'island ID: p1-view-001: Front elevation',
    'p1-view-001: Front elevation\np1-view-001: Front elevation',
    'Here is the answer:\np1-view-001: Front elevation',
    '',
])
def test_plain_classification_rejects_prefixes_duplicates_and_essays(monkeypatch, answer):
    row, pages, _ = setup(monkeypatch)
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout',
        lambda *a, **kw: SimpleNamespace(stop_reason='end_turn', content=[
            SimpleNamespace(type='text', text=answer)]))
    with pytest.raises(RuntimeError if not answer else ValueError):
        agent.run_island_types_only(inputs=[row], page_bytes=pages)


def test_plain_classification_rejects_ambiguous_cross_object_ids_before_provider(monkeypatch):
    from copy import deepcopy
    row, pages, calls = setup(monkeypatch)
    other = deepcopy(row)
    other['input_id'] = 'j'
    other['input_payload']['object']['object_id'] = 'other'
    with pytest.raises(ValueError, match='globally unique'):
        agent.run_island_types_only(inputs=[row, other], page_bytes=pages)
    assert not calls


def test_haiku_thinking_signature_is_preserved_in_tool_continuation(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    provider = agent._create_message_with_hard_timeout
    def with_thinking(*args, **kwargs):
        response = provider(*args, **kwargs)
        if len(calls) == 1:
            response.content.insert(0, SimpleNamespace(type='thinking', thinking='', signature='opaque-test-signature'))
        return response
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', with_thinking)
    agent.run_understanding_with_modules(inputs=[row], page_bytes=pages)
    assert calls[1]['messages'][1]['content'][0] == {
        'type': 'thinking', 'thinking': '', 'signature': 'opaque-test-signature'}
