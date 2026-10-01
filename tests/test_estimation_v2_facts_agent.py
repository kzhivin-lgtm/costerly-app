import json
from pathlib import Path

import agents.estimation_v2_facts_agent as agent
from agents.anthropic_adapter import strip_schema_for_claude
from agents.schemas.estimation_v2_facts_schema import build_estimation_v2_facts_schema


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


def _run(monkeypatch, transport=None):
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"facts_json": json.dumps(transport or _provider_response())}),
    )
    return agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
        preview_bytes=b"preview",
        production_context={"machines": [{"machine_code": "wood_panel_saw", "availability_status": "in_house"}]},
    )


def test_provider_schema_is_tiny_while_local_validation_binds_catalog():
    schema = build_estimation_v2_facts_schema({"birch_plywood", "mdf"})
    assert schema == {
        "type": "object",
        "additionalProperties": False,
        "required": ["facts_json"],
        "properties": {"facts_json": {"type": "string"}},
    }
    provider_schema = strip_schema_for_claude(schema)
    assert "anyOf" not in json.dumps(provider_schema)


def test_agent_returns_materials_and_agent_created_operations(monkeypatch):
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
        lambda _response: json.dumps({"facts_json": json.dumps(_provider_response())}),
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


def test_agent_rejects_unknown_evidence_reference(monkeypatch):
    changed = _provider_response()
    changed["labor_operations"][0]["evidence_refs"] = ["invented-ref"]
    try:
        _run(monkeypatch, changed)
    except ValueError as exc:
        assert "invented evidence refs" in str(exc)
    else:
        raise AssertionError("invented evidence refs must be rejected")


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
