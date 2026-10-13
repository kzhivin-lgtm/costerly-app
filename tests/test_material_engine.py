from decimal import Decimal

from use_cases.material_engine import (
    MaterialDemand,
    MaterialSupplyCandidate,
    plan_material_purchases,
)


def _demand(demand_id: str, *, object_id: str = "cabinet", quantity=1, **overrides):
    values = {
        "demand_id": demand_id,
        "object_id": object_id,
        "material_family": "plywood",
        "selection_key": "plywood|18mm|raw",
        "quantity": quantity,
        "unit": "piece",
        "compatible_candidate_ids": ("sheet-2440",),
        "length_mm": 1200,
        "width_mm": 600,
    }
    values.update(overrides)
    return MaterialDemand(**values)


def _sheet(candidate_id="sheet-2440", *, price="100", length=2440, width=1220, **overrides):
    values = {
        "candidate_id": candidate_id,
        "material_family": "plywood",
        "selection_key": "plywood|18mm|raw",
        "purchase_kind": "sheet",
        "price_per_purchase_unit": price,
        "purchasable_dimensions": {"length_mm": length, "width_mm": width},
        "kerf_mm": 3,
    }
    values.update(overrides)
    return MaterialSupplyCandidate(**values)


def test_engine_nests_demands_from_multiple_objects_before_rounding_to_sheets():
    plan = plan_material_purchases(
        demands=(
            _demand("side-left", object_id="cabinet-a"),
            _demand("side-right", object_id="cabinet-b", width_mm=800),
            _demand("shelf", object_id="cabinet-b", width_mm=800),
        ),
        candidates=(_sheet(),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2")
    assert plan.lines[0].total_cost == Decimal("200")
    assert {allocation.demand_id for allocation in plan.lines[0].allocations} == {
        "side-left", "side-right", "shelf",
    }


def test_engine_selects_lowest_total_sheet_basket_not_lowest_single_sheet_price():
    demand = _demand(
        "large-panel", quantity=2, length_mm=1500, width_mm=700,
        compatible_candidate_ids=("small-cheap", "large-costly"),
    )
    plan = plan_material_purchases(
        demands=(demand,),
        candidates=(
            _sheet("small-cheap", price="80", length=1600, width=800),
            _sheet("large-costly", price="130", length=3100, width=1500),
        ),
    )

    assert plan.status == "planned"
    assert plan.lines[0].candidate_id == "large-costly"
    assert plan.lines[0].purchase_quantity == Decimal("1")
    assert plan.lines[0].total_cost == Decimal("130")


def test_engine_uses_israel_reference_only_when_no_company_candidate_can_supply_group():
    demand = _demand(
        "large-panel", quantity=2, length_mm=1500, width_mm=700,
        compatible_candidate_ids=("company-large", "israel-cheap"),
    )
    plan = plan_material_purchases(
        demands=(demand,),
        candidates=(
            _sheet("company-large", price="130", length=3100, width=1500),
            _sheet("israel-cheap", price="100", length=3100, width=1500, authority="israel_reference"),
        ),
    )

    assert plan.status == "planned"
    assert plan.lines[0].candidate_id == "company-large"


def test_engine_rounds_piece_packages_at_group_scope():
    plan = plan_material_purchases(
        demands=(
            _demand("hinges-a", object_id="cabinet-a", quantity=3, material_family="cabinet_hinge", selection_key="hinge|standard", compatible_candidate_ids=("hinge-pack",), length_mm=None, width_mm=None),
            _demand("hinges-b", object_id="cabinet-b", quantity=3, material_family="cabinet_hinge", selection_key="hinge|standard", compatible_candidate_ids=("hinge-pack",), length_mm=None, width_mm=None),
        ),
        candidates=(MaterialSupplyCandidate(
            candidate_id="hinge-pack", material_family="cabinet_hinge", selection_key="hinge|standard",
            purchase_kind="piece", price_per_purchase_unit="25", package_quantity="4",
        ),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2")
    assert plan.lines[0].total_cost == Decimal("50")


def test_engine_rounds_profile_stock_after_combining_parts():
    plan = plan_material_purchases(
        demands=(
            _demand("profile-a", object_id="cabinet-a", quantity=2, material_family="aluminium_profile", selection_key="profile|led", compatible_candidate_ids=("profile-6m",), length_mm=2400, width_mm=None),
            _demand("profile-b", object_id="cabinet-b", quantity=1, material_family="aluminium_profile", selection_key="profile|led", compatible_candidate_ids=("profile-6m",), length_mm=1100, width_mm=None),
        ),
        candidates=(MaterialSupplyCandidate(
            candidate_id="profile-6m", material_family="aluminium_profile", selection_key="profile|led",
            purchase_kind="linear_stock", price_per_purchase_unit="90",
            purchasable_dimensions={"length_mm": 6000}, kerf_mm=3,
        ),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("1")
    assert plan.lines[0].total_cost == Decimal("90")


def test_engine_marks_demand_for_review_when_no_candidate_can_physically_supply_it():
    plan = plan_material_purchases(
        demands=(_demand("oversize", length_mm=2500, width_mm=1200),),
        candidates=(_sheet(),),
    )

    assert plan.status == "needs_review"
    assert plan.unresolved_demand_ids == ("oversize",)
    assert plan.reason_codes == ("demand_exceeds_purchasable_sheet",)
