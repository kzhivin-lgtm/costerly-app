"""Replay real Detection evidence through explicit module invocation, locally only."""
import argparse
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import tomllib

from agents.estimation_understanding_agent import run_understanding_with_modules, run_island_types_only, run_front_count, export_report
from agents.estimation_understanding_agent import FRONT_COUNT_PROMPT_VERSION, FRONT_SUPPORTS_PROMPT_VERSION, PLANNER_PROMPT_VERSION, run_assembly_plan
from agents.estimation_v4_1_material_facts_agent import _json_object


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--replay', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--execute', action='store_true')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--classify-only', '--map-only', dest='classify_only', action='store_true', help='One isolated classification call, no module continuation')
    mode.add_argument('--count-fronts', action='store_true', help='One combined classification/front-count experiment')
    mode.add_argument('--plan-assemblies', action='store_true', help='One Planner call using an existing Front witness')
    p.add_argument('--front-witness', type=Path, help='Saved Front output for the exact same evidence; no fresh Front call')
    p.add_argument('--front-supports', action='store_true', help='Opt into experimental CB Front V2; requires --count-fronts')
    args = p.parse_args()
    if not args.execute:
        p.error('Explicit --execute required for paid calls')
    if args.front_supports and not args.count_fronts:
        p.error('--front-supports requires --count-fronts')
    front_version = FRONT_SUPPORTS_PROMPT_VERSION if args.front_supports else FRONT_COUNT_PROMPT_VERSION
    if args.output.exists() or args.output.with_suffix('.html').exists():
        p.error('Refuse to overwrite witness')
    if args.output.with_name(args.output.stem + '-assembly_plan-raw.txt').exists():
        p.error('Refuse to overwrite raw Planner response')
    if bool(args.front_witness) != args.plan_assemblies:
        p.error('--front-witness is required only with --plan-assemblies')
    for k, v in tomllib.loads(Path('/Users/qb/costerly-app/.streamlit/secrets.toml').read_text()).items():
        if isinstance(v, (str, int, float)):
            os.environ.setdefault(k, str(v))
    prior = json.loads(args.replay.read_text())
    front_witness = None
    if args.plan_assemblies:
        front_witness = json.loads(args.front_witness.read_text())
        if any(front_witness.get(k) != prior.get(k) for k in ('inputs', 'source_pages_base64')):
            p.error('Front witness must contain the exact same immutable inputs and page bytes')
        front_record = next(r for r in reversed(front_witness['provider_responses']) if r['stage'] == 'front_count')
        front_result = _json_object(front_record['response_text'])
    w = {k: prior[k] for k in ('inputs', 'source_pages_base64', 'evidence_origin')}
    w.update(version='v6.2', route='island_types_cabinet_module_haiku55_diagnostic', database_writes=False,
        status='running', replay_source=str(args.replay), provider_responses=[])
    if args.classify_only:
        w['route'] = 'island_types_only_diagnostic'
    elif args.count_fronts:
        w['route'] = 'island_types_front_count_haiku55_diagnostic'
        w['prompt_version'] = front_version
    elif args.plan_assemblies:
        w.update(route='cb_planner_saved_front_diagnostic', prompt_version=PLANNER_PROMPT_VERSION,
            front_witness=str(args.front_witness), front_witness_sha256=sha256(args.front_witness.read_bytes()).hexdigest(),
            front_status=front_witness['status'], front_prompt_version=front_record.get('prompt_version'))
    def save():
        args.output.write_text(json.dumps(w, ensure_ascii=False, indent=2))
    started = time.monotonic()
    def record(stage, request, response):
        raw = response.model_dump(mode='json')
        text = '\n'.join(b['text'] for b in raw['content'] if b['type'] == 'text')
        prompt_identity = ({'prompt_version': PLANNER_PROMPT_VERSION if stage == 'assembly_plan' else front_version,
            'prompt_sha256': sha256(request['system'].encode()).hexdigest()}
            if stage in {'front_count', 'assembly_plan'} else {})
        w.update(prompt_identity)
        w['provider_responses'].append({'stage': stage, 'request': request,
            **prompt_identity,
            'request_sha256': sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
            'response': raw, 'response_text': text, 'usage': raw.get('usage'),
            'elapsed_from_start': round(time.monotonic() - started, 3)})
        # Text-only answer is byte-preserved; tool arguments are retained as
        # original response JSON, not an assistant paraphrase.
        args.output.with_name(args.output.stem + '-' + stage + '-raw.txt').write_text(
            text if stage in {'understanding', 'island_types', 'front_count', 'assembly_plan'} else json.dumps(raw['content'], ensure_ascii=False, indent=2))
        save()
        print(json.dumps({'stage': stage, 'stop_reason': raw.get('stop_reason'),
                          'elapsed_seconds': round(time.monotonic() - started, 3)}), flush=True)
    save()
    try:
        run = run_assembly_plan if args.plan_assemblies else run_front_count if args.count_fronts else run_island_types_only if args.classify_only else run_understanding_with_modules
        extra = {'front_result': front_result, 'front_status': front_witness['status']} if args.plan_assemblies else {}
        if args.count_fronts:
            extra['include_supports'] = args.front_supports
        w['understanding'] = run(inputs=w['inputs'],
            page_bytes={k: base64.b64decode(v) for k, v in w['source_pages_base64'].items()}, record=record, **extra)
        w['status'] = ('assembly_plan_requires_review' if args.plan_assemblies else 'front_count_requires_review' if args.count_fronts else
            'island_types_require_review' if args.classify_only else 'understanding_requires_review_not_estimate')
    except Exception as exc:
        w['status'] = 'failed'
        w['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        w['elapsed_seconds'] = round(time.monotonic() - started, 3)
        save()
        export_report(w, args.output.with_suffix('.html'))
    print(json.dumps({k: w.get(k) for k in ('status', 'elapsed_seconds', 'error')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
