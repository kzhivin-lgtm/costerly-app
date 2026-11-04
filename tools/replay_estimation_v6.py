"""Read-only database replay of immutable inputs through V6.1.

--execute explicitly enables paid Analyze/Calculation calls. Results are saved
locally only, never published to estimates or production fact tables.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import tomllib

from agents.estimation_composition_analyze_agent import run_estimation_composition_analyze_agent
from agents.estimation_assembly_bom_agent import run_estimation_assembly_bom_agent
from db.repositories import fetch_estimation_object_input
from db.supabase_client import get_supabase_client
from use_cases.estimation_artifacts import download_evidence_artifact
from use_cases.estimation_material_context import build_estimation_material_context
from use_cases.estimation_dimension_graph import build_dimension_graph
from use_cases.estimation_dimension_scale import build_dimension_scale_gate
from use_cases.estimation_composition_scope import validate_composition_scope, apply_composition_scope
from use_cases.estimation_2vn_resolver import resolve_2vn_geometry
from use_cases.estimation_structural_bom import build_structural_assembly_bom
from use_cases.material_engine_adapter import build_material_plan, material_plan_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_ids", nargs="+")
    parser.add_argument("--secrets-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; choose a fresh witness path")
    if args.secrets_file:
        for key, value in tomllib.loads(args.secrets_file.read_text()).items():
            if isinstance(value, (str, int, float)):
                os.environ.setdefault(key, str(value))
    client = get_supabase_client()
    inputs = [fetch_estimation_object_input(client, input_id=i) for i in args.input_ids]
    if any(row is None for row in inputs):
        raise SystemExit("Unknown input")
    if len({row["input_payload"]["run_id"] for row in inputs}) != 1:
        raise SystemExit("Supply objects from one file run only")
    context = build_estimation_material_context(client, inputs[0]["input_payload"]["company_id"])
    page_bytes = {}
    for row in inputs:
        for container in ("evidence", "document_context"):
            for artifact in (row["input_payload"].get(container) or {}).get("artifacts") or []:
                ref = artifact["storage_ref"]
                if ref not in page_bytes:
                    page_bytes[ref] = download_evidence_artifact(client=client, storage_ref=ref)
    print(json.dumps({"objects": len(inputs), "pages": len(page_bytes), "database_writes": False}), flush=True)
    if not args.execute:
        return
    witness = {"version": "v6.1", "input_ids": args.input_ids, "database_writes": False, "objects": [], "usage": []}
    started = time.monotonic()
    try:
        analyze = run_estimation_composition_analyze_agent(inputs=inputs, page_bytes_by_ref=page_bytes, allowed_material_families=context["families"])
        witness["analyze"] = analyze
        witness["usage"].append(analyze["usage_event"])
        print("Analyze complete", flush=True)
        facts = {}
        for row in inputs:
            scope = validate_composition_scope(scope=analyze["scopes_by_input"][row["input_id"]], input_id=row["input_id"])
            graph = build_dimension_graph(input_row=row)
            scale = build_dimension_scale_gate(dimension_graph=graph)
            result = run_estimation_assembly_bom_agent(input_row=row, evidence_page_bytes_by_ref=page_bytes,
                dimension_graph=graph, dimension_scale_gate=scale, allowed_material_families=context["families"], composition_scope=scope)
            witness["usage"].append(result["usage_event"])
            extraction, audit = resolve_2vn_geometry(dimension_graph=graph, extraction=apply_composition_scope(extraction=result["extraction"], scope=scope))
            bom = build_structural_assembly_bom(input_row=row, dimension_graph=graph, extraction=extraction, two_vn=audit,
                dimension_scale_gate=scale, allowed_material_families=context["families"])
            bom["composition_scope"] = scope
            facts[bom["object_id"]] = bom
            witness["objects"].append({"input_id": row["input_id"], "raw_calculation": result["extraction"], "bom": bom})
            print(json.dumps({"calculated": row["input_id"], "assemblies": len(bom["assemblies"]), "parts": len(bom["parts"]), "materials": len(bom["materials"])}), flush=True)
        witness["material_plan"] = material_plan_snapshot(build_material_plan(facts_by_object=facts, catalogs=context["catalogs"]))
        witness["status"] = "computed_not_accepted"
    except Exception as exc:
        witness["status"] = "failed"
        witness["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        witness["elapsed_seconds"] = round(time.monotonic() - started, 2)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(witness, ensure_ascii=False, indent=2, default=str))
        print(json.dumps({"status": witness["status"], "elapsed_seconds": witness["elapsed_seconds"], "witness": str(args.output)}), flush=True)


if __name__ == "__main__":
    main()
