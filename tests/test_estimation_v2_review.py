from concurrent.futures import Future
from pathlib import Path

import streamlit as st

from screens import objects
from ui import object_detail_view, objects_pricing
from use_cases.estimation import (
    apply_object_detail_snapshot,
    _estimation_preview_url,
    _material_rows_from_v2_facts,
    _objects_project_pricing,
    _suggested_sale_price,
    update_object_quantity,
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


def test_review_uses_durable_route_and_quantity_is_editable():
    row = {
        "status": "completed",
        "object_key": "object-1",
        "quantity": 3,
        "route_token": "durable-token",
    }

    markup = objects_pricing.pricing_table_html(
        rows=[row],
        project_costs=[],
        summary={"project_price": None, "vat": None, "total": None},
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert 'href="?screen=object_detail&amp;route_token=durable-token"' not in markup
    assert 'href="?screen=object_detail&route_token=durable-token"' in markup
    assert 'data-object-quantity-input="true"' in markup
    assert '>3</div>' in markup


def test_quantity_update_writes_canonical_and_mirror_and_clears_approval(monkeypatch):
    import pandas as pd

    detected_updates = []
    estimate_updates = []
    monkeypatch.setattr("use_cases.estimation.get_supabase_client", lambda: object())
    monkeypatch.setattr("use_cases.estimation.company_auth_enabled", lambda: False)
    monkeypatch.setattr(
        "use_cases.estimation.fetch_rfq_object_estimates",
        lambda _client, _estimate_id: pd.DataFrame([
            {"run_id": "run-1", "object_id": "object-1"}
        ]),
    )
    monkeypatch.setattr(
        "use_cases.estimation.update_rfq_object_estimate_quantity",
        lambda _client, **kwargs: estimate_updates.append(kwargs),
    )
    monkeypatch.setattr(
        "use_cases.estimation.update_rfq_detected_object",
        lambda _client, **kwargs: detected_updates.append(kwargs),
    )

    assert update_object_quantity(
        estimate_id="estimate-1",
        run_id="run-1",
        object_id="object-1",
        quantity=4,
    ) == 4
    assert estimate_updates == [{
        "estimate_id": "estimate-1",
        "object_id": "object-1",
        "quantity": 4.0,
        "approved": False,
    }]
    assert detected_updates == [{
        "run_id": "run-1",
        "object_id": "object-1",
        "values": {"quantity": 4.0},
    }]


def test_quantity_blur_saves_through_authenticated_rpc_without_rerun():
    source = Path("ui/js_guards.py").read_text()
    guard = source.split("def install_objects_price_input_guard", 1)[1].split(
        "def install_object_detail_input_guard", 1
    )[0]

    assert 'data-object-quantity-input' in guard
    assert 'focusout' in guard
    assert '/rest/v1/rpc/save_rfq_object_quantity' in guard
    assert 'overlay.classList.add("is-visible")' in guard
    assert 'streamlit:setComponentValue' not in guard


def test_object_detail_quantity_uses_the_approve_snapshot_not_the_objects_bridge():
    detail_source = Path("screens/object_detail.py").read_text()
    runtime_source = Path("ui/js_guards.py").read_text()

    assert "object_detail_quantity_bridge" not in detail_source
    assert 'line_id: "__object__"' in runtime_source
    assert 'field: "object_quantity"' in runtime_source
    assert "object-detail-discard-modal" in runtime_source
    assert "Are you sure you want to leave without saving?" in runtime_source
    assert "parentWindow.confirm" not in runtime_source.split(
        "def install_object_detail_input_guard", 1
    )[1].split("def install_objects_live_progress", 1)[0]


def test_object_detail_draft_uses_authenticated_rpc_then_native_bridge():
    source = Path("ui/js_guards.py").read_text()
    guard = source.split("def install_object_detail_input_guard", 1)[1].split(
        "def install_objects_live_progress", 1
    )[0]

    assert "/rest/v1/rpc/save_rfq_object_detail_draft" in guard
    assert "Authorization: `Bearer ${SUPABASE_ACCESS_TOKEN}`" in guard
    assert 'button.textContent = "SAVING..."' in guard
    assert 'button.setAttribute("data-streamlit-bridge-key", "object_detail_approve_bridge")' in guard
    assert "button.click()" in guard
    assert "streamlit:setComponentValue" not in guard


def test_quantity_event_detection_does_not_capture_other_detail_inputs():
    source = Path("ui/js_guards.py").read_text()
    guard = source.split("def install_object_detail_input_guard", 1)[1].split(
        "def install_objects_live_progress", 1
    )[0]

    assert "if (target !== undefined && target !== null)" in guard
    assert "return direct || null;" in guard
    assert "return parentDoc.querySelector" in guard


def test_objects_quantity_uses_direct_rpc_without_streamlit_rerun():
    source = Path("ui/js_guards.py").read_text()
    guard = source.split("def install_objects_price_input_guard", 1)[1].split(
        "def install_object_detail_input_guard", 1
    )[0]

    assert "/rest/v1/rpc/save_rfq_object_quantity" in guard
    assert 'overlay.classList.add("is-visible")' in guard
    assert "streamlit:setComponentValue" not in guard


def test_object_detail_quantity_snapshot_persists_only_at_approval(monkeypatch):
    updates = []
    monkeypatch.setattr(
        "use_cases.estimation.update_object_quantity",
        lambda **kwargs: updates.append(kwargs),
    )

    apply_object_detail_snapshot(
        estimate_id="estimate-1",
        run_id="run-1",
        object_id="object-1",
        edits=[{
            "line_id": "__object__",
            "field": "object_quantity",
            "value": "5",
        }],
    )

    assert updates == [{
        "estimate_id": "estimate-1",
        "run_id": "run-1",
        "object_id": "object-1",
        "quantity": 5.0,
    }]


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
    assert "Project Price" in markup
    assert "Project Summary" not in markup
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
    assert "Project Price" in markup
    assert "Project Summary" not in markup


def test_approved_objects_show_pdf_and_future_xls_download_row():
    markup = objects_pricing.pricing_table_html(
        rows=[],
        project_costs=[],
        summary={"project_price": 100, "vat": 18, "total": 118},
        estimate_id="estimate-1",
        run_id="run-1",
        proposal_pdf_url="https://signed.example/proposal.pdf",
    )

    assert "Client Proposal" in markup
    assert "Download PDF" in markup
    assert "Project Summary" in markup
    assert "Download XLS" in markup
    assert 'href="https://signed.example/proposal.pdf"' in markup
    assert 'objects-pricing-download-button--disabled' in markup

    css = Path("styles/objects.py").read_text()
    assert ".objects-pricing-download-block--summary" in css
    assert "grid-column: 2 / 5" in css
    assert "width: 162px" in css
    assert ".objects-pricing-summary-price" in css
    assert ".objects-pricing-summary-vat" in css
    assert ".objects-pricing-summary-total" in css
    assert "--objects-summary-price-axis: calc(100% - 658px)" in css
    assert "--objects-summary-total-axis: calc(74.712644% + 34.896552px)" in css
    assert "left: calc(87.356322% - 311.551724px)" in css
    assert ".objects-pricing-summary-total" in css
    assert "grid-column: 4" in css


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
