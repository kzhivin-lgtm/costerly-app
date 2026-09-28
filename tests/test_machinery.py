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

    def insert(self, payload):
        if self.table in self.client.fail_inserts:
            raise RuntimeError("insert unavailable")
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
    def __init__(self, reads=None, fail_inserts=None):
        self.reads = reads or {}
        self.fail_inserts = set(fail_inserts or [])
        self.writes: list[tuple[str, dict]] = []

    def table(self, name: str):
        return _Query(self, name)


def test_catalog_is_compact_and_keeps_cnc_and_laser_separate():
    assert len(machinery.MACHINE_SPECS) == 27
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
    assert "metal_welding" not in machinery.PROFILE_MACHINE_CODES
    assert machinery.PROFILE_MACHINE_CODES[-5:] == (
        "metal_profile_saw",
        "finish_wet_spray_booth",
        "finish_powder_booth",
        "finish_sandblast_booth",
        "finish_galvanizing",
    )
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
        "metal_profile_bender",
        "metal_rolling_machine",
        "finish_sandblast_booth",
        "finish_galvanizing",
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
    }
    assert machinery.SUBCONTRACTOR_MACHINE_CODES == expected_detailed
    assert machinery.PROFILE_COSTING_MACHINE_CODES == {"wood_cnc_router"}


def test_machinery_migration_is_additive_and_seeds_the_application_catalog():
    sql = "\n".join(
        path.read_text().lower()
        for path in sorted((Path(__file__).parents[1] / "db/sql").glob("*machinery*.sql"))
    )
    for operation in ("drop table", "delete from", "truncate table", "on delete cascade"):
        assert operation not in sql
    for code in machinery.MACHINE_SPEC_BY_CODE:
        assert f"'{code}'" in sql
    assert "alter table public.company_machines" not in sql


def test_cnc_estimate_level_events_are_private_bounded_and_content_free():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_09_28_cnc_estimate_levels.sql"
    ).read_text().lower()
    assert "company_cnc_estimate_level_events" in sql
    assert "between 1 and 5" in sql
    assert "'in_house', 'subcontractor'" in sql
    assert "previous_level_explicit boolean not null" in sql
    assert "revoke all on public.company_cnc_estimate_level_events" in sql
    assert "to service_role" in sql
    for forbidden in ("estimate_cost", "customer_content", "file_name", "document_text"):
        assert forbidden not in sql


def test_cnc_requires_work_area_and_keeps_only_exceptional_capabilities():
    with pytest.raises(machinery.MachineryError, match="Working width"):
        machinery._validate_capabilities("wood_cnc_router", {"work_area_x_mm": 2500})

    values = machinery._validate_capabilities(
        "wood_cnc_router",
        {
            "work_area_x_mm": 2500,
            "work_area_y_mm": 1300,
            "materials": ["MDF"],
            "two_sided_processing": True,
            "solid_wood": True,
            "horizontal_drilling": True,
            "five_axis_machining": False,
            "ignored": "value",
        },
    )
    assert values == {
        "work_area_x_mm": 2500.0,
        "work_area_y_mm": 1300.0,
        "solid_wood": True,
        "horizontal_drilling": True,
        "five_axis_machining": False,
    }


@pytest.mark.parametrize(
    ("machine_code", "values", "expected"),
    [
        (
            "wood_veneer_press",
            {
                "platen_length_mm": 3000,
                "platen_width_mm": 1300,
                "press_force_t": 70,
            },
            {
                "platen_length_mm": 3000.0,
                "platen_width_mm": 1300.0,
                "press_force_t": 70.0,
            },
        ),
        (
            "metal_punch_press",
            {
                "table_length_mm": 1200,
                "table_width_mm": 700,
                "press_force_t": 200,
            },
            {
                "table_length_mm": 1200.0,
                "table_width_mm": 700.0,
                "press_force_t": 200.0,
            },
        ),
    ],
)
def test_press_profiles_require_area_and_force(machine_code, values, expected):
    assert machinery._validate_capabilities(machine_code, values) == expected

    for missing_key in values:
        incomplete = dict(values)
        incomplete.pop(missing_key)
        with pytest.raises(machinery.MachineryError, match="Complete the required fields"):
            machinery._validate_capabilities(machine_code, incomplete)


def test_sheet_laser_keeps_power_and_only_exceptional_capabilities():
    values = machinery._validate_capabilities(
        "metal_sheet_laser",
        {
            "work_area_x_mm": 3000,
            "work_area_y_mm": 1500,
            "laser_power_kw": 6,
            "copper_brass": True,
            "bevel_cutting": False,
            "material_thickness_limits": "legacy value",
        },
    )

    assert values == {
        "work_area_x_mm": 3000.0,
        "work_area_y_mm": 1500.0,
        "laser_power_kw": 6.0,
        "copper_brass": True,
        "bevel_cutting": False,
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


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_cnc_estimate_level_accepts_only_five_positions(level):
    assert machinery._validate_cnc_estimate_level(level) == level


@pytest.mark.parametrize("level", [0, 6, "", "balanced"])
def test_cnc_estimate_level_rejects_values_outside_the_contract(level):
    with pytest.raises(machinery.MachineryError, match="from 1 to 5"):
        machinery._validate_cnc_estimate_level(level)


def test_explicit_in_house_cnc_level_is_saved_and_recorded(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="wood_cnc_router",
        availability_status="in_house",
        capabilities={"work_area_x_mm": 2500, "work_area_y_mm": 1300},
        estimate_level=2,
    )

    assert client.writes[0][0] == "company_machinery"
    assert client.writes[0][1]["pricing"] == {"estimate_level": 2}
    assert client.writes[1] == (
        "company_cnc_estimate_level_events",
        {
            "company_id": "company-a",
            "user_id": "user-1",
            "route": "in_house",
            "previous_level": 3,
            "previous_level_explicit": False,
            "selected_level": 2,
            "source": "machinery_setting",
        },
    )


def test_explicit_subcontractor_cnc_level_uses_the_exclusive_route(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="wood_cnc_router",
        availability_status="not_in_house",
        capabilities={"work_area_x_mm": 2500},
        pricing_method="hourly",
        pricing={"rate": 300, "currency": "ILS"},
        estimate_level=5,
    )

    machine_payload = client.writes[0][1]
    event_payload = client.writes[1][1]
    assert machine_payload["capabilities"] == {}
    assert machine_payload["pricing_method"] == "unknown"
    assert machine_payload["pricing"] == {"estimate_level": 5}
    assert event_payload["route"] == "subcontractor"
    assert event_payload["selected_level"] == 5


def test_untouched_balanced_default_is_not_saved_as_feedback(monkeypatch):
    client = _Client()
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="wood_cnc_router",
        availability_status="in_house",
        capabilities={"work_area_x_mm": 2500, "work_area_y_mm": 1300},
    )

    assert [table for table, _payload in client.writes] == ["company_machinery"]
    assert client.writes[0][1]["pricing"] == {}


def test_unchanged_explicit_cnc_level_does_not_duplicate_feedback(monkeypatch):
    client = _Client(
        {
            "company_machinery": [
                {
                    "availability_status": "in_house",
                    "pricing": {"estimate_level": 4},
                }
            ]
        }
    )
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    machinery.save_company_machinery(
        ACCESS,
        machine_code="wood_cnc_router",
        availability_status="in_house",
        capabilities={"work_area_x_mm": 2500, "work_area_y_mm": 1300},
        estimate_level=4,
    )

    assert [table for table, _payload in client.writes] == ["company_machinery"]


def test_feedback_telemetry_failure_does_not_undo_the_saved_level(monkeypatch):
    client = _Client(fail_inserts={"company_cnc_estimate_level_events"})
    monkeypatch.setattr(machinery, "get_supabase_client", lambda: client)
    monkeypatch.setattr(machinery, "assert_company_owner", lambda *_args: None)

    result = machinery.save_company_machinery(
        ACCESS,
        machine_code="wood_cnc_router",
        availability_status="in_house",
        capabilities={"work_area_x_mm": 2500, "work_area_y_mm": 1300},
        estimate_level=2,
    )

    assert result["pricing"] == {"estimate_level": 2}
    assert [table for table, _payload in client.writes] == ["company_machinery"]


def test_production_context_exposes_effective_default_without_feedback():
    client = _Client(
        {
            "company_machinery": [
                {
                    "machine_code": "wood_cnc_router",
                    "availability_status": "not_in_house",
                    "pricing": {},
                }
            ]
        }
    )

    context = machinery.build_company_production_context("company-a", client=client)

    cnc = context["machines"][0]
    assert cnc["estimate_level"] == 3
    assert cnc["estimate_level_explicit"] is False


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
    assert context["routing_rules"]["panel_material_manual_fallback_allowed"] is True
    assert context["routing_rules"]["metal_basic_cutting_requires_explicit_confirmation"] is True
    assert context["routing_rules"]["wood_cnc_default_sheet_materials"] == [
        "MDF",
        "Particleboard / LDSP",
        "Plywood",
        "Melamine-faced board",
    ]


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
