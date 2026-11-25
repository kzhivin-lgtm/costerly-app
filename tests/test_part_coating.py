from copy import deepcopy
from decimal import Decimal
import json

import pandas as pd
import pytest

from use_cases.part_coating import calculate_part_coating, coating_hours, RECIPES, coating_material_rows
from use_cases.estimation_labor_v1 import labor_work_metrics
from tests.test_labor_work_editing import labor_state


def coating_plan(choice='veneered_mdf', quantity=1):
    source = {'part_id': 'B01:door_front:001', 'role': 'door_front', 'quantity': 2 * quantity,
              'source_quantity': 2, 'scope_quantity': 1,
              'measurements': {axis: {'mm': value} for axis, value in [('length',1000),('width',500),('thickness',20)]}}
    group = {'id':'front', 'source_name':'Veneered MDF', 'source_choice':'veneered_mdf',
             'family':'mdf_hdf', 'specification':{'board_type':'mdf','surface':'veneer_two_sided'},
             'part_ids':[source['part_id']], 'part_sources':[source]}
    return {'lines':[], 'object_quantities':{'o':quantity},
            'parts_check':{'o':{}}, 'front_panel_groups':{'o':[group]}, 'front_panel_choices':{'o':{'front':choice}}}


def calculate(plan, **kwargs):
    return calculate_part_coating(plan, object_id='o', machinery={'availability':{'finish_wet_spray_booth':'in_house'}}, **kwargs)


@pytest.mark.parametrize('choice,finish,rate', [('ldsp',None,None),('mdf','enamel',16),
    ('veneered_mdf','lacquer',22),('veneered_mdf_oil','oil',22),('plywood','lacquer',22),('plywood_oil','oil',22)])
def test_approved_front_finish_matrix(choice, finish, rate):
    result=calculate(coating_plan(choice))
    assert [b['finish'] for b in result['batches']]==([finish] if finish else [])
    if finish:
        assert result['area_m2']==2.12  # 2 panels, both faces 1m² + four edges .06m² each.
        assert result['batches'][0]['material_rate']==rate
        assert result['batches'][0]['material_cost']==round(2.12*rate,2)
        assert coating_material_rows(result)[-1]['total']==21.2
    else:
        assert result['hours']=='0' and coating_material_rows(result)==[]


def test_finished_count_ignores_lamination_and_purchased_waste_and_scales_physical_configuration_once():
    plan=coating_plan(quantity=3);original=deepcopy(plan)
    part=plan['front_panel_groups']['o'][0]['part_sources'][0]
    part['quantity']=18  # Three sheet layers, still six finished panels.
    part['sheet_layup']={'layer_count':3,'layer_mm':6,'finished_mm':18}
    plan['lines']=[{'purchase_quantity':100,'total_cost':999999}]
    result=calculate(plan)
    assert result['area_m2']==pytest.approx(6.36) and result['parts'][0]['quantity']==6
    assert plan['object_quantities']==original['object_quantities']
    assert plan['lines'][0]['purchase_quantity']==100


@pytest.mark.parametrize('area,hours', [(0,0),(10,Decimal('28')/3),(30,20),(45,32),(60,40),(70,Decimal('148')/3)])
def test_full_batch_preparation_is_inside_reference_and_residual_has_its_own_setup(area,hours):
    assert coating_hours(area, RECIPES['lacquer'])==pytest.approx(hours)


@pytest.mark.parametrize('area',[1,10,30,45,70])
def test_oil_is_linear_without_a_booth_or_batch_surcharge(area):
    assert coating_hours(area, RECIPES['oil'])==Decimal(area)*Decimal(35)/60
    plan=coating_plan('plywood_oil')
    result=calculate_part_coating(plan,object_id='o',machinery={})
    assert result['partial'] is False and result['batches'][0]['route']=='hand_application'


@pytest.mark.parametrize('availability',[None,'not_in_house','subcontractor'])
def test_spray_work_requires_company_in_house_route_and_never_becomes_free_work(availability):
    result=calculate_part_coating(coating_plan(),object_id='o',
                                  machinery={'availability':{'finish_wet_spray_booth':availability}})
    assert result['hours'] is None and result['partial'] is True
    assert result['batches'][0]['material_cost']==46.64


def test_missing_dimensions_and_empty_count_remain_unknown():
    plan=coating_plan()
    source=plan['front_panel_groups']['o'][0]['part_sources'][0]
    source['measurements']['width']['mm']=None
    result=calculate(plan)
    assert result['issues'] and result['hours'] is None
    assert any(row['total'] is None for row in coating_material_rows(result))
    source['measurements']['width']['mm']=500;source['source_quantity']=None
    assert calculate(plan)['partial']


def test_non_front_ada_veneer_panels_are_included_and_selected_fronts_override_source_stock():
    plan=coating_plan('ldsp')
    panel=deepcopy(plan['front_panel_groups']['o'][0]['part_sources'][0]);panel['part_id']='B01:visible_sheet:002'
    source=plan['front_panel_groups']['o'][0]['part_sources'][0]
    line={'raw_agent_json':{'facts':{'family':'mdf_hdf','specification':{'surface':'veneer_two_sided'},
          'material_role':'visible_sheet','part_sources':[source,panel]}}}
    result=calculate(plan,source_lines=[line])
    assert result['area_m2']==2.12 and result['parts'][0]['part_id']==panel['part_id']


@pytest.mark.parametrize('choice,text,multiplier', [('veneered_mdf','High-gloss veneer',2),
    ('veneered_mdf','Veneer with patina',2),('mdf','Филёнчатый фасад МДФ',Decimal('1.1')),
    ('mdf','Patina',1),('plywood_oil','High-gloss',1)])
def test_evidenced_material_effects_change_lkm_only_not_area_consumables_or_hours(choice,text,multiplier):
    plan=coating_plan(choice)
    baseline=calculate(plan)
    plan['front_panel_groups']['o'][0]['part_sources'][0]['material_note']={'source_text':text,'refs':['ocr:finish']}
    result=calculate(plan)
    assert result['area_m2']==baseline['area_m2'] and result['hours']==baseline['hours']
    rate=RECIPES[result['batches'][0]['finish']]['material_rate']
    assert result['batches'][0]['material_cost']==float((Decimal('2.12')*rate*Decimal(multiplier)).quantize(Decimal('.01')))
    assert coating_material_rows(result)[-1]['total']==21.2


def test_unapproved_combination_does_not_silently_multiply_effects():
    plan=coating_plan()
    plan['front_panel_groups']['o'][0]['part_sources'][0]['material_note']={
        'source_text':'High-gloss veneer with patina','refs':['ocr:finish']}
    result=calculate(plan)
    assert result['batches'][0]['material_cost'] is None and result['material_issues']
    assert result['hours'] is not None


def test_auto_coating_and_manual_override_use_100_plus_payroll_once_without_changing_other_work():
    state=labor_state();before=labor_work_metrics(state)
    state['coating']=calculate(coating_plan('plywood_oil'))
    auto=labor_work_metrics(state)
    assert auto['part-coating']['hours']==Decimal('2.12')*35/60
    assert auto['part-coating']['pay']==Decimal('123.67')
    assert auto['part-coating']['taxes']==Decimal('30.92')
    manual=labor_work_metrics(state,quantity=2,overrides={'part-coating':'3'})
    assert manual['part-coating']['hours']==6 and manual['part-coating']['total']==750
    assert auto['sheet-processing']==before['sheet-processing'] and auto['assembly']==before['assembly']


def test_materials_flat_consumables_and_percent_policies_feed_self_cost_once(monkeypatch):
    from use_cases import estimation
    plan=coating_plan('plywood_oil')
    monkeypatch.setattr(estimation,'_material_rows_from_plan',lambda *a,**kw:[{'item':'Boards','total':1000}])
    lines=pd.DataFrame(estimation._material_policy_lines(estimate_id='e',object_id='o',company_id='c',
        settings={},primary_material_total=1000,coating_material_total=0))
    rows=estimation._object_detail_material_rows(plan,lines,'o')
    assert next(r for r in rows if r['item']=='Wood oil')['total']==46.64
    assert next(r for r in rows if r['item']=='Coating consumables')['total']==21.2
    assert not any(r['item']=='Paint consumables' for r in rows)
    assert next(r for r in rows if r['item']=='Consumables')['total']==52.33
    assert sum(r['total'] for r in rows)==pytest.approx(1130.64)


def test_finish_change_refreshes_coating_only_and_reopen_is_idempotent(monkeypatch):
    from use_cases import estimation
    plan=coating_plan()
    monkeypatch.setattr(estimation,'load_object_labor',lambda *a,**kw:labor_state())
    monkeypatch.setattr(estimation,'_material_rows_from_plan',lambda *a,**kw:[{'item':'Boards','total':1000}])
    obj={'object_id':'o','company_id':'c','run_id':'r','quantity':1}
    context={'plan':plan,'parts':{},'machinery':{'availability':{'finish_wet_spray_booth':'in_house'}},
             'settings':{'production_monthly_hours':160,'vat_percent':18},'monthly':{'rent_facilities_cost':1600}}
    lines=pd.DataFrame([{'section':'material','source':'parts_check','cost':1000}])
    first,_=estimation._full_cost_summary(None,estimate_id='e',obj=obj,lines=lines,
                                         material_batch=0,context=context,persist=False)
    saved=pd.concat([lines,pd.DataFrame([{'source':estimation._FULL_COST_SOURCE,'raw_agent_json':first}])],ignore_index=True)
    def forbidden(*a,**kw):raise AssertionError('Unrelated Labor was recalculated')
    monkeypatch.setattr(estimation,'load_object_labor',forbidden)
    plan['front_panel_choices']['o']['front']='veneered_mdf_oil'
    context.update(preserve_labor=True,machinery={},parts={})
    second,changed=estimation._full_cost_summary(None,estimate_id='e',obj=obj,lines=saved,
                                               material_batch=0,context=context,persist=False)
    assert changed and second['labor_blocks']['sheet_processing']==first['labor_blocks']['sheet_processing']
    assert second['labor_blocks']['assembly']==first['labor_blocks']['assembly']
    assert Decimal(second['part_coating']['hours'])==Decimal('2.12')*35/60
    assert Decimal(second['overhead']['labor_hours'])==Decimal(second['labor']['hours'])
    saved.loc[saved.source==estimation._FULL_COST_SOURCE,'raw_agent_json']=pd.Series([second],index=saved.index[saved.source==estimation._FULL_COST_SOURCE])
    third,changed=estimation._full_cost_summary(None,estimate_id='e',obj=obj,lines=saved,
                                              material_batch=0,context=context,persist=False)
    assert not changed and third==second
