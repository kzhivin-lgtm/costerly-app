from copy import deepcopy
from decimal import Decimal
from itertools import permutations

import pytest

from use_cases.preparation_packing import calculate_preparation_packing, packing_size
from use_cases.estimation_preparation_evidence import attach_preparation_evidence
from use_cases.estimation_labor_v1 import preparation_pay_metrics


def block(ident, dims=(600, 600, 400)):
    return {"id": ident, "envelope": {axis: {"mm": value} for axis, value in zip(("width", "height", "depth"), dims)}}


def report(*blocks, interfaces=()):
    return {"source_audit_sha256": "source", "objects": {"o": {"blocks": list(blocks), "parts": [],
        "preparation_evidence": {"status": "ready", "interfaces": list(interfaces)}}}}


@pytest.mark.parametrize('dims,expected', [
    ((600,600,400),'S'), ((601,600,400),'M'), ((600,600,401),'M'),
    ((1200,800,600),'M'), ((1201,800,600),'L'), ((1200,801,600),'L'), ((1200,800,601),'L'),
    ((2000,1200,800),'L'), ((2001,1200,800),'XL'), ((2000,1201,800),'XL'), ((2000,1200,801),'XL'),
    ((None,100,100),None), ((0,100,100),None), ((True,100,100),None), ((float('nan'),100,100),None),
])
def test_all_inclusive_size_boundaries_are_orientation_independent(dims, expected):
    for rotation in permutations(dims):
        assert packing_size(rotation) == expected


def test_approved_man_minutes_are_not_multiplied_by_pace_or_crew_again():
    r = report(block('S'), block('M',(1200,800,600)), block('L',(2000,1200,800)), block('XL',(2500,100,100)),
               interfaces=[{'unit_ids':['S','M'],'source_refs':['drawing']}])
    before = deepcopy(r)
    result = calculate_preparation_packing(r, object_id='o')
    assert result['packing_minutes'] == 10 + 15 + 20 + 25
    assert result['checking_minutes'] == 30
    assert result['planned_minutes'] == 100
    assert r == before
    checking, packing, total = preparation_pay_metrics({'preparation': result}, quantity=3)
    assert checking['hours'] == Decimal('1.5')
    assert packing['hours'] == Decimal('3.5')
    assert total['hours'] == 5 and total['pay'] == 250 and total['taxes'] == Decimal('62.50')


def test_interface_count_is_not_number_of_blocks_minus_one_and_evidence_is_retained():
    interfaces = [{'unit_ids':a,'source_refs':[ref]} for a,ref in [
        (['A','B'],'one'), (['B','A'],'two'), (['B','C'],'three'), (['A','C'],'four')]]
    r = report(block('A'),block('B'),block('C'),interfaces=interfaces)
    result = calculate_preparation_packing(r,object_id='o')
    assert result['checking_minutes'] == 90
    assert result['interfaces'][0]['source_refs'] == ['one','two']
    r['objects']['o']['preparation_evidence']['interfaces'].append(
        {'unit_ids':['A','B'],'interface_id':'second physical interface','source_refs':['five']})
    assert calculate_preparation_packing(r,object_id='o')['checking_minutes'] == 120


def test_missing_legacy_interfaces_and_dimensions_remain_unknown_not_zero_or_small():
    r = report(block('A',(600,None,400)))
    del r['objects']['o']['preparation_evidence']
    result=calculate_preparation_packing(r,object_id='o')
    assert not result['checking_known'] and result['packing_partial']
    assert result['packing_units'][0]['id']=='A' and result['packing_units'][0]['size'] is None
    assert result['packing_units'][0]['man_minutes'] is None
    assert preparation_pay_metrics({'preparation':result}) == (None,None,None)
    r['objects']['o']['blocks'][0]['envelope']['width']['mm']=2500
    result=calculate_preparation_packing(r,object_id='o')
    assert result['size_counts']=={'XL':1} and result['packing_minutes']==25
    assert preparation_pay_metrics({'preparation':result})[2]['partial']


def test_loose_parts_form_one_audited_bundle_without_dropping_physical_quantities():
    r=report(block('A'))
    r['objects']['o']['parts']=[{'owner_id':'top','role':'worktop','quantity':2,
        'dimensions':{'length':{'mm':1000},'width':{'mm':500},'thickness':{'mm':20}}}]
    result=calculate_preparation_packing(r,object_id='o')
    bundle=result['packing_units'][1]
    assert bundle['id']=='top' and bundle['dimensions_mm']=={'width':1000,'height':500,'depth':40}
    assert bundle['size']=='M' and result['packing_minutes']==25


def rectangle(ident,x,y,w=10,h=10):
    return {'id':ident,'bbox':[x,y,x+w,y+h], 'polygon':[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]}


def test_native_shared_edges_count_once_and_point_contact_is_not_a_join():
    r=report(block('A'),block('B'),block('C'))
    analyze={'source_audit_sha256':'source','objects':{'o':{'planner':{'blocks':[
        {'id':i,'appearances':{'v':[i],'v2':[i]}} for i in ['A','B','C']]}}}}
    contours=[rectangle('A',0,0),rectangle('B',10,0),rectangle('C',20,10)]
    views=[{'view_id':v,'candidates':contours} for v in ['v','v2']]
    before=deepcopy(r)
    attach_preparation_evidence(r,analyze,views)
    evidence=r['objects']['o']['preparation_evidence']
    assert evidence['status']=='ready' and len(evidence['interfaces'])==1
    assert len(evidence['interfaces'][0]['source_refs'])==2
    assert calculate_preparation_packing(r,object_id='o')['checking_minutes']==30
    assert r['objects']['o']['blocks']==before['objects']['o']['blocks']


def test_no_native_block_evidence_does_not_claim_zero_interfaces():
    r=report(block('A'))
    analyze={'source_audit_sha256':'source','objects':{'o':{'planner':{'blocks':[{'id':'A','appearances':{}}]}}}}
    attach_preparation_evidence(r,analyze,[])
    assert r['objects']['o']['preparation_evidence']['status']=='partial'
    assert not calculate_preparation_packing(r,object_id='o')['checking_known']


@pytest.mark.parametrize('invalid',["unknown_owner","zero_quantity","conflicting_quantity"])
def test_invalid_interface_evidence_never_becomes_a_confirmed_zero_or_guessed_charge(invalid):
    row={'unit_ids':['A','B'],'quantity':1,'source_refs':['one']}
    rows=[row]
    if invalid=='unknown_owner':row['unit_ids'][1]='missing'
    elif invalid=='zero_quantity':row['quantity']=0
    else:rows.append({'unit_ids':['B','A'],'quantity':2,'source_refs':['two']})
    result=calculate_preparation_packing(report(block('A'),block('B'),interfaces=rows),object_id='o')
    assert not result['checking_known']
    assert preparation_pay_metrics({'preparation':result})[0] is None
    assert preparation_pay_metrics({'preparation':result})[2]['partial']
    if invalid=='conflicting_quantity':
        assert result['interfaces'][0]['source_refs']==['one','two']
        assert result['interfaces'][0]['man_minutes'] is None


def test_saved_side_parts_resolve_depth_with_front_thickness_and_keep_source_immutable():
    r=report(block('A',(1100,780,None)))
    r['objects']['o']['parts']=[
        {'block_id':'A','role':'carcass_side','owner_id':'A','dimensions':{'width':{'mm':600}}},
        {'block_id':'A','role':'door_front','owner_id':'A','dimensions':{'thickness':{'mm':17}}}]
    before=deepcopy(r)
    result=calculate_preparation_packing(r,object_id='o')
    assert result['packing_units'][0]['dimensions_mm']['depth']==617
    assert result['packing_units'][0]['size']=='L'
    assert r==before


def test_preparation_leaves_are_editable_and_preserve_exact_source_hours():
    from screens.estimation_labor_v1 import _labor_html
    r=report(block('A'),block('B'),interfaces=[{'unit_ids':['A','B'],'source_refs':['drawing']}])
    result=calculate_preparation_packing(r,object_id='o')
    html=_labor_html({'status':'waiting_for_materials','preparation':result})
    assert 'data-field="labor_hours" data-line-id="trial-fit" data-original-value="0.5"' in html
    assert 'data-field="labor_hours" data-line-id="packing"' in html
    assert 'A ↔ B' in html and '1 × 30 min' in html
    assert 'A · S · 1 × 10 min' in html and 'B · S · 1 × 10 min' in html
    for key in ['trial-fit','packing']:
        summary=html.split(f'data-cost-band="{key}"',1)[1].split('</summary>',1)[0]
        assert 'contenteditable="true"' in summary


@pytest.mark.parametrize('broken_source',[False,True])
def test_live_wrapper_adds_only_preparation_and_isolates_evidence_failure(tmp_path,monkeypatch,broken_source):
    import json
    from tools import probe_estimation_v9 as runtime
    from tools.estimation_block_geometry import AUDIT_FILE
    r=report(block('A'),block('B'))
    del r['objects']['o']['preparation_evidence']
    analyze={'source_audit_sha256':'other' if broken_source else 'source',
        'objects':{'o':{'planner':{'blocks':[{'id':b,'appearances':{'v':[b]}} for b in ['A','B']]}}}}
    def pipeline(args,*a,**k):
        args.output.mkdir();(args.output/'geometry').mkdir()
        for name,value in [('parts-check.json',r),('result.json',analyze),
            ('geometry/'+AUDIT_FILE,{'documents':{'document':[{'view_id':'v','candidates':[
                rectangle('A',0,0),rectangle('B',10,0)]}]}})]:
            (args.output/name).write_text(json.dumps(value))
    monkeypatch.setattr(runtime,'run_pipeline',pipeline)
    output=tmp_path/'output'
    actual=runtime.run_parts_check(pdf=tmp_path/'source.pdf',detection_context={},output=output)
    evidence=actual['objects']['o'].pop('preparation_evidence')
    assert actual==r
    assert evidence['status']==('read_failed' if broken_source else 'ready')
    if not broken_source:assert len(evidence['interfaces'])==1
    assert json.loads((output/'parts-check.json').read_text())['objects']['o']['preparation_evidence']==evidence
