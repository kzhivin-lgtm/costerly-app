"""Saved V7.2 thinking replay and isolated, sequential V7.3.1/2/3 experiments."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import tomllib

from agents import estimation_analyze_v7_2_agent as agent
from agents import estimation_analyze_v7_3_agent as economical
from tools.probe_estimation_analyze_v7 import render_report
from use_cases.estimation_detection_context_v7 import digest


def replay_request(baseline):
    request = deepcopy(baseline["provider_request"])
    if baseline["version"] != agent.VERSION or request.get("thinking") != {"type": "disabled"}:
        raise ValueError("requires a V7.2 thinking-disabled baseline")
    del request["thinking"]
    return request


def incremental_request(baseline, revision):
    """Transform the saved request, not a newly assembled/current prompt."""
    expected = {"V7.3.1": agent.VERSION, "V7.3.2": "Estimation V7.3.1", "V7.3.3": "Estimation V7.3.2"}
    if baseline.get("version") != expected[revision]:
        raise ValueError("incremental experiment requires the preceding version")
    request = deepcopy(baseline["provider_request"])
    if "thinking" in request or (baseline.get("provider_response") or {}).get("stop_reason") != "end_turn":
        raise ValueError("requires a completed provider-default thinking baseline")
    if revision == "V7.3.1":
        return request
    if revision == "V7.3.2":
        marker = "SINGLE AUTHORITATIVE RESPONSE TEMPLATE\n"
        policy, template = request["system"].split(marker)
        lines = template.splitlines()
        indices = [i for i, line in enumerate(lines) if line.lstrip().startswith('"totals":')]
        if len(indices) != 1:
            raise ValueError("expected exactly one Front totals template field")
        index = indices[0]
        if not lines[index - 1].endswith(","):
            raise ValueError("unexpected template formatting")
        lines[index - 1] = lines[index - 1][:-1]
        del lines[index]
        template = "\n".join(lines)
        json.loads(template)  # fail before a call if surgical removal broke JSON
        request["system"] = policy + (
            "CODE-OWNED FRONT TOTALS\nDo not return front.totals. Code computes them from "
            "front_groups without changing counts or annotations. All other output fields "
            "and interpretation rules are unchanged.\n\n") + marker + template
    else:
        old = "Default ordinary panels are LDSP 17 mm; finished worktops 30 mm."
        if request["system"].count(old) != 1:
            raise ValueError("expected one material-default rule")
        request["system"] = request["system"].replace(old, old + (
            " For an unspecified KITCHEN worktop, choose artificial stone as the estimating "
            "material default, not laminated chipboard. Do not assert quartz or a brand; "
            "source-specified material takes priority."))
    return request


def interpret(raw, witness, revision):
    if revision in {"V7.3.2", "V7.3.3"}:
        return economical.validate_result(raw, detection_context=witness["detection_context"], inputs=witness["inputs"])
    return agent.validate_result(raw, detection_context=witness["detection_context"], inputs=witness["inputs"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--revision", choices=["V7.2-thinking", "V7.3.1", "V7.3.2", "V7.3.3"], default="V7.2-thinking")
    args = parser.parse_args()
    if any(p.exists() for p in (args.output, args.output.with_suffix(".raw.txt"), args.output.with_suffix(".html"))):
        parser.error("refuse to overwrite experiment")
    baseline = json.loads(args.baseline.read_text())
    request = replay_request(baseline) if args.revision == "V7.2-thinking" else incremental_request(baseline, args.revision)
    if args.revision == "V7.3.1" and args.execute:
        parser.error("V7.3.1 is display-only; no provider call is needed or permitted")
    witness = {k: deepcopy(baseline[k]) for k in (
        "version", "inputs", "source_pages_base64", "detection_context", "preflight", "input_files")}
    witness.update(database_writes=False, provider_calls=0, calculate_calls=0,
        status="prepared_no_provider_calls", semantic_status="not_reviewed",
        experiment="V7.2 provider-default thinking, not V7.3",
        baseline_path=str(args.baseline), baseline_sha256=sha256(args.baseline.read_bytes()).hexdigest(),
        changed_request_fields=["thinking (explicit disabled removed)"],
        provider_request=request, request_sha256=digest(request),
        prompt_sha256=sha256(request["system"].encode()).hexdigest())
    if args.revision != "V7.2-thinking":
        witness.update(version="Estimation " + args.revision, experiment="Incremental " + args.revision,
            changed_request_fields=[] if args.revision == "V7.3.1" else ["system"],
            island_normalization=economical.island_normalization(witness["detection_context"]),
            derived_fields=["island_normalization"] + (["result.objects[].front.totals"] if args.revision != "V7.3.1" else []))
    def save():
        args.output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
    save()
    if args.revision == "V7.3.1":
        for key in ("provider_response", "raw_response_text", "usage", "stop_reason", "thinking_present"):
            if key in baseline:
                witness[key] = deepcopy(baseline[key])
        witness.update(status="reused_response_display_only", response_origin=str(args.baseline),
            inherited_provider_elapsed_seconds=baseline["elapsed_seconds"], elapsed_seconds=0)
        try:
            raw = agent.existing._json_object(witness["raw_response_text"])
            witness["result"] = interpret(raw, witness, args.revision)
            witness["validation_status"] = "pass"
        except Exception as exc:
            witness.update(validation_status="failed", error=f"{type(exc).__name__}: {exc}")
        save()
        args.output.with_suffix(".raw.txt").write_text(witness["raw_response_text"])
        args.output.with_suffix(".html").write_text(render_report(witness))
        print(json.dumps({k: witness.get(k) for k in ("version", "status", "provider_calls", "validation_status", "error")}))
        return
    if not args.execute:
        print(json.dumps(witness["preflight"]))
        return
    for key, value in tomllib.loads(Path("/Users/qb/costerly-app/.streamlit/secrets.toml").read_text()).items():
        if isinstance(value, (str, int, float)):
            os.environ.setdefault(key, str(value))
    started = time.monotonic()
    try:
        witness["provider_calls"] = 1
        witness["status"] = "provider_request_pending"
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
        result = interpret(result, witness, args.revision)
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
