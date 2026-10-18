from agents.anthropic_adapter import (
    DETECTION_NO_NAMING_PROMPT_VERSION,
    DETECTION_PROMPT_VERSION,
    DETECTION_VISUAL_REGISTRY_PROMPT_VERSION,
)
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_agent_without_naming_prompt,
    load_detection_registry_prompt,
    load_detection_visual_map_prompt,
    load_detection_visual_registry_prompt,
)


def test_detection_v4_prompt_delegates_naming_and_normalizes_project_identity():
    prompt = load_detection_agent_prompt()

    assert "DETECTION V4 - OBJECT REGISTRY AND EVIDENCE PACKAGING" in prompt
    assert "Naming later assigns the final short product name" in prompt
    assert "presentation_preview_bbox" in prompt
    assert "Return it in English" in prompt
    assert "meaningful uploaded file name" in prompt
    assert "Any number in an example is illustrative only" in prompt
    assert "Beregovoy Proezd 5" in prompt
    assert "Partner and client may be identical only when the source supports self-designed direct commissioning" in prompt
    assert "`file_quality_level` to exactly one integer" in prompt
    assert "`0` / `unreadable`" in prompt
    assert "detected_materials" not in prompt
    assert "No external dimensions, dimension candidates, nodes, materials, notes, missing information" in prompt
    assert DETECTION_PROMPT_VERSION == "detection_v4_object_evidence_handoff_v6"


def test_detection_prompt_vnext_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 16_000
    assert len(prompt.splitlines()) < 220


def test_no_naming_ab_prompt_delegates_user_facing_name_once():
    prompt = load_detection_agent_without_naming_prompt()

    assert DETECTION_NO_NAMING_PROMPT_VERSION == DETECTION_PROMPT_VERSION
    assert "Naming later assigns the final short product name" in prompt
    assert "`object_name` only as source-label transport" in prompt


def test_detection_registry_groups_visual_map_without_treating_it_as_object_set():
    prompt = load_detection_registry_prompt()

    assert "visual map was prepared from full pages and enlarged regions" in prompt
    assert "not an object set" in prompt
    assert "Decide commercial objects only from the full pages" in prompt
    assert "attach relevant `visual_group_ids`" in prompt
    assert "not a reason to add, split or fail an object" in prompt
    assert "vertical shelving unit, a track-supported door system, and a long storage console" in prompt
    assert "Different complete envelopes, functions, silhouettes, or construction systems" in prompt


def test_detection_visual_map_never_decides_objects_or_quantity():
    prompt = load_detection_visual_map_prompt()

    assert "not a commercial-object registry" in prompt
    assert "Do not decide whether any depiction is an independent product" in prompt
    assert "Do not infer quantity" in prompt
    assert "cannot create, split, merge, name, count" in prompt


def test_integrated_visual_registry_keeps_visual_representations_and_commercial_objects_distinct():
    prompt = load_detection_visual_registry_prompt()

    assert "visual representation map and the locked commercial-object registry in one response" in prompt
    assert "Keep these two levels separate" in prompt
    assert "There is no arbitrary page-count cap" in prompt
    assert "For every physical upload page, return exactly one `page_coverage` entry" in prompt
    assert "not a shortlist of pages that appear sufficient for a material calculation" in prompt
    assert "shared schedule, title block, layout or multi-object context" in prompt
    assert "groups that prove this object's commercial boundary" in prompt
    assert "exactly one `commercial_role`" in prompt
    assert "A `component_detail` never becomes a commercial object" in prompt
    assert "A `document_context` never becomes an object" in prompt
    assert "resolve identity across all `assembly_view` groups" in prompt
    assert "Dimensions that agree after a change of axes" in prompt
    assert "Secondary supporting signals only" in prompt
    assert "whole-silhouette similarity is not required" in prompt
    assert "vertical shelving unit, a track-supported door system and a long storage console" in prompt
    assert "BOUNDARY REVIEW MODE" in prompt
    assert "Never leave an `assembly_view` without an owner" in prompt
    assert DETECTION_VISUAL_REGISTRY_PROMPT_VERSION == (
        "detection_v4_visual_registry_boundary_review_v3_temperature_0"
    )
