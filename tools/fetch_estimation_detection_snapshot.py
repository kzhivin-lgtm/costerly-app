"""Read saved Detection/OCR events for immutable replay inputs. No DB writes."""
import argparse
import json
import os
from pathlib import Path
import tomllib

from db.supabase_client import get_supabase_client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("refuse to overwrite snapshot")
    rows = [r for path in args.input for r in json.loads(path.read_text())["inputs"]]
    companies = {str(r["input_payload"]["company_id"]) for r in rows}
    if len(companies) != 1:
        parser.error("exactly one company required")
    runs = sorted({r["input_payload"]["run_id"] for r in rows})
    ocr_ids = sorted({r["input_payload"]["document"]["ocr_event_id"] for r in rows})
    for key,value in tomllib.loads(Path("/Users/qb/costerly-app/.streamlit/secrets.toml").read_text()).items():
        if isinstance(value,(str,int,float)):
            os.environ.setdefault(key,str(value))
    client = get_supabase_client()
    company = next(iter(companies))
    detections = client.table("agent_usage_events").select("id,run_id,company_id,raw_usage,created_at,prompt_version").eq("company_id",company).in_("run_id",runs).eq("agent_name","detection").order("created_at",desc=True).limit(20).execute().data
    ocr = client.table("agent_usage_events").select("id,run_id,company_id,raw_usage,created_at,prompt_version").eq("company_id",company).in_("id",ocr_ids).execute().data
    if {e["id"] for e in ocr} != set(ocr_ids):
        raise ValueError("missing saved OCR event")
    if {e["run_id"] for e in detections} != set(runs):
        raise ValueError("missing saved Detection run")
    args.output.write_text(json.dumps(dict(run_ids=runs,company_id=company,events=detections+ocr,
        database_writes=False),ensure_ascii=False,indent=2))
    for event in detections:
        audit=event.get("raw_usage") or {}
        print(json.dumps(dict(event_id=event["id"],run_id=event["run_id"],
            island_count=len(audit.get("view_evidence_packages") or []),
            hypotheses=len(((audit.get("semantic_ledger_audit") or {}).get("object_hypotheses") or {}).get("accepted") or []),
            audit_keys=[k for k in audit if any(s in k for s in ("decision_audit","semantic_ledger","coordinate_frame","registry"))]),ensure_ascii=False))


if __name__ == "__main__":
    main()
