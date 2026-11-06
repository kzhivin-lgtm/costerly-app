"""Opt-in V5 first-cycle experiment, no implicit calls, defaults or DB writes."""
import json
from hashlib import sha256

from agents import estimation_understanding_agent as existing
from use_cases.estimation_cb_cycle_v5 import validate_front, validate_plan, VERSION

FRONT_VERSION = VERSION + ': Understanding + Front'
PLANNER_VERSION = VERSION + ': Planner'
UNDERSTANDING_VERSION = 'Understanding V1'
UNDERSTANDING_V2_VERSION = 'Understanding V2'


def prompt(stage):
    folder = existing.PROMPT_PATH.parent
    if stage in {'understanding', 'understanding_v2'}:
        filename = 'understanding_v1.md' if stage == 'understanding' else 'understanding_v2.md'
        return (folder / filename).read_text().strip()
    inherited = 'cb_front_v3.md' if stage == 'front' else 'cb_planner_v7.md'
    extension = 'cb_cycle_v5_understanding.md' if stage == 'front' else 'cb_cycle_v5_planner.md'
    # The versioned extension is last, explicitly defining the outer contract.
    return (folder / inherited).read_text().strip() + '\n\n' + (folder / extension).read_text().strip()


def _call(stage, content, record, *, parse_json=True, prompt_stage=None):
    request = dict(model=existing.MODEL, max_tokens=14000, output_config={'effort': 'low'},
        thinking={'type': 'disabled'}, system=prompt(prompt_stage or stage), messages=[{'role': 'user', 'content': content}])
    if record:
        record(stage + '_request', request, None)
    response = existing._create_message_with_hard_timeout(
        existing.get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
    if record:
        record({'front': 'front_count', 'planner': 'assembly_plan',
                'understanding': 'understanding'}[stage], request, response)
    if getattr(response, 'stop_reason', None) != 'end_turn':
        raise ValueError('V5 response incomplete')
    text = existing.extract_text_from_claude_response(response)
    if not text.strip():
        raise ValueError('Empty interpretation response')
    parsed = existing._json_object(text) if parse_json else text
    return parsed, sha256(request['system'].encode()).hexdigest()


def run_understanding_v1(*, inputs, page_bytes, record=None):
    """Owner-approved exact prose prompt; no Front contract or continuation."""
    return _run_understanding(inputs=inputs, page_bytes=page_bytes, record=record, revision=1)


def run_understanding_v2(*, inputs, page_bytes, record=None):
    """Focus-only prompt experiment; retain V1 evidence and provider settings."""
    return _run_understanding(inputs=inputs, page_bytes=page_bytes, record=record, revision=2)


def _run_understanding(*, inputs, page_bytes, record, revision):
    version = UNDERSTANDING_VERSION if revision == 1 else UNDERSTANDING_V2_VERSION
    if len(inputs) != 1:
        raise ValueError(f'{version} diagnostic requires exactly one object')
    content, manifests = existing.prepare_content(inputs, page_bytes)
    if not manifests[0]['known_views']:
        raise ValueError(f'{version} requires saved object islands')
    text, digest = _call('understanding', content, record, parse_json=False,
        prompt_stage='understanding' if revision == 1 else 'understanding_v2')
    return dict(version=version,
        status='understanding_text_requires_review_not_estimate',
        prompt_version=version, prompt_sha256=digest,
        input_id=inputs[0]['input_id'], response_text=text)


def run_front_count(*, inputs, page_bytes, record=None, include_supports=True):
    if len(inputs) != 1 or not include_supports:
        raise ValueError('V5 requires one object and the complete Front contract')
    content, manifests = existing.prepare_content(inputs, page_bytes)
    parsed, digest = _call('front', content, record)
    validate_front(parsed, manifests)
    return dict(version=VERSION, status='interpretation_requires_review',
        prompt_version=FRONT_VERSION, prompt_sha256=digest, input_id=inputs[0]['input_id'], front_count=parsed)


def run_assembly_plan(*, inputs, page_bytes, front_result, front_status, record=None):
    content, manifests = existing.prepare_content(inputs, page_bytes)
    validate_front(front_result, manifests)  # no paid continuation from malformed interpretation
    context = dict(saved_front_status=front_status, saved_interpretation=front_result)
    text = json.dumps(context, ensure_ascii=False)
    if len(text) > 100000:
        raise ValueError('V5 interpretation exceeds bound')
    content.append(dict(type='text', text=text))
    parsed, digest = _call('planner', content, record)
    validate_plan(parsed, front_result=front_result, manifests=manifests)
    return dict(version=VERSION, status='interpretation_requires_review',
        prompt_version=PLANNER_VERSION, prompt_sha256=digest, input_id=inputs[0]['input_id'], assembly_plan=parsed)
