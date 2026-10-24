from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image, ImageDraw

from agents.detection_fusion_candidate_regions import (
    build_detection_fusion_page_profile_audit,
)
from agents.ocr_adapter import build_ocr_evidence
from agents.ocr_rendering import run_mistral_document_evidence_ocr
from agents.pdf_page_inspection import (
    attach_rendered_page_measurements,
    inspect_native_pdf_pages,
    measure_rendered_page_visual_coverage,
)


def _sample_pdf() -> bytes:
    document = fitz.open()
    try:
        vector_page = document.new_page(width=144, height=144)
        vector_page.insert_text((12, 20), "W=358")
        vector_page.draw_rect(fitz.Rect(20, 30, 120, 120))

        image_page = document.new_page(width=144, height=144)
        image = Image.new("RGB", (10, 10), "white")
        image.putpixel((0, 0), (0, 0, 0))
        encoded = BytesIO()
        image.save(encoded, format="PNG")
        image_page.insert_image(fitz.Rect(20, 20, 120, 120), stream=encoded.getvalue())
        return document.tobytes()
    finally:
        document.close()


def test_native_pdf_page_inspection_classifies_each_page_without_object_claims():
    inspection = inspect_native_pdf_pages(_sample_pdf(), dpi=200)

    assert inspection["sources"]["status"] == "succeeded"
    assert len(inspection["text_blocks"]) == 1
    assert len(inspection["graphic_regions"]) == 1
    profiles = inspection["page_profiles"]
    assert [profile["representation"] for profile in profiles] == ["vector", "raster"]
    assert profiles[0]["text_layer"] == "sparse"
    assert profiles[0]["raw_metrics"]["vector_path_count"] >= 1
    assert profiles[1]["raw_metrics"]["image_xobject_placement_count"] == 1
    assert profiles[1]["structural_anchors"] == "image"
    assert "native_anchor_recall" in profiles[1]["eligible_mechanisms"]


def test_rendered_coverage_uses_existing_pixels_and_fusion_keeps_profile_passive():
    image = Image.new("RGB", (100, 100), "#f4f0e9")
    ImageDraw.Draw(image).rectangle((20, 20, 80, 80), fill="black")
    encoded = BytesIO()
    image.save(encoded, format="PNG")
    measurement = measure_rendered_page_visual_coverage(encoded.getvalue())

    assert measurement["status"] == "succeeded"
    assert measurement["occupied_area_ratio"] > 0.3

    profiles = attach_rendered_page_measurements(
        [{"page_number": 1, "representation": "vector"}], {1: encoded.getvalue()},
    )
    evidence = build_ocr_evidence([], page_profiles=profiles)
    assert build_detection_fusion_page_profile_audit({"evidence": evidence}) == profiles


def test_default_ocr_path_attaches_profile_without_changing_ocr_provider_contract():
    def page_ocr(*, file_name, file_bytes, profile):
        return {
            "model": "mistral-ocr-4-1",
            "pages": [{"page_number": 1, "blocks": [], "images": []}],
            "raw_response": {},
        }

    package = run_mistral_document_evidence_ocr(
        file_name="sample.pdf", file_bytes=_sample_pdf(), page_ocr=page_ocr,
    )

    assert package["native_pdf_inspection"]["status"] == "succeeded"
    assert package["native_pdf_inspection"]["profile_count"] == 2
    assert len(package["evidence"]["page_profiles"]) == 2
    assert all(
        profile["rendered_page"]["status"] == "succeeded"
        for profile in package["evidence"]["page_profiles"]
    )
