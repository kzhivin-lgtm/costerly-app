from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_parts import fixture
from tests.test_cb_parts_v3_4 import span_answer
from tools.probe_cb_parts import load_topology
from use_cases.estimation_cb_width_probe import freeze_cb_topology, resolve_frozen_widths, validate_frozen_topology


def setup(monkeypatch):
    row, pages, scope, raw = span_answer(monkeypatch)
    spans = raw.pop("width_spans")
    scope["frozen_topology"] = freeze_cb_topology(raw, scope=scope)
    scope["parts_version"] = "CB Parts V3.5"
    scope["topology_source"] = {"status": "failed", "geometry_accepted": False}
    return row, pages, scope, {"width_spans": spans, "unanchored_widths": []}, raw


def test_only_identity_is_frozen_even_when_source_geometry_failed(monkeypatch):
    _, _, scope, _, raw = setup(monkeypatch)
    original = deepcopy(raw)
    for block in raw["blocks"]:
        block.update(height=-1, depth=None, unit="invalid", assumptions="OLD DIMENSIONS", thickness_mm=999)
        for bay in block["bays"]:
            bay.update(width=9999, shelves=999)
            for f in bay["fronts"]: f.update(height=9999, body_height=99999)
    assert freeze_cb_topology(raw, scope=scope) == scope["frozen_topology"]
    assert freeze_cb_topology(original, scope=scope) == scope["frozen_topology"]
    assert scope["frozen_topology"] == {"blocks": [{"id": "B01", "kind": "carcass", "front_ids": [],
        "bays": [{"id": "left", "front_ids": ["F01"]}, {"id": "right", "front_ids": ["F02"]}]}]}


@pytest.mark.parametrize("change", ["missing_front", "duplicate_front", "foreign_front", "duplicate_bay", "foreign_block", "extra_dimension", "kind"])
def test_invalid_frozen_topology_rejected(monkeypatch, change):
    _, _, scope, _, _ = setup(monkeypatch)
    b = scope["frozen_topology"]["blocks"][0]
    if change == "missing_front": b["bays"][0]["front_ids"] = []
    if change == "duplicate_front": b["bays"][0]["front_ids"].append("F01")
    if change == "foreign_front": b["bays"][0]["front_ids"] = ["F99"]
    if change == "duplicate_bay": b["bays"][0]["id"] = "right"
    if change == "foreign_block": b["id"] = "B99"
    if change == "extra_dimension": b["width"] = 900
    if change == "kind": b["kind"] = "explicit"
    with pytest.raises(ValueError): validate_frozen_topology(scope["frozen_topology"], scope=scope)


def test_reuses_span_allocator_without_compiling_failed_parts(monkeypatch):
    _, _, scope, answer, _ = setup(monkeypatch)
    before = deepcopy((scope, answer))
    result = resolve_frozen_widths(answer, scope=scope)
    assert (scope, answer) == before
    assert [b["width_mm"] for b in result["bay_widths"]] == [400, 800]
    assert result["spans"][0]["allocated_mm"] == 1200
    assert result["spans"][0]["association_verified"] is False


def test_explicit_parts_are_not_sized_or_fabricated(monkeypatch):
    _, _, scope, answer, raw = setup(monkeypatch)
    scope["planner"]["shared_parts"] = [{"id": "S01", "view_ids": []}]
    raw["blocks"].append({"id": "S01", "kind": "explicit", "front_ids": [], "unit": "cm",
        "size": [100, 3, 60], "assumptions": "old", "parts": []})
    scope["frozen_topology"] = freeze_cb_topology(raw, scope=scope)
    assert scope["frozen_topology"]["blocks"][-1] == {"id": "S01", "kind": "explicit", "bays": [], "front_ids": []}
    assert len(resolve_frozen_widths(answer, scope=scope)["bay_widths"]) == 2


def test_fallback_keeps_reason_and_mm_conversion(monkeypatch):
    _, _, scope, answer, _ = setup(monkeypatch)
    answer["width_spans"][0]["members"].pop()
    answer["unanchored_widths"] = [{"block_id": "B01", "bay_id": "right", "width": 0.5, "unit": "m", "reason": "No complete anchor."}]
    result = resolve_frozen_widths(answer, scope=scope)
    bay = result["bay_widths"][1]
    assert bay["width_mm"] == 500 and bay["basis"] == "unanchored_model_assumption"
    assert bay["reason"] == "No complete anchor."


@pytest.mark.parametrize("change", ["rebuild", "missing", "overlap", "duplicate", "unknown", "oversize", "reason"])
def test_width_only_contract_rejects_repair_and_coverage_errors(monkeypatch, change):
    _, _, scope, answer, _ = setup(monkeypatch)
    f = {"block_id": "B01", "bay_id": "right", "width": 50, "unit": "cm", "reason": "Unanchored."}
    if change == "rebuild": answer["blocks"] = []
    elif change == "missing": answer["width_spans"] = []
    else:
        answer["unanchored_widths"] = [f]
        if change != "overlap": answer["width_spans"][0]["members"].pop()
        if change == "duplicate": answer["unanchored_widths"].append(deepcopy(f))
        if change == "unknown": f["bay_id"] = "new"
        if change == "oversize": f["width"] = 3001
        if change == "reason": f["reason"] = ""
    with pytest.raises(ValueError): resolve_frozen_widths(answer, scope=scope)


def test_one_call_retains_images_status_raw_and_no_full_parts_claim(monkeypatch):
    row, pages, scope, answer, _ = setup(monkeypatch)
    scope["front"] = fixture(monkeypatch)[2]["front"]
    before = deepcopy(scope)
    from agents.estimation_understanding_agent import prepare_content, CB_RULEBOOK
    expected_content, _ = prepare_content([row], pages)
    calls = []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {})
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(answer))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph={}, dimension_scale_gate={}, allowed_material_families=[], cb_parts_scope=scope)
    assert scope == before and len(calls) == 1
    assert calls[0]["system"].splitlines()[0] == "CB Parts V3.5"
    assert calls[0]["messages"][0]["content"][:-1] == expected_content
    assert calls[0]["model"] == "claude-haiku-5-5" and calls[0]["thinking"] == {"type": "disabled"}
    assert result["extraction"] == answer and "parts_sized" not in result and "bom" not in result
    assert result["status"] == "cb_width_diagnostic_requires_review"
    assert result["upstream_status"]["front"] == result["topology_source"]["status"] == "failed"
    assert CB_RULEBOOK["parts"]["version"] == "CB Parts V3"


@pytest.mark.parametrize("change", [None, "images", "scope", "incomplete", "text", "request", "version"])
def test_loader_requires_exact_source_evidence_and_original_provider_reply(monkeypatch, tmp_path, change):
    row, pages, scope, _, raw = setup(monkeypatch)
    original = {k: scope[k] for k in ("input_id", "front", "planner", "upstream_status")}
    original["parts_version"] = "CB Parts V3.3"
    prior = {"inputs": [row], "source_pages_base64": {"p1": "fixture"}, "evidence_origin": "fixture"}
    text = json.dumps(raw)
    record = {"stage": "calculation", "response_text": text,
        "response": {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]},
        "request": {"messages": [{"content": [{"type": "text", "text": json.dumps({"calculation_scope": original})}]}]}}
    witness = {**deepcopy(prior), "scope": deepcopy(original), "status": "failed", "provider_responses": [record]}
    if change == "images": witness["source_pages_base64"] = {}
    if change == "scope": witness["scope"]["input_id"] = "other"
    if change == "incomplete": record["response"]["stop_reason"] = "max_tokens"
    if change == "text": record["response_text"] = "{}"
    if change == "request": record["request"]["messages"][0]["content"][-1]["text"] = "{}"
    if change == "version": witness["scope"]["parts_version"] = "CB Parts V3.4"
    path = tmp_path / "witness.json"; path.write_text(json.dumps(witness))
    if change:
        with pytest.raises(ValueError): load_topology(path, prior=prior, scope=scope)
    else:
        loaded = load_topology(path, prior=prior, scope=scope)
        assert loaded["frozen_topology"] == scope["frozen_topology"]
        assert loaded["topology_source"]["status"] == "failed"
        assert loaded["topology_source"]["geometry_accepted"] is False


def test_live_failure_preserves_wrong_membership_without_repair():
    from agents.estimation_v4_1_material_facts_agent import _json_object
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root / "notes/evidence/cb-parts-v3-5-2026-11-06/lev2-fixed-topology-trial.json").read_text())
    raw = _json_object(saved["raw_response_text"])
    assert saved["source_content_identical_to_v3_4"] and saved["image_count"] == 5
    assert saved["provider_calls"] == 1 and not saved["semantic_accepted"]
    assert saved["validation_scope"]["topology_source"]["status"] == "failed"
    with pytest.raises(ValueError, match="finite and positive"):
        resolve_frozen_widths(raw, scope=saved["validation_scope"])
    span = next(s for s in raw["width_spans"] if s["id"] == "D4")
    assert span["value"] == 151 and span["unit"] == "cm"
    assert len(span["members"]) == 5 and all(m["weight"] == 1 for m in span["members"])
    d4 = next(s for s in saved["unvalidated_span_arithmetic_and_locator_comparison"] if s["span_id"] == "D4")
    assert [f for m in d4["members"] for f in m["fronts_entirely_outside_declared_span_x"]] == ["F18", "F19"]
    assert sum(m["arithmetic_width_mm_not_accepted"] for m in d4["members"] if m["block_id"] == "B08") == 604
