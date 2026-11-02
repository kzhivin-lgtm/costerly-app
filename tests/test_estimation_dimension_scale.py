from use_cases.estimation_dimension_scale import build_dimension_scale_gate


def _graph(*values, printed_unit=None):
    return {
        "contract_version": "estimation_dimension_graph_v1",
        "dimension_numbers": [
            {
                "dimension_id": f"dimension-{index:03d}", "numeric_value": value,
                "printed_unit": printed_unit, "evidence_refs": [f"ocr:p1:b{index:04d}"],
            }
            for index, value in enumerate(values, start=1)
        ],
    }


def test_unitless_furniture_scale_gate_locks_centimetres_for_micro_mm_reading():
    gate = build_dimension_scale_gate(dimension_graph=_graph(158, 160, 265, 115, 20))

    assert gate["decision"]["required_unit"] == "cm"
    assert gate["decision"]["candidate_values"][:3] == [265.0, 160.0, 158.0]
    assert gate["decision"]["evidence_refs"][:3] == ["ocr:p1:b0003", "ocr:p1:b0002", "ocr:p1:b0001"]


def test_explicit_source_unit_disables_scale_gate():
    gate = build_dimension_scale_gate(dimension_graph=_graph(158, 160, 265, printed_unit="mm"))

    assert gate["printed_units"] == ["mm"]
    assert gate["decision"] is None


def test_insufficient_ocr_dimensions_does_not_invent_a_unit():
    gate = build_dimension_scale_gate(dimension_graph=_graph(158, 265))

    assert gate["decision"] is None
