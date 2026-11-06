from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents import estimation_cb_cycle_v5_agent as agent
from agents import estimation_understanding_agent as existing
from tests.test_estimation_module_understanding import setup


def test_exact_standalone_prompt_one_call_unchanged_evidence_and_raw(monkeypatch, tmp_path):
    row, pages, _ = setup(monkeypatch)
    before = deepcopy(row)
    content, _ = existing.prepare_content([row], pages)
    raw = 'name:\nExample\ndescription:\nA cabinet.\nmaterials:\nLDSP 17 mm (default).\nassumptions:\n<script>Default board.</script>'
    calls, records, options = [], [], []
    monkeypatch.setattr(existing, 'get_anthropic_client', lambda: SimpleNamespace(
        with_options=lambda **kw: options.append(kw) or object()))
    monkeypatch.setattr(existing, '_create_message_with_hard_timeout', lambda *a, **kw:
        calls.append(kw) or SimpleNamespace(stop_reason='end_turn', content=[SimpleNamespace(type='text', text=raw)]))
    result = agent.run_understanding_v1(inputs=[row], page_bytes=pages,
        record=lambda stage, request, response: records.append(stage))
    assert row == before and len(calls) == 1
    request = calls[0]
    expected = (existing.PROMPT_PATH.parent / 'understanding_v1.md').read_text().strip()
    assert request['system'] == expected and expected.startswith('UNDERSTANDING V1\n')
    assert 'front_components' not in request['system'] and 'Replace placeholders' not in request['system']
    assert request['messages'] == [dict(role='user', content=content)]
    assert request['model'] == 'claude-haiku-5-5'
    assert request['thinking'] == dict(type='disabled') and request['output_config'] == dict(effort='low')
    assert request['max_tokens'] == 14000 and options == [dict(timeout=120, max_retries=0)]
    assert records == ['understanding_request', 'understanding']
    assert result['response_text'] == raw
    assert result['prompt_sha256'] == sha256(expected.encode()).hexdigest()
    assert result['status'] == 'understanding_text_requires_review_not_estimate'
    report = tmp_path / 'result.html'
    existing.export_report(dict(status=result['status'], understanding=result,
        provider_responses=[dict(stage='understanding', response_text=raw)]), report)
    html = report.read_text()
    assert 'incomplete response' not in html and '&lt;script&gt;' in html
    assert '<script>' not in html


@pytest.mark.parametrize('stop,text', [('max_tokens', 'partial'), ('end_turn', '')])
def test_failed_reply_recorded_before_rejection_no_retry(monkeypatch, stop, text):
    row, pages, _ = setup(monkeypatch)
    calls, records = [], []
    monkeypatch.setattr(existing, '_create_message_with_hard_timeout', lambda *a, **kw:
        calls.append(kw) or SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type='text', text=text)]))
    with pytest.raises(ValueError if stop == 'max_tokens' else RuntimeError):
        agent.run_understanding_v1(inputs=[row], page_bytes=pages,
            record=lambda stage, *a: records.append(stage))
    assert len(calls) == 1 and records == ['understanding_request', 'understanding']


def test_one_object_required_before_provider(monkeypatch):
    row, pages, calls = setup(monkeypatch)
    with pytest.raises(ValueError, match='exactly one'):
        agent.run_understanding_v1(inputs=[row, deepcopy(row)], page_bytes=pages)
    assert not calls


def test_live_trials_preserve_errors_without_claiming_semantic_acceptance():
    import json
    path = Path(__file__).parents[1] / 'notes/evidence/understanding-v1-2026-11-06/simple-object-trials.json'
    evidence = json.loads(path.read_text())
    assert not evidence['accepted'] and not evidence['production_promoted']
    assert len(evidence['trials']) == 2
    for trial in evidence['trials']:
        assert trial['prompt_sha256'] == sha256(agent.prompt('understanding').encode()).hexdigest()
        assert trial['changed_request_fields_vs_cycle_v5'] == ['system']
        assert trial['provider_calls'] == 1
        assert trial['front_calls'] == trial['planner_calls'] == trial['calculate_calls'] == 0
        assert trial['stop_reason'] == 'end_turn' and trial['semantic_status'] == 'not_accepted'
    raw = evidence['trials'][0]['raw_response_text']
    assert 'Upholstered-back' in raw and 'single black round leg' in raw and '265 mm high' in raw


@pytest.mark.parametrize('extra', [[], ['--execute', '--cycle-v5'], ['--execute', '--count-fronts'],
    ['--execute', '--front-supports'], ['--execute', '--front-witness', 'unused']])
def test_cli_no_implicit_paid_call_or_combined_mode(monkeypatch, extra):
    from tools.probe_v62_module_call import main
    monkeypatch.setattr('sys.argv', ['probe', '--understanding-v1', '--replay', 'unused',
        '--output', 'unused', *extra])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
