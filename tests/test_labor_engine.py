from use_cases.labor_engine import estimate_labor


def _context(*machines):
    return {"machinery": list(machines)}


def _cabinet(template="base_cabinet_open", **features):
    return {
        "object_id": "cabinet-01",
        "quantity": 1,
        "template_code": template,
        "dimensions_mm": {"width": 600, "depth": 560, "height": 720},
        "materials": [{"family": "laminated_particleboard", "thickness_mm": 18}],
        "features": {"shelf_count": 1, "installation_scope": "included", **features},
        "construction_profile": "panel_screw_standard",
    }


def _codes(result):
    return {line["operation_code"] for line in result["labor_lines"]}


def test_s01_standard_base_cabinet_uses_panel_saw_and_manual_drilling_without_cnc():
    result = estimate_labor(_cabinet(), _context("wood_panel_saw", "edge_bander"))

    assert result["status"] == "estimated"
    assert {"panel_saw_cutting", "manual_drilling", "carcass_assembly", "cabinet_installation"} <= _codes(result)
    assert not any(code.startswith("cnc_") for code in _codes(result))
    drilling = next(line for line in result["labor_lines"] if line["operation_code"] == "manual_drilling")
    assert drilling["input_drivers"]["quantity"] == 24
    assert drilling["provenance"] == ["template:base_cabinet_open", "connection:panel_screw_standard"]


def test_s02_hinged_wall_cabinet_uses_cnc_and_excludes_manual_panel_route():
    result = estimate_labor(
        _cabinet("wall_cabinet_hinged", shelf_count=2, door_count=2, installation_scope="delivery_only",),
        _context("wood_cnc_router", "edge_bander"),
    )

    assert {"cnc_router_profile_cutting", "cnc_vertical_drilling", "door_front_fitting"} <= _codes(result)
    assert "panel_saw_cutting" not in _codes(result)
    assert "manual_drilling" not in _codes(result)
    assert "cabinet_installation" not in _codes(result)
    cnc = next(line for line in result["labor_lines"] if line["operation_code"] == "cnc_vertical_drilling")
    assert cnc["role_allocations"][0]["hours"] < cnc["elapsed_minutes"] / 60


def test_s03_vanity_external_stone_is_never_internal_labor():
    result = estimate_labor(
        _cabinet("vanity_cabinet", drawer_count=3, plumbing_cutout=True),
        _context("wood_panel_saw", "edge_bander"),
    )

    assert {"drawer_assembly", "hardware_installation"} <= _codes(result)
    assert result["purchased_components"] == [
        {"component_type": "stone_countertop", "route": "external_component", "attributes": {"cutout_included": True}}
    ]
    assert not any(code.startswith("stone_") for code in _codes(result))


def test_identical_inputs_produce_identical_trace_and_missing_dimensions_review():
    fact = _cabinet()
    context = _context("wood_panel_saw", "edge_bander")

    assert estimate_labor(fact, context) == estimate_labor(fact, context)
    fact["dimensions_mm"].pop("width")
    assert estimate_labor(fact, context)["status"] == "review_required"


def test_panel_template_requires_a_real_edge_banding_route():
    result = estimate_labor(_cabinet(), _context("wood_panel_saw"))

    assert result["status"] == "review_required"
    assert result["review_items"][0]["code"] == "edge_bander_availability_unknown"


def test_s05_carbon_frame_uses_mig_and_internal_powder_route():
    result = estimate_labor(
        {
            "object_id": "frame-01", "quantity": 1, "template_code": "metal_table_frame",
            "dimensions_mm": {"width": 1600, "depth": 800, "height": 740},
            "materials": [{"family": "carbon_steel"}],
            "features": {"profile_section_mm": 40, "coating": "powder", "installation_scope": "delivery_only"},
        },
        _context("metal_profile_saw", "powder_coating_booth"),
    )

    assert result["status"] == "estimated"
    assert {"metal_profile_cutting", "mig_mag_welding", "powder_coating_application"} <= _codes(result)
    assert "tig_welding" not in _codes(result)


def test_s07_sheet_metal_box_uses_external_laser_and_internal_bending():
    result = estimate_labor(
        {
            "object_id": "box-01", "quantity": 3, "template_code": "sheet_metal_box",
            "dimensions_mm": {"width": 400, "depth": 300, "height": 200},
            "materials": [{"family": "carbon_steel", "thickness_mm": 1.5}],
            "features": {},
        },
        _context("metal_press_brake"),
    )

    assert result["status"] == "estimated"
    assert _codes(result) == {"sheet_metal_bending"}
    assert result["purchased_components"][0]["component_type"] == "sheet_laser_cut_part"


def test_s06_visible_stainless_requires_declared_finishing_qualification():
    fact = {
        "object_id": "stainless-frame-01", "quantity": 1, "template_code": "metal_table_frame",
        "dimensions_mm": {"width": 1400, "depth": 700, "height": 740},
        "materials": [{"family": "stainless_304"}],
        "features": {"profile_section_mm": 40, "visible_finish": "brushed"},
    }

    missing = estimate_labor(fact, _context("metal_profile_saw"))
    assert missing["status"] == "review_required"
    assert missing["review_items"][0]["code"] == "stainless_visible_finish_qualification_unknown"

    confirmed = estimate_labor(
        fact,
        {"machinery": ["metal_profile_saw"], "qualified_roles": ["grinder_polisher"]},
    )
    assert {"tig_welding", "metal_grinding", "metal_polishing"} <= _codes(confirmed)
    assert "mig_mag_welding" not in _codes(confirmed)
