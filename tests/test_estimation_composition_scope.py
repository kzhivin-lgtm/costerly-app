from use_cases.estimation_composition_scope import apply_composition_scope, calculation_handoff, validate_composition_scope


def _scope():
    return {
        "contract_version": "estimation_composition_scope_v1", "input_id": "input-1", "object_id": "object-1",
        "object_summary": "Entrance divider with drawer storage and a fixed slatted screen.",
        "zones": [
            {"scope_id": "drawers", "assembly_role": "drawer_bank", "semantic_role": "drawer storage", "operability": "drawer", "counts": {"drawers": 3}, "front_groups": [], "evidence_refs": ["storage://page-1"]},
            {"scope_id": "screen", "assembly_role": "vertical_panel", "semantic_role": "slatted divider", "operability": "fixed", "counts": {"facades": 12}, "front_groups": [{"front_kind": "hinged_facade", "quantity": 12}], "evidence_refs": ["storage://page-1"]},
        ], "assumptions": [],
    }


def test_scope_gate_locks_drawers_and_rejects_false_hinged_screen():
    scope = validate_composition_scope(scope=_scope(), input_id="input-1")
    result = apply_composition_scope(extraction={
        "assemblies": [
            {"assembly_id": "drawers", "assembly_role": "facade_set", "counts": {"facades": 3}, "front_groups": [{"front_kind": "hinged_facade", "quantity": 3}], "dimensions": {}},
            {"assembly_id": "screen", "assembly_role": "facade_set", "counts": {"facades": 12}, "front_groups": [{"front_kind": "hinged_facade", "quantity": 12}], "dimensions": {}},
            {"assembly_id": "invented", "assembly_role": "facade_set", "front_groups": [{"front_kind": "hinged_facade", "quantity": 99}]},
        ], "secondary_items": [{"role": "hinge"}, {"role": "leg"}],
    }, scope=scope)

    assert [item["assembly_id"] for item in result["assemblies"]] == ["drawers", "screen"]
    assert result["assemblies"][0]["assembly_role"] == "drawer_bank"
    assert result["assemblies"][0]["front_groups"] == [{"front_kind": "drawer_front", "quantity": 3, "arrangement": "stacked"}]
    assert result["assemblies"][1]["front_groups"] == []
    assert result["secondary_items"] == [{"role": "leg"}]
    assert scope["status"] == "ready"


def test_calculation_handoff_persists_scope_not_an_opaque_prompt():
    scope = validate_composition_scope(scope=_scope(), input_id="input-1")
    handoff = calculation_handoff(scope=scope, dimension_graph={"contract_version": "estimation_dimension_graph_v1", "views": [1], "dimension_numbers": [1, 2]})

    assert handoff["contract_version"] == "estimation_calculation_handoff_v1"
    assert handoff["composition_scope"]["zones"][0]["counts"] == {"drawers": 3}
    assert handoff["dimension_graph_summary"] == {"contract_version": "estimation_dimension_graph_v1", "dimension_count": 2, "view_count": 1}


def test_scope_gate_remaps_calculation_dimension_bindings_before_2vn():
    scope = validate_composition_scope(scope=_scope(), input_id="input-1")
    result = apply_composition_scope(extraction={
        "assemblies": [
            {"assembly_id": "assembly-1", "assembly_role": "drawer_bank", "dimensions": {"depth": {"value": 72}}},
            {"assembly_id": "assembly-2", "assembly_role": "vertical_panel", "dimensions": {}},
        ],
        "dimension_bindings": [{"assembly_id": "assembly-1", "axis": "depth"}],
    }, scope=scope)

    assert result["assemblies"][0]["assembly_id"] == "drawers"
    assert result["assemblies"][0]["dimensions"] == {"depth": {"value": 72}}
    assert result["dimension_bindings"] == [{"assembly_id": "drawers", "axis": "depth"}]
