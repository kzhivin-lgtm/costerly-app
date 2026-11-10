from config import agent_cost_category, calculate_ocr_page_cost_usd
from use_cases.rfq_processing import _runtime_event


def test_all_agent_version_families_have_a_dashboard_cost_category():
    assert agent_cost_category("estimation") == "estimation"
    assert agent_cost_category("estimation_v3_material_facts") == "estimation"
    assert agent_cost_category("price_source_v3") == "price_source"
    assert agent_cost_category("new_external_worker") == "detection"


def test_mistral_ocr_cost_uses_provider_reported_page_count():
    assert calculate_ocr_page_cost_usd(
        model="mistral-ocr-4-1", pages_processed=11,
    ) == {
        "input_cost_usd": None,
        "output_cost_usd": None,
        "total_cost_usd": "0.044000",
    }


def test_naming_uses_anthropic_token_rate_without_pricing_ocr():
    naming = _runtime_event(
        agent_name="naming", operation="test", company_id="company", run_id="run",
        file_name="file.pdf", model="claude-haiku-4-5-20251001", prompt_version="test",
        started_at="2026-10-04T00:00:00+00:00", finished_at="2026-10-04T00:00:01+00:00",
        duration_seconds=1, raw_usage={"input_tokens": 1000, "output_tokens": 1000},
    )
    assert naming["total_cost_usd"] == "0.006000"
    assert naming["raw_usage"]["cost_category"] == "detection"


def test_haiku_55_pricing_uses_full_prompt_for_long_context_tier():
    from config import CLAUDE_HAIKU_MODEL, calculate_llm_cost_usd

    assert calculate_llm_cost_usd(
        model=CLAUDE_HAIKU_MODEL, input_tokens=100_000, output_tokens=1000,
    )["total_cost_usd"] == "0.010500"
    assert calculate_llm_cost_usd(
        model=CLAUDE_HAIKU_MODEL, input_tokens=100_000, output_tokens=1000,
        cache_read_input_tokens=1000,
    )["total_cost_usd"] == "0.052550"


def test_haiku_55_request_retains_schema_and_omits_incompatible_sampling():
    from agents.anthropic_adapter import create_claude_message
    from unittest.mock import Mock

    client = Mock()
    schema = {"type": "json_schema", "schema": {"type": "object"}}
    create_claude_message(
        client, model="claude-haiku-4-5-20251001", temperature=0, top_p=0.5,
        output_config={"format": schema},
    )
    assert client.messages.create.call_args.kwargs == {
        "model": "claude-haiku-5-5", "output_config": {"effort": "low", "format": schema},
    }
    create_claude_message(client, model="claude-sonnet-4-6", temperature=0)
    assert client.messages.create.call_args.kwargs == {
        "model": "claude-sonnet-4-6", "temperature": 0,
    }
