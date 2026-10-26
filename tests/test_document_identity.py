from io import BytesIO

from PIL import Image
import pytest

from agents.document_identity import (
    build_document_identity_title_block_crops,
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
