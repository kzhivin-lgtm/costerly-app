from config import agent_cost_category
from use_cases.rfq_processing import _runtime_event


def test_all_agent_version_families_have_a_dashboard_cost_category():
    assert agent_cost_category("estimation") == "estimation"
    assert agent_cost_category("estimation_v2_facts") == "estimation"
    assert agent_cost_category("price_source_v3") == "price_source"
    assert agent_cost_category("new_external_worker") == "detection"


def test_naming_uses_anthropic_token_rate_without_pricing_ocr():
    naming = _runtime_event(
        agent_name="naming", operation="test", company_id="company", run_id="run",
        file_name="file.pdf", model="claude-haiku-4-5-20251001", prompt_version="test",
        started_at="2026-10-04T00:00:00+00:00", finished_at="2026-10-04T00:00:01+00:00",
        duration_seconds=1, raw_usage={"input_tokens": 1000, "output_tokens": 1000},
    )
    assert naming["total_cost_usd"] == "0.006000"
    assert naming["raw_usage"]["cost_category"] == "detection"
