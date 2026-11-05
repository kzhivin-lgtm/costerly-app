"""V6.2 first-cycle-only understanding. Not a BOM or production replacement."""
import json
from pathlib import Path

from agents.estimation_composition_analyze_agent import _page_manifest
from agents.estimation_visual_evidence import page_content
from agents.anthropic_adapter import get_anthropic_client, extract_text_from_claude_response
from agents.estimation_v4_1_material_facts_agent import _create_message_with_hard_timeout, _json_object
from use_cases.estimation_dimension_graph import build_dimension_graph

VERSION = "estimation_understanding_v6_2"
MODEL = "claude-haiku-4-5-20251001"
PROMPT_PATH = Path(__file__).parent / "prompts" / "estimation_understanding_v6_2.md"


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
        timeout_seconds=60, model=MODEL, max_tokens=min(12000, 3500 * len(inputs)), temperature=0,
        system=PROMPT_PATH.read_text().strip(), messages=[{'role': 'user', 'content': content}])
    parsed = validate_understanding(_json_object(extract_text_from_claude_response(response)), manifests)
    return {'version': VERSION, 'status': 'interpretation_requires_review', **parsed}


def report_html(result):
    """Escaped local review artifact, no scripts, network, or production UI."""
    from html import escape
    def e(x): return escape(str(x))
    out = ['<!doctype html><html lang="ru"><meta charset="utf-8"><title>Estimation V6.2</title>',
           '<style>body{font:16px system-ui;max-width:1050px;margin:40px auto;padding:20px;line-height:1.5}td,th{border:1px solid #ddd;padding:9px;vertical-align:top}table{border-collapse:collapse}small{color:#666}</style>',
           '<h1>Estimation V6.2: понимание предмета</h1><p>Интерпретация модели. Не принятый расчёт и не доказательство правильности</p>']
    for obj in result['objects']:
        out += [f'<h2>{e(obj["summary"])}</h2><p>{e(obj["construction_summary"])}</p>',
                f'<small>Input: {e(obj["input_id"])}</small>', '<h3>Узлы и функции</h3><table><tr><th>Узел</th><th>Функция</th><th>Количество / действие</th><th>Материалы и основание</th></tr>']
        for c in obj['components']:
            out.append(f'<tr><td>{e(c["name"])}</td><td>{e(c["function"])}</td><td>{e(c["quantity"])} / {e(c["operation"])}</td><td>{e(c["material_hypothesis"])}<br><small>{e(c["basis"])}</small></td></tr>')
        out += ['</table><h3>Что добавляет каждый вид</h3><ul>']
        for v in obj['views']:
            out.append(f'<li>{e(v["id"])}: {e(v["location"])}. {e(v["observation"])}</li>')
        out += ['</ul><h3>Сопоставление видов</h3><ul>']
        for link in obj['cross_view_links']:
            out.append(f'<li>{e(link["component_id"])} ({e(", ".join(link["view_ids"]))}): {e(link["correspondence"])}</li>')
        out += ['</ul><h3>Неопределённости</h3><ul>']
        out += [f'<li>{e(issue)}</li>' for issue in obj['uncertainties']]
        out += ['</ul>']
    return '\n'.join(out + ['</html>'])


def export_report(witness, path):
    """Retain readable model output even when its transport contract failed."""
    from html import escape
    records = [r for r in witness.get('provider_responses', []) if r['stage'] == 'understanding']
    raw = records[-1]['response_text'] if records else 'No model response received'
    try:
        result = witness.get('understanding') or _json_object(raw)
        report = report_html(result)
    except (ValueError, KeyError, TypeError):
        report = '<!doctype html><meta charset="utf-8"><h1>V6.2: неполный ответ</h1><pre style="white-space:pre-wrap">' + escape(raw) + '</pre>'
    notice = '<p>Status: ' + escape(witness.get('status', 'unknown')) + '</p><p>Evidence: ' + escape(witness.get('evidence_origin', 'unknown')) + '</p>'
    if witness.get('error'):
        notice += '<p>Ответ не прошёл проверку: ' + escape(witness['error']) + '</p>'
    if '<h1>' in report:
        report = report.replace('<h1>', notice + '<h1>', 1)
    else:
        report += notice
    Path(path).write_text(report, encoding='utf-8')
