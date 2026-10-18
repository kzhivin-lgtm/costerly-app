import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from agents.anthropic_adapter import (
    build_detection_content_blocks,
    build_detection_user_text,
)
from agents.detection_page_images import (
    DEFAULT_INLINE_PDF_REQUEST_MAX_BYTES,
    _build_content_aware_drawing_regions,
    _natural_page_number,
    build_detection_registry_regions,
    estimated_inline_pdf_bytes,
    should_use_detection_page_images,
)
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
        "text", "image", "text", "image", "text",
    ]
    assert base64.b64decode(blocks[1]["source"]["data"]) == b"jpeg-one"
    assert "COMPACT PACKAGE-LEVEL INDEX EVIDENCE" not in blocks[-1]["text"]
    assert all(block["type"] != "document" for block in blocks)


def test_large_route_skips_mistral_and_keeps_haiku_default(monkeypatch):
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
    assert captured["model"] is None
    assert result["timings"]["ocr_seconds"] == 0.0
    assert result["timings"]["document_route"] == "jpeg_pages_96dpi_haiku_4_5"


def test_first_file_review_reuses_normalized_detection_payload():
    data = rfq_processing.build_file_review_data(
        {
            "rfq_run": {
                "run_id": "run-001",
                "project_name": "Cafe",
                "design_partner": "Studio",
                "client": "Owner",
                "file_quality_label": "detailed_drawings",
                "status": "completed",
            },
            "detected_objects": [{
                "object_id": "object-001",
                "object_name": "Counter",
                "quantity": 2,
                "review_required": False,
            }],
        },
        timings={"detection_seconds": 12.5, "total_seconds": 14.0},
    )

    assert data["run"]["run_id"] == "run-001"
    assert data["run"]["partner"] == "Studio"
    assert data["objects"] == [{
        "object_id": "object-001",
        "name": "Counter",
        "quantity": "2",
        "review_required": False,
    }]
    assert data["timings"]["detection_seconds"] == 12.5


def test_processing_uses_only_bounded_browser_handshake_after_complete_marker():
    source = Path("screens/processing.py").read_text()
    complete_tail = source.split(
        'render_stage(1.0, complete=True, processing_phase="complete")', 1
    )[1]

    assert "time.sleep(0.25)" not in complete_tail
    assert "time.sleep(0.12)" in complete_tail


def _jpeg_with_left_title_and_three_islands() -> bytes:
    image = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 1380), outline="black", width=4)
    for index, y in enumerate(range(50, 1320, 24)):
        x = 35 + (index * 17) % 145
        draw.rectangle((x, y, x + 24, y + 21), fill="black")
    draw.rectangle((400, 100, 880, 260), outline="black", width=4)
    draw.rectangle((380, 560, 860, 600), outline="black", width=4)
    draw.rectangle((350, 900, 900, 1220), outline="black", width=4)
    output = BytesIO()
    image.save(output, format="JPEG", quality=90)
    return output.getvalue()


def test_content_aware_regions_add_drawing_field_and_three_islands():
    regions = _build_content_aware_drawing_regions(
        _jpeg_with_left_title_and_three_islands(), page_number=11, max_regions=4
    )

    assert [region["region"] for region in regions] == [
        "drawing_field", "drawing_island_1", "drawing_island_2", "drawing_island_3",
    ]
    assert {region["page_number"] for region in regions} == {11}
    assert all(region["bytes"] for region in regions)


def test_content_aware_regions_do_not_trigger_without_one_title_strip():
    image = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(image)
    for y in (100, 560, 900):
        draw.rectangle((300, y, 850, y + 120), outline="black", width=4)
    output = BytesIO()
    image.save(output, format="JPEG", quality=90)

    assert _build_content_aware_drawing_regions(
        output.getvalue(), page_number=1, max_regions=4
    ) == []


def test_content_aware_regions_are_added_without_displacing_standard_regions():
    page = _jpeg_with_left_title_and_three_islands()
    regions = build_detection_registry_regions([page], max_images=8)

    assert [region["region"] for region in regions[:3]] == [
        "upper_left", "upper_right", "lower"
    ]
    assert [region["region"] for region in regions[3:]] == [
        "drawing_field", "drawing_island_1", "drawing_island_2", "drawing_island_3",
    ]
