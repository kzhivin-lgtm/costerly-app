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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--front-witness", type=Path, required=True)
    parser.add_argument("--planner-witness", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--parts-version", choices=("V1", "V2", "V3"), default="V3")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute required for one paid Calculate call")
    if args.output.exists():
        parser.error("refuse to overwrite witness")
    prior, scope = load_scope(args.front_witness, args.planner_witness)
    scope["parts_version"] = "CB Parts " + args.parts_version
    witness = {k: prior[k] for k in ("inputs", "source_pages_base64", "evidence_origin")}
    witness.update(work="3.17.4.6", route="cb_parts_inside_calculate", status="running",
        database_writes=False, scope=scope, provider_responses=[],
        source_hashes={str(p): sha256(p.read_bytes()).hexdigest() for p in (args.front_witness, args.planner_witness)})
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
