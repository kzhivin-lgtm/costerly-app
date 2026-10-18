from inspect import getsource
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import anthropic
import httpx
import pandas as pd
import pytest

from agents.anthropic_adapter import (
    DEFAULT_CLAUDE_DETECTION_MODEL,
    DetectionVisualRegistryValidationError,
    DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE,
    DETECTION_ORPHAN_DETAIL_RESOLVER_PROMPT_VERSION,
    DETECTION_VISUAL_REGISTRY_PROMPT_VERSION,
    apply_benchmark_run_suffix,
    build_agent_usage_event,
    build_detection_ocr_context,
    build_detection_system_content,
    build_detection_user_text,
    build_uploaded_file_content_block,
    create_claude_message,
    create_claude_message_streamed,
    _validate_orphan_detail_resolutions,
    normalize_detection_identity_fields,
    run_anthropic_detection_agent,
    run_anthropic_detection_registry_agent,
    run_anthropic_detection_visual_map_agent,
    run_anthropic_detection_visual_registry_agent,
)
from agents.ocr_adapter import normalize_mistral_ocr_response
from ui.processing_stage import processing_stage_html
from ui.js_guards import (
    install_company_logo_picker_guard,
    install_upload_interaction_guards,
)
from screens.processing import expected_detection_seconds
from use_cases.rfq_processing import (
    _latest_runtime_timings,
    _normalize_run,
    _ocr_storage_usage,
    _run_deferred_naming,
    _run_optional_ocr,
    save_file_review_object_name,
    save_file_review_run_metadata,
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


class _TimeoutMessages:
    @staticmethod
    def _error():
        return anthropic.APITimeoutError(
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )

    def create(self, **_kwargs):
        raise self._error()

    def stream(self, **_kwargs):
        raise self._error()


class _TimeoutClient:
    messages = _TimeoutMessages()


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


def test_message_timeout_is_not_misreported_as_connection_failure():
    with pytest.raises(RuntimeError, match="timed out") as exc_info:
        create_claude_message(_TimeoutClient(), messages=[])

    assert "connection failed" not in str(exc_info.value).lower()


def test_streamed_message_timeout_is_not_misreported_as_connection_failure():
    with pytest.raises(RuntimeError, match="timed out") as exc_info:
        create_claude_message_streamed(_TimeoutClient(), messages=[])

    assert "connection failed" not in str(exc_info.value).lower()


def test_streamed_message_has_an_optional_wall_clock_limit():
    with patch(
        "agents.anthropic_adapter.time.perf_counter",
        side_effect=[10.0, 71.0],
    ):
        with pytest.raises(RuntimeError, match="60-second limit"):
            create_claude_message_streamed(
                _FakeClient(), messages=[], max_stream_seconds=60.0
            )


def test_streamed_message_emits_first_event_and_first_token_phases():
    phases = []

    create_claude_message_streamed(
        _FakeClient(),
        messages=[],
        on_stream_phase=lambda phase, _elapsed: phases.append(phase),
    )

    assert phases == ["first_event", "first_token"]


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


def test_benchmark_suffix_can_be_unique_per_run(monkeypatch):
    monkeypatch.setenv("BENCHMARK_RUN_SUFFIX", "duplicate-code")
    monkeypatch.setenv("BENCHMARK_UNIQUE_RUN_ID", "true")
    result = {
        "rfq_run": {"run_id": "project_run_001"},
        "detected_objects": [{"run_id": "project_run_001"}],
    }

    suffixed = apply_benchmark_run_suffix(result)

    run_id = suffixed["rfq_run"]["run_id"]
    assert run_id.startswith("project_run_001_duplicate-code_20")
    assert run_id.endswith("Z")
    assert suffixed["detected_objects"][0]["run_id"] == run_id


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


def test_upload_processing_shell_is_scoped_to_the_estimate_upload_screen():
    source = getsource(install_upload_interaction_guards)

    assert "COSTERLY_UPLOAD_INTERACTION_GUARDS_V1_1_11" in source
    assert "function uploadScreenIsActive()" in source
    assert "document.querySelector('.upload-screen-active')" in source
    assert "if (!uploadScreenIsActive()) return;" in source
    assert "if (uploadScreenIsActive() && dropzone && dropHasFiles(event))" in source
    assert "costerly:rfq-upload-selected" in source


def test_upload_screen_uses_a_fresh_widget_identity_for_each_estimate_cycle():
    source = Path("screens/upload.py").read_text()

    assert '"rfq_upload_widget_generation"' in source
    assert 'key=f"rfq_upload_input_{upload_widget_generation}"' in source


def test_rfq_upload_and_processing_emit_distinct_runtime_boundaries():
    upload_source = Path("screens/upload.py").read_text()
    processing_source = Path("screens/processing.py").read_text()

    assert "server.rfq_upload_accepted" in upload_source
    assert "server.rfq_processing_queued" in upload_source
    assert "server.rfq_processing_worker_started" in processing_source


def test_company_logo_change_action_opens_picker_until_replacement_is_pending():
    source = getsource(install_company_logo_picker_guard)

    assert ".st-key-save_company_logo button" in source
    assert ".company-logo-change-mode" in source
    assert ".company-logo-pending" in source
    assert "input[type='file']" in source
    assert "input.click()" in source


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


def test_detection_identity_fields_latinize_russian_project_identifier():
    result = {
        "rfq_run": {"run_id": "run-1", "project_name": "Комсомольская 7"},
        "detected_objects": [],
    }

    normalized = normalize_detection_identity_fields(
        result,
        company_id="001",
        file_name="drawing.pdf",
    )

    assert normalized["rfq_run"]["project_name"] == "Komsomolskaya 7"


def test_detection_normalizes_advisory_file_quality_before_schema_validation():
    result = {
        "rfq_run": {
            "run_id": "run-1",
            "file_quality_level": 5,
            "file_quality_label": "production_ready",
            "file_quality_confidence": 125,
            "status": "intake_parsed",
        },
        "detected_objects": [],
    }

    normalized = normalize_detection_identity_fields(
        result,
        company_id="001",
        file_name="drawing.pdf",
    )

    assert normalized["rfq_run"]["file_quality_level"] == 4
    assert normalized["rfq_run"]["file_quality_label"] == "production_ready"
    assert normalized["rfq_run"]["file_quality_confidence"] == 100.0


def test_locked_evidence_handoff_uses_temperature_zero_and_records_it():
    payload = {
        "rfq_run": {
            "run_id": "run-1", "company_id": "company-1", "project_name": "Project",
            "file_name": "drawing.pdf", "source_type": "pdf", "design_partner": "unknown",
            "client": "unknown", "author": "unknown", "document_date": "unknown",
            "pages_detected": 1, "language": "en", "file_quality_level": 3,
            "file_quality_label": "detailed_drawings", "file_quality_confidence": 90,
            "file_quality_notes": "", "status": "intake_parsed", "created_at": "unknown",
        },
        "detected_objects": [{
            "run_id": "run-1", "company_id": "company-1", "object_id": "object-001",
            "object_name": "Object 1", "quantity": 1, "quantity_explicit": False,
            "review_required": False, "evidence_pages": "1", "approved": False,
            "created_at": "unknown",
            "evidence_page_refs": [{
                "page_number": 1, "source_label": "P1",
                "regions": [{"top_left_x": 1, "top_left_y": 2, "bottom_right_x": 30, "bottom_right_y": 40}],
            }],
        }],
    }
    requested_temperatures = []

    def fake_create(*_args, temperature, **_kwargs):
        requested_temperatures.append(temperature)
        return _Response(), {
            "request_started_at": "2026-10-18T00:00:00+00:00",
            "request_finished_at": "2026-10-18T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        result = run_anthropic_detection_agent(
            file_name="drawing.pdf", company_id="company-1", file_bytes=b"pdf",
            page_images=[b"page"], model="model", locked_registry={"objects": []},
        )

    assert requested_temperatures == [DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE]
    raw_usage = result["_agent_usage"]["raw_usage"]
    assert raw_usage["temperature"] == 0.0
    assert raw_usage["request_fingerprint"]


def test_registry_retries_truncated_structured_json_with_larger_budget():
    visual_map = {
        "visual_groups": [{
            "group_id": "view-001", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
        }],
    }
    registry = {
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "estimation_evidence_pages": [1],
            "visual_group_ids": ["view-001"], "visual_identity": "one cabinet",
            "boundary_basis": "one complete product",
        }],
    }
    requested_budgets = []

    def fake_create(*_args, max_tokens, **_kwargs):
        requested_budgets.append(max_tokens)
        return _Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", side_effect=["{", json.dumps(registry)]),
    ):
        result, usage = run_anthropic_detection_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], visual_map=visual_map, ocr_package=None, model="model",
        )

    assert result == registry
    assert requested_budgets == [5000, 8192]
    assert usage["raw_usage"]["retry_after_truncated_json"] is True


def test_integrated_visual_registry_returns_map_and_locked_objects_in_one_call():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
            "commercial_role": "assembly_view",
        }],
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_group_ids": ["view_a"],
            "visual_identity": "one cabinet", "boundary_basis": "one complete product",
            "merge_proofs": [],
        }],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "cabinet view",
        }],
    }
    requested_budgets = []
    requested_temperatures = []

    def fake_create(*_args, max_tokens, temperature, **_kwargs):
        requested_budgets.append(max_tokens)
        requested_temperatures.append(temperature)
        return _Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert requested_budgets == [8192]
    assert requested_temperatures == [0.0]
    assert visual_map["visual_groups"][0]["group_id"] == "view-001"
    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert registry["objects"][0]["estimation_evidence_pages"] == [1]
    assert usage["operation"] == "rfq_detection_visual_registry"
    assert usage["raw_usage"]["temperature"] == 0.0
    assert usage["raw_usage"]["registry_decision_audit"] == payload


def test_integrated_visual_registry_normalizes_and_persists_pairwise_merge_proofs():
    payload = {
        "visual_groups": [
            {
                "group_id": "elevation", "page_number": 1, "location_hint": "left",
                "visual_description": "sliding door system elevation",
                "representation_kind": "elevation", "commercial_role": "assembly_view",
            },
            {
                "group_id": "plan", "page_number": 1, "location_hint": "right",
                "visual_description": "sliding door system plan",
                "representation_kind": "plan", "commercial_role": "assembly_view",
            },
        ],
        "objects": [{
            "object_id": "object-001", "transport_label": "D01",
            "quantity": 1, "quantity_explicit": True, "identity_pages": [1],
            "visual_group_ids": ["elevation", "plan"],
            "visual_identity": "one door system in elevation and plan",
            "boundary_basis": "matching track and three-leaf sequence",
            "merge_proofs": [{
                "from_group_id": "elevation", "to_group_id": "plan",
                "primary_evidence_type": "matching_topology",
                "secondary_evidence_type": "dimension_transform",
                "evidence_pages": [1],
                "observed_fact": "The plan track length matches the elevation after the axis change.",
                "commercial_inseparability": "Both views show one common track and frame.",
            }],
        }],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "both views show D01",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [group["group_id"] for group in visual_map["visual_groups"]] == [
        "view-001", "view-002",
    ]
    assert registry["objects"][0]["visual_group_ids"] == ["view-001", "view-002"]
    assert usage["raw_usage"]["pairwise_merge_proofs"][0]["from_group_id"] == "view-001"
    assert usage["raw_usage"]["pairwise_merge_proofs"][0]["to_group_id"] == "view-002"


def test_integrated_visual_registry_discards_only_trailing_zero_evidence_orphan():
    payload = {
        "visual_groups": [
            {"group_id": "view_a", "page_number": 1, "location_hint": "upper left", "visual_description": "shelving", "representation_kind": "elevation", "commercial_role": "assembly_view"},
            {"group_id": "view_b", "page_number": 1, "location_hint": "upper right", "visual_description": "door system", "representation_kind": "elevation", "commercial_role": "assembly_view"},
            {"group_id": "view_c", "page_number": 1, "location_hint": "lower", "visual_description": "TV console", "representation_kind": "perspective", "commercial_role": "assembly_view"},
            {"group_id": "detail_d", "page_number": 1, "location_hint": "shelving detail", "visual_description": "component detail", "representation_kind": "detail", "commercial_role": "component_detail"},
        ],
        "objects": [
            {"object_id": "object-001", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["view_a"], "visual_identity": "shelving", "boundary_basis": "one complete product"},
            {"object_id": "object-002", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["view_b"], "visual_identity": "door system", "boundary_basis": "one complete product"},
            {"object_id": "object-003", "transport_label": "Object 3", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["view_c"], "visual_identity": "TV console", "boundary_basis": "one complete product"},
            {"object_id": "object-004", "transport_label": "Object 4", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": [], "visual_identity": "component detail", "boundary_basis": "not a commercial object"},
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001", "object-002", "object-003"],
            "evidence_reason": "the page contains all three complete products",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", return_value=(_Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        })),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [item["object_id"] for item in registry["objects"]] == [
        "object-001", "object-002", "object-003",
    ]
    assert usage["raw_usage"]["discarded_orphan_registry_object_ids"] == ["object-004"]
    assert usage["raw_usage"]["registry_decision_audit"] == payload


def test_integrated_visual_registry_resolves_only_an_unowned_component_detail_candidate():
    primary_payload = {
        "visual_groups": [
            {"group_id": "cabinet", "page_number": 1, "location_hint": "left", "visual_description": "cabinet N76", "representation_kind": "elevation", "commercial_role": "assembly_view"},
            {"group_id": "n76b-plan", "page_number": 2, "location_hint": "top", "visual_description": "N76B plan", "representation_kind": "plan", "commercial_role": "component_detail"},
            {"group_id": "n76b-profile", "page_number": 2, "location_hint": "middle", "visual_description": "N76B profile 345 x 5", "representation_kind": "profile", "commercial_role": "document_context"},
            {"group_id": "n76b-elevation", "page_number": 2, "location_hint": "bottom", "visual_description": "N76B panel elevation 345 x 260", "representation_kind": "elevation", "commercial_role": "document_context"},
        ],
        "objects": [
            {"object_id": "object-001", "transport_label": "N76", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["cabinet"], "visual_identity": "cabinet N76", "boundary_basis": "complete cabinet envelope"},
            {"object_id": "object-002", "transport_label": "N76B", "quantity": 1, "quantity_explicit": False, "identity_pages": [2], "visual_group_ids": [], "visual_identity": "N76B panel", "boundary_basis": "unresolved detail cluster"},
        ],
        "merge_proofs": [],
        "page_coverage": [
            {"page_number": 1, "object_ids": ["object-001"], "evidence_reason": "N76 cabinet"},
            {"page_number": 2, "object_ids": ["object-002"], "evidence_reason": "N76B drawing"},
        ],
    }
    resolver_payload = {
        "resolutions": [{
            "candidate_group_ids": ["view-002"],
            "decision": "promote_to_new_object", "target_object_id": "",
            "transport_label": "N76B", "quantity": 1, "quantity_explicit": False,
            "identity_pages": [2], "visual_identity": "N76B decorative panel assembly",
            "boundary_basis": "The three N76B depictions show one coded panel assembly.",
            "assembly_group_ids": ["view-002", "view-003", "view-004"],
            "merge_proofs": [
                {"from_group_id": "view-002", "to_group_id": "view-003", "primary_evidence_type": "explicit_document_relation", "secondary_evidence_type": "not_required", "evidence_pages": [2], "observed_fact": "Both depictions carry N76B and width 345.", "commercial_inseparability": "They are plan and profile views of one panel assembly."},
                {"from_group_id": "view-003", "to_group_id": "view-004", "primary_evidence_type": "explicit_document_relation", "secondary_evidence_type": "not_required", "evidence_pages": [2], "observed_fact": "The profile and elevation carry the same N76B code.", "commercial_inseparability": "They are complementary views of one panel assembly."},
            ],
            "attachment_evidence": [],
            "resolution_basis": "N76B has its own code and coherent dimensions, with no positive link to N76.",
        }],
    }
    requests: list[dict] = []

    def fake_create(*_args, **kwargs):
        requests.append(kwargs)
        return _Response(), {
            "request_started_at": "2026-10-18T00:00:00+00:00",
            "request_finished_at": "2026-10-18T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch(
            "agents.anthropic_adapter.extract_text_from_claude_response",
            side_effect=[json.dumps(primary_payload), json.dumps(resolver_payload)],
        ),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="n76b.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package={
                "pages": [{"page_number": 2, "markdown": "N76B"}],
            }, model="model",
        )

    assert len(requests) == 2
    assert [item["transport_label"] for item in registry["objects"]] == ["N76", "N76B"]
    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert registry["objects"][1]["visual_group_ids"] == ["view-002", "view-003", "view-004"]
    assert registry["objects"][1]["estimation_evidence_pages"] == [2]
    assert all(
        group["commercial_role"] == "assembly_view"
        for group in visual_map["visual_groups"][1:]
    )
    assert usage["raw_usage"]["orphan_detail_resolver"]["candidate_group_ids"] == [
        "view-002",
    ]
    assert usage["raw_usage"]["orphan_detail_resolver"]["eligible_assembly_group_ids"] == [
        "view-002", "view-003", "view-004",
    ]
    assert usage["_additional_usage_events"][0]["raw_usage"]["resolver_page_numbers"] == [2]
    assert usage["_additional_usage_events"][0]["prompt_version"] == (
        DETECTION_ORPHAN_DETAIL_RESOLVER_PROMPT_VERSION
    )
    resolver_request = next(
        block["text"]
        for block in requests[1]["messages"][0]["content"]
        if (
            isinstance(block, dict)
            and block.get("type") == "text"
            and "Conditional orphan-detail resolution input" in block.get("text", "")
        )
    )
    assert '"provisional_candidates"' in resolver_request
    assert '"provisional_objects"' not in resolver_request
    assert '"known_objects_for_comparison"' in resolver_request
    assert '"attachable_existing_objects":[]' in resolver_request
    assert '"object_id":"object-001"' not in resolver_request
    assert '"object_id":"object-002"' not in resolver_request


def test_orphan_detail_resolver_cannot_promote_a_view_already_owned_by_registry():
    context = {
        "candidate_group_ids": ["view-002"],
        "page_scope_group_ids": ["view-001", "view-002", "view-003"],
        "eligible_assembly_group_ids": ["view-002", "view-003"],
        "page_scope_groups": [
            {"group_id": "view-001", "page_number": 2},
            {"group_id": "view-002", "page_number": 2},
            {"group_id": "view-003", "page_number": 2},
        ],
        "existing_objects": [{"object_id": "object-001"}],
    }
    payload = {"resolutions": [{
        "candidate_group_ids": ["view-002"],
        "decision": "promote_to_new_object", "target_object_id": "",
        "transport_label": "N76B", "quantity": 1, "quantity_explicit": False,
        "identity_pages": [2], "visual_identity": "N76B panel",
        "boundary_basis": "Independent dimensioned product.",
        "assembly_group_ids": ["view-001", "view-002", "view-003"],
        "merge_proofs": [], "attachment_evidence": [],
        "resolution_basis": "Own code and dimensions.",
    }]}

    with pytest.raises(ValueError, match="assembly groups are invalid"):
        _validate_orphan_detail_resolutions(payload, context=context, page_count=2)


def test_orphan_detail_resolver_rejects_attachment_without_direct_relation_evidence():
    context = {
        "candidate_group_ids": ["view-002"],
        "page_scope_group_ids": ["view-002"],
        "eligible_assembly_group_ids": ["view-002"],
        "page_scope_groups": [{"group_id": "view-002", "page_number": 2}],
        "existing_objects": [{"object_id": "object-001"}],
    }
    payload = {"resolutions": [{
        "candidate_group_ids": ["view-002"],
        "decision": "attach_to_existing_object", "target_object_id": "object-001",
        "transport_label": "", "quantity": 0, "quantity_explicit": False,
        "identity_pages": [], "visual_identity": "", "boundary_basis": "",
        "assembly_group_ids": [], "merge_proofs": [], "attachment_evidence": [],
        "resolution_basis": "The codes look related and the dimensions are similar.",
    }]}

    with pytest.raises(ValueError, match="requires direct relation evidence"):
        _validate_orphan_detail_resolutions(payload, context=context, page_count=2)


def test_orphan_detail_resolver_rejects_code_similarity_without_literal_target_code():
    context = {
        "candidate_group_ids": ["view-002"],
        "page_scope_group_ids": ["view-002"],
        "eligible_assembly_group_ids": ["view-002"],
        "page_scope_groups": [{"group_id": "view-002", "page_number": 2}],
        "existing_objects": [{"object_id": "object-001", "transport_label": "N76"}],
        "provisional_objects": [{"object_id": "object-002", "transport_label": "N76B", "identity_pages": [2]}],
        "candidate_page_ocr_text": {2: "Drawing N76B, scale 1:25"},
    }
    payload = {"resolutions": [{
        "candidate_group_ids": ["view-002"],
        "decision": "attach_to_existing_object", "target_object_id": "object-001",
        "transport_label": "", "quantity": 0, "quantity_explicit": False,
        "identity_pages": [], "visual_identity": "", "boundary_basis": "",
        "assembly_group_ids": [], "merge_proofs": [],
        "attachment_evidence": [{
            "relation_type": "explicit_callout", "evidence_pages": [2],
            "observed_fact": "N76B is described as a variant of N76.",
        }],
        "resolution_basis": "The codes look related.",
    }]}

    with pytest.raises(ValueError, match="no literal target-code evidence"):
        _validate_orphan_detail_resolutions(payload, context=context, page_count=2)


def test_integrated_visual_registry_attaches_an_unowned_detail_without_changing_owner_boundary():
    primary_payload = {
        "visual_groups": [
            {"group_id": "cabinet", "page_number": 1, "location_hint": "left", "visual_description": "cabinet", "representation_kind": "elevation", "commercial_role": "assembly_view"},
            {"group_id": "detail", "page_number": 2, "location_hint": "right", "visual_description": "cabinet hinge detail", "representation_kind": "detail", "commercial_role": "component_detail"},
        ],
        "objects": [{"object_id": "object-001", "transport_label": "N76", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["cabinet"], "visual_identity": "cabinet", "boundary_basis": "complete cabinet envelope"}],
        "merge_proofs": [],
        "page_coverage": [
            {"page_number": 1, "object_ids": ["object-001"], "evidence_reason": "cabinet"},
            {"page_number": 2, "object_ids": [], "evidence_reason": "unassigned hinge detail"},
        ],
    }
    resolver_payload = {"resolutions": [{
        "candidate_group_ids": ["view-002"], "decision": "attach_to_existing_object",
        "target_object_id": "object-001", "transport_label": "", "quantity": 0,
        "quantity_explicit": False, "identity_pages": [], "visual_identity": "",
        "boundary_basis": "", "assembly_group_ids": [], "merge_proofs": [],
        "attachment_evidence": [{
            "relation_type": "explicit_callout", "evidence_pages": [2],
            "observed_fact": "The hinge callout explicitly names N76.",
        }],
        "resolution_basis": "The hinge detail is explicitly for the N76 cabinet.",
    }]}

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", return_value=(_Response(), {
            "request_started_at": "2026-10-18T00:00:00+00:00",
            "request_finished_at": "2026-10-18T00:00:01+00:00",
        })),
        patch(
            "agents.anthropic_adapter.extract_text_from_claude_response",
            side_effect=[json.dumps(primary_payload), json.dumps(resolver_payload)],
        ),
    ):
        visual_map, registry, _ = run_anthropic_detection_visual_registry_agent(
            file_name="detail.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package=None, model="model",
        )

    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert registry["objects"][0]["estimation_evidence_pages"] == [1, 2]
    assert visual_map["visual_groups"][1]["commercial_role"] == "component_detail"


def test_integrated_visual_registry_keeps_empty_group_object_with_evidence_as_error():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "cabinet", "representation_kind": "elevation",
            "commercial_role": "assembly_view",
        }],
        "objects": [
            {"object_id": "object-001", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": ["view_a"], "visual_identity": "cabinet", "boundary_basis": "one complete product"},
            {"object_id": "object-002", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_group_ids": [], "visual_identity": "unresolved", "boundary_basis": "unresolved"},
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001", "object-002"],
            "evidence_reason": "both are claimed on this page",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", return_value=(_Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        })),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
        pytest.raises(DetectionVisualRegistryValidationError, match="registry visual groups are invalid"),
    ):
        run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )


def test_registry_uses_the_same_atomic_visual_group_contract_for_all_models():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
            "commercial_role": "assembly_view",
        }],
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_group_ids": ["view_a"], "visual_identity": "one cabinet",
            "boundary_basis": "one complete product",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "cabinet view",
        }],
    }
    prompts: list[str] = []

    def fake_system_content(*, prompt):
        prompts.append(prompt)
        return prompt

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
        patch("agents.anthropic_adapter.build_detection_system_content", side_effect=fake_system_content),
    ):
        _, _, haiku_usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None,
            model=DEFAULT_CLAUDE_DETECTION_MODEL,
        )
        _, _, sonnet_usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None,
            model="claude-sonnet-4-6",
        )

    assert haiku_usage["prompt_version"] == DETECTION_VISUAL_REGISTRY_PROMPT_VERSION
    assert sonnet_usage["prompt_version"] == DETECTION_VISUAL_REGISTRY_PROMPT_VERSION
    assert prompts[0] == prompts[1]
    assert "related_group_ids" not in prompts[0]


def test_integrated_visual_registry_requires_page_coverage_for_every_uploaded_page():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
            "commercial_role": "assembly_view",
        }],
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_group_ids": ["view_a"], "visual_identity": "one cabinet",
            "boundary_basis": "one complete product",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "cabinet view",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
        pytest.raises(RuntimeError, match="account for every uploaded page exactly once"),
    ):
        run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package=None, model="model",
        )


def test_integrated_visual_registry_reconciles_missing_object_on_only_page():
    payload = {
        "visual_groups": [
            {
                "group_id": "view_a", "page_number": 1, "location_hint": "left",
                "visual_description": "cabinet", "representation_kind": "perspective",
                "commercial_role": "assembly_view",
            },
            {
                "group_id": "view_b", "page_number": 1, "location_hint": "right",
                "visual_description": "counter", "representation_kind": "perspective",
                "commercial_role": "assembly_view",
            },
        ],
        "objects": [
            {
                "object_id": "object-001", "transport_label": "Object 1",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_group_ids": ["view_a"], "visual_identity": "cabinet",
                "boundary_basis": "separate cabinet",
            },
            {
                "object_id": "object-002", "transport_label": "Object 2",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_group_ids": ["view_b"], "visual_identity": "counter",
                "boundary_basis": "separate counter",
            },
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "cabinet drawing",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [item["estimation_evidence_pages"] for item in registry["objects"]] == [[1], [1]]
    assert usage["raw_usage"]["single_page_coverage_reconciled_object_ids"] == ["object-002"]


def test_integrated_visual_registry_validation_failure_carries_structured_audit():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "cabinet", "representation_kind": "perspective",
            "commercial_role": "assembly_view",
        }],
        "objects": [{
            "object_id": "object-001", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_group_ids": ["view_a"], "visual_identity": "cabinet",
            "boundary_basis": "one cabinet",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001"],
            "evidence_reason": "cabinet drawing",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
        pytest.raises(DetectionVisualRegistryValidationError) as raised,
    ):
        run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package=None, model="model",
        )

    event = raised.value.usage_event
    assert event["status"] == "failed"
    assert event["run_id"] is None
    assert event["error_message"] == "page coverage must account for every uploaded page exactly once"
    assert event["raw_usage"]["registry_decision_audit"] == payload


def test_integrated_visual_registry_persists_duplicate_group_ownership_details():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "center",
            "visual_description": "two adjacent cabinets", "representation_kind": "elevation",
            "commercial_role": "assembly_view",
        }],
        "objects": [
            {
                "object_id": "object-001", "transport_label": "Object 1",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_group_ids": ["view_a"], "visual_identity": "first cabinet",
                "boundary_basis": "first complete envelope",
            },
            {
                "object_id": "object-002", "transport_label": "Object 2",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_group_ids": ["view_a"], "visual_identity": "second cabinet",
                "boundary_basis": "second complete envelope",
            },
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "object_ids": ["object-001", "object-002"],
            "evidence_reason": "shared elevation contains both cabinets",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(payload)),
        pytest.raises(DetectionVisualRegistryValidationError) as raised,
    ):
        run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    event = raised.value.usage_event
    assert event["raw_usage"]["registry_decision_audit"] == payload
    assert event["raw_usage"]["validation_details"] == {
        "duplicate_visual_group_owners": {
            "view-001": ["object-001", "object-002"],
        },
    }


def test_visual_map_retries_truncated_structured_json_with_larger_budget():
    visual_map = {
        "visual_groups": [{
            "group_id": "view-001", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
        }],
    }
    requested_budgets = []

    def fake_create(*_args, max_tokens, **_kwargs):
        requested_budgets.append(max_tokens)
        return _Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", side_effect=fake_create),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", side_effect=["{", json.dumps(visual_map)]),
    ):
        result, usage = run_anthropic_detection_visual_map_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert result == visual_map
    assert requested_budgets == [5000, 8192]
    assert usage["raw_usage"]["retry_after_truncated_json"] is True


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
        "use_cases.rfq_processing.run_mistral_document_evidence_ocr",
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
    project_updates = []
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
        lambda _client, **kwargs: updates.append(kwargs) or True,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_run_project_name_if_unchanged",
        lambda _client, **kwargs: project_updates.append(kwargs) or True,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda _client, event: events.append(event),
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.fetch_rfq_detected_object_names",
        lambda _client, _run_id: [
            {"object_id": "object-001", "object_name": "Display cabinet"},
        ],
    )

    result = _run_deferred_naming(
        client=object(),
        detected_objects=detected_objects,
        locked_objects=locked_objects,
        company_id="001",
        run_id="run-001",
        file_name="drawing.pdf",
        provisional_project_name="25 items",
    )

    assert result == {
        "status": "succeeded",
        "names": {"object-001": "Display cabinet"},
        "naming_seconds": 2.25,
        "token_cost": 0.000045,
    }
    assert updates[0]["expected_name"] == "Object 1"
    assert updates[0]["object_name"] == "Display cabinet"
    assert project_updates == [{
        "run_id": "run-001",
        "expected_project_name": "25 items",
        "project_name": "Display cabinet",
    }]
    assert events[0]["operation"] == "locked_object_naming_deferred"
    assert events[0]["raw_usage"]["names"] == {"object-001": "Display cabinet"}
    assert events[0]["raw_usage"]["persistence_audit"]["readback_mismatches"] == []


def test_deferred_naming_records_readback_mismatch_as_failure(monkeypatch):
    events = []
    detected_objects = [{"object_id": "object-003", "object_name": "Object 3"}]
    locked_objects = [{"object_id": "object-003", "current_name": "Object 3"}]
    monkeypatch.setattr(
        "use_cases.rfq_processing.run_naming_lab_call",
        lambda _locked: {
            "names": [{"object_id": "object-003", "name_en": "TV console", "name_original": ""}],
            "duration_seconds": 1.0,
            "model": "test-model",
            "input_tokens": 1,
            "output_tokens": 1,
            "validation": {"accepted": True, "violations": []},
        },
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_detected_object_name_if_unchanged",
        lambda _client, **_kwargs: True,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.fetch_rfq_detected_object_names",
        lambda _client, _run_id: [
            {"object_id": "object-003", "object_name": "Object 3"},
        ],
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
        run_id="run-003",
        file_name="drawing.pdf",
    )

    assert result["status"] == "failed"
    assert "object-003" in result["error"]
    audit = events[0]["raw_usage"]["persistence_audit"]
    assert audit["readback_mismatches"] == [{
        "object_id": "object-003",
        "requested_name": "TV console",
        "readback_name": "Object 3",
    }]


def test_deferred_naming_records_failure(monkeypatch):
    events = []
    monkeypatch.setattr(
        "use_cases.rfq_processing.run_naming_lab_call",
        lambda _locked: (_ for _ in ()).throw(RuntimeError("provider failed")),
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.insert_agent_usage_event",
        lambda _client, event: events.append(event),
    )

    result = _run_deferred_naming(
        client=object(),
        detected_objects=[],
        locked_objects=[],
        company_id="001",
        run_id="run-001",
        file_name="drawing.pdf",
    )

    assert result["status"] == "failed"
    assert result["error"] == "provider failed"
    assert events[0]["status"] == "failed"
    assert events[0]["raw_usage"]["error"] == "provider failed"


def test_file_review_timings_restore_deferred_naming_duration_and_cycle_tc():
    usage = pd.DataFrame([
        {
            "operation": "rfq_processing_cycle", "status": "succeeded",
            "duration_seconds": None,
            "raw_usage": json.dumps({
                "duration_seconds": 12.3, "ocr_seconds": 1.2,
                "detection_seconds": 9.1, "naming_seconds": 0.0,
            }),
            "total_cost_usd": None,
        },
        {
            "operation": "rfq_detection", "status": "succeeded",
            "duration_seconds": None,
            "raw_usage": {"duration_seconds": 9.1},
            "total_cost_usd": "0.010311",
        },
        {
            "operation": "locked_object_naming_deferred", "status": "succeeded",
            "duration_seconds": None,
            "raw_usage": json.dumps({"duration_seconds": 1.557}),
            "total_cost_usd": "0.003294",
        },
    ])

    assert _latest_runtime_timings(usage) == {
        "ocr_seconds": 1.2,
        "detection_seconds": 9.1,
        "naming_seconds": 1.557,
        "token_cost": 0.013605,
        "total_seconds": 12.3,
    }


def test_file_review_name_is_trimmed_and_saved_immediately(monkeypatch):
    updates = []
    audits = []
    client = object()
    monkeypatch.setattr(
        "use_cases.rfq_processing.get_supabase_client",
        lambda: client,
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_detected_object",
        lambda actual_client, **kwargs: updates.append((actual_client, kwargs)),
    )
    monkeypatch.setattr(
        "use_cases.rfq_processing._queue_object_name_write_audit",
        lambda **kwargs: audits.append(kwargs),
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
    assert audits == [{
        "company_id": "001",
        "run_id": "run-001",
        "object_id": "object-001",
        "expected_name": None,
        "requested_name": "Reception desk",
        "write_source": "file_review_legacy_direct",
    }]


def test_file_review_project_metadata_is_trimmed_and_saved_without_catalog_writes(monkeypatch):
    updates = []
    client = object()
    monkeypatch.setattr("use_cases.rfq_processing.get_supabase_client", lambda: client)
    monkeypatch.setattr(
        "use_cases.rfq_processing.update_rfq_run",
        lambda actual_client, **kwargs: updates.append((actual_client, kwargs)),
    )

    saved = save_file_review_run_metadata(
        run_id="run-001",
        values={
            "project_name": "  Restaurant Olen  ",
            "partner": "  Bureau Yolochka  ",
            "client": "  Restaurant Group LLC  ",
        },
    )

    assert saved == {
        "project_name": "Restaurant Olen",
        "partner": "Bureau Yolochka",
        "client": "Restaurant Group LLC",
    }
    assert updates == [
        (
            client,
            {
                "run_id": "run-001",
                "values": {
                    "project_name": "Restaurant Olen",
                    "design_partner": "Bureau Yolochka",
                    "client": "Restaurant Group LLC",
                },
            },
        )
    ]


def test_file_review_project_metadata_rejects_unknown_fields_and_empty_values(monkeypatch):
    monkeypatch.setattr("use_cases.rfq_processing.get_supabase_client", lambda: object())

    with pytest.raises(ValueError, match="Project Name cannot be empty"):
        save_file_review_run_metadata(
            run_id="run-001",
            values={"project_name": "  ", "untrusted": "ignored"},
        )

    with pytest.raises(ValueError, match="No editable"):
        save_file_review_run_metadata(
            run_id="run-001",
            values={"untrusted": "ignored"},
        )
