from copy import deepcopy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from agents import anthropic_adapter as adapter
from agents import estimation_v4_1_material_facts_agent as gateway
from use_cases import estimation_parts_check_runtime as runtime


class Response:
    def __init__(self, text, stop_reason="end_turn", broken_trace=False):
        self.content = [SimpleNamespace(type="text", text=text)]
        self.stop_reason = stop_reason
        self.model = "claude-haiku-5-5"
        self.usage = SimpleNamespace(input_tokens=100, output_tokens=10)
        self._request_id = "req-offline"
        self.broken_trace = broken_trace

    def model_dump(self, **_kwargs):
        if self.broken_trace:
            raise TypeError("fixture serialization failure")
        return {"id": "msg-offline", "model": self.model, "stop_reason": self.stop_reason,
                "content": [{"type": "text", "text": self.content[0].text}]}


@pytest.fixture
def provider(monkeypatch):
    client = SimpleNamespace(with_options=lambda **_kwargs: client)
    sent, events = [], []
    state = {"response": Response('{"direct_labels":[]}')}

    def send(_client, **kwargs):
        sent.append(deepcopy(kwargs))
        if "error" in state:
            raise state["error"]
        return state["response"]

    monkeypatch.setattr(adapter, "get_anthropic_client", lambda: client)
    monkeypatch.setattr(adapter, "build_agent_usage_event", lambda **kw: {"raw_usage": kw["request_diagnostics"]})
    monkeypatch.setattr(gateway, "_create_message_with_hard_timeout", send)
    invoke = runtime._request_provider("610", "run-new", "estimate-new", "Ada.pdf", events)
    request = {"model": "claude-haiku-5-5", "max_tokens": 2500, "thinking": {"type": "disabled"},
               "output_config": {"effort": "medium"}, "system": "fixture",
               "messages": [{"role": "user", "content": [{"type": "image", "source": {
                   "type": "base64", "media_type": "image/png", "data": "private-input-image-fixture"}}]}]}
    return invoke, request, state, sent, events


@pytest.mark.parametrize("labels", [[], [{"id": "C16", "role": "mirror", "source_text": "Зеркало"}]])
def test_actual_reply_is_saved_before_binding_without_changing_request_or_result(provider, labels):
    invoke, request, state, sent, events = provider
    text = json.dumps({"direct_labels": labels}, ensure_ascii=False)
    state["response"] = Response(text)

    def bind(raw):
        assert events[0]["raw_usage"]["provider_response"]["content"][0]["text"] == text
        return {"bound": raw["direct_labels"]}

    assert invoke("marked-view-001", request, bind) == {"bound": labels}
    assert sent == [{"timeout_seconds": 120, **request}]
    audit = events[0]["raw_usage"]
    assert audit["provider_request_id"] == "req-offline"
    assert audit["provider_response"]["model"] == "claude-haiku-5-5"
    assert audit["estimate_id"] == "estimate-new"
    assert "private-input-image-fixture" not in json.dumps(audit)
    wire = adapter._prepare_claude_request(deepcopy(request))
    assert audit["request_fingerprint"] == sha256(json.dumps(
        wire, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode()).hexdigest()


@pytest.mark.parametrize("text, stop", [("{not-json", "end_turn"), ('{"direct_labels":[]}', "max_tokens")])
def test_invalid_response_keeps_original_failure_and_captures_reply_without_retry(provider, text, stop):
    invoke, request, state, sent, events = provider
    state["response"] = Response(text, stop_reason=stop)
    with pytest.raises(runtime.PartsCheckRequestError):
        invoke("marked-view-001", request, lambda raw: raw)
    assert len(sent) == 1
    assert events[0]["raw_usage"]["provider_response"]["content"][0]["text"] == text


def test_a_trace_serialization_failure_does_not_change_the_calculation(provider):
    invoke, request, state, sent, events = provider
    state["response"] = Response('{"direct_labels":[]}', broken_trace=True)
    assert invoke("marked-view-001", request, lambda raw: raw) == {"direct_labels": []}
    assert len(sent) == 1
    assert events[0]["raw_usage"]["diagnostic_error"] == "TypeError"


def test_transport_failure_still_makes_one_attempt_and_publishes_no_false_response(provider):
    invoke, request, state, sent, events = provider
    state["error"] = RuntimeError("fixture transport failure")
    with pytest.raises(runtime.PartsCheckRequestError, match="RuntimeError"):
        invoke("marked-view-001", request, lambda raw: raw)
    assert len(sent) == 1
    assert events == []
