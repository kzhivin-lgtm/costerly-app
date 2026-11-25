"""Replace front demands inside the saved purchase plan, without rebuilding Parts."""
from collections import defaultdict
from copy import deepcopy
from decimal import Decimal

from use_cases.estimation_front_panels import FRONT_MATERIALS, front_panel_controls, validate_front_choices, front_material_base
from use_cases.material_engine import MaterialSupplyCandidate, plan_material_purchases
from use_cases.material_engine_adapter import (
    MaterialEngineResult, _snapshot_material_demands, _snapshot_allocation_weight, _split_purchase_cost,
    build_material_plan, material_plan_snapshot, material_review_purchases,
)


def _line_costs(line):
    weights = defaultdict(Decimal)
    for row in line['allocations']:
        weights[row['object_id'], row['material_requirement_id']] += _snapshot_allocation_weight(row)
    if 'object_purchases' not in line:
        return _split_purchase_cost(Decimal(str(line['total_cost'])), weights)
    result = {}
    for oid, purchase in line['object_purchases'].items():
        result.update(_split_purchase_cost(Decimal(str(purchase['total'])),
                                          {key: value for key, value in weights.items() if key[0] == oid}))
    return result


def _replan_line(line, snapshot):
    candidate = MaterialSupplyCandidate(
        candidate_id=line['candidate_id'], material_family=line['selection_key'].split('|', 1)[0],
        selection_key=line['selection_key'], purchase_kind=line['purchase_kind'],
        price_per_purchase_unit=line['price_per_purchase_unit'], currency=line['currency'],
        purchasable_dimensions=line.get('purchasable_dimensions'), package_quantity=line.get('package_quantity') or 1,
        kerf_mm=line.get('kerf_mm', 0), authority=line['authority'], display_name=line['display_name'],
        label_specifications=line.get('label_specifications'),
    )
    demands = _snapshot_material_demands(line, candidate, {}, {}, {}, ({}, {}))
    if not demands:
        raise ValueError('The saved front purchase geometry is unavailable.')
    plan = plan_material_purchases(demands=demands, candidates=(candidate,))
    if plan.status != 'planned':
        raise ValueError('The selected purchase format cannot cover the front panels.')
    result = material_plan_snapshot(MaterialEngineResult(
        plan=plan, demand_count=len(demands), candidate_count=1,
        candidate_authorities=((candidate.candidate_id, line['authority']),),
        candidate_display_names=((candidate.candidate_id, line['display_name']),),
        candidate_purchase_forms=((candidate.candidate_id, line),),
    ))
    if snapshot.get('material_review_order') is not None:
        result = material_review_purchases(result, review_order=snapshot['material_review_order'],
                                          overrides=snapshot.get('review_purchase_overrides', {}))
    return result['lines'][0]


def front_group_material(group, choice, *, object_quantity):
    """Change only a selected group's stock identity, using its saved physical fronts."""
    sources = deepcopy(group['part_sources'])
    restoring = choice == 'source' or front_material_base(choice) == group.get('source_choice')
    if restoring:
        name, family, spec = group['source_name'], group['family'], dict(group['specification'])
    else:
        name, family, spec = FRONT_MATERIALS[choice]
        spec = dict(spec)
        explicit = [source.get('dimensions', {}).get('thickness', {}) for source in sources]
        explicit = [value for value in explicit if value.get('mm') and value.get('basis')
                    and value['basis'] != 'unknown' and 'assumption' not in value['basis']
                    and 'default' not in value['basis']]
        if explicit:
            spec['thickness_mm'] = explicit[0]['mm']
    requirement = group.get('front_requirement_id') or (group['id'] + '-front' if group.get('mixed') else group['id'])
    material = {'requirement_id': requirement, 'source_name': name, 'family': family,
                'specification': spec, 'material_role': 'visible_sheet', 'material_class': 'front_panels',
                'basis': 'source_evidence' if restoring else 'user_selection', 'unit': None, 'quantity': None,
                'part_sources': sources, 'evidence_refs': []}
    parts = []
    for source in sources:
        dims = source.get('measurements') or source['dimensions']
        parts.append({'part_id': source['part_id'], 'material_requirement_id': requirement,
                      'component_role': source['role'], 'block_id': source.get('block_id'),
                      'quantity': source['quantity'], 'length_mm': dims['length']['mm'], 'width_mm': dims['width']['mm'],
                      'rotation_allowed': False,
                      'cnc_rotation_allowed': choice == 'mdf', 'basis': 'source_evidence'})
    return material, parts


def patch_front_material_plan(previous, *, object_id, source_lines, choices, contexts):
    """Reprice selected fronts plus only the stock baskets they leave or join."""
    snapshot = deepcopy(previous)
    groups = front_panel_controls(previous, source_lines, object_id)
    validate_front_choices(groups, choices)
    source_facts = [row.get('raw_agent_json', {}).get('facts', {}) for row in source_lines
                    if isinstance(row.get('raw_agent_json'), dict)]
    facts_by_id = {row.get('requirement_id'): row for row in source_facts if row.get('requirement_id')}
    updated_materials, changed_keys, changed_owners = {}, set(), set()
    finish_changed = False
    new_lines = []
    stored_groups = []
    quantity = previous.get('object_quantities', {}).get(object_id, 1)
    for initial in groups:
        group = deepcopy(initial)
        part_ids = set(group['part_ids'])
        if not group.get('part_sources'):
            sources = {source['part_id']: source for fact in source_facts for source in fact.get('part_sources', ())
                       if source.get('part_id') in part_ids}
            if set(sources) != part_ids:
                raise ValueError('The saved front source geometry is not available.')
            group['part_sources'] = list(sources.values())
        choice = choices.get(group['id'])
        if choice is None or choice == group.get('choice'):
            stored_groups.append(group)
            continue
        current = group.get('choice') or group.get('source_choice')
        effective = group.get('source_choice') if choice == 'source' else choice
        if front_material_base(effective) == front_material_base(current):
            # A finish is not a new board offer. Preserve the exact saved basket.
            group['choice'] = effective
            stored_groups.append(group)
            finish_changed = True
            changed_owners.update((object_id, requirement) for requirement in
                                 (group.get('requirement_ids') or [group.get('front_requirement_id') or group['id']]))
            continue
        material, parts = front_group_material(group, choice, object_quantity=quantity)
        for part in parts:
            counts = [a.get('quantity') for line in previous['lines'] for a in line['allocations']
                      if a['object_id'] == object_id and a['demand_id'] == object_id + ':' + part['part_id']]
            if counts and all(value is not None for value in counts):
                part['quantity'] = sum(counts)
        fact = {'company_id': contexts[material['family']]['company_id'], 'object_id': object_id,
                'quantity': quantity, 'composition_version': 'cb_parts_material_demand_v1',
                'materials': [material], 'parts': parts}
        exclusive = set(group.get('requirement_ids', ()))
        if not group.get('mixed'):
            exclusive.add(group['id'])
        if group.get('front_requirement_id'):
            exclusive.add(group['front_requirement_id'])
        snapshot['assumption_fallbacks'] = [row for row in snapshot.get('assumption_fallbacks', ())
            if not (row['object_id'] == object_id and row['material_requirement_id'] in exclusive)]
        snapshot['unresolved_requirement_ids'] = [key for key in snapshot.get('unresolved_requirement_ids', ())
            if key not in {object_id + ':' + req for req in exclusive}]
        front_area = Decimal(0)
        def area(sources):
            return sum(Decimal(str(s['quantity'])) * Decimal(str(s['measurements']['length']['mm']))
                       * Decimal(str(s['measurements']['width']['mm'])) for s in sources)
        original_sources = facts_by_id.get(group['id'], {}).get('part_sources', ())
        ratio = area(group['part_sources']) / area(original_sources) if original_sources else Decimal(1)
        for line in snapshot['lines']:
            remaining = []
            removed = False
            for allocation in line['allocations']:
                source_id = allocation['demand_id'].removeprefix(object_id + ':').removesuffix(':assumption')
                selected = allocation['object_id'] == object_id and (
                    source_id in part_ids or allocation['material_requirement_id'] in exclusive)
                if selected:
                    removed = True
                    front_area += Decimal(str(allocation.get('area_mm2') or 0))
                elif (group.get('mixed') and allocation['object_id'] == object_id
                      and allocation['material_requirement_id'] == group['id']
                      and allocation.get('length_mm') is None and allocation.get('area_mm2')):
                    removed = True
                    front_area += Decimal(str(allocation['area_mm2'])) * ratio
                    remaining.append({**allocation, 'area_mm2': float(Decimal(str(allocation['area_mm2'])) * (1 - ratio))})
                else:
                    remaining.append(allocation)
            if removed:
                changed_keys.add(line['selection_key'])
                changed_owners.update((a['object_id'], a['material_requirement_id']) for a in line['allocations'])
                line['allocations'] = remaining
        physical_area = sum(Decimal(str(p['quantity'])) * Decimal(str(p['length_mm']))
                            * Decimal(str(p['width_mm'])) for p in parts)
        norms = {(object_id, material['requirement_id']): {'unit': 'm2',
                 'quantity_per_item': float(front_area / Decimal(str(quantity)) / 1_000_000)}} if (
                    front_area > 0 and abs(front_area - physical_area) > 1) else {}
        result = build_material_plan(facts_by_object={object_id: fact}, catalogs=contexts[material['family']]['catalogs'],
                                     material_norm_overrides=norms, allow_estimator_allowance=False,
                                     resolve_oversized_cnc=True)
        patch = material_plan_snapshot(result)
        if patch['unresolved_requirement_ids'] or not patch['lines']:
            raise ValueError('No compatible catalog price was found for this front panel material and thickness.')
        if group.get('mixed') and group['id'] in facts_by_id:
            original = facts_by_id[group['id']]
            body = [source for source in original.get('part_sources', ()) if source['part_id'] not in part_ids]
            if body:
                updated_materials[group['id']] = {**original, 'part_sources': body}
        group.update(choice=choice, front_requirement_id=material['requirement_id'],
                     requirement_ids=[material['requirement_id']])
        updated_materials[material['requirement_id']] = material
        new_lines.extend(patch['lines'])
        snapshot['applied_material_defaults'] = [
            row for row in snapshot.get('applied_material_defaults', ())
            if not (row['object_id'] == object_id and row['material_requirement_id'] in exclusive)
        ] + patch['applied_material_defaults']
        stored_groups.append(group)
    if not updated_materials and not finish_changed:
        return previous, {}, set()
    # Merge new fronts with an already purchased stock only when its full key
    # agrees. Its saved offer/price remains authoritative for that basket.
    by_key = {line['selection_key']: line for line in snapshot['lines']}
    for line in new_lines:
        key = line['selection_key']
        changed_keys.add(key)
        if key in by_key:
            by_key[key]['allocations'].extend(line['allocations'])
        else:
            by_key[key] = line
    costs = {(row['object_id'], row['material_requirement_id']): Decimal(str(row['cost_ex_vat']))
             for row in previous['object_material_costs']}
    for line in previous['lines']:
        if line['selection_key'] in changed_keys:
            for owner, value in _line_costs(line).items():
                costs[owner] = costs.get(owner, Decimal(0)) - value
    lines = []
    for key, line in by_key.items():
        if key in changed_keys:
            if not line['allocations']:
                continue
            line = _replan_line(line, snapshot)
            for owner, value in _line_costs(line).items():
                costs[owner] = costs.get(owner, Decimal(0)) + value
                changed_owners.add(owner)
        lines.append(line)
    live_owners = {(a['object_id'], a['material_requirement_id']) for line in lines for a in line['allocations']}
    snapshot.update(lines=lines, input_fingerprint=None,
                    object_material_costs=[{'object_id': oid, 'material_requirement_id': req, 'cost_ex_vat': float(value)}
                                           for (oid, req), value in sorted(costs.items()) if (oid, req) in live_owners])
    snapshot.setdefault('front_panel_groups', {})[object_id] = stored_groups
    snapshot.setdefault('front_panel_choices', {}).setdefault(object_id, {}).update(choices)
    checked = snapshot.get('parts_check', {}).get(object_id)
    if checked is not None:
        current = {row['requirement_id']: row for row in checked.get('materials', ())}
        for requirement, material in updated_materials.items():
            current[requirement] = {**current.get(requirement, {}), 'requirement_id': requirement,
                'source_name': material['source_name'], 'material_role': material['material_role'],
                'unit': material.get('unit'), 'quantity': material.get('quantity')}
        checked['materials'] = list(current.values())
    snapshot['front_material_patch'] = {'object_id': object_id, 'group_ids': list(choices),
                                      'affected_stock_keys': sorted(changed_keys)}
    from use_cases.estimation_labor_v1 import sheet_layout_basis
    if 'front_material_source_sheet_basis' not in snapshot:
        snapshot['front_material_source_sheet_basis'] = sheet_layout_basis(previous)
    return snapshot, updated_materials, changed_owners
