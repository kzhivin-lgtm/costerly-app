import pytest
import copy
import json
from pathlib import Path

from tools.promote_ui_release import require_successful_gate, require_remote_ruleset
from tools.ui_gate_plan import needs_full_gate


def check(**changes):
    return {"id": 1, "name": "UI release gate", "head_sha": "candidate", "app": {"id": 15368},
            "status": "completed", "conclusion": "success", **changes}


@pytest.mark.parametrize("candidate", [
    check(conclusion="failure"), check(conclusion="cancelled"), check(conclusion="skipped"),
    check(status="in_progress", conclusion=None), check(head_sha="previous-commit"),
    check(app={"id": 1}), check(name="Other test"),
])
def test_unverified_candidates_cannot_be_published(candidate):
    with pytest.raises(RuntimeError):
        require_successful_gate([candidate], "candidate")


def test_a_previous_success_cannot_hide_a_later_failed_rerun():
    with pytest.raises(RuntimeError):
        require_successful_gate([check(), check(id=2, conclusion="failure")], "candidate")


def test_only_the_successful_result_for_the_exact_commit_is_accepted():
    assert require_successful_gate([check(head_sha="old"), check(id=2)], "candidate")["id"] == 2


@pytest.mark.parametrize("paths, full", [
    (["notes/DONE_LOG.md", "README.md"], False),
    (["notes/UI_GUIDELINES.md"], True),
    (["app.py", "notes/DONE_LOG.md"], True),
    (["tests/ui/navigation.mjs"], True),
    ([".github/workflows/ui-contract.yml"], True),
    (["uv.lock"], True),
])
def test_docs_skip_is_narrow_and_does_not_bypass_contract_or_runtime_changes(paths, full):
    assert needs_full_gate(paths) is full


def test_remote_gate_cannot_be_disabled_or_bypassed_by_the_publisher():
    ruleset = json.loads(Path(".github/ui-release-ruleset.json").read_text())
    require_remote_ruleset(ruleset)
    for field, value in [("enforcement", "disabled"), ("target", "tag"), ("bypass_actors", [{"actor_type": "User", "actor_id": 1}]), ("rules", [])]:
        broken = copy.deepcopy(ruleset)
        broken[field] = value
        with pytest.raises(RuntimeError):
            require_remote_ruleset(broken)
