from concurrent.futures import Future
from threading import Barrier

import pandas as pd
import pytest
import streamlit as st

from screens import objects, object_detail, file_review
from ui import objects_pricing
from state.session import invalidate_object_detail_cache


def test_review_waits_for_its_own_snapshot_and_failed_preparation_can_retry(monkeypatch):
    st.session_state.clear()
    future = Future()
    monkeypatch.setattr(objects, "submit_object_detail_prefetch", lambda **_: future)
    data = {"rows": [{"object_key": "one", "status": "completed"},
                     {"object_key": "two", "status": "running"}]}
    objects._prefetch_completed_object_details(estimate_id="e", company_id="c", data=data)
    row = objects._with_object_navigation_readiness(data, "e")["rows"][0]
    assert objects._object_navigation_pending(data, "e")
    assert not objects_pricing.review_action_ready(row)
    assert 'aria-disabled="true"' in objects_pricing._review_action_html(row, estimate_id="e", run_id="r")
    assert "detail_navigation_ready" not in data["rows"][0]
    future.set_result({"quantity": 1})
    objects._prefetch_completed_object_details(estimate_id="e", company_id="c", data=data)
    ready = objects._with_object_navigation_readiness(data, "e")
    assert objects_pricing.review_action_ready(ready["rows"][0])
    assert not objects_pricing.review_action_ready(ready["rows"][1])
    assert not objects._object_navigation_pending(data, "e")
    invalidate_object_detail_cache("e")
    future = Future(); future.set_exception(ConnectionError("prepare rejected"))
    for _ in range(2):
        objects._prefetch_completed_object_details(estimate_id="e", company_id="c", data=data)
    row = objects._with_object_navigation_readiness(data, "e")["rows"][0]
    assert not objects_pricing.review_action_ready(row)
    assert '>Retry</a>' in objects_pricing._review_action_html(row, estimate_id="e", run_id="r")
    st.session_state.current_estimate_id = "e"
    objects._open_object_detail("one")
    assert st.session_state.screen == "object_detail"
    assert ("e", "one") not in st.session_state.object_detail_prefetch_failed


def test_pending_timeout_never_duplicates_read_or_exposes_stale_card(monkeypatch):
    st.session_state.clear()
    class PendingFuture(Future):
        def result(self, timeout=None):
            raise TimeoutError()
    pending = PendingFuture()
    st.session_state.object_detail_prefetch_futures = {("e", "one"): pending}
    monkeypatch.setattr(object_detail, "load_object_detail_data", lambda **_: pytest.fail("Duplicate read"))
    monkeypatch.setattr(st, "error", lambda *_: None)
    monkeypatch.setattr(object_detail, "_back_to_objects_button", lambda: None)
    assert object_detail._load_object_detail_or_render_error(object_detail.ObjectDetailContext("e", "one", "r")) is None
    assert st.session_state.object_detail_prefetch_futures[("e", "one")] is pending
    assert st.session_state.object_detail_quantity_check == ("e", "one")


def test_quantity_changed_while_prefetch_ran_rejects_old_snapshot(monkeypatch):
    st.session_state.clear()
    class CompletingFuture(Future):
        def result(self, timeout=None):
            self.set_result({"quantity": 1})
            return super().result(timeout=timeout)
    key = ("e", "one")
    st.session_state.object_detail_quantity_check = key
    st.session_state.object_detail_prefetch_futures = {key: CompletingFuture()}
    monkeypatch.setattr(object_detail, "load_object_detail_quantity", lambda **_: 3)
    monkeypatch.setattr(object_detail, "load_object_detail_data", lambda **_: {"quantity": 3})
    assert object_detail._load_object_detail_or_render_error(object_detail.ObjectDetailContext("e", "one", "r"))["quantity"] == 3


@pytest.mark.parametrize("kind", ["naming", "preview", "document_identity"])
def test_local_pending_work_does_not_block_file_review_on_durable_reads(kind):
    st.session_state.clear()
    future = Future()
    st.session_state.file_review_deferred_work = {"run_id": "r", kind: True}
    st.session_state[f"current_{kind}_future"] = future
    calls = []
    def loader(run):
        calls.append(run)
        return {"status": "succeeded", "canonical": True}
    assert file_review._deferred_publication("r", kind, loader) == {"status": "pending"}
    assert calls == []
    assert file_review._deferred_publication("other", kind, loader)["canonical"]
    future.set_result({"status": "succeeded", "possibly_stale": True})
    assert file_review._deferred_publication("r", kind, loader) == {"status": "succeeded", "canonical": True}
    assert calls == ["other", "r"]


def test_cold_file_review_reads_overlap_only_after_ownership_is_accepted(monkeypatch):
    from use_cases import rfq_processing as rfq
    from state import company_auth
    barrier = Barrier(3)
    calls = []
    client = object()
    monkeypatch.setattr(rfq, "get_supabase_client", lambda: client)
    monkeypatch.setattr(company_auth, "company_auth_enabled", lambda: True)
    monkeypatch.setattr(rfq, "get_company_id", lambda: "c")
    monkeypatch.setattr(rfq, "assert_run_owned", lambda *args: calls.append("owned"))
    def read(kind, frame):
        assert calls[0] == "owned"
        calls.append(kind)
        barrier.wait(timeout=2)
        return frame
    monkeypatch.setattr(rfq, "fetch_rfq_run", lambda *_: read("run", pd.DataFrame([{"run_id": "r", "file_name": "source.pdf"}])))
    monkeypatch.setattr(rfq, "fetch_rfq_detected_objects", lambda *_: read("objects", pd.DataFrame()))
    monkeypatch.setattr(rfq, "fetch_agent_usage_events", lambda *_: read("usage", pd.DataFrame()))
    result = rfq.load_file_review_data("r")
    assert result["run"]["file_name"] == "source.pdf"
    assert set(calls) == {"owned", "run", "objects", "usage"}


@pytest.mark.parametrize("costs_changed", [False, True])
def test_approval_keeps_snapshots_only_when_costs_are_unchanged(monkeypatch, costs_changed):
    st.session_state.clear()
    st.session_state.object_detail_data_cache = {("e", "one"): {"quantity": 1}}
    st.session_state.labor_v1_comparisons = {("c", "r", "e", "one"): {"status": "ready"}}
    monkeypatch.setattr(object_detail, "approve_object_estimate", lambda **_: {"costs_changed": costs_changed})
    object_detail._approve_current_object_and_return(estimate_id="e", object_id="one")
    assert st.session_state.screen == "objects"
    if costs_changed:
        assert not st.session_state.object_detail_data_cache
        assert "e" in st.session_state.objects_estimation_cache_dirty
    else:
        assert ("e", "one") in st.session_state.object_detail_data_cache
        assert ("c", "r", "e", "one") in st.session_state.labor_v1_comparisons
        assert "e" in st.session_state.objects_estimation_pricing_dirty


def test_completed_preparation_seeds_existing_labor_cache_once(monkeypatch):
    st.session_state.clear()
    identity = ("c", "r", "e", "one")
    future = Future()
    future.set_result({"quantity": 1, "_prepared_labor": (identity, {"status": "ready", "overhead_context": {"status": "ready"}})})
    st.session_state.object_detail_prefetch_futures = {("e", "one"): future}
    objects._prefetch_completed_object_details(estimate_id="e", company_id="c", data={"rows": [{"object_key": "one", "status": "completed"}]})
    assert st.session_state.labor_v1_comparisons[identity]["overhead_context"]["status"] == "ready"
    assert "_prepared_labor" not in st.session_state.object_detail_data_cache[("e", "one")]
    invalidate_object_detail_cache("e")
    assert not st.session_state.labor_v1_comparisons


def test_newer_cached_quantity_is_not_replaced_from_an_older_project_render(monkeypatch):
    st.session_state.clear()
    st.session_state.object_detail_data_cache = {("e", "one"): {"quantity": 3}}
    monkeypatch.setattr(objects, "submit_object_detail_prefetch", lambda **_: pytest.fail("Old Project row restarted preparation"))
    objects._prefetch_completed_object_details(estimate_id="e", company_id="c", data={"rows": [
        {"object_key": "one", "status": "completed", "quantity": 1},
    ]})
    assert st.session_state.object_detail_data_cache[("e", "one")]["quantity"] == 3


@pytest.mark.parametrize("fragment_id", [None, "only-object-preparation"])
def test_preparation_refresh_cancellation_is_scoped_and_never_reruns_app(monkeypatch, fragment_id):
    from types import SimpleNamespace
    from ui import objects_workflow
    messages = []
    monkeypatch.setattr(objects_workflow, "get_script_run_ctx", lambda **_: SimpleNamespace(
        current_fragment_id=fragment_id, enqueue=messages.append))
    objects_workflow.stop_completed_preparation_refresh()
    if fragment_id is None:
        assert messages == []
    else:
        assert len(messages) == 1
        assert messages[0].WhichOneof("type") == "stop_auto_rerun"
        assert list(messages[0].stop_auto_rerun.fragment_ids) == [fragment_id]
