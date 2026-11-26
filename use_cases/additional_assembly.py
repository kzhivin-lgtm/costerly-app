"""Provisional owner-selected labor per finished special assembly, not stock units."""
from decimal import Decimal
from math import isfinite


ROLES = {'glass_box_lid': 'Glass box', 'mirror_glass': 'Mirror', 'led_strip_run': 'LED zone'}
MINUTES_PER_UNIT = 60


def calculate_additional_assembly(report, *, object_id):
    rows, issues, seen = [], [], {}
    for index, part in enumerate(report['objects'][object_id].get('parts', ())):
        role = part.get('role')
        if role not in ROLES:
            continue
        quantity, repeats = part.get('quantity'), part.get('scope_quantity', 1)
        if any(type(n) not in (int, float) or not isfinite(n) or n <= 0 or int(n) != n
               for n in (quantity, repeats)):
            issues.append(f'{role}: quantity unresolved')
            continue
        identity = (role, part.get('owner_id'), part.get('instance_ref'))
        if not any(identity[1:]):
            identity = (role, 'unidentified-row', index)
        if identity in seen:
            if seen[identity] != (quantity, repeats):
                issues.append(f'{role}: conflicting duplicate quantity')
            continue
        seen[identity] = (quantity, repeats)
        count = int(quantity) * int(repeats)
        rows.append({'role': role, 'name': ROLES[role], 'owner_id': part.get('owner_id'),
                     'instance_ref': part.get('instance_ref'), 'quantity': count,
                     'minutes_per_unit': MINUTES_PER_UNIT, 'minutes': count * MINUTES_PER_UNIT})
    return {'rows': rows, 'hours': sum((Decimal(row['minutes']) / 60 for row in rows), Decimal(0)),
            'partial': bool(issues), 'issues': issues, 'norm': 'owner-provisional-60min-v1'}
