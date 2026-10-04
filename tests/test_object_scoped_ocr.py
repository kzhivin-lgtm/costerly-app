from use_cases.object_scoped_ocr import build_object_scoped_ocr_evidence


def test_scoped_ocr_selects_only_intersecting_blocks_and_contained_annotations():
    result = build_object_scoped_ocr_evidence(
        object_id="object-001",
        page_number=1,
        preview_bbox={"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 100, "bottom_right_y": 100},
        page_dimensions={"width": 200, "height": 200},
        ocr_evidence={
            "text_blocks": [
                {"page_number": 1, "text": "inside", "bbox": {"top_left_x": 20, "top_left_y": 20, "bottom_right_x": 40, "bottom_right_y": 40}},
                {"page_number": 1, "text": "other", "bbox": {"top_left_x": 120, "top_left_y": 20, "bottom_right_x": 140, "bottom_right_y": 40}},
            ],
            "literal_items": [
                {"page_number": 1, "text": "local", "source_image_bbox": {"top_left_x": 30, "top_left_y": 30, "bottom_right_x": 50, "bottom_right_y": 50}},
                {"page_number": 1, "text": "sheet", "source_image_bbox": {"top_left_x": 0, "top_left_y": 0, "bottom_right_x": 200, "bottom_right_y": 200}},
            ],
        },
    )

    assert [block["text"] for block in result["text_blocks"]] == ["inside"]
    assert [item["text"] for item in result["literal_items"]] == ["local"]
    assert result["source_bbox"]["bottom_right_x"] == 100.0


def test_scoped_ocr_expands_fractional_preview_bbox_before_matching():
    result = build_object_scoped_ocr_evidence(
        object_id="object-001",
        page_number=1,
        preview_bbox={"top_left_x": 0.1, "top_left_y": 0.1, "bottom_right_x": 0.5, "bottom_right_y": 0.5},
        page_dimensions={"width": 200, "height": 100},
        ocr_evidence={"text_blocks": [{"page_number": 1, "text": "local", "bbox": {"top_left_x": 25, "top_left_y": 25, "bottom_right_x": 30, "bottom_right_y": 30}}]},
    )

    assert result["source_bbox"] == {"top_left_x": 20.0, "top_left_y": 10.0, "bottom_right_x": 100.0, "bottom_right_y": 50.0}
    assert [block["text"] for block in result["text_blocks"]] == ["local"]
