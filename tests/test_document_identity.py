from io import BytesIO

from PIL import Image
import pytest

from agents.document_identity import (
    build_document_identity_title_block_crops,
    derive_document_identity_from_ocr,
    unknown_document_identity,
    validate_document_identity,
)


def _page_image() -> bytes:
    image = Image.new("RGB", (1600, 1000), "white")
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def test_document_identity_samples_initial_and_final_pages_as_corner_crops():
    crops, audit = build_document_identity_title_block_crops([_page_image()] * 5)

    assert {(crop["page_number"], crop["corner"]) for crop in crops} == {
        (page, corner)
        for page in (1, 2, 3, 5)
        for corner in ("top_left", "top_right", "bottom_left", "bottom_right")
    }
    assert len(audit) == 16


def test_document_identity_requires_an_explicit_visible_label_for_known_value():
    identity = unknown_document_identity()
    identity["project_name"] = {
        "value": "ROOMS", "source_page": 2,
        "source_corner": "bottom_left", "source_label": "PROJECT",
    }

    assert validate_document_identity(
        identity,
        allowed_pages={1, 2},
        allowed_corners={"bottom_left"},
    )["project_name"]["value"] == "ROOMS"

    identity["design_partner"] = {
        "value": "Hasolelim_Carpentry", "source_page": 2,
        "source_corner": "bottom_left", "source_label": "FILE NAME",
    }
    with pytest.raises(ValueError, match="non-identity"):
        validate_document_identity(
            identity,
            allowed_pages={1, 2},
            allowed_corners={"bottom_left"},
        )


def test_document_identity_reads_project_only_from_explicit_ocr_title_block_label():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [{
            "page_number": 11,
            "text": (
                "<table><tr><td>PROJECT</td><td>שם העבודה</td></tr>"
                "<tr><td>ROOMS<br/>המוללים תל אביב</td></tr>"
                "<tr><td>FILE NAME</td><td>Hasolelim_Carpentry</td></tr></table>"
            ),
        }]}
    })

    assert result["model"] == "deterministic_ocr_title_block_v2"
    assert result["identity"]["project_name"]["value"] == "ROOMS"
    assert result["identity"]["client"]["value"] == "unknown"
    assert result["identity"]["design_partner"]["value"] == "unknown"


def test_document_identity_uses_repeated_explicit_order_as_project_identifier():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {"page_number": page, "text": f"<table><tr><td>Заказ</td><td>12-08</td></tr></table>"}
            for page in range(1, 7)
        ]}
    })

    assert result["identity"]["project_name"] == {
        "value": "Order 12-08",
        "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "ORDER",
    }


def test_document_identity_does_not_treat_one_order_label_as_document_project():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {"page_number": 1, "text": "<table><tr><td>Заказ</td><td>12-08</td></tr></table>"},
            {"page_number": 2, "text": "<table><tr><td>Лист</td><td>2</td></tr></table>"},
            {"page_number": 3, "text": "<table><tr><td>Лист</td><td>3</td></tr></table>"},
        ]}
    })

    assert result["identity"]["project_name"]["value"] == "unknown"
