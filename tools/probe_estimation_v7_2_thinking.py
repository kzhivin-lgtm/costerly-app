"""Replay one saved V7.2 request with only its explicit thinking disable removed."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import tomllib

from agents import estimation_analyze_v7_2_agent as agent
from tools.probe_estimation_analyze_v7 import render_report
from use_cases.estimation_detection_context_v7 import digest


def replay_request(baseline):
    request = deepcopy(baseline["provider_request"])
    if baseline["version"] != agent.VERSION or request.get("thinking") != {"type": "disabled"}:
        raise ValueError("requires a V7.2 thinking-disabled baseline")
    del request["thinking"]
    return request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if any(p.exists() for p in (args.output, args.output.with_suffix(".raw.txt"), args.output.with_suffix(".html"))):
        parser.error("refuse to overwrite experiment")
    baseline = json.loads(args.baseline.read_text())
    request = replay_request(baseline)
    witness = {k: deepcopy(baseline[k]) for k in (
        "version", "inputs", "source_pages_base64", "detection_context", "preflight", "input_files")}
    witness.update(database_writes=False, provider_calls=0, calculate_calls=0,
        status="prepared_no_provider_calls", semantic_status="not_reviewed",
        experiment="V7.2 provider-default thinking, not V7.3",
        baseline_path=str(args.baseline), baseline_sha256=sha256(args.baseline.read_bytes()).hexdigest(),
        changed_request_fields=["thinking (explicit disabled removed)"],
        provider_request=request, request_sha256=digest(request),
        prompt_sha256=sha256(request["system"].encode()).hexdigest())
    def save():
        args.output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
    save()
    if not args.execute:
        print(json.dumps(witness["preflight"]))
        return
    for key, value in tomllib.loads(Path("/Users/qb/costerly-app/.streamlit/secrets.toml").read_text()).items():
        if isinstance(value, (str, int, float)):
            os.environ.setdefault(key, str(value))
    started = time.monotonic()
    try:
        witness["provider_calls"] = 1
        save()
        response = agent.existing._create_message_with_hard_timeout(
            agent.existing.get_anthropic_client().with_options(timeout=120, max_retries=0),
            timeout_seconds=120, **request)
        raw = response.model_dump(mode="json")
        text = "\n".join(b["text"] for b in raw["content"] if b["type"] == "text")
        witness.update(provider_response=raw, raw_response_text=text, usage=raw.get("usage"),
            stop_reason=raw.get("stop_reason"),
            thinking_present=any(b["type"] == "thinking" for b in raw["content"]))
        args.output.with_suffix(".raw.txt").write_text(text)
        save()
        if response.stop_reason != "end_turn":
            raise ValueError("incomplete provider response")
        result = agent.existing._json_object(text)
        agent.validate_result(result, detection_context=witness["detection_context"], inputs=witness["inputs"])
        witness.update(result=result, status="analyze_requires_semantic_review")
    except Exception as exc:
        witness.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        witness["elapsed_seconds"] = round(time.monotonic() - started, 3)
        save()
        args.output.with_suffix(".html").write_text(render_report(witness))
    print(json.dumps({k: witness.get(k) for k in (
        "status", "error", "elapsed_seconds", "usage", "stop_reason", "thinking_present")}))


if __name__ == "__main__":
    main()
