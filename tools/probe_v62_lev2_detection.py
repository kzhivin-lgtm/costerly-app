"""Local diagnostic from persisted Detection evidence. Never writes to the DB."""
import argparse
import base64
import copy
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import time
import tomllib

from PIL import Image
from agents.anthropic_adapter import build_detection_page_evidence_inventory
from agents.detection_page_images import render_detection_pdf_pages
import agents.estimation_understanding_agent as understanding
from db.supabase_client import get_supabase_client
from tools.replay_estimation_v6 import capture_provider_responses
from use_cases.estimation_evidence import build_estimation_input, EvidenceArtifact

RUN = 'run_189150ebf62447fc958f7c23cc34e3bb'
EVENT = '8fd1c7f0-2f36-42bd-b7ae-537460324445'
OCR = '29b1d88e-3848-4046-b4b5-662a03fc6869'
ROOT = Path('/private/tmp/estimation-v6-2-lev2-detection-01')


def main():
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--replay', type=Path, help='Reuse exact local evidence and grouping context; fresh output required')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        ROOT = args.output.with_suffix('')
    for k, v in tomllib.loads(Path('/Users/qb/costerly-app/.streamlit/secrets.toml').read_text()).items():
        if isinstance(v, (str, int, float)):
            os.environ.setdefault(k, str(v))
    output = ROOT.with_suffix('.json')
    if args.replay:
        if not args.execute or not args.output or output.exists():
            raise ValueError('Replay requires --execute and fresh --output')
        prior = json.loads(args.replay.read_text())
        witness = {k: prior[k] for k in ('version', 'database_writes', 'evidence_origin',
            'inputs', 'source_pages_base64', 'upstream_grouping_context', 'original_sha256', 'preflight')}
        witness.update(status='prepared_no_provider_calls', replay_source=str(args.replay))
        output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
    if not args.execute:
        if output.exists():
            raise ValueError('Refuse to overwrite witness')
        c = get_supabase_client()
        events = c.table('agent_usage_events').select('id,run_id,raw_usage').eq('company_id', '610').in_('id', [EVENT, OCR]).execute().data
        by_id = {r['id']: r for r in events}
        assert set(by_id) == {EVENT, OCR} and all(r['run_id'] == RUN for r in events)
        audit = by_id[EVENT]['raw_usage']
        ocr = by_id[OCR]['raw_usage']['ocr_result']
        objects = c.table('rfq_detected_objects').select('*').eq('company_id', '610').eq('run_id', RUN).execute().data
        assert len(objects) == 1 and objects[0]['object_id'] == 'object-001'
        original = Path('/Users/qb/Desktop/SAMPLES/JOLD/Lev 2.pdf').read_bytes()
        assert sha256(original).hexdigest() == ocr['file_sha256']
        rendered, _ = render_detection_pdf_pages(original)
        assert len(rendered) == 1
        page = Image.open(BytesIO(rendered[0]))
        page.save(ROOT.with_suffix('.png'))
        buf = BytesIO()
        page.save(buf, format='WEBP', quality=95)
        page_bytes = buf.getvalue()
        # Builder validates the usual transport. Replace the placeholder with
        # an explicitly LOCAL locator; no storage artifact is claimed or uploaded.
        payload = build_estimation_input(run={'run_id': RUN, 'company_id': '610', 'file_name': 'Lev 2.pdf'},
            detected_object=objects[0], ocr_event_id=OCR, ocr_package=ocr,
            evidence_artifacts=[EvidenceArtifact('storage://rfq-estimation-evidence/local-diagnostic/p1', 1, 'page')],
            versions={'diagnostic': 'v6.2_detection_grounded_local_fixture'})
        ref = 'local-render:' + sha256(page_bytes).hexdigest() + ':p1'
        payload['evidence']['artifacts'][0]['storage_ref'] = ref
        payload['input_origin'] = 'persisted_detection_local_fixture_not_persisted_input'
        row = {'input_id': 'local-detection:' + RUN + ':object-001', 'input_payload': payload}
        content, manifests = understanding.prepare_content([row], {ref: page_bytes})
        groups = audit['v5_9_proposal_decision_audit']['visual_groups']
        views = manifests[0]['known_views']
        mapping = {}
        for group in groups:
            matches = [v for v in views if v['page_number'] == group['page_number'] and v['bbox'] == group['bbox']]
            assert len(matches) == 1, 'No exact source-box mapping'
            mapping[group['group_id']] = matches[0]['view_id']
        facts = build_detection_page_evidence_inventory(ocr)
        source_text = payload['evidence']['ocr_blocks'] + payload['evidence']['ocr_literal_items']
        fact_mapping = {}
        for fact in facts:
            matches = [x for x in source_text if x.get('page_number') == fact['page_number']
                       and x.get('text') == fact['text'] and x.get('bbox') == fact['bbox']]
            assert len(matches) == 1
            fact_mapping[fact['fact_id']] = matches[0]['block_ref']
        grounds = copy.deepcopy(audit['v5_9_review_decision_audit'])
        assert set(grounds) == {'object_hypotheses', 'presentation_render_decisions'}
        def check_refs(value):
            if isinstance(value, dict):
                for key, val in value.items():
                    if key in ('group_ids', 'source_fact_ids'):
                        for token in val:
                            assert token in mapping or token in fact_mapping or token.removeprefix('registry_view:') in mapping
                    elif key in ('render_group_id', 'technical_group_id'):
                        assert val in mapping
                    check_refs(val)
            elif isinstance(value, list):
                for val in value:
                    check_refs(val)
        check_refs(grounds)
        upstream = {'input_id': row['input_id'], 'detection_event_id': EVENT,
            'authority': 'Fallible prior model interpretation, not source facts. Use only as grouping context; re-evaluate physical/geometry claims against all images and OCR. Do not change locked membership. Naming is not supplied.',
            'view_id_mapping': mapping, 'source_fact_mapping': fact_mapping,
            'membership_observations': grounds}
        witness = {'version': 'v6.2', 'status': 'prepared_no_provider_calls', 'database_writes': False,
            'evidence_origin': 'persisted_detection_local_fixture_not_persisted_input',
            'inputs': [row], 'source_pages_base64': {ref: base64.b64encode(page_bytes).decode()},
            'upstream_grouping_context': upstream, 'original_sha256': ocr['file_sha256'],
            'preflight': {'image_count': sum(x['type'] == 'image' for x in content),
                          'view_count': len(views), 'ocr_count': len(source_text),
                          'view_mapping_exact': True, 'naming_in_manifest': 'object_name' in manifests[0]}}
        assert witness['preflight'] == {'image_count': 5, 'view_count': 4, 'ocr_count': 18, 'view_mapping_exact': True, 'naming_in_manifest': False}
        output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
        print(json.dumps(witness['preflight']))
        return
    witness = json.loads(output.read_text())
    assert witness['status'] == 'prepared_no_provider_calls', 'Do not repeat charged call'
    original_prepare = understanding.prepare_content
    def with_grounding(inputs, page_bytes):
        content, manifests = original_prepare(inputs, page_bytes)
        content.append({'type': 'text', 'text': json.dumps({'upstream_grouping_context': witness['upstream_grouping_context']}, ensure_ascii=False)})
        return content, manifests
    understanding.prepare_content = with_grounding
    def save():
        output.write_text(json.dumps(witness, ensure_ascii=False, indent=2, default=str))
    witness['status'] = 'running'
    save()
    started = time.monotonic()
    try:
        with capture_provider_responses(witness, save, allow_calls=True):
            witness['understanding'] = understanding.run_understanding(inputs=witness['inputs'],
                page_bytes={k: base64.b64decode(v) for k, v in witness['source_pages_base64'].items()})
        witness['status'] = 'understanding_requires_review_not_estimate'
    except Exception as exc:
        witness['status'] = 'failed'
        witness['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        understanding.prepare_content = original_prepare
        witness['elapsed_seconds'] = round(time.monotonic() - started, 3)
        save()
        understanding.export_report(witness, ROOT.with_suffix('.html'))
    print(json.dumps({k: witness.get(k) for k in ('status', 'elapsed_seconds', 'error', 'understanding')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
