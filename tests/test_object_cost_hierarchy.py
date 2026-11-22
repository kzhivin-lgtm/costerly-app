from decimal import Decimal
import pytest

from screens.estimation_labor_v1 import _labor_html, _pay_metrics, _sheet_pay_metrics
from ui.object_detail_view import MATERIAL_PURCHASE_COLUMNS, _section_html


@pytest.mark.parametrize('value,label', [(18.0,'18'), (18.5,'18.5')])
def test_vat_label_preserves_fractional_rates_without_integral_decimal(value,label):
    from ui.object_detail_view import _final_html
    result=_final_html({'self_cost':{'vat_percent':value,'excl_vat':100,'vat':value,'total':100+value}})
    assert f'VAT {label}%' in result



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
    partial_html = _section_html(section)
    assert '>Subtotal<' not in partial_html
    assert 'data-material-section-total>₪136<' in partial_html


def test_assembly_remains_available_when_materials_are_pending_and_quantity_is_applied():
    assembly = {'planned_minutes': Decimal('120'), 'active_minutes': 77, 'base_labor_ils': Decimal('100'),
                'hourly_base_ils': Decimal('50'), 'common_roles_for_review': [],
                'blocks': [{'block_id': 'B01', 'planned_minutes': Decimal('120'), 'active_minutes': 77,
                            'base_labor_ils': Decimal('100'), 'issues': [], 'operations': []}]}
    html = _labor_html({'status': 'waiting_for_materials', 'assembly': assembly}, quantity=3)
    assert 'Waiting for the Material Plan.' in html
    assert 'data-cost-band="sheet-processing"' in html
    assert 'data-cost-band="assembly"' in html
    assert '₪300' in html and '₪75' in html and '₪375' in html
    assert '>Total<' in html
    assert 'Some work needs review' not in html
    assert 'outside this estimate' not in html
    assert 'Assembly breakdown' not in html


def test_labor_is_a_single_header_and_two_compact_work_rows():
    html = _labor_html({'status': 'waiting_for_materials'})
    assert html.count('object-detail-work-row') == 2
    assert html.count('object-detail-cost-band') == 1
    assert '>Labor<br>Pay<' in html
    assert '₪50/h' not in html and 'In-house labor</p>' not in html
    assert '>Subtotal<' not in html


def test_pending_labor_does_not_fabricate_zero_cost():
    html = _labor_html({'status': 'preparing'})
    assert 'Preparing Sheet Processing' in html and 'Preparing Assembly' in html
    assert '₪0' not in html


def test_hours_save_roundtrip_is_per_item_and_recalculates_full_sc_without_changing_norms(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    from use_cases.labor_hours import overrides_from_lines
    writes = []
    monkeypatch.setattr(estimation, 'get_supabase_client', lambda: object())
    monkeypatch.setattr(estimation, 'company_auth_enabled', lambda: False)
    monkeypatch.setattr(estimation, '_object_material_context', lambda *a, **k: {
        'company_id': 'company', 'run_id': 'run', 'quantity': 2})
    monkeypatch.setattr(estimation, 'fetch_rfq_estimate_material_plan', lambda *a: pd.DataFrame())
    monkeypatch.setattr(estimation, 'upsert_rfq_estimate_lines', lambda _, *, lines: writes.extend(lines))
    recalculations = []
    monkeypatch.setattr(estimation, '_recalculate_object_estimate_totals', lambda *a, **k: recalculations.append(k))
    estimation.save_object_detail_material_edits(estimate_id='estimate', object_id='object', edits=[
        {'field': 'labor_hours', 'lineId': 'assembly', 'value': '40.5'},
        {'field': 'labor_hours', 'lineId': 'sheet-processing', 'value': '0'},
    ]).result()
    assert len(recalculations) == 1 and recalculations[0]['object_id'] == 'object'
    saved = overrides_from_lines(pd.DataFrame(writes))
    assert saved == {'assembly': '20.25', 'sheet-processing': '0'}
    assert all(row['cost'] == 0 and row['hours'] is None and row['rate'] is None for row in writes)
    from screens.estimation_labor_v1 import _cost_band
    html = _cost_band('Assembly', '', _pay_metrics(Decimal(saved['assembly']) * 2), key='assembly')
    assert '>40.5</div>' in html and '₪2\u202f025' in html and '₪506' in html and '₪2\u202f531' in html


def test_manual_hours_validation_and_tenant_rejection(monkeypatch):
    import pytest
    from use_cases.labor_hours import validate_hours
    from use_cases import estimation
    for value in ('-1', '1.25', 'NaN', 'Infinity', '1000000.1', '', None):
        with pytest.raises(ValueError):
            validate_hours(value)
    assert validate_hours('0') == 0 and validate_hours('1000000.0') == 1_000_000
    monkeypatch.setattr(estimation, 'get_supabase_client', lambda: object())
    monkeypatch.setattr(estimation, 'company_auth_enabled', lambda: True)
    monkeypatch.setattr(estimation, 'assert_estimate_owned', lambda *a: (_ for _ in ()).throw(PermissionError('foreign')))
    with pytest.raises(PermissionError):
        estimation.save_object_detail_material_edits(estimate_id='foreign', object_id='object', edits=[
            {'field': 'labor_hours', 'lineId': 'assembly', 'value': '1'}])


def test_new_estimate_refresh_waits_for_durable_shell_without_masking_access(monkeypatch):
    from concurrent.futures import Future
    from threading import Event
    from screens import objects
    future = Future()
    future.estimate_shell_ready = Event()
    monkeypatch.setattr(objects.st, 'session_state', {'estimation_batch_future': future,
        'objects_estimation_seed_rows': []})
    reads = []
    def load(estimate):
        reads.append(estimate)
        raise PermissionError('foreign')
    monkeypatch.setattr(objects, '_load_objects_screen_data', load)
    monkeypatch.setattr(objects, 'report_runtime_failure', lambda *a, **k: None)
    assert objects._persisted_objects_state('new').data_error is None
    assert reads == []
    future.estimate_shell_ready.set()
    assert 'foreign' in objects._persisted_objects_state('new').data_error
    assert reads == ['new']
