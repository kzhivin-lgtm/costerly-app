from decimal import Decimal

import pytest

from use_cases.manufacturing_costing import (
    CncRouterInHouseInputs,
    CncRouterSubcontractorInputs,
    ManufacturingCostingError,
    SheetLaserInHouseInputs,
    SheetLaserSubcontractorInputs,
    ValueRange,
    calculate_cnc_router_in_house,
    calculate_cnc_router_subcontractor,
    calculate_selected_route,
    calculate_sheet_laser_in_house,
    calculate_sheet_laser_subcontractor,
    select_cost_for_reserve_level,
)
from use_cases.manufacturing_routing import (
    SheetMetalWork,
    WoodPanelWork,
    route_sheet_metal_work,
    route_wood_panel_work,
)


R = ValueRange.point


def test_value_range_and_reserve_levels_are_bounded_and_monotonic():
    values = ValueRange(100, 140, 220)

    assert [select_cost_for_reserve_level(values, level) for level in range(1, 6)] == [
        Decimal("100"),
        Decimal("120"),
        Decimal("140"),
        Decimal("180"),
        Decimal("220"),
    ]
    with pytest.raises(ManufacturingCostingError):
        ValueRange(2, 1, 3)
    with pytest.raises(ManufacturingCostingError):
        select_cost_for_reserve_level(values, 6)


def test_cnc_in_house_calculates_workload_and_cost_components_without_double_counting():
    result = calculate_cnc_router_in_house(
        CncRouterInHouseInputs(
            material_cost=R(100),
            contour_length_m=R(20),
            effective_feed_rate_m_per_min=R(2),
            pass_count=R(2),
            hole_count=R(12),
            seconds_per_hole=R(5),
            pocket_minutes=R(4),
            tool_change_and_non_cutting_minutes=R(5),
            programming_minutes=R(30),
            setup_minutes=R(20),
            sheet_handling_minutes=R(10),
            machine_capacity_rate_per_hour=R(120),
            programmer_rate_per_hour=R(100),
            operator_rate_per_hour=R(60),
            operator_attendance_fraction=R("0.25"),
            energy_cost=R(8),
            tooling_and_consumables_cost=R(7),
            secondary_operations_cost=R(5),
            expected_rework_cost=R(3),
            parameter_ids=("p1", "p1", "p2"),
        )
    )

    # 20 minutes cutting + 1 drilling + 4 pocket + 5 non-cutting = 30 machine minutes.
    assert result.components["machine_capacity"].typical == Decimal("60")
    # 20 setup + 10 handling + 25% of 30 machine minutes = 37.5 labor minutes.
    assert result.components["operator_labor"].typical == Decimal("37.500")
    assert result.components["programming"].typical == Decimal("50.0")
    assert result.total.typical == Decimal("270.500")
    assert result.selected_cost == result.total.typical
    assert result.parameter_ids == ("p1", "p2")


def test_inverse_speed_widens_cnc_cost_range_in_the_correct_direction():
    inputs = CncRouterInHouseInputs(
        material_cost=R(0),
        contour_length_m=ValueRange(8, 10, 12),
        effective_feed_rate_m_per_min=ValueRange(1, 2, 4),
        pass_count=R(1),
        hole_count=R(0),
        seconds_per_hole=R(0),
        pocket_minutes=R(0),
        tool_change_and_non_cutting_minutes=R(0),
        programming_minutes=R(0),
        setup_minutes=R(0),
        sheet_handling_minutes=R(0),
        machine_capacity_rate_per_hour=R(60),
        programmer_rate_per_hour=R(0),
        operator_rate_per_hour=R(0),
        operator_attendance_fraction=R(0),
    )

    result = calculate_cnc_router_in_house(inputs)

    assert result.total == ValueRange(2, 5, 12)


def test_cnc_subcontractor_applies_minimum_with_max_and_respects_inclusions():
    result = calculate_cnc_router_subcontractor(
        CncRouterSubcontractorInputs(
            provider_base_charge=R(100),
            base_includes_material=True,
            base_includes_cutting=True,
            material_cost=R(90),
            cutting_charge=R(80),
            internal_feature_charge=R(20),
            edge_banding=R(10),
            provider_minimum=R(200),
            allocated_delivery=R(25),
        )
    )

    assert result.details["material"] == R(0)
    assert result.details["cutting"] == R(0)
    assert result.details["provider_subtotal_before_minimum"] == R(130)
    assert result.components["provider_charge_after_minimum"] == R(200)
    assert result.total == R(225)


def test_supplier_minimum_is_not_added_after_subtotal_exceeds_it():
    result = calculate_sheet_laser_subcontractor(
        SheetLaserSubcontractorInputs(
            provider_base_charge=R(100),
            base_includes_material=False,
            base_includes_cutting=False,
            material_cost=R(150),
            provider_cut_charge=R(200),
            provider_setup=R(50),
            provider_minimum=R(300),
            allocated_delivery=R(40),
        )
    )

    assert result.details["provider_subtotal_before_minimum"] == R(500)
    assert result.components["provider_charge_after_minimum"] == R(500)
    assert result.total == R(540)


def test_laser_in_house_separates_machine_labor_gas_energy_and_consumables():
    result = calculate_sheet_laser_in_house(
        SheetLaserInHouseInputs(
            sheet_material_cost=R(200),
            cut_length_m=R(10),
            effective_cut_speed_m_per_min=R(2),
            pierce_count=R(30),
            pierce_seconds=R(2),
            rapid_moves_and_sheet_exchange_minutes=R(4),
            programming_and_nesting_minutes=R(30),
            setup_minutes=R(15),
            loading_unloading_minutes=R(5),
            machine_capacity_rate_per_hour=R(120),
            programmer_rate_per_hour=R(100),
            operator_rate_per_hour=R(60),
            operator_attendance_fraction=R("0.5"),
            assist_gas_cost_per_machine_hour=R(30),
            average_production_kw=R(10),
            electricity_cost_per_kwh=R("0.5"),
            consumables_cost_per_machine_hour=R(12),
            deburr_and_secondary_operations_cost=R(10),
            expected_rework_cost=R(5),
        )
    )

    # 5 cutting + 1 piercing + 4 rapid/exchange = 10 machine minutes.
    assert result.components["machine_capacity"].typical == Decimal("20.000000")
    assert result.components["assist_gas"].typical == Decimal("5.000000")
    assert result.components["electricity"].typical == Decimal("0.833333")
    assert result.components["consumables"].typical == Decimal("2.000000")
    assert result.components["operator_labor"].typical == Decimal("25.000000")
    assert result.components["programming_and_nesting"].typical == Decimal("50.000000")
    assert result.total.typical == Decimal("317.833333")


def test_laser_subcontractor_preserves_commercial_scope_and_reserve_selection():
    result = calculate_sheet_laser_subcontractor(
        SheetLaserSubcontractorInputs(
            provider_base_charge=ValueRange(0, 0, 0),
            base_includes_material=True,
            base_includes_cutting=False,
            material_cost=ValueRange(100, 120, 140),
            provider_cut_charge=ValueRange(200, 300, 500),
            provider_setup=ValueRange(50, 100, 150),
            provider_minimum=ValueRange(250, 350, 600),
            allocated_delivery=ValueRange(20, 30, 40),
            rush_surcharge=ValueRange(0, 0, 100),
        ),
        reserve_level=5,
    )

    assert result.details["material"] == R(0)
    assert result.total == ValueRange(270, 430, 790)
    assert result.selected_cost == Decimal("790")


def test_supplier_minimum_can_cross_subtotal_without_invalid_component_range():
    result = calculate_sheet_laser_subcontractor(
        SheetLaserSubcontractorInputs(
            provider_base_charge=ValueRange(100, 200, 500),
            base_includes_material=True,
            base_includes_cutting=True,
            provider_minimum=ValueRange(300, 300, 300),
        )
    )

    assert result.details["provider_subtotal_before_minimum"] == ValueRange(100, 200, 500)
    assert result.components["provider_charge_after_minimum"] == ValueRange(300, 300, 500)
    assert result.total == ValueRange(300, 300, 500)


def test_invalid_productivity_and_attendance_are_rejected():
    valid = dict(
        material_cost=R(0),
        contour_length_m=R(1),
        effective_feed_rate_m_per_min=R(1),
        pass_count=R(1),
        hole_count=R(0),
        seconds_per_hole=R(0),
        pocket_minutes=R(0),
        tool_change_and_non_cutting_minutes=R(0),
        programming_minutes=R(0),
        setup_minutes=R(0),
        sheet_handling_minutes=R(0),
        machine_capacity_rate_per_hour=R(0),
        programmer_rate_per_hour=R(0),
        operator_rate_per_hour=R(0),
        operator_attendance_fraction=R(0),
    )

    with pytest.raises(ManufacturingCostingError):
        calculate_cnc_router_in_house(
            CncRouterInHouseInputs(
                **{**valid, "effective_feed_rate_m_per_min": ValueRange(0, 1, 2)}
            )
        )
    with pytest.raises(ManufacturingCostingError):
        calculate_cnc_router_in_house(
            CncRouterInHouseInputs(
                **{**valid, "operator_attendance_fraction": ValueRange(0, 1, 2)}
            )
        )


def test_dispatch_runs_only_the_calculator_selected_by_router():
    decision = route_sheet_metal_work(
        SheetMetalWork(process_required=True),
        sheet_laser_in_house=True,
    )
    inputs = SheetLaserSubcontractorInputs(
        provider_base_charge=R(100),
        base_includes_material=True,
        base_includes_cutting=True,
    )

    with pytest.raises(ManufacturingCostingError, match="sheet_laser_in_house inputs"):
        calculate_selected_route(decision, inputs)


def test_dispatch_refuses_specialized_calculator_for_manual_route():
    manual_work = WoodPanelWork(
        process_required=True,
        part_count=2,
        rectangular_parts_only=True,
        single_face_processing=True,
        hole_count=2,
        standard_operations_only=True,
        has_freeform_contours=False,
        has_internal_cutouts=False,
        has_pockets=False,
        has_horizontal_or_end_drilling=False,
        has_repeated_hole_patterns=False,
        has_tight_positional_relationships=False,
    )
    decision = route_wood_panel_work(
        manual_work,
        cnc_in_house=False,
        panel_saw_in_house=True,
    )
    inputs = CncRouterSubcontractorInputs(
        provider_base_charge=R(100),
        base_includes_material=True,
        base_includes_cutting=True,
    )

    with pytest.raises(ManufacturingCostingError, match="does not authorize"):
        calculate_selected_route(decision, inputs)
