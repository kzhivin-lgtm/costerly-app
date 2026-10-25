from agents.detection_document_classifier import classify_detection_document


def _capable_source(page_count: int) -> dict:
    return {
        "page_count": page_count,
        "route_eligible": False,
        "route_reason": "ordinary_v5_retains_usable_coordinate_evidence",
    }


def _two_islands_page() -> dict:
    return {
        "dimensions": {"width": 1000, "height": 1000},
        "images": [
            {"top_left_x": 10, "top_left_y": 10, "bottom_right_x": 450, "bottom_right_y": 400},
            {"top_left_x": 520, "top_left_y": 10, "bottom_right_x": 960, "bottom_right_y": 400},
        ],
    }


def test_classifier_routes_continuous_technical_assembly_set_to_haiku():
    pages = [_two_islands_page() for _ in range(6)]
    for index, page in enumerate(pages, start=1):
        page.update({"page_number": index, "markdown": "Detail views"})
    route = classify_detection_document(
        ocr_package={
            "pages": pages,
            "evidence": {
                "text_blocks": [
                    {"page_number": index, "text": "Title: Заказ 1208"}
                    for index in range(1, 7)
                ],
                "page_profiles": [
                    {"page_number": index, "representation": "vector"}
                    for index in range(1, 7)
                ],
            },
        },
        source_capability=_capable_source(6),
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["category"] == "assembly_set"
    assert route["decision"] == "assembly_set_haiku"
    assert route["registry_model"] == "haiku"
    assert route["signals"]["continuous_document_identifiers"] == {"1208": [1, 2, 3, 4, 5, 6]}


def test_classifier_routes_unlabelled_repeated_multi_object_risk_to_sonnet():
    route = classify_detection_document(
        ocr_package={"pages": [_two_islands_page(), _two_islands_page()]},
        source_capability=_capable_source(2),
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["category"] == "ada_sparse_multi_object"
    assert route["registry_model"] == "sonnet"
    assert route["evidence_model"] == "haiku"


def test_classifier_keeps_labelled_multi_drawing_document_on_ordinary_haiku():
    page = _two_islands_page()
    page["markdown"] = "OM 15-1 Stair railing"
    route = classify_detection_document(
        ocr_package={"pages": [page, page]},
        source_capability=_capable_source(2),
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["category"] == "ordinary_object_set"
    assert route["registry_model"] == "haiku"
    assert route["signals"]["strong_source_code_count"] == 1


def test_classifier_reserves_source_degraded_for_absent_coordinate_evidence():
    route = classify_detection_document(
        ocr_package={"pages": [{"page_number": 1}]},
        source_capability={"page_count": 1, "route_eligible": True},
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["category"] == "source_degraded_visual"
    assert route["registry_model"] == "haiku"


def test_classifier_preserves_native_graphic_pack_before_visual_only_fallback():
    route = classify_detection_document(
        ocr_package={
            "pages": [{"page_number": 1}],
            "evidence": {
                "graphic_regions": [
                    {"source": "native_pdf_image_xobject"},
                    {"source": "native_pdf_image_xobject"},
                ],
            },
        },
        source_capability={"page_count": 1, "route_eligible": True},
        base_model="haiku",
        boundary_model="sonnet",
    )

    assert route["category"] == "page23_native_graphic_pack"
    assert route["registry_model"] == "haiku"


def test_classifier_preserves_explicit_model_override_for_benchmarks():
    route = classify_detection_document(
        ocr_package={"pages": [_two_islands_page(), _two_islands_page()]},
        source_capability=_capable_source(2),
        base_model="haiku",
        boundary_model="sonnet",
        explicit_model="benchmark-model",
    )

    assert route["category"] == "explicit_model_override"
    assert route["registry_model"] == "benchmark-model"
    assert route["evidence_model"] == "benchmark-model"
