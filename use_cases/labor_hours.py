"""Manual paid-hour overrides, independent of physical production norms."""
from decimal import Decimal, InvalidOperation

BLOCKS = frozenset({'sheet-processing', 'assembly', 'part-coating', 'additional-assembly',
                    'trial-fit', 'packing', 'cnc-operator', 'file-preparation', 'edge-banding',
                    'block-assembly', 'hardware-fitting'})
SOURCE = 'labor_hours_override'


def validate_hours(value):
    try:
        hours = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Enter hours from 0 to 1,000,000 with one decimal place.') from None
    if not hours.is_finite() or not 0 <= hours <= 1_000_000 or hours != hours.quantize(Decimal('.1')):
        raise ValueError('Enter hours from 0 to 1,000,000 with one decimal place.')
    return hours


def overrides_from_lines(lines):
    result = {}
    for _, line in lines.iterrows():
        if line.get('source') != SOURCE:
            continue
        raw = line.get('raw_agent_json')
        if isinstance(raw, dict) and raw.get('block') in BLOCKS:
            result[raw['block']] = str(raw['hours_per_item'])
    return result


def override_lines(edits, *, estimate_id, object_id, company_id, quantity):
    rows = []
    for block, hours in edits.items():
        if block not in BLOCKS:
            raise ValueError('This labor block is no longer available.')
        rows.append({
            'estimate_id': estimate_id, 'object_id': object_id, 'company_id': company_id,
            'line_id': f'{object_id}__labor_hours__{block}', 'section': 'labor',
            'group_name': 'Labor hours', 'item_name': block, 'source': SOURCE,
            # Metadata only. The existing SC integration is a separate task.
            'cost': 0, 'hours': None, 'rate': None, 'sort_order': 90000,
            'raw_agent_json': {'block': block, 'hours_per_item': format(hours / Decimal(str(quantity)), 'f')},
        })
    return rows
