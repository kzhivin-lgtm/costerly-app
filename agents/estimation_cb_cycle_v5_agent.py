"""Opt-in V5 first-cycle experiment, no implicit calls, defaults or DB writes."""
import json
from hashlib import sha256

from agents import estimation_understanding_agent as existing
from use_cases.estimation_cb_cycle_v5 import validate_front, validate_plan, VERSION

FRONT_VERSION = VERSION + ': Understanding + Front'
PLANNER_VERSION = VERSION + ': Planner'


def prompt(stage):
    folder = existing.PROMPT_PATH.parent
    inherited = 'cb_front_v3.md' if stage == 'front' else 'cb_planner_v7.md'
    extension = 'cb_cycle_v5_understanding.md' if stage == 'front' else 'cb_cycle_v5_planner.md'
    # The versioned extension is last, explicitly defining the outer contract.
    return (folder / inherited).read_text().strip() + '\n\n' + (folder / extension).read_text().strip()


def _call(stage, content, record):
    request = dict(model=existing.MODEL, max_tokens=14000, output_config={'effort': 'low'},
        thinking={'type': 'disabled'}, system=prompt(stage), messages=[{'role': 'user', 'content': content}])
    if record:
        record(stage + '_request', request, None)
    response = existing._create_message_with_hard_timeout(
        existing.get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
    if record:
        record('front_count' if stage == 'front' else 'assembly_plan', request, response)
    if getattr(response, 'stop_reason', None) != 'end_turn':
        raise ValueError('V5 response incomplete')
    parsed = existing._json_object(existing.extract_text_from_claude_response(response))
    return parsed, sha256(request['system'].encode()).hexdigest()


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
