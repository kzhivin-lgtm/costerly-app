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


def test_checked_carcass_preserves_counts_and_holds_worktop_envelope():
    side = _part("carcass_side", scope_quantity=3, count_refs=["view-1:C01"])
    top = _part("shared_worktop", owner_id="worktop", quantity=1)
    result = _build([side, top], {"melamine_faced_particleboard"}, quantity=2)

    material, = result["materials"]
    cut, = result["parts"]
    assert material["family"] == "melamine_faced_particleboard"
    assert material["basis"] == "construction_assumption"
    assert (cut["length_mm"], cut["width_mm"], cut["quantity"]) == (780, 600, 12)
    assert material["specification"]["thickness_mm"] == 17
    assert material["part_sources"][0]["evidence_refs"] == ["view-1:D01", "view-1:C01"]
    held, = result["review_items"]
    assert held["reason"] == "worktop_cut_geometry_unresolved"
    assert held["part_source"]["dimensions"] == top["dimensions"]
    assert result["source_part_count"] == 2


def test_source_stock_note_overrides_family_assumption_with_original_evidence():
    face = _part("door_front")
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


def test_duplicate_rows_keep_both_sources_without_creating_demand():
    rows = [_part("door_front", instance_ref="view-1:C01", owner_id=owner) for owner in ("B01", "B02")]
    issue = {"role": "door_front", "source_ref": "view-1:C01", "reason": "duplicate_part_evidence"}
    result = _build(rows, {"mdf_hdf"}, issues=[issue])

    assert result["materials"] == []
    assert result["parts"] == []
    held = [item for item in result["review_items"] if "part_source" in item]
    assert [item["part_source"]["owner_id"] for item in held] == ["B01", "B02"]
    assert all(item["reason"] == "duplicate_part_evidence" for item in held)


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


@pytest.mark.parametrize("pricing_basis", ["piece", "square_meter"])
def test_checked_operation_uses_a_compatible_catalog_offer_or_stays_unpriced(pricing_basis):
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
        }},
    )
    surface, service = result["facts_by_object"]["object-1"]["materials"]
    assert (surface["quantity"], service["quantity"]) == (5, 2)
    snapshot = result["material_plan"]
    if pricing_basis == "piece":
        assert snapshot["object_material_costs"] == [{"object_id": "object-1",
            "material_requirement_id": service["requirement_id"], "cost_ex_vat": 200.0}]
        assert snapshot["lines"][0]["authority"] == "company"
    else:
        assert not snapshot["object_material_costs"]
        gap = next(item for item in snapshot["assumption_fallbacks"]
                   if item["material_requirement_id"] == service["requirement_id"])
        assert gap["resolution"] == "assumption_required"
        assert "assumption_price" not in gap
