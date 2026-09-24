from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from state.company_auth import CompanyAccess
from use_cases import machinery


ACCESS = CompanyAccess("user-1", "owner@example.com", "company-a", "owner", "token")


@dataclass
class _Response:
    data: list[dict]


class _Query:
    def __init__(self, client, table: str):
        self.client = client
        self.table = table
        self.payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def upsert(self, payload, **_kwargs):
        self.payload = payload
        self.client.writes.append((self.table, payload))
        return self

    def update(self, payload):
        self.payload = payload
        self.client.writes.append((self.table, payload))
        return self

    def execute(self):
        if self.payload is not None:
            return _Response([{**self.payload, "company_machine_id": "machine-1"}])
        return _Response(list(self.client.reads.get(self.table, [])))


class _Client:
    def __init__(self, reads=None):
        self.reads = reads or {}
        self.writes: list[tuple[str, dict]] = []

    def table(self, name: str):
        return _Query(self, name)


def test_catalog_is_compact_and_keeps_cnc_and_laser_separate():
    assert len(machinery.MACHINE_SPECS) == 26
    assert len(machinery.PROFILE_MACHINE_SPECS) == 16
    codes = set(machinery.MACHINE_SPEC_BY_CODE)
    assert "wood_cnc_router" in codes
    assert "metal_sheet_laser" in codes
    assert "metal_tube_laser" in codes
    assert len(codes) == len(machinery.MACHINE_SPECS)
    assert "wood_boring_machine" not in machinery.PROFILE_MACHINE_CODES
    assert "finish_powder_oven" not in machinery.PROFILE_MACHINE_CODES
    assert "metal_tube_laser" not in machinery.PROFILE_MACHINE_CODES
    assert "metal_profile_saw" in machinery.PROFILE_MACHINE_CODES
    assert "finish_polishing" not in machinery.PROFILE_MACHINE_CODES
    assert machinery.SUBCONTRACTOR_MACHINE_CODES <= set(
        machinery.PROFILE_MACHINE_CODES
    )
    assert "wood_solid_preparation" not in machinery.SUBCONTRACTOR_MACHINE_CODES
    availability_only = {
        "wood_panel_saw",
        "wood_edge_bander",
        "wood_solid_preparation",
        "wood_wide_belt_sander",
        "metal_profile_saw",
        "metal_press_brake",
        "metal_punch_press",
        "metal_profile_bender",
        "metal_rolling_machine",
        "metal_welding",
    }
    assert all(
        machinery.MACHINE_SPEC_BY_CODE[code].fields == ()
        for code in availability_only
    )
    assert availability_only.isdisjoint(machinery.PROFILE_COSTING_MACHINE_CODES)
    expected_detailed = {
        "wood_cnc_router",
        "metal_sheet_laser",
        "finish_wet_spray_booth",
        "finish_powder_booth",
        "finish_sandblast_booth",
    }
    assert machinery.SUBCONTRACTOR_MACHINE_CODES == expected_detailed
    assert machinery.PROFILE_COSTING_MACHINE_CODES == expected_detailed


def test_machinery_migration_is_additive_and_seeds_the_application_catalog():
    sql = (
        Path(__file__).parents[1] / "db/sql/2026_09_24_machinery_foundation.sql"
    ).read_text().lower()
    for operation in ("drop table", "delete from", "truncate table", "on delete cascade"):
        assert operation not in sql
    for code in machinery.MACHINE_SPEC_BY_CODE:
        assert f"'{code}'" in sql
    assert "alter table public.company_machines" not in sql


def test_cnc_requires_work_area_and_materials():
    with pytest.raises(machinery.MachineryError, match="Working width"):
        machinery._validate_capabilities("wood_cnc_router", {"work_area_x_mm": 2500})

    values = machinery._validate_capabilities(
        "wood_cnc_router",
        {
            "work_area_x_mm": 2500,
            "work_area_y_mm": 1300,
            "materials": ["MDF", "Unsupported"],
            "two_sided_processing": True,
            "ignored": "value",
        },
    )
    assert values == {
        "work_area_x_mm": 2500.0,
        "work_area_y_mm": 1300.0,
        "materials": ["MDF"],
        "two_sided_processing": True,
    }


def test_structured_pricing_requires_positive_rate_and_currency():
    with pytest.raises(machinery.MachineryError, match="greater than zero"):
        machinery._validate_pricing("hourly", {"rate": 0, "currency": "ILS"})
    with pytest.raises(machinery.MachineryError, match="three-letter"):
        machinery._validate_pricing("per_job", {"rate": 100, "currency": "shekel"})
    assert machinery._validate_pricing(
        "hourly",
        {
            "rate": "120",
            "currency": "ils",
            "rate_kind": "internal_cost",
            "setup_fee": "25",
            "minimum_charge": 50,
        },
    ) == (
        "hourly",
        {
            "rate": 120.0,
            "currency": "ILS",
            "rate_kind": "internal_cost",
            "setup_fee": 25.0,
            "minimum_charge": 50.0,
        },
    )


def test_quote_only_does_not_invent_a_rate():
    assert machinery._validate_pricing("quote_only", {"rate": 500, "currency": "ILS"}) == (
        "quote_only",
        {},
    )


def test_saving_not_in_house_clears_machine_details(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="metal_sheet_laser",
        availability_status="not_in_house",
        capabilities={"work_area_x_mm": 3000},
        pricing_method="hourly",
        pricing={"rate": 300, "currency": "ILS"},
        accepts_external_work=True,
    )

    payload = client.writes[0][1]
    assert payload["capabilities"] == {}
    assert payload["pricing_method"] == "unknown"
    assert payload["pricing"] == {}
    assert payload["accepts_external_work"] is None
    assert payload["source"] == "owner_confirmed"


def test_saving_availability_only_machine_uses_one_identity(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="metal_press_brake",
        availability_status="in_house",
        capabilities={"max_bend_length_mm": 3000, "tonnage_t": 100},
        pricing_method="unknown",
    )

    table, payload = client.writes[0]
    assert table == "company_machinery"
    assert payload["company_id"] == "company-a"
    assert payload["machine_code"] == "metal_press_brake"
    assert payload["capabilities"] == {}


def test_not_answered_deactivates_company_machine(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.deactivate_company_machinery(
        ACCESS,
        machine_code="metal_press_brake",
    )

    assert len(client.writes) == 1
    assert client.writes[0][0] == "company_machinery"
    assert client.writes[0][1]["active"] is False


def test_production_context_preserves_price_precedence(monkeypatch):
    client = _Client({
        "company_machinery": [{
            "machine_code": "wood_cnc_router",
            "availability_status": "in_house",
            "pricing_method": "hourly",
        }],
        "company_suppliers": [{"supplier_id": "supplier-1", "supplier_name": "Cut Co"}],
        "company_supplier_services": [{
            "supplier_service_id": "service-1",
            "supplier_id": "supplier-1",
            "machine_code": "metal_sheet_laser",
        }],
        "company_service_offers": [{
            "service_offer_id": "offer-1",
            "supplier_service_id": "service-1",
            "source_price": 100,
        }],
    })

    context = machinery.build_company_production_context("company-a", client=client)

    assert context["schema_version"] == "machinery_context_v1"
    assert context["supplier_services"][0]["supplier_name"] == "Cut Co"
    assert context["active_supplier_offers"][0]["service_offer_id"] == "offer-1"
    assert context["price_precedence"][0] == "active_supplier_offer"
    assert context["price_precedence"][-1] == "needs_review"
    assert context["routing_rules"]["panel_material_manual_fallback_allowed"] is False


def test_removing_regular_subcontractor_deactivates_history(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.deactivate_supplier_services(ACCESS, machine_code="metal_sheet_laser")

    assert len(client.writes) == 1
    assert client.writes[0][0] == "company_supplier_services"
    payload = client.writes[0][1]
    assert payload["active"] is False
    assert payload["preferred"] is False
