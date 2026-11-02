import agents.estimation_assembly_bom_agent as assembly_agent
import use_cases.estimation_object_to_estimate_runtime as bom_runtime


def test_agent_accepts_missing_coverage_for_later_deterministic_audit():
    result = assembly_agent._validate_response(
        response={
            "batch_id": "batch-1", "pages": [{"page_number": 1}],
            "document_unit": {"unit": "cm"}, "assemblies": [],
        },
        batch={
            "batch_id": "batch-1",
            "pages": [{"page_number": 1, "regions": [{"bounds": {}}]}],
        },
    )

    assert result["coverage"] == []


def test_assembly_failure_persists_safe_stage_trace_without_provider_details(monkeypatch):
    traces = []
    monkeypatch.setattr(bom_runtime, "fetch_estimation_fact_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        bom_runtime, "build_dimension_graph",
        lambda **_kwargs: {"contract_version": "estimation_dimension_graph_v1"},
    )
    monkeypatch.setattr(bom_runtime, "build_dimension_scale_gate", lambda **_kwargs: {})
    monkeypatch.setattr(bom_runtime, "insert_agent_usage_event_returning_id", lambda *_args, **_kwargs: "usage-1")
    monkeypatch.setattr(bom_runtime, "insert_estimation_fact_result", lambda *_args, **_kwargs: "fact-1")
    monkeypatch.setattr(
        bom_runtime, "run_estimation_assembly_bom_agent",
        lambda **_kwargs: {"extraction": {}, "usage_event": {}},
    )
    monkeypatch.setattr(
        bom_runtime, "build_structural_assembly_bom",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("structural BOM has no material demand")),
    )
    monkeypatch.setattr(
        bom_runtime, "insert_estimation_failure_trace",
        lambda _client, **kwargs: traces.append(kwargs) or "trace-1",
    )

    result = bom_runtime.run_assembly_first_bom_batch(
        client=object(),
        inputs=[{"input_id": "input-1", "input_payload": {}}],
        allowed_material_families=["mdf_hdf"],
    )

    assert result["failed"] == {"input-1": "ValueError: structural BOM has no material demand"}
    assert traces == [{
        "input_id": "input-1",
        "agent_version": bom_runtime.ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
        "stage": "structural_composition",
        "error_type": "StructuralValidationError",
        "error_message": "no_material_demand",
    }]


def test_structural_validation_trace_persists_a_code_without_model_content(monkeypatch):
    traces = []
    monkeypatch.setattr(
        bom_runtime, "insert_estimation_failure_trace",
        lambda _client, **kwargs: traces.append(kwargs) or "trace-1",
    )

    bom_runtime._record_failure_trace(
        client=object(), input_id="input-1", stage="structural_composition",
        exc=ValueError("assembly-2 lacks dimensions required by facade_set"),
    )

    assert traces == [{
        "input_id": "input-1",
        "agent_version": bom_runtime.ESTIMATION_ASSEMBLY_BOM_AGENT_VERSION,
        "stage": "structural_composition",
        "error_type": "StructuralValidationError",
        "error_message": "assembly_missing_required_dimensions",
    }]


def test_structural_validation_trace_classifies_invalid_count_without_field_content(monkeypatch):
    traces = []
    monkeypatch.setattr(
        bom_runtime, "insert_estimation_failure_trace",
        lambda _client, **kwargs: traces.append(kwargs) or "trace-1",
    )

    bom_runtime._record_failure_trace(
        client=object(), input_id="input-1", stage="structural_composition",
        exc=ValueError("assembly-7.counts.legs must be a whole positive number"),
    )

    assert traces[0]["error_type"] == "StructuralValidationError"
    assert traces[0]["error_message"] == "invalid_assembly_count"


def test_stage_marker_records_only_bounded_metadata(monkeypatch):
    events = []
    monkeypatch.setattr(
        bom_runtime, "insert_agent_usage_event",
        lambda _client, event: events.append(event),
    )

    bom_runtime._record_stage_event(
        client=object(),
        input_row={
            "input_id": "input-1",
            "input_payload": {
                "company_id": "company-1", "run_id": "run-1",
                "document": {"file_name": "drawing.pdf"},
                "object": {"object_id": "object-1", "object_name": "Locked name"},
            },
        },
        stage="structural_composition", status="succeeded",
        details={"reason_code": "bom_ready", "part_count": 4, "raw_response": "must-not-persist"},
    )

    assert events[0]["operation"] == "estimation_stage"
    assert events[0]["status"] == "succeeded"
    assert events[0]["raw_usage"] == {
        "estimation_stage": "structural_composition", "input_id": "input-1",
        "reason_code": "bom_ready", "part_count": 4,
    }


def test_material_plan_validation_trace_does_not_persist_the_exception_message(monkeypatch):
    traces = []
    monkeypatch.setattr(
        bom_runtime, "insert_estimation_failure_trace",
        lambda _client, **kwargs: traces.append(kwargs) or "trace-1",
    )

    bom_runtime._record_failure_trace(
        client=object(), input_id="input-1", stage="material_plan",
        exc=ValueError("could not convert string to float: approved_catalog_default"),
    )

    assert traces[0]["error_type"] == "MaterialPlanValidationError"
    assert traces[0]["error_message"] == "material_plan_validation_failed"
