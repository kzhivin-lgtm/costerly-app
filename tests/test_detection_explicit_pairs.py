from copy import deepcopy

import pytest

from agents.anthropic_adapter import (
    normalize_detection_membership_evidence,
    normalize_detection_membership_pair_evidence,
)
from agents.schemas.detection_registry_schema import compile_detection_v637_hypothesis_coverage_components


def fact(a="a", b="b", **extra):
    return {"group_id_a": a, "group_id_b": b, "evidence_type": "matching_topology",
            "strength": "standard", "observation": "Both named Views show the stepped three-bay cabinet.",
            **extra}


def test_separate_pairs_cover_three_views_without_inventing_the_third_pair():
    facts = [normalize_detection_membership_pair_evidence(fact("a", member), hypothesis_group_ids={"a", "b", "c"})[0]
             for member in ("b", "c")]
    components, audit = compile_detection_v637_hypothesis_coverage_components(
        [{"group_ids": ["a", "b", "c"], "hypothesis_reason": "same cabinet", "evidence": facts}], facts,
        visual_groups=[{"group_id": g, "evidence_class": "object_evidence"} for g in ("a", "b", "c")],
        allow_star_hypothesis_components=True)
    assert components == [["a", "b", "c"]]
    assert audit["rejected"] == []
    assert [(x["group_id_a"], x["group_id_b"]) for x in facts] == [("a", "b"), ("a", "c")]


@pytest.mark.parametrize("a,b", [("a", "a"), ("a", ""), ("", ""), ("a", "other-object"),
                                 (["a", "b", "c"], "b")])
def test_pair_requires_two_distinct_members_of_this_hypothesis(a, b):
    result, _ = normalize_detection_membership_pair_evidence(fact(a, b), hypothesis_group_ids={"a", "b"})
    assert result is None


@pytest.mark.parametrize("count", [0, 1, 2, 3, 22])
def test_citation_lists_never_create_pair_endpoints(count):
    row = {"evidence_type": "matching_topology", "source_fact_ids": [f"registry_view:v{i}" for i in range(count)]}
    result, _ = normalize_detection_membership_pair_evidence(row, hypothesis_group_ids={f"v{i}" for i in range(22)})
    assert result is None


def test_extra_view_citations_cannot_change_the_explicit_pair_or_mutate_input():
    row = fact(source_fact_ids=["registry_view:a", "registry_view:b", "registry_view:c", "SF001"])
    before = deepcopy(row)
    result, endpoints = normalize_detection_membership_pair_evidence(row, hypothesis_group_ids={"a", "b", "c"})
    assert endpoints == ["a", "b"]
    assert result["source_fact_ids"] == ["registry_view:a", "registry_view:b", "SF001"]
    assert row == before


def test_third_physical_witness_keeps_its_separate_role():
    witness = {"kind": "third_view_shows_both", "witness_view_id": "c",
               "joined_parts": ["base cabinet", "return shelf"], "connection": "The shelf is fixed to the stepped base."}
    result, endpoints = normalize_detection_membership_pair_evidence(
        fact(evidence_type="direct_shared_structure", structural_witness=witness), hypothesis_group_ids={"a", "b", "c"})
    assert endpoints == ["a", "b"]
    assert result["source_fact_ids"] == ["registry_view:a", "registry_view:b", "registry_view:c"]
    assert result["structural_witness"] == witness


def grouped(*views, **extra):
    row = fact(**extra)
    row.pop("group_id_a")
    row.pop("group_id_b")
    row["source_fact_ids"] = [*(f"registry_view:{v}" for v in views), "SF001"]
    return row


def test_multiway_assertion_preserves_original_and_expands_to_star():
    row = grouped("a", "d", "e", "f")
    before = deepcopy(row)
    facts, audit = normalize_detection_membership_evidence(row, hypothesis_group_ids={"a", "d", "e", "f"})
    assert [(f["group_id_a"], f["group_id_b"]) for f in facts] == [("a", "d"), ("a", "e"), ("a", "f")]
    assert row == before == audit["source_evidence"]
    assert audit["status"] == "expanded"
    assert all(f["observation"] == row["observation"] and "SF001" in f["source_fact_ids"] for f in facts)
    assert len({audit["source_evidence_id"]}) == 1


def test_explicit_pair_keeps_extra_references_in_source_record_without_inventing_edges():
    row = fact(source_fact_ids=["registry_view:a", "registry_view:b", "registry_view:c", "SF001"])
    facts, audit = normalize_detection_membership_evidence(row, hypothesis_group_ids={"a", "b", "c"})
    assert len(facts) == 1
    assert audit["source_evidence"] == row
    assert audit["unresolved_view_references"] == ["c"]
    assert audit["status"] == "paired_with_unresolved_references"


def test_legacy_witness_is_preserved_but_not_added_as_a_member():
    witness = {"kind": "third_view_shows_both", "witness_view_id": "c",
               "joined_parts": ["base", "return"], "connection": "The return is fixed to the stepped base."}
    row = grouped("a", "b", "c", evidence_type="direct_shared_structure", structural_witness=witness)
    facts, audit = normalize_detection_membership_evidence(row, hypothesis_group_ids={"a", "b"})
    assert len(facts) == 1
    assert audit["participants"] == ["a", "b"]
    assert facts[0]["structural_witness"] == witness
    assert "registry_view:c" in facts[0]["source_fact_ids"]
    assert audit["source_evidence"] == row


@pytest.mark.parametrize("row", [
    grouped("a", "b", "other-object"),
    fact(a="a", b="", source_fact_ids=["registry_view:a", "registry_view:b"]),
    "unparsed assertion",
])
def test_unresolved_assertions_are_retained_without_guessing(row):
    facts, audit = normalize_detection_membership_evidence(row, hypothesis_group_ids={"a", "b"})
    assert facts == []
    assert audit["status"] == "unresolved"
    assert audit["source_evidence"] == row
    assert audit["reason"]


def test_many_child_pairs_do_not_manufacture_independent_source_evidence():
    row = grouped("a", "b", "c", "d")
    facts, audit = normalize_detection_membership_evidence(row, hypothesis_group_ids={"a", "b", "c", "d"})
    origins = {(f["group_id_a"], f["group_id_b"], f["evidence_type"], f["observation"]): {audit["source_evidence_id"]}
               for f in facts}
    hypotheses = [{"group_ids": ["a", "b", "c", "d"], "evidence": [row]}]
    groups = [{"group_id": g, "evidence_class": "object_evidence"} for g in ("a", "b", "c", "d")]
    components, coverage = compile_detection_v637_hypothesis_coverage_components(
        hypotheses, facts, visual_groups=groups, evidence_origins=origins)
    assert components == []
    assert coverage["rejected"][0]["reason"] == "membership_hypothesis_requires_multiple_independent_source_facts"
    assert len(facts) == 3
    assert audit["source_evidence"] == row

    corroboration = fact("a", "b", evidence_type="unique_geometry", observation="The same asymmetric stepped corner is visible in both Views.")
    extra, extra_audit = normalize_detection_membership_evidence(corroboration, hypothesis_group_ids={"a", "b", "c", "d"})
    for f in extra:
        origins[(f["group_id_a"], f["group_id_b"], f["evidence_type"], f["observation"])] = {extra_audit["source_evidence_id"]}
    components, coverage = compile_detection_v637_hypothesis_coverage_components(
        hypotheses, [*facts, *extra], visual_groups=groups, evidence_origins=origins)
    assert components == [["a", "b", "c", "d"]]
    assert coverage["rejected"] == []
