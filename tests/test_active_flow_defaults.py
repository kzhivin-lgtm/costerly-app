from __future__ import annotations

from agents import anthropic_adapter, ocr_rendering


def test_naming_split_is_active_by_default(monkeypatch) -> None:
    monkeypatch.setattr(anthropic_adapter.sys, "argv", ["app.py"])
    monkeypatch.setattr(
        anthropic_adapter,
        "get_secret",
        lambda name, default=None: default,
    )

    assert anthropic_adapter.detection_naming_split_enabled() is True


def test_naming_split_supports_explicit_rollback(monkeypatch) -> None:
    monkeypatch.setattr(anthropic_adapter.sys, "argv", ["app.py"])
    monkeypatch.setattr(
        anthropic_adapter,
        "get_secret",
        lambda name, default=None: "false",
    )

    assert anthropic_adapter.detection_naming_split_enabled() is False


def test_direct_pdf_ocr_is_active_by_default(monkeypatch) -> None:
    monkeypatch.setattr(ocr_rendering.sys, "argv", ["app.py"])
    monkeypatch.delenv("MISTRAL_DIRECT_PDF_EXPERIMENT", raising=False)

    assert ocr_rendering.direct_pdf_ocr_enabled() is True


def test_direct_pdf_ocr_supports_explicit_rollback(monkeypatch) -> None:
    monkeypatch.setattr(ocr_rendering.sys, "argv", ["app.py"])
    monkeypatch.setenv("MISTRAL_DIRECT_PDF_EXPERIMENT", "false")

    assert ocr_rendering.direct_pdf_ocr_enabled() is False
