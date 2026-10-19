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

    assert "visual representation map and commercial-object registry in one response" in prompt
    assert "strict causal order" in prompt
    assert "There is no arbitrary page-count cap" in prompt
    assert "Return exactly one `page_coverage` entry for every physical upload page" in prompt
    assert "not a shortlist of pages that appear sufficient for a material calculation" in prompt
    assert "Do not create a group for the cover/title page" in prompt
    assert "generic floor plan, room layout, electrical, plumbing or lighting plan" in prompt
    assert "they are not Estimation Evidence" in prompt
    assert "without self-links, duplicate edges or cycles" in prompt
    assert "Do not assign any object IDs or owners to a group" in prompt
    assert "connected proof component as exactly one commercial object" in prompt
    assert "component_anchor_group_id" in prompt
    assert "proof_parent" in prompt
    assert "new_object_root" in prompt
    assert "attach_to_group" in prompt
    assert "why is there no positive proof" in prompt
    assert "why do these two depictions form one independently quoted product" in prompt
    assert "There is no optional global merge list" in prompt
    assert "`object_detail`" in prompt
    assert "dimensions agree after a change of axes" in prompt
    assert "One exact `dimension_transform` can also prove an attachment on its own" in prompt
    assert "Mandatory dimension comparison before every attachment" in prompt
    assert "confirmed same-scope dimension conflict is a critical no-merge finding" in prompt
    assert "exact positive match exists only as one `dimension_transform` evidence fact" in prompt
    assert "Search every earlier object-specific group" in prompt
    assert "`blocked_merge`" in prompt
    assert "Secondary signals" in prompt
    assert "whole-silhouette similarity is not required" in prompt
    assert "Different finished envelopes, principal functions or primary dimensions" in prompt
    assert "Required proof-parent decision" in prompt
    assert "Test commercial separability, not merely visual closeness" in prompt
    assert "It may support an attachment, never establish one alone" in prompt
    assert "evidence_facts" in prompt
    assert "`floor_plan` means generic non-object context and is discarded" in prompt
    assert "OCR GRAPHIC REGION INVENTORY" in prompt
    assert "source_region_ids" in prompt
    assert "spatial_region_context" in prompt
    assert "including the sidebar, are handed to Estimation" in prompt
    assert DETECTION_VISUAL_REGISTRY_PROMPT_VERSION == (
        "detection_v4_24_ocr_graphic_region_coverage_temperature_0"
    )
