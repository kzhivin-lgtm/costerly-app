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
