import use_cases.estimation_assumption_fallbacks as fallbacks


def _snapshot():
    return {
        "assumption_fallbacks": [{
            "object_id": "object-1", "material_requirement_id": "hardware",
            "source_name": "Domicile handle", "material_family": "hardware_handle",
            "specification": {"model": "AL100"}, "reason_code": "no_company_or_israel_candidate",
            "selection_key": "assumption:hardware_handle:hardware", "quantity_per_item": 6,
            "unit": "piece", "assumption_price": {
                "amount": 200, "currency": "ILS", "unit": "piece", "confidence": 0,
                "source_candidates": [], "rationale": ["No source was found."],
            },
        }],
        "object_material_costs": [{
            "object_id": "object-1", "material_requirement_id": "hardware", "cost_ex_vat": 200,
        }],
    }


def test_each_assumption_creates_a_deduplicated_gap_job_and_case_record(monkeypatch):
    calls = []
    monkeypatch.setattr(fallbacks, "fetch_active_estimate_case_assumptions", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        fallbacks, "create_or_update_catalog_gap_job",
        lambda *_args, **kwargs: calls.append(("gap", kwargs)) or "gap-1",
    )
    monkeypatch.setattr(
        fallbacks, "insert_estimate_case_assumption",
        lambda *_args, **kwargs: calls.append(("assumption", kwargs)) or "assumption-1",
    )
    monkeypatch.setattr(
        fallbacks, "insert_catalog_gap_job_occurrence",
        lambda *_args, **kwargs: calls.append(("occurrence", kwargs)),
    )

    persisted = fallbacks.persist_material_assumption_fallbacks(
        client=object(), estimate_id="estimate-1", company_id="company-1",
        facts_by_object={"object-1": {"fact_result_id": "bom-result-1"}}, plan_snapshot=_snapshot(),
    )

    assert persisted == 1
    assert calls[0][1]["gap_type"] == "material_supply"
    assert len(calls[0][1]["gap_fingerprint"]) == 64
    assert calls[1][1]["fact_result_id"] == "bom-result-1"
    assert calls[1][1]["calculation_impact"]["material_cost_ex_vat"] == 200
    assert calls[2][1] == {"gap_job_id": "gap-1", "assumption_id": "assumption-1", "company_id": "company-1"}


def test_recalculation_updates_the_case_assumption_without_creating_a_second_occurrence(monkeypatch):
    calls = []
    monkeypatch.setattr(fallbacks, "fetch_active_estimate_case_assumptions", lambda *_args, **_kwargs: [{
        "assumption_id": "assumption-1", "object_id": "object-1",
        "chosen_assumption": {"material_requirement_id": "hardware"},
    }])
    monkeypatch.setattr(fallbacks, "create_or_update_catalog_gap_job", lambda *_args, **_kwargs: "gap-1")
    monkeypatch.setattr(fallbacks, "update_estimate_case_assumption", lambda *_args, **kwargs: calls.append(kwargs))
    monkeypatch.setattr(fallbacks, "insert_estimate_case_assumption", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr(fallbacks, "insert_catalog_gap_job_occurrence", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))

    fallbacks.persist_material_assumption_fallbacks(
        client=object(), estimate_id="estimate-1", company_id="company-1",
        facts_by_object={}, plan_snapshot=_snapshot(),
    )

    assert calls[0]["assumption_id"] == "assumption-1"
