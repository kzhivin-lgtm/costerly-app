from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from agents.prompt_loader import load_detection_agent_prompt


def test_detection_prompt_v3_3_covers_verified_compact_contract():
    prompt = load_detection_agent_prompt()

    assert "RFQ DETECTION AGENT V3.3" in prompt
    assert "Stage A — lock the commercial object set visually" in prompt
    assert "Stage B — enrich the locked objects from OCR" in prompt
    assert "Stage C — verify every returned object" in prompt
    assert "must not create, split, merge, or increase the object set" in prompt
    assert "Do not spend effort retranscribing text" in prompt
    assert "Detection alone makes all semantic decisions" in prompt
    assert "Do not return 0 for an axis when an explicit overall value is visible" in prompt
    assert "never imply an electrical connection requirement" in prompt
    assert "Keep detected_materials under 240 characters" in prompt
    assert "keep the whole field under 280 characters" in prompt
    assert "six user-facing jobs" in prompt
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
    assert DETECTION_PROMPT_VERSION == "detection_v3_3_verified_compact_candidate"


def test_detection_prompt_v3_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 24_000
    assert len(prompt.splitlines()) < 500
