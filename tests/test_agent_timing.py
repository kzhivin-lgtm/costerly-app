from agents.anthropic_adapter import build_agent_usage_event
from ui.processing_stage import processing_stage_html


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
