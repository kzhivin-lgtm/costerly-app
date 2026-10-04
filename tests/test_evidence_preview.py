from io import BytesIO

from PIL import Image
import pytest

from use_cases.evidence_preview import crop_ocr_region_to_webp
from use_cases.detection_previews import normalize_preview_bbox


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


def test_normalize_preview_bbox_expands_fractional_detection_coordinates():
    assert normalize_preview_bbox(
        {
            "top_left_x": 0.05,
            "top_left_y": 0.08,
            "bottom_right_x": 0.35,
            "bottom_right_y": 0.52,
        },
        {"width": 1009, "height": 714},
    ) == pytest.approx({
        "top_left_x": 50.45,
        "top_left_y": 57.12,
        "bottom_right_x": 353.15,
        "bottom_right_y": 371.28,
    })


def test_normalize_preview_bbox_preserves_ocr_pixel_coordinates():
    assert normalize_preview_bbox(
        {
            "top_left_x": 75,
            "top_left_y": 15,
            "bottom_right_x": 300,
            "bottom_right_y": 410,
        },
        {"width": 1009, "height": 714},
    ) == {
        "top_left_x": 75.0,
        "top_left_y": 15.0,
        "bottom_right_x": 300.0,
        "bottom_right_y": 410.0,
    }
