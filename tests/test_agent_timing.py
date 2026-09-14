from inspect import getsource
from types import SimpleNamespace
from unittest.mock import patch

from agents.anthropic_adapter import (
    apply_benchmark_run_suffix,
    build_agent_usage_event,
    build_detection_ocr_context,
    build_detection_system_content,
    build_detection_user_text,
    build_uploaded_file_content_block,
    create_claude_message_streamed,
    normalize_detection_identity_fields,
)
from agents.ocr_adapter import normalize_mistral_ocr_response
from ui.processing_stage import processing_stage_html
from ui.js_guards import install_upload_interaction_guards
from screens.processing import expected_detection_seconds
from use_cases.rfq_processing import (
    _normalize_run,
    _ocr_storage_usage,
    _run_deferred_naming,
    _run_optional_ocr,
    save_file_review_object_name,
)
from db.repositories import insert_agent_usage_events


class _Usage:
    input_tokens = 100
    output_tokens = 20


class _Response:
    usage = _Usage()


class _FakeStream:
    request_id = "req_benchmark_001"

    def __init__(self):
        self._response = _Response()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return None

    def __iter__(self):
        yield SimpleNamespace(type="message_start")
        yield SimpleNamespace(
            type="content_block_delta",
            delta=SimpleNamespace(type="text_delta", text="{"),
        )

    def get_final_message(self):
        return self._response


class _FakeMessages:
    def stream(self, **kwargs):
        return _FakeStream()


class _FakeClient:
    messages = _FakeMessages()


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


def test_streamed_message_records_first_token_and_generation_phases():
    with patch(
        "agents.anthropic_adapter.time.perf_counter",
        side_effect=[10.0, 10.1, 10.25, 10.5],
    ):
        response, diagnostics = create_claude_message_streamed(
            _FakeClient(),
            model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            messages=[],
        )

    assert isinstance(response, _Response)
    assert diagnostics["request_id"] == "req_benchmark_001"
    assert diagnostics["first_event_seconds"] == 0.1
    assert diagnostics["time_to_first_token_seconds"] == 0.25
    assert diagnostics["generation_after_first_token_seconds"] == 0.25
    assert diagnostics["stream_total_seconds"] == 0.5
    assert diagnostics["stream_event_count"] == 2
    assert diagnostics["text_delta_count"] == 1


def test_benchmark_suffix_is_applied_after_detection(monkeypatch):
    monkeypatch.setenv("BENCHMARK_RUN_SUFFIX", "baseline 3262")
    result = {
        "rfq_run": {"run_id": "project_run_001"},
        "detected_objects": [{"run_id": "project_run_001"}],
    }

    suffixed = apply_benchmark_run_suffix(result)

    assert suffixed["rfq_run"]["run_id"] == "project_run_001_baseline_3262"
    assert suffixed["detected_objects"][0]["run_id"] == (
        "project_run_001_baseline_3262"
    )


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


def test_processing_stage_exposes_expected_detection_seconds():
    markup = processing_stage_html(
        processing_phase="detection",
        expected_detection_seconds=14,
    )

    assert 'data-expected-detection-seconds="14"' in markup


def test_detection_pacing_uses_ocr_page_buckets():
    assert expected_detection_seconds(None) == 28
    assert expected_detection_seconds(0) == 28
    assert expected_detection_seconds(1) == 14
    assert expected_detection_seconds(2) == 14
    assert expected_detection_seconds(3) == 18
    assert expected_detection_seconds(6) == 18
    assert expected_detection_seconds(7) == 28
    assert expected_detection_seconds(12) == 28
    assert expected_detection_seconds(13) == 45
    assert expected_detection_seconds(20) == 45
    assert expected_detection_seconds(21) == 60


def test_processing_progress_uses_golden_stage_weights_and_ease_in_curve():
    source = getsource(install_upload_interaction_guards)

    assert "ocr: [8, 13, 1.5]" in source
    assert "detection: [13, 96, detectionExpectedSeconds]" in source
    assert "saving: [96, 99, 1]" in source
    assert "Math.pow(normalized, 1.35)" in source


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


def test_usage_diagnostics_are_batched_for_legacy_schema():
    class Execute:
        def execute(self):
            return None

    class Table:
        def __init__(self):
            self.rows = None

        def insert(self, rows):
            self.rows = rows
            return Execute()

    class Client:
        def __init__(self):
            self.target = Table()

        def table(self, name):
            assert name == "agent_usage_events"
            return self.target

    client = Client()
    insert_agent_usage_events(
        client,
        [
            {
                "agent_name": "detection",
                "duration_seconds": 12.5,
                "raw_usage": {"input_tokens": 100},
            },
            {
                "agent_name": "naming",
                "duration_seconds": 2.5,
                "raw_usage": {},
            },
        ],
    )

    assert len(client.target.rows) == 2
    assert "duration_seconds" not in client.target.rows[0]
    assert client.target.rows[0]["raw_usage"]["duration_seconds"] == 12.5
    assert client.target.rows[1]["raw_usage"]["duration_seconds"] == 2.5


def test_deferred_naming_updates_locked_names_and_returns_without_detection_changes(
    monkeypatch,
):
    updates = []
    events = []
    detected_objects = [
        {"object_id": "object-001", "object_name": "Object 1", "quantity": 1}
    ]
    locked_objects = [
        {
            "object_id": "object-001",
            "object_index": "",
            "current_name": "Object 1",
        }
    ]

    monkeypatch.setattr(
        "use_cases.rfq_processing.run_naming_lab_call",
        lambda _locked: {
            "names": [
                {
                    "object_id": "object-001",
                    "name_en": "Display cabinet",
                    "name_original": "",
                }
            ],
            "duration_seconds": 2.25,
            "model": "test-model",
            "input_tokens": 20,
            "output_tokens": 5,
            "validation": {"accepted": True, "violations": []},
        },
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_detected_object_name_if_unchanged",
        lambda _client, **kwargs: updates.append(kwargs),
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda _client, event: events.append(event),
    )

    result = _run_deferred_naming(
        client=object(),
        detected_objects=detected_objects,
        locked_objects=locked_objects,
        company_id="001",
        run_id="run-001",
        file_name="drawing.pdf",
    )

    assert result == {
        "status": "succeeded",
        "names": {"object-001": "Display cabinet"},
        "naming_seconds": 2.25,
    }
    assert updates[0]["expected_name"] == "Object 1"
    assert updates[0]["object_name"] == "Display cabinet"
    assert events[0]["operation"] == "locked_object_naming_deferred"


def test_file_review_name_is_trimmed_and_saved_immediately(monkeypatch):
    updates = []
    client = object()
    monkeypatch.setattr(
        "use_cases.rfq_processing.get_supabase_client",
        lambda: client,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_detected_object",
        lambda actual_client, **kwargs: updates.append((actual_client, kwargs)),
    )

    saved_name = save_file_review_object_name(
        run_id="run-001",
        object_id="object-001",
        object_name="  Reception desk  ",
    )

    assert saved_name == "Reception desk"
    assert updates == [
        (
            client,
            {
                "run_id": "run-001",
                "object_id": "object-001",
                "values": {"object_name": "Reception desk"},
            },
        )
    ]
