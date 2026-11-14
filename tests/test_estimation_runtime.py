from concurrent.futures import Future
from json import JSONDecodeError

import pytest

import use_cases.estimation_runtime as runtime


def test_material_edits_wait_for_the_rebuild_that_includes_them(monkeypatch):
    jobs = []

    class Executor:
        def submit(self, _function, **_kwargs):
            jobs.append(Future())
            return jobs[-1]

    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_EXECUTOR", Executor())
    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_FUTURES", {})
    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_PENDING_REQUESTS", {})
    ids = {"estimate_id": "estimate-1", "run_id": "run-1", "company_id": "company-1"}

    first = runtime.queue_material_plan_recalculation(**ids)
    second = runtime.queue_material_plan_recalculation(**ids)
    third = runtime.queue_material_plan_recalculation(**ids)
    assert len(jobs) == 1
    jobs[0].set_result("first plan")
    assert first.result() == "first plan"
    assert not second.done() and not third.done() and len(jobs) == 2
    jobs[1].set_result("latest plan")
    assert second.result() == third.result() == "latest plan"


def test_scoped_material_save_reprices_only_edited_stock_and_its_owners(monkeypatch):
    import pandas as pd
    from use_cases import estimation

    def line(key, owner, amount, price, kind="piece"):
        allocation = {"object_id": owner, "material_requirement_id": key, "demand_id": key,
                      "quantity": amount if kind == "piece" else None,
                      "length_mm": amount if kind == "linear_stock" else None}
        quantity = amount if kind == "piece" else 1
        return {
            "selection_key": key, "candidate_id": key, "authority": "assumption",
            "display_name": key, "currency": "ILS", "purchase_kind": kind,
            "price_per_purchase_unit": price, "total_cost": quantity * price,
            "purchasable_dimensions": {"length_mm": 5000} if kind == "linear_stock" else {},
            "package_quantity": 1, "purchase_quantity": quantity,
            "purchase_quantity_is_manual": False, "allocations": [allocation],
        }

    shared = line("LED", "object-a", 1000, 50, "linear_stock")
    shared["allocations"].append({"object_id": "object-b", "material_requirement_id": "led",
                                  "demand_id": "other-LED", "length_mm": 2000, "quantity": None})
    unrelated = line("Hinge", "object-c", 4, 10)
    saved = {"status": "needs_review", "reason_codes": [], "lines": [shared, unrelated],
             "object_material_costs": [
                 {"object_id": "object-a", "material_requirement_id": "LED", "cost_ex_vat": 16.67},
                 {"object_id": "object-b", "material_requirement_id": "led", "cost_ex_vat": 33.33},
                 {"object_id": "object-c", "material_requirement_id": "Hinge", "cost_ex_vat": 40},
             ]}
    writes = {}
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_plan", lambda *_: pd.DataFrame([{"plan_payload": saved}]))
    monkeypatch.setattr(runtime, "fetch_rfq_object_estimates", lambda *_: pd.DataFrame([
        {"object_id": oid, "quantity": 1} for oid in ("object-a", "object-b", "object-c")
    ]))
    for name in ("fetch_rfq_estimate_material_purchase_overrides", "fetch_rfq_estimate_material_norm_overrides"):
        monkeypatch.setattr(runtime, name, lambda *_: pd.DataFrame())
    for name in ("upsert_rfq_estimate_material_norm_overrides", "delete_rfq_estimate_material_purchase_overrides",
                 "upsert_rfq_estimate_material_plan"):
        monkeypatch.setattr(runtime, name, lambda _client, _name=name, **kw: writes.update({_name: kw}))
    monkeypatch.setattr(estimation, "apply_material_plan_allocations", lambda _client, **kw: writes.update(allocations=kw))

    edit = {("object-a", "LED"): {"unit": "m", "quantity_per_item": 7.5}}
    snapshot = runtime._recalculate_edited_material_lines(
        object(), "estimate", "run", "company", {"LED"}, set(), {}, edit, {},
    )

    assert snapshot["lines"][0]["purchase_quantity"] == 2
    assert snapshot["lines"][1] == unrelated
    assert writes["allocations"]["changed_requirements"] == {("object-a", "LED"), ("object-b", "led")}
    assert writes["upsert_rfq_estimate_material_norm_overrides"]["rows"] == list(edit.values())
    assert writes["delete_rfq_estimate_material_purchase_overrides"]["selection_keys"] == {"LED"}
    assert writes["upsert_rfq_estimate_material_plan"]["plan_payload"] == snapshot


def test_concurrent_material_edits_keep_the_latest_override_and_quantity(monkeypatch):
    jobs = []

    class Executor:
        def submit(self, _fn, **kwargs):
            future = Future()
            jobs.append((kwargs, future))
            return future

    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_EXECUTOR", Executor())
    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_FUTURES", {})
    monkeypatch.setattr(runtime, "_MATERIAL_PLAN_PENDING_REQUESTS", {})
    ids = {"estimate_id": "estimate", "run_id": "run", "company_id": "company"}
    running = runtime.queue_material_plan_recalculation(**ids, purchase_keys=frozenset())
    earlier = runtime.queue_material_plan_recalculation(
        **ids, purchase_keys=frozenset({"LED"}), purchase_edits={"LED": 4}, quantity_edits={"a": 2},
    )
    later = runtime.queue_material_plan_recalculation(
        **ids, norm_keys=frozenset({"LED"}), purchase_keys=frozenset(),
        norm_edits={("a", "LED"): {"unit": "m", "quantity_per_item": 7}}, quantity_edits={"a": 3},
    )

    jobs[0][1].set_result("initial")
    request, future = jobs[1]
    assert running.result() == "initial"
    assert request["norm_keys"] == {"LED"} and not request["purchase_keys"]
    assert not request["purchase_edits"]
    assert request["quantity_edits"] == {"a": 3}
    assert request["norm_edits"][("a", "LED")]["quantity_per_item"] == 7
    future.set_result("updated")
    assert earlier.result() == later.result() == "updated"


def test_submit_creates_estimate_shell_before_background_job(monkeypatch):
    events = []
    future = object()

    class Executor:
        def submit(self, fn, **kwargs):
            events.append(("background_submitted", fn, kwargs))
            return future

    def apply_edits(**kwargs):
        events.append(("edits_applied", kwargs))
        return {"ignored-2"}

    def create_shell(**kwargs):
        events.append(("shell_created", kwargs))
        return {"estimate_id": kwargs["estimate_id"], "status": "pending"}

    monkeypatch.setattr(runtime, "_ESTIMATION_EXECUTOR", Executor())
    monkeypatch.setattr(runtime, "apply_file_review_edits", apply_edits)
    monkeypatch.setattr(runtime, "start_estimation_for_run", create_shell)

    result = runtime.submit_estimation_job(
        estimate_id="estimate-1",
        run_id="run-1",
        company_id="company-1",
        file_name="rfq.pdf",
        file_bytes=b"pdf",
        object_edits={"object-1": {"name": "Cabinet"}},
        edits_changed=True,
        ignored_object_ids=set(),
        create_shell=True,
    )

    assert result is future
    assert [event[0] for event in events] == [
        "edits_applied",
        "shell_created",
        "background_submitted",
    ]
    submitted_kwargs = events[-1][2]
    assert submitted_kwargs["ignored_object_ids"] == {"ignored-2"}
    assert submitted_kwargs["shell"] == {
        "estimate_id": "estimate-1",
        "status": "pending",
    }


def test_prepared_submit_defers_all_persistence_to_executor(monkeypatch):
    submitted = []
    future = object()

    class Executor:
        def submit(self, fn, **kwargs):
            submitted.append((fn, kwargs))
            return future

    monkeypatch.setattr(runtime, "_ESTIMATION_EXECUTOR", Executor())

    result = runtime.submit_prepared_estimation_job(
        estimate_id="estimate-1",
        run_id="run-1",
        company_id="company-1",
        file_name="cabinet.pdf",
        file_bytes=b"pdf",
        object_edits={"object-1": {"name": "Cabinet"}},
        metadata_values={"project_name": "Hall"},
        edits_changed=True,
        ignored_object_ids={"object-2"},
        create_shell=True,
    )

    assert result is future
    assert submitted == [(
        runtime._persist_prepared_launch_and_run,
        {
            "estimate_id": "estimate-1",
            "run_id": "run-1",
            "company_id": "company-1",
            "file_name": "cabinet.pdf",
            "file_bytes": b"pdf",
            "object_edits": {"object-1": {"name": "Cabinet"}},
            "metadata_values": {"project_name": "Hall"},
            "edits_changed": True,
            "ignored_object_ids": {"object-2"},
            "create_shell": True,
        },
    )]


def test_prepared_worker_persists_accepted_snapshot_before_estimation(monkeypatch):
    events = []
    monkeypatch.setattr(
        runtime,
        "save_file_review_run_metadata",
        lambda **kwargs: events.append(("metadata", kwargs)),
    )
    monkeypatch.setattr(
        runtime,
        "apply_file_review_edits",
        lambda **kwargs: events.append(("edits", kwargs)) or {"ignored-after-save"},
    )
    monkeypatch.setattr(
        runtime,
        "start_estimation_for_run",
        lambda **kwargs: events.append(("shell", kwargs)) or {"status": "pending"},
    )
    monkeypatch.setattr(
        runtime,
        "_run_estimation_job",
        lambda **kwargs: events.append(("job", kwargs)) or {"status": "completed"},
    )

    result = runtime._persist_prepared_launch_and_run(
        estimate_id="estimate-1",
        run_id="run-1",
        company_id="company-1",
        file_name="cabinet.pdf",
        file_bytes=b"pdf",
        object_edits={"object-1": {"name": "Cabinet"}},
        metadata_values={"project_name": "Hall"},
        edits_changed=True,
        ignored_object_ids={"object-2"},
        create_shell=True,
    )

    assert result == {"status": "completed"}
    assert [event[0] for event in events] == ["metadata", "edits", "shell", "job"]
    assert events[-1][1]["ignored_object_ids"] == {"ignored-after-save"}
    assert events[-1][1]["shell"] == {"status": "pending"}


@pytest.mark.parametrize("stage", ["planned", "parts_check", "material_plan"])
def test_estimation_prices_the_saved_parts_check_and_reports_stage_failures(monkeypatch, stage):
    events = []
    report = {"stage": "Parts Check", "objects": {"object-1": {"parts": []}}}
    rows = [{"input_id": "input-1", "input_payload": {"object": {"object_id": "object-1"}}}]
    monkeypatch.setattr(runtime, "get_supabase_client", lambda: object())
    monkeypatch.setattr(runtime, "fetch_rfq_run", lambda *_: _Frame([{}]))
    monkeypatch.setattr(runtime, "fetch_rfq_detected_objects", lambda *_: _Frame([{}]))
    monkeypatch.setattr(runtime, "fetch_latest_ocr_result",
                        lambda *_: {"ocr_event_id": "ocr-1", "ocr_result": {}})
    monkeypatch.setattr(runtime, "persist_estimation_inputs", lambda **_: {"created_inputs": rows})
    monkeypatch.setattr(runtime, "describe_estimation_original", lambda **_: {})
    monkeypatch.setattr(runtime, "_set_object_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime, "_mark_material_plan_failed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime, "update_rfq_object_estimate_totals", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runtime, "_set_object_technical_failure",
                        lambda _client, **kwargs: events.append(kwargs["label"]))

    def check(**kwargs):
        assert kwargs["inputs"] is rows
        events.append("parts_check")
        return None if stage == "parts_check" else report

    def price(**kwargs):
        assert kwargs["parts_report"] is report and kwargs["input_rows"] is rows
        events.append("material_plan")
        if stage == "material_plan":
            raise ConnectionError("catalog unavailable")
        return {"status": "planned"}

    monkeypatch.setattr(runtime, "run_parts_check_for_estimate", check)
    monkeypatch.setattr(runtime, "_build_and_persist_material_plan", price)
    result = runtime._run_estimation_job(
        estimate_id="estimate-1", run_id="run-1", company_id="company-1",
        file_name="drawing.pdf", file_bytes=b"pdf", ignored_object_ids=set(),
        shell={"estimate_id": "estimate-1"},
    )

    if stage == "planned":
        assert events == ["parts_check", "material_plan"]
        assert result["estimation"]["status"] == "completed"
    else:
        assert events == (["parts_check", "parts_check_technical_failure"] if stage == "parts_check" else
                          ["parts_check", "material_plan", "material_plan_technical_failure"])
        assert result["estimation"]["failed_objects"] == {"input-1": f"{stage}_technical_failure"}


def test_handoff_failure_ends_known_objects_instead_of_leaving_progress_running(monkeypatch):
    terminal_updates = []
    monkeypatch.setattr(runtime, "get_supabase_client", lambda: object())
    monkeypatch.setattr(runtime, "fetch_rfq_run", lambda _client, _run_id: _Frame([{"run_id": "run-1"}]))
    monkeypatch.setattr(
        runtime,
        "fetch_rfq_detected_objects",
        lambda _client, _run_id: _Frame([{"object_id": "object-1"}]),
    )
    monkeypatch.setattr(
        runtime,
        "fetch_latest_ocr_result",
        lambda _client, _run_id: {"ocr_event_id": "ocr-1", "ocr_result": {}},
    )
    monkeypatch.setattr(runtime, "describe_estimation_original", lambda **_kwargs: object())
    monkeypatch.setattr(
        runtime,
        "persist_estimation_inputs",
        lambda **_kwargs: (_ for _ in ()).throw(JSONDecodeError("Expecting value", "", 0)),
    )
    monkeypatch.setattr(
        runtime,
        "_set_object_technical_failure",
        lambda _client, **kwargs: terminal_updates.append(kwargs),
    )

    with pytest.raises(RuntimeError, match="Estimation handoff failed: Expecting value"):
        runtime._run_estimation_job(
            estimate_id="estimate-1", run_id="run-1", company_id="company-1",
            file_name="drawing.pdf", file_bytes=b"pdf", ignored_object_ids=set(),
            shell={"estimate_id": "estimate-1"},
        )

    assert terminal_updates == [{
        "estimate_id": "estimate-1", "object_id": "object-1",
        "label": "estimation_handoff_failed",
    }]


def test_all_ignored_objects_finish_as_empty_estimate(monkeypatch):
    monkeypatch.setattr(runtime, "get_supabase_client", lambda: object())
    monkeypatch.setattr(runtime, "fetch_rfq_run", lambda _client, _run_id: _Frame([{}]))
    monkeypatch.setattr(runtime, "fetch_rfq_detected_objects", lambda _client, _run_id: _Frame([]))
    monkeypatch.setattr(runtime, "fetch_latest_ocr_result", lambda _client, _run_id: None)

    result = runtime._run_estimation_job(
        estimate_id="estimate-1", run_id="run-1", company_id="company-1",
        file_name="drawing.pdf", file_bytes=b"pdf", ignored_object_ids={"object-1"},
        shell={"estimate_id": "estimate-1", "object_count": 0},
    )

    assert result["estimation"] == {
        "status": "no_objects", "estimated_objects": 0, "failed_objects": {}
    }


class _Row:
    def __init__(self, value):
        self._value = value

    def to_dict(self):
        return dict(self._value)


class _ILoc:
    def __init__(self, rows):
        self._rows = rows

    def __getitem__(self, index):
        return _Row(self._rows[index])


class _Frame:
    def __init__(self, rows):
        self._rows = rows
        self.iloc = _ILoc(rows)
        self.empty = not rows

    def iterrows(self):
        for index, row in enumerate(self._rows):
            yield index, _Row(row)


def test_approval_and_manual_purchase_publish_review_order_with_scoped_costs(monkeypatch):
    import pandas as pd
    from use_cases import estimation
    from use_cases.material_engine_adapter import material_review_purchases, object_purchase_key

    alloc = [{"object_id": oid, "material_requirement_id": "hdf", "demand_id": oid, "area_mm2": area}
             for oid, area in (("A", 3_436_000), ("B", 10_791_000))]
    raw = {"status": "planned", "reason_codes": [], "object_material_costs": [], "lines": [{
        "selection_key": "hdf", "candidate_id": "offer", "purchase_kind": "sheet",
        "purchasable_dimensions": {"length_mm": 2400, "width_mm": 1220}, "package_quantity": 1,
        "price_per_purchase_unit": 105, "purchase_quantity": 6, "total_cost": 630,
        "currency": "ILS", "authority": "company", "allocations": alloc,
    }]}
    saved = material_review_purchases(raw)
    objects = {oid: {"object_id": oid, "quantity": 1, "approved": False} for oid in ("A", "B")}
    overrides = {}
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_plan", lambda *_: pd.DataFrame([{"plan_payload": saved}]))
    monkeypatch.setattr(runtime, "fetch_rfq_object_estimates", lambda *_: pd.DataFrame(objects.values()))
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_purchase_overrides", lambda *_: pd.DataFrame([
        {"selection_key": key, "purchase_quantity": qty} for key, qty in overrides.items()
    ]))
    monkeypatch.setattr(runtime, "upsert_rfq_estimate_material_purchase_overrides",
                        lambda _client, **kw: overrides.update(kw["quantities"]))
    def publish(_client, **kw):
        nonlocal saved
        saved = kw["plan_payload"]
    monkeypatch.setattr(runtime, "upsert_rfq_estimate_material_plan", publish)
    monkeypatch.setattr(estimation, "apply_material_plan_allocations", lambda *_a, **kw: None)
    monkeypatch.setattr(runtime, "update_rfq_object_estimate_approved",
                        lambda _client, object_id, approved, **_kw: objects[object_id].update(approved=approved))

    def purchase_quantities():
        return {oid: item["quantity"] for oid, item in saved["lines"][0]["object_purchases"].items()}

    runtime._recalculate_edited_material_lines(
        object(), "estimate", "run", "company", set(), set(), {}, {}, {}, approve_objects=("A",),
    )
    assert objects["A"]["approved"] and saved["material_review_order"] == ["A"]
    assert purchase_quantities() == {"A": 2, "B": 4}

    override_key = object_purchase_key("B", "hdf")
    runtime._recalculate_edited_material_lines(
        object(), "estimate", "run", "company", set(), {override_key}, {}, {}, {override_key: 5},
    )
    assert overrides == {override_key: 5}
    assert objects["A"]["approved"] and purchase_quantities() == {"A": 2, "B": 5}
