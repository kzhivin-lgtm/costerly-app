from datetime import date
from decimal import Decimal

import pytest

from use_cases.manufacturing_costing import ValueRange
from use_cases.manufacturing_parameters import (
    ManufacturingParameterError,
    ParameterRequirement,
    ParameterScope,
    load_active_manufacturing_parameter_rows,
    resolve_manufacturing_parameters,
)


def _row(parameter_id: str, **changes):
    row = {
        "parameter_id": parameter_id,
        "calculator": "sheet_laser_in_house",
        "parameter_key": "effective_cut_speed",
        "country_code": "IL",
        "region": None,
        "material_family": None,
        "thickness_min_mm": None,
        "thickness_max_mm": None,
        "machine_class": None,
        "object_family": None,
        "qualifiers": {},
        "value_low": "1.0",
        "value_typical": "2.0",
        "value_high": "3.0",
        "unit": "m/min",
        "currency": None,
        "source_type": "platform_prior",
        "source_name": "Platform prior",
        "source_url": "https://example.com/source",
        "source_date": "2026-09-28",
        "confidence": "40",
        "status": "active",
        "version": 1,
        "effective_from": "2026-09-01",
        "effective_to": None,
        "approved_by": "admin-1",
        "approved_at": "2026-09-28T10:00:00Z",
    }
    row.update(changes)
    return row


REQ = [ParameterRequirement("effective_cut_speed", "m/min")]


def test_exact_material_scope_wins_over_general_fallback():
    rows = [
        _row("generic"),
        _row(
            "steel",
            material_family="carbon_steel",
            value_low="4",
            value_typical="5",
            value_high="6",
            source_type="manufacturer",
        ),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(material_family="carbon_steel"),
        as_of=date(2026, 9, 28),
    )

    assert result.needs_review is False
    assert result.parameter_ids == ("steel",)
    assert result.value_range("effective_cut_speed") == ValueRange(4, 5, 6)


def test_unknown_material_does_not_select_material_specific_record():
    result = resolve_manufacturing_parameters(
        [_row("steel", material_family="carbon_steel")],
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(material_family=None),
        as_of=date(2026, 9, 28),
    )

    assert result.needs_review is True
    assert result.missing_keys == ("effective_cut_speed",)
    with pytest.raises(ManufacturingParameterError, match="requires review"):
        result.require_complete()


def test_thickness_must_be_contained_and_nearest_band_is_never_used():
    rows = [
        _row("thin", thickness_min_mm="1", thickness_max_mm="3"),
        _row("thick", thickness_min_mm="4", thickness_max_mm="6"),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(thickness_mm=Decimal("3.5")),
        as_of=date(2026, 9, 28),
    )

    assert result.missing_keys == ("effective_cut_speed",)
    assert result.parameter_ids == ()


def test_narrower_containing_thickness_band_wins():
    rows = [
        _row("wide", thickness_min_mm="1", thickness_max_mm="10"),
        _row(
            "narrow",
            thickness_min_mm="4",
            thickness_max_mm="6",
            value_low="4",
            value_typical="5",
            value_high="6",
        ),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(thickness_mm=Decimal("5")),
        as_of=date(2026, 9, 28),
    )

    assert result.parameter_ids == ("narrow",)


def test_equal_rank_conflict_requires_review_instead_of_averaging():
    rows = [
        _row("provider-a", source_type="provider", source_name="Provider A"),
        _row("provider-b", source_type="provider", source_name="Provider B"),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(),
        as_of=date(2026, 9, 28),
    )

    assert result.ambiguous_keys == ("effective_cut_speed",)
    assert result.values == {}


def test_provider_qualifier_prevents_cross_provider_substitution():
    rows = [
        _row(
            "iron",
            calculator="sheet_laser_subcontractor",
            parameter_key="cut_rate_per_meter",
            unit="ILS/m",
            currency="ILS",
            source_type="provider",
            qualifiers={"provider_model": "iron_laser"},
        ),
        _row(
            "portal",
            calculator="sheet_laser_subcontractor",
            parameter_key="cut_rate_per_meter",
            unit="ILS/m",
            currency="ILS",
            source_type="provider",
            qualifiers={"provider_model": "laser_portal"},
        ),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_subcontractor",
        requirements=[ParameterRequirement("cut_rate_per_meter", "ILS/m", "ILS")],
        scope=ParameterScope(qualifiers={"provider_model": "iron_laser"}),
        as_of=date(2026, 9, 28),
    )

    assert result.parameter_ids == ("iron",)


def test_source_precedence_breaks_an_otherwise_equal_scope_tie():
    rows = [
        _row("prior", source_type="platform_prior"),
        _row("official", source_type="official", source_name="Official tariff"),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(),
        as_of=date(2026, 9, 28),
    )

    assert result.parameter_ids == ("official",)


def test_inactive_future_and_expired_records_do_not_resolve():
    rows = [
        _row("candidate", status="candidate"),
        _row("future", effective_from="2026-10-01"),
        _row("expired", effective_to="2026-09-20"),
    ]

    result = resolve_manufacturing_parameters(
        rows,
        calculator="sheet_laser_in_house",
        requirements=REQ,
        scope=ParameterScope(),
        as_of=date(2026, 9, 28),
    )

    assert result.missing_keys == ("effective_cut_speed",)


def test_active_parameter_unit_or_currency_mismatch_is_not_silently_converted():
    with pytest.raises(ManufacturingParameterError, match="incompatible unit or currency"):
        resolve_manufacturing_parameters(
            [_row("wrong-unit", unit="mm/s")],
            calculator="sheet_laser_in_house",
            requirements=REQ,
            scope=ParameterScope(),
            as_of=date(2026, 9, 28),
        )


def test_parameter_row_requires_active_approval_and_source_provenance():
    for change in (
        {"source_url": None},
        {"approved_by": None},
        {"approved_at": None},
    ):
        with pytest.raises(ManufacturingParameterError):
            resolve_manufacturing_parameters(
                [_row("invalid", **change)],
                calculator="sheet_laser_in_house",
                requirements=REQ,
                scope=ParameterScope(),
                as_of=date(2026, 9, 28),
            )


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, data):
        self.data = data
        self.filters = []

    def select(self, value):
        assert value == "*"
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def execute(self):
        return _Response(self.data)


class _Client:
    def __init__(self, data):
        self.query = _Query(data)

    def table(self, name):
        assert name == "manufacturing_cost_parameters"
        return self.query


def test_runtime_loader_reads_only_active_route_and_country_rows():
    client = _Client([_row("p1")])

    rows = load_active_manufacturing_parameter_rows(
        client,
        calculator="sheet_laser_in_house",
        country_code="IL",
    )

    assert rows[0]["parameter_id"] == "p1"
    assert client.query.filters == [
        ("calculator", "sheet_laser_in_house"),
        ("country_code", "IL"),
        ("status", "active"),
    ]
