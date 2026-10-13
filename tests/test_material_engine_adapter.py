from datetime import date
from decimal import Decimal

from use_cases.material_engine_adapter import (
    company_supply_candidates,
    israel_reference_supply_candidates,
    material_plan_object_cost_allocations,
    material_plan_snapshot,
    shadow_material_plan,
)


AS_OF = date(2026, 10, 13)


def _policy():
    return {
        "family_id": "family-plywood",
        "pricing_key_attribute_codes": ["thickness"],
        "purchase_format_policy": "standard_sheet_2400x1220",
        "active": True,
    }


def _family():
    return {"family_id": "family-plywood", "family_code": "plywood", "active": True}


def _item(item_id: str = "plywood-18"):
    return {
        "company_material_id": item_id,
        "canonical_name": "Plywood 18 mm",
        "normalized_name": "plywood 18 mm",
        "status": "private",
        "specifications": {"material_family": "plywood", "thickness_mm": 18},
    }


def _offer(offer_id: str, *, item_id: str = "plywood-18", price="100", dimensions=None, **overrides):
    values = {
        "offer_id": offer_id,
        "company_material_id": item_id,
        "status": "active",
        "currency": "ILS",
        "price_scope": "material_only",
        "source_price": price,
        "source_unit": "sheet",
        "purchase_unit": "sheet",
        "calculation_unit": "sheet",
        "conversion_factor": "1",
        "normalized_price": price,
        "normalized_unit": "sheet",
        "vat_included": False,
        "purchasable_dimensions": (
            {"length_mm": 2440, "width_mm": 1220} if dimensions is None else dimensions
        ),
    }
    values.update(overrides)
    return values


def _catalogs(*offers, identities=(), prices=(), formats=()):
    return {
        "items": [_item()],
        "offers": list(offers),
        "identities": list(identities),
        "prices": list(prices),
        "material_pricing_policies": [_policy()],
        "material_families": [_family()],
        "family_supply_formats": list(formats),
    }


def _reference_identity(identity_id="reference-plywood-18"):
    return {
        "pricing_identity_id": identity_id,
        "price_attributes": {"material_family": "plywood", "thickness_mm": 18},
    }


def _reference_price(price_id="reference-price-plywood-18", *, identity_id="reference-plywood-18", unit="sqm", typical="50"):
    return {
        "pricing_identity_price_id": price_id,
        "pricing_identity_id": identity_id,
        "status": "active",
        "currency": "ILS",
        "price_scope": "material_only",
        "unit": unit,
        "price_typical": typical,
    }


def _reference_format(format_id="reference-format-plywood-2440", *, length=2440, width=1220):
    return {
        "supply_format_id": format_id,
        "family_id": "family-plywood",
        "active": True,
        "purchasable_dimensions": {"length_mm": length, "width_mm": width},
    }


def _facts(object_id: str, part_id: str, *, length=1200, width=600):
    return {
        "object_id": object_id,
        "materials": [{
            "requirement_id": "plywood", "source_name": "Plywood", "family": "plywood",
            "specification": {"thickness_mm": 18}, "quantity": 1, "unit": "m2",
        }],
        "parts": [{
            "part_id": part_id, "material_requirement_id": "plywood", "quantity": 1,
            "length_mm": length, "width_mm": width, "rotation_allowed": True,
        }],
    }


def test_company_candidate_bridge_keeps_all_estimate_ready_supplier_formats():
    selection_key, candidates = company_supply_candidates(
        requirement_name="Plywood", material_family="plywood", specifications={"thickness_mm": 18},
        company_material_items=[_item()],
        company_offers=[
            _offer("small", price="80", dimensions={"length_mm": 1600, "width_mm": 800}),
            _offer("large", price="130", dimensions={"length_mm": 3100, "width_mm": 1500}),
        ],
        material_pricing_policies=[_policy()], material_families=[_family()], as_of=AS_OF,
    )

    assert selection_key == "plywood|thickness=18"
    assert [candidate.candidate_id for candidate in candidates] == [
        "company-offer:large", "company-offer:small",
    ]
    assert all(candidate.purchase_kind == "sheet" for candidate in candidates)


def test_sheet_candidate_uses_physical_sheet_area_when_invoice_is_priced_per_sqm():
    _key, candidates = company_supply_candidates(
        requirement_name="Plywood", material_family="plywood", specifications={"thickness_mm": 18},
        company_material_items=[_item()],
        company_offers=[_offer(
            "sqm-sheet", price="146.4", source_unit="m2", purchase_unit="sheet",
            calculation_unit="m2", normalized_unit="m2", normalized_price="50",
            conversion_factor="2.928", dimensions={"length_mm": 2400, "width_mm": 1220},
        )],
        material_pricing_policies=[_policy()], material_families=[_family()], as_of=AS_OF,
    )

    assert candidates[0].price_per_purchase_unit == Decimal("146.400")
    assert candidates[0].package_quantity == Decimal("1")


def test_piece_offer_preserves_source_set_price_and_calculation_package_quantity():
    item = {
        "company_material_id": "hinge", "canonical_name": "Hinge", "normalized_name": "hinge",
        "status": "private", "specifications": {"material_family": "hinge"},
    }
    policy = {
        "family_id": "family-hinge", "pricing_key_attribute_codes": [],
        "purchase_format_policy": "not_required", "active": True,
    }
    family = {"family_id": "family-hinge", "family_code": "hardware_hinge", "active": True}
    _key, candidates = company_supply_candidates(
        requirement_name="Hinge", material_family="hinge", specifications={},
        company_material_items=[item],
        company_offers=[_offer(
            "hinge-set", item_id="hinge", price="100", source_unit="set", purchase_unit="set",
            calculation_unit="piece", normalized_unit="piece", normalized_price="50",
            conversion_factor="2", dimensions={},
        )],
        material_pricing_policies=[policy], material_families=[family], as_of=AS_OF,
    )

    assert candidates[0].purchase_kind == "piece"
    assert candidates[0].price_per_purchase_unit == Decimal("100")
    assert candidates[0].package_quantity == Decimal("2")


def test_israel_reference_candidate_uses_active_pricing_identity_and_physical_format():
    selection_key, candidates = israel_reference_supply_candidates(
        material_family="plywood",
        specifications={"thickness_mm": 18},
        pricing_identities=[_reference_identity()],
        pricing_identity_prices=[_reference_price()],
        material_pricing_policies=[_policy()],
        material_families=[_family()],
        family_supply_formats=[_reference_format()],
        as_of=AS_OF,
    )

    assert selection_key == "plywood|thickness=18"
    assert len(candidates) == 1
    assert candidates[0].candidate_id == "israel-reference:reference-price-plywood-18:reference-format-plywood-2440"
    assert candidates[0].authority == "israel_reference"
    assert candidates[0].purchase_kind == "sheet"
    assert candidates[0].price_per_purchase_unit == Decimal("148.840")


def test_reference_candidate_bridges_its_older_underscored_family_label():
    policy = {
        "family_id": "family-acrylic", "pricing_key_attribute_codes": ["thickness"],
        "purchase_format_policy": "required", "active": True,
    }
    family = {"family_id": "family-acrylic", "family_code": "acrylic_pmma", "active": True}
    identity = {
        "pricing_identity_id": "reference-acrylic-20",
        "price_attributes": {"material_family": "acrylic_sheet", "thickness_mm": 20},
    }
    price = _reference_price(
        "reference-price-acrylic-20", identity_id="reference-acrylic-20", typical="80",
    )
    supply_format = {
        "supply_format_id": "reference-format-acrylic-3050",
        "family_id": "family-acrylic", "active": True,
        "purchasable_dimensions": {"length_mm": 3050, "width_mm": 2030},
    }

    selection_key, candidates = israel_reference_supply_candidates(
        material_family="acrylic sheet", specifications={"thickness_mm": 20},
        pricing_identities=[identity], pricing_identity_prices=[price],
        material_pricing_policies=[policy], material_families=[family],
        family_supply_formats=[supply_format], as_of=AS_OF,
    )

    assert selection_key == "acrylic_pmma|thickness=20"
    assert [candidate.candidate_id for candidate in candidates] == [
        "israel-reference:reference-price-acrylic-20:reference-format-acrylic-3050",
    ]


def test_reference_sheet_price_is_not_assigned_to_an_unlinked_generic_format():
    _key, candidates = israel_reference_supply_candidates(
        material_family="plywood",
        specifications={"thickness_mm": 18},
        pricing_identities=[_reference_identity()],
        pricing_identity_prices=[_reference_price(unit="sheet", typical="150")],
        material_pricing_policies=[_policy()],
        material_families=[_family()],
        family_supply_formats=[_reference_format()],
        as_of=AS_OF,
    )

    assert candidates == ()


def test_shadow_plan_combines_part_demands_across_objects_before_sheet_rounding():
    shadow = shadow_material_plan(
        facts_by_object={
            "cabinet-a": _facts("cabinet-a", "side-a", width=800),
            "cabinet-b": _facts("cabinet-b", "side-b", width=800),
        },
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert shadow.unresolved_requirement_ids == ()
    assert shadow.plan is not None
    assert shadow.plan.status == "planned"
    assert shadow.plan.lines[0].purchase_quantity == Decimal("1")
    assert {allocation.demand_id for allocation in shadow.plan.lines[0].allocations} == {
        "cabinet-a:side-a", "cabinet-b:side-b",
    }


def test_shadow_uses_israel_reference_when_no_complete_company_basket_exists():
    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=2000, width=1000)},
        catalogs=_catalogs(
            _offer("small", price="80", dimensions={"length_mm": 1600, "width_mm": 800}),
            identities=[_reference_identity()],
            prices=[_reference_price()],
            formats=[_reference_format()],
        ),
    )

    assert shadow.plan is not None
    assert shadow.plan.status == "planned"
    assert shadow.plan.lines[0].candidate_id.startswith("israel-reference:")


def test_shadow_keeps_complete_company_basket_even_when_reference_is_cheaper():
    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=1200, width=600)},
        catalogs=_catalogs(
            _offer("company", price="500"),
            identities=[_reference_identity()],
            prices=[_reference_price()],
            formats=[_reference_format()],
        ),
    )

    assert shadow.plan is not None
    assert shadow.plan.status == "planned"
    assert shadow.plan.lines[0].candidate_id == "company-offer:company"


def test_material_plan_snapshot_preserves_purchase_and_object_traceability():
    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=1200, width=600)},
        catalogs=_catalogs(_offer("company", price="100")),
    )

    snapshot = material_plan_snapshot(shadow)

    assert snapshot["status"] == "planned"
    assert snapshot["lines"][0]["authority"] == "company"
    assert snapshot["lines"][0]["total_cost"] == 100.0
    assert snapshot["lines"][0]["allocations"] == [{
        "demand_id": "cabinet-a:side-a", "purchase_index": 1,
        "object_id": "cabinet-a", "material_requirement_id": "plywood",
        "length_mm": 1200.0, "width_mm": 600.0, "area_mm2": None,
        "quantity": 1.0, "rotated": False,
    }]


def test_shared_purchase_cost_is_allocated_back_to_each_object_without_rounding_gap():
    shadow = shadow_material_plan(
        facts_by_object={
            "cabinet-a": _facts("cabinet-a", "side-a", width=800),
            "cabinet-b": _facts("cabinet-b", "side-b", width=800),
        },
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    allocations = material_plan_object_cost_allocations(shadow)

    assert allocations == {
        ("cabinet-a", "plywood"): Decimal("50.00"),
        ("cabinet-b", "plywood"): Decimal("50.00"),
    }
    assert sum(allocations.values()) == shadow.plan.lines[0].total_cost


def test_shadow_uses_net_material_area_when_parts_are_unavailable():
    facts = _facts("cabinet-a", "side-a")
    facts["parts"] = []

    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert shadow.plan is not None
    assert shadow.plan.status == "planned"
    assert shadow.plan.lines[0].purchase_quantity == Decimal("1")
    assert shadow.reason_codes == ()


def test_manual_norm_creates_an_area_demand_without_inventing_part_geometry():
    facts = _facts("cabinet-a", "side-a", length=1200, width=600)
    facts["quantity"] = 1

    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
        material_norm_overrides={
            ("cabinet-a", "plywood"): {"quantity_per_item": 2, "unit": "m2"},
        },
    )

    assert shadow.plan is not None
    assert shadow.plan.status == "planned"
    assert shadow.plan.lines[0].purchase_quantity == Decimal("1")
    # The override replaces, rather than supplements, the original part
    # geometry. Two square metres fit in one 2.976 m2 sheet.
    assert shadow.reason_codes == ("manual_material_norm_without_geometry",)


def test_manual_norm_scales_by_the_object_target_quantity():
    facts = _facts("cabinet-a", "side-a")
    facts["quantity"] = 2
    facts["parts"] = []

    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
        material_norm_overrides={
            ("cabinet-a", "plywood"): {"quantity_per_item": 2, "unit": "m2"},
        },
    )

    assert shadow.plan is not None
    assert shadow.plan.lines[0].purchase_quantity == Decimal("2")
    snapshot = material_plan_snapshot(shadow)
    assert snapshot["object_material_costs"] == [{
        "object_id": "cabinet-a", "material_requirement_id": "plywood", "cost_ex_vat": 200.0,
    }]


def test_shadow_marks_assumption_required_only_after_company_and_israel_have_no_candidate():
    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a")},
        catalogs=_catalogs(),
    )

    assert shadow.plan is None
    assert shadow.unresolved_requirement_ids == ("cabinet-a:plywood",)
    assert shadow.reason_codes == ("assumption_required",)
