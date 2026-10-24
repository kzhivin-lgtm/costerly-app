from io import BytesIO

from PIL import Image

from agents.anthropic_adapter import (
    build_detection_v5_source_degraded_context_pair_crops,
    build_detection_v5_source_degraded_registry_content_blocks,
    build_detection_v5_membership_view_crops,
    build_detection_v5_review_coordinate_frames,
    build_detection_v5_review_page_context_images,
    format_detection_v5_coordinate_frame_context,
)


def _page_image() -> bytes:
    image = Image.new("RGB", (1588, 1123), "white")
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def _ocr_package() -> dict:
    return {
        "rendering": {"dpi": 200},
        "pages": [{"page_number": 1, "dimensions": {"width": 3308, "height": 2339}}],
    }


def _group() -> dict:
    return {
        "group_id": "VG-005",
        "page_number": 1,
        "evidence_class": "object_evidence",
        "bbox": {
            "top_left_x": 1600,
            "top_left_y": 900,
            "bottom_right_x": 3265,
            "bottom_right_y": 1500,
        },
    }


def test_v510_review_maps_fusion_bbox_to_smaller_page_image_frame():
    frames, frame_audit = build_detection_v5_review_coordinate_frames(
        ocr_package=_ocr_package(), page_images=[_page_image()],
    )

    assert frame_audit[0]["fusion_dimensions"] == {"width": 3308, "height": 2339}
    assert frame_audit[0]["review_dimensions"] == {"width": 1588, "height": 1123}
    assert frame_audit[0]["source"] == "mistral_page_dimensions"
    assert "P1|FUSION=3308x2339|IMAGE=1588x1123" in (
        format_detection_v5_coordinate_frame_context(frames)
    )

    crops, crop_audit = build_detection_v5_membership_view_crops(
        page_images=[_page_image()], visual_groups=[_group()], coordinate_frames=frames,
    )

    assert len(crops) == 1
    assert crop_audit[0]["review_bbox"] == {
        "top_left_x": 768,
        "top_left_y": 432,
        "bottom_right_x": 1567,
        "bottom_right_y": 720,
    }
    assert crop_audit[0]["crop_dimensions"]["width"] > 700

    contexts, context_audit = build_detection_v5_review_page_context_images(
        page_images=[_page_image()], visual_groups=[_group()], coordinate_frames=frames,
    )

    assert len(contexts) == 1
    assert context_audit[0]["overlays"][0]["review_bbox"] == crop_audit[0]["review_bbox"]


def test_source_degraded_review_keeps_full_page_and_adds_only_local_pair_context():
    groups = [
        {
            "group_id": "view-001", "page_number": 1,
            "evidence_class": "object_evidence",
            "bbox": {
                "top_left_x": 80, "top_left_y": 40,
                "bottom_right_x": 500, "bottom_right_y": 360,
            },
        },
        {
            "group_id": "view-002", "page_number": 1,
            "evidence_class": "object_evidence",
            "bbox": {
                "top_left_x": 520, "top_left_y": 40,
                "bottom_right_x": 980, "bottom_right_y": 360,
            },
        },
        {
            "group_id": "view-003", "page_number": 1,
            "evidence_class": "object_evidence",
            "bbox": {
                "top_left_x": 1200, "top_left_y": 650,
                "bottom_right_x": 1450, "bottom_right_y": 1000,
            },
        },
    ]
    page = _page_image()

    pair_crops, pair_audit = build_detection_v5_source_degraded_context_pair_crops(
        page_images=[page], visual_groups=groups,
    )

    assert len(pair_crops) == 1
    assert pair_crops[0]["group_ids"] == ["view-001", "view-002"]
    assert pair_crops[0]["bbox_distance_px"] == 20.0
    assert pair_audit[0]["source_bbox"] == {
        "top_left_x": 80, "top_left_y": 40,
        "bottom_right_x": 980, "bottom_right_y": 360,
    }

    view_crops, _ = build_detection_v5_membership_view_crops(
        page_images=[page], visual_groups=[groups[0]], max_side=1024,
    )
    blocks = build_detection_v5_source_degraded_registry_content_blocks(
        file_name="source.png",
        file_bytes=b"source",
        page_images=[page],
        user_text="full-page decision contract",
        view_crops=view_crops,
        pair_crops=pair_crops,
    )

    assert blocks[0] == {"type": "text", "text": "PDF page 1"}
    assert sum(block["type"] == "image" for block in blocks) == 3
    assert any(
        "Supplemental enlargement of mapped representation view-001" in block["text"]
        for block in blocks if block["type"] == "text"
    )
    assert any(
        "Supplemental local enlargement of mapped pair view-001 and view-002" in block["text"]
        for block in blocks if block["type"] == "text"
    )
