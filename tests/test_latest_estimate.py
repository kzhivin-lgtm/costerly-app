from __future__ import annotations

from use_cases.latest_estimate import (
    load_latest_estimate_route,
    load_latest_estimate_route_for_run,
)


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def select(self, value):
        self.calls.append(("select", value))
        return self

    def eq(self, key, value):
        self.calls.append(("eq", key, value))
        return self

    def order(self, key, *, desc=False):
        self.calls.append(("order", key, desc))
        return self

    def limit(self, value):
        self.calls.append(("limit", value))
        return self

    def execute(self):
        return type("Result", (), {"data": self.rows})()


class _Client:
    def __init__(self, rows):
        self.query = _Query(rows)

    def table(self, name):
        assert name == "rfq_estimates"
        return self.query


def test_latest_estimate_route_is_company_scoped_and_newest_first():
    client = _Client([{"estimate_id": "estimate-2", "run_id": "run-2"}])

    assert load_latest_estimate_route(client, "company-1") == {
        "estimate_id": "estimate-2",
        "run_id": "run-2",
    }
    assert ("eq", "company_id", "company-1") in client.query.calls
    assert ("order", "updated_at", True) in client.query.calls
    assert ("limit", 1) in client.query.calls


def test_latest_estimate_route_returns_none_for_missing_or_incomplete_row():
    assert load_latest_estimate_route(_Client([]), "company-1") is None
    assert load_latest_estimate_route(_Client([{"estimate_id": "estimate-2"}]), "company-1") is None


def test_latest_estimate_route_for_run_is_scoped_to_the_active_rfq():
    client = _Client([{"estimate_id": "estimate-2", "run_id": "run-2"}])

    assert load_latest_estimate_route_for_run(client, "company-1", "run-2") == {
        "estimate_id": "estimate-2",
        "run_id": "run-2",
    }
    assert ("eq", "company_id", "company-1") in client.query.calls
    assert ("eq", "run_id", "run-2") in client.query.calls


def test_latest_estimate_route_for_run_rejects_a_row_from_another_run():
    assert load_latest_estimate_route_for_run(
        _Client([{"estimate_id": "estimate-2", "run_id": "run-other"}]),
        "company-1",
        "run-2",
    ) is None
