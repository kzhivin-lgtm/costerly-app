from agents.ocr_rendering import run_mistral_document_evidence_ocr


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
        "assembly_seconds",
        "unattributed_seconds",
    }
    assert package["processing_seconds"] >= sum(package["timings"].values()) - 0.004
