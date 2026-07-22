from threading import Event

from agents.ocr_rendering import (
    run_mistral_direct_pdf_evidence_ocr,
    run_mistral_document_evidence_ocr,
)


def test_direct_pdf_mode_uses_one_original_document_request():
    calls = []

    def document_ocr(*, file_name, file_bytes, profile):
        calls.append((file_name, file_bytes, profile))
        return {
            "model": "mistral-ocr-4-0",
            "profile": profile,
            "pages": [{"page_number": 1, "markdown": "PAGE 1"}],
            "processing_seconds": 1.25,
        }

    package = run_mistral_direct_pdf_evidence_ocr(
        file_name="drawing.pdf",
        file_bytes=b"source pdf",
        document_ocr=document_ocr,
    )

    assert calls == [("drawing.pdf", b"source pdf", "evidence")]
    assert package["transport"] == {
        "mode": "direct_pdf",
        "request_count": 1,
        "source_bytes": 10,
    }
    assert package["rendering"]["rendered_page_count"] == 0
    assert package["timings"]["provider_wall_seconds"] == 1.25


def test_pdf_pages_are_ocrd_in_order_and_combined():
    rendered = [b"page one", b"page two"]

    def renderer(file_bytes, *, dpi):
        assert file_bytes == b"source pdf"
        assert dpi == 200
        return rendered

    def page_ocr(*, file_name, file_bytes, profile):
        number = 1 if file_bytes == b"page one" else 2
        return {
            "model": "mistral-ocr-4-0",
            "pages": [
                {
                    "page_number": 1,
                    "source_page_index": 0,
                    "markdown": f"PAGE {number}",
                    "blocks": [{"type": "text", "content": f"PAGE {number}"}],
                    "images": [],
                }
            ],
            "raw_response": {"page": number},
        }

    package = run_mistral_document_evidence_ocr(
        file_name="drawing.pdf",
        file_bytes=b"source pdf",
        renderer=renderer,
        page_ocr=page_ocr,
    )

    assert package["page_count"] == 2
    assert [page["page_number"] for page in package["pages"]] == [1, 2]
    assert package["rendering"]["dpi"] == 200
    assert package["evidence"]["text_blocks"][1]["text"] == "PAGE 2"
    assert set(package["timings"]) == {
        "render_seconds",
        "warmup_wait_seconds",
        "provider_wall_seconds",
        "pipeline_seconds",
        "pipeline_overlap_seconds",
        "assembly_seconds",
        "unattributed_seconds",
    }
    assert package["rendering"]["pipeline_enabled"] is False
    assert package["transport"]["mode"] == "rendered_pages"
    assert package["transport"]["request_count"] == 2
    assert package["processing_seconds"] >= package["timings"]["pipeline_seconds"]


def test_pipeline_starts_ocr_before_all_pages_finish_rendering():
    first_ocr_started = Event()
    events: list[str] = []

    def page_streamer(file_bytes, *, dpi, render_workers):
        assert file_bytes == b"source pdf"
        assert dpi == 200
        assert render_workers == 4
        events.append("render-1")
        yield 0, b"page one"
        assert first_ocr_started.wait(timeout=1)
        events.append("render-2")
        yield 1, b"page two"

    def page_ocr(*, file_name, file_bytes, profile):
        if file_bytes == b"page one":
            events.append("ocr-1")
            first_ocr_started.set()
        return {
            "model": "mistral-ocr-4-0",
            "pages": [
                {
                    "page_number": 1,
                    "source_page_index": 0,
                    "markdown": file_name,
                    "blocks": [],
                    "images": [],
                }
            ],
            "raw_response": {},
        }

    package = run_mistral_document_evidence_ocr(
        file_name="drawing.pdf",
        file_bytes=b"source pdf",
        page_streamer=page_streamer,
        page_ocr=page_ocr,
    )

    assert events.index("ocr-1") < events.index("render-2")
    assert package["rendering"]["pipeline_enabled"] is True
    assert [page["page_number"] for page in package["pages"]] == [1, 2]
