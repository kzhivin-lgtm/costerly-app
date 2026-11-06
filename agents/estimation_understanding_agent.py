"""V6.2 first-cycle-only understanding. Not a BOM or production replacement."""
import json
import math
from hashlib import sha256
from pathlib import Path

from agents.estimation_composition_analyze_agent import _page_manifest
from agents.estimation_visual_evidence import page_content
from agents.anthropic_adapter import get_anthropic_client, extract_text_from_claude_response
from agents.estimation_v4_1_material_facts_agent import _create_message_with_hard_timeout, _json_object
from use_cases.estimation_dimension_graph import build_dimension_graph

VERSION = "estimation_understanding_v6_2"
MODEL = "claude-haiku-5-5"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_understanding_v6_2.md"
ISLAND_TYPES_PROMPT_PATH = PROMPT_PATH.with_name("estimation_island_types_v6_2.md")
FRONT_COUNT_PROMPT_PATH = PROMPT_PATH.with_name("estimation_front_count_v6_2.md")
FRONT_COUNT_PROMPT_VERSION = "estimation_front_count_v6_2_r03"
FRONT_SUPPORTS_PROMPT_PATH = PROMPT_PATH.with_name("cb_front_v2.md")
FRONT_SUPPORTS_PROMPT_VERSION = "estimation_front_count_v6_2_r05"
PLANNER_PROMPT_PATH = PROMPT_PATH.with_name("cb_planner_v4.md")
PLANNER_PROMPT_VERSION = "CB Planner V4"
# One rulebook, logical sections. Existing Front/Planner defaults stay immutable.
CB_RULEBOOK = {
    'front': {'name': 'CB Front V2', 'version': FRONT_SUPPORTS_PROMPT_VERSION, 'path': FRONT_SUPPORTS_PROMPT_PATH,
              'previous': {'name': 'CB Front V1', 'version': FRONT_COUNT_PROMPT_VERSION, 'path': FRONT_COUNT_PROMPT_PATH}},
    'planner': {'name': PLANNER_PROMPT_VERSION, 'version': PLANNER_PROMPT_VERSION, 'path': PLANNER_PROMPT_PATH},
    'parts': {'name': 'CB Parts V3', 'version': 'CB Parts V3',
              'path': PROMPT_PATH.with_name('cb_parts_v3.md'),
              'consumer': 'Calculate', 'status': 'experimental_not_accepted',
              'v3_1': {'version': 'CB Parts V3.1', 'path': PROMPT_PATH.with_name('cb_parts_v3_1.md')},
              'v3_2': {'version': 'CB Parts V3.2', 'path': PROMPT_PATH.with_name('cb_parts_v3_2.md')},
              'v3_3': {'version': 'CB Parts V3.3', 'path': PROMPT_PATH.with_name('cb_parts_v3_3.md')},
              'v3_4': {'version': 'CB Parts V3.4', 'path': PROMPT_PATH.with_name('cb_parts_v3_4.md')},
              'v3_5': {'version': 'CB Parts V3.5', 'path': PROMPT_PATH.with_name('cb_parts_v3_5.md')},
              'v4': {'version': 'CB Parts V4', 'path': PROMPT_PATH.with_name('cb_parts_v4.md')},
              'v4_1': {'version': 'CB Parts V4.1', 'path': PROMPT_PATH.with_name('cb_parts_v4_1.md')},
              'v2': {'version': 'CB Parts V2', 'path': PROMPT_PATH.with_name('cb_parts_v2.md')},
              'previous': {'name': 'CB Parts V1', 'version': 'CB Parts V1',
                           'path': PROMPT_PATH.with_name('cb_parts_v1.md')}},
}

ISLAND_TYPES = ['Front elevation', 'Side view', 'Rear view', 'Top view',
    'Bottom view', 'Axonometric view', 'Perspective view', 'Section', 'Undetermined']


def island_types_schema():
    properties = {'view_id': {'type': 'string'},
        'type': {'type': 'string', 'enum': ISLAND_TYPES}}
    return {'type': 'array', 'minItems': 1, 'items': {'type': 'object',
        'additionalProperties': False, 'required': list(properties), 'properties': properties}}


def validate_island_types(entries, known):
    """Validate coverage and references, never certify inferred projections."""
    if not isinstance(entries, list) or not entries:
        raise ValueError('island_types required')
    expected = set(island_types_schema()['items']['required'])
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != expected:
            raise ValueError('invalid island type fields')
        vid = entry['view_id']
        if not isinstance(vid, str) or vid not in known or vid in seen:
            raise ValueError('foreign/duplicate island')
        seen.add(vid)
        if not isinstance(entry['type'], str) or entry['type'] not in ISLAND_TYPES:
            raise ValueError('invalid island classification')
    if seen != known:
        raise ValueError('omitted island')
    return entries


def prepare_content(inputs, page_bytes):
    if not inputs or any(not r.get('input_id') for r in inputs) or len({r['input_id'] for r in inputs}) != len(inputs):
        raise ValueError("unique nonempty input set required")
    if len({(r['input_payload']['company_id'], r['input_payload']['run_id']) for r in inputs}) != 1:
        raise ValueError("one company/document run per understanding request")
    pages, objects = _page_manifest(inputs, page_bytes)
    manifests = []
    for row, obj in zip(inputs, objects):
        # Preserve Detection's name in the immutable input/audit, not as a
        # semantic hint to the visual reader. IDs still lock object membership.
        manifests.append({**{k: v for k, v in obj.items() if k != 'object_name'},
            "known_views": build_dimension_graph(input_row=row)['views']})
    overviews, details = [], []
    for page in pages:
        visual, _ = page_content(page_bytes=page['bytes'], storage_ref=page['storage_ref'],
            page_number=page['page_number'], payloads=[r['input_payload'] for r in inputs], detail_budget=64)
        overviews.extend(visual[:3])
        details.extend(visual[3:])
    content = overviews + details
    if not pages or sum(c['type'] == 'image' for c in content) > 64:
        raise ValueError("understanding evidence exceeds image bound; never silently truncate")
    text = {str(item['block_ref']): item for r in inputs for container in ('evidence', 'document_context')
        for kind in ('ocr_blocks', 'ocr_literal_items')
        for item in r['input_payload'].get(container, {}).get(kind, []) if item.get('block_ref')}
    context = json.dumps({'objects': manifests, 'source_text': list(text.values())}, ensure_ascii=False)
    if len(context) > 100000:
        raise ValueError("understanding text exceeds bound; never silently truncate")
    content.append({'type': 'text', 'text': context})
    return content, manifests


def validate_understanding(parsed, manifests):
    """Reference/coverage validation only. Never certifies physical correctness."""
    if not isinstance(parsed, dict) or set(parsed) != {'objects'} or not isinstance(parsed['objects'], list):
        raise ValueError("objects required")
    expected = {m['input_id']: m for m in manifests}
    seen = set()
    def words(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 2500:
            raise ValueError("bounded explanation required")
    for obj in parsed['objects']:
        iid = obj['input_id']
        if iid not in expected or iid in seen:
            raise ValueError("foreign/duplicate input")
        seen.add(iid)
        for key in ('summary', 'construction_summary'): words(obj[key])
        for key in ('views', 'components', 'cross_view_links', 'uncertainties'):
            if not isinstance(obj[key], list): raise ValueError("list required")
        if not obj['views'] or not obj['components']: raise ValueError("views/components required")
        known = {v['view_id']: v['page_number'] for v in expected[iid]['known_views']}
        pages = {p['page_number'] for p in expected[iid]['evidence_pages']}
        views = {}
        for view in obj['views']:
            words(view['id']); words(view['location']); words(view['observation'])
            if view['id'] in views or view['page_number'] not in pages:
                raise ValueError("foreign/duplicate view")
            if known and known.get(view['id']) != view['page_number']:
                raise ValueError("changed source view")
            views[view['id']] = view
        if known and set(views) != set(known): raise ValueError("omitted source view")
        components = set()
        for comp in obj['components']:
            for key in ('id', 'name', 'function', 'material_hypothesis'): words(comp[key])
            if comp['id'] in components: raise ValueError("duplicate component")
            components.add(comp['id'])
            if comp['operation'] not in {'fixed', 'drawer', 'hinged', 'lift_up', 'unknown'}:
                raise ValueError("unknown operation")
            if comp['basis'] not in {'source', 'visual_interpretation', 'construction_assumption'}:
                raise ValueError("unknown interpretation basis")
            q = comp['quantity']
            if q is not None and (type(q) is not int or q <= 0): raise ValueError("invalid quantity")
            refs = comp['view_ids']
            if not isinstance(refs, list) or not refs or not set(refs) <= set(views):
                raise ValueError("component needs object-owned view references")
        for link in obj['cross_view_links']:
            words(link['correspondence'])
            refs = link['view_ids']
            if (link['component_id'] not in components or not isinstance(refs, list)
                    or len(set(refs)) < 2 or not set(refs) <= set(views)):
                raise ValueError("invalid cross-view correspondence")
        for issue in obj['uncertainties']: words(issue)
    if seen != set(expected): raise ValueError("omitted object")
    return parsed


def run_understanding(*, inputs, page_bytes):
    content, manifests = prepare_content(inputs, page_bytes)
    response = _create_message_with_hard_timeout(get_anthropic_client().with_options(timeout=60, max_retries=0),
        timeout_seconds=60, model=MODEL, max_tokens=min(12000, 3500 * len(inputs)), output_config={'effort': 'low'},
        system=PROMPT_PATH.read_text().strip(), messages=[{'role': 'user', 'content': content}])
    parsed = validate_understanding(_json_object(extract_text_from_claude_response(response)), manifests)
    return {'version': VERSION, 'status': 'interpretation_requires_review', **parsed}


def cabinet_module_policy():
    """Load existing policy only after explicit module selection, no new library."""
    prompt = PROMPT_PATH.read_text()
    start = prompt.index('Cabinet Block operability policy')
    end = prompt.index('Explicit applicable material notes', start)
    return prompt[start:end], prompt[:start] + prompt[end:]


def validate_front_count(parsed, known, *, require_annotations=False, require_supports=False):
    """Check references and arithmetic, not visual accuracy. Never repair counts."""
    fields = {'island_types', 'front_groups', 'totals'}
    if require_annotations:
        fields.add('excluded_surfaces')
    if require_supports:
        if not require_annotations:
            raise ValueError('support interpretation requires annotations')
        fields.add('tabletop_supports')
    if not isinstance(parsed, dict) or set(parsed) != fields:
        raise ValueError('invalid front-count fields')
    validate_island_types(parsed['island_types'], known)
    groups = parsed['front_groups']
    if not isinstance(groups, list) or len(groups) > 200:
        raise ValueError('bounded front_groups required')
    categories = {'drawer': 'drawers', 'hinged': 'hinged_doors',
                  'lift_up': 'lift_up_fronts', 'unresolved': 'unresolved_fronts'}
    counts = {key: [] for key in categories.values()}
    for group in groups:
        group_fields = {'location', 'type', 'count', 'count_basis', 'view_ids', 'uncertainty'}
        if require_annotations:
            group_fields.add('fronts')
        if not isinstance(group, dict) or set(group) != group_fields:
            raise ValueError('invalid front group fields')
        for key in ('location', 'uncertainty'):
            if not isinstance(group[key], str) or len(group[key]) > 2500:
                raise ValueError('bounded front group text required')
        if not group['location'].strip():
            raise ValueError('physical group location required')
        kind, basis, count = group['type'], group['count_basis'], group['count']
        if not isinstance(kind, str) or kind not in categories:
            raise ValueError('invalid front type')
        if not isinstance(basis, str) or basis not in {'clear', 'estimated', 'undetermined'}:
            raise ValueError('invalid count basis')
        if count is not None and (type(count) is not int or count <= 0):
            raise ValueError('positive integer or null group count required')
        if (count is None) != (basis == 'undetermined'):
            raise ValueError('null count requires undetermined basis')
        if basis != 'clear' and not group['uncertainty'].strip():
            raise ValueError('uncertain count needs a specific ambiguity')
        refs = group['view_ids']
        if (not isinstance(refs, list) or not refs or
                any(not isinstance(v, str) or v not in known for v in refs) or
                len(set(refs)) != len(refs)):
            raise ValueError('group needs unique object-owned view references')
        counts[categories[kind]].append(count)
    def total(values):
        return None if any(v is None for v in values) else sum(values)
    expected = {key: total(values) for key, values in counts.items()}
    expected['total_fronts'] = total(list(expected.values()))
    totals = parsed['totals']
    if (not isinstance(totals, dict) or set(totals) != set(expected) or
            any(v is not None and (type(v) is not int or v < 0) for v in totals.values()) or
            totals != expected):
        raise ValueError('front totals do not match group counts')
    if require_annotations:
        seen = set()
        def annotation(item, *, excluded=False):
            keys = {'id', 'view_id', 'bbox_1000'} | ({'reason'} if excluded else set())
            if not isinstance(item, dict) or set(item) != keys:
                raise ValueError('invalid front annotation fields')
            aid = item['id']
            if not isinstance(aid, str) or not aid.strip() or len(aid) > 40 or aid in seen:
                raise ValueError('invalid/duplicate annotation ID')
            seen.add(aid)
            if not isinstance(item['view_id'], str) or item['view_id'] not in known:
                raise ValueError('annotation references foreign island')
            box = item['bbox_1000']
            if (not isinstance(box, list) or len(box) != 4 or
                    any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1000 for v in box) or
                    box[0] >= box[2] or box[1] >= box[3]):
                raise ValueError('invalid image-local annotation box')
            if excluded and (not isinstance(item['reason'], str) or not item['reason'].strip() or len(item['reason']) > 1200):
                raise ValueError('excluded surface needs bounded reason')
        for group in groups:
            fronts = group['fronts']
            if not isinstance(fronts, list) or len(fronts) > 200:
                raise ValueError('bounded individual front annotations required')
            if group['count'] is not None and len(fronts) != group['count']:
                raise ValueError('front box count differs from group count')
            for item in fronts:
                annotation(item)
                if item['view_id'] not in group['view_ids']:
                    raise ValueError('front annotation outside group view references')
        excluded = parsed['excluded_surfaces']
        if not isinstance(excluded, list) or len(excluded) > 200:
            raise ValueError('bounded excluded surfaces required')
        for item in excluded:
            annotation(item, excluded=True)
        if require_supports:
            supports = parsed['tabletop_supports']
            if not isinstance(supports, list) or len(supports) > 200:
                raise ValueError('bounded tabletop supports required')
            for support in supports:
                if not isinstance(support, dict) or set(support) != {
                        'id', 'location', 'leg_count', 'count_basis', 'view_ids',
                        'support_scheme', 'uncertainty', 'legs'}:
                    raise ValueError('invalid tabletop support fields')
                sid = support['id']
                if not isinstance(sid, str) or not sid.strip() or len(sid) > 40 or sid in seen:
                    raise ValueError('invalid/duplicate support ID')
                seen.add(sid)
                for key in ('location', 'support_scheme', 'uncertainty'):
                    value = support[key]
                    if not isinstance(value, str) or len(value) > 2500 or (key != 'uncertainty' and not value.strip()):
                        raise ValueError('bounded support description required')
                refs = support['view_ids']
                if (not isinstance(refs, list) or not refs or
                        any(not isinstance(v, str) or v not in known for v in refs) or len(set(refs)) != len(refs)):
                    raise ValueError('support needs unique object-owned views')
                count, basis = support['leg_count'], support['count_basis']
                if count is not None and (type(count) is not int or count < 0 or count > 200):
                    raise ValueError('bounded nonnegative leg count or null required')
                if not isinstance(basis, str) or basis not in {'clear', 'estimated', 'undetermined'}:
                    raise ValueError('invalid support count basis')
                if (count is None) != (basis == 'undetermined'):
                    raise ValueError('null leg count requires undetermined basis')
                if basis != 'clear' and not support['uncertainty'].strip():
                    raise ValueError('uncertain support count needs explanation')
                legs = support['legs']
                if not isinstance(legs, list) or len(legs) > 200:
                    raise ValueError('bounded leg annotations required')
                if count is not None and (len(legs) > count or (basis == 'clear' and len(legs) != count)):
                    raise ValueError('leg annotations disagree with count')
                for leg in legs:
                    annotation(leg)
                    if leg['view_id'] not in refs:
                        raise ValueError('leg annotation outside support views')
    return parsed


def planner_front_ids(front_result, known):
    """Read fallible saved Front references without repairing its classifications."""
    if not isinstance(front_result, dict) or not isinstance(front_result.get('front_groups'), list):
        raise ValueError('saved Front result required')
    ids = set()
    for group in front_result['front_groups']:
        if not isinstance(group, dict) or not isinstance(group.get('fronts'), list):
            raise ValueError('saved Front annotations required')
        for front in group['fronts']:
            if not isinstance(front, dict):
                raise ValueError('invalid saved Front reference')
            fid = front.get('id')
            if (not isinstance(fid, str) or not fid or fid in ids or
                    front.get('view_id') not in known):
                raise ValueError('invalid/duplicate/foreign saved Front reference')
            ids.add(fid)
    return ids


def validate_assembly_plan(parsed, known, front_ids):
    """Validate scope and references, not buildability or visual correctness."""
    if not isinstance(parsed, dict) or set(parsed) != {'summary', 'blocks', 'shared_parts', 'front_conflicts', 'uncertainties'}:
        raise ValueError('invalid Planner fields')
    def words(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 1500:
            raise ValueError('bounded Planner text required')
    def refs(values, allowed, minimum=1):
        if (not isinstance(values, list) or len(values) < minimum or
                any(not isinstance(v, str) or v not in allowed for v in values) or
                len(set(values)) != len(values)):
            raise ValueError('invalid Planner references')
    def region(item):
        refs(item['view_ids'], known)
        r = item['region']
        if not isinstance(r, dict) or set(r) != {'view_id', 'bbox_1000'} or r['view_id'] not in item['view_ids']:
            raise ValueError('invalid Planner region')
        b = r['bbox_1000']
        if (not isinstance(b, list) or len(b) != 4 or
                any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1000 for v in b) or
                b[0] >= b[2] or b[1] >= b[3]):
            raise ValueError('invalid Planner box')
    words(parsed['summary'])
    for key in ('blocks', 'shared_parts', 'front_conflicts', 'uncertainties'):
        if not isinstance(parsed[key], list) or len(parsed[key]) > 200:
            raise ValueError('bounded Planner lists required')
    if not parsed['blocks']:
        raise ValueError('Planner blocks required')
    ids, assigned = set(), set()
    def identity(item):
        words(item['id']); words(item['name'])
        if item['id'] in ids:
            raise ValueError('duplicate Planner ID')
        ids.add(item['id'])
        region(item)
    for block in parsed['blocks']:
        if not isinstance(block, dict) or set(block) != {'id', 'name', 'contains', 'reason', 'front_ids', 'view_ids', 'region'}:
            raise ValueError('invalid Planner block')
        identity(block); words(block['contains']); words(block['reason'])
        refs(block['front_ids'], front_ids, 0)
        if assigned.intersection(block['front_ids']):
            raise ValueError('front assigned twice')
        assigned.update(block['front_ids'])
    block_ids = set(ids)
    for part in parsed['shared_parts']:
        if not isinstance(part, dict) or set(part) != {'id', 'name', 'block_ids', 'view_ids', 'region'}:
            raise ValueError('invalid shared part')
        identity(part); refs(part['block_ids'], block_ids, 2)
    for conflict in parsed['front_conflicts']:
        if not isinstance(conflict, dict) or set(conflict) != {'front_id', 'reason'}:
            raise ValueError('invalid front conflict')
        refs([conflict['front_id']], front_ids); words(conflict['reason'])
        if conflict['front_id'] in assigned:
            raise ValueError('front assigned twice')
        assigned.add(conflict['front_id'])
    if assigned != front_ids:
        raise ValueError('omitted Front references')
    for uncertainty in parsed['uncertainties']:
        words(uncertainty)
    return parsed


def run_assembly_plan(*, inputs, page_bytes, front_result, front_status, record=None):
    """One isolated Planner probe consuming saved Front; no implicit Front call."""
    if len(inputs) != 1:
        raise ValueError('Planner experiment requires exactly one object')
    content, manifests = prepare_content(inputs, page_bytes)
    known = {v['view_id'] for v in manifests[0]['known_views']}
    if not known:
        raise ValueError('Planner requires Detection-owned islands')
    fronts = planner_front_ids(front_result, known)
    context = json.dumps({'saved_front_status': front_status, 'fallible_front_reference': front_result}, ensure_ascii=False)
    if len(context) > 100000:
        raise ValueError('Front reference exceeds bound')
    content.append({'type': 'text', 'text': context})
    request = {'model': MODEL, 'max_tokens': 6000, 'output_config': {'effort': 'low'},
        'system': PLANNER_PROMPT_PATH.read_text().strip(), 'messages': [{'role': 'user', 'content': content}]}
    response = _create_message_with_hard_timeout(
        get_anthropic_client().with_options(timeout=60, max_retries=0), timeout_seconds=60, **request)
    if record:
        record('assembly_plan', request, response)
    if getattr(response, 'stop_reason', None) != 'end_turn':
        raise ValueError('Planner response did not finish normally')
    parsed = validate_assembly_plan(_json_object(extract_text_from_claude_response(response)), known, fronts)
    return {'version': VERSION, 'status': 'assembly_plan_requires_review',
        'prompt_version': PLANNER_PROMPT_VERSION, 'prompt_sha256': sha256(request['system'].encode()).hexdigest(),
        'input_id': manifests[0]['input_id'], 'assembly_plan': parsed}


def run_front_count(*, inputs, page_bytes, record=None, include_supports=True):
    """Approved single-object prompt experiment, not an added production stage."""
    if len(inputs) != 1:
        raise ValueError('front-count experiment requires exactly one object')
    content, manifests = prepare_content(inputs, page_bytes)
    known = {v['view_id'] for v in manifests[0]['known_views']}
    if not known:
        raise ValueError('front-count experiment requires Detection-owned islands')
    prompt_path = FRONT_SUPPORTS_PROMPT_PATH if include_supports else FRONT_COUNT_PROMPT_PATH
    prompt_version = FRONT_SUPPORTS_PROMPT_VERSION if include_supports else FRONT_COUNT_PROMPT_VERSION
    request = {'model': MODEL, 'max_tokens': 10000, 'output_config': {'effort': 'low'},
        'system': prompt_path.read_text().strip(),
        'messages': [{'role': 'user', 'content': content}]}
    response = _create_message_with_hard_timeout(
        get_anthropic_client().with_options(timeout=60, max_retries=0),
        timeout_seconds=60, **request)
    if record:
        record('front_count', request, response)
    if getattr(response, 'stop_reason', None) != 'end_turn':
        raise ValueError('front-count response did not finish normally')
    parsed = validate_front_count(_json_object(extract_text_from_claude_response(response)), known,
                                  require_annotations=True, require_supports=include_supports)
    return {'version': VERSION, 'status': 'front_count_requires_review',
            'prompt_version': prompt_version,
            'prompt_sha256': sha256(request['system'].encode()).hexdigest(),
            'input_id': manifests[0]['input_id'], 'front_count': parsed}


def run_island_types_only(*, inputs, page_bytes, record=None):
    """Isolation experiment, one request instead of the module workflow, not a third stage."""
    content, manifests = prepare_content(inputs, page_bytes)
    if any(not m['known_views'] for m in manifests):
        raise ValueError('Classification diagnostic requires Detection-owned islands')
    ids = [v['view_id'] for m in manifests for v in m['known_views']]
    if len(ids) != len(set(ids)):
        raise ValueError('Plain classification requires globally unique island IDs')
    # Identical classification instructions, without module selection/decomposition.
    system = ISLAND_TYPES_PROMPT_PATH.read_text() + (
        '\nReturn exactly one line per island: <original view_id>: <type label>. '
        'Replace the placeholders, do not print a literal prefix. '
        'No explanations, headings, JSON, Markdown or other text.')
    request = {'model': MODEL, 'output_config': {'effort': 'low'}, 'max_tokens': min(12000, 4000 * len(inputs)),
        'system': system, 'messages': [{'role': 'user', 'content': content}]}
    response = _create_message_with_hard_timeout(
        get_anthropic_client().with_options(timeout=60, max_retries=0), timeout_seconds=60, **request)
    if record:
        record('island_types', request, response)
    if getattr(response, 'stop_reason', None) == 'max_tokens':
        raise ValueError('island classification response truncated')
    entries = []
    for line in extract_text_from_claude_response(response).strip().splitlines():
        parts = line.split(':', 1)
        if len(parts) != 2:
            raise ValueError('invalid island classification line')
        entries.append({'view_id': parts[0].strip(), 'type': parts[1].strip()})
    known = {v['view_id'] for m in manifests for v in m['known_views']}
    validate_island_types(entries, known)
    return {'version': VERSION, 'status': 'island_types_require_review',
        'classifications': [{'input_id': m['input_id'], 'island_types': [e for e in entries
            if e['view_id'] in {v['view_id'] for v in m['known_views']}]} for m in manifests], 'objects': []}


def run_understanding_with_modules(*, inputs, page_bytes, record=None):
    """Diagnostic tool-selected Analyze. Two provider calls, no Calculation/DB."""
    content, manifests = prepare_content(inputs, page_bytes)
    by_id = {m['input_id']: m for m in manifests}
    if any(not m['known_views'] for m in manifests):
        raise ValueError('Classification diagnostic requires Detection-owned islands')
    tool = {'name': 'apply_cabinet_block',
        'description': 'Select this construction module for cabinet furniture: kitchens, cabinets, storage/shelving systems or their cabinet assemblies. First identify the physical whole from all evidence. The module returns the existing interpretation rules. Do not select it for unrelated furniture just because it is the only registered module.',
        'input_schema': {'type': 'object', 'additionalProperties': False,
            'required': ['input_id', 'island_types', 'whole_object', 'applicable_assemblies', 'excluded_assemblies', 'view_ids'],
            'properties': {
                'input_id': {'type': 'string', 'enum': list(by_id)},
                'island_types': island_types_schema(),
                'whole_object': {'type': 'string'},
                'applicable_assemblies': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1},
                'excluded_assemblies': {'type': 'array', 'items': {'type': 'string'}},
                'view_ids': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1},
            }}}
    system = (ISLAND_TYPES_PROMPT_PATH.read_text().strip() + '\n\n'
        'You are a furniture estimator. Examine all evidence jointly to identify the physical '
        'whole and its large assemblies. Then explicitly select an applicable construction module '
        'by calling its tool. Include one island_types entry per known view_id, containing only '
        'view_id and type. Do not output an essay or a correspondence map. '
        'Do not count hardware or materials before module selection. Do not rely on Naming. '
        'If no module applies, report that instead of forcing an unsuitable selection. '
        'Describe observable applicability, not internal reasoning. All generated text must be English. '
        'After receiving the module, apply its rules to the original evidence and follow the '
        'provided result contract. This continues the analysis, not a review by another model. '
        'Module rules and inferred view types are not source facts. Use the original images '
        'throughout; page position is not physical position in the object.')
    client = get_anthropic_client().with_options(timeout=60, max_retries=0)
    messages = [{'role': 'user', 'content': content}]
    def call(stage, **kwargs):
        response = _create_message_with_hard_timeout(client, timeout_seconds=60, model=MODEL,
            output_config={'effort': 'low'}, system=system, **kwargs)
        if record:
            record(stage, {'model': MODEL, 'output_config': {'effort': 'low'}, 'system': system, **kwargs}, response)
        if getattr(response, 'stop_reason', None) == 'max_tokens':
            raise ValueError('module response truncated')
        return response
    # Map output scales with owned islands, not one provider request per island.
    map_budget = min(12000, max(1600, 1000 * sum(len(m['known_views']) for m in manifests)))
    first = call('module_selection', max_tokens=map_budget, messages=messages,
                 tools=[tool], tool_choice={'type': 'auto'})
    blocks = [b.model_dump(exclude_none=True) if hasattr(b, 'model_dump') else vars(b) for b in first.content]
    selected = [b for b in blocks if b.get('type') == 'tool_use']
    if not selected:
        raise ValueError('no applicable module selected; no forced fallback')
    seen, calls, results = set(), set(), []
    policy, final_contract = cabinet_module_policy()
    for block in selected:
        arg = block.get('input') or {}
        iid = arg.get('input_id')
        if block.get('name') != tool['name'] or iid not in by_id or iid in seen:
            raise ValueError('unknown/duplicate module target')
        if not block.get('id') or block['id'] in calls:
            raise ValueError('invalid module call id')
        if set(arg) != set(tool['input_schema']['required']):
            raise ValueError('invalid module selection fields')
        known = {v['view_id'] for v in by_id[iid]['known_views']}
        validate_island_types(arg['island_types'], known)
        refs = arg['view_ids']
        if not isinstance(refs, list) or not refs or not set(refs) <= known:
            raise ValueError('module selection references foreign views')
        if not isinstance(arg['whole_object'], str) or not arg['whole_object'].strip():
            raise ValueError('module selection needs whole-object description')
        for key in ('applicable_assemblies', 'excluded_assemblies'):
            if not isinstance(arg[key], list) or any(not isinstance(s, str) or not s.strip() for s in arg[key]):
                raise ValueError('invalid module scope')
        if not arg['applicable_assemblies']:
            raise ValueError('module scope is empty')
        seen.add(iid); calls.add(block['id'])
        results.append({'type': 'tool_result', 'tool_use_id': block['id'], 'content': json.dumps({
            'module': 'Cabinet Block', 'input_id': iid, 'scope': arg,
            'policy': policy, 'boundary': 'Interpret the selected cabinet assemblies. Keep excluded assemblies in the whole-object result with their own roles. No hardware totals, catalogue choices or Calculation in this diagnostic.'}, ensure_ascii=False)})
    if seen != set(by_id):
        raise ValueError('not all objects have an applicable module; diagnostic stops')
    messages = messages + [{'role': 'assistant', 'content': blocks},
        {'role': 'user', 'content': results + [{'type': 'text', 'text': final_contract}]}]
    final = call('understanding', max_tokens=min(12000, 6000 * len(inputs)), messages=messages,
                 tools=[tool], tool_choice={'type': 'none'})
    parsed = validate_understanding(_json_object(extract_text_from_claude_response(final)), manifests)
    return {'version': VERSION, 'status': 'interpretation_requires_review',
            'module_applications': [b['input'] for b in selected], **parsed}


def report_html(result):
    """Escaped local review artifact, no scripts, network, or production UI."""
    from html import escape
    def e(x): return escape(str(x))
    out = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Estimation V6.2</title>',
           '<style>body{font:16px system-ui;max-width:1050px;margin:40px auto;padding:20px;line-height:1.5}td,th{border:1px solid #ddd;padding:9px;vertical-align:top}table{border-collapse:collapse}small{color:#666}</style>',
           '<h1>Estimation V6.2: object understanding</h1><p>Model interpretation, not an accepted estimate or proof of correctness</p>']
    for application in result.get('classifications', result.get('module_applications', [])):
        if not application.get('island_types'):
            continue
        out += [f'<h2>Island types</h2><small>Input: {e(application["input_id"])}</small>',
            '<table><tr><th>Island</th><th>Type</th></tr>']
        for entry in application['island_types']:
            out.append(f'<tr><td>{e(entry["view_id"])}</td><td>{e(entry["type"])}</td></tr>')
        out.append('</table>')
    for obj in result['objects']:
        out += [f'<h2>{e(obj["summary"])}</h2><p>{e(obj["construction_summary"])}</p>',
                f'<small>Input: {e(obj["input_id"])}</small>', '<h3>Assemblies and functions</h3><table><tr><th>Component</th><th>Function</th><th>Quantity / operation</th><th>Materials and basis</th></tr>']
        for c in obj['components']:
            out.append(f'<tr><td>{e(c["name"])}</td><td>{e(c["function"])}</td><td>{e(c["quantity"])} / {e(c["operation"])}</td><td>{e(c["material_hypothesis"])}<br><small>{e(c["basis"])}</small></td></tr>')
        out += ['</table><h3>Evidence from each view</h3><ul>']
        for v in obj['views']:
            out.append(f'<li>{e(v["id"])}: {e(v["location"])}. {e(v["observation"])}</li>')
        out += ['</ul><h3>Cross-view references</h3><ul>']
        for link in obj['cross_view_links']:
            out.append(f'<li>{e(link["component_id"])} ({e(", ".join(link["view_ids"]))}): {e(link["correspondence"])}</li>')
        out += ['</ul><h3>Uncertainties</h3><ul>']
        out += [f'<li>{e(issue)}</li>' for issue in obj['uncertainties']]
        out += ['</ul>']
    return '\n'.join(out + ['</html>'])


def export_report(witness, path):
    """Retain readable model output even when its transport contract failed."""
    from html import escape
    records = [r for r in witness.get('provider_responses', []) if r['stage'] in {'understanding', 'island_types', 'island_map', 'front_count', 'assembly_plan'}]
    raw = records[-1]['response_text'] if records else 'No model response received'
    try:
        result = witness.get('understanding') or _json_object(raw)
        if 'front_count' in result or 'assembly_plan' in result or 'response_text' in result:
            report = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                '<h1>V6.2: interpretation requires review</h1>'
                '<pre style="white-space:pre-wrap">' + escape(raw) + '</pre></html>')
        else:
            report = report_html(result)
    except (ValueError, KeyError, TypeError):
        report = '<!doctype html><meta charset="utf-8"><h1>V6.2: incomplete response</h1><pre style="white-space:pre-wrap">' + escape(raw) + '</pre>'
    notice = '<p>Status: ' + escape(witness.get('status', 'unknown')) + '</p><p>Evidence: ' + escape(witness.get('evidence_origin', 'unknown')) + '</p>'
    if witness.get('error'):
        notice += '<p>Validation failed: ' + escape(witness['error']) + '</p>'
    if '<h1>' in report:
        report = report.replace('<h1>', notice + '<h1>', 1)
    else:
        report += notice
    Path(path).write_text(report, encoding='utf-8')
