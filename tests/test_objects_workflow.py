from copy import deepcopy
import pytest

from screens import objects
from ui import objects_workflow
from ui.objects_workflow import pricing_signature


def data():
    return {"rows": [{"object_key": "one", "quantity": 1, "self_cost_unit": 100, "sale_price_unit": 130,
                      "sale_price_total": 130, "reviewed": True, "status": "completed"}],
            "project_costs": [{"object_key": "delivery", "sale_price_unit": 4}],
            "summary": {"project_price": 134, "vat": 24.12, "total": 158.12}}


def test_back_refreshes_only_current_estimate_without_dropping_detail_cache(monkeypatch):
    from screens import object_detail
    cache={'saved':'unchanged'}
    class Session(dict):
        __getattr__=dict.__getitem__
        __setattr__=dict.__setitem__
    session=Session(current_estimate_id='e',current_object_id='one',object_detail_data_cache=cache,
                    objects_estimation_cache_dirty={'another'})
    monkeypatch.setattr(object_detail.st,'session_state',session)
    object_detail._return_to_objects()
    assert session['objects_estimation_cache_dirty']=={'another'}
    assert session['objects_estimation_pricing_dirty']=={'e'}
    assert session['object_detail_data_cache']==cache
    assert session['screen']=='objects'


def test_commercial_refresh_reads_saved_inputs_without_cost_or_material_rebuild(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    original=data()
    original['material_plan']={'preserved':True}
    before=deepcopy(original)
    monkeypatch.setattr(estimation,'get_supabase_client',lambda:object())
    monkeypatch.setattr(estimation,'_assert_screen_estimate_access',lambda *a:None)
    monkeypatch.setattr(estimation,'fetch_rfq_object_estimates',lambda *a:pd.DataFrame([
        {'object_id':'one','company_id':'c','quantity':2,'self_cost_ex_vat':100,'status':'completed','approved':False}]))
    monkeypatch.setattr(estimation,'fetch_rfq_estimate_pricing_overrides',lambda *a:pd.DataFrame([
        {'object_key':'one','field':'sale_price_unit','value':175},
        {'object_key':'delivery','field':'sale_price_unit','value':123},
        {'object_key':'installation','field':'sale_price_unit','value':321}]))
    monkeypatch.setattr(estimation,'fetch_company_overhead_settings',lambda *a:pd.DataFrame([{'vat_percent':18}]))
    def forbidden(*a,**k):raise AssertionError('Price refresh rebuilt costs/materials')
    monkeypatch.setattr(estimation,'_ensure_full_object_costs',forbidden)
    monkeypatch.setattr(estimation,'fetch_rfq_estimate_material_plan',forbidden)
    result=estimation.refresh_objects_estimation_prices('e',original)
    assert result['rows'][0]['quantity']==2
    assert result['rows'][0]['sale_price_total']==350
    assert result['summary']['project_price']==794
    assert result['material_plan']==original['material_plan']
    assert original==before


@pytest.mark.parametrize("source", ["cache", "prefetch"])
def test_review_rejects_stale_quantity_snapshot_and_keeps_other_cards(monkeypatch, source):
    from concurrent.futures import Future
    from contextlib import nullcontext
    from screens import object_detail
    key=("e","one"); old={"quantity":1}; fresh={"quantity":2,"sections":["canonical"]}
    future=Future();future.set_result(old)
    session={"object_detail_quantity_check":key,"object_detail_data_cache":{("e","other"):old},
             "object_detail_prefetch_futures":{},"object_detail_data_cache_dirty":set()}
    session["object_detail_data_cache" if source=="cache" else "object_detail_prefetch_futures"][key]=old if source=="cache" else future
    monkeypatch.setattr(object_detail.st,"session_state",session)
    monkeypatch.setattr(object_detail.st,"spinner",lambda *a,**k:nullcontext())
    reads=[];loads=[]
    monkeypatch.setattr(object_detail,"load_object_detail_quantity",lambda **k:reads.append(k) or 2)
    monkeypatch.setattr(object_detail,"load_object_detail_data",lambda **k:loads.append(k) or fresh)
    context=object_detail.ObjectDetailContext("e","one","r")
    assert object_detail._load_object_detail_or_render_error(context) is fresh
    assert session["object_detail_data_cache"][("e","other")] is old
    assert len(reads)==len(loads)==1
    assert object_detail._load_object_detail_or_render_error(context) is fresh
    assert len(reads)==len(loads)==1, "Editing rerenders must not repeat quantity reads"


def test_review_keeps_matching_snapshot_without_loading_costs(monkeypatch):
    from screens import object_detail
    key=("e","one");snapshot={"quantity":2,"sections":["preserved"]}
    monkeypatch.setattr(object_detail.st,"session_state",{
        "object_detail_quantity_check":key,"object_detail_data_cache":{key:snapshot}})
    monkeypatch.setattr(object_detail,"load_object_detail_quantity",lambda **k:2)
    monkeypatch.setattr(object_detail,"load_object_detail_data",lambda **k:pytest.fail("Unchanged card reloaded costs"))
    assert object_detail._load_object_detail_or_render_error(object_detail.ObjectDetailContext("e","one","r")) is snapshot


def test_quantity_read_failure_never_exposes_old_card_on_rerender(monkeypatch):
    from screens import object_detail
    key=("e","one");session={"object_detail_quantity_check":key,"object_detail_data_cache":{key:{"quantity":1}}}
    monkeypatch.setattr(object_detail.st,"session_state",session)
    def rejected(**k):raise PermissionError("Quantity unavailable")
    monkeypatch.setattr(object_detail,"load_object_detail_quantity",rejected)
    errors=[];monkeypatch.setattr(object_detail.st,"error",errors.append)
    monkeypatch.setattr(object_detail,"_back_to_objects_button",lambda:None)
    for _ in range(2):
        assert object_detail._load_object_detail_or_render_error(object_detail.ObjectDetailContext("e","one","r")) is None
    assert len(errors)==2 and session["object_detail_quantity_check"]==key


def test_quantity_projection_is_scoped_and_checks_access_before_read(monkeypatch):
    from use_cases import estimation
    client=object();calls=[]
    monkeypatch.setattr(estimation,"get_supabase_client",lambda:client)
    monkeypatch.setattr(estimation,"_assert_screen_estimate_access",lambda *a,**k:calls.append("access"))
    monkeypatch.setattr(estimation,"fetch_rfq_object_quantity",lambda c,**k:calls.append((c,k)) or 3)
    assert estimation.load_object_detail_quantity(estimate_id="e",object_id="one")==3
    assert calls==["access",(client,{"estimate_id":"e","object_id":"one"})]
    def rejected(*a,**k):raise PermissionError("foreign")
    monkeypatch.setattr(estimation,"_assert_screen_estimate_access",rejected)
    with pytest.raises(PermissionError):estimation.load_object_detail_quantity(estimate_id="foreign",object_id="one")
    assert len(calls)==2


@pytest.mark.parametrize("field,value", [("quantity", 2), ("self_cost_unit", 110), ("sale_price_unit", 150), ("sale_price_total", 150), ("reviewed", False)])
def test_confirmation_is_bound_to_the_current_review_and_commercial_basis(field, value):
    before = data()
    after = deepcopy(before)
    after["rows"][0][field] = value
    assert pricing_signature(before) != pricing_signature(after)


def test_project_allocation_changes_also_require_setting_prices_again():
    before = data()
    after = deepcopy(before)
    after["project_costs"][0]["sale_price_unit"] = 10
    assert pricing_signature(before) != pricing_signature(after)


def test_telemetry_and_progress_refresh_do_not_revoke_a_confirmation():
    before = data()
    after = deepcopy(before)
    after["rows"][0].update(progress_percent=100, progress_label="Ready", elapsed=2)
    after["timings"] = {"total": 4}
    after["summary"]["project_pricing_ready"] = True
    assert pricing_signature(before) == pricing_signature(after)


def test_three_stages_follow_real_review_confirmation_and_proposal():
    state = data()
    assert 'data-stage="2" data-state="current"' in objects_workflow.stages_html(state, prices_set=False, proposal_ready=False)
    assert 'data-stage="3" data-state="current"' in objects_workflow.stages_html(state, prices_set=True, proposal_ready=False)
    assert objects_workflow.stages_html(state, prices_set=True, proposal_ready=True).count('data-state="complete"') == 3
    state["rows"][0]["reviewed"] = False
    assert 'data-stage="1" data-state="current"' in objects_workflow.stages_html(state, prices_set=False, proposal_ready=False)


def test_set_prices_accepts_saved_values_without_changing_them(monkeypatch):
    saved = data()
    before = deepcopy(saved)
    session = {}
    monkeypatch.setattr(objects.st, "session_state", session)
    monkeypatch.setattr(objects, "_persisted_objects_state", lambda _: objects.ObjectsScreenState(data=saved))
    monkeypatch.setattr(objects, "_cache_routed_objects_data", lambda **_: None)
    objects._set_objects_prices(estimate_id="e")
    assert saved == before
    assert session["objects_set_price_basis"]["e"] == pricing_signature(saved)
    assert objects_workflow.prices_are_set("e", saved)


def test_failed_saved_read_cannot_confirm_prices(monkeypatch):
    session = {}
    monkeypatch.setattr(objects.st, "session_state", session)
    monkeypatch.setattr(objects, "_persisted_objects_state", lambda _: objects.ObjectsScreenState(data=data(), cache_warning="stale read"))
    objects._set_objects_prices(estimate_id="e")
    assert "e" not in session["objects_set_price_basis"]
    assert session["final_approval_error"]
def test_project_title_preserves_file_review_value_without_identity_repair():
    from ui.objects_workflow import project_title
    assert project_title(' A3 ') == 'Project A3'
    assert project_title('ADA') == 'Project ADA'
    for value in (None,'','  ','Unknown','unknown'):
        assert project_title(value) == 'Project'


def test_production_days_are_commercial_metadata_and_never_a_price():
    import pandas as pd
    from use_cases.estimation import production_time_from_overrides,_pricing_overrides_by_object
    from ui.objects_pricing import pricing_table_html
    overrides=pd.DataFrame([{'object_key':'__project__','field':'production_time_working_days','value':15},
                            {'object_key':'delivery','field':'sale_price_unit','value':200}])
    assert production_time_from_overrides(overrides)==15
    assert _pricing_overrides_by_object(overrides)=={'delivery':200}
    html=pricing_table_html(rows=[],project_costs=[{'object_key':'delivery','name':'Delivery'}],
                            summary={},estimate_id='e',run_id='r',production_time_working_days=15)
    assert html.index('Estimated production time') < html.index('>Delivery<')
    assert '>15</div>' in html and 'preliminary estimate in working days<br>installation time not included' in html
    assert '₪15' not in html


def test_generate_consumes_confirmed_values_without_another_saved_data_read(monkeypatch):
    from copy import deepcopy
    class Session(dict):
        __getattr__ = dict.__getitem__
        __setattr__ = dict.__setitem__
    saved = data()
    session = Session(objects_estimation_data_cache={'e':saved})
    monkeypatch.setattr(objects.st,'session_state',session)
    monkeypatch.setattr(objects,'_persisted_objects_state',lambda _:objects.ObjectsScreenState(data=saved))
    monkeypatch.setattr(objects,'_cache_routed_objects_data',lambda **_:None)
    objects._set_objects_prices(estimate_id='e')
    monkeypatch.setattr(objects,'_persisted_objects_state',lambda _:(_ for _ in ()).throw(AssertionError('redundant saved read')))
    captured=[]
    monkeypatch.setattr(objects,'final_approval',lambda **kw:captured.append(kw) or {'proposal_pdf_url':'https://example.test/file.pdf'})
    objects._complete_final_approval(company_id='c',run_id='r',estimate_id='e')
    assert captured[0]['confirmed_data']['rows']==saved['rows']
    assert session['proposal_first_download']['url']=='https://example.test/file.pdf'
    assert not session.final_approval_error
    saved['rows'][0]['sale_price_unit']=999
    objects._complete_final_approval(company_id='c',run_id='r',estimate_id='e')
    assert len(captured)==1
    assert 'Set prices again' in session.final_approval_error


def test_document_relevant_changes_invalidate_price_confirmation():
    from copy import deepcopy
    before=data()
    for field,value in [('advance_payment_percent',70),('project_name','Changed')]:
        after=deepcopy(before);after[field]=value
        assert pricing_signature(after)!=pricing_signature(before)
    after=deepcopy(before);after['rows'][0]['materials']='Changed fronts'
    assert pricing_signature(after)!=pricing_signature(before)


@pytest.mark.parametrize('mutation',[
    lambda d: d['rows'][0].update(sale_price_unit=150),
    lambda d: d['rows'][0].update(quantity=3),
    lambda d: d['rows'][0].update(proposal_input_basis='edited even with equal rounded cost'),
    lambda d: d.update(production_time_working_days=18),
    lambda d: d.update(design_partner='New partner'),
    lambda d: d.update(client='New client'),
    lambda d: d.update(proposal_source={'settings':{'advance_payment_percent':50}}),
])
def test_any_persisted_proposal_input_revokes_issued_download_and_confirmation(monkeypatch,mutation):
    original=data();signature=pricing_signature(original)
    session={'objects_set_price_basis':{'e':signature},'proposal_basis_by_estimate':{'e':signature},
             'proposal_pdf_urls_by_estimate':{'e':'issued-v1.pdf'},
             'objects_confirmed_proposal_data':{'e':original}}
    monkeypatch.setattr(objects_workflow.st,'session_state',session)
    changed=deepcopy(original);mutation(changed)
    assert objects_workflow.current_proposal_url('e',changed) is None
    assert not objects_workflow.prices_are_set('e',changed)
    assert 'e' not in session['objects_confirmed_proposal_data']
    assert not session['proposal_pdf_urls_by_estimate']['e']


def test_generation_retry_reuses_request_but_next_changed_confirmation_gets_new_one(monkeypatch):
    saved=data();session={}
    monkeypatch.setattr(objects.st,'session_state',session)
    monkeypatch.setattr(objects,'_persisted_objects_state',lambda _:objects.ObjectsScreenState(data=saved))
    monkeypatch.setattr(objects,'_cache_routed_objects_data',lambda **_:None)
    objects._set_objects_prices(estimate_id='e')
    first=session['objects_confirmed_proposal_data']['e']['proposal_request_id']
    objects._set_objects_prices(estimate_id='e')
    assert session['objects_confirmed_proposal_data']['e']['proposal_request_id']==first
    saved['rows'][0]['sale_price_unit']=999
    objects._set_objects_prices(estimate_id='e')
    assert session['objects_confirmed_proposal_data']['e']['proposal_request_id']!=first


def test_numeric_json_roundtrip_and_empty_optional_metadata_keep_same_identity():
    from decimal import Decimal
    before=data();after=deepcopy(before)
    before['rows'][0]['quantity']=Decimal('1.0');after['rows'][0]['quantity']=1
    before['client']='unknown';after['client']=None
    assert pricing_signature(before)==pricing_signature(after)


def test_read_or_approval_timestamps_do_not_invalidate_unchanged_inputs():
    before=data();after=deepcopy(before)
    after['rows'][0]['updated_at']='new read/approval timestamp'
    assert pricing_signature(before)==pricing_signature(after)


@pytest.mark.parametrize('ok',[False,True])
def test_profile_ack_revokes_only_the_saved_company_and_only_after_success(monkeypatch,ok):
    from types import SimpleNamespace
    from screens import company_profile
    session={'objects_estimation_data_cache':{'e':{'company_id':'one'},'other':{'company_id':'two'}},
             'objects_set_price_basis':{'e':'confirmed','other':'foreign'},
             'proposal_pdf_urls_by_estimate':{'e':'v1.pdf','other':'foreign.pdf'}}
    monkeypatch.setattr(company_profile.st,'session_state',session)
    monkeypatch.setattr(company_profile.st,'markdown',lambda *a,**k:None)
    company_profile._profile_save_ack(SimpleNamespace(company_id='one'),'contacts',ok=ok)
    assert session['proposal_pdf_urls_by_estimate']['e']==(None if ok else 'v1.pdf')
    assert session['proposal_pdf_urls_by_estimate']['other']=='foreign.pdf'


def test_confirming_after_issuance_starts_a_new_cycle_even_if_an_edit_was_reverted(monkeypatch):
    saved=data();basis=pricing_signature(saved)
    session={'objects_set_price_basis':{'e':basis},'proposal_basis_by_estimate':{'e':basis},
             'objects_confirmed_proposal_data':{'e':{**saved,'proposal_request_id':'old'}},
             'proposal_pdf_urls_by_estimate':{'e':'v1.pdf'}}
    monkeypatch.setattr(objects.st,'session_state',session)
    monkeypatch.setattr(objects,'_persisted_objects_state',lambda _:objects.ObjectsScreenState(data=saved))
    monkeypatch.setattr(objects,'_cache_routed_objects_data',lambda **_:None)
    objects._set_objects_prices(estimate_id='e')
    assert session['proposal_pdf_urls_by_estimate']['e'] is None
    assert session['objects_confirmed_proposal_data']['e']['proposal_request_id']!='old'
    assert objects_workflow.prices_are_set('e',saved)
