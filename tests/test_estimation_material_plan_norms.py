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
    monkeypatch.setattr(estimation, "fetch_rfq_estimate_lines", lambda *_args: pd.DataFrame([{
        "section": "material", "object_id": "cabinet", "line_id": "line-1",
        "raw_agent_json": {"facts": {"requirement_id": "mdf"}},
    }]))
    monkeypatch.setattr(estimation, "fetch_rfq_object_estimates", lambda *_args: pd.DataFrame([{
        "object_id": "cabinet", "quantity": 1,
    }]))
    monkeypatch.setattr(
        estimation, "update_rfq_estimate_line",
        lambda _client, **kwargs: updates.append(kwargs),
    )
    monkeypatch.setattr(estimation, "_recalculate_object_estimate_totals", lambda *_args, **_kwargs: None)

    estimation.apply_material_plan_allocations(client=object(), estimate_id="estimate-1", plan_snapshot={
        "status": "needs_review",
        "object_material_costs": [{"object_id": "cabinet", "material_requirement_id": "mdf", "cost_ex_vat": 244}],
        "lines": [{
            "display_name": "MDF 20 mm 1220 × 2440 mm, raw", "purchase_kind": "sheet",
            "allocations": [{"object_id": "cabinet", "material_requirement_id": "mdf", "area_mm2": 1_000_000}],
        }],
    })

    assert updates[0]["values"]["item_name"] == "MDF 20 mm 1220 × 2440 mm, raw"
    assert updates[0]["values"]["cost"] == 244
    assert updates[0]["values"]["needs_price"] is False
