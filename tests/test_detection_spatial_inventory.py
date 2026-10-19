import pytest

from agents.anthropic_adapter import (
    build_detection_user_text,
)
from agents.detection_spatial_inventory import (
    build_detection_spatial_inventory,
    validate_detection_spatial_islands,
)
from agents.schemas.detection_visual_map_schema import (
    DetectionVisualMapSchemaError,
    validate_detection_visual_map,
)


def _ocr_with_graphic_and_sidebar() -> dict:
    return {
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {
                        "type": "table",
                        "content": "project and material notes",
                        "top_left_x": 10,
                        "top_left_y": 10,
                        "bottom_right_x": 200,
                        "bottom_right_y": 900,
                    },
                    {
                        "type": "image",
                        "content": "![img-0.jpeg](img-0.jpeg)",
                        "top_left_x": 300,
                        "top_left_y": 100,
                        "bottom_right_x": 900,
                        "bottom_right_y": 800,
                    },
                ],
            }
        ]
    }


def _group(*, source_region_ids: list[str]) -> dict:
    return {
        "group_id": "view-001",
        "page_number": 1,
        "location_hint": "drawing field",
        "visual_description": "unlabelled cabinet elevation",
        "representation_kind": "elevation",
        "source_region_ids": source_region_ids,
    }


def test_spatial_inventory_keeps_unlabelled_graphic_region_but_not_sidebar_text():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())

    assert inventory == [{
        "region_id": "ocr-image-p001-001",
        "page_number": 1,
        "bbox": {
            "top_left_x": 300,
            "top_left_y": 100,
            "bottom_right_x": 900,
            "bottom_right_y": 800,
        },
    }]


def test_vision_only_visual_group_is_allowed_when_ocr_missed_its_island():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())
    assert validate_detection_visual_map(
        {"visual_groups": [_group(source_region_ids=[])]},
        require_source_region_ids=True,
        spatial_regions=inventory,
    )


def test_spatial_islands_reject_a_silent_uninspected_graphic_region():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())
    with pytest.raises(ValueError, match="every OCR graphic region"):
        validate_detection_spatial_islands(
            [], spatial_regions=inventory, page_count=1,
        )


def test_spatial_islands_keep_non_object_context_as_an_island():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())
    validated = validate_detection_spatial_islands([
        {
            "island_id": "island-001",
            "page_number": 1,
            "location_hint": "full drawing field",
            "visual_description": "generic floor plan",
            "classification": "non_object_context",
            "observation_basis": "ocr_supported",
            "source_region_ids": ["ocr-image-p001-001"],
        },
    ], spatial_regions=inventory, page_count=1)
    assert validated[0]["classification"] == "non_object_context"


def test_spatial_islands_allow_a_rendered_vision_only_island():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())
    validated = validate_detection_spatial_islands([
        {
            "island_id": "island-001",
            "page_number": 1,
            "location_hint": "full drawing field",
            "visual_description": "cabinet elevation",
            "classification": "object_candidate",
            "observation_basis": "ocr_supported",
            "source_region_ids": ["ocr-image-p001-001"],
        },
        {
            "island_id": "island-002",
            "page_number": 1,
            "location_hint": "lower drawing field",
            "visual_description": "separate rendered section",
            "classification": "object_candidate",
            "observation_basis": "vision_only",
            "source_region_ids": [],
        },
    ], spatial_regions=inventory, page_count=1)
    assert validated[1]["observation_basis"] == "vision_only"


def test_spatial_inventory_accepts_an_unlabelled_graphic_as_object_evidence():
    inventory = build_detection_spatial_inventory(_ocr_with_graphic_and_sidebar())
    group = _group(source_region_ids=["ocr-image-p001-001"])
    validated = validate_detection_visual_map(
        {"visual_groups": [group]},
        require_source_region_ids=True,
        spatial_regions=inventory,
    )
    assert validated["visual_groups"][0]["source_region_ids"] == ["ocr-image-p001-001"]


def test_spatial_inventory_is_sent_only_to_the_registry_call():
    ocr = _ocr_with_graphic_and_sidebar()

    ordinary = build_detection_user_text("drawing.pdf", "001", ocr)
    registry = build_detection_user_text(
        "drawing.pdf", "001", ocr, include_spatial_inventory=True,
    )

    assert "OCR GRAPHIC REGION INVENTORY" not in ordinary
    assert "ocr-image-p001-001" in registry
