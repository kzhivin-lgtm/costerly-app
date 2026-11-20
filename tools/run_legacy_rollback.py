"""Exact historical rollback gate. Modern contract remains intact for later releases.

Owner explicitly approved the full V1.2.21 rollback on 20 November 2026.
The owner approved one diagnostic-only delta on 20 November 2026.
Its entire runtime file is pinned by SHA256; all other historical code and
runtime dependency pins remain exact. This accepts no arbitrary runtime edits.
Remove approved-rollback.json before restoring or changing runtime behavior.
"""
from __future__ import annotations
import json
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
BASE = "c84ece4c959c75be41271b2221807e3df6579297"
BUILD = "estimation-labor-v1.2.21-b20261120190513-parts-trace-detection-v8.4.29"
DIAGNOSTIC_FILE = "use_cases/estimation_parts_check_runtime.py"
DIAGNOSTIC_SHA256 = "13c6abf6145b7b51c956d9703f8bd71d2a51600999ec06a411f2fe4543d2b109"
GATE_TOOLS = {"tools/configure_ui_gate.py", "tools/promote_ui_release.py",
              "tools/run_ui_contract.py", "tools/ui_gate_plan.py", "tools/run_legacy_rollback.py"}
TESTS = [
    "test_agent_timing.py", "test_company_access.py", "test_parts_diagnostic_trace.py",
    "test_deployment_dependencies.py", "test_estimation_labor_v1.py",
    "test_estimation_parts_check_runtime.py", "test_estimation_runtime.py",
    "test_estimation_object_to_estimate.py", "test_estimation_object_to_estimate_builder.py",
    "test_labor_engine.py", "test_latest_estimate.py", "test_material_engine.py",
    "test_material_engine_adapter.py", "test_navigation_routes.py", "test_object_detail_cache.py",
    "test_object_detail_pricing_policy.py", "test_runtime_observability.py",
    "test_screen_transition_markers.py", "test_wood_cnc_calculation.py",
    "test_workflow_header.py", "test_workflow_routes.py",
]

def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def verify_runtime() -> dict:
    manifest = json.loads((ROOT / ".github/approved-rollback.json").read_text())
    assert manifest["source_commit"] == BASE and manifest["version"] == "V1.2.21", manifest
    assert manifest.get("diagnostic_runtime_sha256") == DIAGNOSTIC_SHA256, "Unapproved diagnostic manifest"
    baseline = set(_git("ls-tree", "-r", "--name-only", BASE).decode().splitlines())
    tracked = set(_git("ls-files").decode().splitlines())
    errors = []
    verified = 0
    for name in sorted(baseline | tracked):
        if name.startswith(("notes/", "tests/", ".github/")) or name in GATE_TOOLS | {"AGENTS.md", ".gitignore", "pyproject.toml", "uv.lock"}:
            continue
        if name == "cloudflare/version.json":
            assert json.loads((ROOT/name).read_text()) == {"build": BUILD}
            continue
        expected = _git("show", BASE+":"+name) if name in baseline else None
        if name == "cloudflare/index.html":
            expected = re.sub(rb'(<meta name="costerly-wrapper-version" content=")[^"]+',
                              lambda m: m[1] + BUILD.encode(), expected)
        if name == "cloudflare/index.html":
            expected = expected.replace(b'estimation-labor-v1.2.21-finished-mirrors-detection-v8.4.29', BUILD.encode())
        if name == "observability/runtime.py":
            expected = expected.replace(b'estimation-labor-v1.2.21-finished-mirrors-detection-v8.4.29', BUILD.encode())
        actual = (ROOT/name).read_bytes() if (ROOT/name).is_file() else None
        if name == DIAGNOSTIC_FILE:
            if actual is None or sha256(actual).hexdigest() != DIAGNOSTIC_SHA256:
                errors.append(name)
        elif expected != actual:
            errors.append(name)
        verified += 1
    # Later dependency changes added only the locked UI test group. Runtime pins must match.
    import tomllib
    old = tomllib.loads(_git("show", BASE+":pyproject.toml").decode())
    new = tomllib.loads((ROOT/"pyproject.toml").read_text())
    assert old["project"] == new["project"], "Runtime dependency contract changed"
    old_lock = tomllib.loads(_git("show", BASE+":uv.lock").decode())
    new_lock = tomllib.loads((ROOT/"uv.lock").read_text())
    normalized = []
    for candidate in new_lock["package"]:
        candidate = dict(candidate)
        if candidate["name"] == old["project"]["name"]:
            candidate.pop("dev-dependencies", None)
            candidate["metadata"] = dict(candidate["metadata"])
            candidate["metadata"].pop("requires-dev", None)
        normalized.append(candidate)
    for package in old_lock["package"]:
        assert package in normalized, "Runtime lock changed: "+package["name"]
    assert not errors, "Runtime differs from approved V1.2.21: "+", ".join(errors)
    return {"source_commit": BASE, "build": BUILD, "runtime_files_verified": verified,
            "exceptions": ["wrapper meta version synchronized", "static version.json added", "UI-test-only dependency group",
                           "owner-approved exact-hash Parts diagnostic log and build marker"]}


def run_rollback_gate(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    report = {"status":"running", "mode":"owner-approved-exact-historical-rollback",
              "commit":_git("rev-parse", "HEAD").decode().strip(), "stages":[]}
    try:
        report["identity"] = verify_runtime()
        print("Verified V1.2.21 runtime, pinned diagnostic delta and dependency pins", flush=True)
        reference = output/"historical-source"
        reference.mkdir(exist_ok=True)
        with tarfile.open(fileobj=BytesIO(_git("archive", BASE))) as archive:
            archive.extractall(reference, filter="data")
        # One pre-existing stale test omitted historical ONNX dependencies and
        # pinned pandas/Pillow to versions not present in the historical lock.
        # Correct only that literal expectation; retain exact pin assertions.
        (reference/"tests/test_deployment_dependencies.py").write_bytes(
            (ROOT/"tests/test_deployment_dependencies.py").read_bytes())
        # Verify the actual candidate runtime, including the pinned diagnostic delta.
        # Keep every original historical assertion intact and add trace regressions.
        for relative in ["cloudflare/index.html", "cloudflare/version.json", "observability/runtime.py", DIAGNOSTIC_FILE,
                         "tests/test_parts_diagnostic_trace.py"]:
            (reference/relative).write_bytes((ROOT/relative).read_bytes())
        command = [sys.executable,"-m","pytest","-q","--tb=short",*["tests/"+name for name in TESTS]]
        log = output/"legacy-regression.log"
        with log.open("w") as stream:
            result = subprocess.run(command,cwd=reference,stdout=stream,stderr=subprocess.STDOUT)
        report["stages"].append({"name":"historical_regression", "exit_code":result.returncode})
        print("\n".join(log.read_text().splitlines()[-35:]),flush=True)
        if result.returncode:
            raise RuntimeError("Historical regression failed")
        log = output/"publication-protection.log"
        with log.open("w") as stream:
            result = subprocess.run([sys.executable,"-m","pytest","-q","--tb=short","tests/test_ui_release_gate.py","tests/test_legacy_diagnostic_gate.py"],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        report["stages"].append({"name":"publication_protection", "exit_code":result.returncode})
        print(log.read_text(),flush=True)
        if result.returncode:
            raise RuntimeError("Publication protection failed")
        report["status"] = "passed"
        return 0
    except Exception as exc:
        report.update(status="failed",error=str(exc))
        print(str(exc),file=sys.stderr)
        return 1
    finally:
        report["total_seconds"] = round(time.perf_counter()-start,3)
        report["limitations"] = "Modern V1.3.3-V3.1 behavior is intentionally rolled back; fresh production Ada acceptance remains pending"
        (output/"gate-report.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"Rollback gate {report['status']}: {report['total_seconds']}s",flush=True)
