from concurrent.futures import Future

import streamlit as st

from screens import objects
from ui import object_detail_view, objects_pricing
from use_cases.estimation import (
    _estimation_preview_url,
    _material_rows_from_v2_facts,
    _objects_project_pricing,
    _suggested_sale_price,
)
from use_cases.estimation_progress import get_estimate_progress, set_object_progress


def test_pending_object_without_v2_facts_stays_disabled():
    markup = objects_pricing._review_action_html(
        {"object_key": "object-1", "status": "pending"},
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert ">Pending<" in markup
    assert "aria-disabled" in markup


def test_review_required_object_is_openable_without_fake_self_cost():
    row = {
        "status": "review_required",
        "object_key": "object-1",
        "self_cost_unit": "review_required",
    }

    assert objects_pricing._self_cost_unit_html(row) == "review"
    markup = objects_pricing._review_action_html(
        row,
        estimate_id="estimate-1",
        run_id="run-1",
    )
    assert ">Review</a>" in markup


def test_review_required_object_displays_persisted_approximate_self_cost():
    row = {
        "status": "review_required",
        "object_key": "object-1",
        "self_cost_unit": 1725.61,
    }

    assert objects_pricing._self_cost_unit_html(row) == "₪1\u202f726"


def test_project_totals_include_priced_review_required_objects():
    rows = [{
        "object_key": "object-1", "status": "review_required",
        "sale_price_total": 1300.0,
    }]

    project_costs, summary = _objects_project_pricing(rows, vat_percent=18)

    assert project_costs[0]["sale_price_unit"] == 39.0
    assert project_costs[1]["sale_price_unit"] == 130.0
    assert summary == {"project_price": 1469.0, "vat": 264.42, "total": 1733.42, "vat_percent": 18}


def test_objects_show_blank_project_pricing_until_every_object_finishes(monkeypatch):
    st.session_state.clear()
    st.session_state.estimation_batch_future = Future()
    monkeypatch.setattr(objects, "get_estimate_progress", lambda _estimate_id: None)
    data = {
        "rows": [
            {
                "object_key": "object-1",
                "name": "Cabinet",
                "status": "review_required",
                "sale_price_total": 1300.0,
            },
            {
                "object_key": "object-2",
                "name": "Bench",
                "status": "running",
                "sale_price_total": 900.0,
            },
        ],
        "project_costs": [{"object_key": "delivery", "name": "Delivery"}],
        "summary": {"project_price": 2200.0, "vat": 396.0, "total": 2596.0},
    }

    visible = objects._data_with_progress(data, "estimate-1")
    markup = objects_pricing.pricing_table_html(
        rows=visible["rows"],
        project_costs=visible["project_costs"],
        summary=visible["summary"],
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert [row["name"] for row in visible["project_costs"]] == ["Delivery", "Installation"]
    assert all(row["sale_price_unit"] is None for row in visible["project_costs"])
    assert visible["summary"]["project_pricing_ready"] is False
    assert "Delivery" in markup
    assert "Installation" in markup
    assert "Project Summary" in markup
    assert markup.count("—") >= 5


def test_objects_show_project_pricing_after_every_object_finishes(monkeypatch):
    st.session_state.clear()
    monkeypatch.setattr(objects, "get_estimate_progress", lambda _estimate_id: None)
    data = {
        "rows": [
            {
                "object_key": "object-1",
                "name": "Cabinet",
                "status": "review_required",
                "sale_price_total": 1300.0,
            },
            {
                "object_key": "object-2",
                "name": "Bench",
                "status": "review_required",
                "sale_price_total": 900.0,
            },
        ],
        "project_costs": [{"object_key": "delivery", "name": "Delivery"}],
        "summary": {"project_price": 2200.0, "vat": 396.0, "total": 2596.0},
    }

    visible = objects._data_with_progress(data, "estimate-1")
    markup = objects_pricing.pricing_table_html(
        rows=visible["rows"],
        project_costs=visible["project_costs"],
        summary=visible["summary"],
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert visible["summary"]["project_pricing_ready"] is True
    assert "Delivery" in markup
    assert "Project Summary" in markup


def test_completed_estimation_future_clears_stale_process_progress():
    st.session_state.clear()
    future = Future()
    future.set_result({"status": "completed"})
    st.session_state.estimation_batch_future = future
    st.session_state.current_estimate_id = "estimate-1"
    set_object_progress(
        estimate_id="estimate-1", object_id="object-2", percent=58, status="running"
    )

    objects._consume_estimation_future()

    assert get_estimate_progress("estimate-1") is None
    assert st.session_state.estimation_batch_future is None


def test_company_pricing_policy_drives_sale_delivery_installation_and_vat():
    assert _suggested_sale_price(1000, 25) == 1250
    project_costs, summary = _objects_project_pricing(
        [{"object_key": "object-1", "status": "completed", "sale_price_total": 1250}],
        vat_percent=17, delivery_percent=4, installation_percent=8,
    )
    assert [row["sale_price_unit"] for row in project_costs] == [50, 100]
    assert summary == {
        "project_price": 1400, "vat": 238, "total": 1638, "vat_percent": 17,
    }


def test_object_detail_uses_v2_materials_without_inventing_costs():
    rows = _material_rows_from_v2_facts({
        "materials": [{
            "requirement_id": "mat-1",
            "source_name": "MDF panel 20 mm",
            "family": "mdf",
            "unit": "m2",
            "quantity": None,
        }]
    })

    assert rows == [{
        "group": "Detected materials",
        "line_id": "mat-1",
        "item": "MDF panel 20 mm",
        "unit": "m2",
        "unit_cost": None,
        "qty": None,
        "cost": None,
    }]


class _Bucket:
    def create_signed_url(self, path, expires_in):
        assert path == "company-1/run-1/object-1/preview.webp"
        assert expires_in == 3600
        return {"signedURL": "https://signed.example/preview.webp"}


class _Storage:
    def from_(self, bucket):
        assert bucket == "rfq-estimation-evidence"
        return _Bucket()


class _Client:
    storage = _Storage()


def test_object_detail_preview_requires_owned_private_path():
    assert _estimation_preview_url(
        _Client(),
        "storage://rfq-estimation-evidence/company-1/run-1/object-1/preview.webp",
        company_id="company-1",
    ) == "https://signed.example/preview.webp"
    assert _estimation_preview_url(
        _Client(),
        "storage://rfq-estimation-evidence/company-2/run-1/object-1/preview.webp",
        company_id="company-1",
    ) is None


def test_object_detail_hero_renders_source_preview():
    markup = object_detail_view.hero_html({
        "name": "Shelving unit",
        "quantity": 1,
        "confidence": 0.95,
        "preview_label": "Object preview",
        "preview_url": "https://signed.example/preview.webp",
    })

    assert 'class="object-detail-preview-image"' in markup
    assert 'src="https://signed.example/preview.webp"' in markup
