"""Saved Analyze controls: thinking replay, incremental changes and budget probes."""
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

FRONT_SOFT_STEERING = """REASONING SCOPE FOR THIS REQUEST
Use brief internal reasoning only for ambiguous CB Front decisions: physical
front boundaries, movement type, repeated depictions and distinct tabletop
legs. For Island Map, Understanding and Planner, answer directly from the
supplied evidence and established rules without extended deliberation. Do not
repeat Detection membership proofs or unit inference. Keep the Front check
brief and targeted; do not explore alternative designs. Still complete EVERY
requested section and all its annotations; do not trade completeness for
brevity. The response schema, material defaults and interpretation rules above
are unchanged. Return only the requested JSON, not your reasoning."""

PROMPT_V2_PATH = Path(__file__).resolve().parents[1] / "agents/prompts/estimation_v7_2_reasoning_prompt_v2.md"


def disabled_effort_request(baseline, effort):
    if effort not in {"medium", "high"}:
        raise ValueError("this experiment supports only medium or high")
    if (baseline.get("version") != agent.VERSION
            or (baseline.get("provider_response") or {}).get("stop_reason") != "end_turn"):
        raise ValueError("requires the original completed V7.2 disabled-thinking control")
    request = deepcopy(baseline["provider_request"])
    if (request.get("thinking") != {"type": "disabled"}
            or request.get("output_config") != {"effort": "low"}
            or request.get("max_tokens") != 14000 or request.get("system") != agent.prompt()):
        raise ValueError("requires the original V7.2 disabled/low prompt and settings")
    request["output_config"]["effort"] = effort
    return request


def prompt_v2_request(baseline):
    if (baseline.get("version") != agent.VERSION
            or (baseline.get("provider_response") or {}).get("stop_reason") != "end_turn"):
        raise ValueError("requires the original completed V7.2 Thinking control")
    request = deepcopy(baseline["provider_request"])
    if ("thinking" in request or request.get("output_config") != {"effort": "low"}
            or request.get("max_tokens") != 14000 or request.get("system") != agent.prompt()):
        raise ValueError("requires the unmodified V7.2 prompt and settings")
    request["system"] += "\n\n" + PROMPT_V2_PATH.read_text().strip()
    return request


def front_soft_request(baseline):
    if (baseline.get("version") != agent.VERSION
            or (baseline.get("provider_response") or {}).get("stop_reason") != "end_turn"):
        raise ValueError("requires the original completed V7.2 Thinking control")
    request = deepcopy(baseline["provider_request"])
    if "thinking" in request or request.get("output_config") != {"effort": "low"}:
        raise ValueError("requires unchanged provider-default thinking at low effort")
    request["system"] += "\n\n" + FRONT_SOFT_STEERING
    return request


def hard_cap_request(baseline):
    if (baseline.get("version") != agent.VERSION
            or (baseline.get("provider_response") or {}).get("stop_reason") != "end_turn"):
        raise ValueError("requires the original completed V7.2 Thinking control")
    request = deepcopy(baseline["provider_request"])
    if ("thinking" in request or request.get("output_config") != {"effort": "low"}
            or request.get("max_tokens") != 14000 or request.get("system") != agent.prompt()):
        raise ValueError("requires the unmodified V7.2 prompt and settings")
    request["max_tokens"] = 5000
    return request


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
    parser.add_argument("--revision", choices=["V7.2-thinking", "V7.2-front-soft", "V7.2-prompt-v2", "V7.2-cap5000", "V7.2-disabled-medium", "V7.2-disabled-high", "V7.3.1", "V7.3.2", "V7.3.3"], default="V7.2-thinking")
    args = parser.parse_args()
    if any(p.exists() for p in (args.output, args.output.with_suffix(".raw.txt"), args.output.with_suffix(".html"))):
        parser.error("refuse to overwrite experiment")
    baseline = json.loads(args.baseline.read_text())
    if args.revision == "V7.2-thinking":
        request = replay_request(baseline)
    elif args.revision == "V7.2-front-soft":
        request = front_soft_request(baseline)
    elif args.revision == "V7.2-cap5000":
        request = hard_cap_request(baseline)
    elif args.revision == "V7.2-prompt-v2":
        request = prompt_v2_request(baseline)
    elif args.revision in {"V7.2-disabled-medium", "V7.2-disabled-high"}:
        request = disabled_effort_request(baseline, args.revision.rsplit("-", 1)[1])
    else:
        request = incremental_request(baseline, args.revision)
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
    if args.revision in {"V7.2-disabled-medium", "V7.2-disabled-high"}:
        witness.update(experiment="V7.2 disabled thinking, effort " + request["output_config"]["effort"],
            changed_request_fields=["output_config.effort"], thinking_control="explicitly disabled, not adaptive",
            comparison_criteria=["verify measured thinking tokens are zero and no thinking content blocks",
                "compare complete Analyze quality, latency and output tokens with saved disabled/low control",
                "do not treat fewer fronts or missing blocks as resource efficiency"])
    elif args.revision == "V7.2-prompt-v2":
        witness.update(experiment="V7.2 reasoning prompt V2, owner-approved wording",
            changed_request_fields=["system"], steering_instruction=PROMPT_V2_PATH.read_text().strip(),
            reasoning_control="prompt-only soft guidance; no separate thinking budget or scope enforcement",
            comparison_criteria=["complete all original sections and annotations",
                "compare thinking, total output and latency against original V7.2 Thinking and first soft prompt",
                "compare Front and Blocks to owner benchmarks without interpreting omissions as economy"])
    elif args.revision == "V7.2-cap5000":
        witness.update(experiment="V7.2 hard total-output cap 5000, trial 01",
            changed_request_fields=["max_tokens"], hard_total_output_cap=5000,
            reasoning_control="enforced combined thinking plus answer cap, not a dedicated thinking budget",
            comparison_criteria=["actual total output <=5000",
                "measure latency against saved V7.2 control; faster latency is not guaranteed by the cap",
                "inspect completeness, Front and Blocks; preserve partial responses without repair/retry"])
    elif args.revision == "V7.2-front-soft":
        witness.update(experiment="V7.2 Front-only brief thinking, soft steering trial 01",
            changed_request_fields=["system"], reasoning_control="prompt guidance, not a hard or section-isolated API budget",
            steering_instruction=FRONT_SOFT_STEERING,
            comparison_criteria=["complete all sections without truncation",
                "reduce measured thinking tokens and latency against saved V7.2 control",
                "preserve physical coverage and compare Front/Blocks with owner benchmarks; do not reward omissions"],
            owner_benchmarks=dict(Lev1=dict(drawers=3, legs=2),
                Lev2=dict(hinged_doors=15, drawers=5, lift_up_fronts=2, cabinet_blocks=8)))
    elif args.revision != "V7.2-thinking":
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
