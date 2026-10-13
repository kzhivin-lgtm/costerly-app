from datetime import date
from decimal import Decimal

from use_cases.material_engine_adapter import company_supply_candidates, shadow_material_plan


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


def _catalogs(*offers):
    return {
        "items": [_item()],
        "offers": list(offers),
        "material_pricing_policies": [_policy()],
        "material_families": [_family()],
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


def test_shadow_records_missing_parts_without_reverting_to_legacy_area_pricing():
    facts = _facts("cabinet-a", "side-a")
    facts["parts"] = []

    shadow = shadow_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert shadow.plan is None
    assert shadow.unresolved_requirement_ids == ("cabinet-a:plywood",)
    assert shadow.reason_codes == ("material_parts_missing",)
