from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from agents.prompt_loader import load_detection_agent_prompt


def test_detection_prompt_v3_covers_core_commercial_object_contract():
    prompt = load_detection_agent_prompt()

    assert "RFQ DETECTION AGENT V3.0" in prompt
    assert "quote-line test" in prompt
    assert "one Curtain system" in prompt
    assert "Object naming" in prompt
    assert "Quantity" in prompt
    assert "External dimensions" in prompt
    assert "Notes and clarification questions" in prompt
    assert "Estimation Agent handoff boundary" in prompt
    assert "independent-product test" in prompt
    assert "Living room furniture assembly" in prompt
    assert 'use "W 3610 × H 630 × D 610 mm"' in prompt
    assert DETECTION_PROMPT_VERSION == "detection_v3_candidate_2"


def test_detection_prompt_v3_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 24_000
    assert len(prompt.splitlines()) < 500
