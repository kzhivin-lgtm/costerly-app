"""Explicit, fallible whole-object context and lineage for the opt-in V5 cycle."""
from copy import deepcopy

from use_cases.estimation_cb_bays import _fields, _list

VERSION = 'CB Cycle V5'
FRONT_FIELDS = 'understanding front front_components support_components'
UNDERSTANDING_FIELDS = 'input_id summary construction_summary views components cross_view_links uncertainties'


def validate_front(parsed, manifests):
    from agents.estimation_understanding_agent import validate_understanding, validate_front_count
    if len(manifests) != 1:
        raise ValueError('V5 diagnostic requires one object; document batching not implemented')
    _fields(parsed, FRONT_FIELDS, VERSION)
    u = parsed['understanding']
    _fields(u, UNDERSTANDING_FIELDS, 'whole-object understanding')
    validate_understanding({'objects': [u]}, manifests)
    _list(u['components'], 'components', 1, 100)
    known = {v['view_id'] for v in manifests[0]['known_views']}
    validate_front_count(parsed['front'], known, require_annotations=True, require_supports=True)
    components = {c['id']: set(c['view_ids']) for c in u['components']}
    fronts = {f['id']: {f['view_id']} for g in parsed['front']['front_groups'] for f in g['fronts']}
    supports = {s['id']: set(s['view_ids']) for s in parsed['front']['tabletop_supports']}
    for key, id_key, expected in [('front_components', 'front_id', fronts), ('support_components', 'support_id', supports)]:
        _list(parsed[key], key, len(expected), len(expected))
        seen = set()
        for link in parsed[key]:
            _fields(link, f'{id_key} component_id', key)
            item, cid = link[id_key], link['component_id']
            if not isinstance(item, str) or item not in expected or item in seen:
                raise ValueError('foreign/duplicate component member')
            if not isinstance(cid, str) or cid not in components or not expected[item] <= components[cid]:
                raise ValueError('component member requires matching object-owned views')
            seen.add(item)
    return parsed


def validate_plan(parsed, *, front_result, manifests):
    from agents.estimation_understanding_agent import validate_assembly_plan, planner_front_ids
    validate_front(front_result, manifests)
    _fields(parsed, 'plan component_blocks interpretation_conflicts', 'V5 plan')
    known = {v['view_id'] for v in manifests[0]['known_views']}
    fids = planner_front_ids(front_result['front'], known)
    plan = validate_assembly_plan(parsed['plan'], known, fids)
    components = {c['id'] for c in front_result['understanding']['components']}
    blocks = {b['id'] for b in plan['blocks'] + plan['shared_parts']}
    _list(parsed['interpretation_conflicts'], 'interpretation conflicts', 0, 100)
    conflicts = set()
    for c in parsed['interpretation_conflicts']:
        _fields(c, 'component_id view_ids reason', 'interpretation conflict')
        if not isinstance(c['component_id'], str) or c['component_id'] not in components:
            raise ValueError('foreign conflict component')
        if not isinstance(c['reason'], str) or not c['reason'].strip() or len(c['reason']) > 1500:
            raise ValueError('bounded visible conflict reason required')
        _list(c['view_ids'], 'conflict views', 1, len(known))
        if any(not isinstance(v, str) or v not in known for v in c['view_ids']):
            raise ValueError('foreign conflict view')
        conflicts.add(c['component_id'])
    _list(parsed['component_blocks'], 'component mappings', len(components), len(components))
    mappings, covered = {}, set()
    for link in parsed['component_blocks']:
        _fields(link, 'component_id block_ids', 'component block map')
        cid = link['component_id']
        if not isinstance(cid, str) or cid not in components or cid in mappings:
            raise ValueError('foreign/duplicate plan component')
        _list(link['block_ids'], 'component block IDs', 0 if cid in conflicts else 1, len(blocks))
        if any(not isinstance(b, str) or b not in blocks for b in link['block_ids']):
            raise ValueError('foreign component block')
        if len(set(link['block_ids'])) != len(link['block_ids']):
            raise ValueError('duplicate component block')
        mappings[cid] = set(link['block_ids'])
        covered.update(link['block_ids'])
    if covered != blocks:
        raise ValueError('output block has no physical component')
    owners = {x['front_id']: x['component_id'] for x in front_result['front_components']}
    for block in plan['blocks']:
        if any(block['id'] not in mappings[owners[f]] for f in block['front_ids']):
            raise ValueError('Planner changed front physical component')
    return parsed


def parts_scope(*, front_result, planner_result, manifests, upstream_status):
    """Keep accepted topology; use the existing V3.3 compiler, not V4 regrouping."""
    validate_plan(planner_result, front_result=front_result, manifests=manifests)
    if planner_result['interpretation_conflicts'] or planner_result['plan']['front_conflicts']:
        raise ValueError('V5 interpretation conflicts require review before Calculate')
    return deepcopy(dict(input_id=front_result['understanding']['input_id'],
        analysis_contract=VERSION, parts_version='CB Parts V3.3',
        understanding=front_result['understanding'], front=front_result['front'],
        front_components=front_result['front_components'], support_components=front_result['support_components'],
        planner=planner_result['plan'], component_blocks=planner_result['component_blocks'],
        upstream_status=upstream_status))
