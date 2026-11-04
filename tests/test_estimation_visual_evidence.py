import base64
from io import BytesIO
import json

from PIL import Image

from agents.estimation_visual_evidence import page_content


def source_bytes():
    buf = BytesIO()
    Image.new("RGB", (1000, 700), "white").save(buf, format="WEBP")
    return buf.getvalue()


def payload():
    return {"object": {"object_id": "o"}, "evidence": {"geometry_context": {
        "rendering": {"dpi": 144}, "page_profiles": [{"page_number": 1,
            "page_size_points": {"width": 1000, "height": 700}}]}}}


VIEWS = [{"view_id": "v1", "page_number": 1, "bbox": {
    "top_left_x": 1000, "top_left_y": 700, "bottom_right_x": 1800, "bottom_right_y": 1300}},
    {"view_id": "v2", "page_number": 1, "bbox": {
    "top_left_x": 100, "top_left_y": 100, "bottom_right_x": 800, "bottom_right_y": 600}}]


def test_view_details_map_source_render_coordinates_to_resized_evidence():
    content, used = page_content(page_bytes=source_bytes(), storage_ref="r", page_number=1,
                                payloads=[payload()], views=VIEWS, detail_budget=1)
    assert used == 1
    meta = json.loads(content[0]["text"])
    assert meta["displayed_image_pixels"] == [1000, 700]
    assert meta["view_regions"][0]["coordinate_frame_pixels"] == [2000, 1400]
    assert meta["view_regions"][0]["bbox_normalized"][:2] == [.5, .5]
    images = [item for item in content if item["type"] == "image"]
    assert len(images) == 2
    detail = Image.open(BytesIO(base64.b64decode(images[1]["source"]["data"])))
    assert 425 <= detail.width <= 435 and 352 <= detail.height <= 357
    caption = next(json.loads(item["text"]) for item in content if item["type"] == "text" and "detail_of_existing_view" in item["text"])
    assert caption["generated_header_height_px"] == 32
    assert caption["detail_of_existing_view"]["view_id"] == "v1"


def test_unknown_coordinate_frame_never_guesses_a_crop_and_shared_regions_deduplicate():
    _, used = page_content(page_bytes=source_bytes(), storage_ref="r", page_number=1,
                          payloads=[{}], views=VIEWS)
    assert used == 0
    content, used = page_content(page_bytes=source_bytes(), storage_ref="r", page_number=1,
                                payloads=[payload(), payload()], views=VIEWS)
    assert used == 2 and len(json.loads(content[0]["text"])["view_regions"]) == 2
