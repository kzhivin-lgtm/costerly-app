from agents.anthropic_adapter import (
    DETECTION_NO_NAMING_PROMPT_VERSION,
    DETECTION_PROMPT_VERSION,
)
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_agent_without_naming_prompt,
    load_detection_registry_prompt,
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
    assert "detected_materials" not in prompt
    assert "No external dimensions, dimension candidates, nodes, materials, notes, missing information" in prompt
    assert DETECTION_PROMPT_VERSION == "detection_v4_object_evidence_handoff_v3"


def test_detection_prompt_vnext_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 16_000
    assert len(prompt.splitlines()) < 220


def test_no_naming_ab_prompt_delegates_user_facing_name_once():
    prompt = load_detection_agent_without_naming_prompt()

    assert DETECTION_NO_NAMING_PROMPT_VERSION == DETECTION_PROMPT_VERSION
    assert "Naming later assigns the final short product name" in prompt
    assert "`object_name` only as source-label transport" in prompt


def test_detection_registry_requires_coverage_of_separate_product_groups():
    prompt = load_detection_registry_prompt()

    assert "separate coverage candidate" in prompt
    assert "Map each candidate to exactly one returned object" in prompt
    assert "never merge evidence" in prompt
    assert "vertical shelving unit, a track-supported door system, and a long storage console" in prompt
    assert "First decide whether a drawing group is a complete commercial object or a component" in prompt
    assert "Only after this containment check" in prompt
