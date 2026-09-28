import json
from decimal import Decimal
from pathlib import Path

import pytest

from tools.build_israel_reference_baseline_activation import (
    EXPECTED_MATERIAL_COUNT,
    build_payload,
    render_activation_sql,
)
from use_cases.reference_material_readiness import CatalogPriceCandidate


def _candidate(index: int) -> CatalogPriceCandidate:
    return CatalogPriceCandidate(
        material_id=f"00000000-0000-4000-8000-{index:012d}",
        price_low=Decimal("10"),
        price_typical=Decimal("12"),
        price_high=Decimal("15"),
        unit="ea",
        currency="ILS",
        price_scope="material_only",
        confidence=Decimal("35"),
        tier="modeled_offer",
        methodology="test methodology",
        offer_ids=(f"10000000-0000-4000-8000-{index:012d}",),
    )


def test_activation_payload_requires_complete_unique_catalog():
    with pytest.raises(ValueError, match="Expected 280"):
        build_payload((_candidate(1),))

    candidates = tuple(_candidate(index) for index in range(EXPECTED_MATERIAL_COUNT))
    duplicate = candidates[:-1] + (candidates[0],)
    with pytest.raises(ValueError, match="unique"):
        build_payload(duplicate)


def test_activation_payload_requires_evidence():
    candidates = list(_candidate(index) for index in range(EXPECTED_MATERIAL_COUNT))
    candidates[0] = CatalogPriceCandidate(
        **{**candidates[0].__dict__, "offer_ids": ()}
    )
    with pytest.raises(ValueError, match="evidence"):
        build_payload(tuple(candidates))


def test_activation_sql_is_transactional_guarded_and_idempotent():
    candidates = tuple(_candidate(index) for index in range(EXPECTED_MATERIAL_COUNT))
    sql = render_activation_sql(build_payload(candidates)).lower()

    assert sql.startswith("-- 3.15.2")
    assert "begin;" in sql
    assert "commit;" in sql
    assert "expected 280 baseline rows" in sql
    assert "a different active israel baseline already exists" in sql
    assert "baseline evidence is missing or has an incompatible scope" in sql
    assert "on conflict (baseline_id) do nothing" in sql
    assert "status = 'active'" in sql
    assert "role = 'platform_admin'" in sql
    assert "market_material_baseline_evidence" in sql


def test_generated_activation_contains_the_verified_catalog_snapshot():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_israel_reference_baselines_v1_activation.sql"
    ).read_text()
    payload_text = sql.split("$payload$", 2)[1]
    payload = json.loads(payload_text)

    assert len(payload) == EXPECTED_MATERIAL_COUNT
    assert len({row["baseline_id"] for row in payload}) == EXPECTED_MATERIAL_COUNT
    assert len({row["material_id"] for row in payload}) == EXPECTED_MATERIAL_COUNT
    assert all(row["offer_ids"] for row in payload)
    assert sum(
        row["methodology"].startswith("tier=modeled_") for row in payload
    ) == 36
    assert sum(
        row["methodology"].startswith("tier=exact_") for row in payload
    ) == 244
