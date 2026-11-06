from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from agents.estimation_understanding_agent import CB_RULEBOOK
from tests.test_cb_parts import fixture
from use_cases.estimation_cb_parts import validate_cb_part_counts
from use_cases.estimation_dimension_graph import build_dimension_graph


def answer():
    return {"blocks": [{"id": "B01", "parts": [
        {"name": "Carcass side wall", "quantity": 2},
        {"name": "Drawer bottom", "quantity": 2}]}]}


def test_counts_only_retains_exact_raw_names_and_quantities(monkeypatch):
    _, _, scope, _ = fixture(monkeypatch)
    raw = answer(); before = deepcopy(raw)
    assert validate_cb_part_counts(raw, scope=scope) is raw
    assert raw == before


@pytest.mark.parametrize("change", ["material", "dimensions", "explanation", "missing", "duplicate_block", "foreign", "duplicate_name", "zero", "fraction", "bool", "empty"])
def test_count_contract_rejects_extras_and_invalid_counts(monkeypatch, change):
    _, _, scope, _ = fixture(monkeypatch)
    raw = answer(); part = raw["blocks"][0]["parts"][0]
    if change in {"material", "dimensions", "explanation"}: part[change] = "not requested"
    if change == "missing": raw["blocks"] = []
    if change == "duplicate_block": raw["blocks"].append(deepcopy(raw["blocks"][0]))
    if change == "foreign": raw["blocks"][0]["id"] = "B99"
    if change == "duplicate_name": raw["blocks"][0]["parts"].append(deepcopy(part))
    if change == "zero": part["quantity"] = 0
    if change == "fraction": part["quantity"] = 1.2
    if change == "bool": part["quantity"] = True
    if change == "empty": raw["blocks"][0]["parts"] = []
    with pytest.raises(ValueError): validate_cb_part_counts(raw, scope=scope)


def test_v2_one_calculate_call_without_geometry_or_material_composition(monkeypatch):
    row, pages, scope, _ = fixture(monkeypatch)
    scope["parts_version"] = "CB Parts V2"
    calls = []
    raw = answer()
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {"prompt_version": kw["prompt_version"]})
    monkeypatch.setattr(agent, "build_v4_1_evidence_batches", lambda *a: pytest.fail("legacy batching"))
    import use_cases.estimation_cb_parts as parts
    monkeypatch.setattr(parts, "compose_cb_parts", lambda **kw: pytest.fail("V1 composition"))
    def provider(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph=build_dimension_graph(input_row=row), dimension_scale_gate={"test": "unused"},
        allowed_material_families=[], cb_parts_scope=scope)
    assert len(calls) == 1
    request = calls[0]
    assert request["model"] == "claude-haiku-5-5" and request["thinking"] == {"type": "disabled"}
    assert request["system"].startswith("CB Parts V2")
    assert all(ord(c) < 128 for c in request["system"])
    context = json.loads(request["messages"][0]["content"][-1]["text"])
    assert set(context) == {"calculation_scope"}
    assert any(x["type"] == "image" for x in request["messages"][0]["content"])
    assert result["parts_count"] == raw == result["extraction"]
    assert "bom" not in result
    assert result["status"] == "cb_parts_count_requires_review"
    assert result["upstream_status"]["front"] == "failed"
    assert CB_RULEBOOK["parts"]["previous"]["path"].name == "cb_parts_v1.md"


def test_live_count_reply_is_unchanged_and_semantic_defects_remain_visible():
    saved = json.loads((Path(__file__).resolve().parents[1] / "notes/evidence/cb-parts-v2-2026-11-06/lev2-counts.json").read_text())
    raw = json.loads(saved["response_text"])
    scope = {"planner": {"blocks": [{"id": x} for x in saved["input_block_ids"]], "shared_parts": []}}
    assert validate_cb_part_counts(raw, scope=scope) == saved["parsed_response"]
    assert saved["provider_calls"] == 1 and saved["stop_reason"] == "end_turn"
    assert saved["same_input_and_pages_as_v1"] and saved["same_supplied_images_as_v1"]
    assert saved["semantic_accepted"] is False
    totals = saved["totals_computed_for_review_not_model_fields"]
    assert totals["Drawer front"] == totals["Drawer body bottom"] == 5
    assert totals["Drawer body side"] == totals["Drawer body end panel"] == 10
    b09 = next(b for b in raw["blocks"] if b["id"] == "B09")
    assert {"name": "Door", "quantity": 1} in b09["parts"]
    assert not any("partition" in p["name"].lower() for b in raw["blocks"] for p in b["parts"])
