from pathlib import Path
import json
import subprocess

import pytest

from tools import run_legacy_rollback as gate


@pytest.fixture
def pinned_candidate(tmp_path, monkeypatch):
    root = Path(gate.ROOT)
    names = ["app.py", "cloudflare/index.html", "cloudflare/version.json",
             "observability/runtime.py", gate.DIAGNOSTIC_FILE]
    baseline = {name: subprocess.check_output(["git", "show", gate.BASE + ":" + name], cwd=root)
                for name in names if name != "cloudflare/version.json"}
    # version.json is the approved wrapper identity addition to the old source.
    for name in names + ["pyproject.toml", "uv.lock", ".github/approved-rollback.json"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(["git", "show",
            "7d631d354506df02b9fffe5830ab3fc463d79f58:" + name], cwd=root))
    for name in ["pyproject.toml", "uv.lock"]:
        baseline[name] = subprocess.check_output(["git", "show", gate.BASE + ":" + name], cwd=root)

    def git(*args):
        if args[0] == "ls-tree":
            return "\n".join(name for name in names if name != "cloudflare/version.json").encode()
        if args[0] == "ls-files":
            return "\n".join(names).encode()
        if args[0] == "show":
            return baseline[args[1].split(":", 1)[1]]
        raise AssertionError(args)

    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "_git", git)
    return tmp_path


def test_exact_approved_trace_and_build_are_accepted(pinned_candidate):
    report = gate.verify_runtime()
    assert report["source_commit"] == gate.BASE
    assert report["build"] == gate.BUILD


@pytest.mark.parametrize("name", ["app.py", "observability/runtime.py", "use_cases/estimation_parts_check_runtime.py"])
def test_any_unapproved_runtime_change_is_rejected(pinned_candidate, name):
    path = pinned_candidate / name
    path.write_bytes(path.read_bytes() + b"\n# unapproved change\n")
    with pytest.raises(AssertionError, match="Runtime differs"):
        gate.verify_runtime()


def test_manifest_cannot_authorize_a_different_diagnostic_hash(pinned_candidate):
    path = pinned_candidate / ".github/approved-rollback.json"
    manifest = json.loads(path.read_text())
    manifest["diagnostic_runtime_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(AssertionError, match="Unapproved diagnostic manifest"):
        gate.verify_runtime()


def test_different_wrapper_identity_is_rejected(pinned_candidate):
    (pinned_candidate / "cloudflare/version.json").write_text('{"build":"unapproved"}')
    with pytest.raises(AssertionError):
        gate.verify_runtime()
