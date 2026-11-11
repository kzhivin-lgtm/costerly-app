from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image, ImageDraw

from agents.detection_fusion_candidate_regions import (
    build_detection_fusion_page_profile_audit,
    format_detection_fusion_page_profiles,
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


def test_fusion_page_profile_handoff_is_complete_but_never_an_object_claim():
    profiles = [{
        "page_number": 3,
        "representation": "mixed",
        "text_layer": "substantive",
        "structural_anchors": "several",
        "coordinate_evidence": "usable",
        "eligible_mechanisms": ["OCR", "text_fusion", "vector_cluster_recall"],
        "page_size_points": {"width": 1191, "height": 1684},
        "rendered_page": {
            "status": "succeeded", "occupied_area_ratio": 0.099199,
            "dominant_background_rgb": [248, 248, 248],
        },
        "raw_metrics": {
            "native_text_span_count": 83,
            "image_xobject_placement_count": 1,
            "image_info_count": 1,
            "image_placement_area_ratio": 0.003396,
            "form_xobject_count": 0,
            "vector_path_count": None,
            "vector_path_count_estimate": 52729,
            "vector_primitive_count": 52729,
            "vector_content_stream_bytes": 1657156,
            "vector_summary_status": "approximate_content_stream",
            "vector_cluster_count": None,
            "vector_cluster_status": "skipped_content_stream_limit",
            "vector_path_area_ratio": None,
        },
        "sources": {
            "native_text": {"status": "succeeded", "seconds": 0.029215},
            "image_xobjects": {"status": "succeeded", "seconds": 0.025265},
            "form_xobjects": {"status": "succeeded", "seconds": 0.000087},
            "vector_summary": {"status": "succeeded", "seconds": 0.040662},
        },
    }]

    handoff = format_detection_fusion_page_profiles(profiles)

    assert "PP-P003|REP=mixed|TEXT=substantive" in handoff
    assert "VECTOR_PATHS=52729" in handoff
    assert "VECTOR_STATUS=approximate_content_stream" in handoff
    assert "OCCUPIED=0.099199" in handoff
    assert "not object claims" in handoff


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
