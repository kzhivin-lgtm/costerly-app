import json

import agents.estimation_v3_material_facts_agent as agent


def test_estimation_model_request_excludes_decorative_object_name(monkeypatch):
    captured = {}

    class _Client:
        def with_options(self, **_kwargs):
            return self

    class _Response:
        usage = None
        stop_reason = "end_turn"

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: _Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(
        agent,
        "create_claude_message",
        lambda *_args, **kwargs: captured.update(kwargs) or _Response(),
    )
    monkeypatch.setattr(
        agent,
        "extract_text_from_claude_response",
        lambda _response: json.dumps({"objects": [{"id": "object-1", "d": [0, 0, 0], "m": [], "p": []}]}),
    )

    evidence_ref = "storage://rfq-estimation-evidence/company-1/object-1/p1.webp"
    agent.run_estimation_v3_material_facts_agent(
        inputs=[{
            "input_id": "input-1",
            "object_input_revision": 1,
            "input_payload": {
                "run_id": "run-1",
                "company_id": "company-1",
                "object": {
                    "object_id": "object-1",
                    "object_name": "Misleading storage console",
                    "quantity": 1,
                    "evidence_pages": [{"page_number": 1, "source_label": "1", "regions": []}],
                },
                "evidence": {
                    "ocr_blocks": [],
                    "ocr_literal_items": [],
                    "artifacts": [{"storage_ref": evidence_ref, "page_number": 1, "artifact_kind": "page"}],
                },
            },
        }],
        allowed_material_families={"mdf_hdf"},
        evidence_page_bytes_by_ref={evidence_ref: b"page"},
    )

    request = json.loads(captured["messages"][0]["content"][-1]["text"])
    assert request["targets"] == [{
        "id": "object-1",
        "quantity": 1,
        "evidence": {
            "pages": [{"page_number": 1, "regions": []}],
            "ocr_blocks": [],
            "ocr_literal_items": [],
            "artifacts": [{"storage_ref": evidence_ref, "page_number": 1, "artifact_kind": "page"}],
        },
    }]
    assert "Misleading storage console" not in captured["messages"][0]["content"][-1]["text"]
    assert "source_label" not in captured["messages"][0]["content"][-1]["text"]
