from __future__ import annotations

from types import SimpleNamespace

import pytest

from db.workflow_routes import (
    ensure_workflow_route_token,
    resolve_workflow_route_token,
    workflow_route_key,
)


class _RoutesQuery:
    def __init__(self, rows: list[dict[str, object]]):
        self.rows = rows
        self.filters: dict[str, str] = {}
        self.insert_payload: dict[str, object] | None = None

    def select(self, _columns: str):
        return self

    def eq(self, key: str, value: str):
        self.filters[key] = str(value)
        return self

    def limit(self, _value: int):
        return self

    def insert(self, payload: dict[str, object]):
        self.insert_payload = dict(payload)
        return self

    def execute(self):
        if self.insert_payload is not None:
            self.rows.append(self.insert_payload)
            return SimpleNamespace(data=[self.insert_payload])
        matched = [
            row
            for row in self.rows
            if all(str(row.get(key) or "") == value for key, value in self.filters.items())
        ]
        return SimpleNamespace(data=matched)


class _RoutesClient:
    def __init__(self):
        self.rows: list[dict[str, object]] = []

    def table(self, name: str):
        assert name == "rfq_workflow_routes"
        return _RoutesQuery(self.rows)


def test_route_key_is_deterministic_and_scoped():
    assert workflow_route_key(scope="run", run_id="run-1") == "run:run-1"
    assert workflow_route_key(
        scope="estimate", run_id="run-1", estimate_id="estimate-1"
    ) == "estimate:estimate-1"
    assert workflow_route_key(
        scope="object", run_id="run-1", estimate_id="estimate-1", object_id="object-1"
    ) == "object:estimate-1:object-1"


def test_short_route_token_is_durable_and_requires_its_owner(monkeypatch):
    client = _RoutesClient()
    monkeypatch.setattr("db.workflow_routes.secrets.token_urlsafe", lambda _bytes: "route-token-1")

    token = ensure_workflow_route_token(
        client,
        company_id="company-1",
        scope="estimate",
        run_id="run-1",
        estimate_id="estimate-1",
    )
    assert token == "route-token-1"
    assert ensure_workflow_route_token(
        client,
        company_id="company-1",
        scope="estimate",
        run_id="run-1",
        estimate_id="estimate-1",
    ) == token
    assert len(client.rows) == 1

    assert resolve_workflow_route_token(
        client,
        route_token=token,
        company_id="company-1",
        expected_scope="estimate",
    ) == {"run_id": "run-1", "estimate_id": "estimate-1"}
    with pytest.raises(PermissionError):
        resolve_workflow_route_token(
            client,
            route_token=token,
            company_id="company-2",
            expected_scope="estimate",
        )


def test_short_route_rejects_the_wrong_screen_scope(monkeypatch):
    client = _RoutesClient()
    monkeypatch.setattr("db.workflow_routes.secrets.token_urlsafe", lambda _bytes: "route-token-2")
    token = ensure_workflow_route_token(
        client,
        company_id="company-1",
        scope="run",
        run_id="run-1",
    )

    with pytest.raises(ValueError):
        resolve_workflow_route_token(
            client,
            route_token=token,
            company_id="company-1",
            expected_scope="estimate",
        )
