from hashlib import sha256
import json
from types import SimpleNamespace

import pytest
import agents.estimation_understanding_agent as agent
from tests.test_cb_front_supports import supported
from tests.test_estimation_module_understanding import setup


def test_v3_candidate_identity_and_general_lower_row_rules():
    prompt = agent.FRONT_SUPPORTS_PROMPT_PATH.with_name('cb_front_v3.md').read_text()
    assert prompt.startswith('CB Front V3')
    assert sha256(prompt.strip().encode()).hexdigest() == '2530993b653575e5445eced53b34ed6b9393eb73c30428c2bac28d641d49429b'
    assert 'Read each drawer bank from top to bottom' in prompt
    assert 'height alone does not make it a door or a plinth' in prompt
    assert 'not\nmandatory proportions or a required number of rows' in prompt
    assert 'unresolved operating front' in prompt
    assert 'excluded fixed surface with a specific visible reason' in prompt
    assert 'N68' not in prompt
    assert agent.FRONT_SUPPORTS_PROMPT_VERSION == 'estimation_front_count_v6_2_r05'
    assert sha256(agent.FRONT_SUPPORTS_PROMPT_PATH.read_text().strip().encode()).hexdigest() == 'a929fe8ce72fd7cf75c9c100f2ce48c1e1ab2a4da8cb9ce44a9ac16545e0affd'


def test_v3_process_local_probe_changes_only_system(monkeypatch):
    row, pages, _ = setup(monkeypatch)
    calls = []
    response = supported()
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason='end_turn', content=[SimpleNamespace(type='text', text=json.dumps(response))])
    monkeypatch.setattr(agent, '_create_message_with_hard_timeout', provider)
    agent.run_front_count(inputs=[row], page_bytes=pages)
    monkeypatch.setattr(agent, 'FRONT_SUPPORTS_PROMPT_PATH', agent.FRONT_SUPPORTS_PROMPT_PATH.with_name('cb_front_v3.md'))
    monkeypatch.setattr(agent, 'FRONT_SUPPORTS_PROMPT_VERSION', 'CB Front V3')
    result = agent.run_front_count(inputs=[row], page_bytes=pages)
    assert len(calls) == 2
    old, new = [dict(c) for c in calls]
    assert old.pop('system') != new.pop('system')
    assert old == new
    assert result['prompt_version'] == 'CB Front V3'


def test_n68_recorded_v3_improvement_does_not_hide_failure():
    root = agent.FRONT_SUPPORTS_PROMPT_PATH.parents[2]
    saved = json.loads((root / 'notes/evidence/hsl07-v62-2026-11-06/n68-front-v3-planner-v7.json').read_text())
    front = saved['stages']['front']
    assert front['status'] == 'failed'
    parsed = front['parsed_response']
    assert parsed['totals']['drawers'] == 6
    assert parsed['totals']['hinged_doors'] == 7
    assert saved['review']['owner_benchmark']['hinged_doors'] == 8
    # Preserve the at-run review, but compare against the later owner correction.
    benchmark = json.loads((root / 'notes/evidence/hsl07-v62-2026-11-05/n68-owner-benchmark-2026-11-06.json').read_text())
    assert benchmark['expected']['door_like_fronts'] - parsed['totals']['hinged_doors'] == 3
    assert benchmark['expected']['drawers'] == parsed['totals']['drawers']
    assert sum(len(g['fronts']) for g in parsed['front_groups'] if g['type'] == 'drawer') == 6
    with pytest.raises(ValueError, match='invalid island classification'):
        agent.validate_front_count(parsed, {f'p7-view-{i:03d}' for i in range(1, 5)}, require_annotations=True, require_supports=True)
    planner = saved['stages']['planner']
    assert planner['status'] == 'failed' and planner['stop_reason'] == 'max_tokens'
    with pytest.raises(ValueError):
        agent._json_object(planner['response_text'])
