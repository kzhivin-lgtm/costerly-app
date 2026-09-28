from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ManufacturingRoute = Literal[
    "not_required",
    "needs_review",
    "cnc_router_in_house",
    "wood_panel_saw_manual",
    "cnc_router_subcontractor",
    "sheet_laser_in_house",
    "metal_basic_sheet_cutting_in_house",
    "sheet_laser_subcontractor",
]
CostingStrategy = Literal[
    "none",
    "needs_review",
    "specialized_calculator",
    "standard_material_labor",
]
CalculatorIdentity = Literal[
    "cnc_router_in_house",
    "cnc_router_subcontractor",
    "sheet_laser_in_house",
    "sheet_laser_subcontractor",
]


class ManufacturingRoutingError(ValueError):
    pass


@dataclass(frozen=True)
class RoutingPolicy:
    """Versionable platform limits for narrow non-CNC fallback routes."""

    wood_manual_max_parts: int = 6
    wood_manual_max_holes: int = 12
    metal_basic_max_parts: int = 2
    metal_basic_max_cuts: int = 4
    version: str = "routing_policy_v1_candidate"

    def __post_init__(self) -> None:
        for field_name in (
            "wood_manual_max_parts",
            "wood_manual_max_holes",
            "metal_basic_max_parts",
            "metal_basic_max_cuts",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ManufacturingRoutingError(
                    f"{field_name} must be a non-negative integer."
                )
        if not self.version.strip():
            raise ManufacturingRoutingError("Routing policy version is required.")


@dataclass(frozen=True)
class WoodPanelWork:
    process_required: bool
    part_count: int | None = None
    rectangular_parts_only: bool | None = None
    single_face_processing: bool | None = None
    hole_count: int | None = None
    standard_operations_only: bool | None = None
    has_freeform_contours: bool | None = None
    has_internal_cutouts: bool | None = None
    has_pockets: bool | None = None
    has_horizontal_or_end_drilling: bool | None = None
    has_repeated_hole_patterns: bool | None = None
    has_tight_positional_relationships: bool | None = None


@dataclass(frozen=True)
class SheetMetalWork:
    process_required: bool
    part_count: int | None = None
    straight_edge_to_edge_cuts_only: bool | None = None
    cut_count: int | None = None
    rough_finish_acceptable: bool | None = None
    material_and_thickness_supported: bool | None = None
    basic_in_house_cutting_explicitly_confirmed: bool = False
    has_holes_or_internal_features: bool | None = None
    has_curves_or_shaped_edges: bool | None = None
    precision_or_repeatability_required: bool | None = None


@dataclass(frozen=True)
class RoutingDecision:
    route: ManufacturingRoute
    reasons: tuple[str, ...]
    needs_review: bool = False
    costing_strategy: CostingStrategy = "none"
    calculator: CalculatorIdentity | None = None
    schema_version: str = "manufacturing_route_decision_v1"
    policy_version: str = "routing_policy_v1_candidate"


def _validate_optional_count(value: int | None, name: str) -> None:
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ManufacturingRoutingError(f"{name} must be a non-negative integer.")


def _decision(
    route: ManufacturingRoute,
    *reasons: str,
    needs_review: bool = False,
    policy_version: str,
) -> RoutingDecision:
    calculators: dict[ManufacturingRoute, CalculatorIdentity] = {
        "cnc_router_in_house": "cnc_router_in_house",
        "cnc_router_subcontractor": "cnc_router_subcontractor",
        "sheet_laser_in_house": "sheet_laser_in_house",
        "sheet_laser_subcontractor": "sheet_laser_subcontractor",
    }
    if route in calculators:
        costing_strategy: CostingStrategy = "specialized_calculator"
        calculator = calculators[route]
    elif route in {"wood_panel_saw_manual", "metal_basic_sheet_cutting_in_house"}:
        costing_strategy = "standard_material_labor"
        calculator = None
    elif route == "needs_review":
        costing_strategy = "needs_review"
        calculator = None
    else:
        costing_strategy = "none"
        calculator = None
    return RoutingDecision(
        route=route,
        reasons=tuple(reasons),
        needs_review=needs_review,
        costing_strategy=costing_strategy,
        calculator=calculator,
        policy_version=policy_version,
    )


def route_wood_panel_work(
    work: WoodPanelWork,
    *,
    cnc_in_house: bool | None,
    panel_saw_in_house: bool | None,
    policy: RoutingPolicy = RoutingPolicy(),
) -> RoutingDecision:
    """Choose one wood-panel production route for one homogeneous part group."""

    def decide(
        route: ManufacturingRoute,
        *reasons: str,
        needs_review: bool = False,
    ) -> RoutingDecision:
        return _decision(
            route,
            *reasons,
            needs_review=needs_review,
            policy_version=policy.version,
        )

    _validate_optional_count(work.part_count, "part_count")
    _validate_optional_count(work.hole_count, "hole_count")

    if not work.process_required:
        return decide("not_required", "wood_panel_processing_not_required")
    if cnc_in_house is None:
        return decide(
            "needs_review",
            "cnc_availability_unknown",
            needs_review=True,
        )
    if cnc_in_house:
        return decide("cnc_router_in_house", "cnc_available_in_house")
    if panel_saw_in_house is None:
        return decide(
            "needs_review",
            "panel_saw_availability_unknown",
            needs_review=True,
        )
    if not panel_saw_in_house:
        return decide(
            "cnc_router_subcontractor",
            "cnc_unavailable_in_house",
            "panel_saw_unavailable_in_house",
        )

    hard_stop_fields = (
        ("has_freeform_contours", work.has_freeform_contours),
        ("has_internal_cutouts", work.has_internal_cutouts),
        ("has_pockets", work.has_pockets),
        ("has_horizontal_or_end_drilling", work.has_horizontal_or_end_drilling),
        ("has_repeated_hole_patterns", work.has_repeated_hole_patterns),
        ("has_tight_positional_relationships", work.has_tight_positional_relationships),
    )
    hard_stops = tuple(name for name, value in hard_stop_fields if value is True)
    if hard_stops:
        return decide(
            "cnc_router_subcontractor",
            "manual_route_disqualified",
            *hard_stops,
        )
    if work.rectangular_parts_only is False:
        return decide(
            "cnc_router_subcontractor",
            "manual_route_requires_rectangular_parts",
        )
    if work.single_face_processing is False:
        return decide(
            "cnc_router_subcontractor",
            "manual_route_requires_single_face_processing",
        )
    if work.standard_operations_only is False:
        return decide(
            "cnc_router_subcontractor",
            "manual_route_requires_standard_operations",
        )
    if work.part_count is not None and work.part_count > policy.wood_manual_max_parts:
        return decide(
            "cnc_router_subcontractor",
            "manual_part_limit_exceeded",
        )
    if work.hole_count is not None and work.hole_count > policy.wood_manual_max_holes:
        return decide(
            "cnc_router_subcontractor",
            "manual_hole_limit_exceeded",
        )

    required_evidence = {
        "part_count": work.part_count,
        "rectangular_parts_only": work.rectangular_parts_only,
        "single_face_processing": work.single_face_processing,
        "hole_count": work.hole_count,
        "standard_operations_only": work.standard_operations_only,
        **{name: value for name, value in hard_stop_fields},
    }
    missing = tuple(name for name, value in required_evidence.items() if value is None)
    if missing:
        return decide(
            "needs_review",
            "manual_route_evidence_incomplete",
            *missing,
            needs_review=True,
        )

    return decide(
        "wood_panel_saw_manual",
        "panel_saw_available_in_house",
        "simple_low_volume_single_face_work",
    )


def route_sheet_metal_work(
    work: SheetMetalWork,
    *,
    sheet_laser_in_house: bool | None,
    policy: RoutingPolicy = RoutingPolicy(),
) -> RoutingDecision:
    """Choose a strict sheet-metal route, defaulting to laser subcontracting."""

    def decide(
        route: ManufacturingRoute,
        *reasons: str,
        needs_review: bool = False,
    ) -> RoutingDecision:
        return _decision(
            route,
            *reasons,
            needs_review=needs_review,
            policy_version=policy.version,
        )

    _validate_optional_count(work.part_count, "part_count")
    _validate_optional_count(work.cut_count, "cut_count")

    if not work.process_required:
        return decide("not_required", "sheet_metal_cutting_not_required")
    if sheet_laser_in_house is None:
        return decide(
            "needs_review",
            "sheet_laser_availability_unknown",
            needs_review=True,
        )
    if sheet_laser_in_house:
        return decide("sheet_laser_in_house", "sheet_laser_available_in_house")

    # Basic cutting is intentionally not inferred from another metal capability.
    # It must be confirmed for this job because the compact Machinery profile does
    # not expose a sheet shear or guillotine.
    if not work.basic_in_house_cutting_explicitly_confirmed:
        return decide(
            "sheet_laser_subcontractor",
            "sheet_laser_unavailable_in_house",
            "basic_in_house_cutting_not_confirmed",
        )

    if work.straight_edge_to_edge_cuts_only is False:
        return decide("sheet_laser_subcontractor", "non_straight_or_bounded_cut")
    if work.rough_finish_acceptable is False:
        return decide("sheet_laser_subcontractor", "production_finish_required")
    if work.material_and_thickness_supported is False:
        return decide("sheet_laser_subcontractor", "material_or_thickness_unsupported")
    if work.has_holes_or_internal_features is True:
        return decide("sheet_laser_subcontractor", "holes_or_internal_features_present")
    if work.has_curves_or_shaped_edges is True:
        return decide("sheet_laser_subcontractor", "curves_or_shaped_edges_present")
    if work.precision_or_repeatability_required is True:
        return decide("sheet_laser_subcontractor", "precision_or_repeatability_required")
    if work.part_count is not None and work.part_count > policy.metal_basic_max_parts:
        return decide("sheet_laser_subcontractor", "basic_cutting_part_limit_exceeded")
    if work.cut_count is not None and work.cut_count > policy.metal_basic_max_cuts:
        return decide("sheet_laser_subcontractor", "basic_cutting_cut_limit_exceeded")

    required_evidence = {
        "part_count": work.part_count,
        "straight_edge_to_edge_cuts_only": work.straight_edge_to_edge_cuts_only,
        "cut_count": work.cut_count,
        "rough_finish_acceptable": work.rough_finish_acceptable,
        "material_and_thickness_supported": work.material_and_thickness_supported,
        "has_holes_or_internal_features": work.has_holes_or_internal_features,
        "has_curves_or_shaped_edges": work.has_curves_or_shaped_edges,
        "precision_or_repeatability_required": work.precision_or_repeatability_required,
    }
    missing = tuple(name for name, value in required_evidence.items() if value is None)
    if missing:
        return decide(
            "needs_review",
            "basic_sheet_cutting_evidence_incomplete",
            *missing,
            needs_review=True,
        )

    return decide(
        "metal_basic_sheet_cutting_in_house",
        "basic_in_house_cutting_explicitly_confirmed",
        "rough_low_volume_straight_cutting_only",
    )
