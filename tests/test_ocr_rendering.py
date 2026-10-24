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

    assert calls == [("drawing.pdf", b"source pdf", "basic")]
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


def test_pdf_ocr_merges_native_pdf_text_with_mistral_evidence():
    def renderer(file_bytes, *, dpi):
        return [b"page one"]

    def page_ocr(*, file_name, file_bytes, profile):
        return {
            "model": "mistral-ocr-4-1",
            "pages": [{"page_number": 1, "blocks": [], "images": []}],
            "raw_response": {},
        }

    package = run_mistral_document_evidence_ocr(
        file_name="drawing.pdf",
        file_bytes=b"source pdf",
        renderer=renderer,
        page_ocr=page_ocr,
        native_text_extractor=lambda file_bytes, *, dpi: [{
            "page_number": 1,
            "text": "358",
            "bbox": {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 30, "bottom_right_y": 40},
        }],
        native_graphic_extractor=lambda file_bytes, *, dpi: [{
            "graphic_id": "NPIG-P001-X10-I001-R001",
            "page_number": 1,
            "bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            "source_bbox_points": {"top_left_x": 1.0, "top_left_y": 2.0, "bottom_right_x": 30.0, "bottom_right_y": 40.0},
            "source_page_width_points": 100.0,
            "source_page_height_points": 100.0,
            "image_width": 100,
            "image_height": 100,
        }],
    )

    assert package["native_pdf_text"]["status"] == "succeeded"
    assert package["native_pdf_text"]["span_count"] == 1
    assert package["native_pdf_text"]["extraction_seconds"] >= 0
    assert package["native_pdf_text"]["error"] is None
    assert package["native_pdf_graphics"]["status"] == "succeeded"
    assert package["native_pdf_graphics"]["region_count"] == 1
    assert package["native_pdf_graphics"]["error"] is None
    assert package["native_pdf_graphics"]["extraction_seconds"] >= 0
    assert package["native_pdf_graphics"]["embedding_preload"] == {
        "status": "not_candidate"
    }
    assert package["evidence"]["text_blocks"] == [{
        "page_number": 1,
        "block_type": "native_pdf_text",
        "source": "native_pdf_text",
        "text": "358",
        "bbox": {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 30, "bottom_right_y": 40},
    }]
    assert package["evidence"]["graphic_regions"] == [{
        "graphic_id": "NPIG-P001-X10-I001-R001",
        "page_number": 1,
        "source": "native_pdf_image_xobject",
        "bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
        "source_page_width_points": 100.0,
        "source_page_height_points": 100.0,
        "source_bbox_points": {"top_left_x": 1.0, "top_left_y": 2.0, "bottom_right_x": 30.0, "bottom_right_y": 40.0},
        "image_width": 100,
        "image_height": 100,
    }]


def test_native_graphic_embedding_preload_is_scheduled_during_ocr_pipeline():
    def renderer(_file_bytes, *, dpi):
        assert dpi == 200
        return [b"page one"]

    def page_ocr(*, file_name, file_bytes, profile):
        return {
            "model": "mistral-ocr-4-1",
            "pages": [{"page_number": 1, "blocks": [], "images": []}],
            "raw_response": {},
        }

    scheduled: list[list[str]] = []
    package = run_mistral_document_evidence_ocr(
        file_name="drawing.pdf",
        file_bytes=b"source pdf",
        renderer=renderer,
        page_ocr=page_ocr,
        native_text_extractor=lambda _file_bytes, *, dpi: [],
        native_graphic_extractor=lambda _file_bytes, *, dpi: [
            {
                "graphic_id": "NPIG-P001-X10-I001-R001", "page_number": 1,
                "bbox": {"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40},
            },
            {
                "graphic_id": "NPIG-P001-X11-I002-R001", "page_number": 1,
                "bbox": {"top_left_x": 31, "top_left_y": 2, "bottom_right_x": 60, "bottom_right_y": 40},
            },
        ],
        native_embedding_preloader=lambda regions: (
            scheduled.append([region["graphic_id"] for region in regions]) or {"status": "scheduled"}
        ),
    )

    assert scheduled == [["NPIG-P001-X10-I001-R001", "NPIG-P001-X11-I002-R001"]]
    assert package["native_pdf_graphics"]["embedding_preload"] == {"status": "scheduled"}


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
