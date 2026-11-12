from use_cases.estimation_cb_material_demand import build_cb_material_demand


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
