from datetime import date
from decimal import Decimal

from use_cases.material_engine_adapter import (
    company_supply_candidates,
    israel_reference_supply_candidates,
    material_plan_object_cost_allocations,
    material_plan_snapshot,
    build_material_plan,
    replan_material_norm_snapshot,
    reprice_material_purchase_snapshot,
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


def _catalogs(*offers, reference_positions=()):
    return {
        "items": [_item()],
        "offers": list(offers),
        "reference_positions": list(reference_positions),
        "material_pricing_policies": [_policy()],
        "material_families": [_family()],
    }


def _reference_position(position_id="reference-plywood-18", *, specifications=None, prices=None, formats=None):
    return {
        "reference_position_id": position_id,
        "family_code": "plywood",
        "specifications": specifications or {"thickness_mm": 18},
        "prices": list(prices or ()),
        "supply_formats": list(formats or ()),
    }


def _reference_price(price_id="reference-price-plywood-18", *, unit="sqm", typical="50"):
    return {
        "model_price_id": price_id,
        "status": "active",
        "currency": "ILS",
        "price_scope": "material_only",
        "unit": unit,
        "price_typical": typical,
    }


def _reference_format(format_id="reference-format-plywood-2440", *, length=2440, width=1220):
    return {
        "supply_format_id": format_id,
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
        "status": "private", "specifications": {"material_family": "hardware_hinge"},
    }
    policy = {
        "family_id": "family-hinge", "pricing_key_attribute_codes": [],
        "purchase_format_policy": "not_required", "active": True,
    }
    family = {"family_id": "family-hinge", "family_code": "hardware_hinge", "active": True}
    _key, candidates = company_supply_candidates(
        requirement_name="Hinge", material_family="hardware_hinge", specifications={},
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
        reference_positions=[_reference_position(
            prices=[_reference_price()], formats=[_reference_format()],
        )],
        material_pricing_policies=[_policy()],
        material_families=[_family()],
        as_of=AS_OF,
    )

    assert selection_key == "plywood|thickness=18"
    assert len(candidates) == 1
    assert candidates[0].candidate_id == "israel-reference:reference-plywood-18:reference-price-plywood-18:reference-format-plywood-2440"
    assert candidates[0].authority == "israel_reference"
    assert candidates[0].purchase_kind == "sheet"
    assert candidates[0].price_per_purchase_unit == Decimal("148.840")


def test_reference_candidate_bridges_its_older_underscored_family_label():
    policy = {
        "family_id": "family-acrylic", "pricing_key_attribute_codes": ["thickness"],
        "purchase_format_policy": "required", "active": True,
    }
    family = {"family_id": "family-acrylic", "family_code": "acrylic_pmma", "active": True}
    position = {
        "reference_position_id": "reference-acrylic-20",
        "family_code": "acrylic_pmma",
        "specifications": {"thickness_mm": 20},
        "prices": [], "supply_formats": [],
    }
    price = _reference_price(
        "reference-price-acrylic-20", typical="80",
    )
    supply_format = {
        "supply_format_id": "reference-format-acrylic-3050",
        "purchasable_dimensions": {"length_mm": 3050, "width_mm": 2030},
    }

    selection_key, candidates = israel_reference_supply_candidates(
        material_family="acrylic_pmma", specifications={"thickness_mm": 20},
        reference_positions=[{**position, "prices": [price], "supply_formats": [supply_format]}],
        material_pricing_policies=[policy], material_families=[family],
        as_of=AS_OF,
    )

    assert selection_key == "acrylic_pmma|thickness=20"
    assert [candidate.candidate_id for candidate in candidates] == [
        "israel-reference:reference-acrylic-20:reference-price-acrylic-20:reference-format-acrylic-3050",
    ]


def test_reference_sheet_price_uses_only_its_linked_physical_format():
    _key, candidates = israel_reference_supply_candidates(
        material_family="plywood",
        specifications={"thickness_mm": 18},
        reference_positions=[_reference_position(
            prices=[_reference_price(unit="sheet", typical="150")], formats=[_reference_format()],
        )],
        material_pricing_policies=[_policy()],
        material_families=[_family()],
        as_of=AS_OF,
    )

    assert len(candidates) == 1
    assert candidates[0].purchase_kind == "sheet"
    assert candidates[0].price_per_purchase_unit == Decimal("150")
    assert candidates[0].candidate_id == (
        "israel-reference:reference-plywood-18:reference-price-plywood-18:"
        "reference-format-plywood-2440"
    )


def test_reference_candidates_require_the_exact_pricing_key():
    _key, candidates = israel_reference_supply_candidates(
        material_family="plywood",
        specifications={"thickness_mm": 18},
        reference_positions=[
            _reference_position(
                "plywood-18",
                prices=[_reference_price("price-18")], formats=[_reference_format()],
            ),
            _reference_position(
                "plywood-12",
                specifications={"thickness_mm": 12},
                prices=[_reference_price("price-12")], formats=[_reference_format("format-12")],
            ),
        ],
        material_pricing_policies=[_policy()], material_families=[_family()], as_of=AS_OF,
    )

    assert [candidate.reference_price_id for candidate in candidates] == ["price-18"]


def test_plan_combines_part_demands_across_objects_before_sheet_rounding():
    result = build_material_plan(
        facts_by_object={
            "cabinet-a": _facts("cabinet-a", "side-a", width=800),
            "cabinet-b": _facts("cabinet-b", "side-b", width=800),
        },
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert result.unresolved_requirement_ids == ()
    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].purchase_quantity == Decimal("1")
    assert {allocation.demand_id for allocation in result.plan.lines[0].allocations} == {
        "cabinet-a:side-a", "cabinet-b:side-b",
    }


def test_plan_skips_physically_incompatible_company_sheet_for_compatible_israel_sheet():
    result = build_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=2000, width=1000)},
        catalogs=_catalogs(
            _offer("small", price="80", dimensions={"length_mm": 1600, "width_mm": 800}),
            reference_positions=[_reference_position(
                prices=[_reference_price()], formats=[_reference_format()],
            )],
        ),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id.startswith("israel-reference:reference-plywood-18:")


def test_plan_keeps_complete_company_basket_even_when_reference_is_cheaper():
    result = build_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=1200, width=600)},
        catalogs=_catalogs(
            _offer("company", price="500"),
            reference_positions=[_reference_position(
                prices=[_reference_price()], formats=[_reference_format()],
            )],
        ),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id == "company-offer:company"


def test_plan_completes_a_proven_family_from_an_active_israel_default():
    facts = _facts("cabinet-a", "side-a")
    facts["materials"][0]["specification"] = {}
    catalogs = _catalogs(
        reference_positions=[_reference_position(
            prices=[_reference_price()], formats=[_reference_format()],
        )],
    )
    catalogs["material_default_variants"] = [{
        "default_variant_id": "plywood-18-default",
        "family_id": "family-plywood",
        "reference_position_id": "reference-plywood-18",
        "default_specifications": {"thickness_mm": 18},
        "priority": 10,
        "active": True,
    }]

    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=catalogs,
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.applied_defaults == ({
        "object_id": "cabinet-a",
        "material_requirement_id": "plywood",
        "default_variant_id": "plywood-18-default",
        "reference_position_id": "reference-plywood-18",
        "family_code": "plywood",
        "applied_specifications": {"thickness_mm": 18},
    },)
    assert material_plan_snapshot(result)["applied_material_defaults"] == [
        dict(result.applied_defaults[0])
    ]


def test_profile_dimension_never_uses_an_unrelated_family_default():
    facts = {
        "object_id": "frame-a",
        "materials": [{
            "requirement_id": "tube", "source_name": "Metal profile 20x20", "family": "metal_tube",
            "specification": {"profile_section": "20x20"}, "quantity": 4, "unit": "m",
        }],
        "parts": [],
    }
    policy = {
        "family_id": "family-tube", "pricing_key_attribute_codes": ["section_profile", "metal_type"],
        "purchase_format_policy": "required", "active": True,
    }
    family = {"family_id": "family-tube", "family_code": "metal_tube", "active": True}
    def position(position_id, specs):
        return {
            "reference_position_id": position_id, "family_code": "metal_tube",
            "specifications": specs,
            "prices": [_reference_price(f"{position_id}-price", unit="m", typical="10")],
            "supply_formats": [{"supply_format_id": f"{position_id}-6m", "active": True,
                                "purchasable_dimensions": {"length_mm": 6000}}],
        }

    result = build_material_plan(
        facts_by_object={"frame-a": facts},
        catalogs={
            "items": [], "offers": [],
            "reference_positions": [
                position("reference-round-default", {"section_profile": "round_tube_d20", "metal_type": "steel"}),
                position("reference-square-20", {"section_profile": "square_tube_20x20", "metal_type": "steel"}),
            ],
            "material_pricing_policies": [policy], "material_families": [family],
            "material_default_variants": [{
                "default_variant_id": "tube-default", "family_id": "family-tube",
                "reference_position_id": "reference-round-default",
                "default_specifications": {"metal_type": "steel", "section_profile": "round_tube_d20"},
                "applicability_specifications": {}, "priority": 10, "active": True,
            }],
        },
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id.startswith("assumption:")
    assert result.applied_defaults == ()
    assert result.assumption_fallbacks[0]["reason_code"] == "material_pricing_key_incomplete"
    assert result.assumption_fallbacks[0]["selection_key"] == "assumption:frame-a:metal_tube:tube"


def test_melamine_one_sided_missing_thickness_uses_generic_laminated_default_position():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "front", "source_name": "Melamine MDF", "family": "mdf_hdf",
            "specification": {"board_type": "mdf", "surface": "melamine_one_sided"},
            "quantity": 1, "unit": "m2",
        }],
        "parts": [{
            "part_id": "front-a", "material_requirement_id": "front", "quantity": 1,
            "length_mm": 600, "width_mm": 400, "rotation_allowed": True,
        }],
    }
    policy = {
        "family_id": "family-mdf", "pricing_key_attribute_codes": ["board_type", "surface", "thickness"],
        "purchase_format_policy": "standard_sheet_2400x1220", "active": True,
    }
    family = {"family_id": "family-mdf", "family_code": "mdf_hdf", "active": True}
    position = {
        "reference_position_id": "reference-mdf-laminated-17", "family_code": "mdf_hdf",
        "specifications": {"board_type": "mdf", "surface": "laminated", "thickness_mm": 17},
        "prices": [_reference_price("price-mdf-laminated-17")],
        "supply_formats": [_reference_format("format-mdf-laminated-17")],
    }
    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs={
            "items": [], "offers": [], "reference_positions": [position],
            "material_pricing_policies": [policy], "material_families": [family],
            "material_default_variants": [{
                "default_variant_id": "melamine-one-to-laminated-17",
                "family_id": "family-mdf", "reference_position_id": "reference-mdf-laminated-17",
                "default_specifications": {"thickness_mm": 17},
                "applicability_specifications": {"board_type": "mdf", "surface": "melamine_one_sided"},
                "priority": 31, "active": True,
            }],
        },
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.applied_defaults[0]["source_specifications"] == {
        "board_type": "mdf", "surface": "melamine_one_sided",
    }
    assert result.applied_defaults[0]["purchase_specifications"] == {
        "board_type": "mdf", "surface": "laminated", "thickness_mm": 17,
    }


def test_hardware_default_can_use_active_package_price():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "hinge", "source_name": "Cabinet hinge", "family": "hardware_hinge",
            "specification": {}, "quantity": 2, "unit": "piece",
        }],
        "parts": [],
    }
    policy = {
        "family_id": "family-hinge", "pricing_key_attribute_codes": [],
        "purchase_format_policy": "not_required", "active": True,
    }
    family = {"family_id": "family-hinge", "family_code": "hardware_hinge", "active": True}
    position = {
        "reference_position_id": "reference-standard-hinge", "family_code": "hardware_hinge",
        "specifications": {},
        "prices": [{
            "model_price_id": "price-standard-hinge", "status": "active", "currency": "ILS",
            "price_scope": "retail_package", "unit": "ea", "price_typical": "22",
        }],
        "supply_formats": [],
    }
    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs={
            "items": [], "offers": [], "reference_positions": [position],
            "material_pricing_policies": [policy], "material_families": [family],
            "material_default_variants": [{
                "default_variant_id": "hardware-hinge-default", "family_id": "family-hinge",
                "reference_position_id": "reference-standard-hinge", "default_specifications": {},
                "applicability_specifications": {}, "priority": 100, "active": True,
            }],
        },
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].purchase_kind == "piece"
    assert result.plan.lines[0].price_per_purchase_unit == Decimal("22")


def test_material_plan_snapshot_preserves_purchase_and_object_traceability():
    result = build_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a", length=1200, width=600)},
        catalogs=_catalogs(_offer("company", price="100", dimensions={
            "length_mm": 2440, "width_mm": 1220, "format_source": "approved_catalog_default",
        })),
    )

    snapshot = material_plan_snapshot(result)

    assert snapshot["status"] == "planned"
    assert snapshot["lines"][0]["authority"] == "company"
    assert snapshot["lines"][0]["display_name"] == "Plywood 18 mm"
    assert snapshot["lines"][0]["purchasable_dimensions"] == {"length_mm": 2440.0, "width_mm": 1220.0}
    assert snapshot["lines"][0]["total_cost"] == 100.0
    assert snapshot["lines"][0]["allocations"] == [{
        "demand_id": "cabinet-a:side-a", "purchase_index": 1,
        "object_id": "cabinet-a", "material_requirement_id": "plywood",
        "length_mm": 1200.0, "width_mm": 600.0, "area_mm2": 720000.0,
        "quantity": 1.0, "rotated": False,
    }]


def test_shared_purchase_cost_is_allocated_back_to_each_object_without_rounding_gap():
    result = build_material_plan(
        facts_by_object={
            "cabinet-a": _facts("cabinet-a", "side-a", width=800),
            "cabinet-b": _facts("cabinet-b", "side-b", width=800),
        },
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    allocations = material_plan_object_cost_allocations(result)

    assert allocations == {
        ("cabinet-a", "plywood"): Decimal("50.00"),
        ("cabinet-b", "plywood"): Decimal("50.00"),
    }
    assert sum(allocations.values()) == result.plan.lines[0].total_cost


def test_editing_purchase_quantity_uses_existing_demands_and_reallocates_both_objects():
    facts = {
        "cabinet-a": _facts("cabinet-a", "side-a", width=800),
        "cabinet-b": _facts("cabinet-b", "side-b", width=800),
    }
    catalogs = _catalogs(_offer("sheet", price="100"))
    saved = material_plan_snapshot(build_material_plan(facts_by_object=facts, catalogs=catalogs))
    saved["parts_check"] = {"cabinet-a": {"parts": ["unchanged"]}}
    original = saved["lines"][0]
    overrides = {original["selection_key"]: {"purchase_quantity": 3}}
    updated, changed = reprice_material_purchase_snapshot(saved, overrides)
    rebuilt = material_plan_snapshot(build_material_plan(
        facts_by_object=facts, catalogs=catalogs, material_purchase_overrides=overrides,
    ))

    assert changed == {("cabinet-a", "plywood"), ("cabinet-b", "plywood")}
    assert updated["object_material_costs"] == rebuilt["object_material_costs"]
    assert updated["lines"] == rebuilt["lines"]
    assert updated["parts_check"] == saved["parts_check"]
    assert original["purchase_quantity"] == 1
    assert updated["lines"][0]["purchase_quantity"] == 3


def test_plan_uses_net_material_area_when_parts_are_unavailable():
    facts = _facts("cabinet-a", "side-a")
    facts["parts"] = []

    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].purchase_quantity == Decimal("1")
    assert result.reason_codes == ()


def test_editing_one_sheet_norm_replans_only_its_saved_stock_and_keeps_other_parts():
    facts = {
        "cabinet-a": _facts("cabinet-a", "side-a", width=800),
        "cabinet-b": _facts("cabinet-b", "side-b", width=800),
    }
    catalogs = _catalogs(_offer("sheet", price="100"))
    saved = material_plan_snapshot(build_material_plan(facts_by_object=facts, catalogs=catalogs))
    (original,) = saved["lines"]
    unrelated = {**original, "selection_key": "other-stock"}
    saved["lines"].append(unrelated)
    norms = {("cabinet-a", "plywood"): {"quantity_per_item": 3.3, "unit": "m²"}}

    updated, changed = replan_material_norm_snapshot(
        saved, norms, {"cabinet-a": 1}, {}, changed_keys={original["selection_key"]},
    )
    rebuilt = material_plan_snapshot(build_material_plan(
        facts_by_object=facts, catalogs=catalogs, material_norm_overrides=norms,
    ))

    assert changed == {("cabinet-a", "plywood"), ("cabinet-b", "plywood")}
    assert updated["object_material_costs"] == rebuilt["object_material_costs"]
    assert updated["lines"] == [rebuilt["lines"][0], unrelated]


def test_manual_norm_creates_an_area_demand_without_inventing_part_geometry():
    facts = _facts("cabinet-a", "side-a", length=1200, width=600)
    facts["quantity"] = 1

    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
        material_norm_overrides={
            ("cabinet-a", "plywood"): {"quantity_per_item": 2, "unit": "m2"},
        },
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].purchase_quantity == Decimal("1")
    # The override replaces, rather than supplements, the original part
    # geometry. Two square metres fit in one 2.976 m2 sheet.
    assert result.reason_codes == ("manual_material_norm_without_geometry",)


def test_manual_norm_scales_by_the_object_target_quantity():
    facts = _facts("cabinet-a", "side-a")
    facts["quantity"] = 2
    facts["parts"] = []

    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
        material_norm_overrides={
            ("cabinet-a", "plywood"): {"quantity_per_item": 2, "unit": "m2"},
        },
    )

    assert result.plan is not None
    assert result.plan.lines[0].purchase_quantity == Decimal("2")
    snapshot = material_plan_snapshot(result)
    assert snapshot["object_material_costs"] == [{
        "object_id": "cabinet-a", "material_requirement_id": "plywood", "cost_ex_vat": 200.0,
    }]


def test_plan_prices_assumption_fallback_after_company_and_israel_have_no_candidate():
    result = build_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "side-a")},
        catalogs=_catalogs(),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].total_cost == Decimal("200")
    assert result.unresolved_requirement_ids == ()
    assert result.reason_codes == ("assumption_fallback",)
    fallback = result.assumption_fallbacks[0]
    assert fallback["reason_code"] == "no_company_or_israel_candidate"
    assert fallback["resolution"] == "assumption_fallback"
    assert fallback["assumption_price"] == {
        "contract_version": "estimation_assumption_price_v1",
        "material_requirement_id": "plywood", "amount": 200.0,
        "currency": "ILS", "unit": "sheet", "confidence": 0.0,
        "basis_kind": "estimator_allowance",
        "rationale": [
            "No compatible Company Catalog or Israel Reference purchase candidate was available.",
            "A fixed 200 ILS allowance was applied for sheet (no_company_or_israel_candidate).",
        ],
        "source_candidates": [],
    }


def test_required_piece_override_recalculates_assumption_purchase():
    facts = {
        "object_id": "bench", "quantity": 1,
        "materials": [{
            "requirement_id": "leg", "source_name": "Furniture leg",
            "family": "purchased_fabricated_component", "specification": {},
            "quantity": 2, "unit": "piece", "assumption_reason": "material_pricing_key_incomplete",
        }],
        "parts": [],
    }
    result = build_material_plan(
        facts_by_object={"bench": facts}, catalogs=_catalogs(),
        material_norm_overrides={("bench", "leg"): {"unit": "piece", "quantity_per_item": 3}},
    )
    line = result.plan.lines[0]
    assert line.allocations[0].quantity == 3
    assert line.purchase_quantity == 3
    assert line.total_cost == 600


def test_oversized_finished_part_uses_dimension_compatible_assumption_not_sheet_split():
    result = build_material_plan(
        facts_by_object={"cabinet-a": _facts("cabinet-a", "tall-side", length=2650, width=600)},
        catalogs=_catalogs(_offer("company-sheet", dimensions={"length_mm": 2440, "width_mm": 1220})),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id == "assumption:cabinet-a:plywood:sheet"
    assert result.plan.lines[0].purchase_quantity == Decimal("1")
    assert result.plan.lines[0].allocations[0].length_mm == Decimal("2650")
    assert result.assumption_fallbacks[0]["resolution"] == "assumption_fallback"


def test_parts_check_prices_an_oversized_panel_from_catalog_sheet_area():
    facts = _facts("cabinet-a", "long-panel", length=3200, width=1000)
    facts["composition_version"] = "cb_parts_material_demand_v1"
    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("company-sheet", dimensions={"length_mm": 2440, "width_mm": 1220})),
    )

    assert not result.assumption_fallbacks
    line, = result.plan.lines
    assert line.purchase_quantity == 2
    allocation, = line.allocations
    assert allocation.length_mm == 3200
    assert allocation.area_mm2 == 3200000


def test_plan_uses_evidenced_count_only_for_discrete_resolved_materials():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "hinge", "source_name": "Cabinet hinge", "family": "hardware_hinge",
            "specification": {}, "quantity": 4, "unit": None,
        }],
        "parts": [],
    }
    catalogs = {
        "items": [{
            "company_material_id": "hinge", "canonical_name": "Cabinet hinge",
            "normalized_name": "cabinet hinge", "status": "private",
            "specifications": {"material_family": "hardware_hinge"},
        }],
        "offers": [{
                "offer_id": "hinge-piece", "company_material_id": "hinge", "status": "active",
                "currency": "ILS", "price_scope": "retail_package", "source_price": "10",
            "source_unit": "piece", "purchase_unit": "piece", "calculation_unit": "piece",
            "conversion_factor": "1", "normalized_price": "10", "normalized_unit": "ea",
            "vat_included": False, "purchasable_dimensions": None,
        }],
        "reference_positions": [],
        "material_pricing_policies": [{
            "family_id": "family-hinge", "pricing_key_attribute_codes": [],
            "purchase_format_policy": "discrete", "active": True,
        }],
        "material_families": [{"family_id": "family-hinge", "family_code": "hardware_hinge", "active": True}],
    }

    result = build_material_plan(facts_by_object={"cabinet-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].purchase_kind == "piece"
    assert result.plan.lines[0].purchase_quantity == Decimal("4")


def test_drawer_slide_without_evidenced_depth_uses_last_resort_400_mm_policy():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "drawer-slide", "source_name": "Drawer slide",
            "family": "hardware_drawer_slide", "specification": {},
            "quantity": 2, "unit": None,
        }],
        "parts": [],
    }
    catalogs = {
        "items": [{
            "company_material_id": "slide-400", "canonical_name": "Drawer slide 400 mm",
            "normalized_name": "drawer slide 400 mm", "status": "private",
            "specifications": {"material_family": "hardware_drawer_slide", "depth_mm": 400},
        }],
        "offers": [{
            "offer_id": "slide-400-package", "company_material_id": "slide-400", "status": "active",
            "currency": "ILS", "price_scope": "retail_package", "source_price": "30",
            "source_unit": "piece", "purchase_unit": "piece", "calculation_unit": "piece",
            "conversion_factor": "1", "normalized_price": "30", "normalized_unit": "ea",
            "vat_included": False, "purchasable_dimensions": None,
        }],
        "reference_positions": [],
        "material_pricing_policies": [{
            "family_id": "family-drawer-slide", "pricing_key_attribute_codes": ["depth_mm"],
            "purchase_format_policy": "not_required", "active": True,
        }],
        "material_families": [{
            "family_id": "family-drawer-slide", "family_code": "hardware_drawer_slide", "active": True,
        }],
    }

    result = build_material_plan(facts_by_object={"cabinet-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.candidate_authorities == (("company-offer:slide-400-package", "company"),)
    assert result.applied_defaults == ({
        "object_id": "cabinet-a", "material_requirement_id": "drawer-slide",
        "policy": "drawer_slide_last_resort_depth", "family_code": "hardware_drawer_slide",
        "applied_specifications": {"depth_mm": 400},
    },)


def test_drawer_slide_last_resort_policy_never_overwrites_evidenced_depth():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "drawer-slide", "source_name": "Drawer slide",
            "family": "hardware_drawer_slide", "specification": {"depth_mm": 500},
            "quantity": 1, "unit": None,
        }],
        "parts": [],
    }
    catalogs = {
        "items": [{
            "company_material_id": "slide-500", "canonical_name": "Drawer slide 500 mm",
            "normalized_name": "drawer slide 500 mm", "status": "private",
            "specifications": {"material_family": "hardware_drawer_slide", "depth_mm": 500},
        }],
        "offers": [{
            "offer_id": "slide-500-package", "company_material_id": "slide-500", "status": "active",
            "currency": "ILS", "price_scope": "retail_package", "source_price": "35",
            "source_unit": "piece", "purchase_unit": "piece", "calculation_unit": "piece",
            "conversion_factor": "1", "normalized_price": "35", "normalized_unit": "ea",
            "vat_included": False, "purchasable_dimensions": None,
        }],
        "reference_positions": [],
        "material_pricing_policies": [{
            "family_id": "family-drawer-slide", "pricing_key_attribute_codes": ["depth_mm"],
            "purchase_format_policy": "not_required", "active": True,
        }],
        "material_families": [{
            "family_id": "family-drawer-slide", "family_code": "hardware_drawer_slide", "active": True,
        }],
    }

    result = build_material_plan(facts_by_object={"cabinet-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.candidate_authorities == (("company-offer:slide-500-package", "company"),)
    assert result.applied_defaults == ()


def test_drawer_slide_400_mm_last_resort_falls_back_to_israel_when_company_is_absent():
    facts = {
        "object_id": "cabinet-a",
        "materials": [{
            "requirement_id": "drawer-slide", "source_name": "Drawer slide",
            "family": "hardware_drawer_slide", "specification": {},
            "quantity": 1, "unit": None,
        }],
        "parts": [],
    }
    policy = {
        "family_id": "family-drawer-slide", "pricing_key_attribute_codes": ["depth_mm"],
        "purchase_format_policy": "not_required", "active": True,
    }
    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs={
            "items": [], "offers": [],
            "reference_positions": [{
                "reference_position_id": "reference-slide-400", "family_code": "hardware_drawer_slide",
                "specifications": {"depth_mm": 400}, "supply_formats": [],
                "prices": [{
                    "model_price_id": "price-slide-400", "status": "active", "currency": "ILS",
                    "price_scope": "retail_package", "unit": "ea", "price_typical": "40",
                }],
            }],
            "material_pricing_policies": [policy],
            "material_families": [{
                "family_id": "family-drawer-slide", "family_code": "hardware_drawer_slide", "active": True,
            }],
        },
    )

    assert result.plan is not None
    assert result.plan.lines[0].candidate_id == "israel-reference:reference-slide-400:price-slide-400"
    assert result.applied_defaults[0]["applied_specifications"] == {"depth_mm": 400}


def test_plan_does_not_treat_a_profile_count_as_a_linear_demand():
    facts = {
        "object_id": "shelf-a",
        "materials": [{
            "requirement_id": "tube", "source_name": "Square steel tube", "family": "metal_tube",
            "specification": {}, "quantity": 1, "unit": None,
        }],
        "parts": [],
    }
    catalogs = {
        "items": [{
            "company_material_id": "tube", "canonical_name": "Square steel tube",
            "normalized_name": "square steel tube", "status": "private",
            "specifications": {"material_family": "metal_tube"},
        }],
        "offers": [{
            "offer_id": "tube-linear", "company_material_id": "tube", "status": "active",
            "currency": "ILS", "price_scope": "material_only", "source_price": "30",
            "source_unit": "m", "purchase_unit": "m", "calculation_unit": "m",
            "conversion_factor": "1", "normalized_price": "30", "normalized_unit": "lm",
            "vat_included": False, "purchasable_dimensions": {"length_mm": 6000},
        }],
        "reference_positions": [],
        "material_pricing_policies": [{
            "family_id": "family-tube", "pricing_key_attribute_codes": [],
            "purchase_format_policy": "linear", "active": True,
        }],
        "material_families": [{"family_id": "family-tube", "family_code": "metal_tube", "active": True}],
    }

    result = build_material_plan(facts_by_object={"shelf-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id.startswith("assumption:")
    assert result.unresolved_requirement_ids == ()
    assert result.reason_codes == ("assumption_fallback",)
    assert result.assumption_fallbacks[0]["reason_code"] == "material_geometry_required"


def test_known_discrete_material_keeps_catalog_authority_when_its_count_is_assumed():
    facts = {
        "object_id": "cabinet-a", "quantity": 2,
        "materials": [{
            "requirement_id": "handle", "source_name": "Handle", "family": "hardware_handle",
            "specification": {}, "quantity": None, "unit": None,
        }],
        "parts": [],
    }
    catalogs = _catalogs(_offer(
        "piece", item_id="handle", price="12", source_unit="piece", purchase_unit="piece",
        calculation_unit="piece", normalized_unit="piece", dimensions={}, price_scope="retail_package",
    ))
    catalogs["items"] = [{
        "company_material_id": "handle", "canonical_name": "Handle", "normalized_name": "handle",
        "status": "private", "specifications": {"material_family": "hardware_handle"},
    }]
    catalogs["material_families"] = [{
        "family_id": "family-plywood", "family_code": "hardware_handle", "active": True,
    }]
    catalogs["material_pricing_policies"] = [{
        "family_id": "family-plywood", "pricing_key_attribute_codes": [],
        "purchase_format_policy": "not_required", "active": True,
    }]

    result = build_material_plan(facts_by_object={"cabinet-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.plan.lines[0].candidate_id == "company-offer:piece"
    assert result.plan.lines[0].purchase_quantity == Decimal("2")
    assert result.assumption_fallbacks == ()
    assert "assumed_discrete_quantity" in result.reason_codes
    assert result.applied_defaults[-1]["default_type"] == "assumed_one_discrete_item_per_finished_object"


def test_plan_uses_a_positive_count_as_interim_sheets_only_for_sheet_candidates():
    facts = {
        "object_id": "shelf-a",
        "materials": [{
            "requirement_id": "panel", "source_name": "Plywood", "family": "plywood",
            "specification": {"thickness_mm": 18}, "quantity": 5, "unit": None,
        }],
        "parts": [],
    }

    result = build_material_plan(
        facts_by_object={"shelf-a": facts}, catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert result.plan is not None
    assert result.plan.lines[0].purchase_quantity == Decimal("5")
    assert result.reason_codes == ("interim_sheet_count_without_geometry",)


def test_interim_sheet_count_receives_a_nonzero_cost_share_next_to_known_parts():
    facts = _facts("shelf-a", "known-part")
    facts["materials"].append({
        "requirement_id": "fallback", "source_name": "Plywood", "family": "plywood",
        "specification": {"thickness_mm": 18}, "quantity": 5, "unit": None,
    })

    result = build_material_plan(
        facts_by_object={"shelf-a": facts}, catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert material_plan_object_cost_allocations(result)[("shelf-a", "fallback")] > Decimal("0")


def test_assumption_fallbacks_with_one_incomplete_ci_key_stay_physically_separate():
    facts = {
        "object_id": "cabinet-a", "quantity": 1,
        "materials": [
            {
                "requirement_id": "visible_facade", "source_name": "Paint Nirlat",
                "family": "paint_lacquer_stain", "specification": {}, "quantity": None, "unit": None,
            },
            {
                "requirement_id": "finish", "source_name": "Paint Nirlat",
                "family": "paint_lacquer_stain", "specification": {}, "quantity": None, "unit": None,
            },
        ],
        "parts": [{
            "part_id": "facade", "material_requirement_id": "visible_facade", "quantity": 1,
            "length_mm": 2000, "width_mm": 600, "rotation_allowed": True,
        }],
    }
    catalogs = {
        "items": [], "offers": [], "reference_positions": [],
        "material_pricing_policies": [{
            "family_id": "paint", "pricing_key_attribute_codes": [],
            "purchase_format_policy": "not_required", "active": True,
        }],
        "material_families": [{"family_id": "paint", "family_code": "paint_lacquer_stain", "active": True}],
    }

    result = build_material_plan(facts_by_object={"cabinet-a": facts}, catalogs=catalogs)

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert result.unresolved_requirement_ids == ()
    assert {line.purchase_kind for line in result.plan.lines} == {"sheet", "direct"}
    assert {fallback["selection_key"] for fallback in result.assumption_fallbacks} == {
        "assumption:cabinet-a:paint_lacquer_stain:finish",
        "assumption:cabinet-a:paint_lacquer_stain:visible_facade",
    }


def test_every_purchase_plan_is_priced_when_another_fact_needs_assumption():
    facts = _facts("cabinet-a", "side-a")
    facts["materials"].append({
        "requirement_id": "unknown", "source_name": "Unknown", "family": "unknown",
        "specification": {}, "quantity": 1, "unit": "piece",
    })

    result = build_material_plan(
        facts_by_object={"cabinet-a": facts},
        catalogs=_catalogs(_offer("sheet", price="100")),
    )

    assert result.plan is not None
    assert result.plan.status == "planned"
    assert len(result.plan.lines) == 2
    assert result.unresolved_requirement_ids == ()
    assert result.reason_codes == ("assumption_fallback",)
    assert result.assumption_fallbacks[0]["reason_code"] == "material_pricing_key_incomplete"
