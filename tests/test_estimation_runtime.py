import use_cases.estimation_runtime as runtime
from decimal import Decimal
from types import SimpleNamespace


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


def test_v3_material_runtime_routes_all_objects_through_the_current_path(monkeypatch):
    events = []
    monkeypatch.setattr(runtime, "get_supabase_client", lambda: object())
    monkeypatch.setattr(runtime, "fetch_rfq_run", lambda _client, _run_id: _Frame([{}]))
    monkeypatch.setattr(runtime, "fetch_rfq_detected_objects", lambda _client, _run_id: _Frame([{}]))
    monkeypatch.setattr(
        runtime,
        "fetch_latest_ocr_result",
        lambda _client, _run_id: {"ocr_event_id": "ocr-1", "ocr_result": {}},
    )
    monkeypatch.setattr(
        runtime,
        "persist_estimation_inputs",
        lambda **_kwargs: {
            "created_inputs": [{"input_id": "input-1", "input_payload": {}}]
        },
    )
    monkeypatch.setattr(runtime, "describe_estimation_original", lambda **_kwargs: object())
    monkeypatch.setattr(
        runtime,
        "_run_estimation_v3_for_all_objects",
        lambda **kwargs: events.append(("v3_run", kwargs["created_inputs"])) or {
            "processed_input_ids": ["input-1"], "failed": {}
        },
    )

    result = runtime._run_estimation_job(
        estimate_id="estimate-1",
        run_id="run-1",
        company_id="company-1",
        file_name="drawing.pdf",
        file_bytes=b"pdf",
        ignored_object_ids=set(),
        shell={"estimate_id": "estimate-1"},
    )

    assert [event[0] for event in events] == ["v3_run"]
    assert result["estimation"]["status"] == "completed"
    assert result["estimation"]["estimated_objects"] == 1
    assert result["estimation_version"] == "v3_materials"


def test_all_ignored_objects_finish_as_empty_v3_estimate(monkeypatch):
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


def test_material_engine_plan_runs_after_facts_and_cannot_block_object_publishing(monkeypatch):
    events = []
    facts = {
        "object-1": {"facts_payload": {"object_id": "object-1", "materials": [], "parts": []}},
    }

    monkeypatch.setattr(runtime, "build_estimation_material_context", lambda *_args: {"catalogs": {}, "families": {"mdf"}})
    captured_facts = {}
    monkeypatch.setattr(
        runtime,
        "run_estimation_v3_material_facts_batch",
        lambda **kwargs: captured_facts.update(kwargs) or events.append("facts") or {"failed": {}},
    )
    monkeypatch.setattr(runtime, "fetch_latest_estimation_facts_by_object", lambda _client, **_kwargs: facts)
    monkeypatch.setattr(runtime, "fetch_rfq_estimate_material_norm_overrides", lambda *_args, **_kwargs: SimpleNamespace(empty=True))
    monkeypatch.setattr(
        runtime,
        "build_material_plan",
        lambda **_kwargs: events.append("material_plan") or SimpleNamespace(
            plan=SimpleNamespace(status="planned", lines=[SimpleNamespace(total_cost=Decimal("42"))]),
            demand_count=1, candidate_count=1, unresolved_requirement_ids=(), reason_codes=(),
        ),
    )
    monkeypatch.setattr(runtime, "material_plan_snapshot", lambda _shadow, **_kwargs: {
        "status": "planned", "demand_count": 1, "candidate_count": 1,
        "lines": [{"total_cost": 42.0}], "unresolved_requirement_ids": [], "reason_codes": [],
    })
    monkeypatch.setattr(
        runtime,
        "upsert_rfq_estimate_material_plan",
        lambda *_args, **_kwargs: events.append("material_plan_persisted"),
    )
    monkeypatch.setattr(runtime, "publish_estimation_v3_material_object", lambda **_kwargs: events.append("publish") or {"status": "review_required"})
    monkeypatch.setattr(runtime, "_set_object_progress", lambda _client, **_kwargs: None)
    monkeypatch.setattr(runtime, "update_rfq_object_estimate_progress", lambda _client, **_kwargs: None)

    result = runtime._run_estimation_v3_for_all_objects(
        client=object(), estimate_id="estimate-1",
        created_inputs=[{
            "input_id": "input-1", "object_id": "object-1",
            "input_payload": {"company_id": "company-1", "run_id": "run-1"},
        }],
    )

    assert events == ["facts", "material_plan", "material_plan_persisted", "publish"]
    assert captured_facts["material_context"] == {"catalogs": {}, "families": {"mdf"}}
    assert result["processed_input_ids"] == ["input-1"]
    assert result["material_engine_plan"] == {
        "status": "planned", "demand_count": 1, "candidate_count": 1,
        "planned_line_count": 1, "planned_material_cost_ex_vat": 42.0,
        "unresolved_requirement_ids": [], "assumption_fallback_count": 0, "reason_codes": [],
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
