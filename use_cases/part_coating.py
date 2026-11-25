"""Owner-calibrated finishing recipes for saved physical front panels.

No model call, catalog selection or new geometry. Areas include two faces and
four edges. Batch setup is inside the approved full-batch norm, never on top.
"""
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re

from use_cases.estimation_front_panels import front_panel_controls, front_material_finish

VERSION = 'part_coating_v1'
HOURLY_RATE = Decimal('100')
CONSUMABLES_RATE = Decimal('10')
RECIPES = {
    'lacquer': {'label': 'Wood lacquer', 'material_rate': 22, 'minutes_per_m2': 40, 'batch_m2': 30, 'setup_hours': 4},
    'enamel': {'label': 'MDF enamel / lacquer', 'material_rate': 16, 'minutes_per_m2': 45, 'batch_m2': 30, 'setup_hours': 4},
    'oil': {'label': 'Wood oil', 'material_rate': 22, 'minutes_per_m2': 35, 'batch_m2': None, 'setup_hours': 0},
}


def _positive(value):
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number > 0 and not isinstance(value, bool) else None
    except Exception:
        return None


def coating_hours(area, recipe):
    area = Decimal(str(area))
    if area <= 0:
        return Decimal(0)
    per_m2 = Decimal(str(recipe['minutes_per_m2'])) / 60
    if not recipe['batch_m2']:
        return area * per_m2
    batch = Decimal(str(recipe['batch_m2']))
    setup = Decimal(str(recipe['setup_hours']))
    full = int(area // batch)
    residual = area - full * batch
    return full * batch * per_m2 + (setup + residual * (per_m2 - setup / batch) if residual else 0)


def _material_effects(source, finish):
    """Use only the part's evidenced material note, not page-wide prose."""
    note = source.get('material_note') or {}
    text = note.get('source_text') or ''
    text = ' '.join(text) if isinstance(text, list) else str(text)
    if not note.get('refs') or finish == 'oil':
        return Decimal(1), []
    effects = []
    if re.search(r'глянцев|high[ -]?gloss|glossy|מבריק', text, re.I):
        effects.append(('gloss', Decimal(2)))
    if finish == 'lacquer' and re.search(r'патин|patina|פטינה', text, re.I):
        effects.append(('patina', Decimal(2)))
    if re.search(r'фил[её]нчат|panelled facade|paneled facade|raised[ -]panel', text, re.I):
        effects.append(('profiled_facade', Decimal('1.1')))
    multiplier = Decimal(1)
    if len(effects) > 1:
        return None, [name for name, _ in effects]
    for _, factor in effects:
        multiplier *= factor
    return multiplier, [name for name, _ in effects]


def calculate_part_coating(plan, *, object_id, source_lines=(), report=None, machinery=None):
    """Return a reproducible recipe audit, with unknown geometry kept unknown."""
    groups = front_panel_controls(plan, source_lines, object_id)
    # Front selections override their original stock. Other unfinished wood
    # parts retain their saved substrate, including decorative Ada panels.
    front_ids = {part for group in groups for part in group['part_ids']}
    facts = [(line.get('raw_agent_json') or {}).get('facts') for line in source_lines
             if isinstance(line.get('raw_agent_json'), dict)]
    for fact in facts:
        if not fact or fact.get('unit') or fact.get('material_role') not in {'visible_sheet', 'carcass_sheet', 'internal_sheet'}:
            continue
        spec = fact.get('specification') or {}
        family, surface = fact.get('family'), str(spec.get('surface') or '')
        choice = None
        if family == 'mdf_hdf' and spec.get('board_type') != 'hdf':
            choice = 'veneered_mdf' if 'veneer' in surface else 'mdf' if surface in {'raw', ''} else None
        elif family in {'plywood', 'plywood_special'} and not surface:
            choice = 'plywood'
        other = [s for s in fact.get('part_sources', ()) if s['part_id'] not in front_ids]
        if choice and other:
            groups.append({'choice': choice, 'part_sources': other, 'part_ids': [s['part_id'] for s in other]})
    sources = {}
    if report:
        counts = Counter()
        for row in (report.get('objects', {}).get(object_id) or {}).get('parts', ()):
            counts[row['owner_id']] += 1
            sources[f"{row['owner_id']}:{row['role']}:{counts[row['owner_id']]:03d}"] = row
    for line in source_lines:
        raw = line.get('raw_agent_json')
        if isinstance(raw, dict):
            sources.update({s['part_id']: s for s in (raw.get('facts') or {}).get('part_sources', ())})
    object_quantity = Decimal(str((plan.get('object_quantities') or {}).get(object_id, 1)))
    rows, issues, material_issues, seen = [], [], [], set()
    areas = {key: Decimal(0) for key in RECIPES}
    material_totals = {key: Decimal(0) for key in RECIPES}
    for group in groups:
        finish = front_material_finish(group['choice'])
        if finish is None:
            continue
        local = {s['part_id']: s for s in group.get('part_sources', ())}
        for part_id in group['part_ids']:
            if part_id in seen:
                continue
            seen.add(part_id)
            source = local.get(part_id) or sources.get(part_id) or {}
            dims = source.get('measurements') or source.get('dimensions') or {}
            values = [_positive((dims.get(axis) or {}).get('mm')) for axis in ('length', 'width', 'thickness')]
            # Saved source counts exclude layup layers and include assembly scope.
            if 'source_quantity' in source:
                count = _positive(source['source_quantity'])
                count = count * Decimal(str(source.get('scope_quantity', 1))) * object_quantity if count else None
            else:
                count = _positive(source.get('quantity'))
                if report and part_id not in local and 'part_id' not in source and count:
                    owner = source.get('owner_id')
                    scopes = {b['id']: b.get('quantity', 1) for b in (report['objects'][object_id].get('blocks') or ())}
                    count *= object_quantity * Decimal(str(source.get('scope_quantity', scopes.get(owner, 1))))
            if not count or not all(values):
                issues.append({'part_id': part_id, 'issue': 'coating_geometry_unresolved'})
                continue
            length, width, thickness = (value / 1000 for value in values)
            area = count * (2 * length * width + 2 * thickness * (length + width))
            areas[finish] += area
            multiplier, effects = _material_effects(source, finish)
            if multiplier is None:
                material_issues.append({'part_id': part_id, 'issue': 'combined_finish_effects_unapproved'})
            else:
                material_totals[finish] += area * RECIPES[finish]['material_rate'] * multiplier
            rows.append({'part_id': part_id, 'finish': finish, 'quantity': float(count), 'area_m2': float(area),
                         'material_multiplier': str(multiplier) if multiplier is not None else None, 'material_effects': effects,
                         'evidence_refs': list(dict.fromkeys([*(source.get('evidence_refs') or source.get('refs') or []),
                              *((source.get('material_note') or {}).get('refs') or [])]))})
    availability = (machinery or {}).get('availability', {}).get('finish_wet_spray_booth')
    batches = []
    for finish, area in areas.items():
        if not area:
            continue
        recipe = RECIPES[finish]
        route = 'hand_application' if finish == 'oil' else 'in_house' if availability == 'in_house' else availability or 'unknown'
        hours = coating_hours(area, recipe) if route in {'hand_application', 'in_house'} else None
        unknown_material = any(row['finish'] == finish and row['material_multiplier'] is None for row in rows)
        batches.append({'finish': finish, **recipe, 'area_m2': float(area), 'hours': str(hours) if hours is not None else None,
                        'route': route, 'material_cost': None if unknown_material else float(material_totals[finish].quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
                        'effective_material_rate': None if unknown_material else float(material_totals[finish] / area)})
    audit = {'version': VERSION, 'parts': rows, 'batches': batches, 'issues': issues, 'material_issues': material_issues,
             'area_m2': float(sum(areas.values())), 'hourly_rate': str(HOURLY_RATE),
             'consumables_rate': str(CONSUMABLES_RATE), 'booth_availability': availability}
    audit['partial'] = bool(issues or any(b['hours'] is None for b in batches))
    audit['hours'] = (str(sum((Decimal(b['hours']) for b in batches if b['hours'] is not None), Decimal(0)))
                      if not audit['partial'] else None)
    audit['basis_sha256'] = hashlib.sha256(json.dumps(audit, sort_keys=True).encode()).hexdigest()
    return audit


def coating_material_rows(audit):
    rows = [{'item': batch['label'], 'material_family': 'wood_coatings', 'price_source': 'A',
             'is_coating': True, 'coating_recipe': True, 'required_material_value': batch['area_m2'],
             'required_material_unit': 'm²', 'purchase_unit': 'm²', 'purchase_quantity_value': batch['area_m2'],
             'purchase_unit_cost': batch['effective_material_rate'], 'total': batch['material_cost']}
            for batch in audit['batches']]
    if rows or audit['issues']:
        if audit['issues']:
            rows.append({'item': 'Unresolved coating area', 'coating_recipe': True, 'is_coating': True, 'total': None})
        rows.append({'item': 'Coating consumables', 'locked': True, 'policy_basis': 'coating_area',
                     'policy_description': '₪10/m² of coated area', 'coating_recipe': True,
                     'required_material_value': audit['area_m2'], 'policy_rate': 10,
                     'total': float((Decimal(str(audit['area_m2'])) * CONSUMABLES_RATE).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))})
    return rows
