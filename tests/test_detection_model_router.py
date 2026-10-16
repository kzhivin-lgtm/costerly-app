from agents.detection_model_router import detection_v42_model_route


def _two_islands_page() -> dict:
    return {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 450, "bottom_right_y": 400},
            {"top_left_x": 520, "top_left_y": 10, "bottom_right_x": 960, "bottom_right_y": 400},
        ],
    }


def test_router_selects_sonnet_only_for_unlabelled_repeated_multi_drawing_pages():
    route = detection_v42_model_route(
        ocr_package={"pages": [_two_islands_page(), _two_islands_page()]},
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["decision"] == "sonnet_boundary_risk"
    assert route["registry_model"] == "sonnet"
    assert route["evidence_model"] == "haiku"
    assert route["signals"]["pages_with_multiple_large_drawings"] == 2


def test_router_keeps_labelled_multi_drawing_document_on_base_model():
    page = _two_islands_page()
    page["markdown"] = "OM 15-1 Stair railing"
    route = detection_v42_model_route(
        ocr_package={"pages": [page, page]},
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["decision"] == "haiku_default"
    assert route["registry_model"] == "haiku"
    assert route["signals"]["strong_source_code_count"] == 1


def test_router_preserves_explicit_model_override_for_benchmarks():
    route = detection_v42_model_route(
        ocr_package={"pages": [_two_islands_page(), _two_islands_page()]},
        base_model="haiku",
        boundary_model="sonnet",
        explicit_model="benchmark-model",
    )

    assert route["decision"] == "explicit_model_override"
    assert route["registry_model"] == "benchmark-model"
    assert route["evidence_model"] == "benchmark-model"
