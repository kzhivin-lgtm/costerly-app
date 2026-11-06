from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_parts import fixture
from tests.test_cb_parts_v3_3 import setup
from use_cases.estimation_cb_spans import resolve_cb_span_widths, compose_cb_span_parts


def span_answer(monkeypatch):
    row, pages, scope, raw = setup(monkeypatch)
    scope["parts_version"] = "CB Parts V3.4"
    view = scope["planner"]["blocks"][0]["view_ids"][0]
    for b in raw["blocks"][0]["bays"]: b["width"] = None
    raw["width_spans"] = [{"id": "D1", "view_id": view, "value": 120, "unit": "cm",
        "source_label": "120", "endpoints_1000": [100, 200, 800, 200], "members": [
            {"block_id": "B01", "bay_id": "left", "weight": 1, "label": "Drawer bay"},
            {"block_id": "B01", "bay_id": "right", "weight": 2, "label": "Door bay"}]}]
    return row, pages, scope, raw


def test_weighted_span_conserves_total_and_does_not_mutate_inputs(monkeypatch):
    _, _, scope, raw = span_answer(monkeypatch)
    before = deepcopy((scope, raw))
    compiled = compose_cb_span_parts(raw, scope=scope)
    assert (scope, raw) == before
    block = compiled["blocks"][0]
    assert block["size_mm"][0] == 1200
    assert [b["width_mm"] for b in block["derivation"]["bays"]] == [400, 800]
    assert next(p for p in block["parts"] if p["name"] == "Shared mounting partition")["quantity"] == 1
    audit = compiled["width_allocation"]["spans"][0]
    assert audit["allocated_mm"] == audit["span_mm"] == 1200
    assert not audit["association_verified"]


def test_one_span_crosses_blocks_with_mixed_units(monkeypatch):
    _, _, scope, raw = span_answer(monkeypatch)
    left = raw["blocks"][0]
    right = deepcopy(left); right["id"] = "B02"; right["bays"] = [right["bays"].pop()]
    left["bays"].pop()
    right["unit"] = "mm"; right["height"] = 850; right["depth"] = 650
    right["bays"][0]["fronts"][0]["height"] = 800
    raw["blocks"].append(right)
    p = scope["planner"]["blocks"][0]; p["front_ids"] = ["F01"]
    scope["planner"]["blocks"].append({**deepcopy(p), "id": "B02", "front_ids": ["F02"]})
    raw["width_spans"][0]["members"][1]["block_id"] = "B02"
    resolved, audit = resolve_cb_span_widths(raw, scope=scope)
    assert resolved["blocks"][0]["bays"][0]["width"] == 40  # cm
    assert resolved["blocks"][1]["bays"][0]["width"] == 800  # mm
    compiled = compose_cb_span_parts(raw, scope=scope)
    assert [b["size_mm"][0] for b in compiled["blocks"]] == [400, 800]
    assert audit["spans"][0]["allocated_mm"] == 1200


def test_equal_three_way_span_and_real_nonbay_interval(monkeypatch):
    _, _, scope, raw = span_answer(monkeypatch)
    s = raw["width_spans"][0]; s["value"] = 1; s["unit"] = "m"; s["source_label"] = "1"
    for m in s["members"]: m["weight"] = 1
    s["members"].append({"block_id": None, "bay_id": None, "weight": 1, "label": "Explicit wall gap"})
    _, audit = resolve_cb_span_widths(raw, scope=scope)
    assert audit["spans"][0]["allocated_mm"] == 1000
    assert [m["width_mm"] for m in audit["spans"][0]["members"]] == pytest.approx([1000 / 3] * 3)


def test_unanchored_fallback_is_visible_not_a_fake_span(monkeypatch):
    _, _, scope, raw = span_answer(monkeypatch)
    raw["width_spans"] = []
    for b in raw["blocks"][0]["bays"]: b["width"] = 50
    compiled = compose_cb_span_parts(raw, scope=scope)
    assert compiled["blocks"][0]["size_mm"][0] == 1000
    assert {b["basis"] for b in compiled["width_allocation"]["bay_widths"]} == {"unanchored_model_assumption"}


@pytest.mark.parametrize("change", ["duplicate", "numeric_and_span", "null_no_span", "unknown_bay", "unknown_view", "zero_weight", "nan_weight", "bool_value", "bad_unit", "endpoints", "label", "all_gap", "duplicate_span", "missing_block"])
def test_invalid_associations_fail_without_repair(monkeypatch, change):
    _, _, scope, raw = span_answer(monkeypatch)
    span = raw["width_spans"][0]; member = span["members"][0]
    if change == "duplicate": span["members"].append(deepcopy(member))
    if change == "numeric_and_span": raw["blocks"][0]["bays"][0]["width"] = 50
    if change == "null_no_span": raw["width_spans"] = []
    if change == "unknown_bay": member["bay_id"] = "not_known"
    if change == "unknown_view": span["view_id"] = "not_known"
    if change == "zero_weight": member["weight"] = 0
    if change == "nan_weight": member["weight"] = float("nan")
    if change == "bool_value": span["value"] = True
    if change == "bad_unit": span["unit"] = "inches"
    if change == "endpoints": span["endpoints_1000"] = [800, 0, 100, 0]
    if change == "label": span["source_label"] = ""
    if change == "all_gap":
        for m in span["members"]: m.update(block_id=None, bay_id=None)
    if change == "duplicate_span": raw["width_spans"].append(deepcopy(span))
    if change == "missing_block": raw["blocks"] = []
    with pytest.raises(ValueError): resolve_cb_span_widths(raw, scope=scope)


def test_v3_4_one_call_retains_raw_and_full_input(monkeypatch):
    row, pages, scope, raw = span_answer(monkeypatch)
    scope["front"] = fixture(monkeypatch)[2]["front"]
    raw["blocks"][0]["bays"][1]["fronts"][0]["body_height"] = 20
    calls = []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {})
    def provider(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph={}, dimension_scale_gate={}, allowed_material_families=[], cb_parts_scope=scope)
    assert len(calls) == 1 and calls[0]["system"].splitlines()[0] == "CB Parts V3.4"
    assert result["extraction"] == raw and result["parts_sized"]["blocks"][0]["size_mm"][0] == 1200
    context = json.loads(calls[0]["messages"][0]["content"][-1]["text"])
    assert context == {"calculation_scope": scope}
    assert result["upstream_status"]["front"] == "failed"


def test_live_span_trial_keeps_conserved_totals_and_wrong_topology_visible():
    from agents.estimation_v4_1_material_facts_agent import _json_object
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root / "notes/evidence/cb-parts-v3-4-2026-11-06/lev2-span-trial.json").read_text())
    raw = _json_object(saved["raw_response_text"])
    scope = saved["validation_scope"]
    resolved, audit = resolve_cb_span_widths(raw, scope=scope)
    assert audit == saved["width_allocation_audit_not_accepted_parts"]
    assert saved["request_same_except_prompt_and_version"] and saved["provider_calls"] == 1
    assert not saved["semantic_accepted"]
    for span in audit["spans"]:
        assert span["allocated_mm"] == pytest.approx(span["span_mm"])
        assert not span["association_verified"]
    b08 = next(b for b in resolved["blocks"] if b["id"] == "B08")
    assert len(b08["bays"]) == 1
    assert {f["id"] for f in b08["bays"][0]["fronts"]} == {"F21", "F22", "F23", "F24"}
    assert b08["bays"][0]["width"] == pytest.approx(151 * 1.3 / 4.3)  # cm, wrong physical association retained
    with pytest.raises(ValueError, match="stacked front heights"):
        compose_cb_span_parts(raw, scope=scope)
