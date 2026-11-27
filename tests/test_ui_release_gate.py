import pytest
import copy
import json
from pathlib import Path
from types import SimpleNamespace

from tools.promote_ui_release import require_successful_gate, require_remote_ruleset, github_token
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
    hidden = copy.deepcopy(ruleset)
    del hidden["bypass_actors"]
    with pytest.raises(RuntimeError, match="visibility"):
        require_remote_ruleset(hidden)


def test_normal_git_identity_can_verify_policy_without_an_admin_token(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("tools.promote_ui_release.subprocess.run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="username=fixture\npassword=fixture-credential\n"))
    github_token.cache_clear()
    try:
        assert github_token() == "fixture-credential"
    finally:
        github_token.cache_clear()


def test_ui_logs_are_retained_even_when_the_suite_fails():
    import yaml
    workflow = yaml.load(Path(".github/workflows/ui-contract.yml").read_text(), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["ui-release-gate"]["steps"]
    upload = next(step for step in steps if step.get("uses", "").startswith("actions/upload-artifact@"))
    assert upload["if"].startswith("always()")
    assert upload["with"]["include-hidden-files"] == "true"
    assert upload["with"]["if-no-files-found"] == "error"
def test_labor_fixture_wrapper_does_not_capture_a_previous_script_namespace():
    import ast
    from pathlib import Path
    from types import SimpleNamespace

    tree=ast.parse(Path('tests/ui/app_fixture.py').read_text())
    first=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign)
               and any(isinstance(target,ast.Name) and target.id=='_original_labor_loader' for target in node.targets))
    last=next(i for i,node in enumerate(tree.body[first:],first)
              if isinstance(node,ast.FunctionDef) and node.name=='fixture_labor_loader')
    fixture=compile(ast.Module(body=tree.body[first:last+1],type_ignores=[]),'fixture-labor-hook','exec')
    calls=[]
    def production(*args,**kwargs):
        calls.append((args,kwargs))
        return {'status':'ready'}
    labor=SimpleNamespace(load_object_labor=production)
    old={'labor':labor,'scenario':lambda:{}}
    exec(fixture,old)
    labor.load_object_labor=old['fixture_labor_loader']
    current={'labor':labor,'scenario':lambda:{}}
    exec(fixture,current)
    old.clear()  # Streamlit can release the preceding script's globals.
    assert current['fixture_labor_loader']('fixture-client',identity=('c','r','e','o'))=={'status':'ready'}
    assert calls==[(('fixture-client',),{'identity':('c','r','e','o')})]
