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
        "error_type": "ValueError",
        "error_message": "structural BOM has no material demand",
    }]
