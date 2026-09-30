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
            "notes": "",
            "evidence_pages": [{"page_number": 1, "source_label": "A-01"}],
        },
        "evidence": {
            "ocr_blocks": [
                {"block_ref": "ocr:ocr-1:p1:b0001", "page_number": 1, "text": "CAB-01 Base cabinet", "bbox": {}},
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
        "template_code": facts["template"]["code"],
        "template_confidence": facts["template"]["confidence"],
        "template_provenance": facts["template"]["provenance"],
        "template_evidence_refs": facts["template"]["evidence_refs"],
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
            {
                "key": key,
                "value": (
                    "yes" if value is True else "no" if value is False else str(value)
                ),
            }
            for key, value in facts["features"].items()
        ],
        "manufacturing_features": [],
        "purchased_components": [],
        "source_facts": [
            {**item, "value": str(item["value"])}
            for item in facts["source_facts"]
        ],
        "review_items": facts["review_items"],
    }
    result.update(overrides)
    return result


class _Client:
    def with_options(self, **_kwargs):
        return self


class _Response:
    usage = None


def test_provider_schema_is_tiny_while_local_validation_binds_catalog():
    schema = build_estimation_v2_facts_schema({"birch_plywood", "mdf"})

    assert schema == {
        "type": "object",
        "additionalProperties": False,
        "required": ["facts_json"],
        "properties": {"facts_json": {"type": "string"}},
    }
    provider_schema = strip_schema_for_claude(schema)
    assert "exclusiveMinimum" not in json.dumps(provider_schema)
    assert "uniqueItems" not in json.dumps(provider_schema)
    assert "anyOf" not in json.dumps(provider_schema)


def test_e01_agent_uses_only_bounded_json_and_returns_validated_facts(monkeypatch):
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
    )

    assert result["facts"]["template"] == FIXTURE["facts"]["template"]
    assert result["facts"]["dimensions_mm"] == FIXTURE["facts"]["dimensions_mm"]
    assert result["facts"]["materials"] == FIXTURE["facts"]["materials"]
    assert result["facts"]["source_facts"][0]["value"] == "1200"
    assert captured["temperature"] == 0
    assert captured["messages"][0]["content"][0]["type"] == "text"
    assert len(captured["messages"][0]["content"]) == 1
    request = json.loads(captured["messages"][0]["content"][0]["text"].split("\n", 1)[1])
    assert request["transport_contract"]["allowed_provenance"] == [
        "assumed_template", "derived", "explicit",
    ]
    assert request["transport_item_fields"]["manufacturing_feature"] == [
        "feature_id", "process", "material_requirement_id", "measurements",
        "flags", "evidence_refs",
    ]
    assert "original document is not available" in captured["system"].lower()
    assert result["usage_event"]["raw_usage"]["source_document_attached"] is False
    assert result["usage_event"]["raw_usage"]["ocr_rerun"] is False


def test_agent_rejects_server_owned_identity_in_provider_transport(monkeypatch):
    changed = _provider_response(object_name="Model renamed the object")
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"facts_json": json.dumps(changed)}),
    )

    try:
        agent.run_estimation_v2_facts_agent(
            input_id="input-e01-r1",
            object_input_revision=1,
            estimation_input=_input(),
            allowed_material_families={"birch_plywood"},
        )
    except ValueError as exc:
        assert "facts transport fields are invalid" in str(exc)
    else:
        raise AssertionError("server-owned object identity must be rejected")


def test_agent_rejects_evidence_reference_not_present_in_frozen_input(monkeypatch):
    changed = _provider_response()
    changed["materials"][0]["evidence_refs"] = ["ocr:invented:p9:b9999"]
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"facts_json": json.dumps(changed)}),
    )

    try:
        agent.run_estimation_v2_facts_agent(
            input_id="input-e01-r1",
            object_input_revision=1,
            estimation_input=_input(),
            allowed_material_families={"birch_plywood"},
        )
    except ValueError as exc:
        assert "invented evidence refs" in str(exc)
    else:
        raise AssertionError("invented evidence refs must be rejected")


def test_agent_treats_omitted_optional_specification_items_as_empty(monkeypatch):
    changed = _provider_response()
    changed["materials"][0].pop("specification_items")
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", lambda *_args, **_kwargs: _Response())
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"facts_json": json.dumps(changed)}),
    )

    result = agent.run_estimation_v2_facts_agent(
        input_id="input-e01-r1",
        object_input_revision=1,
        estimation_input=_input(),
        allowed_material_families={"birch_plywood"},
    )

    assert result["facts"]["materials"][0]["specification"] == {}


def test_square_profile_section_transport_normalizes_to_face_mm():
    assert agent._profile_section_number("20x20", "features.profile_section_mm") == 20
    assert agent._profile_section_number("40 × 40", "features.profile_section_mm") == 40


def test_rectangular_profile_section_requires_explicit_weld_face():
    try:
        agent._profile_section_number("20x40", "features.profile_section_mm")
    except ValueError as exc:
        assert "explicit weld face" in str(exc)
    else:
        raise AssertionError("rectangular profile must not silently select one face")
