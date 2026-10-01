from pathlib import Path

import use_cases.estimation_v2_facts_shadow as shadow
from agents.estimation_v2_facts_agent import ESTIMATION_V2_FACTS_AGENT_VERSION
from db.repositories import (
    fetch_active_israel_material_families,
    insert_estimation_v2_fact_result,
)


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.value = None
        self.page = None

    def select(self, *_args):
        return self

    def eq(self, key, value):
        self.client.filters.append((self.table, key, value))
        return self

    def insert(self, value):
        self.value = value
        return self

    def range(self, start, end):
        self.client.ranges.append((self.table, start, end))
        self.page = (start, end)
        return self

    def execute(self):
        if self.value is not None:
            self.client.inserted[self.table] = self.value
            return _Response([{"fact_result_id": "facts-1"}])
        rows = self.client.selected.get(self.table, [])
        if self.page is not None:
            rows = rows[self.page[0]:self.page[1] + 1]
        return _Response(rows)


class _Client:
    def __init__(self, selected=None):
        self.selected = selected or {}
        self.filters = []
        self.ranges = []
        self.inserted = {}

    def table(self, name):
        return _Query(self, name)


def test_object_facts_migration_is_additive_private_and_immutable():
    sql = Path("db/sql/2026_10_01_estimation_v2_object_facts.sql").read_text()

    assert "create table if not exists public.rfq_estimation_object_fact_results" in sql
    assert "references public.rfq_estimation_object_inputs(input_id)" in sql
    assert "references public.agent_usage_events(id)" in sql
    assert "unique (input_id, agent_version)" in sql
    assert "enable row level security" in sql
    assert "company_members" in sql
    assert "grant select" in sql and "to authenticated" in sql
    assert "drop table" not in sql.lower()
    assert "drop policy" not in sql.lower()
    assert "alter table public.rfq_estimates" not in sql.lower()


def test_repository_loads_only_nonempty_active_israel_material_families():
    client = _Client({
        "reference_material_pricing_identities": [
            {"price_attributes": {"material_family": "mdf"}},
            {"price_attributes": {"material_family": ""}},
            {"price_attributes": {"material_family": "birch_plywood"}},
        ],
    })

    assert fetch_active_israel_material_families(client) == {"mdf", "birch_plywood"}
    assert ("reference_material_pricing_identities", "market_code", "IL") in client.filters
    assert ("reference_material_pricing_identities", "status", "active") in client.filters
    assert client.ranges == [("reference_material_pricing_identities", 0, 999)]


def test_repository_pages_past_postgrest_thousand_row_limit():
    rows = [
        {"price_attributes": {"material_family": "mdf"}}
        for _ in range(1000)
    ] + [{"price_attributes": {"material_family": "plywood"}}]
    client = _Client({"reference_material_pricing_identities": rows})

    assert fetch_active_israel_material_families(client) == {"mdf", "plywood"}
    assert client.ranges == [
        ("reference_material_pricing_identities", 0, 999),
        ("reference_material_pricing_identities", 1000, 1999),
    ]


def test_repository_persists_only_validated_fact_envelope():
    client = _Client()
    facts = {"contract_version": "estimation_object_facts_v1", "status": "review_required"}

    result_id = insert_estimation_v2_fact_result(
        client,
        input_id="input-1",
        agent_version="agent-v1",
        facts_payload=facts,
        agent_usage_event_id="usage-1",
    )

    assert result_id == "facts-1"
    assert client.inserted["rfq_estimation_object_fact_results"] == {
        "input_id": "input-1",
        "agent_usage_event_id": "usage-1",
        "agent_version": "agent-v1",
        "contract_version": "estimation_object_facts_v1",
        "status": "review_required",
        "facts_payload": facts,
    }


def test_shadow_batch_persists_validated_facts_and_usage(monkeypatch):
    calls = []
    monkeypatch.setattr(shadow, "fetch_active_israel_material_families", lambda _client: {"birch_plywood"})
    monkeypatch.setattr(shadow, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        shadow,
        "run_estimation_v2_facts_agent",
        lambda **kwargs: {
            "facts": {"contract_version": "estimation_object_facts_v1", "status": "review_required"},
            "usage_event": {"agent_name": "estimation_v2_facts"},
        },
    )
    monkeypatch.setattr(shadow, "insert_agent_usage_event_returning_id", lambda *_args: "usage-1")

    def _insert(_client, **kwargs):
        calls.append(kwargs)
        return "facts-1"

    monkeypatch.setattr(shadow, "insert_estimation_v2_fact_result", _insert)
    result = shadow.run_estimation_v2_facts_batch(
        client=object(),
        inputs=[{"input_id": "input-1", "object_input_revision": 1, "input_payload": {"x": 1}}],
    )

    assert result == {"created_result_ids": ["facts-1"], "reused_input_ids": [], "failed": {}}
    assert calls[0]["agent_version"] == ESTIMATION_V2_FACTS_AGENT_VERSION
    assert calls[0]["agent_usage_event_id"] == "usage-1"


def test_shadow_batch_reuses_exact_agent_version_without_model_call(monkeypatch):
    monkeypatch.setattr(shadow, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(shadow, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"fact_result_id": "facts-1"})
    monkeypatch.setattr(
        shadow,
        "run_estimation_v2_facts_agent",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("model must not run")),
    )

    result = shadow.run_estimation_v2_facts_batch(
        client=object(),
        inputs=[{"input_id": "input-1", "object_input_revision": 1, "input_payload": {"x": 1}}],
    )

    assert result["reused_input_ids"] == ["input-1"]
    assert result["created_result_ids"] == []


def test_shadow_batch_is_fail_isolated_per_object(monkeypatch):
    monkeypatch.setattr(shadow, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(shadow, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        shadow,
        "run_estimation_v2_facts_agent",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("unsafe evidence")),
    )

    result = shadow.run_estimation_v2_facts_batch(
        client=object(),
        inputs=[{"input_id": "input-1", "object_input_revision": 1, "input_payload": {"x": 1}}],
    )

    assert result["created_result_ids"] == []
    assert result["failed"] == {"input-1": "ValueError: unsafe evidence"}
