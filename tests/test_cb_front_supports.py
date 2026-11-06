from copy import deepcopy
import json
from pathlib import Path

import pytest

from agents.estimation_understanding_agent import validate_front_count, planner_front_ids, validate_assembly_plan, ISLAND_TYPES
from tests.test_estimation_front_count import annotated


def supported(count=2):
    result = annotated()
    result['tabletop_supports'] = [{
        'id': 'T01', 'location': 'Projecting tabletop', 'leg_count': count,
        'count_basis': 'clear', 'view_ids': ['p1-view-001'],
        'support_scheme': 'Visible legs; connection to the upright is assumed.',
        'uncertainty': '', 'legs': [
            {'id': f'L{i + 1:02d}', 'view_id': 'p1-view-001',
             'bbox_1000': [100 + i * 100, 600, 120 + i * 100, 900]}
            for i in range(count)]}]
    return result


def validate(result):
    return validate_front_count(result, {'p1-view-001'}, require_annotations=True, require_supports=True)


def test_lev2_v2_rollback_repeat_preserves_identical_request_failure():
    import agents.estimation_understanding_agent as agent
    from hashlib import sha256
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root / 'notes/evidence/cb-front-v2-2026-11-06/lev2-rollback-repeat.json').read_text())
    assert agent.FRONT_SUPPORTS_PROMPT_PATH.name == 'cb_front_v2.md'
    assert agent.PLANNER_PROMPT_VERSION == 'CB Planner V4'
    assert sha256(agent.FRONT_SUPPORTS_PROMPT_PATH.read_text().strip().encode()).hexdigest() == saved['prompt_sha256']
    assert saved['exact_request_equal'] is True
    assert saved['request_sha256'] == saved['comparison_request_sha256']
    assert saved['calls'] == 1 and saved['retries'] == 0
    parsed = agent._json_object(saved['response_text'])
    assert parsed == saved['parsed_response']
    assert parsed['totals'] == dict(drawers=5, hinged_doors=18, lift_up_fronts=2, unresolved_fronts=0, total_fronts=25)
    assert saved['previous_totals']['hinged_doors'] == 15
    assert saved['previous_totals']['unresolved_fronts'] == 2
    assert saved['status'] == 'failed' and saved['review']['accepted'] is False
    with pytest.raises(ValueError, match='invalid island classification'):
        agent.validate_front_count(parsed, {f'p1-view-{i:03d}' for i in range(1, 5)}, require_annotations=True, require_supports=True)


@pytest.mark.parametrize('count', [0, 1, 2, 4])
def test_support_counts_are_not_forced_to_one_typical_scheme(count):
    result = supported(count)
    before = deepcopy(result)
    assert validate(result) == before
    assert result['totals']['total_fronts'] == 3
    assert planner_front_ids(result, {'p1-view-001'}) == {'F0', 'F1', 'F2'}


@pytest.mark.parametrize('index,expected', [(0, (5, 17, 2, 1)), (1, (5, 16, 2, 1)), (2, (2, 11, 2, 0))])
def test_lev2_fixed_request_controls_preserve_variation(index, expected):
    import agents.estimation_understanding_agent as agent
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads((root / 'notes/evidence/cb-front-v2-2026-11-06/lev2-three-controls.json').read_text())
    assert evidence['calls'] == 3 and evidence['retries'] == 0
    run = evidence['runs'][index]
    assert run['exact_request_equal_to_baseline'] is True
    assert run['request_sha256'] == evidence['baseline_request_sha256']
    parsed = agent._json_object(run['response_text'])
    assert parsed == run['parsed_response']
    assert tuple(parsed['totals'][k] for k in ('drawers', 'hinged_doors', 'lift_up_fronts', 'unresolved_fronts')) == expected
    known = {f'p1-view-{i:03d}' for i in range(1, 5)}
    if index == 2:
        assert run['status'] == 'failed'
        with pytest.raises(ValueError, match='invalid island classification'):
            validate_front_count(parsed, known, require_annotations=True, require_supports=True)
        assert not any(f['view_id'] == 'p1-view-004' for g in parsed['front_groups'] for f in g['fronts'])
        assert any('three drawers that may partly overlap' in g['uncertainty'] for g in parsed['front_groups'])
    else:
        assert run['status'] == 'front_count_requires_review'
        assert validate_front_count(parsed, known, require_annotations=True, require_supports=True) == parsed
        assert run['front_box_counts_by_island']['p1-view-004']['drawer'] == 3
    assert evidence['review']['accepted'] is False


def test_hidden_inferred_legs_require_uncertainty_not_invented_boxes():
    result = supported()
    group = result['tabletop_supports'][0]
    group.update(leg_count=4, count_basis='estimated', uncertainty='Two rear supports are occluded; four is an estimate.')
    assert validate(result) == result
    group.update(leg_count=None, count_basis='undetermined')
    assert validate(result) == result


@pytest.mark.parametrize('bad', ['missing', 'extra', 'negative', 'bool', 'large', 'null_clear',
    'no_reason', 'missing_box', 'too_many_boxes', 'duplicate_leg', 'front_collision',
    'excluded_collision', 'group_collision', 'foreign', 'wrong_group_view', 'nan',
    'empty_scheme', 'duplicate_group', 'duplicate_refs', 'bad_basis', 'bad_type'])
def test_support_contract_rejects_invalid_data_without_repair(bad):
    result = supported()
    g = result['tabletop_supports'][0]
    if bad == 'missing': result.pop('tabletop_supports')
    if bad == 'extra': g['price'] = 1
    if bad == 'negative': g['leg_count'] = -1
    if bad == 'bool': g['leg_count'] = True
    if bad == 'large': g['leg_count'] = 201
    if bad == 'null_clear': g['leg_count'] = None
    if bad == 'no_reason': g['count_basis'] = 'estimated'
    if bad == 'missing_box': g['legs'].pop()
    if bad == 'too_many_boxes': g['leg_count'] = 1
    if bad == 'duplicate_leg': g['legs'][1]['id'] = g['legs'][0]['id']
    if bad == 'front_collision': g['legs'][0]['id'] = 'F0'
    if bad == 'excluded_collision': result['excluded_surfaces'] = [{**g['legs'][0], 'reason': 'Fixed'}]
    if bad == 'group_collision': g['id'] = g['legs'][0]['id']
    if bad == 'foreign': g['view_ids'] = ['foreign']
    if bad == 'wrong_group_view': g['legs'][0]['view_id'] = 'foreign'
    if bad == 'nan': g['legs'][0]['bbox_1000'][0] = float('nan')
    if bad == 'empty_scheme': g['support_scheme'] = ''
    if bad == 'duplicate_group': result['tabletop_supports'].append(deepcopy(g))
    if bad == 'duplicate_refs': g['view_ids'] *= 2
    if bad == 'bad_basis': g['count_basis'] = []
    if bad == 'bad_type': result['tabletop_supports'] = {}
    before = deepcopy(result)
    with pytest.raises(ValueError):
        validate(result)
    assert result == before


def test_legacy_and_support_contracts_are_explicit():
    with pytest.raises(ValueError):
        validate_front_count(supported(), {'p1-view-001'}, require_annotations=True)
    with pytest.raises(ValueError):
        validate_front_count(supported(), {'p1-view-001'}, require_supports=True)


def test_recorded_support_probe_preserves_original_rejection_and_planner_regression():
    root = Path(__file__).parents[1] / 'notes' / 'evidence' / 'cb-front-v2-2026-11-05'
    front = json.loads((root / 'lev1-front-evidence.json').read_text())
    planner = json.loads((root / 'lev1-planner-evidence.json').read_text())
    known = {f'p1-view-{i:03d}' for i in range(1, 7)}
    assert front['changed_request_fields'] == ['system']
    assert front['original_status'] == 'failed'
    with pytest.raises(ValueError, match='invalid island classification'):
        validate_front_count(front['parsed_response'], known, require_annotations=True, require_supports=True)
    # Diagnostic copy only: verify remaining contract without altering the witness.
    copied = deepcopy(front['parsed_response'])
    aliases = {v.lower().replace(' ', '_'): v for v in ISLAND_TYPES}
    for island in copied['island_types']:
        island['type'] = aliases[island['type']]
    assert validate_front_count(copied, known, require_annotations=True, require_supports=True) == copied
    assert copied['tabletop_supports'][0]['leg_count'] == 2
    assert len(copied['tabletop_supports'][0]['legs']) == 2
    assert copied['totals']['drawers'] == 3
    assert planner['changed_request_fields'] == ['messages']
    assert planner['image_and_ocr_content_unchanged']
    p = planner['parsed_response']
    assert validate_assembly_plan(p, known, {'F01', 'F02', 'F03'}) == p
    assert len(p['blocks']) == 2  # Observed regrouping, not the desired target.
    assert 'two legs' in p['summary']


@pytest.mark.parametrize('flag', ['--front-supports', '--front-v1'])
def test_probe_support_switch_requires_front_mode_before_credentials(monkeypatch, flag):
    from tools.probe_v62_module_call import main
    monkeypatch.setattr('sys.argv', ['probe', '--replay', 'unused', '--output', 'unused',
                                   '--execute', flag])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


def test_recorded_repeat_does_not_reproduce_three_to_two_dependency():
    path = Path(__file__).parents[1] / 'notes' / 'evidence' / 'cb-front-v2-2026-11-05' / 'lev1-repeat-comparison.json'
    evidence = json.loads(path.read_text())
    known = {f'p1-view-{i:03d}' for i in range(1, 7)}
    for variant in ('v1', 'v2'):
        front, planner = evidence[variant]['front_count'], evidence[variant]['assembly_plan']
        assert front['changed_request_fields_vs_same_variant_previous'] == []
        assert front['original_status'] == 'failed'
        with pytest.raises(ValueError, match='invalid island classification'):
            validate_front_count(front['parsed_response'], known,
                                 require_annotations=True, require_supports=variant == 'v2')
        assert planner['changed_request_fields_vs_same_variant_previous'] == ['messages']
        assert planner['image_and_ocr_content_unchanged']
        p = planner['parsed_response']
        assert validate_assembly_plan(p, known, {'F01', 'F02', 'F03'}) == p
        assert len(p['blocks']) == 3
    assert evidence['v2']['front_count']['parsed_response']['tabletop_supports'][0]['leg_count'] == 2
    assert 'two legs' in evidence['v2']['assembly_plan']['parsed_response']['summary']


def test_lev2_support_probe_keeps_counts_and_records_truncated_planner():
    root = Path(__file__).parents[1] / 'notes' / 'evidence' / 'cb-front-v2-2026-11-05'
    front = json.loads((root / 'lev2-front-evidence.json').read_text())
    planner = json.loads((root / 'lev2-planner-evidence.json').read_text())
    p = front['parsed_response']
    assert front['original_status'] == 'front_count_requires_review'
    assert front['changed_request_fields'] == ['system']
    assert validate_front_count(p, {f'p1-view-{i:03d}' for i in range(1, 5)},
                                require_annotations=True, require_supports=True) == p
    assert p['totals'] == {'drawers': 5, 'hinged_doors': 15, 'lift_up_fronts': 2,
                           'unresolved_fronts': 2, 'total_fronts': 24}
    assert p['tabletop_supports'][0]['leg_count'] == 0
    assert not p['tabletop_supports'][0]['legs']
    assert planner['original_status'] == 'failed'
    assert planner['stop_reason'] == 'max_tokens'
    assert planner['max_tokens'] == 6000
    assert planner['parsed_response'] is None
    assert planner['changed_request_fields'] == ['messages']
    assert planner['image_and_ocr_content_unchanged']
    with pytest.raises(json.JSONDecodeError):
        json.loads(planner['response_text'])
