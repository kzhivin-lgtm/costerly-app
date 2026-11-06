"""One Calculate call from saved Front/Planner, no DB or production writes."""
import argparse
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import tomllib

from agents.estimation_assembly_bom_agent import run_estimation_assembly_bom_agent
from agents.estimation_v4_1_material_facts_agent import _json_object
from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_dimension_scale import build_dimension_scale_gate


def load_scope(front_path, planner_path):
    front = json.loads(front_path.read_text())
    planner = json.loads(planner_path.read_text())
    if any(front.get(k) != planner.get(k) for k in ("inputs", "source_pages_base64")):
        raise ValueError("saved Front/Planner evidence differs")
    if len(planner["inputs"]) != 1:
        raise ValueError("exactly one object per Calculate probe")
    front_record = next(r for r in reversed(front["provider_responses"]) if r["stage"] == "front_count")
    plan_record = next(r for r in reversed(planner["provider_responses"]) if r["stage"] == "assembly_plan")
    if plan_record["response"].get("stop_reason") != "end_turn":
        raise ValueError("cannot calculate from incomplete Planner")
    parsed_front = _json_object(front_record["response_text"])
    supplied = json.loads(plan_record["request"]["messages"][0]["content"][-1]["text"])
    if supplied.get("fallible_front_reference") != parsed_front or supplied.get("saved_front_status") != front["status"]:
        raise ValueError("Planner consumed a different Front result/status")
    scope = {"input_id": planner["inputs"][0]["input_id"], "front": parsed_front,
        "planner": _json_object(plan_record["response_text"]),
        "upstream_status": {"front": front["status"], "planner": planner["status"],
            "origin": "saved_separate_probes_not_integrated_Analyze"}}
    return planner, scope


def load_topology(path, *, prior, scope):
    from use_cases.estimation_cb_width_probe import freeze_cb_topology
    data = path.read_bytes()
    saved = json.loads(data)
    if any(saved.get(k) != prior.get(k) for k in ("inputs", "source_pages_base64", "evidence_origin")):
        raise ValueError("topology witness uses different evidence")
    original = saved["scope"]
    if original.get("parts_version") != "CB Parts V3.3" or "diagnostic_omit_block_locator" in original:
        raise ValueError("original unmodified V3.3 witness required")
    if any(original.get(k) != scope.get(k) for k in ("input_id", "front", "planner", "upstream_status")):
        raise ValueError("topology witness uses different Front/Planner scope")
    records = [r for r in saved["provider_responses"] if r["stage"] == "calculation"]
    if len(records) != 1 or records[0]["response"].get("stop_reason") != "end_turn":
        raise ValueError("one complete original calculation response required")
    record = records[0]
    supplied = json.loads(record["request"]["messages"][0]["content"][-1]["text"])
    if supplied != {"calculation_scope": original}:
        raise ValueError("topology request differs from its saved scope")
    raw_text = "\n".join(b["text"] for b in record["response"]["content"] if b["type"] == "text")
    if raw_text != record["response_text"]:
        raise ValueError("topology response text differs from provider raw")
    topology = freeze_cb_topology(_json_object(raw_text), scope=scope)
    return {"frozen_topology": topology,
        "topology_source": {"sha256": sha256(data).hexdigest(), "version": "CB Parts V3.3",
            "status": saved["status"], "geometry_accepted": False}}


def load_v4_scope(front_path):
    """V4 measures before workshop planning, so a saved Planner is not required."""
    front = json.loads(front_path.read_text())
    if len(front["inputs"]) != 1:
        raise ValueError("exactly one object per Calculate probe")
    record = next(r for r in reversed(front["provider_responses"]) if r["stage"] == "front_count")
    if record["response"].get("stop_reason") != "end_turn":
        raise ValueError("cannot use incomplete Front response")
    text = "\n".join(b["text"] for b in record["response"]["content"] if b["type"] == "text")
    if text != record["response_text"]:
        raise ValueError("Front text differs from provider raw")
    return front, {"input_id": front["inputs"][0]["input_id"], "front": _json_object(text),
        "upstream_status": {"front": front["status"], "origin": "saved_front_probe_not_integrated_Analyze",
            "planner": "not_consumed_geometry_precedes_grouping"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--front-witness", type=Path, required=True)
    parser.add_argument("--planner-witness", type=Path, help="Required for V1-V3.5; not consumed by V4")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--omit-block-locator", help="Explicit diagnostic: omit only this block's region from the model context")
    parser.add_argument("--topology-witness", type=Path, help="V3.5 only: freeze topology from an original V3.3 provider reply")
    parser.add_argument("--parts-version", choices=("V1", "V2", "V3", "V3.1", "V3.2", "V3.3", "V3.4", "V3.5", "V4", "V4.1"), default="V3")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute required for one paid Calculate call")
    if args.output.exists():
        parser.error("refuse to overwrite witness")
    if args.parts_version in ("V4", "V4.1"):
        if args.planner_witness:
            parser.error("V4 consumes Front evidence only, omit --planner-witness")
        prior, scope = load_v4_scope(args.front_witness)
    else:
        if not args.planner_witness:
            parser.error("--planner-witness required before V4")
        prior, scope = load_scope(args.front_witness, args.planner_witness)
    if (args.parts_version == "V3.5") != bool(args.topology_witness):
        parser.error("V3.5 requires --topology-witness; other versions do not accept it")
    if args.topology_witness:
        scope.update(load_topology(args.topology_witness, prior=prior, scope=scope))
    scope["parts_version"] = "CB Parts " + args.parts_version
    if args.omit_block_locator:
        scope["diagnostic_omit_block_locator"] = args.omit_block_locator
    witness = {k: prior[k] for k in ("inputs", "source_pages_base64", "evidence_origin")}
    witness.update(work="3.17.4.6", route="cb_parts_inside_calculate", status="running",
        database_writes=False, scope=scope, provider_responses=[],
        source_hashes={str(p): sha256(p.read_bytes()).hexdigest() for p in (args.front_witness, args.planner_witness) if p is not None})
    if args.topology_witness:
        witness["source_hashes"][str(args.topology_witness)] = scope["topology_source"]["sha256"]
    def save():
        args.output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
    started = time.monotonic()
    def record(stage, request, response):
        if response is None:
            witness["provider_request"] = request
            witness["request_sha256"] = sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            save()
            return
        raw = response.model_dump(mode="json")
        witness["provider_responses"].append({"stage": stage, "request": request,
            "prompt_sha256": sha256(request["system"].encode()).hexdigest(),
            "response": raw, "response_text": "\n".join(b["text"] for b in raw["content"] if b["type"] == "text"),
            "elapsed_seconds": round(time.monotonic() - started, 3)})
        save()  # Preserve original provider output before parsing/validation.
    save()
    try:
        for k, v in tomllib.loads(Path("/Users/qb/costerly-app/.streamlit/secrets.toml").read_text()).items():
            if isinstance(v, (str, int, float)):
                os.environ.setdefault(k, str(v))
        row = witness["inputs"][0]
        graph = build_dimension_graph(input_row=row)
        witness["result"] = run_estimation_assembly_bom_agent(input_row=row,
            evidence_page_bytes_by_ref={k: base64.b64decode(v) for k, v in witness["source_pages_base64"].items()},
            dimension_graph=graph, dimension_scale_gate=build_dimension_scale_gate(dimension_graph=graph),
            allowed_material_families=["ldsp", "mdf", "plywood", "solid_wood", "hdf", "glass", "stone", "metal"],
            cb_parts_scope=scope, record=record)
        witness["status"] = witness["result"].get("status", "cb_parts_requires_review")
    except Exception as exc:
        witness.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        witness["elapsed_seconds"] = round(time.monotonic() - started, 3)
        save()
    print(json.dumps({k: witness.get(k) for k in ("status", "elapsed_seconds", "error")}))
    if witness["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
