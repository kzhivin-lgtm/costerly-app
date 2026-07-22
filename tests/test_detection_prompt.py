from agents.anthropic_adapter import DETECTION_PROMPT_VERSION
from agents.prompt_loader import (
    load_detection_agent_prompt,
    load_detection_agent_without_naming_prompt,
)


def test_detection_prompt_v3_2_6_covers_ocr_identity_reconciliation():
    prompt = load_detection_agent_prompt()

    assert "RFQ DETECTION AGENT V3.2.6" in prompt
    assert "Stage A — establish visual object candidates" in prompt
    assert "Stage B — lock identities and enrich from OCR" in prompt
    assert "unanchored OCR never creates an object" in prompt
    assert "reconcile authoritative product-level tags from OCR once" in prompt
    assert "This targeted reconciliation is not a second page-by-page review" in prompt
    assert "Do not retranscribe text OCR already provides" in prompt
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
    assert "ЛП-1, ЛС-1, ЛС-2, and МП-1 remain separate quote lines" in prompt
    assert "Component, BOM, hardware, and detail codes are not object identities" in prompt
    assert "does not establish parent-child containment" in prompt
    assert "Build one package-level candidate set" in prompt
    assert "Living room furniture assembly" in prompt
    assert 'use "W 3610 × H 630 × D 610 mm"' in prompt
    assert DETECTION_PROMPT_VERSION == "detection_v3_2_6_ocr_identity_reconciliation"


def test_detection_prompt_v3_stays_compact():
    prompt = load_detection_agent_prompt()

    assert len(prompt) < 24_000
    assert len(prompt.splitlines()) < 500


def test_no_naming_ab_prompt_delegates_user_facing_name_once():
    prompt = load_detection_agent_without_naming_prompt()

    assert "Your output has five user-facing jobs" in prompt
    assert "## 5. Object naming" not in prompt
    assert "Do not create, translate, shorten, improve, or validate" in prompt
    assert "otherwise use Object 1, Object 2" in prompt
    assert "Naming is performed once by a separate downstream Naming Agent" in prompt
