"""Review or install the approved, additive GitHub ruleset (admin access required)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import ssl
import sys
from urllib.request import Request, urlopen

import certifi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.promote_ui_release import CHECK_NAME, REPOSITORY, github_json, require_remote_ruleset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create the approved ruleset; requires a dedicated admin token")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    template = json.loads((Path(__file__).resolve().parents[1] / ".github/ui-release-ruleset.json").read_text())
    require_remote_ruleset(template)
    if args.verify:
        rows = [row for row in github_json("rulesets") if row["name"] == CHECK_NAME]
        if len(rows) != 1:
            raise RuntimeError("Exactly one UI release gate ruleset must be installed")
        require_remote_ruleset(github_json(f"rulesets/{rows[0]['id']}"))
        print("Remote UI release gate is active, with no bypass actors")
    elif args.apply:
        token = os.getenv("GITHUB_ADMIN_TOKEN")
        if not token:
            raise RuntimeError("Set a dedicated GITHUB_ADMIN_TOKEN with repository Administration: write; do not broaden the app's runtime token")
        if any(row["name"] == CHECK_NAME for row in github_json("rulesets")):
            raise RuntimeError("A UI release gate ruleset already exists; inspect it instead of overwriting")
        request = Request(f"https://api.github.com/repos/{REPOSITORY}/rulesets", data=json.dumps(template).encode(), method="POST", headers={
            "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28",
        })
        with urlopen(request, timeout=20, context=ssl.create_default_context(cafile=certifi.where())) as response:
            installed = json.load(response)
        require_remote_ruleset(installed)
        print(f"Installed UI release gate ruleset {installed['id']}")
    else:
        print(json.dumps(template, indent=2))


if __name__ == "__main__":
    main()
