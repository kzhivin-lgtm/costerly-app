from io import BytesIO

from PIL import Image
import pytest

from agents.document_identity import (
    build_document_identity_title_block_crops,
    document_identity_multilingual_signal,
    derive_document_identity_from_ocr,
    merge_document_identity_fallback,
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


def test_visual_identity_fallback_fills_only_unknown_deterministic_fields():
    deterministic = unknown_document_identity()
    deterministic["project_name"] = {
        "value": "Known project", "source_page": 2,
        "source_corner": "ocr_title_block", "source_label": "PROJECT",
    }
    visual = unknown_document_identity()
    visual["project_name"] = {
        "value": "Wrong replacement", "source_page": 1,
        "source_corner": "top_right", "source_label": "OBJEKTS",
    }
    visual["client"] = {
        "value": "MAGNUM SOCIAL & MEDICAL CARE SIA", "source_page": 3,
        "source_corner": "bottom_right", "source_label": "PASŪTĪTĀJS",
    }

    merged = merge_document_identity_fallback(deterministic, visual)

    assert merged["project_name"] == deterministic["project_name"]
    assert merged["client"] == visual["client"]


def test_multilingual_identity_fallback_is_gated_by_fusion_text_not_unknown_fields():
    primary_only = document_identity_multilingual_signal({
        "evidence": {"text_blocks": [{"text": "PROJECT Rooms Заказ כמות"}]},
    })
    latvian = document_identity_multilingual_signal({
        "evidence": {"text_blocks": [{
            "text": " ".join([
                "DIZAINA AUTORS GATERIS WORKS PASŪTĪTĀJS MAGNUM",
            ] * 4),
        }]},
    })

    assert primary_only["eligible"] is False
    assert latvian["eligible"] is True


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

    assert result["model"] == "deterministic_ocr_title_block_v4_semantic_fallback"
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


def test_document_identity_uses_repeated_explicit_title_as_project_name():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": page,
                "text": (
                    "<table><tr><td>Title<br/>Офис</td>"
                    f"<td>Sheet<br/>{page}/5</td></tr></table>"
                ),
            }
            for page in range(1, 6)
        ]}
    })

    assert result["model"] == "deterministic_ocr_title_block_v4_semantic_fallback"
    assert result["identity"]["project_name"] == {
        "value": "Офис",
        "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "TITLE",
    }


def test_document_identity_does_not_promote_one_sheet_title_to_project():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": 1,
                "text": "<table><tr><td>Title</td><td>Stair detail</td></tr></table>",
            },
            {"page_number": 2, "text": "<table><tr><td>Sheet</td><td>2</td></tr></table>"},
            {"page_number": 3, "text": "<table><tr><td>Sheet</td><td>3</td></tr></table>"},
        ]}
    })

    assert result["identity"]["project_name"]["value"] == "unknown"


def test_document_identity_prefers_explicit_project_over_repeated_title():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": page,
                "text": (
                    "<table><tr><td>PROJECT</td><td>North Wing</td></tr>"
                    "<tr><td>Title</td><td>Office</td></tr></table>"
                ),
            }
            for page in range(1, 4)
        ]}
    })

    assert result["identity"]["project_name"]["value"] == "North Wing"
    assert result["identity"]["project_name"]["source_label"] == "PROJECT"


def test_document_identity_uses_semantic_title_block_roles_when_labels_are_absent():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": 1, "text": "СТУДИЯ CALGEL",
                "bbox": {"top_left_x": 2600, "top_left_y": 1880, "bottom_right_x": 2800, "bottom_right_y": 1910},
            },
            {
                "page_number": 1, "text": "ПО АДРЕСУ: МОСКВА | ВОЛХОНКА, 3",
                "bbox": {"top_left_x": 2500, "top_left_y": 1930, "bottom_right_x": 2920, "bottom_right_y": 1960},
            },
            {
                "page_number": 1, "text": "ООО \\\"АРХИПРОБА\\\"",
                "bbox": {"top_left_x": 2850, "top_left_y": 2135, "bottom_right_x": 3070, "bottom_right_y": 2160},
            },
            {
                "page_number": 1, "text": "МЕБЕЛЬ / СТЕЙШН И ПОДДОНЫ",
                "bbox": {"top_left_x": 2260, "top_left_y": 2130, "bottom_right_x": 2610, "bottom_right_y": 2160},
            },
            {
                "page_number": 1, "text": "GSPublisherVersion 0.0.100.100",
                "bbox": {"top_left_x": 100, "top_left_y": 2210, "bottom_right_x": 3200, "bottom_right_y": 2230},
            },
        ]},
    })

    assert result["identity"]["design_partner"] == {
        "value": "ООО \\\"АРХИПРОБА\\\"", "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "SEMANTIC_DESIGN_ORGANIZATION",
    }
    assert result["identity"]["client"] == {
        "value": "СТУДИЯ CALGEL", "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "ADDRESS_ASSOCIATED_ORGANIZATION",
    }
    assert result["identity"]["project_name"] == {
        "value": "МЕБЕЛЬ / СТЕЙШН И ПОДДОНЫ", "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "TITLE_BLOCK_DOCUMENT_TITLE",
    }


def test_document_identity_uses_address_only_when_no_document_title_survives():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": 1, "text": "АДРЕС: МОСКВА, ВОЛХОНКА, 3",
                "bbox": {"top_left_x": 2200, "top_left_y": 1900, "bottom_right_x": 3000, "bottom_right_y": 1930},
            },
            {
                "page_number": 1, "text": "Лист",
                "bbox": {"top_left_x": 2900, "top_left_y": 2000, "bottom_right_x": 3000, "bottom_right_y": 2030},
            },
            {
                "page_number": 1, "text": "GSPublisherVersion 0.0.100.100",
                "bbox": {"top_left_x": 100, "top_left_y": 2200, "bottom_right_x": 3200, "bottom_right_y": 2230},
            },
        ]},
    })

    assert result["identity"]["project_name"]["value"] == "АДРЕС: МОСКВА, ВОЛХОНКА, 3"
    assert result["identity"]["project_name"]["source_label"] == "ADDRESS_AS_PROJECT_FALLBACK"


def test_document_identity_uses_named_designer_as_partner_when_no_design_firm_exists():
    result = derive_document_identity_from_ocr({
        "evidence": {"text_blocks": [
            {
                "page_number": 1, "text": "Дизайнер",
                "bbox": {"top_left_x": 2200, "top_left_y": 1900, "bottom_right_x": 2320, "bottom_right_y": 1930},
            },
            {
                "page_number": 1, "text": "Людмила Виноградова",
                "bbox": {"top_left_x": 2340, "top_left_y": 1900, "bottom_right_x": 2600, "bottom_right_y": 1930},
            },
            {
                "page_number": 1, "text": "GSPublisherVersion 0.0.100.100",
                "bbox": {"top_left_x": 100, "top_left_y": 2200, "bottom_right_x": 3200, "bottom_right_y": 2230},
            },
        ]},
    })

    assert result["identity"]["design_partner"] == {
        "value": "Людмила Виноградова", "source_page": 1,
        "source_corner": "ocr_title_block",
        "source_label": "SEMANTIC_DESIGN_PERSON",
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
