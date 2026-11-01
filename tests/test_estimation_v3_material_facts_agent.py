import json
from types import SimpleNamespace

import pytest

import agents.estimation_v4_1_material_facts_agent as agent
import use_cases.estimation_v4_1_material_facts as replay


def _row(page_count=2):
    artifacts = []
    pages = []
    blocks = []
    for page_number in range(1, page_count + 1):
        ref = f"storage://rfq-estimation-evidence/company/run/object/r1/page-{page_number}.webp"
        artifacts.append({"storage_ref": ref, "page_number": page_number, "artifact_kind": "page"})
        pages.append({"page_number": page_number, "source_label": str(page_number), "regions": []})
        blocks.append({"page_number": page_number, "text": f"MDF panel page {page_number}", "block_ref": f"ocr:event:p{page_number}:b0001"})
    return {
        "input_id": "input-1", "object_input_revision": 1,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1", "document": {"file_name": "kitchen.pdf"},
            "object": {"object_id": "object-1", "object_name": "Kitchen", "quantity": 1, "evidence_pages": pages},
            "evidence": {"ocr_blocks": blocks, "ocr_literal_items": [], "artifacts": artifacts},
        },
    }


def test_v4_1_builds_disjoint_bounded_batches_with_complete_page_coverage():
    row = _row(39)

    batches = agent.build_v4_1_evidence_batches(row["input_payload"])

    covered = [page["page_number"] for batch in batches for page in batch["pages"]]
    assert sorted(covered) == list(range(1, 40))
    assert len(covered) == len(set(covered))
    assert all(len(batch["pages"]) <= agent.MAX_SOURCE_PAGES_PER_CALL for batch in batches)
    assert all(page["topic"] == "structure" for batch in batches for page in batch["pages"])


def test_v4_1_splits_dense_ocr_before_it_exceeds_the_output_budget():
    row = _row(3)
    row["input_payload"]["evidence"]["ocr_blocks"] = [
        {"page_number": page_number, "text": f"MDF {index}", "block_ref": f"ocr:p{page_number}:b{index}"}
        for page_number in range(1, 4) for index in range(130)
    ]

    batches = agent.build_v4_1_evidence_batches(row["input_payload"])

    assert [[page["page_number"] for page in batch["pages"]] for batch in batches] == [[1], [2], [3]]
    assert all(sum(len(page["ocr_blocks"]) for page in batch["pages"]) <= agent.MAX_OCR_BLOCKS_PER_CALL for batch in batches)


def test_v4_1_rejects_a_model_response_that_silently_omits_a_page():
    batch = agent.build_v4_1_evidence_batches(_row(2)["input_payload"])[0]

    with pytest.raises(ValueError, match="page coverage"):
        agent._response_for_batch(
            response={"batch_id": batch["batch_id"], "pages": [{"page_number": 1, "material_signal": "no", "claim_ids": []}], "claims": []},
            batch=batch, families={"mdf_hdf"},
        )


def test_v4_1_accepts_a_json_fence_missing_only_its_closing_marker():
    assert agent._json_object("```json\n{\"batch_id\": \"b1\"}") == {"batch_id": "b1"}
    assert agent._json_object("Here is the result: {\"batch_id\": \"b1\"}") == {"batch_id": "b1"}
    with pytest.raises(ValueError, match="JSON object"):
        agent._json_object("No structured result")


def test_v4_1_sends_each_source_page_once_in_a_bounded_call(monkeypatch):
    captured = []

    class Client:
        def with_options(self, **_kwargs):
            return self

    def fake_message(_client, **kwargs):
        captured.append(kwargs)
        request = json.loads(kwargs["messages"][0]["content"][-1]["text"])
        answer = {
            "batch_id": request["batch_id"],
            "pages": [{"page_number": page["page_number"], "material_signal": "no", "claim_ids": []} for page in request["pages"]],
            "claims": [],
        }
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(answer))],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(agent, "create_claude_message", fake_message)
    row = _row(13)
    bytes_by_ref = {item["storage_ref"]: b"page" for item in row["input_payload"]["evidence"]["artifacts"]}

    result = agent.run_estimation_v4_1_material_facts_agent(
        inputs=[row], allowed_material_families={"mdf_hdf"}, evidence_page_bytes_by_ref=bytes_by_ref,
    )

    assert result["failed"] == {}
    assert result["facts_by_input"]["input-1"]["contract_version"] == "estimation_material_facts_v4_2"
    assert len(captured) == 3
    sent_refs = []
    for kwargs in captured:
        content = kwargs["messages"][0]["content"]
        request = json.loads(content[-1]["text"])
        images = [item for item in content if item["type"] == "image"]
        assert len(images) <= 6
        sent_refs.extend(page["source_evidence_ref"] for page in request["pages"])
        page_numbers = {page["page_number"] for page in request["pages"]}
        assert all(block["page_number"] in page_numbers for page in request["pages"] for block in page["ocr_blocks"])
    assert sorted(sent_refs) == sorted(bytes_by_ref)
    assert result["usage_event"]["raw_usage"]["batch_count"] == 3


def test_v4_1_records_provider_usage_when_response_parsing_fails(monkeypatch):
    class Client:
        def with_options(self, **_kwargs):
            return self

    monkeypatch.setattr(agent, "get_anthropic_client", lambda: Client())
    monkeypatch.setattr(agent, "get_secret", lambda *_args: "test-model")
    monkeypatch.setattr(
        agent, "create_claude_message",
        lambda *_args, **_kwargs: SimpleNamespace(
            content=[SimpleNamespace(type="text", text="not json")],
            usage=SimpleNamespace(input_tokens=123, output_tokens=45),
        ),
    )
    row = _row(1)
    bytes_by_ref = {item["storage_ref"]: b"page" for item in row["input_payload"]["evidence"]["artifacts"]}

    result = agent.run_estimation_v4_1_material_facts_agent(
        inputs=[row], allowed_material_families={"mdf_hdf"}, evidence_page_bytes_by_ref=bytes_by_ref,
    )

    assert result["failed"]
    assert result["usage_event"]["status"] == "failed"
    assert result["usage_event"]["input_tokens"] == 123
    assert result["usage_event"]["raw_usage"]["batch_count"] == 1


def test_v4_1_never_combines_repeated_material_scope_into_a_quantity():
    row = _row(2)
    claims = [
        {"raw": {"id": "a", "n": "MDF", "f": "mdf_hdf", "q": 2, "u": "m²", "s": {}}, "family": "mdf_hdf", "evidence_refs": ["storage://rfq-estimation-evidence/company/run/object/r1/page-1.webp"]},
        {"raw": {"id": "b", "n": "MDF", "f": "mdf_hdf", "q": 3, "u": "m²", "s": {}}, "family": "mdf_hdf", "evidence_refs": ["storage://rfq-estimation-evidence/company/run/object/r1/page-2.webp"]},
    ]

    facts = agent._facts_from_claims(row=row, claims=claims, reviews=[], families={"mdf_hdf"})

    assert [material["quantity"] for material in facts["materials"]] == [None, None]
    assert any(item["code"] == "material_scope_overlap" for item in facts["review_items"])


def test_v4_1_replay_uses_the_immutable_input_without_a_new_upload(monkeypatch):
    row = _row(1)
    captured = {}
    monkeypatch.setattr(replay, "fetch_estimation_object_input", lambda _client, **_kwargs: row)
    monkeypatch.setattr(replay, "build_estimation_material_context", lambda _client, company_id: {"company_id": company_id})
    monkeypatch.setattr(replay, "run_estimation_v4_1_material_facts_batch", lambda **kwargs: captured.update(kwargs) or {"failed": {}})

    result = replay.replay_estimation_v4_1_material_facts_input(client=object(), input_id="input-1")

    assert result == {"failed": {}}
    assert captured["inputs"] == [row]
    assert captured["material_context"] == {"company_id": "company-1"}
