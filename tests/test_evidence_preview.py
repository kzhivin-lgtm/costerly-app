from io import BytesIO

from PIL import Image
import pytest

from use_cases.evidence_preview import crop_ocr_region_to_webp


def _page() -> bytes:
    image = Image.new("RGB", (1000, 500), "white")
    result = BytesIO()
    image.save(result, format="JPEG")
    return result.getvalue()


def test_crop_uses_ocr_page_dimensions_not_assumed_render_dimensions():
    preview = crop_ocr_region_to_webp(
        page_image=_page(),
        page_dimensions={"width": 2000, "height": 1000},
        bbox={"top_left_x": 400, "top_left_y": 200, "bottom_right_x": 800, "bottom_right_y": 600},
        padding_ratio=0,
    )

    with Image.open(BytesIO(preview)) as image:
        assert image.format == "WEBP"
        assert image.size == (200, 200)


def test_crop_rejects_bbox_outside_ocr_page():
    with pytest.raises(ValueError, match="inside"):
        crop_ocr_region_to_webp(
            page_image=_page(),
            page_dimensions={"width": 1000, "height": 500},
            bbox={"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 1001, "bottom_right_y": 10},
        )


def test_crop_converts_normalized_vision_bbox_to_ocr_page_pixels():
    preview = crop_ocr_region_to_webp(
        page_image=_page(),
        page_dimensions={"width": 1000, "height": 500},
        bbox={"top_left_x": 0.1, "top_left_y": 0.2, "bottom_right_x": 0.9, "bottom_right_y": 0.8},
        padding_ratio=0,
    )

    with Image.open(BytesIO(preview)) as image:
        assert image.size == (800, 300)
