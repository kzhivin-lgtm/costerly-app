"""Set the Admin dashboard stage for one existing company."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config import get_optional_secret
from db.supabase_client import get_supabase_client


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--stage", required=True, choices=("test", "pilot", "paid"))
    args = parser.parse_args()

    if not get_optional_secret("SUPABASE_SERVICE_ROLE_KEY"):
        parser.error("SUPABASE_SERVICE_ROLE_KEY is required on this trusted machine.")

    get_supabase_client().table("platform_company_accounts").upsert(
        {
            "company_id": args.company_id,
            "account_stage": args.stage,
        },
        on_conflict="company_id",
    ).execute()
    print(f"Set {args.company_id} to {args.stage}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
