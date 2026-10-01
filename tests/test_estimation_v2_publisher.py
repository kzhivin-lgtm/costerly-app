import pytest

import use_cases.estimation_v2_publisher as publisher


def _ready_facts():
    return {
        "contract_version": "estimation_object_facts_v2",
        "input_id": "input-1",
        "object_input_revision": 1,
        "run_id": "run-1",
        "company_id": "company-1",
        "object_id": "object-1",
        "object_name": "Object 1",
        "quantity": 1,
        "status": "ready",
        "dimensions_mm": {"width": 1000, "depth": 500, "height": 700},
        "materials": [{
            "requirement_id": "m1", "source_name": "MDF", "family": "mdf",
            "specification": {}, "quantity": 2, "unit": "sqm",
            "evidence_refs": ["ref"],
        }],
        "features": {},
        "manufacturing_features": [],
        "purchased_components": [],
        "labor_operations": [{
            "operation_id": "op-1", "operation_code": "panel_saw_cutting",
            "route": "in_house_machine", "quantity": 5, "unit": "cut_sequence",
            "batch_key": "mdf-panel-saw", "machine_code": "wood_panel_saw",
            "material_requirement_ids": ["m1"], "basis": "Five visible cuts",
            "provenance": "derived", "evidence_refs": ["ref"], "confidence": 70,
        }],
        "source_facts": [],
        "review_items": [],
        "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp",
    }


def test_company_offer_price_uses_deterministic_median_and_removes_vat():
    class Resolution:
        offer_ids = ("offer-1", "offer-2", "offer-3")

    price, source = publisher._company_offer_price(
        Resolution(),
        [
            {"offer_id": "offer-1", "normalized_price": "118", "normalized_unit": "sqm", "vat_included": True},
            {"offer_id": "offer-2", "normalized_price": "90", "normalized_unit": "sqm", "vat_included": False},
            {"offer_id": "offer-3", "normalized_price": "120", "normalized_unit": "sqm", "vat_included": False},
        ],
        requested_unit="sqm",
        vat_percent=18,
    )

    assert price == 100.0
    assert source == "company-offer:offer-1"


def test_role_rate_uses_company_profile_position_mapping():
    rate, matched = publisher._role_rate(
        "wood_machine_operator",
        [{"position_code": "cnc_operator", "gross_hourly_rate": 40, "deleted_at": None}],
        176,
    )
    assert rate == 40
    assert matched == "cnc_operator"


def test_publisher_writes_agent_materials_operations_totals_and_completed_status(monkeypatch):
    facts = _ready_facts()
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(publisher, "validate_object_facts", lambda *_args, **_kwargs: facts)
    monkeypatch.setattr(publisher, "_settings", lambda *_args: ({"vat_percent": 18}, {}))
    monkeypatch.setattr(publisher, "_catalogs", lambda *_args: {})
    monkeypatch.setattr(publisher, "_material_rows_and_costs", lambda **_kwargs: ([{"line_id": "m", "cost": 100}], [{"line_id": "mc", "section": "material", "status": "resolved", "amount": 100, "currency": "ILS", "source_ref": "source", "reason_codes": []}]))

    def _labor(**kwargs):
        assert kwargs["facts"]["labor_operations"] == facts["labor_operations"]
        return ([{"line_id": "l", "cost": 50}], [{"line_id": "lc", "section": "labor", "status": "resolved", "amount": 62.5, "currency": "ILS", "source_ref": "source", "reason_codes": []}], 1, 62.5)

    monkeypatch.setattr(publisher, "_labor_rows_and_costs", _labor)
    monkeypatch.setattr(publisher, "build_overhead_lines", lambda **_kwargs: [{"line_id": "o", "cost": 10}])
    monkeypatch.setattr(publisher, "compose_object_estimate", lambda **_kwargs: {"status": "complete", "self_cost_unit": 172.5})
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object", lambda *_args, **kwargs: events.append(("lines", kwargs["lines"])))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_totals", lambda *_args, **kwargs: events.append(("totals", kwargs)))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress", lambda *_args, **kwargs: events.append(("status", kwargs["status"])))

    result = publisher.publish_estimation_v2_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-1", "object_id": "object-1"},
        context={"families": {"mdf"}, "settings": {"vat_percent": 18},
                 "overhead_monthly": {}, "catalogs": {}, "employees": [],
                 "production_context": {}},
    )

    assert result["status"] == "complete"
    assert [event[0] for event in events] == ["status", "lines", "totals", "status"]
    assert events[-1] == ("status", "completed")
    assert events[2][1]["self_cost_ex_vat"] == 172.5
    assert events[2][1]["vat_amount"] == 31.05


def test_publisher_preserves_review_required_without_fake_totals(monkeypatch):
    facts = {
        "status": "review_required", "company_id": "company-1", "object_id": "object-1",
        "review_items": [{"code": "dimensions_missing", "severity": "blocking"}],
    }
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(publisher, "validate_object_facts", lambda *_args, **_kwargs: facts)
    monkeypatch.setattr(publisher, "_material_rows_and_costs", lambda **_kwargs: ([{"line_id": "m1"}], []))
    monkeypatch.setattr(publisher, "_purchased_component_rows_and_costs", lambda _facts: ([], []))
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object", lambda *_args, **kwargs: events.append({"lines": kwargs["lines"]}))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress", lambda *_args, **kwargs: events.append(kwargs))

    result = publisher.publish_estimation_v2_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-1", "object_id": "object-1"},
        context={"families": {"mdf"}, "catalogs": {}, "settings": {}},
    )

    assert result["status"] == "review_required"
    assert result["reason_codes"] == ["dimensions_missing"]
    assert events == [{"lines": [{"line_id": "m1"}]}, {
        "estimate_id": "estimate-1", "object_id": "object-1",
        "status": "review_required", "progress_percent": 100,
        "progress_label": "object_facts_review_required",
    }]
