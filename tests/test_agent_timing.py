from agents.anthropic_adapter import (
    build_agent_usage_event,
    build_detection_ocr_context,
    build_detection_system_content,
    build_detection_user_text,
    build_uploaded_file_content_block,
    normalize_detection_identity_fields,
)
from agents.ocr_adapter import normalize_mistral_ocr_response
from ui.processing_stage import processing_stage_html
from use_cases.rfq_processing import _normalize_run, _ocr_storage_usage, _run_optional_ocr


class _Usage:
    input_tokens = 100
    output_tokens = 20


class _Response:
    usage = _Usage()


def test_anthropic_usage_event_contains_duration():
    event = build_agent_usage_event(
        agent_name="detection",
        operation="rfq_detection",
        company_id="001",
        run_id="run_001",
        file_name="drawing.pdf",
        object_id=None,
        object_name=None,
        model="claude-haiku-4-5-20251001",
        prompt_version="detection_v1",
        response=_Response(),
        started_at="2026-07-17T10:00:00+00:00",
        finished_at="2026-07-17T10:00:12.345000+00:00",
    )

    assert event["duration_seconds"] == 12.345
    assert event["raw_usage"]["duration_seconds"] == 12.345


def test_processing_stage_shows_live_timer_and_original_subtitle():
    markup = processing_stage_html(
        progress_value=0.5,
        elapsed_seconds=65,
    )

    assert "Elapsed 01:05" in markup
    assert "Detecting scope items for estimation" in markup
    assert "taking longer than expected" not in markup


def test_processing_stage_exposes_real_phase_and_completion():
    markup = processing_stage_html(
        progress_value=1,
        processing_phase="complete",
        complete=True,
    )

    assert 'data-processing-phase="complete"' in markup
    assert 'data-processing-complete="true"' in markup


def test_detection_input_cache_is_disabled_by_default_and_can_be_enabled():
    system = build_detection_system_content()
    document = build_uploaded_file_content_block("drawing.pdf", b"pdf")
    user_text = build_detection_user_text("drawing.pdf", "001")

    assert "cache_control" not in system[0]
    assert "commercial object" in system[0]["text"].lower()
    assert "cache_control" not in document
    assert "DETECTION PROMPT:" not in user_text

    cached_system = build_detection_system_content(cache_enabled=True)
    cached_document = build_uploaded_file_content_block(
        "drawing.pdf",
        b"pdf",
        cache_enabled=True,
    )
    assert cached_system[0]["cache_control"] == {"type": "ephemeral"}
    assert cached_document["cache_control"] == {"type": "ephemeral"}


def test_detection_identity_fields_are_normalized_before_validation():
    result = {
        "rfq_run": {
            "run_id": "authoritative_run",
            "company_id": "wrong_company",
            "file_name": "wrong.pdf",
            "project_name": "Keep this semantic value",
        },
        "detected_objects": [
            {
                "run_id": "mismatched_run",
                "company_id": "another_company",
                "object_name": "Keep this object",
            }
        ],
    }

    normalized = normalize_detection_identity_fields(
        result,
        company_id="001",
        file_name="drawing.pdf",
    )

    assert normalized["rfq_run"]["run_id"] == "authoritative_run"
    assert normalized["rfq_run"]["company_id"] == "001"
    assert normalized["rfq_run"]["file_name"] == "drawing.pdf"
    assert normalized["rfq_run"]["project_name"] == "Keep this semantic value"
    assert normalized["detected_objects"][0]["run_id"] == "authoritative_run"
    assert normalized["detected_objects"][0]["company_id"] == "001"
    assert normalized["detected_objects"][0]["object_name"] == "Keep this object"


def test_file_review_run_keeps_partner_and_client_roles_separate():
    normalized = _normalize_run(
        {
            "project_name": "Example",
            "design_partner": "Studio A",
            "client": "Developer B",
            "file_quality_label": "detailed_drawings",
        }
    )

    assert normalized["partner"] == "Studio A"
    assert normalized["client"] == "Developer B"
    assert normalized["file_quality"] == "detailed_drawings"




def test_ocr_storage_preserves_full_result_and_detection_context():
    provider_response = {
        "model": "mistral-ocr-4-0",
        "pages": [
            {
                "index": 0,
                "markdown": "QTY 3",
                "header": "PROJECT 472",
                "footer": "PAGE 23",
            }
        ],
        "usage_info": {"pages_processed": 1, "doc_size_bytes": 100},
    }
    package = normalize_mistral_ocr_response(
        provider_response,
        file_name="drawing.pdf",
        file_bytes=b"pdf",
        model="mistral-ocr-4-0",
        elapsed_seconds=1,
    )

    stored = _ocr_storage_usage(package)

    assert stored["provider_usage"]["pages_processed"] == 1
    assert stored["ocr_result"]["raw_response"] == provider_response
    assert "QTY 3" in stored["detection_context"]
    assert "QTY 3" in stored["candidate_ocr_context"]


def test_ocr_storage_can_preserve_actual_spatial_detection_handoff():
    package = {
        "usage": {"pages_processed": 1},
        "pages": [{"page_number": 1}],
        "evidence": {
            "text_blocks": [],
            "literal_items": [
                {
                    "page_number": 1,
                    "source_image_id": "img-0.jpeg",
                    "source_image_bbox": {},
                    "text": "2695",
                    "category": "dimension",
                    "region": "center",
                    "occurrences": 1,
                }
            ],
        },
    }
    context = build_detection_ocr_context(package)

    stored = _ocr_storage_usage(package, detection_context=context)

    assert stored["detection_context"] == context
    assert "2695" in stored["detection_context"]


def test_ocr_failure_falls_back_to_original_file_without_ocr(monkeypatch):
    def fail_ocr(**_kwargs):
        raise RuntimeError("Mistral OCR request failed: timed out")

    monkeypatch.setattr(
        "use_cases.rfq_processing.run_mistral_direct_pdf_evidence_ocr",
        fail_ocr,
    )

    stored_package, detection_package = _run_optional_ocr(
        file_name="drawing.pdf",
        file_bytes=b"pdf",
    )

    assert detection_package is None
    assert stored_package["status"] == "failed"
    assert "timed out" in stored_package["error"]
    assert build_detection_ocr_context(detection_package) == "OCR text layer: unavailable"
