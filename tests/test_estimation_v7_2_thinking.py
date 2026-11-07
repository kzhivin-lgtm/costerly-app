from copy import deepcopy
import pytest
from tools.probe_estimation_v7_2_thinking import replay_request


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
