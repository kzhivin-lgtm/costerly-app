"""Grant or update trusted Platform Admin access for one existing user.

Run only from a trusted machine after applying the Platform Admin migration.
The service-role key is required because customer sessions cannot access the
platform_staff table.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config import get_optional_secret
from db.supabase_client import get_supabase_client


def _user_id_for_email(client, email: str) -> str:
    expected = email.strip().lower()
    for page in range(1, 101):
        users = client.auth.admin.list_users(page=page, per_page=1000)
        for user in users:
            if str(user.email or "").strip().lower() == expected:
                return str(user.id)
        if len(users) < 1000:
            break
    raise ValueError(f"No existing auth user found for {email!r}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    identity = parser.add_mutually_exclusive_group(required=True)
    identity.add_argument("--user-id", help="Existing Supabase auth user UUID.")
    identity.add_argument("--email", help="Existing Supabase auth email.")
    parser.add_argument(
        "--role",
        choices=("platform_admin", "platform_viewer"),
        default="platform_admin",
    )
    args = parser.parse_args()

    if not get_optional_secret("SUPABASE_SERVICE_ROLE_KEY"):
        parser.error("SUPABASE_SERVICE_ROLE_KEY is required on this trusted machine.")

    client = get_supabase_client()
    user_id = args.user_id or _user_id_for_email(client, args.email)
    client.table("platform_staff").upsert(
        {
            "user_id": user_id,
            "role": args.role,
            "active": True,
        },
        on_conflict="user_id",
    ).execute()
    print(f"Granted {args.role} to {user_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
