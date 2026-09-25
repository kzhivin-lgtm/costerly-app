"""Generate exactly one one-use company registration link.

Run from a trusted machine after the company-access SQL migration is applied.
The service-role key is read server-side; only a token hash is stored in DB.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config import get_optional_secret
from db.supabase_client import get_supabase_client
from use_cases.invite_links import create_one_company_link
from use_cases.invite_links import DEFAULT_PUBLIC_APP_URL, public_app_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Public Costerly AI URL; never the Supabase URL.")
    parser.add_argument("--label", help="Optional private tracking label for this one link.")
    args = parser.parse_args()

    base_url = public_app_url(
        args.base_url or get_optional_secret("COSTERLY_PUBLIC_URL") or DEFAULT_PUBLIC_APP_URL
    )
    if not get_optional_secret("SUPABASE_SERVICE_ROLE_KEY"):
        parser.error("SUPABASE_SERVICE_ROLE_KEY is required on this trusted machine.")

    url = create_one_company_link(get_supabase_client(), base_url, args.label)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
