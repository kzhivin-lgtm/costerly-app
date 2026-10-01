import json
from pathlib import Path

import agents.estimation_v2_facts_agent as agent
import agents.estimation_v2_page_facts_agent as page_agent


FIXTURE = json.loads(
    Path("tests/fixtures/estimation_v2/e01_complete_object.json").read_text()
)


def _input():
    facts = FIXTURE["facts"]
    return {
        "contract_version": "estimation_input_v2",
        "run_id": facts["run_id"],
        "company_id": facts["company_id"],
        "document": {"file_name": "drawing.pdf", "ocr_event_id": "ocr-1", "ocr_contract_version": "ocr-v2"},
        "object": {
            "object_id": facts["object_id"],
            "object_name": facts["object_name"],
            "quantity": facts["quantity"],
            "quantity_explicit": True,
            "dimensions": facts["dimensions_mm"],
            "detected_materials": "18 mm birch plywood",
            "notes": "unverified detection note",
            "evidence_pages": [{"page_number": 1, "source_label": "A-01"}],
        },
        "evidence": {
            "ocr_blocks": [
                {"block_ref": "ocr:ocr-1:p1:b0001", "page_number": 1, "text": "Object E01", "bbox": {}},
                {"block_ref": "ocr:ocr-1:p1:b0002", "page_number": 1, "text": "18 mm birch plywood", "bbox": {}},
                {"block_ref": "ocr:ocr-1:p1:b0003", "page_number": 1, "text": "W 1200 x D 560 x H 720 mm", "bbox": {}},
            ],
            "artifacts": [{"artifact_kind": "preview", "page_number": 1, "storage_ref": facts["primary_preview_ref"]}],
            "primary_preview_ref": facts["primary_preview_ref"],
        },
        "versions": {"detection": "test"},
    }


def _provider_response(**overrides):
    facts = FIXTURE["facts"]
    result = {
        "status": facts["status"],
        "dimensions_mm": [
            facts["dimensions_mm"]["width"],
            facts["dimensions_mm"]["depth"],
            facts["dimensions_mm"]["height"],
        ],
        "materials": [{
            "requirement_id": facts["materials"][0]["requirement_id"],
            "source_name": facts["materials"][0]["source_name"],
            "family": facts["materials"][0]["family"],
            "specification_items": [
                {"key": key, "value": str(value)}
                for key, value in facts["materials"][0]["specification"].items()
            ],
            "quantity": facts["materials"][0]["quantity"],
            "unit": facts["materials"][0]["unit"],
            "evidence_refs": facts["materials"][0]["evidence_refs"],
        }],
        "features": [
            {"key": key, "value": "yes" if value is True else "no" if value is False else str(value)}
            for key, value in facts["features"].items()
        ],
        "manufacturing_features": [],
        "purchased_components": [],
        "labor_operations": [
            {key: value for key, value in operation.items() if key not in {"route", "machine_code"}}
            for operation in facts["labor_operations"]
        ],
        "source_facts": [{**item, "value": str(item["value"])} for item in facts["source_facts"]],
        "review_items": facts["review_items"],
    }
    result.update(overrides)
    return result


class _Client:
    def with_options(self, **_kwargs):
        return self


class _Response:
    usage = None
    stop_reason = "end_turn"


def _run(monkeypatch, transport=None):
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps(transport or _provider_response()),
    )
    return agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
        preview_bytes=b"preview",
        production_context={"machines": [{"machine_code": "wood_panel_saw", "availability_status": "in_house"}]},
    )


def test_agent_returns_materials_and_agent_created_operations(monkeypatch):
    captured = {}
    client_options = {}

    class _OptionsClient(_Client):
        def with_options(self, **kwargs):
            client_options.update(kwargs)
            return self

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _OptionsClient())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")

    def _create(_client, **kwargs):
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr(agent, "create_claude_message", _create)
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps(_provider_response()),
    )
    result = agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
        preview_bytes=b"preview",
        production_context={"machines": [{"machine_code": "wood_panel_saw", "availability_status": "in_house"}]},
    )

    assert result["facts"]["labor_operations"] == FIXTURE["facts"]["labor_operations"]
    assert result["facts"]["materials"] == FIXTURE["facts"]["materials"]
    request = json.loads(captured["messages"][0]["content"][1]["text"].split("\n", 1)[1])
    assert "dimensions" not in request["estimation_input"]["object"]
    assert "notes" not in request["estimation_input"]["object"]
    assert "allowed_labor_operations" in request["transport_contract"]
    assert "available_company_machinery" not in request["transport_contract"]
    assert result["facts"]["labor_operations"][0]["route"] == "in_house_machine"
    assert result["facts"]["labor_operations"][0]["machine_code"] == "wood_panel_saw"
    assert captured["messages"][0]["content"][0]["type"] == "image"
    assert client_options == {"timeout": 180.0, "max_retries": 0}
    assert captured["max_tokens"] == 16384
    assert "output_config" not in captured


def test_agent_reports_output_token_truncation_before_json_parsing(monkeypatch):
    class _TruncatedResponse:
        usage = None
        stop_reason = "max_tokens"

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(
        agent,
        "create_claude_message",
        lambda *_args, **_kwargs: _TruncatedResponse(),
    )
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: '{"status":"ready"',
    )

    try:
        agent.run_estimation_v2_facts_agent(
            input_id="input-e01-r1",
            object_input_revision=1,
            estimation_input=_input(),
            allowed_material_families={"birch_plywood"},
            preview_bytes=b"preview",
            production_context={},
        )
    except RuntimeError as exc:
        assert "truncated" in str(exc)
        assert "result was not published" in str(exc)
    else:
        raise AssertionError("max_tokens response must be rejected before parsing")


def test_agent_accepts_one_exact_json_fence(monkeypatch):
    transport = _provider_response()
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(
        agent,
        "create_claude_message",
        lambda *_args, **_kwargs: _Response(),
    )
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: "```json\n" + json.dumps(transport) + "\n```",
    )

    result = agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
        preview_bytes=b"preview",
        production_context={
            "machines": [{
                "machine_code": "wood_panel_saw",
                "availability_status": "in_house",
            }]
        },
    )

    assert result["facts"]["materials"] == FIXTURE["facts"]["materials"]


def test_agent_extracts_single_json_object_from_commentary_wrapper():
    assert json.loads(agent._provider_json_text(
        'Result:\n{"status":"ready"}\nDone.'
    )) == {"status": "ready"}


def test_sparse_named_manufacturing_fields_are_normalized_without_position():
    transport = _provider_response()
    material_id = transport["materials"][0]["requirement_id"]
    transport["manufacturing_features"] = [{
        "feature_id": "mf-1",
        "process": "cnc_router",
        "material_requirement_id": material_id,
        "measurement_items": [
            {"key": "thickness_mm", "value": "18"},
            {"key": "part_count", "value": "6"},
        ],
        "flag_items": [
            {"key": "production_file_ready", "value": "no"},
            {"key": "has_internal_cutouts", "value": "yes"},
        ],
        "evidence_refs": transport["materials"][0]["evidence_refs"],
    }]

    normalized = agent._normalize_provider_result(
        transport,
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        production_context={},
    )

    feature = normalized["manufacturing_features"][0]
    assert feature["measurements"]["thickness_mm"] == 18
    assert feature["measurements"]["part_count"] == 6
    assert feature["measurements"]["sheet_count"] is None
    assert feature["flags"]["production_file_ready"] == "no"
    assert feature["flags"]["has_internal_cutouts"] == "yes"
    assert feature["flags"]["has_pockets"] == "unknown"


def test_unknown_optional_manufacturing_key_becomes_warning_not_failure():
    transport = _provider_response()
    material_id = transport["materials"][0]["requirement_id"]
    transport["manufacturing_features"] = [{
        "feature_id": "mf-1",
        "process": "cnc_router",
        "material_requirement_id": material_id,
        "measurement_items": [{"key": "unsupported_measure", "value": "2"}],
        "flag_items": [{"key": "unsupported_flag", "value": "yes"}],
        "evidence_refs": transport["materials"][0]["evidence_refs"],
    }]

    normalized = agent._normalize_provider_result(
        transport,
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        production_context={},
    )

    warning = normalized["review_items"][0]
    assert warning["code"] == "manufacturing_feature_unsupported"
    assert warning["severity"] == "warning"
    assert "unsupported_flag" in warning["message"]
    assert "unsupported_measure" in warning["message"]


def test_laser_subcontractor_route_is_not_blocked_when_manufacturing_inputs_exist():
    transport = _provider_response()
    material_id = transport["materials"][0]["requirement_id"]
    transport["labor_operations"][0]["operation_code"] = "sheet_laser_cutting"
    transport["manufacturing_features"] = [{
        "feature_id": "laser-1", "process": "sheet_laser",
        "material_requirement_id": material_id,
        "measurement_items": [
            {"key": "thickness_mm", "value": "5"},
            {"key": "path_length_m", "value": "12"},
        ],
        "flag_items": [],
        "evidence_refs": transport["materials"][0]["evidence_refs"],
    }]

    normalized = agent._normalize_provider_result(
        transport, input_id="input-e01-r1", object_input_revision=1,
        estimation_input=_input(),
        production_context={"machines": [{
            "machine_code": "metal_sheet_laser", "availability_status": "not_in_house",
        }]},
    )

    assert normalized["status"] == "ready"
    assert not any(
        item["code"] == "machinery_route_unresolved"
        for item in normalized["review_items"]
    )


def test_machine_operation_without_manufacturing_inputs_requires_review():
    transport = _provider_response()
    transport["labor_operations"][0]["operation_code"] = "sheet_laser_cutting"

    normalized = agent._normalize_provider_result(
        transport, input_id="input-e01-r1", object_input_revision=1,
        estimation_input=_input(), production_context={},
    )

    assert normalized["status"] == "review_required"
    assert any(
        item["code"] == "manufacturing_feature_unsupported"
        for item in normalized["review_items"]
    )


def test_agent_normalizes_unknown_evidence_reference_with_warning(monkeypatch):
    changed = _provider_response()
    changed["labor_operations"][0]["evidence_refs"] = ["invented-ref"]
    result = _run(monkeypatch, changed)
    assert result["facts"]["labor_operations"][0]["evidence_refs"] == [
        "storage://rfq-estimation-evidence/company-e01/run-e01/object-e01/r1/preview.webp"
    ]
    assert any(
        item["code"] == "invalid_evidence_reference"
        and item["severity"] == "warning"
        for item in result["facts"]["review_items"]
    )


def test_server_adds_blocking_review_when_material_quantity_is_missing():
    transport = _provider_response(status="ready")
    transport["materials"][0]["quantity"] = 0
    transport["review_items"] = []

    normalized = agent._normalize_provider_result(
        transport, input_id="input-e01-r1", object_input_revision=1,
        estimation_input=_input(),
    )

    assert normalized["status"] == "review_required"
    assert normalized["review_items"][0]["code"] == "material_quantity_missing"


def test_server_adds_blocking_review_when_operation_plan_is_missing():
    transport = _provider_response(status="ready")
    transport["labor_operations"] = []
    transport["review_items"] = []

    normalized = agent._normalize_provider_result(
        transport, input_id="input-e01-r1", object_input_revision=1,
        estimation_input=_input(),
    )

    assert normalized["status"] == "review_required"
    assert normalized["review_items"][0]["code"] == "labor_result_unavailable"


def test_unknown_purchased_component_quantity_normalizes_to_none():
    transport = _provider_response()
    transport["purchased_components"] = [{
        "component_id": "part-1", "component_type": "fabricated_part",
        "quantity": 0, "unit": "job", "specification_items": [],
        "evidence_refs": FIXTURE["facts"]["materials"][0]["evidence_refs"],
    }]
    normalized = agent._normalize_provider_result(
        transport, input_id="input-e01-r1", object_input_revision=1,
        estimation_input=_input(),
    )
    assert normalized["purchased_components"][0]["quantity"] is None


def test_hollow_profile_height_required_by_prompt_is_supported():
    transport = _provider_response()
    transport["materials"][0]["family"] = "carbon_steel"
    transport["materials"][0]["specification_items"] = [
        {"key": "profile_section", "value": "square_hollow"},
        {"key": "width_mm", "value": "20"},
        {"key": "height_mm", "value": "20"},
        {"key": "wall_thickness_mm", "value": "1.5"},
    ]

    normalized = agent._normalize_provider_result(
        transport,
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
    )

    specification = normalized["materials"][0]["specification"]
    assert specification["height_mm"] == 20
    assert specification["wall_thickness_mm"] == 1.5

    validated = agent.validate_object_facts(
        normalized,
        allowed_material_families={"carbon_steel"},
    )
    assert validated["materials"][0]["specification"]["height_mm"] == 20


def test_agent_transport_does_not_offer_installation_scope_as_cost_fact(monkeypatch):
    captured = {}
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")

    def _create(_client, **kwargs):
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr(agent, "create_claude_message", _create)
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps(_provider_response()),
    )
    agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
        preview_bytes=b"preview",
        production_context={
            "machines": [{
                "machine_code": "wood_panel_saw",
                "availability_status": "in_house",
            }]
        },
    )

    request = json.loads(captured["messages"][0]["content"][1]["text"].split("\n", 1)[1])
    assert "installation_scope" not in request["transport_contract"]["feature_keys"]


def test_page_agent_sends_one_labeled_preview_per_object(monkeypatch):
    captured = {}
    first = _input()
    second = json.loads(json.dumps(first))
    second["object"]["object_id"] = "object-2"
    second["object"]["object_name"] = "Object 2"
    rows = [
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": first},
        {"input_id": "input-2", "object_input_revision": 1, "input_payload": second},
    ]
    monkeypatch.setattr(page_agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(page_agent, "get_secret", lambda *_args: "test-model")

    def _create(_client, **kwargs):
        captured.update(kwargs)
        return _Response()

    monkeypatch.setattr(page_agent, "create_claude_message", _create)
    monkeypatch.setattr(page_agent, "extract_text_from_claude_response", lambda _response: '{"objects":[]}')
    monkeypatch.setattr(page_agent, "build_agent_usage_event", lambda **_kwargs: {"raw_usage": {}})

    page_agent.run_estimation_v2_page_facts_agent(
        inputs=rows,
        allowed_material_families={"birch_plywood"},
        preview_bytes_by_input={"input-1": b"preview-one", "input-2": b"preview-two"},
    )

    content = captured["messages"][0]["content"]
    labels = [json.loads(block["text"])["source_preview_for_object_id"] for block in content[:-1:2]]
    images = [block for block in content if block["type"] == "image"]
    assert labels == [first["object"]["object_id"], "object-2"]
    assert len(images) == 2
    assert images[0]["source"]["data"] != images[1]["source"]["data"]


def test_page_agent_normalizes_purchased_component_phrase_to_stable_identifier():
    assert page_agent._stable_identifier("Glass door panel", "purchased_component") == "glass_door_panel"
    assert page_agent._stable_identifier("Drawer runner", "purchased_component") == "drawer_runner"


def test_page_agent_builds_logged_fallback_when_object_payload_is_missing():
    facts = page_agent._expand_object(
        {},
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": _input()},
        {"birch_plywood"},
    )

    assert facts["status"] == "review_required"
    assert [row["operation_code"] for row in facts["labor_operations"]] == [
        "estimate_review", "shop_drawing", "quality_inspection", "protective_packaging",
    ]
    assert {row["code"] for row in facts["review_items"]} == {
        "material_requirement_missing", "approximation_applied",
    }


def test_page_agent_logs_purchased_component_normalization():
    compact = {
        "m": [{"id": "m 1", "n": "Birch plywood", "f": "birch_plywood", "q": 1, "u": "m²", "s": {}}],
        "op": [{"id": "op 1", "c": "carcass_assembly", "q": 1, "u": "object", "m": ["m_1"]}],
        "pc": [{"id": "door 1", "t": "Glass door panel", "q": 1, "u": "piece", "s": {}}],
        "d": [1200, 560, 720], "x": {}, "mf": [],
    }
    facts = page_agent._expand_object(
        compact,
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": _input()},
        {"birch_plywood"},
    )

    assert facts["purchased_components"][0]["component_type"] == "glass_door_panel"
    assert facts["purchased_components"][0]["component_id"] == "door_1"
    assert any(row["code"] == "model_value_normalized" for row in facts["review_items"])
