from concurrent.futures import Future
from threading import Barrier

import pandas as pd
import pytest
import streamlit as st

from screens import objects, object_detail, file_review
from ui import objects_pricing
from state.session import invalidate_object_detail_cache


def test_unchanged_back_opens_project_without_price_or_cost_reads(monkeypatch):
    st.session_state.clear()
    data = {"rows": [{"quantity": 3, "sale_price_unit": 77, "reviewed": True}]}
    st.session_state.current_estimate_id = "e"
    st.session_state.objects_estimation_data_cache = {"e": data}
    monkeypatch.setattr(objects, "load_objects_estimation_data", lambda *a, **kw: pytest.fail("Unchanged Back rebuilt costs"))
    monkeypatch.setattr(objects, "refresh_objects_estimation_prices", lambda *a, **kw: pytest.fail("Unchanged Back read prices"))
    object_detail._return_to_objects()
    assert objects._load_objects_screen_data("e") == (data, None)
    assert st.session_state.screen == "objects"


def test_saved_back_keeps_invalidation_and_loads_acknowledged_values(monkeypatch):
    st.session_state.clear()
    st.session_state.current_estimate_id = "e"
    st.session_state.objects_estimation_data_cache = {"e": {"rows": [{"self_cost_unit": 100}]}}
    object_detail._mark_objects_estimation_dirty("e")
    fresh = {"rows": [{"self_cost_unit": 200, "reviewed": False}]}
    monkeypatch.setattr(objects, "load_objects_estimation_data", lambda *a, **kw: fresh)
    object_detail._return_to_objects()
    assert "e" in st.session_state.objects_estimation_cache_dirty
    assert objects._load_objects_screen_data("e", parallel_reads=True, company_id="c") == (fresh, None)


def test_approval_overhead_inputs_overlap_without_changing_context(monkeypatch):
    from screens import estimation_labor_v1 as labor
    import pandas as pd
    from threading import Barrier
    barrier = Barrier(3, timeout=2)
    parallel = False
    def read(value):
        if parallel: barrier.wait()
        return value
    monkeypatch.setattr(labor, "fetch_company_overhead_settings", lambda *a: read(pd.DataFrame([{"vat_percent": 18, "production_monthly_hours": 12}])))
    monkeypatch.setattr(labor, "fetch_company_overhead_monthly", lambda *a: read(pd.DataFrame([{"rent": 5}])))
    monkeypatch.setattr(labor, "with_production_capacity", lambda c, co, s: {**s, **read({"production_monthly_hours": 40})})
    expected = labor._load_overhead_context(object(), "c")
    parallel = True
    assert labor._load_overhead_context(object(), "c", parallel_reads=True) == expected


def test_approval_labor_read_join_matches_sequential_and_reuses_committed_plan(monkeypatch):
    from use_cases import estimation_labor_v1 as labor
    import pandas as pd
    from threading import Barrier
    import json
    parallel = False
    barrier = Barrier(3, timeout=2)
    plan = {"status": "planned"}
    def read(value):
        if parallel: barrier.wait()
        return value
    parts = lambda **kw: read({"status": "ready", "payload": json.dumps({"objects": {"one": {}}})})
    plans = lambda *a: read(pd.DataFrame([{"plan_payload": plan}]))
    machines = lambda *a: read({"availability": {}})
    monkeypatch.setattr("use_cases.block_assembly.calculate_block_assembly", lambda *a, **kw: {"hours": 2})
    monkeypatch.setattr("use_cases.preparation_packing.calculate_preparation_packing", lambda *a, **kw: {"hours": 1})
    monkeypatch.setattr("use_cases.additional_assembly.calculate_additional_assembly", lambda *a, **kw: {})
    def sheet(client, report, *, machinery_loader, plan_loader, plan=None, **kw):
        if plan is None: plan = plan_loader(client, "e").iloc[0]["plan_payload"]
        return {"status": "ready", "plan": plan, "machinery": machinery_loader(client, "c")}
    monkeypatch.setattr(labor, "_load_object_sheet", sheet)
    args = dict(identity=("c", "r", "e", "one"), parts_loader=parts, plan_loader=plans, machinery_loader=machines)
    expected = labor.load_object_labor(object(), **args)
    parallel = True
    assert labor.load_object_labor(object(), **args, parallel_reads=True) == expected
    parallel = False
    args["plan_loader"] = lambda *a: pytest.fail("Approval reread its committed plan")
    assert labor.load_object_labor(object(), **args, plan=plan, parallel_reads=True) == expected


def test_parallel_approved_price_refresh_keeps_canonical_plan_and_pdf_basis(monkeypatch):
    from use_cases import estimation as e
    import pandas as pd
    from threading import Barrier
    barrier = Barrier(5, timeout=2)
    parallel = False
    def read(value):
        if parallel: barrier.wait()
        return value
    monkeypatch.setattr(e, "get_supabase_client", object)
    monkeypatch.setattr(e, "_assert_screen_estimate_access", lambda *a, **kw: None)
    monkeypatch.setattr(e, "fetch_rfq_object_estimates", lambda *a: read(pd.DataFrame([{"object_id": "one", "company_id": "c", "quantity": 3, "approved": True, "self_cost_ex_vat": 123}])) )
    monkeypatch.setattr(e, "fetch_rfq_estimate_pricing_overrides", lambda *a: read(pd.DataFrame([])))
    monkeypatch.setattr(e, "fetch_company_overhead_settings", lambda *a: read(pd.DataFrame([{"vat_percent": 18}])))
    monkeypatch.setattr(e, "fetch_rfq_estimate_material_plan", lambda *a: read(pd.DataFrame([{"plan_status": "planned", "plan_payload": {}, "updated_at": "committed"}])))
    monkeypatch.setattr(e, "fetch_rfq_estimate_lines", lambda *a: read(pd.DataFrame([{"object_id": "one", "source": e._FULL_COST_SOURCE, "raw_agent_json": {"basis_sha256": "new-basis", "partial": False}}])))
    cached = {"company_id": "c", "rows": [{"object_key": "one", "status": "completed"}]}
    expected = e.refresh_objects_estimation_prices("e", cached, refresh_inputs=True)
    parallel = True
    actual = e.refresh_objects_estimation_prices("e", cached, refresh_inputs=True, parallel_reads=True, company_id="c")
    assert actual == expected
    assert actual["rows"][0]["proposal_input_basis"] == "new-basis"
    assert actual["proposal_source"]["material_plan_updated_at"] == "committed"


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


def test_post_save_approval_restores_labor_readiness_before_project_done(monkeypatch):
    from screens import estimation_labor_v1 as labor
    st.session_state.clear()
    st.session_state.screen = "object_detail"
    st.session_state.object_detail_data_cache = {("e", "one"): {
        "company_id": "c", "run_id": "r", "approved": False, "quantity": 1}}
    st.session_state.objects_estimation_data_cache = {"e": {"rows": [{"object_key": "one", "status": "completed"}]}}
    st.session_state.objects_estimation_cache_dirty = {"e"}
    calls = []
    def calculate(client, *, identity, parallel_reads=False):
        assert st.session_state.screen == "object_detail"
        assert parallel_reads is True
        calls.append(identity)
        return {"status": "ready", "assembly": {}, "preparation": {}}
    monkeypatch.setattr(object_detail, "get_supabase_client", object)
    monkeypatch.setattr(object_detail, "approve_object_estimate", lambda **kw: {"costs_changed": False})
    monkeypatch.setattr(labor, "_calculate", calculate)
    monkeypatch.setattr(labor, "_load_overhead_context", lambda *a, **kw: {"status": "ready"})
    monkeypatch.setattr(object_detail, "refresh_objects_estimation_prices", lambda e, data, **kw: {
        **data, "rows": [{"object_key": "one", "status": "completed", "reviewed": True}]})
    object_detail._approve_current_object_and_return(estimate_id="e", object_id="one")
    assert calls == [("c", "r", "e", "one")]
    assert st.session_state.screen == "objects"
    assert st.session_state.labor_v1_comparisons[("c", "r", "e", "one")]["overhead_context"] == {"status": "ready"}
    assert st.session_state.object_detail_data_cache[("e", "one")]["approved"]


def test_preparation_completion_is_painted_before_its_interval_is_stopped(monkeypatch):
    from contextlib import nullcontext
    st.session_state.clear()
    st.session_state.screen = "objects"
    future = Future()
    st.session_state.object_detail_prefetch_futures = {("e", "one"): future}
    data = {"rows": [{"object_key": "one", "status": "completed"}]}
    rendered = []
    stopped = []
    monkeypatch.setattr(objects, "_consume_estimation_future", lambda: None)
    monkeypatch.setattr(objects, "_data_with_object_routes", lambda data, **kw: data)
    monkeypatch.setattr(objects, "_cache_routed_objects_data", lambda **kw: None)
    monkeypatch.setattr(st, "container", lambda **kw: nullcontext())
    monkeypatch.setattr(objects.objects_workflow, "stop_completed_preparation_refresh", lambda: stopped.append(len(rendered)))
    def render(**kw):
        row = objects._with_object_navigation_readiness(kw["screen_state"].data, "e")["rows"][0]
        rendered.append(objects_pricing.review_action_ready(row))
        # Complete during this paint, after readiness has been projected.
        if not future.done(): future.set_result({"quantity": 1})
    monkeypatch.setattr(objects, "_render_objects_table_content", render)
    arguments = dict(estimate_id="e", run_id="r", company_id="c",
                     initial_state=objects.ObjectsScreenState(data=data), live=False, preparing_details=True)
    objects._render_live_objects_content(**arguments)
    assert rendered == [False]
    assert stopped == [], "The only painted frame is still Estimating; cancelling now strands it"
    objects._render_live_objects_content(**arguments)
    assert rendered == [False, True]
    assert stopped == [2]


def test_last_estimate_receipt_is_scoped_and_single_use(monkeypatch):
    from state import company_auth, session
    st.session_state.clear()
    monkeypatch.setattr(session, "get_company_id", lambda: pytest.fail("Callback must leave auth validation to app"))
    company_auth._open_last_estimate({"run_id": "r", "estimate_id": "e"}, company_id="c")
    receipt = st.session_state.file_review_navigation_ready
    assert receipt == {"company_id": "c", "run_id": "r", "last_estimate": True}
    assert file_review._consume_prepared_file_review_navigation(company_id="other", run_id="r") is None
    assert st.session_state.file_review_navigation_ready == receipt
    assert file_review._consume_prepared_file_review_navigation(company_id="c", run_id="r") is None
    assert "file_review_navigation_ready" not in st.session_state
    assert st.session_state.screen == "file_review"


def test_last_estimate_publications_overlap_without_worker_state_access(monkeypatch):
    from threading import current_thread, main_thread
    st.session_state.clear()
    st.session_state.screen = "file_review"
    barrier = Barrier(2)
    calls = []
    client = object()
    monkeypatch.setattr(file_review, "get_supabase_client", lambda: client)
    def read(kind):
        def loader(run_id, **kwargs):
            assert kwargs == {"client": client, "company_id": "c"}
            assert run_id == "r" and current_thread() != main_thread()
            barrier.wait(timeout=2)
            return {"status": "succeeded", "kind": kind}
        return loader
    monkeypatch.setattr(file_review, "load_file_review_naming_publication", read("naming"))
    monkeypatch.setattr(file_review, "load_file_review_document_identity_publication", read("identity"))
    def publish(kind):
        def record(*args, **kwargs):
            assert current_thread() == main_thread()
            calls.append(kind)
        return record
    monkeypatch.setattr(file_review, "_publish_persisted_naming", publish("naming"))
    monkeypatch.setattr(file_review, "_publish_persisted_document_identity", publish("identity"))
    file_review._sync_last_estimate_publications("r", "c")
    assert calls == ["naming", "identity"]
    assert st.session_state.screen == "file_review"
    assert st.session_state["file_review_naming_cache_synced.r"]
    assert st.session_state["file_review_document_identity_cache_synced.r"]
    file_review._sync_last_estimate_publications("r", "c")
    assert calls == ["naming", "identity"], "Terminal publication must not be read twice"


def test_last_estimate_keeps_local_pending_work_read_free(monkeypatch):
    st.session_state.clear()
    st.session_state.file_review_deferred_work = {"run_id": "r", "naming": True}
    st.session_state.current_naming_future = Future()
    st.session_state["file_review_document_identity_cache_synced.r"] = True
    monkeypatch.setattr(file_review, "get_supabase_client", lambda: pytest.fail("Pending local work must not read"))
    file_review._sync_last_estimate_publications("r", "c")
    assert "file_review_naming_cache_synced.r" not in st.session_state


def test_last_estimate_owned_project_reads_overlap_and_preserve_output(monkeypatch):
    from use_cases import estimation as e
    barrier = Barrier(3)
    parallel = False
    owned = []
    monkeypatch.setattr(e, "get_supabase_client", object)
    monkeypatch.setattr(e, "_assert_screen_estimate_access", lambda *a, **kw: owned.append(kw))
    objects_frame = pd.DataFrame([{"object_id": "one", "company_id": "c", "run_id": "r",
        "object_name": "Bench", "status": "completed", "quantity": 2, "self_cost_ex_vat": 100, "approved": True}])
    def read(value):
        assert owned
        if parallel:
            barrier.wait(timeout=2)
        return value.copy(deep=True)
    monkeypatch.setattr(e, "fetch_rfq_object_estimates", lambda *a: read(objects_frame))
    monkeypatch.setattr(e, "fetch_rfq_estimate_pricing_overrides", lambda *a: read(pd.DataFrame()))
    monkeypatch.setattr(e, "fetch_rfq_estimate_material_plan", lambda *a: read(pd.DataFrame()))
    monkeypatch.setattr(e, "fetch_company_overhead_settings", lambda *a: pd.DataFrame([{"vat_percent": 18, "sale_price_markup_percent": 30}]))
    monkeypatch.setattr(e, "fetch_rfq_run", lambda *a: pd.DataFrame([{"project_name": "Current title"}]))
    sequential = e.load_objects_estimation_data("e")
    parallel = True
    overlapping = e.load_objects_estimation_data("e", parallel_reads=True, company_id="c")
    assert overlapping == sequential
    assert owned == [{}, {"company_id": "c"}]
    assert overlapping["rows"][0]["reviewed"] is True
    assert overlapping["rows"][0]["sale_price_total"] == 260


def test_last_estimate_cost_context_reads_overlap_but_keep_identical_inputs(monkeypatch):
    from use_cases import estimation as e
    barrier = Barrier(4)
    parallel = False
    client = object()
    def read(value):
        if parallel:
            barrier.wait(timeout=2)
        return value
    monkeypatch.setattr(e, "with_production_capacity", lambda *a: read({"workers": 12}))
    monkeypatch.setattr(e, "fetch_company_overhead_monthly", lambda *a: read(pd.DataFrame([{"rent": 20}])))
    monkeypatch.setattr(e, "load_sheet_processing_machinery", lambda *a: read({"machine": "current"}))
    monkeypatch.setattr(e, "load_parts_check", lambda **kw: read({"status": "ready", "report_sha256": "current"}))
    obj = {"company_id": "c", "run_id": "r", "estimate_id": "e"}
    plan = {"current": True}
    original = e._full_cost_context(client, obj, plan, {})
    parallel = True
    assert e._full_cost_context(client, obj, plan, {}, parallel_reads=True) == original


def test_last_estimate_parallel_reads_never_start_before_ownership(monkeypatch):
    from use_cases import estimation as e
    monkeypatch.setattr(e, "get_supabase_client", object)
    def reject(*a, **kw):
        raise PermissionError("not owned")
    monkeypatch.setattr(e, "_assert_screen_estimate_access", reject)
    monkeypatch.setattr(e, "fetch_rfq_object_estimates", lambda *a: pytest.fail("Read before ownership"))
    with pytest.raises(PermissionError, match="not owned"):
        e.load_objects_estimation_data("e", parallel_reads=True, company_id="other")


@pytest.mark.parametrize("kind", ["naming", "document_identity"])
def test_last_estimate_publication_uses_captured_owned_client(monkeypatch, kind):
    from use_cases import rfq_processing as r
    from state import company_auth
    client = object()
    calls = []
    monkeypatch.setattr(company_auth, "company_auth_enabled", lambda: True)
    monkeypatch.setattr(r, "get_supabase_client", lambda: pytest.fail("No worker session/client lookup"))
    monkeypatch.setattr(r, "get_company_id", lambda: pytest.fail("No worker auth state lookup"))
    monkeypatch.setattr(r, "assert_run_owned", lambda *a: calls.append(("owned", a)))
    def terminal(*args):
        assert calls == [("owned", (client, "r", "c"))]
        calls.append(("terminal", args))
        return {"status": "succeeded"}
    monkeypatch.setattr(r, "fetch_deferred_naming_status", terminal)
    monkeypatch.setattr(r, "fetch_deferred_document_identity_status", terminal)
    monkeypatch.setattr(r, "fetch_rfq_detected_object_names", lambda *a: [{"object_id": "one", "object_name": "Current manual name"}])
    monkeypatch.setattr(r, "fetch_rfq_run", lambda *a: pd.DataFrame([{"project_name": "Current title"}]))
    loader = r.load_file_review_naming_publication if kind == "naming" else r.load_file_review_document_identity_publication
    result = loader("r", client=client, company_id="c")
    assert result["status"] == "succeeded"
    assert result.get("names", {}).get("one") == "Current manual name" if kind == "naming" else result["metadata"]["project_name"] == "Current title"


def test_last_estimate_warm_prices_overlap_without_changing_canonical_result(monkeypatch):
    from use_cases import estimation as e
    parallel = False
    barrier = Barrier(3)
    monkeypatch.setattr(e, "get_supabase_client", object)
    monkeypatch.setattr(e, "_assert_screen_estimate_access", lambda *a, **kw: None)
    objects_frame = pd.DataFrame([{"object_id": "one", "company_id": "c", "quantity": 3,
        "self_cost_ex_vat": 120, "approved": False}])
    def read(value):
        if parallel:
            barrier.wait(timeout=2)
        return value.copy(deep=True)
    monkeypatch.setattr(e, "fetch_rfq_object_estimates", lambda *a: read(objects_frame))
    monkeypatch.setattr(e, "fetch_rfq_estimate_pricing_overrides", lambda *a: read(pd.DataFrame()))
    monkeypatch.setattr(e, "fetch_company_overhead_settings", lambda *a: read(pd.DataFrame([{"vat_percent": 18, "sale_price_markup_percent": 30}])))
    cached = {"company_id": "c", "rows": [{"object_key": "one", "name": "Bench", "status": "completed"}]}
    expected = e.refresh_objects_estimation_prices("e", cached)
    parallel = True
    actual = e.refresh_objects_estimation_prices("e", cached, parallel_reads=True, company_id="c")
    assert actual == expected
    assert actual["rows"][0]["quantity"] == 3 and actual["rows"][0]["sale_price_total"] == 468
    assert actual["rows"][0]["reviewed"] is False


def test_last_estimate_context_failure_never_starts_cost_writes(monkeypatch):
    from use_cases import estimation as e
    monkeypatch.setattr(e, "with_production_capacity", lambda *a: {})
    monkeypatch.setattr(e, "fetch_company_overhead_monthly", lambda *a: pd.DataFrame())
    monkeypatch.setattr(e, "load_sheet_processing_machinery", lambda *a: {})
    def fail(**kwargs):
        raise ConnectionError("owned parts read failed")
    monkeypatch.setattr(e, "load_parts_check", fail)
    monkeypatch.setattr(e, "_recalculate_object_estimate_totals", lambda *a, **kw: pytest.fail("Write before complete input reads"))
    objects_frame = pd.DataFrame([{"object_id": "one", "company_id": "c", "run_id": "r", "status": "completed"}])
    with pytest.raises(ConnectionError, match="owned parts read failed"):
        e._ensure_full_object_costs(object(), estimate_id="e", objects=objects_frame,
                                  plan={"parts_check_source": {"current": True}}, settings={}, parallel_reads=True)
