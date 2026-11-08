"""Run the experimental CB Planner V9 → Block Locator sequence."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from agents.estimation_understanding_agent import planner_front_ids, validate_assembly_plan
from tools.probe_cb_planner_v9_vector import bind_locked_locators, bind_regions, prepare_request, render_overlay
from tools.probe_estimation_v7_4_front_evidence import execute_request
from use_cases.estimation_detection_context_v7 import digest


def load_witness(path, request, source_hash):
    witness = json.loads(path.read_bytes())
    if (witness["provider_request"] != request or witness["request_sha256"] != digest(request)
            or witness["source_request_sha256"] != source_hash or witness["provider_calls"] != 1):
        raise ValueError(f"unexpected stage witness: {path.name}")
    return witness


def usable_plan(witness):
    if witness.get("stop_reason") != "end_turn" or not isinstance(witness.get("model_readings"), dict):
        raise ValueError("CB Planner did not return a complete plan")
    plan = witness["model_readings"]
    if not isinstance(plan.get("blocks"), list) or not plan["blocks"] or not isinstance(plan.get("shared_parts"), list):
        raise ValueError("CB Planner returned no usable assembly inventory")
    rows = plan["blocks"] + plan["shared_parts"]
    if any(not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]
           or not isinstance(row.get("region"), dict)
           or not {"view_id", "bbox_1000"} <= row["region"].keys() for row in rows):
        raise ValueError("CB Planner returned incomplete assembly records")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("CB Planner returned duplicate assembly IDs")
    return plan


def diagnostic_geometry(locator, plan, geometry):
    readings = locator.get("model_readings")
    raw = readings.get("locators") if isinstance(readings, dict) else None
    rows = raw if isinstance(raw, list) else []
    expected = {row["id"] for row in plan["blocks"] + plan["shared_parts"]}
    fields = {"id", "view_id", "geometry_scope", "contour_ids"}
    counts = Counter(row["id"] for row in rows
                     if isinstance(row, dict) and isinstance(row.get("id"), str))
    retained = [row for row in rows if isinstance(row, dict) and set(row) == fields
                and isinstance(row["id"], str) and isinstance(row["view_id"], str)
                and row["id"] in expected and counts[row["id"]] == 1]
    return bind_regions(retained, geometry)


def run_sequence(baseline, archive, document, output_dir, *, execute=False):
    source = baseline.read_bytes()
    seed = json.loads(source)
    planner_request = seed["provider_request"]
    _, geometry, audit_hash = prepare_request(seed, archive, document=document)
    context = json.loads(planner_request["messages"][0]["content"][-1]["text"])
    front_ids = planner_front_ids(context["fallible_front_reference"], set(geometry))
    print(json.dumps({"planner_request_sha256": digest(planner_request),
                      "geometry_sha256": audit_hash, "islands": sorted(geometry),
                      "stages": ["CB Planner", "Block Locator"], "execute": execute}), flush=True)
    if not execute:
        return

    output_dir.mkdir(mode=0o700)
    planner_path = output_dir / "planner.json"
    locator_path = output_dir / "locator.json"
    source_hash = sha256(source).hexdigest()
    print("CB Planner", flush=True)
    execute_request(planner_request, planner_path, source_hash=source_hash,
                    bind=lambda plan: validate_assembly_plan(plan, set(geometry), front_ids))
    planner = load_witness(planner_path, planner_request, source_hash)
    plan = usable_plan(planner)
    plan_hash = digest(plan)
    locator_request, locator_geometry, _ = prepare_request(
        planner, archive, document=document, locked_plan=True)
    if locator_geometry != geometry:
        raise ValueError("source geometry changed between stages")
    planner_witness_hash = sha256(planner_path.read_bytes()).hexdigest()
    print("Block Locator", flush=True)
    execute_request(locator_request, locator_path, source_hash=planner_witness_hash,
                    bind=lambda rows: bind_locked_locators(rows, plan=plan, geometry=geometry, front_ids=front_ids))
    locator = load_witness(locator_path, locator_request, planner_witness_hash)
    if digest(plan) != plan_hash or sha256(planner_path.read_bytes()).hexdigest() != planner_witness_hash:
        raise ValueError("saved plan changed during localization")
    accepted = locator.get("bound_fronts")
    result = accepted or diagnostic_geometry(locator, plan, geometry)
    overlay = output_dir / "overlay.png"
    render_overlay(locator_request, plan, result, geometry, overlay,
                   review_note=None if accepted else "Rejected locator response. Preview shows only its valid saved IDs.")
    summary = {
        "work": "3.17.4.6", "stages": ["CB Planner", "Block Locator"], "provider_calls": 2,
        "locked_plan_sha256": plan_hash, "planner_witness_sha256": planner_witness_hash,
        "planner_request_sha256": planner["request_sha256"], "locator_request_sha256": locator["request_sha256"],
        "geometry_sha256": audit_hash, "block_ids": [row["id"] for row in plan["blocks"]],
        "shared_ids": [row["id"] for row in plan["shared_parts"]],
        "planner_status": planner["status"], "planner_error": planner.get("error"),
        "locator_status": locator["status"], "locator_error": locator.get("error"),
        "geometry_issues": result["geometry_issues"],
        "localized_ids": sorted(accepted["bindings"]) if accepted else [],
        "diagnostic_localized_ids": [] if accepted else sorted(result["bindings"]),
        "overlay": str(overlay),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--document", choices=("lev2", "adda"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    run_sequence(args.baseline, args.archive, args.document, args.output_dir, execute=args.execute)


if __name__ == "__main__":
    main()
