from use_cases.manufacturing_estimation import build_manufacturing_cost_lines


def _parameter(parameter_id, key, low, typical, high, unit, currency="ILS", thickness=None):
    return {
        "parameter_id": parameter_id,
        "calculator": "cnc_router_subcontractor",
        "parameter_key": key,
        "country_code": "IL",
        "region": None,
        "material_family": None,
        "thickness_min_mm": thickness,
        "thickness_max_mm": thickness,
        "machine_class": None,
        "object_family": None,
        "qualifiers": {},
        "value_low": low,
        "value_typical": typical,
        "value_high": high,
        "unit": unit,
        "currency": currency,
        "source_type": "research",
        "source_name": "Runtime test",
        "source_url": "https://example.com/runtime-test",
        "source_date": "2026-09-28",
        "confidence": 60,
        "status": "active",
        "version": 1,
        "effective_from": "2026-09-28",
        "effective_to": None,
        "approved_by": "admin-1",
        "approved_at": "2026-09-28T10:00:00Z",
    }


def _feature():
    return {
        "process": "cnc_router",
        "material_family": "melamine_white",
        "thickness_mm": 17,
        "part_count": 10,
        "sheet_count": 2,
        "path_length_m": 20,
        "machine_minutes": 30,
        "pass_count": 1,
        "hole_count": 20,
        "pocket_minutes": 0,
        "edge_banding_length_m": 0,
        "production_file_ready": "yes",
        "rectangular_parts_only": "yes",
        "single_face_processing": "yes",
        "standard_operations_only": "yes",
        "has_freeform_contours": "no",
        "has_internal_cutouts": "no",
        "has_pockets": "no",
        "has_horizontal_or_end_drilling": "no",
        "has_repeated_hole_patterns": "no",
        "has_tight_positional_relationships": "no",
        "straight_edge_to_edge_cuts_only": "unknown",
        "rough_finish_acceptable": "unknown",
        "material_and_thickness_supported": "unknown",
        "has_curves_or_shaped_edges": "unknown",
        "precision_or_repeatability_required": "unknown",
        "evidence_pages": "A-01",
        "confidence": 80,
        "notes": "Ten repeated cabinet parts.",
    }


def _rows():
    return [
        _parameter("dxf", "dxf_cutting_service", 110, 330, 550, "ILS/job"),
        _parameter("minimum", "provider_minimum", 200, 300, 400, "ILS/job"),
        _parameter("delivery", "allocated_delivery", 50, 150, 300, "ILS/job"),
    ]


def _result():
    return {
        "estimate_id": "estimate-1",
        "object_id": "object-1",
        "company_id": "company-1",
        "manufacturing": [_feature()],
    }


def _context(level):
    return {
        "machines": [
            {
                "machine_code": "wood_cnc_router",
                "availability_status": "not_in_house",
                "estimate_level": level,
            },
            {
                "machine_code": "wood_panel_saw",
                "availability_status": "not_in_house",
            },
        ]
    }


def test_cnc_subcontractor_runtime_uses_company_slider_against_market_range():
    selected = []
    for level in (1, 3, 5):
        lines = build_manufacturing_cost_lines(
            estimation_result=_result(),
            production_context=_context(level),
            parameter_rows=_rows(),
        )
        assert len(lines) == 1
        assert lines[0]["source"] == "manufacturing_engine"
        assert lines[0]["raw_agent_json"]["calculator"] == "cnc_router_subcontractor"
        assert lines[0]["raw_agent_json"]["reserve_level"] == level
        selected.append(lines[0]["cost"])

    assert selected == [250.0, 480.0, 850.0]


def test_simple_low_volume_panel_work_stays_on_manual_route_without_cnc_charge():
    result = _result()
    result["manufacturing"][0].update({"part_count": 2, "hole_count": 4})
    context = _context(3)
    context["machines"][1]["availability_status"] = "in_house"

    assert build_manufacturing_cost_lines(
        estimation_result=result,
        production_context=context,
        parameter_rows=_rows(),
    ) == []
