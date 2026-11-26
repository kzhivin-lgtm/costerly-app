from copy import deepcopy
from decimal import Decimal
from html.parser import HTMLParser

import pandas as pd
import pytest

from screens.estimation_labor_v1 import _labor_html
from use_cases.estimation_labor_v1 import labor_work_metrics, sheet_pay_metrics
from use_cases.labor_hours import BLOCKS, override_lines, overrides_from_lines, validate_hours
from ui.object_detail_view import overhead_section_html
from use_cases.overhead_engine import estimate_object_overhead


def labor_state():
    return {'status':'ready', 'result':{
        'in_house_route':'cnc', 'work':{'blank_count':4, 'machine_minutes':60,
            **{key:0 for key in ('setup_minutes','load_minutes','unload_minutes','cleanup_minutes',
                'cut_minutes','move_minutes','drilling_minutes','tool_change_minutes')}},
        'in_house':{'operator_hours':4}, 'file_preparation':{'minutes':60},
        'edge_banding':{'minutes':60,'metres':10}, 'cnc_edging':{'minutes':60},
        'issues':[], 'unplaced_blanks':0, 'joined_parts':[]},
        'assembly':{'planned_minutes':Decimal(120),'common_roles_for_review':[],'blocks':[]},
        'preparation':{'checking_minutes':30,'packing_minutes':15,'checking_known':True,
            'packing_partial':False,'interfaces':[],'packing_units':[],'issues':[]}}


def test_cnc_split_keeps_original_sheet_payroll_and_source_norms():
    state=labor_state();original=deepcopy(state)
    work=labor_work_metrics(state)
    assert work['sheet-processing']==sheet_pay_metrics(state['result'])
    assert [work[key]['hours'] for key in ('cnc-operator','file-preparation','edge-banding')]==[4,1,1]
    assert work['labor']['hours']==Decimal('8.75')
    assert work['labor']['total']==Decimal('546.88')
    assert state==original


def test_edge_visibility_uses_applicability_not_a_saved_zero_hour_override():
    state=labor_state()
    applicable=_labor_html(state,overrides={'edge-banding':'0'})
    assert 'data-line-id="edge-banding"' in applicable
    state['result']['edge_banding']={'minutes':0,'metres':0}
    state['result']['cnc_edging']={'minutes':0}
    absent=_labor_html(state)
    assert 'data-line-id="edge-banding"' not in absent
    assert 'data-line-id="edge-banding"' in _labor_html(state,overrides={'edge-banding':'2'})


def test_saved_old_sheet_override_is_retained_and_new_specific_edit_changes_one_share():
    state=labor_state();original=deepcopy(state)
    work=labor_work_metrics(state,overrides={'sheet-processing':'9'})
    assert [work[key]['hours'] for key in ('cnc-operator','file-preparation','edge-banding')]==[6,Decimal('1.5'),Decimal('1.5')]
    assert work['sheet-processing']['hours']==9
    changed=labor_work_metrics(state,overrides={'sheet-processing':'9','file-preparation':'2'})
    assert changed['cnc-operator']['hours']==6 and changed['edge-banding']['hours']==Decimal('1.5')
    assert changed['sheet-processing']['hours']==Decimal('9.5')
    assert state==original


@pytest.mark.parametrize('key', ['cnc-operator','file-preparation','edge-banding','part-coating',
    'assembly','additional-assembly','trial-fit','packing'])
def test_every_terminal_work_saves_per_item_and_counts_once(key):
    state=labor_state();baseline=labor_work_metrics(state)
    lines=override_lines({key:validate_hours('12.3')},estimate_id='e',object_id='o',company_id='c',quantity=3)
    overrides=overrides_from_lines(pd.DataFrame(lines));work=labor_work_metrics(state,quantity=3,overrides=overrides)
    assert overrides=={key:'4.1'} and work[key]['hours']==Decimal('12.3')
    assert lines[0]['cost']==0 and lines[0]['company_id']=='c'
    expected=(labor_work_metrics(state,quantity=3)['labor']['hours']
              -labor_work_metrics(state,quantity=3)[key]['hours']+Decimal('12.3'))
    assert work['labor']['hours']==expected


def test_unavailable_work_stays_unknown_until_explicit_override_including_zero():
    state={'status':'preparing'}
    assert labor_work_metrics(state)['labor'] is None
    work=labor_work_metrics(state,overrides={'trial-fit':'0'})
    assert work['trial-fit']['hours']==0 and work['packing'] is None
    assert work['labor']['hours']==0 and work['labor']['partial'] is True
    assert all(key not in BLOCKS for key in ('labor','part-production','cnc','assembly-stage','preparation-packing'))


class WorkEditors(HTMLParser):
    def __init__(self):
        super().__init__();self.editors=[]
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if data.get('data-field')=='labor_hours':self.editors.append(data['data-line-id'])


def test_actual_cnc_view_has_only_elements_and_work_breakdown_and_terminal_editors():
    state=labor_state();state['assembly']=None
    html=_labor_html(state,object_id='o',elements=[{'label':'B01','rows':[]}])
    parsed=WorkEditors();parsed.feed(html)
    assert set(parsed.editors)=={'cnc-operator','file-preparation','edge-banding',
        'part-coating','assembly','additional-assembly','trial-fit','packing'}
    assert '>CNC</div>' in html and 'Elements' in html
    assert 'In-house' not in html and 'Subcontractor' not in html and 'Materials + labor' not in html
    assert 'Social +25%' in html


def test_new_leaf_hours_feed_saved_self_cost_and_overhead_once(monkeypatch):
    from use_cases import estimation
    state=labor_state();original=deepcopy(state)
    monkeypatch.setattr(estimation,'load_object_labor',lambda *a,**k:state)
    hours={key:Decimal('1') for key in ('cnc-operator','file-preparation','edge-banding','assembly',
        'part-coating','additional-assembly','trial-fit','packing')}
    lines=pd.DataFrame(override_lines(hours,estimate_id='e',object_id='o',company_id='c',quantity=1))
    summary,_=estimation._full_cost_summary(None,estimate_id='e',obj={'object_id':'o','run_id':'r','company_id':'c','quantity':1},
        lines=lines,material_batch=1000,context={'plan':{'lines':[]},'parts':{'status':'ready','payload':'saved'},
        'machinery':{},'settings':{'production_workers':1,'workdays_per_month':20,'hours_per_day':8,'vat_percent':18},
        'monthly':{'rent_facilities_cost':1600}},persist=False)
    assert Decimal(summary['labor']['hours'])==8 and Decimal(summary['labor']['total'])==Decimal('562.5')
    assert Decimal(summary['overhead']['labor_hours'])==8 and summary['overhead']['cost']==80
    assert summary['self_cost_ex_vat']==1642.5
    assert set(summary['labor_work'])>=set(hours)
    assert state==original


def test_overhead_has_one_shared_header_outside_all_groups():
    result=estimate_object_overhead(company_id='c',estimate_id='e',object_id='o',
        settings={'production_workers':1,'workdays_per_month':20,'hours_per_day':8},
        overhead_monthly={'rent_facilities_cost':1600,'electricity_utilities_cost':160},labor_hours=8,labor_cost=500,material_cost=1000)
    html=overhead_section_html(result)
    assert html.count('>Monthly cost<')==1 and html.count('>Allocation<')==1
    assert html.index('object-detail-overhead-column-headings')<html.index('<details class="object-detail-group">')


def test_legacy_manual_budget_without_split_is_not_invented_as_edge_banding():
    state=labor_state()
    state['result']['in_house']['operator_hours']=0
    state['result']['file_preparation']['minutes']=0
    state['result']['cnc_edging']['minutes']=0
    work=labor_work_metrics(state,overrides={'sheet-processing':'9'})
    assert work['sheet-processing']['hours']==9
    assert work['cnc-operator']['hours']==9 and work['edge-banding']['hours']==0


def test_manual_sheet_hours_are_rendered_even_when_calculated_source_is_unavailable():
    html=_labor_html({'status':'preparing'},overrides={'sheet-processing':'2'})
    assert 'data-field="labor_hours" data-line-id="sheet-processing" data-original-value="2"' in html
    assert 'Preparing Sheet Processing' in html


def test_cnc_is_readonly_rollup_before_reference_elements_and_keeps_source_cost():
    import re
    state=labor_state();original=deepcopy(state)
    html=_labor_html(state,object_id='o',elements=[{'label':'B01','rows':[]}], overrides={'file-preparation':'2'})
    summary=re.search(r'data-cost-band="cnc"(.*?)</summary>',html,re.S).group(1)
    assert 'data-labor-aggregate="true"' in summary
    assert 'data-labor-detail="cnc"' in summary
    assert 'contenteditable' not in summary
    assert '>7.0<' in summary and '>₪350<' in summary and '>₪438<' in summary
    assert html.index('data-cost-band="cnc"') < html.index('class="object-detail-cnc-elements"')
    assert labor_work_metrics(state,overrides={'file-preparation':'2'})['labor']['hours']==Decimal('9.75')
    assert state==original
