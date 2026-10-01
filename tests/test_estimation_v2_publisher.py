from decimal import Decimal

import pytest

import use_cases.estimation_v2_publisher as publisher


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


def test_publisher_writes_lines_totals_and_completed_status(monkeypatch):
    facts = {
        "contract_version": "estimation_object_facts_v1",
        "input_id": "input-1",
        "object_input_revision": 1,
        "run_id": "run-1",
        "company_id": "company-1",
        "object_id": "object-1",
        "object_name": "Cabinet",
        "quantity": 1,
        "status": "ready",
        "template": {"code": "base_cabinet_open", "confidence": 90, "provenance": "explicit", "evidence_refs": ["ref"]},
        "dimensions_mm": {"width": 1000, "depth": 500, "height": 700},
        "materials": [{"requirement_id": "m1", "source_name": "MDF", "family": "mdf", "specification": {}, "quantity": 2, "unit": "sqm", "evidence_refs": ["ref"]}],
        "features": {"shelf_count": 1},
        "manufacturing_features": [],
        "purchased_components": [],
        "source_facts": [],
        "review_items": [],
        "primary_preview_ref": "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp",
    }
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "fetch_active_israel_material_families", lambda _client: {"mdf"})
    monkeypatch.setattr(publisher, "validate_object_facts", lambda *_args, **_kwargs: facts)
    monkeypatch.setattr(publisher, "_settings", lambda *_args: ({"vat_percent": 18}, {}))
    monkeypatch.setattr(publisher, "_catalogs", lambda *_args: {})
    monkeypatch.setattr(publisher, "_material_rows_and_costs", lambda **_kwargs: ([{"line_id": "m", "cost": 100}], [{"line_id": "mc", "section": "material", "status": "resolved", "amount": 100, "currency": "ILS", "source_ref": "source", "reason_codes": []}]))
    monkeypatch.setattr(publisher, "_labor_rows_and_costs", lambda **_kwargs: ([{"line_id": "l", "cost": 50}], [{"line_id": "lc", "section": "labor", "status": "resolved", "amount": 62.5, "currency": "ILS", "source_ref": "source", "reason_codes": []}], 1, 62.5))
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
    facts = {"status": "review_required", "company_id": "company-1", "object_id": "object-1", "review_items": [{"code": "dimensions_missing", "severity": "blocking"}]}
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


def test_open_shelving_review_facts_become_complete_deterministic_draft(monkeypatch):
    ref = "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp"
    facts = {
        "contract_version": "estimation_object_facts_v1", "input_id": "input-shelf",
        "object_input_revision": 1, "run_id": "run-1", "company_id": "company-1",
        "object_id": "object-1", "object_name": "Shelving unit", "quantity": 1,
        "status": "review_required",
        "template": {"code": "open_shelving_unit", "confidence": 95, "provenance": "explicit",
                     "evidence_refs": [ref]},
        "dimensions_mm": {"width": 450, "depth": 510, "height": 2695},
        "materials": [
            {"requirement_id": "m1", "source_name": "MDF 20 mm", "family": "mdf",
             "specification": {"thickness_mm": 20}, "quantity": 1.053, "unit": "m2", "evidence_refs": [ref]},
            {"requirement_id": "m2", "source_name": "metal profile 20x20", "family": "carbon_steel",
             "specification": {"profile_section": "20x20"}, "quantity": None, "unit": "m", "evidence_refs": [ref]},
            {"requirement_id": "m3", "source_name": "perforated metal sheet", "family": "carbon_steel",
             "specification": {}, "quantity": None, "unit": "m2", "evidence_refs": [ref]},
        ],
        "features": {"shelf_count": 5, "back_panel": True, "profile_section_mm": 20},
        "manufacturing_features": [], "purchased_components": [], "source_facts": [],
        "review_items": [
            {"code": "material_quantity_missing", "severity": "blocking", "path": "materials[1].quantity",
             "message": "Profile takeoff is delegated to deterministic BOM", "evidence_refs": [ref]},
        ],
        "primary_preview_ref": ref,
    }
    names = [
        "Carbon steel S235, square tube, mill finish", "Standard MDF, raw, 19 mm",
        "Carbon steel S235, perforated sheet, mill finish", "Epoxy metal primer",
        "Polyurethane metal topcoat, satin",
    ]
    units = ["kg", "m2", "m2", "l", "l"]
    prices = [11.21, 209.39, 102, 74.25, 148.5]
    refs = [
        {"material_id": f"ref-{index}", "canonical_name": name, "active": True}
        for index, name in enumerate(names)
    ]
    memberships = [
        {"material_id": f"ref-{index}", "pricing_identity_id": f"identity-{index}"}
        for index in range(5)
    ]
    price_rows = [
        {"pricing_identity_price_id": f"price-{index}", "pricing_identity_id": f"identity-{index}",
         "status": "active", "currency": "ILS", "unit": unit, "price_scope": "material_only",
         "price_low": str(price), "price_typical": str(price), "price_high": str(price)}
        for index, (unit, price) in enumerate(zip(units, prices))
    ]
    events = []
    monkeypatch.setattr(publisher, "fetch_estimation_v2_fact_result", lambda *_args, **_kwargs: {"facts_payload": facts})
    monkeypatch.setattr(publisher, "replace_rfq_estimate_lines_for_object",
                        lambda *_args, **kwargs: events.append(("lines", kwargs["lines"])))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_totals",
                        lambda *_args, **kwargs: events.append(("totals", kwargs)))
    monkeypatch.setattr(publisher, "update_rfq_object_estimate_progress",
                        lambda *_args, **kwargs: events.append(("status", kwargs["status"])))
    context = {
        "families": {"mdf", "carbon_steel", "metal_coatings"},
        "settings": {"vat_percent": 18, "employer_load_percent": 25, "production_workers": 1,
                     "workdays_per_month": 22, "hours_per_day": 8},
        "overhead_monthly": {"rent_facilities_cost": 1000},
        "catalogs": {"items": [], "offers": [], "identities": [], "prices": price_rows,
                     "reference_materials": refs, "pricing_identity_members": memberships},
        "employees": [
            {"position_code": "welder", "gross_hourly_rate": 50},
            {"position_code": "carpenter", "gross_hourly_rate": 50},
            {"position_code": "cnc_operator", "gross_hourly_rate": 40},
            {"position_code": "painter_finisher", "gross_hourly_rate": 60},
            {"position_code": "general_manager", "gross_hourly_rate": 71.4286},
        ],
        "production_context": {"machines": [
            {"machine_code": code, "availability_status": "in_house"}
            for code in ("metal_profile_saw", "wood_panel_saw", "wood_edge_bander", "finish_wet_spray_booth")
        ]},
    }

    result = publisher.publish_estimation_v2_object(
        client=object(), estimate_id="estimate-1",
        input_row={"input_id": "input-shelf", "object_id": "object-1"}, context=context,
    )

    assert result["status"] == "complete"
    lines = next(value for kind, value in events if kind == "lines")
    assert len([row for row in lines if row["section"] == "material"]) == 5
    assert len([row for row in lines if row["section"] == "labor"]) == 12
    assert any(row["section"] == "overhead" for row in lines)
    assert sum(row["cost"] for row in lines if row["section"] == "material") == pytest.approx(674.67)
    totals = next(value for kind, value in events if kind == "totals")
    assert totals["self_cost_ex_vat"] > 900
    assert events[-1] == ("status", "completed")
