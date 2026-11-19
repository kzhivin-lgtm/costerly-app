"""Run the saved UI contract locally or in CI and retain timing/failure evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
UNIT_TESTS = [
    "tests/test_company_profile_preload.py", "tests/test_company_access.py",
    "tests/test_navigation_routes.py", "tests/test_workflow_header.py",
    "tests/test_runtime_observability.py", "tests/test_ui_release_gate.py",
    "tests/test_presentation_previews.py",
    "tests/test_object_cost_hierarchy.py",
    "tests/test_isometric_attachment_policy.py",
    "tests/test_detection_explicit_pairs.py",
    "tests/test_agent_timing.py::test_v848_ada_compares_every_same_sheet_pair_independently_of_grouping",
    "tests/test_agent_timing.py::test_isometric_membership_uses_primary_attachment_without_extra_requests",
    "tests/test_agent_timing.py::test_presentation_render_without_technical_match_never_creates_registry_object",
]
BROWSER_SUITES = ["navigation.mjs", "calculation.mjs", "profile_save.mjs", "profile_recovery.mjs", "screen_recovery.mjs", "version_refresh.mjs", "auth_resume.mjs", "auth_reconnect.mjs"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-only", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / ".ui-artifacts")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    state = output / "state"
    if state.exists():
        shutil.rmtree(state)
    state.mkdir()
    env = dict(os.environ, COSTERLY_UI_STATE_DIR=str(state), COSTERLY_UI_REPORT_DIR=str(output / "browser"))
    env.setdefault("PYTHONPATH", str(ROOT))
    started = time.perf_counter()
    report = {
        "status": "running",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)),
        "stages": [],
    }
    server = None
    server_log = None

    def run(label: str, command: list[str]) -> None:
        before = time.perf_counter()
        log = output / (label + ".log")
        print(f"Starting {label}", flush=True)
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        elapsed = round(time.perf_counter() - before, 3)
        report["stages"].append({"name": label, "seconds": elapsed, "exit_code": result.returncode})
        print(f"{label}: {elapsed:.3f}s, exit {result.returncode}", flush=True)
        if result.returncode:
            print("\n".join(log.read_text().splitlines()[-45:]), flush=True)
            raise RuntimeError(f"{label} failed; publication is not allowed")

    try:
        if not args.browser_only:
            run("unit", [sys.executable, "-m", "pytest", "-q", "--tb=short", *UNIT_TESTS])
        for suite in BROWSER_SUITES:
            before = time.perf_counter()
            # Independent processes keep intentional failure/caching scenarios
            # from inheriting data cached by an earlier browser suite.
            suite_state = state / Path(suite).stem
            suite_state.mkdir()
            env["COSTERLY_UI_STATE_DIR"] = str(suite_state)
            if suite == "auth_reconnect.mjs":
                # This scenario owns two real server processes, preserving
                # one open browser form across their restart.
                run(Path(suite).stem, ["node", str(ROOT / "tests/ui" / suite)])
                continue
            server_log = (output / (Path(suite).stem + "-server.log")).open("w")
            server = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(ROOT / "tests/ui" / ("auth_resume_fixture.py" if suite == "auth_resume.mjs" else "app_fixture.py")),
                "--global.developmentMode", "false", "--server.headless", "true",
                "--server.address", "127.0.0.1", "--server.port", "8789",
                "--browser.gatherUsageStats", "false",
            ], cwd=ROOT, env=env, stdout=server_log, stderr=subprocess.STDOUT)
            while True:
                if server.poll() is not None:
                    raise RuntimeError("UI test server exited during startup")
                try:
                    with urlopen("http://127.0.0.1:8789/_stcore/health", timeout=1) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    pass
                if time.perf_counter() - before > 25:
                    raise RuntimeError("UI test server did not become ready")
                time.sleep(0.1)
            report["stages"].append({"name": Path(suite).stem + "_server_start", "seconds": round(time.perf_counter() - before, 3), "exit_code": 0})
            run(Path(suite).stem, ["node", str(ROOT / "tests/ui" / suite)])
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # This isolated test process owns no production work. Python
                # executors can outlive Streamlit's graceful server shutdown.
                server.kill()
                server.wait()
                report["stages"].append({"name": Path(suite).stem + "_cleanup", "forced": True})
            server = None
            server_log.close()
            server_log = None
        report["status"] = "passed"
        return 0
    except Exception as exc:
        report.update(status="failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        if server_log is not None:
            server_log.close()
        report["total_seconds"] = round(time.perf_counter() - started, 3)
        (output / "gate-report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"UI gate {report['status']}: {report['total_seconds']:.3f}s", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
