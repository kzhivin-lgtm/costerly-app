import pytest

from use_cases.manufacturing_routing import (
    ManufacturingRoutingError,
    RoutingPolicy,
    SheetMetalWork,
    WoodPanelWork,
    route_sheet_metal_work,
    route_wood_panel_work,
)


SIMPLE_WOOD_WORK = WoodPanelWork(
    process_required=True,
    part_count=4,
    rectangular_parts_only=True,
    single_face_processing=True,
    hole_count=8,
    standard_operations_only=True,
    has_freeform_contours=False,
    has_internal_cutouts=False,
    has_pockets=False,
    has_horizontal_or_end_drilling=False,
    has_repeated_hole_patterns=False,
    has_tight_positional_relationships=False,
)

ROUGH_METAL_WORK = SheetMetalWork(
    process_required=True,
    part_count=2,
    straight_edge_to_edge_cuts_only=True,
    cut_count=4,
    rough_finish_acceptable=True,
    material_and_thickness_supported=True,
    basic_in_house_cutting_explicitly_confirmed=True,
    has_holes_or_internal_features=False,
    has_curves_or_shaped_edges=False,
    precision_or_repeatability_required=False,
)


def test_router_skips_processes_that_are_not_required():
    wood = route_wood_panel_work(
        WoodPanelWork(process_required=False),
        cnc_in_house=False,
        panel_saw_in_house=False,
    )
    metal = route_sheet_metal_work(
        SheetMetalWork(process_required=False),
        sheet_laser_in_house=False,
    )

    assert wood.route == "not_required"
    assert metal.route == "not_required"


def test_in_house_cnc_is_the_exclusive_wood_route_when_available():
    decision = route_wood_panel_work(
        SIMPLE_WOOD_WORK,
        cnc_in_house=True,
        panel_saw_in_house=True,
    )

    assert decision.route == "cnc_router_in_house"
    assert decision.needs_review is False
    assert decision.costing_strategy == "specialized_calculator"
    assert decision.calculator == "cnc_router_in_house"


def test_simple_low_volume_wood_uses_panel_saw_and_manual_processing():
    decision = route_wood_panel_work(
        SIMPLE_WOOD_WORK,
        cnc_in_house=False,
        panel_saw_in_house=True,
    )

    assert decision.route == "wood_panel_saw_manual"
    assert decision.costing_strategy == "standard_material_labor"
    assert decision.calculator is None
    assert "simple_low_volume_single_face_work" in decision.reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("rectangular_parts_only", False, "manual_route_requires_rectangular_parts"),
        ("single_face_processing", False, "manual_route_requires_single_face_processing"),
        ("standard_operations_only", False, "manual_route_requires_standard_operations"),
        ("has_freeform_contours", True, "has_freeform_contours"),
        ("has_internal_cutouts", True, "has_internal_cutouts"),
        ("has_pockets", True, "has_pockets"),
        ("has_horizontal_or_end_drilling", True, "has_horizontal_or_end_drilling"),
        ("has_repeated_hole_patterns", True, "has_repeated_hole_patterns"),
        ("has_tight_positional_relationships", True, "has_tight_positional_relationships"),
    ),
)
def test_complex_wood_features_require_cnc_subcontractor(field, value, reason):
    work = WoodPanelWork(**{**SIMPLE_WOOD_WORK.__dict__, field: value})

    decision = route_wood_panel_work(
        work,
        cnc_in_house=False,
        panel_saw_in_house=True,
    )

    assert decision.route == "cnc_router_subcontractor"
    assert reason in decision.reasons


def test_wood_manual_route_has_conservative_volume_limits():
    too_many_parts = WoodPanelWork(**{**SIMPLE_WOOD_WORK.__dict__, "part_count": 7})
    too_many_holes = WoodPanelWork(**{**SIMPLE_WOOD_WORK.__dict__, "hole_count": 13})

    assert route_wood_panel_work(
        too_many_parts,
        cnc_in_house=False,
        panel_saw_in_house=True,
    ).route == "cnc_router_subcontractor"
    assert route_wood_panel_work(
        too_many_holes,
        cnc_in_house=False,
        panel_saw_in_house=True,
    ).route == "cnc_router_subcontractor"


def test_incomplete_wood_evidence_requires_review_instead_of_guessing():
    work = WoodPanelWork(**{**SIMPLE_WOOD_WORK.__dict__, "hole_count": None})

    decision = route_wood_panel_work(
        work,
        cnc_in_house=False,
        panel_saw_in_house=True,
    )

    assert decision.route == "needs_review"
    assert decision.needs_review is True
    assert "hole_count" in decision.reasons


def test_wood_without_cnc_or_panel_saw_uses_subcontractor():
    decision = route_wood_panel_work(
        SIMPLE_WOOD_WORK,
        cnc_in_house=False,
        panel_saw_in_house=False,
    )

    assert decision.route == "cnc_router_subcontractor"


def test_in_house_sheet_laser_is_used_when_available():
    decision = route_sheet_metal_work(
        ROUGH_METAL_WORK,
        sheet_laser_in_house=True,
    )

    assert decision.route == "sheet_laser_in_house"


def test_metal_without_laser_defaults_to_subcontractor():
    work = SheetMetalWork(
        **{
            **ROUGH_METAL_WORK.__dict__,
            "basic_in_house_cutting_explicitly_confirmed": False,
        }
    )

    decision = route_sheet_metal_work(work, sheet_laser_in_house=False)

    assert decision.route == "sheet_laser_subcontractor"
    assert "basic_in_house_cutting_not_confirmed" in decision.reasons


def test_confirmed_rough_low_volume_metal_can_use_basic_in_house_cutting():
    decision = route_sheet_metal_work(
        ROUGH_METAL_WORK,
        sheet_laser_in_house=False,
    )

    assert decision.route == "metal_basic_sheet_cutting_in_house"
    assert decision.needs_review is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("straight_edge_to_edge_cuts_only", False, "non_straight_or_bounded_cut"),
        ("rough_finish_acceptable", False, "production_finish_required"),
        ("material_and_thickness_supported", False, "material_or_thickness_unsupported"),
        ("has_holes_or_internal_features", True, "holes_or_internal_features_present"),
        ("has_curves_or_shaped_edges", True, "curves_or_shaped_edges_present"),
        ("precision_or_repeatability_required", True, "precision_or_repeatability_required"),
    ),
)
def test_metal_exception_is_rejected_by_any_production_requirement(field, value, reason):
    work = SheetMetalWork(**{**ROUGH_METAL_WORK.__dict__, field: value})

    decision = route_sheet_metal_work(work, sheet_laser_in_house=False)

    assert decision.route == "sheet_laser_subcontractor"
    assert reason in decision.reasons


def test_metal_exception_has_lower_volume_limits_than_wood():
    policy = RoutingPolicy()

    assert policy.metal_basic_max_parts < policy.wood_manual_max_parts
    assert route_sheet_metal_work(
        SheetMetalWork(**{**ROUGH_METAL_WORK.__dict__, "part_count": 3}),
        sheet_laser_in_house=False,
    ).route == "sheet_laser_subcontractor"
    assert route_sheet_metal_work(
        SheetMetalWork(**{**ROUGH_METAL_WORK.__dict__, "cut_count": 5}),
        sheet_laser_in_house=False,
    ).route == "sheet_laser_subcontractor"


def test_confirmed_metal_exception_with_missing_evidence_requires_review():
    work = SheetMetalWork(
        **{**ROUGH_METAL_WORK.__dict__, "material_and_thickness_supported": None}
    )

    decision = route_sheet_metal_work(work, sheet_laser_in_house=False)

    assert decision.route == "needs_review"
    assert decision.needs_review is True
    assert "material_and_thickness_supported" in decision.reasons


def test_unknown_primary_machine_availability_requires_review():
    wood = route_wood_panel_work(
        SIMPLE_WOOD_WORK,
        cnc_in_house=None,
        panel_saw_in_house=True,
    )
    metal = route_sheet_metal_work(ROUGH_METAL_WORK, sheet_laser_in_house=None)

    assert wood.route == "needs_review"
    assert metal.route == "needs_review"
    assert wood.costing_strategy == "needs_review"
    assert metal.costing_strategy == "needs_review"


def test_router_decision_preserves_contract_and_policy_versions():
    policy = RoutingPolicy(version="routing_policy_test_v7")

    decision = route_wood_panel_work(
        SIMPLE_WOOD_WORK,
        cnc_in_house=False,
        panel_saw_in_house=True,
        policy=policy,
    )

    assert decision.schema_version == "manufacturing_route_decision_v1"
    assert decision.policy_version == "routing_policy_test_v7"


def test_negative_counts_and_invalid_policy_are_rejected():
    with pytest.raises(ManufacturingRoutingError):
        route_wood_panel_work(
            WoodPanelWork(process_required=True, part_count=-1),
            cnc_in_house=False,
            panel_saw_in_house=True,
        )
    with pytest.raises(ManufacturingRoutingError):
        RoutingPolicy(metal_basic_max_parts=-1)
