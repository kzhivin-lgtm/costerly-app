from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.estimation_assembly_bom_agent as agent
from tests.test_cb_parts import fixture
from tests.test_cb_parts_v3 import answer as sized_answer
from use_cases.estimation_cb_bays import compose_cb_bay_parts


def setup(monkeypatch):
    row, pages, scope, _ = fixture(monkeypatch)
    scope["parts_version"] = "CB Parts V3.3"
    fronts = scope["front"]["front_groups"][0]["fronts"]
    assert len(fronts) == 2
    scope["front"]["front_groups"] = [dict(type="drawer", fronts=[fronts[0]]), dict(type="hinged", fronts=[fronts[1]])]
    raw = {"blocks": [{"id": "B01", "kind": "carcass", "unit": "cm", "height": 85, "depth": 65,
        "thickness_mm": None, "assumptions": "Two estimated equal bays.", "bays": [
            {"id": "left", "width": 50, "shelves": 0, "fronts": [{"id": "F01", "height": 25, "body_height": 15}]},
            {"id": "right", "width": 50, "shelves": 1, "fronts": [{"id": "F02", "height": 80, "body_height": None}]}]}]}
    return row, pages, scope, raw


def test_bays_derive_width_panels_drawer_box_and_one_partition(monkeypatch):
    _, _, scope, raw = setup(monkeypatch)
    before = deepcopy((scope, raw))
    block = compose_cb_bay_parts(raw, scope=scope)["blocks"][0]
    assert (scope, raw) == before
    assert block["size_mm"] == [1000, 850, 650]
    rows = {p["name"]: p for p in block["parts"]}
    assert rows["Carcass top"]["size_mm"] == [1000, 650, 17]
    assert rows["Back panel"]["size_mm"] == [1000, 850, 17]
    assert rows["Hinged door"]["size_mm"] == [500, 800, 17]
    assert rows["Drawer front"]["size_mm"] == [500, 250, 17]
    assert rows["Drawer body side"]["size_mm"] == [500, 150, 17]
    assert rows["Drawer body side"]["quantity"] == rows["Drawer body end panel"]["quantity"] == 2
    assert rows["Drawer body side"]["drawer_depth_derived"]
    assert rows["Drawer bottom"]["drawer_depth_derived"]
    assert rows["Drawer bottom"]["quantity"] == 1
    assert rows["Shared mounting partition"]["quantity"] == 1
    assert block["derivation"]["partition_boundaries"] == [["left", "right"]]


def test_stacked_drawers_single_bay_no_duplicate_width_or_wall(monkeypatch):
    _, _, scope, raw = setup(monkeypatch)
    scope["front"]["front_groups"][1]["type"] = "drawer"
    b = raw["blocks"][0]
    b["bays"] = [{"id": "stack", "width": 60, "shelves": 0, "fronts": [
        {"id": "F01", "height": 20, "body_height": 15}, {"id": "F02", "height": 30, "body_height": 15}]}]
    block = compose_cb_bay_parts(raw, scope=scope)["blocks"][0]
    assert block["size_mm"][0] == 600
    assert block["derivation"]["partition_boundaries"] == []
    assert sum(p["quantity"] for p in block["parts"] if p["name"] == "Drawer front") == 2
    assert len([p for p in block["parts"] if p["name"] == "Drawer front"]) == 2


def test_two_adjacent_drawer_bays_share_one_wall(monkeypatch):
    _, _, scope, raw = setup(monkeypatch)
    scope["front"]["front_groups"][1]["type"] = "drawer"
    raw["blocks"][0]["bays"][1]["fronts"][0]["body_height"] = 20
    block = compose_cb_bay_parts(raw, scope=scope)["blocks"][0]
    assert next(p for p in block["parts"] if p["name"] == "Shared mounting partition")["quantity"] == 1


def test_two_door_bays_no_automatic_partition_and_specific_thickness(monkeypatch):
    _, _, scope, raw = setup(monkeypatch)
    scope["front"]["front_groups"][0]["type"] = "hinged"
    raw["blocks"][0]["bays"][0]["fronts"][0]["body_height"] = None
    raw["blocks"][0]["thickness_mm"] = 40
    block = compose_cb_bay_parts(raw, scope=scope)["blocks"][0]
    assert not block["derivation"]["partition_boundaries"]
    assert all(p["size_mm"][2] == 40 for p in block["parts"])


@pytest.mark.parametrize("change", ["width", "missing", "duplicate", "extra_width", "shelves", "body", "tall", "foreign", "unit", "duplicate_bay", "kind"])
def test_bad_topology_rejected_not_repaired(monkeypatch, change):
    _, _, scope, raw = setup(monkeypatch)
    b = raw["blocks"][0]; bay = b["bays"][0]
    if change == "width": bay["width"] = float("nan")
    if change == "missing": b["bays"].pop()
    if change == "duplicate": bay["fronts"].append(deepcopy(bay["fronts"][0]))
    if change == "extra_width": b["width"] = 500
    if change == "shelves": bay["shelves"] = True
    if change == "body": bay["fronts"][0]["body_height"] = 100
    if change == "tall": bay["fronts"][0]["height"] = 200
    if change == "foreign": bay["fronts"][0]["id"] = "F99"
    if change == "unit": b["unit"] = "inches"
    if change == "duplicate_bay": b["bays"][1]["id"] = bay["id"]
    if change == "kind": b["kind"] = "unknown"
    with pytest.raises(ValueError): compose_cb_bay_parts(raw, scope=scope)


def test_explicit_geometry_does_not_gain_carcass_panels(monkeypatch):
    _, _, scope, _ = setup(monkeypatch)
    raw = sized_answer()
    b = raw["blocks"][0]; b.update(kind="explicit", front_ids=["F01", "F02"])
    block = compose_cb_bay_parts(raw, scope=scope)["blocks"][0]
    assert len(block["parts"]) == 2
    assert block["parts"][1]["size_mm"][2] == 30
    assert block["derivation"]["mode"] == "explicit_model_geometry"


@pytest.mark.parametrize("omit", [None, "B01"])
def test_one_call_and_locator_ablation_preserve_original_scope(monkeypatch, omit):
    row, pages, scope, raw = setup(monkeypatch)
    # Existing fixture supplies legal detailed Front groups to plan validator.
    original_fronts = fixture(monkeypatch)[2]["front"]
    original_fronts["front_groups"][0]["type"] = "drawer"
    scope["front"] = original_fronts
    raw["blocks"][0]["bays"][1]["fronts"][0]["body_height"] = 20
    if omit: scope["diagnostic_omit_block_locator"] = omit
    before = deepcopy(scope)
    calls = []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {})
    def provider(*a, **kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", provider)
    result = agent.run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=pages,
        dimension_graph={}, dimension_scale_gate={}, allowed_material_families=[], cb_parts_scope=scope)
    assert len(calls) == 1 and scope == before
    assert calls[0]["system"].splitlines()[0] == "CB Parts V3.3"
    assert result["extraction"] == raw and result["parts_sized"]["blocks"][0]["size_mm"][0] == 1000
    assert result["upstream_status"]["front"] == "failed"
    supplied = json.loads(calls[0]["messages"][0]["content"][-1]["text"])["calculation_scope"]
    expected = deepcopy(scope); expected.pop("diagnostic_omit_block_locator", None)
    if omit: expected["planner"]["blocks"][0].pop("region")
    assert supplied == expected


def test_live_trials_keep_failed_objects_separate_from_b08_audits():
    from agents.estimation_v4_1_material_facts_agent import _json_object
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root / "notes/evidence/cb-parts-v3-3-2026-11-06/locator-and-bay-trials.json").read_text())
    assert saved["locator_ablation"]["only_B08_region_removed"]
    ablated = _json_object(saved["locator_ablation"]["response_text"])
    assert "S01" not in {b["id"] for b in ablated["blocks"]}
    scope = saved["validation_scope"]
    for run, width in zip(saved["v3_3_runs"], (900, 800)):
        raw = _json_object(run["raw_response_text"])
        assert run["request_identical_to_first"] and run["only_prompt_and_version_changed_from_original_v3_2"]
        assert run["status"] == "failed"
        with pytest.raises(ValueError, match="stacked front heights"):
            compose_cb_bay_parts(raw, scope=scope)
        b08 = next(b for b in raw["blocks"] if b["id"] == "B08")
        b08scope = {**scope, "planner": {"blocks": [b for b in scope["planner"]["blocks"] if b["id"] == "B08"], "shared_parts": []}}
        compiled = compose_cb_bay_parts({"blocks": [b08]}, scope=b08scope)["blocks"][0]
        audit = next(b for b in run["block_audit_not_runtime_result"] if b["id"] == "B08")
        assert compiled == audit["compiled_parts"]
        assert compiled["size_mm"][0] == width
        by_name = {p["name"]: p for p in compiled["parts"]}
        assert by_name["Carcass top"]["size_mm"][0] == by_name["Back panel"]["size_mm"][0] == width
        assert by_name["Shared mounting partition"]["quantity"] == 1
        assert by_name["Hinged door"]["size_mm"][0] + by_name["Drawer front"]["size_mm"][0] == width
        assert by_name["Drawer front"]["quantity"] == by_name["Drawer bottom"]["quantity"] == 3


def test_four_run_checkpoint_preserves_raw_failures_and_bay_sums():
    from hashlib import sha256
    from agents.estimation_v4_1_material_facts_agent import _json_object
    root = Path(__file__).resolve().parents[1]
    saved = json.loads((root / "notes/evidence/cb-parts-v3-3-2026-11-06/four-run-checkpoint.json").read_text())
    assert saved["new_calls"] == 2 and saved["full_object_passes"] == 0
    assert len({r["request_sha256"] for r in saved["runs"]}) == 1
    prompt_hash = sha256((root / "agents/prompts/cb_parts_v3_3.md").read_text().strip().encode()).hexdigest()
    assert {r["prompt_sha256"] for r in saved["runs"]} == {prompt_hash}
    scope = saved["validation_scope"]
    for run, width in zip(saved["runs"], (900, 800, 620, 1000)):
        raw = _json_object(run["raw_response_text"])
        assert run["request_identical_to_first"] and run["status"] == "failed"
        with pytest.raises(ValueError): compose_cb_bay_parts(raw, scope=scope)
        b08 = next(b for b in raw["blocks"] if b["id"] == "B08")
        sc = {**scope, "planner": {"blocks": [b for b in scope["planner"]["blocks"] if b["id"] == "B08"], "shared_parts": []}}
        compiled = compose_cb_bay_parts({"blocks": [b08]}, scope=sc)["blocks"][0]
        assert compiled == next(b for b in run["block_audit_not_runtime_result"] if b["id"] == "B08")["compiled_parts"]
        assert compiled["size_mm"][0] == width
        assert sum(b["width_mm"] for b in compiled["derivation"]["bays"]) == width
        assert sum(p["quantity"] for p in compiled["parts"] if p["name"] == "Shared mounting partition") == 1
    assert saved["runs"][2]["missing_block_ids"] == ["B09"]
