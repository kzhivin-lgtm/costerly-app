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


@pytest.mark.parametrize('count', [0, 1, 2, 4])
def test_support_counts_are_not_forced_to_one_typical_scheme(count):
    result = supported(count)
    before = deepcopy(result)
    assert validate(result) == before
    assert result['totals']['total_fronts'] == 3
    assert planner_front_ids(result, {'p1-view-001'}) == {'F0', 'F1', 'F2'}


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


def test_probe_support_switch_requires_front_mode_before_credentials(monkeypatch):
    from tools.probe_v62_module_call import main
    monkeypatch.setattr('sys.argv', ['probe', '--replay', 'unused', '--output', 'unused',
                                   '--execute', '--front-supports'])
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
