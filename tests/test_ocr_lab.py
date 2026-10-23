from agents.ocr_contract import (
    OCR_PROFILE_BASIC,
    OCR_PROFILE_EVIDENCE,
    build_mistral_ocr_request,
)
from agents.ocr_quality import evaluate_ocr_result, score_expected_evidence


def test_technical_profile_uses_native_coordinate_blocks_without_annotation_schema():
    basic = build_mistral_ocr_request(
        model="mistral-ocr-4-0",
        document_url="data:application/pdf;base64,abc",
        profile=OCR_PROFILE_BASIC,
    )
    evidence = build_mistral_ocr_request(
        model="mistral-ocr-4-0",
        document_url="data:application/pdf;base64,abc",
        profile=OCR_PROFILE_EVIDENCE,
    )

    assert "bbox_annotation_format" not in basic
    assert "bbox_annotation_format" not in evidence
    assert evidence["include_blocks"] is True
    assert evidence["confidence_scores_granularity"] == "block"


def test_quality_flags_image_only_basic_ocr_for_annotations():
    package = {
        "page_count": 1,
        "processing_seconds": 0.4,
        "pages": [
            {
                "markdown": "![img-0.jpeg](img-0.jpeg)",
                "blocks": [{"type": "image", "content": "![img-0.jpeg]"}],
                "images": [{"id": "img-0.jpeg", "image_annotation": None}],
            }
        ],
    }

    metrics = evaluate_ocr_result(package)

    assert metrics["needs_annotations"] is True
    assert metrics["image_blocks"] == 1


def test_expected_evidence_score_is_literal_and_auditable():
    package = {"pages": [{"header": "Project 472", "markdown": "4130 mm"}]}

    score = score_expected_evidence(
        package,
        {"metadata": ["Project 472"], "dimensions": ["4130", "950"]},
    )

    assert score["found"] == 2
    assert score["total"] == 3
    assert score["recall"] == 0.667


def test_expected_evidence_does_not_count_layout_coordinates():
    package = {
        "pages": [
            {
                "header": "Project",
                "markdown": "![img-0.jpeg](img-0.jpeg)",
                "blocks": [
                    {
                        "type": "image",
                        "content": "![img-0.jpeg](img-0.jpeg)",
                        "bottom_right_x": 630,
                    }
                ],
                "images": [],
            }
        ]
    }

    score = score_expected_evidence(package, {"dimensions": ["630"]})

    assert score["found"] == 0
