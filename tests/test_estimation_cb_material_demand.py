import pytest

from use_cases.estimation_cb_material_demand import build_cb_material_demand, calculate_cb_materials


def _input(quantity=1):
    return {"input_id": "input-1", "input_payload": {
        "run_id": "run-1", "company_id": "company-1",
        "object": {"object_id": "object-1", "quantity": quantity},
    }}


def _part(role, **fields):
    return {"role": role, "owner_id": "B01", "quantity": 2,
            "dimensions": {key: {"mm": value, "refs": ["view-1:D01"]}
                           for key, value in (("length", 780), ("width", 600), ("thickness", 17))},
            **fields}


def _build(rows, families, *, quantity=1, issues=()):
    return build_cb_material_demand(
        parts_report={"stage": "Parts Check", "run_id": "run-1",
                      "objects": {"object-1": {"parts": rows, "inventory_issues": list(issues)}}},
        input_row=_input(quantity), allowed_material_families=families,
    )


def test_lighting_accessories_size_one_supply_per_physical_object_across_temperatures():
    strips = [_part("led_strip_run", quantity=1, unit="run", colour_temperature_k=kelvin,
                    dimensions={"length": {"mm": length, "refs": [str(kelvin)]}})
              for kelvin, length in ((3000, 4000), (4000, 6000))]
    result = _build(strips, {"hardware_electrical_component"}, quantity=2.0)
    warm, neutral, profile, supply = result["materials"]
    assert [(line["quantity"], line["purchase_variant"]) for line in (warm, neutral)] == [(8, "3000K"), (12, "4000K")]
    assert (profile["quantity"], profile["unit"]) == (20, "m")
    assert (supply["quantity"], supply["unit"], supply["lighting_capacity"]["minimum_w"]) == (2, "piece", 75)
    assert profile["linear_cuts"] == [{"length_mm": 2000, "quantity": 10}]
    assert supply["lighting_capacity"]["installed_m_per_object"] == 10


def test_unmeasured_lighting_does_not_borrow_another_route_or_price_it_as_a_piece():
    strip = _part("led_strip_run", quantity=1, unit="run", colour_temperature_k=3000,
                  dimensions={"length": {"mm": 1500, "refs": ["view-1:A1"]}})
    missing = {**strip, "dimensions": {"length": {"mm": None, "refs": ["view-1:A2"]}}}
    result = _build([strip, missing], {"hardware_electrical_component"})
    strip, profile, supply = result["materials"]
    assert strip["quantity"] == profile["quantity"] == 1.5
    assert supply["lighting_capacity"]["partial"]
    assert result["review_items"][0]["reason"] == "lighting_route_length_unresolved"


def test_checked_carcass_preserves_counts_and_sends_unresolved_worktop_to_fallback():
    side = _part("carcass_side", scope_quantity=3, count_refs=["view-1:C01"])
    top = _part("shared_worktop", owner_id="worktop", quantity=1)
    result = _build([side, top], {"melamine_faced_particleboard"}, quantity=2)

    material, worktop = result["materials"]
    cut, _worktop_cut = result["parts"]
    assert material["family"] == "melamine_faced_particleboard"
    assert material["basis"] == "construction_assumption"
    assert (cut["length_mm"], cut["width_mm"], cut["quantity"]) == (780, 600, 12)
    assert material["specification"]["thickness_mm"] == 17
    assert material["part_sources"][0]["evidence_refs"] == ["view-1:D01", "view-1:C01"]
    held, = result["review_items"]
    assert held["reason"] == "worktop_cut_geometry_unresolved"
    assert worktop["assumption_reason"] == held["reason"]
    assert held["part_source"]["dimensions"] == top["dimensions"]
    assert result["source_part_count"] == 2


def test_source_stock_note_overrides_family_assumption_with_original_evidence():
    face = _part("door_front", visual_stock={"surface": "wood_grain", "refs": ["view-1"]})
    face["dimensions"]["thickness"] = {
        "mm": 18, "basis": "ocr_material_note", "refs": ["ocr:18"],
        "source_text": ["Фанера 18 мм"],
    }
    result = _build([face], {"plywood", "mdf_hdf"})

    material, = result["materials"]
    assert material["family"] == "plywood"
    assert material["basis"] == "source_evidence"
    assert material["evidence_refs"] == ["ocr:18"]
    assert material["specification"]["thickness_mm"] == 18


def test_compatible_visible_wood_grain_parts_share_one_veneered_mdf_demand():
    finish = {"surface": "wood_grain", "refs": ["view-1"], "material": "veneered_mdf"}
    seat = _part("seat_cover", visual_stock=finish)
    rail = _part("frame_side", owner_id="B02", visual_stock=finish)
    material, = _build([seat, rail], {"mdf_hdf", "melamine_faced_particleboard"})["materials"]
    assert material["source_name"] == "Veneered MDF"
    assert material["specification"] == {"board_type": "mdf", "surface": "veneer_two_sided", "thickness_mm": 17}
    assert material["basis"] == "construction_assumption"
    assert material["evidence_refs"] == ["view-1"]
    assert [source["role"] for source in material["part_sources"]] == ["seat_cover", "frame_side"]


def test_supported_worktop_substrate_defaults_to_raw_mdf_and_keeps_its_cut():
    underlayer = _part("tabletop_underlayer", quantity=1)
    underlayer["dimensions"]["thickness"]["mm"] = 40
    demand = _build([underlayer], {"melamine_faced_particleboard", "mdf_hdf"})
    material, = demand["materials"]
    cut, = demand["parts"]
    assert material["family"] == "mdf_hdf"
    assert material["specification"] == {"board_type": "mdf", "surface": "raw", "thickness_mm": 40}
    assert material["basis"] == "construction_assumption"
    assert (cut["length_mm"], cut["width_mm"], cut["quantity"]) == (780, 600, 1)


def test_veneered_layup_keeps_finished_part_and_combines_material_cuts():
    visual = {"surface": "wood_grain", "refs": ["view-1"], "material": "veneered_mdf"}
    seat = _part("seat_cover", visual_stock=visual, sheet_layup={"finished_mm": 40, "layer_mm": 20, "layer_count": 2})
    seat["dimensions"]["thickness"]["mm"] = 40
    face = _part("drawer_front", visual_stock=visual)
    face["dimensions"]["thickness"]["mm"] = 20
    result = _build([seat, face], {"mdf_hdf"})
    material, = result["materials"]
    assert material["specification"]["thickness_mm"] == 20
    assert [part["quantity"] for part in result["parts"]] == [4, 2]
    assert result["source_part_count"] == 2
    assert material["part_sources"][0]["dimensions"]["thickness"]["mm"] == 40
    assert material["part_sources"][0]["source_quantity"] == 2


def test_explicit_solid_wood_survives_material_demand():
    face = _part("door_front",
                 visual_stock={"surface": "wood_grain", "refs": ["view-1"], "material": "solid_wood"},
                 material_note={"basis": "ocr_material_note", "refs": ["ocr:solid"],
                                "source_text": ["Фасады: массив дуба, 17 мм."]})
    material, = _build([face], {"timber_solid_wood_panel", "mdf_hdf"})["materials"]
    assert material["family"] == "timber_solid_wood_panel"
    assert material["basis"] == "source_evidence"
    assert "ocr:solid" in material["evidence_refs"]


def test_cyrillic_stock_ocr_matches_a_shared_alias_with_original_evidence():
    face = _part("carcass_side")
    face["dimensions"]["thickness"] = {
        "mm": 16, "basis": "ocr_material_note", "refs": ["ocr:16"],
        "source_text": ["Phanepe 6epe3o8a 16 MM. (Macno)"],
    }
    report = {"stage": "Parts Check", "objects": {"object-1": {"parts": [face]}}}
    aliases = {"plywood": {"family_aliases": ["фанера"]}}
    facts = build_cb_material_demand(parts_report=report, input_row=_input(),
                                    allowed_material_families={"plywood", "mdf_hdf"}, family_alias_context=aliases)
    material, = facts["materials"]
    assert material["family"] == "plywood"
    assert material["specification"] == {"thickness_mm": 16}
    assert material["evidence_refs"] == ["ocr:16"]
    assert "assumption_reason" not in material
    aliases["mdf_hdf"] = {"family_aliases": ["фанера"]}
    facts = build_cb_material_demand(parts_report=report, input_row=_input(),
                                    allowed_material_families={"plywood", "mdf_hdf"}, family_alias_context=aliases)
    assert facts["materials"][0]["assumption_reason"] == "material_note_unresolved"


def test_duplicate_rows_keep_both_sources_without_creating_demand():
    rows = [_part("door_front", instance_ref="view-1:C01", owner_id=owner) for owner in ("B01", "B02")]
    issue = {"role": "door_front", "source_ref": "view-1:C01", "reason": "duplicate_part_evidence"}
    result = _build(rows, {"mdf_hdf"}, issues=[issue])

    assert result["materials"] == []
    assert result["parts"] == []
    held = [item for item in result["review_items"] if "part_source" in item]
    assert [item["part_source"]["owner_id"] for item in held] == ["B01", "B02"]
    assert all(item["reason"] == "duplicate_part_evidence" for item in held)


def test_unlisted_part_and_missing_dimensions_keep_a_priced_requirement():
    mirror = _part("mirror_glass", quantity=1)
    mirror["dimensions"]["thickness"] = {"mm": None}
    component = _part("new_component_kind", owner_id="B02", quantity=None,
                      material_hint="Uncatalogued component", dimensions={})
    context = {"company_id": "company-1", "families": {"mirror"}, "catalogs": {}}
    result = calculate_cb_materials(
        parts_report={"stage": "Parts Check", "run_id": "run-1",
                      "objects": {"object-1": {"parts": [mirror, component]}}},
        input_rows=[_input()], catalog_context=context,
    )
    facts = result["facts_by_object"]["object-1"]
    assert len(facts["materials"]) == 2
    assert facts["materials"][0]["specification"] == {}
    assert facts["materials"][1]["quantity"] == 1
    plan = result["material_plan"]
    assert plan["status"] == "needs_review"
    assert plan["parts_check"]["object-1"]["unpriced_requirements"] == []
    assert {line["purchase_kind"] for line in plan["lines"]} == {"sheet", "piece"}


def test_worktop_surface_areas_are_preserved_without_inventing_end_material():
    outline = {"area_basis": "gross_plan_outline", "cutout_status": "unresolved", "kitchen_worktop": True,
               "source_refs": ["plan:C01"], "seam_source_refs": ["plan:C02"],
               "finish_evidence": {"view_id": "render"}, "surfaces": [
                   {"id": "main", "material_role": "main_worktop", "area_m2": 2.5},
                   {"id": "end", "material_role": "contrasting_end", "area_m2": .2},
               ]}
    cutout = {"id": "render:worktop-cutout-01", "view_id": "render", "bbox_px": [10, 20, 40, 50],
              "fixture_hint": "cooktop", "surface": "main_worktop"}
    row = _part("shared_worktop", quantity=1, worktop_outline=outline, worktop_cutouts=[cutout, cutout])
    result = _build([row], {"engineered_quartz_mineral_hybrid"}, quantity=2)

    main, end, service = result["materials"]
    assert (main["family"], main["quantity"], main["unit"]) == ("engineered_quartz_mineral_hybrid", 5, "m2")
    assert main["basis"] == "construction_assumption"
    assert (end["family"], end["quantity"], end["unit"]) == (None, .4, "m2")
    assert "render" in end["evidence_refs"]
    assert (service["source_name"], service["operation_code"], service["quantity"], service["unit"]) == (
        "Worktop cutout", "stone_cutout", 2, "piece",
    )
    assert service["item_kind"] == "operation_service" and service["family"] is None
    assert service["part_sources"][0]["cutout"] == cutout
    assert result["parts"] == []
    assert [issue["reason"] for issue in result["review_items"]] == [
        "worktop_material_family_unresolved",
    ]


@pytest.mark.parametrize(("pricing_basis", "reference_family", "authority", "cost"), [
    ("piece", "engineered_quartz_mineral_hybrid", "company", 200.0),
    ("square_meter", "engineered_quartz_mineral_hybrid", "israel_reference", 160.0),
    ("square_meter", "porcelain_ceramic_slab", "assumption", 400.0),
])
def test_checked_operation_uses_a_compatible_catalog_offer_or_fallback(
    pricing_basis, reference_family, authority, cost,
):
    outline = {"area_basis": "gross_plan_outline", "kitchen_worktop": True, "source_refs": ["plan:C01"],
               "surfaces": [{"id": "main", "material_role": "main_worktop", "area_m2": 2.5}]}
    cutout = {"id": "render:worktop-cutout-01", "view_id": "render", "surface": "main_worktop"}
    row = _part("shared_worktop", quantity=1, worktop_outline=outline, worktop_cutouts=[cutout])
    result = calculate_cb_materials(
        parts_report={"stage": "Parts Check", "run_id": "run-1", "input_ids": ["input-1"],
                      "objects": {"object-1": {"parts": [row]}}},
        input_rows=[_input(2)],
        catalog_context={"company_id": "company-1", "families": {"engineered_quartz_mineral_hybrid"}, "catalogs": {
            "operations": [{"operation_id": "op-1", "operation_code": "stone_cutout", "active": True}],
            "supplier_operation_offers": [{"operation_offer_id": "offer-1", "operation_id": "op-1", "status": "active",
                                           "pricing_basis": pricing_basis, "currency": "ILS", "vat_included": True,
                                           "source_price": 118}],
            "israel_operation_prices": [{"operation_service_price_id": "price-1", "operation_id": "op-1", "status": "active",
                                         "market_code": "IL", "unit": "piece", "currency": "ILS", "price_ex_vat": 80,
                                         "source_id": "source-1", "material_family_code": reference_family}],
        }},
    )
    surface, service = result["facts_by_object"]["object-1"]["materials"]
    assert (surface["quantity"], service["quantity"]) == (5, 2)
    snapshot = result["material_plan"]
    priced, = [item for item in snapshot["object_material_costs"]
               if item["material_requirement_id"] == service["requirement_id"]]
    line, = [line for line in snapshot["lines"] if any(
        item["material_requirement_id"] == service["requirement_id"] for item in line["allocations"])]
    assert (line["authority"], priced["cost_ex_vat"]) == (authority, cost)
    assert snapshot["parts_check"]["object-1"]["unpriced_requirements"] == []


def test_unknown_visible_stock_and_kitchen_worktop_end_default_to_ldsp_17():
    visible = _part("door_front")
    visible["dimensions"]["thickness"] = {"mm": None}
    outline = {"area_basis": "gross_plan_outline", "kitchen_worktop": True, "source_refs": ["plan:C01"],
               "surfaces": [{"id": "main", "material_role": "main_worktop", "area_m2": 2.5},
                            {"id": "end", "material_role": "contrasting_end", "area_m2": .2}]}
    worktop = _part("shared_worktop", quantity=1, worktop_outline=outline)
    worktop["dimensions"]["thickness"] = {"mm": 30, "basis": "construction_assumption"}
    result = _build([visible, worktop], {"mdf_hdf", "melamine_faced_particleboard", "engineered_quartz_mineral_hybrid"})
    facade, main, end = result["materials"]
    assert (facade["family"], facade["specification"]["thickness_mm"]) == ("melamine_faced_particleboard", 17)
    assert (main["family"], main["specification"]["thickness_mm"]) == ("engineered_quartz_mineral_hybrid", 30)
    assert (end["family"], end["specification"]["thickness_mm"]) == ("melamine_faced_particleboard", 17)
    assert end["quantity"] == .2 and end["basis"] == "construction_assumption"


def test_runner_demand_keeps_physical_counts_and_distinguishes_purchase_packages():
    old_shelf = _part("drawer_slide", material_hint="concealed soft-close pull-out slide")
    new_shelf = _part("pull_out_shelf_slide", material_hint="pull-out shelf slide")
    drawer = _part("drawer_slide", material_hint="concealed soft-close drawer slide")
    rows = [drawer, old_shelf, new_shelf]
    materials = _build(rows, {"hardware_drawer_slide"}, quantity=2)["materials"]

    assert [(row["material_role"], row["quantity"], row["unit"], row["purchase_package_quantity"])
            for row in materials] == [("drawer_slide", 4, "piece", 2), ("pull_out_shelf_slide", 8, "piece", 2)]
