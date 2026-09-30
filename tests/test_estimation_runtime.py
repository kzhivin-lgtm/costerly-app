import use_cases.estimation_runtime as runtime


def test_estimation_v2_facts_shadow_is_enabled_by_default_after_acceptance(monkeypatch):
    monkeypatch.setattr(runtime, "get_secret", lambda _name, default: default)

    assert runtime._estimation_v2_facts_shadow_enabled() is True


def test_estimation_v2_facts_shadow_has_explicit_false_rollback(monkeypatch):
    monkeypatch.setattr(runtime, "get_secret", lambda _name, _default: "false")

    assert runtime._estimation_v2_facts_shadow_enabled() is False


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


def test_v2_facts_are_queued_before_legacy_estimation(monkeypatch):
    events = []

    class FactsExecutor:
        def submit(self, fn, inputs):
            events.append(("facts_queued", fn, inputs))

    monkeypatch.setattr(runtime, "_ESTIMATION_V2_FACTS_EXECUTOR", FactsExecutor())
    monkeypatch.setattr(runtime, "_estimation_v2_facts_shadow_enabled", lambda: True)
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
        "persist_estimation_v2_shadow_inputs",
        lambda **_kwargs: {
            "created_inputs": [{"input_id": "input-1", "input_payload": {}}]
        },
    )
    monkeypatch.setattr(runtime, "describe_estimation_original", lambda **_kwargs: object())

    def fail_legacy(**_kwargs):
        events.append(("legacy_started",))
        raise RuntimeError("legacy failed")

    monkeypatch.setattr(runtime, "estimate_all_objects_for_run", fail_legacy)

    try:
        runtime._run_estimation_job(
            estimate_id="estimate-1",
            run_id="run-1",
            company_id="company-1",
            file_name="drawing.pdf",
            file_bytes=b"pdf",
            ignored_object_ids=set(),
            shell={"estimate_id": "estimate-1"},
        )
    except RuntimeError as exc:
        assert str(exc) == "legacy failed"
    else:
        raise AssertionError("legacy failure was expected")

    assert [event[0] for event in events] == ["facts_queued", "legacy_started"]


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
