from agents.anthropic_adapter import build_detection_user_text
from agents.detection_spatial_inventory import build_detection_spatial_inventory


def _ocr_with_graphic_region() -> dict:
    return {"pages": [{"page_number": 1, "blocks": [
        {
            "type": "image", "content": "graphical drawing",
            "top_left_x": 300, "top_left_y": 100,
            "bottom_right_x": 900, "bottom_right_y": 800,
        },
        {
            "type": "text", "content": "sidebar note",
            "top_left_x": 0, "top_left_y": 0,
            "bottom_right_x": 200, "bottom_right_y": 900,
        },
    ]}]}


def test_passive_inventory_keeps_only_provider_graphic_regions():
    assert build_detection_spatial_inventory(_ocr_with_graphic_region()) == [{
        "region_id": "ocr-image-p001-001", "page_number": 1,
        "bbox": {
            "top_left_x": 300, "top_left_y": 100,
            "bottom_right_x": 900, "bottom_right_y": 800,
        },
    }]


def test_passive_inventory_is_appended_only_for_registry_crosscheck():
    ocr = _ocr_with_graphic_region()
    ordinary = build_detection_user_text("drawing.pdf", "001", ocr)
    registry = build_detection_user_text(
        "drawing.pdf", "001", ocr, include_spatial_inventory=True,
    )

    assert "OCR GRAPHIC REGION INVENTORY" not in ordinary
    assert "ocr-image-p001-001" in registry
