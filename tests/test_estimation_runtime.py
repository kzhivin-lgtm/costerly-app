import use_cases.estimation_runtime as runtime
from json import JSONDecodeError

import pytest


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
