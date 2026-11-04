from types import SimpleNamespace

import pytest

from tools.replay_estimation_v6 import capture_provider_responses
import agents.estimation_composition_analyze_agent as analyze


def test_replay_retains_raw_response_and_usage_before_validation_failure(monkeypatch):
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text='{"unexpected":true}')],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=20), id="r", stop_reason="end_turn")
    original = lambda *_args, **_kwargs: response
    monkeypatch.setattr(analyze, "_create_message_with_hard_timeout", original)
    witness, snapshots = {}, []
    with pytest.raises(ValueError):
        with capture_provider_responses(witness, lambda: snapshots.append(list(witness["provider_responses"]))):
            assert analyze._create_message_with_hard_timeout(object(), model="test", messages=[]) is response
            raise ValueError("later validation failed")
    assert analyze._create_message_with_hard_timeout is original
    assert snapshots[0][0]["response_text"] == '{"unexpected":true}'
    assert snapshots[0][0]["usage"]["output_tokens"] == 20


def test_replay_uses_only_identical_cached_requests_without_paid_calls(monkeypatch):
    calls = []
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text="{}")], usage=SimpleNamespace(input_tokens=10))
    monkeypatch.setattr(analyze, "_create_message_with_hard_timeout", lambda *_args, **_kwargs: calls.append(1) or response)
    first = {}
    with capture_provider_responses(first, lambda: None):
        analyze._create_message_with_hard_timeout(object(), model="test", messages=["a"])
    second = {}
    with capture_provider_responses(second, lambda: None, cached=first["provider_responses"], allow_calls=False):
        assert analyze._create_message_with_hard_timeout(object(), model="test", messages=["a"]).content[0].text == "{}"
        with pytest.raises(RuntimeError, match="paid calls disabled"):
            analyze._create_message_with_hard_timeout(object(), model="test", messages=["changed"])
    assert calls == [1] and second["provider_responses"][0]["reused"] is True


def test_diagnostic_thinking_options_are_fingerprinted_and_do_not_store_thinking_blocks(monkeypatch):
    requests = []
    response = SimpleNamespace(content=[SimpleNamespace(type="thinking", thinking="private"),
        SimpleNamespace(type="text", text="{}")], usage=SimpleNamespace(input_tokens=10))
    monkeypatch.setattr(analyze, "_create_message_with_hard_timeout", lambda _client, **kwargs: requests.append(kwargs) or response)
    witness = {}
    with capture_provider_responses(witness, lambda: None, request_overrides={"analyze": {"thinking": {"type": "adaptive"}}}):
        analyze._create_message_with_hard_timeout(object(), model="test", temperature=0, messages=[])
    assert "temperature" not in requests[0]
    record = witness["provider_responses"][0]
    assert record["request"]["thinking"] == {"type": "adaptive"}
    assert record["response_text"] == "{}" and "private" not in str(record)


@pytest.mark.parametrize("v6", [False, True])
def test_calculation_selects_geometry_prompt_only_for_locked_v6_scope(monkeypatch, v6):
    import agents.estimation_assembly_bom_agent as calculation
    import agents.estimation_geometry_verification_agent as verification
    monkeypatch.setattr(verification, "verify_geometry_once", lambda **kw: pytest.fail("Unaccepted verifier reached normal Calculation"))
    requests = []
    monkeypatch.setattr(calculation, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(calculation, "build_v4_1_evidence_batches", lambda payload: [{"batch_id": "b", "pages": []}])
    monkeypatch.setattr(calculation, "build_agent_usage_event", lambda **kw: {})
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text='{"document_unit":{"unit":"mm"},"assemblies":[]}')],
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1))
    monkeypatch.setattr(calculation, "_create_message_with_hard_timeout", lambda client, **kw: requests.append(kw) or response)
    calculation.run_estimation_assembly_bom_agent(input_row={"input_payload": {}}, evidence_page_bytes_by_ref={},
        dimension_graph={}, dimension_scale_gate={}, allowed_material_families=[], model="test",
        composition_scope={"construction_version": "estimation_construction_v6_1"} if v6 else None)
    expected = calculation.V6_PROMPT_PATH if v6 else calculation.PROMPT_PATH
    assert requests[0]["system"] == expected.read_text().strip()
    assert len(requests) == 1


@pytest.mark.parametrize("flags", [
    ["--observe-relations"], ["--observe-view", "v"], ["--reobserve-ownership"],
    ["--observe-measurements"], ["--measurement-axes"], ["--fresh-provider"],
    ["--geometry-verification", "--observe-only"],
])
def test_invalid_diagnostic_modes_fail_before_provider_or_database_access(monkeypatch, tmp_path, flags):
    from tools import replay_estimation_v6 as replay
    monkeypatch.setattr("sys.argv", ["replay", "input", "--output", str(tmp_path / "unused.json"), *flags])
    monkeypatch.setattr(replay, "get_supabase_client", lambda: pytest.fail("Invalid mode reached database"))
    with pytest.raises(SystemExit) as error:
        replay.main()
    assert error.value.code == 2
