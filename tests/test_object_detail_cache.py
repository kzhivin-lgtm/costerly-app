from concurrent.futures import Future

import pytest
import streamlit as st

from screens import object_detail
from screens import objects
from state.session import invalidate_object_detail_cache, reset_new_estimate_session
from use_cases import object_detail_runtime


def test_object_detail_uses_ready_session_snapshot_without_a_second_read(monkeypatch):
    st.session_state.clear()
    context = object_detail.ObjectDetailContext(
        estimate_id="estimate-1", object_id="object-1", run_id="run-1",
    )
    expected = {"name": "Cabinet", "sections": []}
    st.session_state.object_detail_data_cache = {
        (context.estimate_id, context.object_id): expected,
    }
    st.session_state.object_detail_data_cache_dirty = set()

    monkeypatch.setattr(
        object_detail,
        "load_object_detail_data",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected database read")),
    )

    assert object_detail._load_object_detail_or_render_error(context) == expected


def test_object_detail_consumes_completed_prefetch_snapshot(monkeypatch):
    st.session_state.clear()
    context = object_detail.ObjectDetailContext(
        estimate_id="estimate-1", object_id="object-1", run_id="run-1",
    )
    prefetched = Future()
    prefetched.set_result({"name": "Cabinet", "sections": []})
    st.session_state.object_detail_prefetch_futures = {
        (context.estimate_id, context.object_id): prefetched,
    }

    monkeypatch.setattr(
        object_detail,
        "load_object_detail_data",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected fallback read")),
    )

    assert object_detail._load_object_detail_or_render_error(context)["name"] == "Cabinet"
    assert st.session_state.object_detail_data_cache[("estimate-1", "object-1")]["name"] == "Cabinet"
    assert st.session_state.object_detail_prefetch_futures == {}


def test_invalidating_estimate_discards_all_its_detail_cache_and_prefetches():
    st.session_state.clear()
    old_prefetch = Future()
    st.session_state.object_detail_data_cache = {
        ("estimate-old", "object-1"): {"name": "Old"},
        ("estimate-other", "object-2"): {"name": "Other"},
    }
    st.session_state.object_detail_prefetch_futures = {
        ("estimate-old", "object-1"): old_prefetch,
        ("estimate-other", "object-2"): Future(),
    }
    st.session_state.object_detail_prefetch_failed = {
        ("estimate-old", "object-1"),
        ("estimate-other", "object-2"),
    }

    invalidate_object_detail_cache("estimate-old")

    assert ("estimate-old", "object-1") not in st.session_state.object_detail_data_cache
    assert ("estimate-other", "object-2") in st.session_state.object_detail_data_cache
    assert ("estimate-old", "object-1") not in st.session_state.object_detail_prefetch_futures
    assert ("estimate-other", "object-2") in st.session_state.object_detail_prefetch_futures
    assert ("estimate-old", "object-1") not in st.session_state.object_detail_prefetch_failed
    assert ("estimate-other", "object-2") in st.session_state.object_detail_prefetch_failed


def test_new_estimate_reset_drops_object_detail_snapshots_and_prefetches():
    st.session_state.clear()
    st.session_state.current_run_id = "run-old"
    st.session_state.object_detail_data_cache = {("estimate-old", "object-1"): {}}
    st.session_state.object_detail_data_cache_dirty = {"estimate-old"}
    st.session_state.object_detail_prefetch_futures = {("estimate-old", "object-1"): Future()}
    st.session_state.object_detail_prefetch_failed = {("estimate-old", "object-1")}

    reset_new_estimate_session(clear_upload_widget=False)

    assert st.session_state.object_detail_data_cache == {}
    assert st.session_state.object_detail_data_cache_dirty == set()
    assert st.session_state.object_detail_prefetch_futures == {}
    assert st.session_state.object_detail_prefetch_failed == set()


@pytest.mark.parametrize("legacy_state", [False, True])
def test_reopened_object_can_save_materials_after_new_estimate(monkeypatch, legacy_state):
    st.session_state.clear()
    context = object_detail.ObjectDetailContext("estimate-1", "object-1", "run-1")
    key = (context.estimate_id, context.object_id)
    scope = list(key)
    st.session_state.object_detail_material_edit_results = {key: {"id": "old"}}
    reset_new_estimate_session(clear_upload_widget=True)
    assert "object_detail_material_edit_results" not in st.session_state
    if legacy_state:
        st.session_state.object_detail_material_edit_results = None

    st.session_state.current_estimate_id = context.estimate_id
    st.session_state.current_object_id = context.object_id
    st.session_state.current_run_id = context.run_id
    edits = [{"field": "required_material", "lineId": "sheet-1", "value": "2"}]
    request = {"id": "new", "scope": scope, "edits": edits}
    receipts = []
    saved = []
    future = Future()
    future.set_result(None)

    def bridge(*, result, **_):
        receipts.append(result)
        return request

    def save(**kwargs):
        saved.append(kwargs)
        return future

    monkeypatch.setattr(object_detail, "material_edit_bridge", bridge)
    monkeypatch.setattr(object_detail, "save_object_detail_material_edits", save)
    monkeypatch.setattr(object_detail, "load_object_detail_material_receipt", lambda **_: {
        "sections": [], "self_cost": {"excl_vat": 200}, "quantity": 1,
    })
    monkeypatch.setattr(st, "rerun", lambda *, scope: None)

    object_detail._material_editor.__wrapped__(context)
    object_detail._material_editor.__wrapped__(context)

    assert saved == [{"estimate_id": "estimate-1", "object_id": "object-1", "edits": edits}]
    assert receipts[0] is None
    assert receipts[1]["id"] == "new"
    assert receipts[1]["self_cost"]["excl_vat"] == 200


def test_prefetch_runtime_passes_explicit_company_scope(monkeypatch):
    captured = {}

    def fake_load(**kwargs):
        captured.update(kwargs)
        return {"name": "Cabinet"}

    monkeypatch.setattr(object_detail_runtime, "load_object_detail_data", fake_load)

    result = object_detail_runtime.submit_object_detail_prefetch(
        estimate_id="estimate-1", object_id="object-1", company_id="610",
    ).result(timeout=2)

    assert result == {"name": "Cabinet"}
    assert captured == {
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }


def test_completed_object_prefetch_runs_without_the_global_material_plan(monkeypatch):
    st.session_state.clear()
    prefetch = Future()
    submitted = []

    def submit(**kwargs):
        submitted.append(kwargs)
        return prefetch

    monkeypatch.setattr(objects, "submit_object_detail_prefetch", submit)
    data = {
        "material_plan_ready": False,
        "rows": [{"object_key": "object-1", "status": "completed"}],
    }

    objects._prefetch_completed_object_details(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    assert submitted == [{
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }]

    prefetch.set_result({"name": "Cabinet", "sections": []})
    objects._prefetch_completed_object_details(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    assert st.session_state.object_detail_data_cache[("estimate-1", "object-1")]["name"] == "Cabinet"


def test_review_action_remains_a_link_while_detail_is_uncached():
    from ui import objects_pricing

    html = objects_pricing._review_action_html(
        {"object_key": "object-1", "status": "completed"},
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert ">Review</a>" in html
    assert "aria-disabled" not in html
    assert "object_id=object-1" in html


def test_failed_prefetch_falls_back_once_without_fragment_retry(monkeypatch):
    st.session_state.clear()
    prefetch = Future()
    prefetch.set_exception(RuntimeError("temporary database error"))
    submitted = []

    def submit(**kwargs):
        submitted.append(kwargs)
        return prefetch

    monkeypatch.setattr(objects, "submit_object_detail_prefetch", submit)
    data = {"rows": [{"object_key": "object-1", "status": "completed"}]}

    objects._prefetch_completed_object_details(
        estimate_id="estimate-1", company_id="610", data=data,
    )
    objects._prefetch_completed_object_details(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    objects._prefetch_completed_object_details(estimate_id="estimate-1", company_id="610", data=data)
    assert ("estimate-1", "object-1") in st.session_state.object_detail_prefetch_failed
    assert submitted == [{
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }]


def test_open_second_object_after_return_uses_foreground_read_if_prefetch_is_pending(monkeypatch):
    st.session_state.clear()
    st.session_state.current_estimate_id = "estimate-1"
    running = Future()
    running.set_running_or_notify_cancel()
    st.session_state.object_detail_prefetch_futures = {("estimate-1", "object-2"): running}
    st.session_state.object_detail_data_cache = {("estimate-1", "object-1"): {"name": "First", "quantity": 1}}
    monkeypatch.setattr(object_detail, "load_object_detail_data", lambda **kw: {"name": kw["object_id"]})
    monkeypatch.setattr(object_detail, "load_object_detail_quantity", lambda **kw: 1)
    objects._open_object_detail("object-1")
    assert object_detail._load_object_detail_or_render_error(object_detail._current_object_detail_context()) == {"name": "First", "quantity": 1}
    object_detail._return_to_objects()
    objects._open_object_detail("object-2")
    assert object_detail._load_object_detail_or_render_error(object_detail._current_object_detail_context()) == {"name": "object-2"}
    assert not running.done()


def test_material_save_uses_committed_receipt_without_a_fallible_second_read(monkeypatch):
    st.session_state.clear()
    context=object_detail.ObjectDetailContext('estimate-1','object-1','run-1');key=('estimate-1','object-1')
    st.session_state.current_estimate_id='estimate-1';st.session_state.current_object_id='object-1'
    st.session_state.current_run_id='run-1';st.session_state.screen='object_detail'
    st.session_state.object_detail_data_cache={key:{'name':'Preserved name','preview_url':'preserved-preview',
        'sections':[], 'self_cost':{'vat_percent':18,'excl_vat':100},'quantity':3}}
    receipt={'sections':[{'key':'material','rows':[],'front_panels':[]}],
             'self_cost':{'excl_vat':200,'vat':36,'total':236,'batch_excl_vat':600},
             'quantity':3,'cost_policy':'object_costs_v3_1'}
    future=Future();future.set_result({'_object_detail_receipts':{'object-1':receipt}})
    request={'id':'save-front','scope':list(key),'edits':[{'field':'front_material','lineId':'__front_panels__:g','value':'mdf'}]}
    monkeypatch.setattr(object_detail,'material_edit_bridge',lambda **k:request)
    monkeypatch.setattr(object_detail,'save_object_detail_material_edits',lambda **k:future)
    def failed_read(**k):raise ConnectionError('The acknowledged save must not depend on this read')
    monkeypatch.setattr(object_detail,'load_object_detail_material_receipt',failed_read)
    monkeypatch.setattr(st,'rerun',lambda **k:None)
    object_detail._material_editor.__wrapped__(context)
    result=st.session_state.object_detail_material_edit_results[key]
    assert 'error' not in result
    assert result['self_cost']['excl_vat']==200
    cached=st.session_state.object_detail_data_cache[key]
    assert cached['name']=='Preserved name' and cached['preview_url']=='preserved-preview'
    assert cached['self_cost']['vat_percent']==18 and cached['self_cost']['batch_excl_vat']==600
    assert st.session_state.screen=='object_detail'
