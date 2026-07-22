from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from agents.naming_lab import build_locked_naming_input, run_naming_lab_call
from db.repositories import fetch_latest_ocr_result, fetch_rfq_detected_objects
from db.supabase_client import get_supabase_client


def run_lab(run_id: str, *, repeat: int) -> dict:
    client = get_supabase_client()
    objects_df = fetch_rfq_detected_objects(client, run_id)
    ocr_record = fetch_latest_ocr_result(client, run_id)
    if objects_df.empty:
        raise RuntimeError(f"No detected objects found for run_id={run_id}")
    if not ocr_record:
        raise RuntimeError(f"No OCR result found for run_id={run_id}")

    objects = [row.to_dict() for _, row in objects_df.iterrows()]
    locked_input = build_locked_naming_input(objects, ocr_record["ocr_result"])
    calls = [run_naming_lab_call(locked_input) for _ in range(repeat)]
    return {
        "lab_version": "naming_lab_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "locked_object_count": len(locked_input),
        "source_objects": locked_input,
        "calls": calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run isolated naming experiments on a stored RFQ run.")
    parser.add_argument("run_id")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/naming_lab"))
    args = parser.parse_args()
    if args.repeat < 1 or args.repeat > 10:
        raise SystemExit("--repeat must be between 1 and 10")

    report = run_lab(args.run_id, repeat=args.repeat)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output_dir / f"{args.run_id}_{stamp}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output_path),
                "run_id": args.run_id,
                "locked_object_count": report["locked_object_count"],
                "calls": [
                    {
                        "duration_seconds": call["duration_seconds"],
                        "accepted": call["validation"]["accepted"],
                        "violations": call["validation"]["violations"],
                        "preview": call["preview"],
                    }
                    for call in report["calls"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
