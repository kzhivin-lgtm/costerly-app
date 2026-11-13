import pandas as pd

import use_cases.estimation as estimation
from use_cases.estimation import _material_norms_from_plan


def test_object_norms_are_derived_from_sheet_allocations_not_purchase_count():
    norms = _material_norms_from_plan({
        "lines": [{
            "purchase_kind": "sheet",
            # Two purchased sheets are deliberately irrelevant to Object Detail.
            "purchase_quantity": 2,
            "allocations": [{
                "object_id": "cabinet", "material_requirement_id": "mdf",
                "length_mm": 1200, "width_mm": 600, "quantity": 2,
            }],
        }],
    })

    assert norms == {("cabinet", "mdf"): ("m²", 1.44)}


def test_object_norms_are_derived_from_linear_stock_allocations():
    norms = _material_norms_from_plan({
        "lines": [{
            "purchase_kind": "linear_stock",
            "allocations": [{
                "object_id": "shelf", "material_requirement_id": "tube",
                "length_mm": 2500, "quantity": 2,
            }],
        }],
    })

    assert norms == {("shelf", "tube"): ("m", 5.0)}


def test_partial_material_plan_publishes_resolved_canonical_line(monkeypatch):
    updates = []
    source_lines = [{
        "section": "material", "object_id": "cabinet", "line_id": "line-1",
        "raw_agent_json": {"facts": {"requirement_id": "mdf"}},
    }]
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines", lambda *_args: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines_for_object", lambda *_args, **_kwargs: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *_args: pd.DataFrame([{
        "object_id": "cabinet", "quantity": 1,
    }]))
    monkeypatch.setattr(
        estimation, "update_rfq_estimate_line",
        lambda _client, **kwargs: updates.append(kwargs),
    )
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *_args: pd.DataFrame())
    monkeypatch.setattr(estimation, "upsert_rfq_estimate_lines", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(estimation, "_recalculate_object_estimate_totals", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_progress", lambda *_args, **_kwargs: None)

    estimation.apply_material_plan_allocations(client=object(), estimate_id="estimate-1", plan_snapshot={
        "status": "needs_review",
        "object_material_costs": [{"object_id": "cabinet", "material_requirement_id": "mdf", "cost_ex_vat": 244}],
        "lines": [{
            "display_name": "MDF 20 mm 1220 × 2440 mm, raw", "authority": "company", "purchase_kind": "sheet",
            "allocations": [{"object_id": "cabinet", "material_requirement_id": "mdf", "area_mm2": 1_000_000}],
        }],
    })

    assert updates[0]["values"]["item_name"] == "MDF 20 mm 1220 × 2440 mm, raw"
    assert updates[0]["values"]["unit"] == "project allocation"
    assert updates[0]["values"]["quantity"] is None
    assert updates[0]["values"]["unit_cost"] is None
    assert updates[0]["values"]["cost"] == 244
    assert updates[0]["values"]["needs_price"] is False
    assert updates[0]["values"]["raw_agent_json"]["price_source"] == "C"


def test_assumption_fallback_is_published_as_a_priced_material_line(monkeypatch):
    updates = []
    source_lines = [{
        "section": "material", "object_id": "cabinet", "line_id": "line-1",
        "raw_agent_json": {"facts": {"requirement_id": "track"}},
    }]
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines", lambda *_args: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines_for_object", lambda *_args, **_kwargs: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *_args: pd.DataFrame([{
        "object_id": "cabinet", "quantity": 1,
    }]))
    monkeypatch.setattr(
        estimation, "update_rfq_estimate_line",
        lambda _client, **kwargs: updates.append(kwargs),
    )
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *_args: pd.DataFrame())
    monkeypatch.setattr(estimation, "upsert_rfq_estimate_lines", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(estimation, "_recalculate_object_estimate_totals", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_progress", lambda *_args, **_kwargs: None)

    estimation.apply_material_plan_allocations(client=object(), estimate_id="estimate-1", plan_snapshot={
        "status": "planned",
        "object_material_costs": [{"object_id": "cabinet", "material_requirement_id": "track", "cost_ex_vat": 200}],
        "lines": [{
            "purchase_kind": "linear_cut",
            "allocations": [{"object_id": "cabinet", "material_requirement_id": "track", "length_mm": 4130, "quantity": 1}],
        }],
        "assumption_fallbacks": [{
            "object_id": "cabinet", "material_requirement_id": "track",
            "source_name": "Sliding door track", "unit": "m", "quantity_per_item": 4.13,
            "reason_code": "no_company_or_israel_candidate",
            "assumption_price": {"rationale": ["No source was found.", "Allowance selected."]},
        }],
    })

    assert updates[0]["values"]["item_name"] == "Sliding door track"
    assert updates[0]["values"]["unit"] == "project allocation"
    assert updates[0]["values"]["quantity"] is None
    assert updates[0]["values"]["unit_cost"] is None
    assert updates[0]["values"]["cost"] == 200
    assert updates[0]["values"]["needs_price"] is False
    assert updates[0]["values"]["raw_agent_json"]["price_source"] == "A"


def test_priced_materials_with_open_review_still_publish_provisional_totals(monkeypatch):
    updates = []
    policy_lines = []
    totals = []
    progress = []
    source_lines = [{
        "section": "material", "object_id": "cabinet", "line_id": "line-1", "company_id": "company-1",
        "cost": 1000.0, "source": "estimation_assembly_bom_v4_24",
        "raw_agent_json": {"facts": {"requirement_id": "mdf", "family": "mdf_hdf"}},
    }]
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines", lambda *_args: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines_for_object", lambda *_args, **_kwargs: pd.DataFrame(source_lines))
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *_args: pd.DataFrame([
        {"object_id": "cabinet", "quantity": 1, "company_id": "company-1"},
    ]))
    monkeypatch.setattr(estimation, "fetch_company_overhead_settings", lambda *_args: pd.DataFrame([{
        "consumables_percent": 5, "paint_consumables_percent": 10, "packaging_percent": 1,
    }]))
    monkeypatch.setattr(estimation, "update_rfq_estimate_line", lambda _client, **kwargs: updates.append(kwargs))
    monkeypatch.setattr(estimation, "upsert_rfq_estimate_lines", lambda _client, *, lines: policy_lines.extend(lines))
    monkeypatch.setattr(estimation, "_recalculate_object_estimate_totals",
                        lambda _client, **kwargs: totals.append(kwargs))
    monkeypatch.setattr(estimation, "update_rfq_object_estimate_progress",
                        lambda _client, **kwargs: progress.append(kwargs))

    estimation.apply_material_plan_allocations(client=object(), estimate_id="estimate-1", plan_snapshot={
        "status": "needs_review",
        "parts_check": {"cabinet": {"issues": [{"reason": "dimensions_pending"}],
                                    "unpriced_requirements": ["unpriced"], "has_unresolved_demands": True}},
        "object_material_costs": [{"object_id": "cabinet", "material_requirement_id": "mdf", "cost_ex_vat": 1000}],
        "lines": [{"purchase_kind": "sheet", "allocations": [{
            "object_id": "cabinet", "material_requirement_id": "mdf", "area_mm2": 1_000_000,
        }]}],
    })

    assert [line["item_name"] for line in policy_lines] == ["Consumables", "Paint consumables", "Packaging"]
    assert [line["cost"] for line in policy_lines] == [50.0, 0.0, 10.0]
    assert all(line["source"] == "pricing_policy" for line in policy_lines)
    assert totals == [{"estimate_id": "estimate-1", "object_id": "cabinet"}]
    assert [event["status"] for event in progress] == ["review_required"]


def test_profile_paint_consumables_use_only_coating_material_cost():
    lines = pd.DataFrame([
        {"section": "material", "source": "catalog", "cost": 1000,
         "raw_agent_json": {"facts": {"family": "mdf_hdf"}}},
        {"section": "material", "source": "catalog", "cost": 500,
         "raw_agent_json": {"facts": {"family": "wood_coatings"}}},
    ])

    primary, coating = estimation._material_policy_base_totals(lines)
    policies = estimation._material_policy_lines(
        estimate_id="estimate-1", object_id="cabinet", company_id="company-1",
        settings={"consumables_percent": 5, "paint_consumables_percent": 10, "packaging_percent": 1},
        primary_material_total=primary, coating_material_total=coating,
    )

    assert (primary, coating) == (1500.0, 500.0)
    assert [line["cost"] for line in policies] == [75.0, 50.0, 15.0]


def test_project_material_purchase_rows_preserve_whole_sheet_cost():
    rows = estimation._project_material_purchase_rows({
        "lines": [{
            "display_name": "LDSP 18 mm", "purchase_kind": "sheet", "purchase_quantity": 2,
            "price_per_purchase_unit": 211.99, "total_cost": 423.98, "authority": "israel_reference",
        }],
    })

    assert rows == [{
        "item": "LDSP 18 mm", "purchase": "2 sheet", "unit_price": 211.99,
        "total_cost": 423.98, "price_source": "I",
    }]
