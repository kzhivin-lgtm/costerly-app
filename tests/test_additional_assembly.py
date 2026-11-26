from copy import deepcopy
from decimal import Decimal

from use_cases.additional_assembly import calculate_additional_assembly
from use_cases.block_assembly import calculate_block_assembly, partition_block_assembly
from use_cases.estimation_labor_v1 import labor_work_metrics


def test_finished_units_count_once_not_glass_panels_or_led_length():
    parts = [{'role':'glass_box_lid','quantity':8,'instance_ref':'boxes'},
             {'role':'glass_box_long_wall','quantity':16},
             {'role':'glass_box_end_wall','quantity':16},
             {'role':'mirror_glass','quantity':2,'instance_ref':'mirrors'},
             {'role':'led_strip_run','quantity':4,'instance_ref':'lighting','dimensions':{'length':{'mm':12000}}}]
    report={'objects':{'o':{'parts':parts}}};before=deepcopy(report)
    audit=calculate_additional_assembly(report,object_id='o')
    assert audit['hours']==14 and not audit['partial']
    assert sum(row['quantity'] for row in audit['rows'])==14
    assert report==before


def test_scope_repeats_duplicates_and_unknown_counts_are_explicit():
    mirror={'role':'mirror_glass','quantity':1,'scope_quantity':2,'owner_id':'m','instance_ref':'m'}
    report={'objects':{'o':{'parts':[mirror,dict(mirror),{'role':'led_strip_run','quantity':None},
        {'role':'mirror_glass','quantity':1},{'role':'mirror_glass','quantity':1}]}}}
    result=calculate_additional_assembly(report,object_id='o')
    assert result['hours']==4 and result['partial'] and len(result['issues'])==1


def test_existing_hardware_is_partitioned_without_changing_norms_or_source():
    report={'objects':{'o':{'blocks':[{'id':'B'}],'parts':[
        {'role':'hinge','quantity':4,'block_id':'B'},
        {'role':'door_front','quantity':2,'block_id':'B'},
        {'role':'push_latch','quantity':2,'block_id':'B'},
        {'role':'fixed_panel','quantity':3,'block_id':'B'}]}}}
    original=calculate_block_assembly(report,object_id='o');before=deepcopy(original)
    structural,hardware=partition_block_assembly(original)
    assert structural['planned_minutes']+hardware['planned_minutes']==original['planned_minutes']
    assert hardware['active_minutes']==4*2+2*5+2*3
    assert original==before
    state={'status':'preparing','assembly':original,'additional_assembly':{'hours':14,'partial':False}}
    work=labor_work_metrics(state)
    assert work['assembly']['hours']==original['planned_minutes']/60
    assert work['assembly-stage']['hours']==work['assembly']['hours']+14
    for field in ('hours','pay','taxes','total'):
        assert work['block-assembly'][field]+work['hardware-fitting'][field]==work['assembly'][field]
    legacy=labor_work_metrics(state,overrides={'assembly':'10'})
    assert legacy['assembly']['hours']==10 and legacy['assembly-stage']['hours']==24
    edited=labor_work_metrics(state,overrides={'assembly':'10','hardware-fitting':'0'})
    assert edited['hardware-fitting']['hours']==0
    assert edited['block-assembly']['hours']==legacy['block-assembly']['hours']
    assert edited['assembly-stage']['hours']==legacy['block-assembly']['hours']+14


def test_full_cost_persists_special_work_and_allocates_its_hours_once(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    report={'objects':{'o':{'blocks':[{'id':'B'}],'parts':[
        {'role':'fixed_panel','quantity':3,'block_id':'B'},
        {'role':'hinge','quantity':4,'block_id':'B'},
        {'role':'door_front','quantity':2,'block_id':'B'},
        {'role':'push_latch','quantity':2,'block_id':'B'}]}}}
    state={'status':'preparing','assembly':calculate_block_assembly(report,object_id='o'),
           'additional_assembly':{'hours':14,'partial':False,'rows':[]}}
    monkeypatch.setattr(estimation,'load_object_labor',lambda *a,**k:state)
    summary,_=estimation._full_cost_summary(None,estimate_id='e',
        obj={'object_id':'o','run_id':'r','company_id':'c','quantity':1},lines=pd.DataFrame(),
        material_batch=1000,context={'plan':{'lines':[]},'parts':{},'machinery':{},
            'settings':{'production_workers':1,'workdays_per_month':20,'hours_per_day':8,'vat_percent':18},
            'monthly':{'rent_facilities_cost':1600}},persist=False)
    assert Decimal(summary['labor']['total'])==Decimal('946.61')
    assert summary['overhead']['cost']==151.46
    assert summary['self_cost_ex_vat']==2098.07
    assert summary['additional_assembly']['hours']==14
    assert summary['hardware_fitting']['active_minutes']==24
