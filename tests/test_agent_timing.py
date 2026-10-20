import copy
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
    _apply_reference_root_suffixes,
    DEFAULT_CLAUDE_DETECTION_MODEL,
    DetectionVisualRegistryValidationError,
    DETECTION_LOCKED_EVIDENCE_HANDOFF_TEMPERATURE,
    DETECTION_VISUAL_REGISTRY_PROMPT_VERSION,
    apply_benchmark_run_suffix,
    build_agent_usage_event,
    build_detection_ocr_context,
    build_detection_system_content,
    build_detection_user_text,
    build_uploaded_file_content_block,
    create_claude_message,
    create_claude_message_streamed,
    extract_detection_document_dimension_unit_profile,
    extract_detection_page_drawing_codes,
    normalize_detection_identity_fields,
    run_anthropic_detection_agent,
    run_anthropic_detection_registry_agent,
    run_anthropic_detection_visual_map_agent,
    run_anthropic_detection_visual_registry_agent,
)
from agents.schemas.detection_registry_schema import (
    REFERENCE_RELATIONSHIP,
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


def _visual_registry_payload(payload):
    """Upgrade legacy Registry fixtures to the V4.44 extraction contract."""
    if not isinstance(payload, dict) or "visual_groups" not in payload:
        return payload
    groups = copy.deepcopy(payload["visual_groups"])
    non_object_kinds = {
        "floor_plan", "title_block", "title_page", "cover", "cover_page", "legend",
    }
    classifications = []
    for index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            continue
        group.setdefault("bbox", {
            "top_left_x": index * 10,
            "top_left_y": 10,
            "bottom_right_x": index * 10 + 5,
            "bottom_right_y": 20,
        })
        is_document_context = group.get("representation_kind") in non_object_kinds
        evidence_class = group.pop(
            "evidence_class",
            "document_context" if is_document_context else "object_evidence",
        )
        classification_reason = group.pop(
            "classification_reason",
            "Generic page context is not object-specific Evidence."
            if is_document_context
            else "The depiction directly shows a fabricated object or its construction.",
        )
        classifications.append({
            "group_id": group["group_id"], "evidence_class": evidence_class,
            "classification_reason": classification_reason,
        })
    inventory = payload.get("dimension_inventory")
    if not isinstance(inventory, list):
        inventory = [
            {"group_id": item["group_id"], "envelope_chains": []}
            for item in classifications
            if item["evidence_class"] == "object_evidence"
        ]
    for row in inventory:
        for chain in row.get("envelope_chains") or []:
            chain.setdefault("source_fact_ids", [])
    return {
        "visual_groups": groups,
        "classifications": classifications,
        "evidence_attributions": [
            {"group_id": item["group_id"], "source_fact_ids": []}
            for item in classifications
        ],
        "dimension_inventory": inventory,
    }


def test_document_dimension_unit_profile_requires_one_explicit_unit_across_document():
    profile = extract_detection_document_dimension_unit_profile({
        "pages": [
            {"page_number": 1, "blocks": [{"content": "H=260 ס\"מ; panel thickness 18 mm"}]},
            {"page_number": 2, "images": [{"image_annotation": {"text": "W=331 cm"}}]},
        ],
    })

    assert profile == {
        "unit": "cm",
        "status": "one_explicit_document_unit",
        "evidence_pages": [1, 2],
    }

    conflicting_profile = extract_detection_document_dimension_unit_profile({
        "pages": [
            {"page_number": 1, "blocks": [{"content": "H=260 cm"}]},
            {"page_number": 2, "blocks": [{"content": "W=331 mm"}]},
        ],
    })

    assert conflicting_profile["unit"] == "unknown"
    assert conflicting_profile["status"] == "conflicting_explicit_document_units"


def test_title_block_drawing_code_extractor_accepts_only_one_explicit_code_per_page():
    codes = extract_detection_page_drawing_codes({
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {"type": "table", "content": (
                        "<table><tr><td>DRAWING NAME</td><td>N57</td></tr></table>"
                    )},
                    {"type": "text", "content": "Component label VEN-01"},
                ],
            },
            {
                "page_number": 2,
                "blocks": [{"type": "table", "content": (
                    "<table><tr><td>DRAWING NAME</td><td>N76B</td></tr></table>"
                )}],
            },
            {
                "page_number": 3,
                "blocks": [{"type": "table", "content": (
                    "<table>DRAWING NAME N57 N58</table>"
                )}],
            },
        ],
    })

    assert codes == {1: "N57", 2: "N76B"}


def test_shared_reference_splits_one_author_root_into_deterministic_child_codes():
    objects = [
        {"object_id": "object-001", "transport_label": "N57", "visual_group_ids": ["view-002"]},
        {"object_id": "object-002", "transport_label": "Cabinet assembly N57", "visual_group_ids": ["view-003"]},
        {"object_id": "object-003", "transport_label": "N57", "visual_group_ids": ["view-004"]},
    ]

    result = _apply_reference_root_suffixes(
        objects,
        proof_components=[["view-002"], ["view-003"], ["view-004"]],
        reference_links=[
            {"group_id_a": "view-001", "group_id_b": "view-002"},
            {"group_id_a": "view-001", "group_id_b": "view-003"},
            {"group_id_a": "view-001", "group_id_b": "view-004"},
        ],
        shared_reference_group_ids={"view-001"},
    )

    assert [item["transport_label"] for item in result] == [
        "N57A", "N57B", "N57C",
    ]


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
        }],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "one cabinet", "boundary_basis": "one complete product",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert requested_budgets == [12288]
    assert requested_temperatures == [0.0]
    assert visual_map["visual_groups"][0]["group_id"] == "view-001"
    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert registry["objects"][0]["estimation_evidence_pages"] == [1]
    assert usage["operation"] == "rfq_detection_visual_registry"
    assert usage["raw_usage"]["temperature"] == 0.0
    assert usage["raw_usage"]["registry_decision_audit"] == _visual_registry_payload(payload)
    assert usage["raw_usage"]["classification_decisions"] == [{
        "group_id": "view_a",
        "page_number": 1,
        "evidence_class": "object_evidence",
        "representation_kind": "perspective",
        "classification_reason": "The depiction directly shows a fabricated object or its construction.",
    }]


def test_visual_registry_materializes_view_package_from_immutable_source_fact():
    payload = _visual_registry_payload({
        "visual_groups": [{
            "group_id": "cabinet", "page_number": 1, "location_hint": "center",
            "visual_description": "cabinet elevation", "representation_kind": "elevation",
        }],
    })
    payload["evidence_attributions"] = [{
        "group_id": "cabinet", "source_fact_ids": ["SF00001"],
    }]
    payload["dimension_inventory"] = [{
        "group_id": "cabinet", "envelope_chains": [{
            "chain_id": "cabinet-width", "axis": "horizontal", "segments": [],
            "direct_total": "358", "source_fact_ids": ["SF00001"],
        }],
    }]
    ocr_package = {"evidence": {"text_blocks": [{
        "page_number": 1, "source": "native_pdf_text",
        "bbox": {"top_left_x": 10, "top_left_y": 20, "bottom_right_x": 40, "bottom_right_y": 30},
        "text": "358",
    }]}}

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
            page_images=[b"page"], regions=[], ocr_package=ocr_package, model="model",
        )

    package = usage["raw_usage"]["view_evidence_packages"][0]
    assert package["source_fact_ids"] == ["SF00001"]
    assert package["source_facts"][0]["text"] == "358"
    assert package["bbox"] == {
        "top_left_x": 10, "top_left_y": 10,
        "bottom_right_x": 15, "bottom_right_y": 20,
    }
    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]


def test_integrated_visual_registry_uses_two_literal_overall_dimensions_to_merge():
    payload = {
        "visual_groups": [
            {
                "group_id": "elevation", "page_number": 1, "location_hint": "left",
                "visual_description": "sliding door system elevation",
                "representation_kind": "elevation",
            },
            {
                "group_id": "plan", "page_number": 1, "location_hint": "right",
                "visual_description": "sliding door system plan",
                "representation_kind": "plan",
            },
        ],
        "objects": [{
            "component_anchor_group_id": "elevation", "transport_label": "D01",
            "quantity": 1, "quantity_explicit": True, "identity_pages": [1],
            "visual_identity": "one door system in elevation and plan",
            "boundary_basis": "matching track and three-leaf sequence",
        }],
        "merge_proofs": [{
            "group_id_a": "elevation", "group_id_b": "plan",
            "relationship": "same_object_view",
            "evidence_facts": [
                {"evidence_type": "dimension_transform", "evidence_pages": [1], "observation": "The plan track length matches the elevation after the axis change."},
                {"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "Both views show the same three-leaf track sequence."},
            ],
            "commercial_inseparability": "Both views show one common track and frame.",
        }],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["elevation"],
            "evidence_reason": "both views show D01",
        }],
    }

    response_payload = _visual_registry_payload(payload)
    response_payload["dimension_inventory"] = [
        {"group_id": "elevation", "envelope_chains": [
                {"chain_id": "e-h", "axis": "horizontal", "segments": [], "direct_total": "1200", "source_fact_ids": []},
                {"chain_id": "e-v", "axis": "vertical", "segments": [], "direct_total": "2400", "source_fact_ids": []},
        ]},
        {"group_id": "plan", "envelope_chains": [
                {"chain_id": "p-h", "axis": "horizontal", "segments": [], "direct_total": "1200", "source_fact_ids": []},
                {"chain_id": "p-v", "axis": "vertical", "segments": [], "direct_total": "2400", "source_fact_ids": []},
        ]},
    ]

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(response_payload)),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [group["group_id"] for group in visual_map["visual_groups"]] == [
        "view-001", "view-002",
    ]
    assert registry["objects"][0]["visual_group_ids"] == ["view-001", "view-002"]
    assert usage["raw_usage"]["accepted_merge_edges"][0]["group_id_a"] == "view-001"
    assert usage["raw_usage"]["accepted_merge_edges"][0]["group_id_b"] == "view-002"
    assert usage["raw_usage"]["dimension_inventory_valid"] is True
    assert usage["raw_usage"]["dimension_inventory_group_count"] == 2
    assert usage["raw_usage"]["proof_graph_components"] == [{
        "canonical_anchor_group_id": "view-001",
        "visual_group_ids": ["view-001", "view-002"],
    }]


def test_integrated_visual_registry_keeps_upload_actionable_when_dimension_index_is_invalid():
    payload = _visual_registry_payload({
        "visual_groups": [
            {"group_id": "left", "page_number": 1, "location_hint": "left", "visual_description": "cabinet elevation", "representation_kind": "elevation"},
            {"group_id": "right", "page_number": 1, "location_hint": "right", "visual_description": "cabinet section", "representation_kind": "section"},
        ],
        "objects": [{
            "component_anchor_group_id": "left", "transport_label": "N56",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "cabinet", "boundary_basis": "one cabinet",
        }],
        "merge_proofs": [{
            "group_id_a": "left", "group_id_b": "right",
            "relationship": "same_object_view",
            "evidence_facts": [{
                "evidence_type": "explicit_document_relation", "evidence_pages": [1],
                "observation": "N56 labels both views.",
            }],
            "commercial_inseparability": "Both views identify N56.",
        }],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["left"],
            "evidence_reason": "cabinet views",
        }],
    })
    payload["dimension_inventory"] = []

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

    assert [item["visual_group_ids"] for item in registry["objects"]] == [
        ["view-001"], ["view-002"],
    ]
    assert usage["raw_usage"]["dimension_inventory_valid"] is False
    assert "must account for every visual group" in usage["raw_usage"]["dimension_inventory_error"]


def test_integrated_visual_registry_keeps_title_code_as_label_but_not_graph_edge():
    payload = {
        "visual_groups": [
            {"group_id": "overview", "page_number": 1, "location_hint": "upper", "visual_description": "kitchen, island and cabinet together", "representation_kind": "plan"},
            {"group_id": "kitchen", "page_number": 1, "location_hint": "lower left", "visual_description": "dedicated kitchen elevation", "representation_kind": "elevation"},
            {"group_id": "island", "page_number": 1, "location_hint": "lower center", "visual_description": "dedicated island elevation", "representation_kind": "elevation"},
            {"group_id": "cabinet", "page_number": 1, "location_hint": "lower right", "visual_description": "dedicated cabinet elevation", "representation_kind": "elevation"},
        ],
        "objects": [
            {"component_anchor_group_id": "kitchen", "transport_label": "N57", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_identity": "kitchen", "boundary_basis": "dedicated kitchen view"},
            {"component_anchor_group_id": "island", "transport_label": "N57", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_identity": "island", "boundary_basis": "dedicated island view"},
            {"component_anchor_group_id": "cabinet", "transport_label": "N57", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_identity": "cabinet", "boundary_basis": "dedicated cabinet view"},
        ],
        "proof_edges": [
            {"group_id_a": "kitchen", "group_id_b": "overview", "relationship": "reference_link", "evidence_facts": [{"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "Overview visibly locates the kitchen."}], "commercial_inseparability": "Shared overview reference, not a merge."},
            {"group_id_a": "island", "group_id_b": "overview", "relationship": "reference_link", "evidence_facts": [{"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "Overview visibly locates the island."}], "commercial_inseparability": "Shared overview reference, not a merge."},
            {"group_id_a": "cabinet", "group_id_b": "overview", "relationship": "reference_link", "evidence_facts": [{"evidence_type": "matching_topology", "evidence_pages": [1], "observation": "Overview visibly locates the cabinet."}], "commercial_inseparability": "Shared overview reference, not a merge."},
        ],
        "page_coverage": [{
            "page_number": 1,
            "component_anchor_group_ids": ["kitchen", "island", "cabinet"],
            "evidence_reason": "The composite overview and dedicated views inform all three products.",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", return_value=(_Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        })),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package={"pages": [{
                "page_number": 1,
                "blocks": [{"type": "table", "content": "<table>DRAWING NAME N57</table>"}],
            }]}, model="model",
        )

    assert [item["transport_label"] for item in registry["objects"]] == [
        "N57", "N57", "N57", "N57",
    ]
    assert [item["visual_group_ids"] for item in registry["objects"]] == [
        ["view-001"], ["view-002"], ["view-003"], ["view-004"],
    ]
    assert usage["raw_usage"]["reference_link_count"] == 0
    assert usage["raw_usage"]["dimension_graph_audit"]["page_drawing_codes"] == {"1": "N57"}
    assert usage["raw_usage"]["dimension_graph_audit"]["source_root_merge_edge_count"] == 0
    assert usage["raw_usage"]["registry_graph_review_required_object_ids"] == [
        "object-001", "object-002", "object-003", "object-004",
    ]
    assert usage["raw_usage"]["unassigned_object_evidence_group_count"] == 0


def test_integrated_visual_registry_does_not_accept_model_package_metadata():
    payload = {
        "visual_groups": [
            {"group_id": "view_a", "page_number": 1, "location_hint": "upper left", "visual_description": "shelving", "representation_kind": "elevation"},
        ],
        "objects": [
            {"component_anchor_group_id": "view_a", "transport_label": "Object 1", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_identity": "shelving", "boundary_basis": "one complete product"},
            {"component_anchor_group_id": "view_a", "transport_label": "Object 2", "quantity": 1, "quantity_explicit": False, "identity_pages": [1], "visual_identity": "unresolved", "boundary_basis": "unresolved"},
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )
    assert [item["transport_label"] for item in registry["objects"]] == ["Unlabelled"]
    assert usage["raw_usage"]["registry_metadata_fallback_object_ids"] == ["object-001"]
    assert usage["raw_usage"]["registry_metadata_audit"]["discarded_metadata_rows"] == []


def test_integrated_visual_registry_keeps_unproved_group_as_review_fallback():
    payload = {
        "visual_groups": [
            {"group_id": "view_a", "page_number": 1, "location_hint": "left", "visual_description": "cabinet elevation", "representation_kind": "elevation"},
            {"group_id": "view_b", "page_number": 1, "location_hint": "right", "visual_description": "cabinet section", "representation_kind": "section"},
        ],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "N76B",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "cabinet", "boundary_basis": "claimed one cabinet",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
            "evidence_reason": "cabinet elevation",
        }],
    }

    with (
        patch("agents.anthropic_adapter.get_secret", return_value="model"),
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch("agents.anthropic_adapter.create_claude_message_streamed", return_value=(_Response(), {
            "request_started_at": "2026-10-16T00:00:00+00:00",
            "request_finished_at": "2026-10-16T00:00:01+00:00",
        })),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )
    assert [item["visual_group_ids"] for item in registry["objects"]] == [
        ["view-001"], ["view-002"],
    ]
    assert [item["transport_label"] for item in registry["objects"]] == [
        "Unlabelled", "Unlabelled",
    ]
    assert usage["raw_usage"]["registry_metadata_fallback_object_ids"] == [
        "object-001", "object-002",
    ]
    assert usage["raw_usage"]["registry_metadata_audit"]["fallback_component_anchor_group_ids"] == [
        "view-001", "view-002",
    ]


def test_registry_uses_the_same_atomic_visual_group_contract_for_all_models():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
        }],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "one cabinet",
            "boundary_basis": "one complete product",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
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


def test_integrated_visual_registry_derives_missing_page_coverage_from_graph():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "one cabinet", "representation_kind": "perspective",
        }],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "one cabinet",
            "boundary_basis": "one complete product",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package=None, model="model",
        )

    assert registry["objects"][0]["estimation_evidence_pages"] == [1]
    assert usage["raw_usage"]["page_coverage_count"] == 2


def test_integrated_visual_registry_excludes_non_object_pages_from_estimation_evidence():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 2, "location_hint": "center",
            "visual_description": "cabinet elevation", "representation_kind": "elevation",
        }],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "N56",
            "quantity": 1, "quantity_explicit": True, "identity_pages": [2],
            "visual_identity": "cabinet", "boundary_basis": "one finished cabinet",
        }],
        "merge_proofs": [],
        "page_coverage": [
            {
                "page_number": 1, "component_anchor_group_ids": [],
                "evidence_reason": "cover page has project metadata only",
            },
            {
                "page_number": 2, "component_anchor_group_ids": ["view_a"],
                "evidence_reason": "object-specific cabinet elevation",
            },
        ],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, _ = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"cover", b"drawing"], regions=[], ocr_package=None, model="model",
        )

    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert registry["objects"][0]["estimation_evidence_pages"] == [2]


def test_integrated_visual_registry_discards_document_context_before_pair_ledger():
    payload = {
        "visual_groups": [
            {
                "group_id": "generic-plan", "page_number": 1,
                "location_hint": "center", "visual_description": "full floor plan with furniture zones",
                "representation_kind": "floor_plan",
            },
            {
                "group_id": "cabinet-elevation", "page_number": 2,
                "location_hint": "center", "visual_description": "cabinet elevation",
                "representation_kind": "elevation",
            },
        ],
        "objects": [{
            "component_anchor_group_id": "cabinet-elevation", "transport_label": "N56",
            "quantity": 1, "quantity_explicit": True, "identity_pages": [1, 2],
            "visual_identity": "one cabinet", "boundary_basis": "one finished cabinet",
        }],
        "merge_proofs": [{
            "group_id_a": "cabinet-elevation", "group_id_b": "generic-plan",
            "relationship": "same_object_view",
            "evidence_facts": [{
                "evidence_type": "explicit_document_relation", "evidence_pages": [1, 2],
                "observation": "The plan and elevation carry the N56 label.",
            }],
            "commercial_inseparability": "The plan and elevation describe one cabinet.",
        }],
        "page_coverage": [
            {
                "page_number": 1, "component_anchor_group_ids": [],
                "evidence_reason": "generic floor plan",
            },
            {
                "page_number": 2, "component_anchor_group_ids": ["cabinet-elevation"],
                "evidence_reason": "object-specific cabinet elevation",
            },
        ],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"plan", b"elevation"], regions=[], ocr_package=None, model="model",
        )

    assert [group["page_number"] for group in visual_map["visual_groups"]] == [2]
    assert registry["objects"][0]["visual_group_ids"] == ["view-001"]
    assert usage["raw_usage"]["classification_decisions"][0] == {
        "group_id": "generic-plan",
        "page_number": 1,
        "evidence_class": "document_context",
        "representation_kind": "floor_plan",
        "classification_reason": "Generic page context is not object-specific Evidence.",
    }


def test_integrated_visual_registry_accepts_document_only_upload_without_object_package():
    payload = {
        "visual_groups": [{
            "group_id": "title", "page_number": 1, "location_hint": "full page",
            "visual_description": "cover page with project title",
            "representation_kind": "title_page",
        }],
        "objects": [],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": [],
            "evidence_reason": "cover page only",
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        visual_map, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="cover.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"cover"], regions=[], ocr_package=None, model="model",
        )

    assert visual_map == {"visual_groups": []}
    assert registry == {"objects": []}
    assert usage["raw_usage"]["classification_decisions"][0]["evidence_class"] == "document_context"


def test_integrated_visual_registry_reconciles_missing_object_on_only_page():
    payload = {
        "visual_groups": [
            {
                "group_id": "view_a", "page_number": 1, "location_hint": "left",
                "visual_description": "cabinet", "representation_kind": "perspective",
            },
            {
                "group_id": "view_b", "page_number": 1, "location_hint": "right",
                "visual_description": "counter", "representation_kind": "perspective",
            },
        ],
        "objects": [
            {
                "component_anchor_group_id": "view_a", "transport_label": "Object 1",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_identity": "cabinet",
                "boundary_basis": "separate cabinet",
            },
            {
                "component_anchor_group_id": "view_b", "transport_label": "Object 2",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_identity": "counter",
                "boundary_basis": "separate counter",
            },
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [item["estimation_evidence_pages"] for item in registry["objects"]] == [[1], [1]]
    assert usage["raw_usage"]["graph_page_coverage_supplements"] == [{
        "page_number": 1,
        "object_id": "object-001",
        "visual_group_id": "view-001",
        "source": "component_group",
    }, {
        "page_number": 1,
        "object_id": "object-002",
        "visual_group_id": "view-002",
        "source": "component_group",
    }]


def test_integrated_visual_registry_keeps_valid_graph_when_page_coverage_is_incomplete():
    payload = {
        "visual_groups": [{
            "group_id": "view_a", "page_number": 1, "location_hint": "left",
            "visual_description": "cabinet", "representation_kind": "perspective",
        }],
        "objects": [{
            "component_anchor_group_id": "view_a", "transport_label": "Object 1",
            "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
            "visual_identity": "cabinet",
            "boundary_basis": "one cabinet",
        }],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a"],
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"one", b"two"], regions=[], ocr_package=None, model="model",
        )

    assert registry["objects"][0]["estimation_evidence_pages"] == [1]
    assert usage["raw_usage"]["page_coverage_count"] == 2


def test_integrated_visual_registry_json_failure_carries_transport_diagnostics():
    raw_text = (
        '{"visual_groups":[{"group_id":"G01"}],'
        '"classifications":[{"group_id":"G01","classification_reason":"'
    )

    with (
        patch("agents.anthropic_adapter.get_anthropic_client", return_value=object()),
        patch(
            "agents.anthropic_adapter.create_claude_message_streamed",
            return_value=(_Response(), {
                "request_started_at": "2026-10-16T00:00:00+00:00",
                "request_finished_at": "2026-10-16T00:00:01+00:00",
            }),
        ),
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=raw_text),
        pytest.raises(DetectionVisualRegistryValidationError) as raised,
    ):
        run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    event = raised.value.usage_event
    assert event["status"] == "failed"
    assert event["raw_usage"]["validation_stage"] == "visual_registry_json"
    assert event["raw_usage"]["response_character_count"] == len(raw_text)
    assert event["raw_usage"]["response_text_sha256"]
    assert event["raw_usage"]["max_tokens"] == 12288
    assert event["raw_usage"]["raw_response_persisted"] is False
    assert event["raw_usage"]["top_level_sections_started"] == [
        "visual_groups", "classifications",
    ]
    assert event["raw_usage"]["terminal_top_level_section"] == "classifications"
    assert event["raw_usage"]["terminal_json_property_key"] == "classification_reason"
    assert event["raw_usage"]["terminal_response_ends_inside_string"] is True
    assert event["raw_usage"]["output_token_budget_utilization_percent"] > 0


def test_integrated_visual_registry_allows_one_physical_page_for_multiple_components():
    payload = {
        "visual_groups": [
            {"group_id": "view_a", "page_number": 1, "location_hint": "left", "visual_description": "first cabinet elevation", "representation_kind": "elevation"},
            {"group_id": "view_b", "page_number": 1, "location_hint": "right", "visual_description": "second cabinet elevation", "representation_kind": "elevation"},
        ],
        "objects": [
            {
                "component_anchor_group_id": "view_a", "transport_label": "Object 1",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_identity": "first cabinet",
                "boundary_basis": "first complete envelope",
            },
            {
                "component_anchor_group_id": "view_b", "transport_label": "Object 2",
                "quantity": 1, "quantity_explicit": False, "identity_pages": [1],
                "visual_identity": "second cabinet",
                "boundary_basis": "second complete envelope",
            },
        ],
        "merge_proofs": [],
        "page_coverage": [{
            "page_number": 1, "component_anchor_group_ids": ["view_a", "view_b"],
            "evidence_reason": "one physical sheet contains both separate cabinets",
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
        patch("agents.anthropic_adapter.extract_text_from_claude_response", return_value=json.dumps(_visual_registry_payload(payload))),
    ):
        _, registry, usage = run_anthropic_detection_visual_registry_agent(
            file_name="drawing.pdf", company_id="001", file_bytes=b"pdf",
            page_images=[b"page"], regions=[], ocr_package=None, model="model",
        )

    assert [item["object_id"] for item in registry["objects"]] == [
        "object-001", "object-002",
    ]
    assert usage["raw_usage"]["registry_decision_audit"] == _visual_registry_payload(payload)


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
