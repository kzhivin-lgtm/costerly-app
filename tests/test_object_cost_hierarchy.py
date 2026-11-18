from decimal import Decimal

from screens.estimation_labor_v1 import _labor_html, _pay_metrics, _sheet_pay_metrics
from ui.object_detail_view import MATERIAL_PURCHASE_COLUMNS, _section_html


def sheet_result(*, route='cnc'):
    return {
        'in_house_route': route, 'work': {'blank_count': 12},
        'in_house': {'operator_hours': 2, 'materials': [{'stock_ex_vat': 999999}]},
        'file_preparation': {'minutes': 30}, 'edge_banding': {'minutes': 60, 'metres': 7},
        'cnc_edging': {'minutes': 60}, 'issues': [], 'unplaced_blanks': 0,
        'panel_saw': {'preparation_minutes': 15, 'saw': {'cut': 40}, 'drilling': {'mark': 10},
                      'helper_minutes': 5, 'edging': {'minutes': 20}, 'unplaced': 0, 'geometry_review': []},
    }


def test_labor_uses_paid_hours_at_50_and_one_payroll_load_without_stock():
    metrics = _sheet_pay_metrics(sheet_result())
    assert metrics == {'hours': Decimal('3.5'), 'pay': Decimal('175.00'),
                       'taxes': Decimal('43.75'), 'total': Decimal('218.75'), 'partial': False}
    changed = sheet_result()
    changed['in_house']['materials'][0]['stock_ex_vat'] *= 10
    assert _sheet_pay_metrics(changed) == metrics


def test_panel_saw_includes_helper_paid_time_once():
    metrics = _sheet_pay_metrics(sheet_result(route='panel_saw'))
    assert metrics['hours'] == Decimal('1.5')
    assert metrics['pay'] == Decimal('75.00')
    assert metrics['taxes'] == Decimal('18.75')
    assert metrics['total'] == Decimal('93.75')


def test_unavailable_route_is_unknown_not_zero_and_partial_work_is_marked():
    assert _sheet_pay_metrics(sheet_result(route=None)) is None
    result = sheet_result()
    result['issues'] = [{'description': 'Missing dimensions'}]
    assert _sheet_pay_metrics(result)['partial'] is True
    assert _pay_metrics(None) is None


def test_material_summary_uses_exact_row_totals_and_one_title():
    section = {'key': 'material', 'title': 'Materials', 'columns': MATERIAL_PURCHASE_COLUMNS, 'metrics': [],
               'rows': [{'item': 'Sheet', 'total': 123.49}, {'item': 'Tape', 'total': 12.49}]}
    html = _section_html(section)
    assert 'object-detail-materials-band' in html
    assert html.count('>Materials<') == 1
    assert 'data-material-section-total>₪136<' in html
    section['rows'].append({'item': 'Unknown', 'total': None})
    assert '>Subtotal<' in _section_html(section)


def test_assembly_remains_available_when_materials_are_pending_and_quantity_is_applied():
    assembly = {'planned_minutes': Decimal('120'), 'active_minutes': 77, 'base_labor_ils': Decimal('100'),
                'hourly_base_ils': Decimal('50'), 'common_roles_for_review': [],
                'blocks': [{'block_id': 'B01', 'planned_minutes': Decimal('120'), 'active_minutes': 77,
                            'base_labor_ils': Decimal('100'), 'issues': [], 'operations': []}]}
    html = _labor_html({'status': 'waiting_for_materials', 'assembly': assembly}, quantity=3)
    assert 'Waiting for the Material Plan.' in html
    assert 'data-cost-band="sheet-processing"' in html
    assert 'data-cost-band="assembly"' in html
    assert '₪300.00' in html and '₪75.00' in html and '₪375.00' in html
    assert '>Total<' in html
    assert 'Some work needs review' in html
    assert 'Assembly breakdown' not in html


def test_labor_is_a_single_header_and_two_compact_work_rows():
    html = _labor_html({'status': 'waiting_for_materials'})
    assert html.count('object-detail-work-row') == 2
    assert html.count('object-detail-cost-band') == 1
    assert '>Labor pay<' in html
    assert '₪50/h' not in html and 'In-house labor</p>' not in html
    assert '>Subtotal<' not in html


def test_pending_labor_does_not_fabricate_zero_cost():
    html = _labor_html({'status': 'preparing'})
    assert 'Preparing Sheet Processing' in html and 'Preparing Assembly' in html
    assert '₪0' not in html
