from io import BytesIO

from PIL import Image

from agents.anthropic_adapter import build_detection_registry_content_blocks
from agents.detection_page_images import build_detection_registry_regions


def _page_image() -> bytes:
    output = BytesIO()
    Image.new("RGB", (1000, 1000), color="white").save(output, format="JPEG")
    return output.getvalue()


def test_registry_uses_ocr_visual_region_and_excludes_remote_revision_text():
    page = _page_image()
    ocr_package = {
        "pages": [{
            "page_number": 1,
            "dimensions": {"width": 1000, "height": 1000},
            "images": [{
                "id": "front-elevation",
                "top_left_x": 250,
                "top_left_y": 250,
                "bottom_right_x": 800,
                "bottom_right_y": 750,
            }],
        }],
        "evidence": {
            "text_blocks": [
                {
                    "page_number": 1,
                    "block_type": "caption",
                    "text": "Veneer decorative partition",
                    "bbox": {
                        "top_left_x": 300,
                        "top_left_y": 810,
                        "bottom_right_x": 700,
                        "bottom_right_y": 840,
                    },
                },
                {
                    "page_number": 1,
                    "block_type": "revision",
                    "text": "REVISION TABLE COLUMN HEADING",
                    "bbox": {
                        "top_left_x": 10,
                        "top_left_y": 10,
                        "bottom_right_x": 150,
                        "bottom_right_y": 150,
                    },
                },
            ],
            "literal_items": [{
                "page_number": 1,
                "source_image_id": "front-elevation",
                "source_image_bbox": {
                    "top_left_x": 250,
                    "top_left_y": 250,
                    "bottom_right_x": 800,
                    "bottom_right_y": 750,
                },
                "category": "dimension",
                "text": "345 x 260",
            }],
        },
    }

    regions = build_detection_registry_regions([page], ocr_package=ocr_package)

    assert len(regions) == 1
    region = regions[0]
    assert region["region"] == "ocr_visual_front-elevation"
    assert region["source_image_id"] == "front-elevation"
    assert region["local_ocr_item_count"] == 2
    assert "345 x 260" in region["local_ocr_context"]
    assert "Veneer decorative partition" in region["local_ocr_context"]
    assert "REVISION TABLE" not in region["local_ocr_context"]


def test_registry_keeps_quadrant_fallback_when_ocr_has_no_visual_regions():
    regions = build_detection_registry_regions([_page_image()], ocr_package={"pages": []})

    assert [region["region"] for region in regions] == [
        "upper_left",
        "upper_right",
        "lower",
    ]


def test_registry_places_local_ocr_immediately_after_its_crop():
    region = {
        "page_number": 1,
        "region": "ocr_visual_front-elevation",
        "bytes": _page_image(),
        "local_ocr_context": "LOCAL OCR FOR THE IMMEDIATELY PRECEDING REGION ONLY.\n- dimension '345 x 260'",
    }

    blocks = build_detection_registry_content_blocks(
        file_name="drawing.pdf",
        file_bytes=b"pdf",
        user_text="GLOBAL OCR INDEX",
        page_images=[_page_image()],
        regions=[region],
    )

    local_index = next(
        index
        for index, block in enumerate(blocks)
        if block.get("text", "").startswith("LOCAL OCR FOR")
    )
    assert blocks[local_index - 1]["type"] == "image"
    assert blocks[-1] == {"type": "text", "text": "GLOBAL OCR INDEX"}
