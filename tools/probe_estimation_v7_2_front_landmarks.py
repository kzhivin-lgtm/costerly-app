"""Owner-selected V7.2 research checkpoint; never changes the runtime default."""
import argparse
import json
import os
from pathlib import Path
import time
import tomllib

from agents import estimation_analyze_v7_2_agent as analyze
from agents.estimation_understanding_agent import (
    _create_message_with_hard_timeout, _json_object, get_anthropic_client,
)
from tools.probe_estimation_analyze_v7 import render_report
from tools.probe_estimation_v7_2_thinking import front_crop_sizes, normalize_front_pixel_boxes
from use_cases.estimation_detection_context_v7 import digest

EDITS = (
    ('Do not force one facade to be the main front of a corner item. Brief observation\n'
     'identifies the visible evidence; do not reproduce a dimension narrative.',
     'Do not force one facade to be the main front of a corner item.'),
    (', "observation": "Visible evidence"', ''),
    ('For EACH individual counted physical front, return one bounding box on ONE\n'
     'supplied enlarged island image, choosing the clearest view.',
     'For EACH individually identified physical front, return one entry on ONE\n'
     'supplied enlarged island image, choosing the clearest view. State a short\n'
     'visible landmark identifying that distinct surface, not the whole group.\n'
     'Give its bounding box if the boundaries can be located; otherwise keep\n'
     'the entry and return bbox_px: null. Do not invent a box.'),
    ('For a known group count, the number of individual front boxes must equal count.',
     'For any numeric group count, including estimated, the number of individual front entries must equal count.'),
    ('If a group count is undetermined, annotate only fronts you can locate;',
     'If a group count is undetermined, list only individually identified fronts;'),
    ('"fronts": [{"id": "F01", "view_id": "Detection ID", "bbox_px": [100,200,200,400]}]',
     '"fronts": [{"id": "F01", "view_id": "Detection ID", "landmark": "visible location of this individual face", "bbox_px": [100,200,200,400]}]'),
)


def landmark_request(saved):
    request = saved['provider_request']
    if (saved['version'] != analyze.VERSION or saved.get('stop_reason') != 'end_turn'
            or saved['request_sha256'] != digest(request)
            or request.get('thinking') != {'type': 'disabled'}
            or request.get('output_config') != {'effort': 'medium'} or request.get('max_tokens') != 14000
            or saved['detection_context']['contract_version'] != 'estimation_detection_context_v7_2'):
        raise ValueError('requires a saved V7.2 medium pixel control')
    prompt = request['system']
    for before, after in EDITS:
        if prompt.count(before) != 1:
            raise ValueError('unexpected original pixel control prompt')
        prompt = prompt.replace(before, after, 1)
    return {**request, 'system': prompt}


def validate_landmark_result(raw, witness):
    normalized = normalize_front_pixel_boxes(raw, witness['front_crop_sizes_px'], allow_unlocalized_fronts=True)
    return analyze.validate_result(normalized, detection_context=witness['detection_context'],
        inputs=witness['inputs'], island_observation_required=False, allow_unlocalized_fronts=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--compare', type=Path, help='verify byte-identical saved provider request, locally')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true', help='one provider call, no retries')
    args = parser.parse_args()
    saved = json.loads(args.baseline.read_text())
    request = landmark_request(saved)
    if args.compare:
        expected = json.loads(args.compare.read_text())
        if request != expected['provider_request'] or digest(request) != expected['request_sha256']:
            raise ValueError('checkpoint request differs from saved witness')
    witness = {k: saved[k] for k in ('version', 'inputs', 'detection_context', 'preflight')}
    witness.update(status='prepared_no_provider_calls', strict_island_map=True, provider_calls=0,
        calculate_calls=0, database_writes=False, provider_request=request, request_sha256=digest(request),
        control_path=str(args.baseline), control_request_sha256=saved['request_sha256'],
        front_crop_sizes_px=front_crop_sizes(request))
    if not args.execute:
        print(json.dumps({k: witness[k] for k in ('status', 'provider_calls', 'preflight', 'request_sha256')}))
        return
    output = args.output
    if not output or any(p.exists() for p in (output, output.with_suffix('.raw.txt'), output.with_suffix('.html'))):
        parser.error('--execute needs a new --output path')
    for key, value in tomllib.loads(Path('/Users/qb/costerly-app/.streamlit/secrets.toml').read_text()).items():
        if isinstance(value, (str, int, float)):
            os.environ.setdefault(key, str(value))
    witness.update(status='provider_request_pending', provider_calls=1)
    with output.open('x') as handle:
        json.dump(witness, handle, ensure_ascii=False, indent=2)
    started = time.monotonic()
    try:
        response = _create_message_with_hard_timeout(
            get_anthropic_client().with_options(timeout=120, max_retries=0), timeout_seconds=120, **request)
        raw = response.model_dump(mode='json')
        body = '\n'.join(b['text'] for b in raw['content'] if b['type'] == 'text')
        witness.update(provider_response=raw, raw_response_text=body, usage=raw['usage'], stop_reason=raw['stop_reason'])
        output.with_suffix('.raw.txt').write_text(body)
        if raw['stop_reason'] != 'end_turn':
            raise ValueError('incomplete provider response')
        witness['result'] = validate_landmark_result(_json_object(body), witness)
        witness['status'] = 'analyze_requires_semantic_review'
    except Exception as exc:
        witness.update(status='failed', error=f'{type(exc).__name__}: {exc}')
    finally:
        witness['elapsed_seconds'] = round(time.monotonic() - started, 3)
        output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
        output.with_suffix('.html').write_text(render_report(witness))
    print(json.dumps({k: witness.get(k) for k in ('status', 'provider_calls', 'elapsed_seconds', 'error')}))


if __name__ == '__main__':
    main()
