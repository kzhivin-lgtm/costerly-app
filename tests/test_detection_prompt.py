from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from agents.prompt_loader import load_detection_agent_prompt


def test_detection_prompt_v3_2_4_covers_metadata_roles_contract():
    prompt = load_detection_agent_prompt()

    assert "RFQ DETECTION AGENT V3.2.4" in prompt
    assert "Stage A — lock the commercial object set visually" in prompt
    assert "Stage B — enrich the locked objects from OCR" in prompt
    assert "must not create, split, merge, or increase the object set" in prompt
    assert "Do not spend effort retranscribing text" in prompt
    assert "Detection alone makes all semantic decisions" in prompt
    assert "six user-facing jobs" in prompt
    assert "### Metadata — project name" in prompt
    assert "file name alone only as weak evidence" in prompt
    assert "Береговой проезд, 5" in prompt
    assert "Omit city, apartment, корпус, строение" in prompt
    assert "### Metadata — partner, client, and author" in prompt
    assert "design_partner is the supported intermediary" in prompt
    assert "client is the end customer" in prompt
    assert 'use "unknown" for design_partner' in prompt
    assert "Do not copy one visible name into both fields" in prompt
    assert "Do not use the upload date" in prompt
    assert "quote-line test" in prompt
    assert "one Curtain system" in prompt
    assert "Object naming" in prompt
    assert "Quantity" in prompt
    assert "External dimensions" in prompt
    assert "Notes and clarification questions" in prompt
    assert "They never imply mains power" in prompt
    assert "Estimation Agent handoff boundary" in prompt
    assert "independent-product test" in prompt
    assert "Living room furniture assembly" in prompt
    assert 'use "W 3610 × H 630 × D 610 mm"' in prompt
    assert DETECTION_PROMPT_VERSION == "detection_v3_2_4_metadata_no_cache_baseline"


def test_detection_prompt_v3_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 24_000
    assert len(prompt.splitlines()) < 500
