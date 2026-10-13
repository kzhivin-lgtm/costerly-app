import use_cases.estimation_v3_material_publisher as publisher


def test_v3_publisher_writes_only_net_material_norms(monkeypatch):
    facts = {
        "contract_version": "estimation_material_facts_v3",
        "input_id": "input-1", "object_input_revision": 1,
        "run_id": "run-1", "company_id": "company-1",
        "object_id": "object-1", "object_name": "Cabinet", "quantity": 2,
        "status": "ready",
        "dimensions_mm": {"width": 1200.0, "depth": 600.0, "height": 720.0},
        "materials": [{
            "requirement_id": "m1", "source_name": "MDF panel", "family": "mdf",
            "specification": {"thickness_mm": 18}, "quantity": 4.0, "unit": "m²",
            "evidence_refs": ["storage://rfq-estimation-evidence/company/run/a.webp"],
        }],
        "parts": [], "review_items": [],
        "primary_preview_ref": "storage://rfq-estimation-evidence/company/run/a.webp",
    }
    captured = {}
    monkeypatch.setattr(publisher, "fetch_estimation_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object", lambda *_args, **kwargs: captured.update(kwargs))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_totals", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress", lambda *_args, **_kwargs: None)

    result = publisher.publish_estimation_v3_material_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-1", "object_id": "object-1"},
        allowed_material_families={"mdf"},
    )

    assert result == {"status": "review_required", "material_line_count": 1}
    line = captured["lines"][0]
    assert line["section"] == "material"
    assert line["quantity"] == 2.0
    assert line["unit_cost"] is None and line["cost"] is None
    assert line["raw_agent_json"]["facts"]["requirement_id"] == "m1"
    assert "labor" not in line and "overhead" not in line
    assert "currency" not in line and "status" not in line
