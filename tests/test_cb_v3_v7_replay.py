import json
from pathlib import Path

import pytest

import agents.estimation_understanding_agent as agent


EVIDENCE = Path(__file__).resolve().parents[1] / 'notes/evidence/lev2-v3-v7-2026-11-06/three-paired-runs.json'


@pytest.mark.parametrize('index', range(3))
def test_paired_v3_v7_records_preserve_stage_failures(index):
    saved = json.loads(EVIDENCE.read_text())
    assert saved['calls'] == 6 and saved['retries'] == 0
    assert saved['front_requests_identical_across_three_runs'] is True
    run = saved['runs'][index]
    front, planner = run['stages']['front'], run['stages']['planner']
    known = {f'p1-view-{i:03d}' for i in range(1, 5)}
    parsed = agent._json_object(front['response_text'])
    assert parsed == front['parsed_response']
    assert parsed['totals'] == dict(drawers=5, hinged_doors=17, lift_up_fronts=2, unresolved_fronts=0, total_fronts=24)
    assert front['prompt_sha256'] == '2530993b653575e5445eced53b34ed6b9393eb73c30428c2bac28d641d49429b'
    assert planner['prompt_sha256'] == 'd3271d697f5398e699511d8a261f3f8734bf744835b52b894188d37d819cd848'
    assert planner['request_settings']['max_tokens'] == 6000
    if index == 1:
        assert agent.validate_front_count(parsed, known, require_annotations=True, require_supports=True) == parsed
    else:
        with pytest.raises(ValueError, match='invalid island classification'):
            agent.validate_front_count(parsed, known, require_annotations=True, require_supports=True)
    if index < 2:
        assert planner['status'] == 'failed' and planner['stop_reason'] == 'max_tokens'
        assert planner['parsed_response'] is None
        with pytest.raises(ValueError):
            agent._json_object(planner['response_text'])
    else:
        plan = agent._json_object(planner['response_text'])
        assert agent.validate_assembly_plan(plan, known, agent.planner_front_ids(parsed, known)) == plan
        assert len(plan['blocks']) == 9 and len(plan['shared_parts']) == 1
        block = next(b for b in plan['blocks'] if b['id'] == 'B08')
        drawer = next(f for g in parsed['front_groups'] for f in g['fronts'] if f['id'] == 'F22')
        assert drawer['id'] in block['front_ids']
        assert block['region']['bbox_1000'][0] > drawer['bbox_1000'][0]
    assert run['full_chain_format_pass'] is False
    assert saved['review']['accepted'] is False
    assert agent.FRONT_SUPPORTS_PROMPT_PATH.name == 'cb_front_v2.md'
    assert agent.PLANNER_PROMPT_VERSION == 'CB Planner V4'
