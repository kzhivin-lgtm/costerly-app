from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Mapping

from use_cases.manufacturing_routing import RoutingDecision


CalculatorIdentity = Literal[
    "cnc_router_in_house",
    "cnc_router_subcontractor",
    "sheet_laser_in_house",
    "sheet_laser_subcontractor",
]


class ManufacturingCostingError(ValueError):
    pass


def _decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, bool):
        raise ManufacturingCostingError("Boolean values are not valid numeric inputs.")
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ManufacturingCostingError("Costing values must be numeric.") from exc
    if not result.is_finite():
        raise ManufacturingCostingError("Costing values must be finite.")
    return result


@dataclass(frozen=True)
class ValueRange:
    low: Decimal
    typical: Decimal
    high: Decimal

    def __init__(
        self,
        low: Decimal | int | float | str,
        typical: Decimal | int | float | str,
        high: Decimal | int | float | str,
    ) -> None:
        object.__setattr__(self, "low", _decimal(low))
        object.__setattr__(self, "typical", _decimal(typical))
        object.__setattr__(self, "high", _decimal(high))
        self.__post_init__()

    def __post_init__(self) -> None:
        if self.low < 0:
            raise ManufacturingCostingError("Range values cannot be negative.")
        if not self.low <= self.typical <= self.high:
            raise ManufacturingCostingError("Range must satisfy low <= typical <= high.")

    @classmethod
    def point(cls, value: Decimal | int | float | str) -> ValueRange:
        return cls(value, value, value)

    def scenario(self, index: int) -> Decimal:
        return (self.low, self.typical, self.high)[index]


ZERO_RANGE = ValueRange.point(0)
MONEY_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class CostCalculation:
    calculator: CalculatorIdentity
    total: ValueRange
    selected_cost: Decimal
    reserve_level: int
    components: Mapping[str, ValueRange]
    details: Mapping[str, ValueRange]
    parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CncRouterInHouseInputs:
    material_cost: ValueRange
    contour_length_m: ValueRange
    effective_feed_rate_m_per_min: ValueRange
    pass_count: ValueRange
    hole_count: ValueRange
    seconds_per_hole: ValueRange
    pocket_minutes: ValueRange
    tool_change_and_non_cutting_minutes: ValueRange
    programming_minutes: ValueRange
    setup_minutes: ValueRange
    sheet_handling_minutes: ValueRange
    machine_capacity_rate_per_hour: ValueRange
    programmer_rate_per_hour: ValueRange
    operator_rate_per_hour: ValueRange
    operator_attendance_fraction: ValueRange
    energy_cost: ValueRange = ZERO_RANGE
    tooling_and_consumables_cost: ValueRange = ZERO_RANGE
    secondary_operations_cost: ValueRange = ZERO_RANGE
    expected_rework_cost: ValueRange = ZERO_RANGE
    parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CncRouterSubcontractorInputs:
    provider_base_charge: ValueRange
    base_includes_material: bool
    base_includes_cutting: bool
    material_cost: ValueRange = ZERO_RANGE
    programming_or_file_preparation: ValueRange = ZERO_RANGE
    cutting_charge: ValueRange = ZERO_RANGE
    internal_feature_charge: ValueRange = ZERO_RANGE
    edge_banding: ValueRange = ZERO_RANGE
    secondary_operations: ValueRange = ZERO_RANGE
    provider_minimum: ValueRange = ZERO_RANGE
    allocated_delivery: ValueRange = ZERO_RANGE
    rush_surcharge: ValueRange = ZERO_RANGE
    parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SheetLaserInHouseInputs:
    sheet_material_cost: ValueRange
    cut_length_m: ValueRange
    effective_cut_speed_m_per_min: ValueRange
    pierce_count: ValueRange
    pierce_seconds: ValueRange
    rapid_moves_and_sheet_exchange_minutes: ValueRange
    programming_and_nesting_minutes: ValueRange
    setup_minutes: ValueRange
    machine_capacity_rate_per_hour: ValueRange
    programmer_rate_per_hour: ValueRange
    operator_rate_per_hour: ValueRange
    operator_attendance_fraction: ValueRange
    assist_gas_cost_per_machine_hour: ValueRange
    average_production_kw: ValueRange
    electricity_cost_per_kwh: ValueRange
    consumables_cost_per_machine_hour: ValueRange
    loading_unloading_minutes: ValueRange = ZERO_RANGE
    deburr_and_secondary_operations_cost: ValueRange = ZERO_RANGE
    expected_rework_cost: ValueRange = ZERO_RANGE
    parameter_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SheetLaserSubcontractorInputs:
    provider_base_charge: ValueRange
    base_includes_material: bool
    base_includes_cutting: bool
    material_cost: ValueRange = ZERO_RANGE
    provider_setup: ValueRange = ZERO_RANGE
    provider_cut_charge: ValueRange = ZERO_RANGE
    file_preparation: ValueRange = ZERO_RANGE
    secondary_operations: ValueRange = ZERO_RANGE
    provider_minimum: ValueRange = ZERO_RANGE
    allocated_delivery: ValueRange = ZERO_RANGE
    rush_surcharge: ValueRange = ZERO_RANGE
    parameter_ids: tuple[str, ...] = ()


CalculatorInputs = (
    CncRouterInHouseInputs
    | CncRouterSubcontractorInputs
    | SheetLaserInHouseInputs
    | SheetLaserSubcontractorInputs
)


def _validate_fraction(value: ValueRange, name: str) -> None:
    if value.high > 1:
        raise ManufacturingCostingError(f"{name} must be between 0 and 1.")


def _validate_positive(value: ValueRange, name: str) -> None:
    if value.low <= 0:
        raise ManufacturingCostingError(f"{name} must be greater than zero.")


def _range_from_scenarios(values: list[Decimal]) -> ValueRange:
    return ValueRange(
        *(value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP) for value in values)
    )


def _sum_components(components: Mapping[str, ValueRange]) -> ValueRange:
    return _range_from_scenarios(
        [sum((item.scenario(index) for item in components.values()), Decimal(0)) for index in range(3)]
    )


def _inverse_scenario(value: ValueRange, index: int) -> Decimal:
    return (value.high, value.typical, value.low)[index]


def select_cost_for_reserve_level(cost_range: ValueRange, reserve_level: int) -> Decimal:
    if reserve_level not in {1, 2, 3, 4, 5}:
        raise ManufacturingCostingError("Reserve level must be from 1 to 5.")
    if reserve_level == 1:
        return cost_range.low
    if reserve_level == 2:
        return (cost_range.low + cost_range.typical) / Decimal(2)
    if reserve_level == 3:
        return cost_range.typical
    if reserve_level == 4:
        return (cost_range.typical + cost_range.high) / Decimal(2)
    return cost_range.high


def _result(
    calculator: CalculatorIdentity,
    components: Mapping[str, ValueRange],
    reserve_level: int,
    parameter_ids: tuple[str, ...],
    *,
    details: Mapping[str, ValueRange] | None = None,
) -> CostCalculation:
    total = _sum_components(components)
    return CostCalculation(
        calculator=calculator,
        total=total,
        selected_cost=select_cost_for_reserve_level(total, reserve_level),
        reserve_level=reserve_level,
        components=dict(components),
        details=dict(details or components),
        parameter_ids=tuple(dict.fromkeys(parameter_ids)),
    )


def calculate_cnc_router_in_house(
    inputs: CncRouterInHouseInputs,
    *,
    reserve_level: int = 3,
) -> CostCalculation:
    _validate_positive(inputs.effective_feed_rate_m_per_min, "effective_feed_rate_m_per_min")
    _validate_fraction(inputs.operator_attendance_fraction, "operator_attendance_fraction")

    cutting_minutes: list[Decimal] = []
    drilling_minutes: list[Decimal] = []
    machine_minutes: list[Decimal] = []
    for index in range(3):
        cut = (
            inputs.contour_length_m.scenario(index)
            / _inverse_scenario(inputs.effective_feed_rate_m_per_min, index)
            * inputs.pass_count.scenario(index)
        )
        drill = (
            inputs.hole_count.scenario(index)
            * inputs.seconds_per_hole.scenario(index)
            / Decimal(60)
        )
        cutting_minutes.append(cut)
        drilling_minutes.append(drill)
        machine_minutes.append(
            cut
            + drill
            + inputs.pocket_minutes.scenario(index)
            + inputs.tool_change_and_non_cutting_minutes.scenario(index)
        )

    components = {
        "material": inputs.material_cost,
        "programming": _range_from_scenarios([
            inputs.programming_minutes.scenario(i)
            / Decimal(60)
            * inputs.programmer_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "machine_capacity": _range_from_scenarios([
            machine_minutes[i]
            / Decimal(60)
            * inputs.machine_capacity_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "operator_labor": _range_from_scenarios([
            (
                inputs.setup_minutes.scenario(i)
                + inputs.sheet_handling_minutes.scenario(i)
                + machine_minutes[i] * inputs.operator_attendance_fraction.scenario(i)
            )
            / Decimal(60)
            * inputs.operator_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "energy": inputs.energy_cost,
        "tooling_and_consumables": inputs.tooling_and_consumables_cost,
        "secondary_operations": inputs.secondary_operations_cost,
        "expected_rework": inputs.expected_rework_cost,
    }
    return _result(
        "cnc_router_in_house",
        components,
        reserve_level,
        inputs.parameter_ids,
    )


def _subcontract_components(
    *,
    provider_base_charge: ValueRange,
    base_includes_material: bool,
    base_includes_cutting: bool,
    material_cost: ValueRange,
    cutting_charge: ValueRange,
    other_pre_minimum: Mapping[str, ValueRange],
    provider_minimum: ValueRange,
    allocated_delivery: ValueRange,
    rush_surcharge: ValueRange,
) -> tuple[dict[str, ValueRange], dict[str, ValueRange]]:
    pre_minimum = {
        "provider_base": provider_base_charge,
        "material": ZERO_RANGE if base_includes_material else material_cost,
        "cutting": ZERO_RANGE if base_includes_cutting else cutting_charge,
        **other_pre_minimum,
    }
    subtotal = _sum_components(pre_minimum)
    provider_charge_after_minimum = _range_from_scenarios([
        max(provider_minimum.scenario(i), subtotal.scenario(i))
        for i in range(3)
    ])
    components = {
        "provider_charge_after_minimum": provider_charge_after_minimum,
        "allocated_delivery": allocated_delivery,
        "rush_surcharge": rush_surcharge,
    }
    details = {
        **pre_minimum,
        "provider_subtotal_before_minimum": subtotal,
        "provider_minimum": provider_minimum,
    }
    return components, details


def calculate_cnc_router_subcontractor(
    inputs: CncRouterSubcontractorInputs,
    *,
    reserve_level: int = 3,
) -> CostCalculation:
    components, details = _subcontract_components(
        provider_base_charge=inputs.provider_base_charge,
        base_includes_material=inputs.base_includes_material,
        base_includes_cutting=inputs.base_includes_cutting,
        material_cost=inputs.material_cost,
        cutting_charge=inputs.cutting_charge,
        other_pre_minimum={
            "programming_or_file_preparation": inputs.programming_or_file_preparation,
            "internal_features": inputs.internal_feature_charge,
            "edge_banding": inputs.edge_banding,
            "secondary_operations": inputs.secondary_operations,
        },
        provider_minimum=inputs.provider_minimum,
        allocated_delivery=inputs.allocated_delivery,
        rush_surcharge=inputs.rush_surcharge,
    )
    return _result(
        "cnc_router_subcontractor",
        components,
        reserve_level,
        inputs.parameter_ids,
        details=details,
    )


def calculate_sheet_laser_in_house(
    inputs: SheetLaserInHouseInputs,
    *,
    reserve_level: int = 3,
) -> CostCalculation:
    _validate_positive(inputs.effective_cut_speed_m_per_min, "effective_cut_speed_m_per_min")
    _validate_fraction(inputs.operator_attendance_fraction, "operator_attendance_fraction")

    machine_minutes: list[Decimal] = []
    for index in range(3):
        cut_minutes = (
            inputs.cut_length_m.scenario(index)
            / _inverse_scenario(inputs.effective_cut_speed_m_per_min, index)
        )
        pierce_minutes = (
            inputs.pierce_count.scenario(index)
            * inputs.pierce_seconds.scenario(index)
            / Decimal(60)
        )
        machine_minutes.append(
            cut_minutes
            + pierce_minutes
            + inputs.rapid_moves_and_sheet_exchange_minutes.scenario(index)
        )

    components = {
        "material": inputs.sheet_material_cost,
        "programming_and_nesting": _range_from_scenarios([
            inputs.programming_and_nesting_minutes.scenario(i)
            / Decimal(60)
            * inputs.programmer_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "machine_capacity": _range_from_scenarios([
            machine_minutes[i]
            / Decimal(60)
            * inputs.machine_capacity_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "operator_labor": _range_from_scenarios([
            (
                inputs.setup_minutes.scenario(i)
                + inputs.loading_unloading_minutes.scenario(i)
                + machine_minutes[i] * inputs.operator_attendance_fraction.scenario(i)
            )
            / Decimal(60)
            * inputs.operator_rate_per_hour.scenario(i)
            for i in range(3)
        ]),
        "assist_gas": _range_from_scenarios([
            machine_minutes[i]
            / Decimal(60)
            * inputs.assist_gas_cost_per_machine_hour.scenario(i)
            for i in range(3)
        ]),
        "electricity": _range_from_scenarios([
            machine_minutes[i]
            / Decimal(60)
            * inputs.average_production_kw.scenario(i)
            * inputs.electricity_cost_per_kwh.scenario(i)
            for i in range(3)
        ]),
        "consumables": _range_from_scenarios([
            machine_minutes[i]
            / Decimal(60)
            * inputs.consumables_cost_per_machine_hour.scenario(i)
            for i in range(3)
        ]),
        "deburr_and_secondary_operations": inputs.deburr_and_secondary_operations_cost,
        "expected_rework": inputs.expected_rework_cost,
    }
    return _result(
        "sheet_laser_in_house",
        components,
        reserve_level,
        inputs.parameter_ids,
    )


def calculate_sheet_laser_subcontractor(
    inputs: SheetLaserSubcontractorInputs,
    *,
    reserve_level: int = 3,
) -> CostCalculation:
    components, details = _subcontract_components(
        provider_base_charge=inputs.provider_base_charge,
        base_includes_material=inputs.base_includes_material,
        base_includes_cutting=inputs.base_includes_cutting,
        material_cost=inputs.material_cost,
        cutting_charge=inputs.provider_cut_charge,
        other_pre_minimum={
            "provider_setup": inputs.provider_setup,
            "file_preparation": inputs.file_preparation,
            "secondary_operations": inputs.secondary_operations,
        },
        provider_minimum=inputs.provider_minimum,
        allocated_delivery=inputs.allocated_delivery,
        rush_surcharge=inputs.rush_surcharge,
    )
    return _result(
        "sheet_laser_subcontractor",
        components,
        reserve_level,
        inputs.parameter_ids,
        details=details,
    )


def calculate_selected_route(
    decision: RoutingDecision,
    inputs: CalculatorInputs,
    *,
    reserve_level: int = 3,
) -> CostCalculation:
    """Run exactly the specialized calculator authorized by the route decision."""

    dispatch = {
        "cnc_router_in_house": (CncRouterInHouseInputs, calculate_cnc_router_in_house),
        "cnc_router_subcontractor": (
            CncRouterSubcontractorInputs,
            calculate_cnc_router_subcontractor,
        ),
        "sheet_laser_in_house": (SheetLaserInHouseInputs, calculate_sheet_laser_in_house),
        "sheet_laser_subcontractor": (
            SheetLaserSubcontractorInputs,
            calculate_sheet_laser_subcontractor,
        ),
    }
    if decision.costing_strategy != "specialized_calculator" or decision.calculator is None:
        raise ManufacturingCostingError(
            f"Route {decision.route} does not authorize a specialized CNC or laser calculator."
        )
    expected = dispatch.get(decision.calculator)
    if expected is None:
        raise ManufacturingCostingError("Route decision contains an unsupported calculator.")
    expected_type, calculator = expected
    if not isinstance(inputs, expected_type):
        raise ManufacturingCostingError(
            f"Route {decision.route} requires {decision.calculator} inputs."
        )
    return calculator(inputs, reserve_level=reserve_level)
