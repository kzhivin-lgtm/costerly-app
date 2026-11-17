"""Promote only an exact commit with a successful GitHub Actions UI release gate."""
from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
from urllib.request import Request, urlopen

import certifi

CHECK_NAME = "UI release gate"
REPOSITORY = "kzhivin-lgtm/costerly-app"
GITHUB_ACTIONS_APP_ID = 15368


def github_json(path: str) -> dict | list:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"https://api.github.com/repos/{REPOSITORY}/" + path, headers=headers)
    with urlopen(request, timeout=20, context=ssl.create_default_context(cafile=certifi.where())) as response:
        return json.load(response)


def require_remote_ruleset(ruleset: dict) -> None:
    checks = [rule for rule in ruleset.get("rules", []) if rule.get("type") == "required_status_checks"]
    types = {rule.get("type") for rule in ruleset.get("rules", [])}
    if not (ruleset.get("target") == "branch" and ruleset.get("enforcement") == "active" and ruleset.get("bypass_actors") == []
            and {"non_fast_forward", "deletion"}.issubset(types)
            and "refs/heads/main" in ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
            and not ruleset.get("conditions", {}).get("ref_name", {}).get("exclude")):
        raise RuntimeError("The remote main gate is absent, bypassable or inactive; publication blocked")
    if not any(rule["parameters"].get("strict_required_status_checks_policy") is True
               and rule["parameters"].get("do_not_enforce_on_create") is False and any(
        check.get("context") == CHECK_NAME and check.get("integration_id") == GITHUB_ACTIONS_APP_ID
        for check in rule["parameters"].get("required_status_checks", [])
    ) for rule in checks):
        raise RuntimeError("The remote ruleset does not require the trusted UI gate; publication blocked")


def require_successful_gate(checks: list[dict], sha: str) -> dict:
    expected = [check for check in checks if check.get("name") == CHECK_NAME
                and check.get("app", {}).get("id") == GITHUB_ACTIONS_APP_ID
                and check.get("head_sha") == sha]
    if not expected:
        raise RuntimeError(f"No trusted {CHECK_NAME} check exists for {sha}")
    latest = max(expected, key=lambda check: check["id"])
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise RuntimeError(f"{CHECK_NAME} is {latest.get('status')}/{latest.get('conclusion')}; publication blocked")
    return latest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha")
    parser.add_argument("--publish", action="store_true", help="Push the verified SHA to main")
    args = parser.parse_args()
    sha = subprocess.check_output(["git", "rev-parse", "--verify", args.sha + "^{commit}"], text=True).strip()
    check = require_successful_gate(github_json(f"commits/{sha}/check-runs?per_page=100")["check_runs"], sha)
    print(f"Verified {CHECK_NAME}: {check['html_url']}")
    if args.publish:
        remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        if remote not in {f"https://github.com/{REPOSITORY}.git", f"git@github.com:{REPOSITORY}.git"}:
            raise RuntimeError("Origin is not the expected publication repository")
        rulesets = github_json("rulesets")
        candidates = [row for row in rulesets if row["name"] == CHECK_NAME]
        if len(candidates) != 1:
            raise RuntimeError("One active remote UI release ruleset is required before publishing")
        require_remote_ruleset(github_json(f"rulesets/{candidates[0]['id']}"))
        subprocess.run(["git", "push", "origin", f"{sha}:refs/heads/main"], check=True)
    else:
        print("Check only; main was not changed")


if __name__ == "__main__":
    main()
