import base64

from agents.anthropic_adapter import (
    build_detection_content_blocks,
    build_detection_user_text,
)
from agents.detection_page_images import (
    DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES,
    _natural_page_number,
    estimated_inline_pdf_bytes,
    should_use_detection_page_images,
)
from pathlib import Path
from use_cases import rfq_processing


def test_large_pdf_router_uses_estimated_base64_size():
    small_pdf = b"x" * 1_000
    large_pdf = b"x" * ((DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES * 3 // 4) + 1)

    assert estimated_inline_pdf_bytes(small_pdf) < DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES
    assert should_use_detection_page_images(
        file_name="small.pdf", file_bytes=small_pdf
    ) is False
    assert should_use_detection_page_images(
        file_name="large.pdf", file_bytes=large_pdf
    ) is True
    assert should_use_detection_page_images(
        file_name="large.jpg", file_bytes=large_pdf
    ) is False


def test_fallback_renderer_sorts_page_numbers_naturally():
    assert _natural_page_number(Path("page-10.jpg")) == 10
    assert _natural_page_number(Path("page-2.jpg")) == 2


def test_detection_request_combines_jpeg_pages_without_index_anchor():
    text = build_detection_user_text("drawing.pdf", "001", None)
    blocks = build_detection_content_blocks(
        file_name="drawing.pdf",
        file_bytes=b"original-pdf",
        user_text=text,
        page_images=[b"jpeg-one", b"jpeg-two"],
    )

    assert [block["type"] for block in blocks] == [
        "text",
        "image",
        "text",
        "image",
        "text",
    ]
    assert base64.b64decode(blocks[1]["source"]["data"]) == b"jpeg-one"
    assert "COMPACT PACKAGE-LEVEL INDEX EVIDENCE" not in blocks[-1]["text"]
    assert all(block["type"] != "document" for block in blocks)


def test_large_route_skips_mistral_and_uses_sonnet(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        rfq_processing, "should_use_detection_page_images", lambda **_kwargs: True
    )
    monkeypatch.setattr(
        rfq_processing,
        "render_detection_pdf_pages",
        lambda _bytes: ([b"page-1"], {"page_count": 1, "render_seconds": 0.3}),
    )
    monkeypatch.setattr(
        rfq_processing,
        "_run_optional_ocr",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("Mistral must not run")),
    )

    def fake_detection(**kwargs):
        captured.update(kwargs)
        return {
            "rfq_run": {"run_id": "run-001"},
            "detected_objects": [],
            "_agent_usage": {"agent_name": "detection"},
        }

    monkeypatch.setattr(rfq_processing, "run_detection_agent", fake_detection)
    monkeypatch.setattr(rfq_processing, "detection_naming_split_enabled", lambda: False)
    monkeypatch.setattr(rfq_processing, "get_supabase_client", object)
    monkeypatch.setattr(rfq_processing, "upsert_rfq_detection_result", lambda *_args: None)
    monkeypatch.setattr(
        rfq_processing._DIAGNOSTICS_EXECUTOR,
        "submit",
        lambda *_args, **_kwargs: None,
    )

    result = rfq_processing.process_uploaded_rfq(
        file_name="large.pdf", file_bytes=b"pdf", company_id="001"
    )

    assert captured["page_images"] == [b"page-1"]
    assert captured["ocr_package"] is None
    assert captured["model"] == "claude-sonnet-4-6"
    assert result["timings"]["ocr_seconds"] == 0.0
    assert result["timings"]["document_route"] == "jpeg_pages_96dpi_sonnet_4_6"
