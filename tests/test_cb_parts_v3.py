from copy import deepcopy
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_parts import fixture
from use_cases.estimation_cb_parts import compose_cb_sized_parts


def answer():
    return {"blocks": [{"id": "B01", "unit": "cm", "size": [120, 80, 72],
        "assumptions": "Bay widths estimated.", "parts": [
            {"name": "Drawer body side", "quantity": 6, "role": "panel", "size": ["drawer_depth", 20],
             "thickness_mm": None, "approximate": True},
            {"name": "Worktop", "quantity": 1, "role": "worktop", "size": [120, 72],
             "thickness_mm": None, "approximate": False}]}]}


def test_units_defaults_and_drawer_depth_preserve_raw(monkeypatch):
    _, _, scope, _ = fixture(monkeypatch)
    raw = answer(); before = deepcopy(raw)
    rows = compose_cb_sized_parts(raw, scope=scope)["blocks"][0]["parts"]
    assert raw == before
    assert rows[0]["size_mm"] == [600, 200, 17]
    assert rows[1]["size_mm"] == [1200, 720, 30]
    assert rows[1]["approximate"] and rows[1]["thickness_basis"] == "default"
    raw["blocks"][0]["parts"][1]["thickness_mm"] = 40
    assert compose_cb_sized_parts(raw, scope=scope)["blocks"][0]["parts"][1]["size_mm"][2] == 40


@pytest.mark.parametrize("change", ["unit", "missing", "duplicate", "quantity", "bool", "negative", "nan", "extra", "envelope", "same_row", "flag"])
def test_invalid_contract_is_not_repaired(monkeypatch, change):
    _, _, scope, _ = fixture(monkeypatch)
    raw = answer(); b = raw["blocks"][0]; p = b["parts"][0]
    if change == "unit": b["unit"] = "unknown"
    if change == "missing": raw["blocks"] = []
    if change == "duplicate": raw["blocks"].append(deepcopy(b))
    if change == "quantity": p["quantity"] = 1.5
    if change == "bool": p["size"][1] = True
    if change == "negative": p["thickness_mm"] = -1
    if change == "nan": b["size"][0] = float("nan")
    if change == "extra": p["material"] = "ldsp"
    if change == "envelope": p["size"][1] = 2000
    if change == "same_row": b["parts"].append(deepcopy(p))
    if change == "flag": p["approximate"] = "yes"
    with pytest.raises(ValueError): compose_cb_sized_parts(raw, scope=scope)


@pytest.mark.parametrize("version", ["CB Parts V3", "CB Parts V3.1", "CB Parts V3.2"])
def test_v3_one_call_whole_evidence_no_legacy_composition(monkeypatch, version):
    row, pages, scope, _ = fixture(monkeypatch)
    scope["parts_version"] = version
    calls, records = [], []
    raw = answer()
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {})
    monkeypatch.setattr(agent, "build_v4_1_evidence_batches", lambda *a: pytest.fail("legacy batch"))
    def provider(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph={}, dimension_scale_gate={}, allowed_material_families=[], cb_parts_scope=scope,
        record=lambda *args: records.append(args))
    assert len(calls) == 1 and len(records) == 2
    assert calls[0]["system"].splitlines()[0] == version
    assert all(ord(c) < 128 for c in calls[0]["system"])
    assert any(b["type"] == "image" for b in calls[0]["messages"][0]["content"])
    assert result["extraction"] == raw and "bom" not in result
    assert result["upstream_status"]["front"] == "failed"
    assert result["status"] == "cb_parts_sized_requires_review"


def test_v3_1_adds_only_one_generic_width_rule():
    prompts = Path(__file__).resolve().parents[1] / "agents/prompts"
    original = (prompts / "cb_parts_v3.md").read_text().split("\n\n")
    revised = (prompts / "cb_parts_v3_1.md").read_text().split("\n\n")
    rule = revised.pop(3)
    assert rule.startswith("Width estimation:")
    assert "neighbouring blocks" in rule and "assumptions field" in rule
    assert all(token not in rule for token in ("151", "B08", "Lev2", "110"))
    revised[0] = original[0]
    assert revised == original


def test_v3_2_adds_only_generic_bay_sum_and_shared_wall_rule():
    prompts = Path(__file__).resolve().parents[1] / "agents/prompts"
    original = (prompts / "cb_parts_v3_1.md").read_text().split("\n\n")
    revised = (prompts / "cb_parts_v3_2.md").read_text().split("\n\n")
    rule = revised.pop(4)
    assert rule.startswith("Bay consistency:")
    assert "SUM" in rule and "equal subdivision" in rule and "ONE shared mounting partition" in rule
    assert "Vertically stacked drawers" in rule
    assert all(token not in rule for token in ("151", "B08", "Lev2", "500", "1000"))
    revised[0] = original[0]
    assert revised == original


def test_live_v3_witness_retains_geometry_failures():
    saved = json.loads((Path(__file__).resolve().parents[1] / "notes/evidence/cb-parts-v3-2026-11-06/lev2-sized-parts.json").read_text())
    raw = json.loads(saved["response_text"])
    scope = {"planner": {"blocks": [{"id": x} for x in saved["input_block_ids"]], "shared_parts": []}}
    assert raw == saved["parsed_response"]
    assert compose_cb_sized_parts(raw, scope=scope) == saved["normalized_parts"]
    assert saved["same_input_and_pages_as_v2"] and saved["same_supplied_images_as_v2"]
    assert saved["image_count"] == 5 and saved["provider_calls"] == 1
    assert saved["semantic_accepted"] is False
    b = next(b for b in raw["blocks"] if b["id"] == "B08")
    assert b["unit"] == "cm" and b["size"] == [60, 72, 60]
    assert next(p for p in b["parts"] if p["name"] == "Shared internal partition")["quantity"] == 1
    fronts = next(p for p in b["parts"] if p["name"] == "Drawer front")
    assert fronts["quantity"] == 3 and fronts["size"] == [30, 22]  # visible error, not repaired


def test_live_v3_1_preserves_failed_width_allocation_and_missing_divider():
    saved = json.loads((Path(__file__).resolve().parents[1] / "notes/evidence/cb-parts-v3-1-2026-11-06/lev2-sized-parts.json").read_text())
    raw = json.loads(saved["response_text"])
    scope = {"planner": {"blocks": [{"id": x} for x in saved["input_block_ids"]], "shared_parts": []}}
    result = compose_cb_sized_parts(raw, scope=scope)
    b08 = next(b for b in result["blocks"] if b["id"] == "B08")
    assert b08 == saved["normalized_b08"]
    assert saved["same_input_and_pages_as_v3"] and saved["request_same_except_prompt_and_version"]
    assert saved["provider_calls"] == 1 and not saved["semantic_accepted"]
    assert b08["size_mm"][0] == 500
    assert next(p for p in b08["parts"] if p["name"] == "Hinged door")["size_mm"][0] == 500
    assert next(p for p in b08["parts"] if p["name"] == "Drawer front")["size_mm"][0] == 500
    assert not any("partition" in p["name"].lower() or "divider" in p["name"].lower() for p in b08["parts"])


def test_live_v3_2_retains_width_failure_and_returned_partition():
    saved = json.loads((Path(__file__).resolve().parents[1] / "notes/evidence/cb-parts-v3-2-2026-11-06/lev2-sized-parts.json").read_text())
    raw = json.loads(saved["response_text"])
    scope = {"planner": {"blocks": [{"id": x} for x in saved["input_block_ids"]], "shared_parts": []}}
    b08 = next(b for b in compose_cb_sized_parts(raw, scope=scope)["blocks"] if b["id"] == "B08")
    assert b08 == saved["normalized_b08"]
    assert saved["same_input_and_pages_as_v3_1"] and saved["request_same_except_prompt_and_version"]
    assert saved["provider_calls"] == 1 and not saved["semantic_accepted"]
    assert b08["size_mm"][0] == 500
    by_name = {p["name"]: p for p in b08["parts"]}
    assert by_name["Hinged door"]["size_mm"][0] == by_name["Drawer front"]["size_mm"][0] == 500
    assert by_name["Shared mounting partition"]["quantity"] == 1
    assert saved["targeted_checks"] == {"adjacent_bay_sum": "FAIL", "shared_mounting_partition": "PASS"}
