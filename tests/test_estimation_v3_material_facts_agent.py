from agents.estimation_v3_material_facts_agent import _expand


def test_v3_expands_only_material_demands_and_cut_geometry():
    facts = _expand(
        {
            "d": [1200, 600, 720],
            "m": [{"id": "m1", "n": "MDF panel", "f": "mdf", "q": 2.4, "u": "m²", "s": {"thickness_mm": 18}}],
            "p": [{"id": "p1", "m": "m1", "q": 2, "l": 1200, "w": 600, "r": "yes"}],
        },
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": {
            "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Cabinet", "quantity": 1},
            "evidence": {"primary_preview_ref": "storage://rfq-estimation-evidence/company-1/a.webp"},
        }},
        {"mdf"},
    )

    assert facts["contract_version"] == "estimation_material_facts_v3"
    assert facts["materials"][0]["family"] == "mdf"
    assert facts["materials"][0]["quantity"] == 2.4
    assert facts["materials"][0]["unit"] is None
    assert facts["parts"][0]["material_requirement_id"] == "m1"
    assert set(facts) == {
        "contract_version", "input_id", "object_input_revision", "run_id",
        "company_id", "object_id", "object_name", "quantity", "status",
        "dimensions_mm", "materials", "parts", "review_items", "primary_preview_ref",
    }


def test_v3_ignores_model_guessed_purchase_units_for_geometry_free_materials():
    facts = _expand(
        {
            "m": [{
                "id": "profile", "n": "square steel tube", "f": "metal tube",
                "q": 1, "u": "piece", "s": {"profile_section": "20x20 mm square"},
            }],
        },
        {"input_id": "input-1", "object_input_revision": 1, "input_payload": {
            "run_id": "run-1", "company_id": "company-1",
            "object": {"object_id": "object-1", "object_name": "Shelf", "quantity": 1},
            "evidence": {"primary_preview_ref": "storage://rfq-estimation-evidence/company-1/a.webp"},
        }},
        {"metal tube"},
    )

    material = facts["materials"][0]
    assert material["family"] == "metal tube"
    assert material["quantity"] == 1
    assert material["unit"] is None
