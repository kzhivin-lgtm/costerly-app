"""Inspect or deliberately replay one immutable Estimation V4 input.

The default mode is read-only and prints the bounded page plan.  `--execute`
is explicit because it calls the paid extraction provider and persists a new
versioned fact result.  Neither mode re-runs OCR or uploads the original file.
"""

from __future__ import annotations

import argparse
import json

from agents.estimation_v4_1_material_facts_agent import build_v4_1_evidence_batches
from db.repositories import fetch_estimation_object_input
from db.supabase_client import get_supabase_client
from use_cases.estimation_v4_1_material_facts import replay_estimation_v4_1_material_facts_input


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_id", help="immutable rfq_estimation_object_inputs.input_id")
    parser.add_argument("--execute", action="store_true", help="call Cloud extraction and persist V4.1 facts")
    args = parser.parse_args()
    client = get_supabase_client()
    row = fetch_estimation_object_input(client, input_id=args.input_id)
    if row is None:
        raise SystemExit("Estimation input was not found")
    payload = row.get("input_payload") or {}
    batches = build_v4_1_evidence_batches(payload)
    plan = {
        "input_id": args.input_id,
        "object_id": (payload.get("object") or {}).get("object_id"),
        "batch_count": len(batches),
        "batches": [{
            "batch_id": batch["batch_id"], "topic": batch["topic"],
            "page_numbers": [page["page_number"] for page in batch["pages"]],
            "ocr_block_count": sum(len(page["ocr_blocks"]) for page in batch["pages"]),
        } for batch in batches],
    }
    if not args.execute:
        print(json.dumps({"mode": "read_only_plan", **plan}, ensure_ascii=False))
        return
    result = replay_estimation_v4_1_material_facts_input(client=client, input_id=args.input_id)
    print(json.dumps({"mode": "executed", **plan, **result}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
