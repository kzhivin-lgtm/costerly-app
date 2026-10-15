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


def test_engine_does_not_treat_fragmented_offcuts_as_a_manual_area_norm():
    plan = plan_material_purchases(
        demands=(
            _demand("known-part", length_mm=1200, width_mm=600),
            _demand(
                "manual-norm", length_mm=None, width_mm=None,
                area_mm2=Decimal("2000000"),
            ),
        ),
        candidates=(_sheet(),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2")


def test_engine_preserves_a_requirement_already_stated_in_whole_sheets():
    plan = plan_material_purchases(
        demands=(
            _demand(
                "supplier-sheet-count", quantity=2, unit="sheet",
                length_mm=None, width_mm=None,
            ),
        ),
        candidates=(_sheet(),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2")


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


def test_engine_treats_owner_approved_one_metre_cut_as_a_physical_sheet():
    plan = plan_material_purchases(
        demands=(_demand("veneer", length_mm=900, width_mm=600, material_family="wood_veneer",
                         selection_key="veneer|oak", compatible_candidate_ids=("veneer-cut",)),),
        candidates=(MaterialSupplyCandidate(
            candidate_id="veneer-cut", material_family="wood_veneer", selection_key="veneer|oak",
            purchase_kind="sheet", price_per_purchase_unit="61",
            purchasable_dimensions={"length_mm": 1000, "width_mm": 1220},
        ),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("1")


def test_engine_prices_edge_banding_by_metre_without_rounding_to_the_roll():
    plan = plan_material_purchases(
        demands=(_demand("edge", quantity=1, length_mm=None, width_mm=None, linear_length_mm=2500,
                         material_family="edge_banding", selection_key="edge|24x5",
                         compatible_candidate_ids=("edge-cut",)),),
        candidates=(MaterialSupplyCandidate(
            candidate_id="edge-cut", material_family="edge_banding", selection_key="edge|24x5",
            purchase_kind="linear_cut", price_per_purchase_unit="3.2",
        ),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2.5")
    assert plan.lines[0].total_cost == Decimal("8.0")


def test_engine_prices_solid_timber_by_exact_part_volume():
    plan = plan_material_purchases(
        demands=(_demand("oak", quantity=1, length_mm=1000, width_mm=500,
                         volume_mm3=Decimal("10000000"), material_family="timber_solid_wood_panel",
                         selection_key="timber|oak", compatible_candidate_ids=("oak-m3",)),),
        candidates=(MaterialSupplyCandidate(
            candidate_id="oak-m3", material_family="timber_solid_wood_panel", selection_key="timber|oak",
            purchase_kind="volume_direct", price_per_purchase_unit="5000",
        ),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("0.01")
    assert plan.lines[0].total_cost == Decimal("50")


def test_engine_splits_an_oversized_finished_panel_across_joinable_stock_panels():
    plan = plan_material_purchases(
        demands=(_demand("oversize", length_mm=2500, width_mm=1200),),
        candidates=(_sheet(),),
    )

    assert plan.status == "planned"
    assert plan.lines[0].purchase_quantity == Decimal("2")
    assert sum(allocation.length_mm * allocation.width_mm for allocation in plan.lines[0].allocations) == Decimal("3000000")
