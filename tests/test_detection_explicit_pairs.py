from copy import deepcopy

import pytest

from agents.anthropic_adapter import normalize_detection_membership_pair_evidence
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
