from copy import deepcopy
from types import SimpleNamespace
import json
import pytest

from agents import estimation_analyze_v7_3_agent as agent
from tests.test_estimation_analyze_v7_2 import setup


def raw_fixture():
    row, context, value = setup()
    del value["objects"][0]["front"]["totals"]
    return row, context, value


def test_totals_are_derived_without_mutating_raw():
    row, context, raw = raw_fixture(); before = deepcopy(raw)
    result = agent.validate_result(raw, detection_context=context, inputs=[row])
    assert raw == before
    assert result["objects"][0]["front"]["totals"]["total_fronts"] == 0
    assert agent.derive_totals([dict(type="drawer", count=2), dict(type="drawer", count=3), dict(type="hinged", count=4)]) == dict(
        drawers=5, hinged_doors=4, lift_up_fronts=0, unresolved_fronts=0, total_fronts=9)


def test_unknown_counts_propagate_without_becoming_zero():
    value = agent.derive_totals([dict(type="drawer", count=None), dict(type="hinged", count=2)])
    assert value["drawers"] is None and value["total_fronts"] is None
    assert value["hinged_doors"] == 2 and value["lift_up_fronts"] == 0


@pytest.mark.parametrize("count", [True, -1, 1.5, "3"])
def test_totals_reject_invalid_count(count):
    with pytest.raises(ValueError): agent.derive_totals([dict(type="drawer", count=count)])


def test_model_totals_not_silently_overwritten():
    row, context, raw = raw_fixture()
    raw["objects"][0]["front"]["totals"] = {}
    with pytest.raises(ValueError, match="code-owned"):
        agent.validate_result(raw, detection_context=context, inputs=[row])


def test_derived_totals_do_not_repair_annotation_or_provenance_errors():
    row, context, raw = raw_fixture()
    raw["objects"][0]["front"]["front_groups"] = [dict(type="drawer", count=1,
        location="base", count_basis="clear", view_ids=["view-001"], uncertainty="", fronts=[])]
    with pytest.raises(ValueError): agent.validate_result(raw, detection_context=context, inputs=[row])
    row, context, raw = raw_fixture()
    raw["objects"][0]["understanding"]["characteristics"][0]["source_refs"] = ["view-001"]
    with pytest.raises(ValueError, match="source refs"):
        agent.validate_result(raw, detection_context=context, inputs=[row])


def test_normalization_copies_values_and_preserves_unknown_units():
    _, context, _ = raw_fixture()
    context["unit_context"] = dict(effective_unit="cm", reason="saved", declared=dict(unit="unknown"))
    before = deepcopy(context)
    rows = agent.island_normalization(context)
    m = rows[0]["readings"][0]
    assert m["original_text"] == "4" and m["value_mm"] == "40" and m["conversion_required"] is True
    assert rows[0]["unit_context"]["declared"]["unit"] == "unknown"
    assert context == before
    for unit, expected in [("mm", False), ("unknown", None)]:
        context["objects"][0]["dimension_inventory"][0]["occurrences"][0]["unit_basis"] = unit
        assert agent.island_normalization(context)[0]["readings"][0]["conversion_required"] is expected


def test_prompt_is_one_contract_without_model_totals_or_benchmark_targets():
    text = agent.prompt()
    assert '"totals"' not in text and "EXISTING CB FRONT POLICY" not in text
    assert "artificial stone 30 mm" in text and "never island IDs" in text
    assert "do not bridge" in text.lower() and "A sink cutout" in text
    assert "15 hinged" not in text and "eight blocks" not in text


def test_one_call_disabled_thinking_raw_recorded_before_validation(monkeypatch):
    row, context, raw = raw_fixture(); calls=[]; records=[]; options=[]
    monkeypatch.setattr(agent.previous.previous, "prepare_content", lambda **kw: [dict(type="text", text="saved")])
    monkeypatch.setattr(agent.previous.existing, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: options.append(kw)))
    monkeypatch.setattr(agent.previous.existing, "_create_message_with_hard_timeout", lambda *a, **kw:
        calls.append(kw) or SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(raw))]))
    agent.run_analyze(inputs=[row], page_bytes={}, detection_context=context, record=lambda stage,*args: records.append(stage))
    assert len(calls) == 1 and calls[0]["thinking"] == dict(type="disabled")
    assert calls[0]["max_tokens"] == 14000 and options == [dict(timeout=120, max_retries=0)]
    assert records == ["request", "response"]
    raw["objects"][0]["planner"]["blocks"][0]["front_ids"] = ["F_UNKNOWN"]
    records.clear()
    with pytest.raises(ValueError):
        agent.run_analyze(inputs=[row], page_bytes={}, detection_context=context, record=lambda stage,*args: records.append(stage))
    assert records == ["request", "response"]
