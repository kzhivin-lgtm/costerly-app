from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_planner import plan, front
from tests.test_estimation_module_understanding import setup
from use_cases.estimation_cb_parts import compose_cb_parts, face_size
from use_cases.estimation_dimension_graph import build_dimension_graph


def fixture(monkeypatch):
    row, pages, _ = setup(monkeypatch)
    scope = dict(input_id=row["input_id"], parts_version="CB Parts V1", planner=plan(), front=front(),
        upstream_status={"front": "failed", "planner": "assembly_plan_requires_review"})
    scope["front"]["front_groups"][0]["type"] = "drawer"
    def dim(n):
        return dict(value=n, basis="assumption", evidence_refs=[], assumption_reason="Unlabelled estimated size")
    raw = dict(document_unit=dict(unit="mm", basis="document_convention_assumption", evidence_refs=[], assumption_reason="Estimated mm"),
        materials=[], view_interpretations=[], dimension_bindings=[], conflicts=[], omissions=[],
        blocks=[dict(id="B01", dimensions=dict(width=1000, height=800, depth=720), parts=[
            dict(role="side", quantity=2, size=["height", "depth"], material_id="M0", front_ids=[], note="Outer carcass sides"),
            dict(role="partition", quantity=1, size=["height", "depth"], material_id="M0", front_ids=[], note="One shared partition"),
            dict(role="facade", quantity=2, size=["width/2", "height"], material_id="M0", front_ids=["F01", "F02"], note="Assumed equal fronts"),
            dict(role="drawer_box", quantity=2, size=["width/2", "150"], material_id="M0", front_ids=["F01", "F02"], note="Estimated box height 150 mm")])])
    raw["blocks"][0]["dimensions"] = {k: dim(v) for k, v in raw["blocks"][0]["dimensions"].items()}
    return row, pages, scope, raw


def compose(row, scope, raw):
    return compose_cb_parts(response=raw, input_row=row, scope=scope,
        dimension_graph=build_dimension_graph(input_row=row), allowed_material_families=["ldsp", "mdf"])


def test_coarse_parts_preserve_inputs_defaults_and_drawer_rule(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    before = deepcopy((row, scope, raw))
    bom = compose(row, scope, raw)
    assert (row, scope, raw) == before
    assert bom["status"] == "cb_parts_requires_review"
    assert bom["upstream_status"]["front"] == "failed"
    assert bom["materials"][0]["specification"] == dict(thickness_mm=17, stock_thickness_mm=17, layers=1)
    parts = {p["component_role"]: p for p in bom["parts"]}
    assert parts["drawer_bottom"]["width_mm"] == 600
    assert parts["drawer_side"]["length_mm"] == 600
    assert parts["drawer_side"]["quantity"] == 4
    assert parts["drawer_end"]["quantity"] == 4
    assert parts["partition"]["quantity"] == 1
    assert parts["facade"]["quantity"] == 2
    assert parts["drawer_bottom"]["length_mm"] == 500  # no clearance/thickness deductions
    assert all(p["basis"] == "assumption" for p in parts.values())
    assert bom["material_area_per_object"][0]["finished_area_m2"] == pytest.approx(3.788)


def test_specific_40mm_layers_override_only_selected_material(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    raw["materials"] = [dict(id="M1", name="Veneered MDF", family="mdf", thickness_mm=40,
        stock_thickness_mm=20, layers=2, basis="construction_assumption", evidence_refs=[], reason="Two 20 mm panels")]
    raw["blocks"][0]["parts"][0]["material_id"] = "M1"
    bom = compose(row, scope, raw)
    assert {m["specification"]["thickness_mm"] for m in bom["materials"]} == {17, 40}
    assert bom["material_area_per_object"][0]["stock_area_m2"] == 2 * bom["material_area_per_object"][0]["finished_area_m2"]


@pytest.mark.parametrize("expression", ["__import__('os')", "width**2", "width/0", "depth.foo", "True", "height-height", "NaN"])
def test_size_expression_is_bounded_arithmetic(expression):
    with pytest.raises(ValueError):
        face_size(expression, dict(width=500, height=700, depth=720))


@pytest.mark.parametrize("change", ["missing_block", "duplicate_block", "missing_drawer", "missing_facade", "foreign_front", "duplicate_front", "negative_size", "nan", "bad_layers", "foreign_refs"])
def test_contract_rejects_silent_loss_and_invention(monkeypatch, change):
    row, _, scope, raw = fixture(monkeypatch)
    b = raw["blocks"][0]
    if change == "missing_block": raw["blocks"] = []
    if change == "duplicate_block": raw["blocks"].append(deepcopy(b))
    if change == "missing_drawer": b["parts"].pop()
    if change == "missing_facade": b["parts"].pop(2)
    if change == "foreign_front": b["parts"][2]["front_ids"][0] = "foreign"
    if change == "duplicate_front": b["parts"].append(deepcopy(b["parts"][2]))
    if change == "negative_size": b["parts"][0]["size"][0] = "0-10"
    if change == "nan": b["dimensions"]["width"]["value"] = float("nan")
    if change == "bad_layers": raw["materials"] = [dict(id="M1", name="MDF", family="mdf", thickness_mm=40, stock_thickness_mm=17, layers=2, basis="construction_assumption", evidence_refs=[], reason="Invalid stack")]
    if change == "foreign_refs": b["dimensions"]["width"]["evidence_refs"] = ["fake"]
    with pytest.raises(ValueError): compose(row, scope, raw)


def test_shared_worktop_is_required_once(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    scope["planner"]["shared_parts"] = [dict(id="S01", block_ids=["B01"], front_ids=[])]
    with pytest.raises(ValueError, match="parts block"):
        compose(row, scope, raw)
    worktop = deepcopy(raw["blocks"][0]); worktop["id"] = "S01"
    worktop["parts"] = [dict(role="worktop", quantity=1, size=["width", "depth"], material_id="M0", front_ids=[], note="Shared top once")]
    raw["blocks"].append(worktop)
    assert len(compose(row, scope, raw)["assemblies"]) == 2


def test_calculate_single_call_no_legacy_batches_and_raw_capture(monkeypatch):
    row, pages, scope, raw = fixture(monkeypatch)
    calls, records = [], []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_v4_1_evidence_batches", lambda *a: pytest.fail("legacy batching called"))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {"prompt_version": kw["prompt_version"]})
    def provider(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph=build_dimension_graph(input_row=row), dimension_scale_gate={},
        allowed_material_families=["ldsp"], cb_parts_scope=scope, record=lambda *args: records.append(args))
    assert len(calls) == 1 and len(records) == 2
    assert calls[0]["model"] == "claude-haiku-5-5"
    assert calls[0]["thinking"] == {"type": "disabled"}
    assert calls[0]["system"].startswith("CB Parts V1")
    assert result["extraction"] == raw
    assert result["bom"]["upstream_status"]["front"] == "failed"
    assert any(c["type"] == "image" for c in calls[0]["messages"][0]["content"])
    assert all(ord(c) < 128 for c in calls[0]["system"])


def test_source_without_numeric_witness_becomes_assumption(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    axis = raw["blocks"][0]["dimensions"]["width"]
    axis.update(basis="source", evidence_refs=[row["input_payload"]["evidence"]["artifacts"][0]["storage_ref"]], assumption_reason=None)
    bom = compose(row, scope, raw)
    assert bom["resolved_blocks"][0]["dimensions"]["width"]["basis"] == "assumption"
    assert raw["blocks"][0]["dimensions"]["width"]["basis"] == "source"


def test_rejected_numeric_binding_does_not_silently_keep_size(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    raw["dimension_bindings"] = [dict(assembly_id="B01", axis="width", view_id="p1-view-001",
        local_orientation="horizontal", dimension_id="invented", resolution="direct")]
    with pytest.raises(ValueError, match="rejected 2VN dimension"):
        compose(row, scope, raw)


def test_multiple_pages_still_one_call_and_truncation_is_captured(monkeypatch):
    row, pages, scope, raw = fixture(monkeypatch)
    row["input_payload"]["evidence"]["artifacts"].append(dict(artifact_kind="page", page_number=2, storage_ref="second-page"))
    pages["second-page"] = pages["page"]
    calls, records = [], []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_v4_1_evidence_batches", lambda *a: pytest.fail("legacy batching called"))
    def provider(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="max_tokens", content=[SimpleNamespace(type="text", text='{"blocks":[')])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    with pytest.raises(ValueError, match="did not finish"):
        agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
            dimension_graph=build_dimension_graph(input_row=row), dimension_scale_gate={},
            allowed_material_families=["ldsp"], cb_parts_scope=scope, record=lambda *args: records.append(args))
    assert len(calls) == 1 and len(records) == 2
    text = json.dumps(calls[0]["messages"][0]["content"])
    assert "second-page" in text


def test_material_evidence_in_document_context_is_retained(monkeypatch):
    row, _, scope, raw = fixture(monkeypatch)
    raw["materials"] = [dict(id="M1", name="Legend MDF", family="mdf", thickness_mm=17,
        stock_thickness_mm=17, layers=1, basis="source_evidence", evidence_refs=["legend"], reason="Legend material")]
    raw["blocks"][0]["parts"][0]["material_id"] = "M1"
    assert compose(row, scope, raw)["materials"][0]["evidence_refs"] == ["legend"]


def test_real_v1_experiments_remain_failed_without_json_repair():
    saved = json.loads((Path(__file__).resolve().parents[1] / "notes/evidence/cb-parts-v1-2026-11-06/lev2-calculation.json").read_text())
    assert saved["accepted"] is False and saved["same_evidence"] is True
    assert saved["changed_request_fields_02_to_03"] == ["thinking"]
    first, thinking, disabled = saved["runs"]
    assert first["response_text"] is None
    assert thinking["stop_reason"] == "max_tokens"
    assert thinking["usage"]["output_tokens_details"]["thinking_tokens"] == 13971
    assert disabled["stop_reason"] == "end_turn"
    assert disabled["usage"]["output_tokens_details"]["thinking_tokens"] == 0
    for trial in (thinking, disabled):
        with pytest.raises(ValueError):
            agent._json_object(trial["response_text"])
