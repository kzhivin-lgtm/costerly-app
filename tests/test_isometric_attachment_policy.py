from copy import deepcopy
from unittest.mock import Mock

import pytest

from agents.anthropic_adapter import (
    normalize_detection_v711_presentation_render_decisions,
    build_detection_presentation_render_edges,
    attach_detection_v711_presentation_render_components,
    review_detection_unattached_renders_on_same_sheet,
    _v8411_discovery_technical_counts,
)
from agents.schemas.detection_registry_schema import (
    partition_detection_presentation_render_components, project_attachment_only_hypotheses,
)


def group(identifier, kind):
    return {"group_id": identifier, "page_number": 1,
            "evidence_class": "object_evidence", "representation_kind": kind}


def decision(identifier, target="", disposition="attach"):
    return {"render_group_id": identifier, "technical_group_id": target,
            "disposition": disposition,
            "evidence_type": "matching_topology" if disposition == "attach" else "none",
            "visual_witness": "The same stepped corner joins the drawer base and vertical panel in both Views."}


def test_isometric_attaches_without_changing_its_original_class():
    groups = [group("iso", "isometric_technical"), group("front", "orthographic_elevation")]
    before = deepcopy(groups)
    facts, audit = normalize_detection_v711_presentation_render_decisions(
        [decision("iso", "front")], visual_groups=groups, group_id_mapping={})
    edges = build_detection_presentation_render_edges(facts, {"iso": 1, "front": 1})
    components = attach_detection_v711_presentation_render_components([["front"]], edges)
    retained, excluded, _ = partition_detection_presentation_render_components(components, visual_groups=groups)
    assert retained == [["front", "iso"]]
    assert excluded == []
    assert groups == before
    assert audit[0]["technical_group_id"] == "front"


@pytest.mark.parametrize("disposition", ["no_match", "unresolved"])
def test_unmatched_isometric_cannot_create_an_object_or_trigger_an_extra_call(disposition):
    groups = [group("iso", "isometric_technical"), group("front", "orthographic_elevation")]
    facts, audit = normalize_detection_v711_presentation_render_decisions(
        [decision("iso", disposition=disposition)], visual_groups=groups, group_id_mapping={})
    assert facts == []
    retained, excluded, component_audit = partition_detection_presentation_render_components(
        [["front"], ["iso"]], visual_groups=groups)
    assert retained == [["front"]]
    assert excluded == ["iso"]
    assert component_audit[0]["disposition"] == "excluded_unattached_isometric_technical"
    stream = Mock(side_effect=AssertionError("No extra model call is allowed for an isometric"))
    recovered, _ = review_detection_unattached_renders_on_same_sheet(
        primary_decisions=audit, visual_groups=groups, group_id_mapping={"iso": "iso", "front": "front"},
        view_crops=[], page_context_images=[], model="fixture", stream_message=stream)
    assert recovered == []
    stream.assert_not_called()


def test_isometric_cannot_attach_to_another_attachment_only_view():
    groups = [group("a", "isometric_technical"), group("b", "isometric_technical")]
    with pytest.raises(ValueError, match="attachment is invalid"):
        normalize_detection_v711_presentation_render_decisions(
            [decision("a", "b"), decision("b", disposition="no_match")],
            visual_groups=groups, group_id_mapping={})
    retained, excluded, _ = partition_detection_presentation_render_components([["a", "b"]], visual_groups=groups)
    assert retained == []
    assert excluded == ["a", "b"]


def test_two_objects_keep_their_own_isometrics_and_ambiguous_double_attachment_is_rejected():
    groups = [group("a", "orthographic_elevation"), group("b", "orthographic_plan"),
              group("ia", "isometric_technical"), group("ib", "isometric_technical")]
    decisions = [decision("ia", "a"), decision("ib", "b")]
    facts, _ = normalize_detection_v711_presentation_render_decisions(
        decisions, visual_groups=groups, group_id_mapping={})
    components = attach_detection_v711_presentation_render_components(
        [["a"], ["b"]], build_detection_presentation_render_edges(facts, {x["group_id"]: 1 for x in groups}))
    assert components == [["a", "ia"], ["b", "ib"]]
    with pytest.raises(ValueError):
        normalize_detection_v711_presentation_render_decisions(
            [*decisions, decision("ia", "b")], visual_groups=groups, group_id_mapping={})


def test_discovery_still_counts_the_isometric_as_a_technical_island():
    groups = [group("iso", "isometric_technical")]
    assert _v8411_discovery_technical_counts({"visual_groups": groups, "classifications": []}) == {1: 1}


def test_real_render_attachment_behavior_is_preserved():
    groups = [group("photo", "presentation_render"), group("front", "orthographic_elevation")]
    facts, _ = normalize_detection_v711_presentation_render_decisions(
        [decision("photo", "front")], visual_groups=groups, group_id_mapping={})
    assert facts[0]["group_id_a"] == "photo"
    retained, excluded, audit = partition_detection_presentation_render_components([["photo"]], visual_groups=groups)
    assert retained == [] and excluded == ["photo"]
    assert audit[0]["disposition"] == "excluded_unattached_presentation_render"


def test_attachment_members_and_their_proof_cannot_bridge_technical_groups():
    hypotheses = [{"group_ids": ["front", "side", "iso"], "hypothesis_reason": "same cabinet",
                   "evidence": [
                       {"source_fact_ids": ["registry_view:front", "registry_view:side"]},
                       {"source_fact_ids": ["registry_view:iso", "registry_view:front", "registry_view:side"]},
                   ]},
                  {"group_ids": ["other", "iso"], "evidence": []}]
    before = deepcopy(hypotheses)
    projected, audit = project_attachment_only_hypotheses(hypotheses, {"iso"})
    assert len(projected) == 1
    assert projected[0]["group_ids"] == ["front", "side"]
    assert projected[0]["evidence"] == [{"source_fact_ids": ["registry_view:front", "registry_view:side"]}]
    assert len(audit) == 2
    assert hypotheses == before


def test_isometric_explicit_endpoint_cannot_bridge_technical_hypotheses():
    projected, _ = project_attachment_only_hypotheses(
        [{"group_ids": ["a", "b", "iso"], "evidence": [
            {"group_id_a": "a", "group_id_b": "b"},
            {"group_id_a": "a", "group_id_b": "iso"},
        ]}], {"iso"})
    assert projected[0]["group_ids"] == ["a", "b"]
    assert projected[0]["evidence"] == [{"group_id_a": "a", "group_id_b": "b"}]
