from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace

from PIL import Image
import pytest

import agents.estimation_geometry_verification_agent as agent
from use_cases.estimation_geometry_verification import collect_conflicts, apply_review


def fixture():
    def number(did, value, orientation):
        return {"dimension_id": did, "interpreted_value_mm": value, "evidence_refs": [did + "-ref"],
            "page_number": 1, "view_candidates": ["v"], "line_candidates": [{"orientation": orientation}]}
    scope = {"input_id": "i", "construction_version": "v6", "zones": [{"scope_id": "z", "assembly_role": "countertop"}],
        "evidence_map": {"input_id": "i", "dimensions": [number("depth", 900, "horizontal"), number("width", 600, "vertical")],
            "views": [{"view_id": "v", "page_number": 1}], "pages": [{"page_number": 1, "source_ref": "page"}],
            "view_readings": [{"view_id": "v", "projection": "top_plan", "horizontal_axis": "depth"}]}}
    extraction = {"document_unit": {"unit": "mm"}, "assemblies": [{"assembly_id": "z",
        "dimensions": {"width": {"value": 900, "unit": "mm", "basis": "source", "evidence_refs": ["depth-ref"]}},
        "material_roles": [{"id": "fixed-material"}], "counts": {"drawers": 3}}],
        "view_interpretations": deepcopy(scope["evidence_map"]["view_readings"]),
        "dimension_bindings": [{"assembly_id": "z", "axis": "width", "view_id": "v", "dimension_id": "depth"}]}
    response = {"patches": [{"assembly_id": "z", "axis": "width", "dimension_id": "width", "reason": "Across the depicted top surface."}], "unresolved": []}
    buffer = BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="WEBP")
    return extraction, scope, response, {"page": buffer.getvalue()}


def mock_provider(monkeypatch, response=None, error=None):
    import json
    calls = []
    monkeypatch.setattr(agent, "get_anthropic_client", lambda: SimpleNamespace(with_options=lambda **kw: object()))
    monkeypatch.setattr(agent, "build_agent_usage_event", lambda **kw: {"operation": kw["operation"], "model": kw["model"]})
    def create(_client, **kwargs):
        calls.append(kwargs)
        if error:
            raise error
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=json.dumps(response))])
    monkeypatch.setattr(agent, "_create_message_with_hard_timeout", create)
    return calls


def run(extraction, scope, pages):
    return agent.verify_geometry_once(extraction=extraction, scope=scope, input_row={"input_id": "i", "input_payload": {}}, page_bytes_by_ref=pages)


def test_trigger_and_atomic_patch_preserve_every_non_target_field_and_source_authority():
    extraction, scope, response, _ = fixture()
    before = deepcopy(extraction)
    targets = collect_conflicts(extraction, scope)
    assert targets[0]["reasons"] == ["source_axis_mismatch"]
    assert [c["dimension_id"] for c in targets[0]["candidates"]] == ["width"]
    result, applied, remaining = apply_review(extraction, scope, targets, response)
    assert result["assemblies"][0]["dimensions"]["width"]["value"] == 600
    assert result["assemblies"][0]["dimensions"]["width"]["basis"] == "assumption"
    assert result["dimension_bindings"] == [] and remaining == []
    assert applied[0]["dimension_id"] == "width"
    assert result["assemblies"][0]["material_roles"] == before["assemblies"][0]["material_roles"]
    assert result["assemblies"][0]["counts"] == before["assemblies"][0]["counts"]
    assert extraction == before


@pytest.mark.parametrize("change", ["foreign_target", "wrong_axis_candidate", "numeric_override", "missing_target", "duplicate", "material_change"])
def test_invalid_review_fails_atomically(change):
    extraction, scope, response, _ = fixture()
    before = deepcopy(extraction)
    if change == "foreign_target":
        response["patches"][0]["assembly_id"] = "foreign"
    elif change == "wrong_axis_candidate":
        response["patches"][0]["dimension_id"] = "depth"
    elif change == "numeric_override":
        response["patches"][0]["value_mm"] = 900
    elif change == "missing_target":
        response["patches"] = []
    elif change == "duplicate":
        response["patches"].append(deepcopy(response["patches"][0]))
    else:
        response["materials"] = []
    with pytest.raises(ValueError):
        apply_review(extraction, scope, collect_conflicts(extraction, scope), response)
    assert extraction == before


def test_numeric_contradiction_detected_but_derived_subtraction_is_not():
    extraction, scope, _, _ = fixture()
    extraction["dimension_bindings"] = []
    dim = extraction["assemblies"][0]["dimensions"]["width"]
    dim["evidence_refs"] = ["width-ref"]
    assert collect_conflicts(extraction, scope)[0]["reasons"] == ["source_numeric_mismatch"]
    dim["basis"] = "derived"
    assert collect_conflicts(extraction, scope) == []


def test_no_conflict_zero_requests_and_legacy_is_unchanged(monkeypatch):
    extraction, scope, response, pages = fixture()
    corrected, _, _ = apply_review(extraction, scope, collect_conflicts(extraction, scope), response)
    calls = mock_provider(monkeypatch, response)
    assert run(corrected, scope, pages)["audit"]["status"] == "not_needed"
    assert run(extraction, {}, pages)["extraction"] == extraction
    assert calls == []


def test_one_haiku_call_usage_and_idempotence(monkeypatch):
    extraction, scope, response, pages = fixture()
    calls = mock_provider(monkeypatch, response)
    result = run(extraction, scope, pages)
    assert result["audit"]["status"] == "repaired_as_assumptions"
    assert result["audit"]["attempts"] == 1
    assert result["usage_event"]["model"] == "claude-haiku-4-5-20251001"
    assert run(result["extraction"], scope, pages)["extraction"] == result["extraction"]
    assert len(calls) == 1 and calls[0]["max_tokens"] == 1600
    result["extraction"]["assemblies"][0]["dimensions"]["width"]["value"] = 500
    assert run(result["extraction"], scope, pages)["audit"]["status"] == "needs_review_after_change"
    assert len(calls) == 1


@pytest.mark.parametrize("failure", ["timeout", "malformed", "unresolved"])
def test_failed_or_unresolved_review_retains_prior_estimate_without_retry(monkeypatch, failure):
    extraction, scope, response, pages = fixture()
    if failure == "malformed":
        response = {"bad": True}
    elif failure == "unresolved":
        response = {"patches": [], "unresolved": [{"assembly_id": "z", "axis": "width", "reason": "No reliable boundary."}]}
    calls = mock_provider(monkeypatch, response, error=TimeoutError() if failure == "timeout" else None)
    result = run(extraction, scope, pages)
    assert result["audit"]["status"] == "needs_review"
    assert result["extraction"]["assemblies"] == extraction["assemblies"]
    run(result["extraction"], scope, pages)
    assert len(calls) == 1
    assert bool(result.get("usage_event")) == (failure != "timeout")


@pytest.mark.parametrize("bound", ["targets", "pages", "missing_image", "candidates", "context"])
def test_exceeded_bounds_or_missing_evidence_never_make_a_request(monkeypatch, bound):
    extraction, scope, response, pages = fixture()
    if bound == "targets":
        monkeypatch.setattr(agent, "MAX_TARGETS", 0)
    elif bound == "pages":
        monkeypatch.setattr(agent, "MAX_PAGES", 0)
    elif bound == "candidates":
        monkeypatch.setattr(agent, "MAX_CANDIDATES_PER_TARGET", 0)
    elif bound == "context":
        monkeypatch.setattr(agent, "MAX_CONTEXT_CHARS", 0)
    else:
        pages = {}
    calls = mock_provider(monkeypatch, response)
    result = run(extraction, scope, pages)
    assert result["audit"]["status"] == "needs_review" and result["audit"]["attempts"] == 0
    assert calls == []


def test_foreign_object_evidence_never_enters_review(monkeypatch):
    extraction, scope, response, pages = fixture()
    scope["evidence_map"]["input_id"] = "foreign"
    calls = mock_provider(monkeypatch, response)
    result = run(extraction, scope, pages)
    assert result["audit"]["reason"] == "review_input_scope_mismatch"
    assert calls == [] and result["extraction"]["assemblies"] == extraction["assemblies"]


def test_projection_hypotheses_and_review_never_mutate_authoritative_scope(monkeypatch):
    import json
    extraction, scope, response, pages = fixture()
    scope["zones"][0]["semantic_role"] = "unsupported rectangular leg description"
    scope["object_summary"] = "unsupported first-reader narrative"
    before = deepcopy(scope)
    calls = mock_provider(monkeypatch, response)
    result = run(extraction, scope, pages)
    assert scope == before and result["audit"]["attempts"] == 1
    context = json.loads(calls[0]["messages"][0]["content"][-1]["text"])
    assert "object_summary" not in context
    assert all("description" not in target for target in context["targets"])
    assert "assumptions" in context["view_direction_basis"]
