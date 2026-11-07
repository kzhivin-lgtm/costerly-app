from copy import deepcopy
import json
import pytest
from tools.probe_estimation_v7_2_thinking import replay_request, incremental_request, front_soft_request, hard_cap_request, prompt_v2_request, disabled_effort_request, PROMPT_V2_PATH, FRONT_SOFT_STEERING
from agents import estimation_analyze_v7_2_agent as original_agent


def test_replay_changes_only_thinking_without_mutating_baseline():
    baseline = dict(version="Estimation V7.2", provider_request=dict(
        model="saved-model", thinking={"type": "disabled"}, max_tokens=14000,
        system="unchanged", messages=[{"role": "user", "content": ["saved pixels"]}]))
    original = deepcopy(baseline)
    request = replay_request(baseline)
    assert baseline == original
    assert {**request, "thinking": {"type": "disabled"}} == original["provider_request"]
    assert "thinking" not in request


def test_replay_rejects_wrong_baseline():
    with pytest.raises(ValueError):
        replay_request(dict(version="Estimation V7.3", provider_request={}))


def baseline(version="Estimation V7.2"):
    return dict(version=version, provider_response=dict(stop_reason="end_turn"),
        provider_request=dict(model="saved-model", max_tokens=14000,
            system=original_agent.prompt(), messages=[dict(role="user", content=["saved-pixels"])],
            output_config=dict(effort="low")))


def test_731_only_changes_display_not_request():
    saved = baseline(); before = deepcopy(saved)
    assert incremental_request(saved, "V7.3.1") == saved["provider_request"]
    assert saved == before


def test_732_only_removes_totals_and_adds_matching_instruction():
    saved = baseline("Estimation V7.3.1"); before = deepcopy(saved)
    new = incremental_request(saved, "V7.3.2")
    assert saved == before
    assert {k:v for k,v in new.items() if k != "system"} == {k:v for k,v in saved["provider_request"].items() if k != "system"}
    marker = "SINGLE AUTHORITATIVE RESPONSE TEMPLATE\n"
    old_policy, old_template = saved["provider_request"]["system"].split(marker)
    policy, template = new["system"].split(marker)
    assert policy.startswith(old_policy)
    old_json = json.loads(old_template); new_json = json.loads(template)
    del old_json["objects"][0]["front"]["totals"]
    assert old_json == new_json
    assert '"totals"' not in template
    assert "thinking" not in new


def test_733_only_adds_kitchen_material_default():
    saved = baseline("Estimation V7.3.1")
    saved.update(version="Estimation V7.3.2", provider_request=incremental_request(saved, "V7.3.2"))
    new = incremental_request(saved, "V7.3.3")
    addition = (" For an unspecified KITCHEN worktop, choose artificial stone as the estimating "
        "material default, not laminated chipboard. Do not assert quartz or a brand; "
        "source-specified material takes priority.")
    assert new["system"].count(addition) == 1
    new["system"] = new["system"].replace(addition, "")
    assert new == saved["provider_request"]


@pytest.mark.parametrize("revision", ["V7.3.1", "V7.3.2", "V7.3.3"])
def test_increment_requires_preceding_completed_thinking_baseline(revision):
    saved = baseline("wrong")
    with pytest.raises(ValueError): incremental_request(saved, revision)
    expected = {"V7.3.1":"Estimation V7.2", "V7.3.2":"Estimation V7.3.1", "V7.3.3":"Estimation V7.3.2"}
    saved["version"] = expected[revision]
    saved["provider_request"]["thinking"] = dict(type="disabled")
    with pytest.raises(ValueError): incremental_request(saved, revision)


def test_increment_does_not_continue_from_truncated_response():
    saved = baseline("Estimation V7.3.2")
    saved["provider_response"]["stop_reason"] = "max_tokens"
    with pytest.raises(ValueError, match="completed"):
        incremental_request(saved, "V7.3.3")


def test_front_soft_only_appends_reasoning_guidance_to_original_control():
    saved = baseline(); before = deepcopy(saved)
    request = front_soft_request(saved)
    assert saved == before
    assert request["system"] == before["provider_request"]["system"] + "\n\n" + FRONT_SOFT_STEERING
    request["system"] = before["provider_request"]["system"]
    assert request == before["provider_request"]
    assert '"totals"' in request["system"] and "artificial stone" not in request["system"]


@pytest.mark.parametrize("problem", ["wrong_version", "truncated", "disabled", "different_effort"])
def test_front_soft_rejects_a_changed_or_incomplete_control(problem):
    saved = baseline()
    if problem == "wrong_version": saved["version"] = "Estimation V7.3.2"
    if problem == "truncated": saved["provider_response"]["stop_reason"] = "max_tokens"
    if problem == "disabled": saved["provider_request"]["thinking"] = dict(type="disabled")
    if problem == "different_effort": saved["provider_request"]["output_config"]["effort"] = "medium"
    with pytest.raises(ValueError): front_soft_request(saved)


def test_hard_cap_changes_only_max_tokens_and_preserves_original():
    saved = baseline(); before = deepcopy(saved)
    request = hard_cap_request(saved)
    assert request["max_tokens"] == 5000
    assert saved == before
    request["max_tokens"] = 14000
    assert request == before["provider_request"]


@pytest.mark.parametrize("problem", ["changed_prompt", "wrong_cap", "disabled", "truncated", "other_version"])
def test_hard_cap_cannot_inherit_soft_or_v73_changes(problem):
    saved = baseline()
    if problem == "changed_prompt": saved["provider_request"]["system"] += "\nThink briefly."
    if problem == "wrong_cap": saved["provider_request"]["max_tokens"] = 6000
    if problem == "disabled": saved["provider_request"]["thinking"] = dict(type="disabled")
    if problem == "truncated": saved["provider_response"]["stop_reason"] = "max_tokens"
    if problem == "other_version": saved["version"] = "Estimation V7.3"
    with pytest.raises(ValueError): hard_cap_request(saved)


def test_prompt_v2_matches_approved_wording_and_changes_only_guidance():
    saved = baseline(); before = deepcopy(saved)
    guidance = PROMPT_V2_PATH.read_text().strip()
    assert guidance == ("REASONING GUIDANCE\n"
        "Do not perform a separate extended analysis for each section.\n"
        "Use Detection's established island correspondences and normalized measurements directly.\n"
        "Use brief internal reasoning only for ambiguous operating fronts and tabletop supports.\n"
        "Do not explore alternative constructions or repeat a complete analysis.\n"
        "Return the same complete JSON without additional reasoning text.")
    request = prompt_v2_request(saved)
    assert request["system"] == before["provider_request"]["system"] + "\n\n" + guidance
    request["system"] = before["provider_request"]["system"]
    assert request == before["provider_request"] and saved == before
    assert request["max_tokens"] == 14000 and '"totals"' in request["system"]


@pytest.mark.parametrize("problem", ["soft", "cap", "v73", "disabled", "incomplete"])
def test_prompt_v2_rejects_accumulated_changes(problem):
    saved = baseline()
    if problem == "soft": saved["provider_request"] = front_soft_request(saved)
    if problem == "cap": saved["provider_request"]["max_tokens"] = 5000
    if problem == "v73": saved["version"] = "Estimation V7.3.3"
    if problem == "disabled": saved["provider_request"]["thinking"] = dict(type="disabled")
    if problem == "incomplete": saved["provider_response"]["stop_reason"] = "max_tokens"
    with pytest.raises(ValueError): prompt_v2_request(saved)


@pytest.mark.parametrize("effort", ["medium", "high"])
def test_disabled_effort_changes_only_effort_on_original_low(effort):
    saved = baseline()
    saved["provider_request"]["thinking"] = dict(type="disabled")
    before = deepcopy(saved)
    request = disabled_effort_request(saved, effort)
    assert request["thinking"] == dict(type="disabled")
    assert request["output_config"] == dict(effort=effort)
    request["output_config"]["effort"] = "low"
    assert request == before["provider_request"] and saved == before


@pytest.mark.parametrize("problem", ["adaptive", "medium_source", "changed_prompt", "cap", "incomplete", "v73", "max"])
def test_disabled_effort_rejects_nonoriginal_source_or_unsupported_level(problem):
    saved = baseline(); saved["provider_request"]["thinking"] = dict(type="disabled")
    effort = "medium"
    if problem == "adaptive": del saved["provider_request"]["thinking"]
    if problem == "medium_source": saved["provider_request"]["output_config"]["effort"] = "medium"
    if problem == "changed_prompt": saved["provider_request"]["system"] += "\nThink briefly."
    if problem == "cap": saved["provider_request"]["max_tokens"] = 5000
    if problem == "incomplete": saved["provider_response"]["stop_reason"] = "max_tokens"
    if problem == "v73": saved["version"] = "Estimation V7.3"
    if problem == "max": effort = "max"
    with pytest.raises(ValueError): disabled_effort_request(saved, effort)
