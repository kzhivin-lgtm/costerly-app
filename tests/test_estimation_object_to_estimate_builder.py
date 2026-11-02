from use_cases.estimation_object_to_estimate import build_object_to_estimate_brief


PAGE = "storage://rfq-estimation-evidence/company/run/object/page-2.webp"
BLOCK = "ocr:ocr-1:p2:b0001"


def _input_row():
    return {
        "input_id": "input-1", "object_input_revision": 1,
        "input_payload": {
            "contract_version": "estimation_input_v4", "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Wardrobe", "quantity": 2},
            "evidence": {"artifacts": [{"storage_ref": PAGE}], "ocr_blocks": [{"block_ref": BLOCK}], "ocr_literal_items": []},
        },
    }


def test_builder_keeps_cited_geometry_and_defaults_only_missing_values():
    brief = build_object_to_estimate_brief(input_row=_input_row(), extraction={
        "object_kind": "wardrobe",
        "dimensions": [
            {"key": "width", "value": 2400, "confidence": 88, "evidence_refs": [PAGE]},
            {"key": "height", "value": 2600, "confidence": 88, "evidence_refs": [PAGE]},
        ],
        "counts": [{"key": "bay_count", "value": 4, "confidence": 70, "evidence_refs": [PAGE]}],
        "material_roles": [{
            "role": "visible_facade", "source_name": "Paint Nirlat IS0011W", "family": "mdf_hdf",
            "specification": {"board_type": "mdf"}, "quantity": None, "unit": None, "evidence_refs": [BLOCK],
        }],
    })

    assert brief["dimensions_mm"]["width"]["basis"] == "evidence"
    assert brief["dimensions_mm"]["depth"] == {
        "value_mm": 600.0, "basis": "assumption", "evidence_refs": [],
        "assumption_rule": "default_cabinet_depth_600mm",
    }
    assert brief["counts"]["bay_count"]["value"] == 4
    assert brief["counts"]["door_count"]["basis"] == "assumption"
    assert brief["material_roles"][0]["evidence_refs"] == [BLOCK]


def test_builder_rejects_unknown_reference_by_replacing_it_with_a_declared_default():
    brief = build_object_to_estimate_brief(input_row=_input_row(), extraction={
        "object_kind": "unknown",
        "dimensions": [{"key": "width", "value": 9999, "confidence": 100, "evidence_refs": ["not-a-ref"]}],
    })

    assert brief["object_kind"] == "cabinet"
    assert brief["dimensions_mm"]["width"]["basis"] == "assumption"
    assert "default_cabinet_width_1000mm" in brief["assumptions"]
