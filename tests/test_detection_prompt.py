from agents.anthropic_adapter import (
    DETECTION_NO_NAMING_PROMPT_VERSION,
    DETECTION_PROMPT_VERSION,
)
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_agent_without_naming_prompt,
)


def test_detection_prompt_vnext_locks_object_dossiers_without_naming():
    prompt = load_detection_agent_prompt()

    assert "RFQ DETECTION AGENT VNEXT 3.15.8" in prompt
    assert "four primary jobs" in prompt
    assert "OCR may enrich a locked object but cannot create" in prompt
    assert "Kitchen and large integrated systems" in prompt
    assert "Physical contact alone proves neither merge nor split" in prompt
    assert "coffee machines" in prompt
    assert "floor plan may supply only an external dimension" in prompt
    assert "preview_bbox" in prompt
    assert "text-only Naming Agent" in prompt
    assert "Partner and client may match only when direct commissioning is supported" in prompt
    assert "street and primary building number" in prompt
    assert "Do not shorten a proper project name" in prompt
    assert "detected_materials" not in prompt
    assert "package-wide missing-information" in prompt
    assert "one continuous track or guide" in prompt
    assert DETECTION_PROMPT_VERSION == "detection_vnext_3_15_8_object_dossier_v2"


def test_detection_prompt_vnext_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 16_000
    assert len(prompt.splitlines()) < 220


def test_no_naming_ab_prompt_delegates_user_facing_name_once():
    prompt = load_detection_agent_without_naming_prompt()

    assert DETECTION_NO_NAMING_PROMPT_VERSION == DETECTION_PROMPT_VERSION
    assert "Naming is delegated to a separate text-only Naming Agent" in prompt
    assert "Do not create a user-facing product name" in prompt
