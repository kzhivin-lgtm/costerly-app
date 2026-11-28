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
def test_approval_handoff_uses_committed_receipt_and_canonical_commercial_projection(monkeypatch, costs_changed):
    from screens import estimation_labor_v1 as labor
    st.session_state.clear()
    identity = ("c", "r", "e", "one")
    base = {"quantity": 1, "approved": False, "preview_url": "owned-preview",
            "sections": [{"key": "material", "columns": ["Material"], "rows": ["old"]}]}
    st.session_state.object_detail_data_cache = {("e", "one"): base, ("e", "two"): {"approved": True}}
    st.session_state.labor_v1_comparisons = {identity: {"status": "ready", "overhead_context": {"status": "ready"}}}
    st.session_state.objects_estimation_data_cache = {"e": {"rows": [{"object_key": "one", "status": "completed"}]}}
    receipt = {"sections": [{"key": "material", "rows": ["committed"]}], "cost_quantity": 3, "self_cost": {"excl_vat": 42}}
    monkeypatch.setattr(object_detail, "approve_object_estimate", lambda **_: {
        "costs_changed": costs_changed, **({"material_plan": {"revision": "new", "_object_detail_receipts": {"one": receipt}}} if costs_changed else {})})
    monkeypatch.setattr(object_detail, "load_object_detail_material_receipt", lambda **_: pytest.fail("Receipt was already returned"))
    monkeypatch.setattr(object_detail, "get_supabase_client", object)
    monkeypatch.setattr(labor, "_calculate", lambda *a, **kw: {"status": "ready", "assembly": {}, "preparation": {}})
    monkeypatch.setattr(object_detail, "refresh_objects_estimation_prices", lambda e, cached, **kw: {**cached, **({"material_plan": {"revision": "new"}} if kw.get("refresh_inputs") else {}), "rows": [
        {"object_key": "one", "quantity": 3, "status": "completed", "reviewed": True},
        {"object_key": "two", "status": "completed", "reviewed": not costs_changed}]})
    object_detail._approve_current_object_and_return(estimate_id="e", object_id="one")
    assert st.session_state.screen == "objects"
    data = st.session_state.object_detail_data_cache[("e", "one")]
    assert data["approved"] is True and data["preview_url"] == "owned-preview"
    assert data["sections"][0]["columns"] == ["Material"]
    if costs_changed:
        assert data["sections"][0]["rows"] == ["committed"] and data["cost_quantity"] == 3
        assert ("e", "two") not in st.session_state.object_detail_data_cache
        assert st.session_state.objects_estimation_data_cache["e"]["material_plan"] == {"revision": "new"}
    assert identity in st.session_state.labor_v1_comparisons
    assert "e" not in st.session_state.objects_estimation_cache_dirty
    assert "e" not in st.session_state.objects_estimation_pricing_dirty
    row = objects._with_object_navigation_readiness(st.session_state.objects_estimation_data_cache["e"], "e")["rows"][0]
    assert '>Done</a>' in objects_pricing._review_action_html(row, estimate_id="e", run_id="r")
    monkeypatch.setattr(object_detail, "approve_object_estimate", lambda **_: pytest.fail("Unchanged approved Object wrote again"))
    object_detail._approve_current_object_and_return(estimate_id="e", object_id="one")


@pytest.mark.parametrize("write_fails", [False, True])
def test_approval_failure_is_distinct_from_preparation_failure(monkeypatch, write_fails):
    st.session_state.clear()
    st.session_state.screen = "object_detail"
    st.session_state.object_detail_data_cache = {("e", "one"): {"approved": False}}
    def fail(*a, **kw):
        raise ConnectionError("controlled failure")
    monkeypatch.setattr(object_detail, "approve_object_estimate", fail if write_fails else lambda **_: {"costs_changed": True})
    monkeypatch.setattr(object_detail, "load_object_detail_material_receipt", fail)
    monkeypatch.setattr(object_detail, "report_runtime_failure", lambda *a, **kw: None)
    object_detail._approve_current_object_and_return(estimate_id="e", object_id="one")
    if write_fails:
        assert st.session_state.screen == "object_detail"
        assert st.session_state.object_detail_approval_error
        assert not st.session_state.object_detail_data_cache[("e", "one")]["approved"]
    else:
        assert st.session_state.screen == "objects" and "one" in st.session_state.approved_object_keys
        assert not st.session_state.get("object_detail_approval_error")
        assert not st.session_state.object_detail_data_cache


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
    from streamlit.runtime.scriptrunner_utils.script_run_context import ThreadState
    messages = []
    monkeypatch.setattr(objects_workflow, "get_script_run_ctx", lambda **_: SimpleNamespace(
        enqueue=messages.append))
    ThreadState.initialize()
    with ThreadState.scoped(fragment_id=fragment_id):
        objects_workflow.stop_completed_preparation_refresh()
    if fragment_id is None:
        assert messages == []
    else:
        assert len(messages) == 1
        assert messages[0].WhichOneof("type") == "stop_auto_rerun"
        assert list(messages[0].stop_auto_rerun.fragment_ids) == [fragment_id]


def _real_preparation_fragment():
    import streamlit as st
    from ui.objects_workflow import stop_completed_preparation_refresh
    @st.fragment(run_every=1.5)
    def prepared():
        st.markdown("Prepared Object")
        stop_completed_preparation_refresh()
    prepared()


def test_preparation_refresh_stops_with_real_streamlit_fragment_context():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_function(_real_preparation_fragment).run()
    assert not app.exception
    assert app.markdown[0].value == "Prepared Object"


def test_first_approval_returns_committed_allocation_receipts(monkeypatch):
    from use_cases import estimation, estimation_runtime
    client = object()
    committed = {"revision": "accepted", "_object_detail_receipts": {"one": {"self_cost": {"excl_vat": 42}}}}
    future = Future(); future.set_result(committed)
    calls = []
    monkeypatch.setattr(estimation, "get_supabase_client", lambda: client)
    monkeypatch.setattr(estimation, "_assert_screen_estimate_access", lambda *a: None)
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([
        {"plan_payload": {"material_review_order": []}}]))
    monkeypatch.setattr(estimation, "_object_material_context", lambda *a, **kw: {"run_id": "r", "company_id": "c"})
    monkeypatch.setattr(estimation_runtime, "queue_material_plan_recalculation", lambda **kw: calls.append(kw) or future)
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_approved", lambda *a, **kw: pytest.fail("Allocation approval bypassed"))
    result = estimation.approve_object_estimate(estimate_id="e", object_id="one")
    assert result == {"costs_changed": True, "material_plan": committed}
    assert calls == [{"estimate_id": "e", "run_id": "r", "company_id": "c",
                     "purchase_keys": frozenset(), "approve_objects": ("one",)}]


def test_approval_refresh_preserves_pdf_input_identity_even_when_prices_are_unchanged(monkeypatch):
    from use_cases import estimation
    from use_cases.proposal_basis import pricing_signature
    monkeypatch.setattr(estimation, "get_supabase_client", object)
    monkeypatch.setattr(estimation, "_assert_screen_estimate_access", lambda *a: None)
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *a: pd.DataFrame([
        {"object_id": "one", "company_id": "c", "quantity": 1, "status": "completed", "approved": True, "self_cost_ex_vat": 100}]))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_pricing_overrides", lambda *a: pd.DataFrame())
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *a: pd.DataFrame([{"vat_percent": 18}]))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_material_plan", lambda *a: pd.DataFrame([
        {"updated_at": "new-revision", "plan_status": "planned", "plan_payload": {"status": "planned"}}]))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines", lambda *a: pd.DataFrame([
        {"object_id": "one", "source": estimation._FULL_COST_SOURCE, "raw_agent_json": {"basis_sha256": "new-inputs", "partial": False}}]))
    monkeypatch.setattr(estimation, "_ensure_full_object_costs", lambda *a, **kw: pytest.fail("Approval rebuilt full costs"))
    cached = {"rows": [{"object_key": "one", "proposal_input_basis": "old-inputs"}],
              "proposal_source": {"material_plan_updated_at": "old-revision"}}
    fresh = estimation.refresh_objects_estimation_prices("e", cached, refresh_inputs=True)
    assert fresh["rows"][0]["proposal_input_basis"] == "new-inputs"
    assert fresh["proposal_source"]["material_plan_updated_at"] == "new-revision"
    assert fresh["material_plan"] == {"status": "planned"}
    old_identity = {**fresh, "rows": [{**fresh["rows"][0], "proposal_input_basis": "old-inputs"}],
                    "proposal_source": {**fresh["proposal_source"], "material_plan_updated_at": "old-revision"}}
    assert pricing_signature(fresh) != pricing_signature(old_identity)
