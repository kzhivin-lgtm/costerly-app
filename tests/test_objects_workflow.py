from copy import deepcopy
import pytest

from screens import objects
from ui import objects_workflow
from ui.objects_workflow import pricing_signature


def data():
    return {"rows": [{"object_key": "one", "quantity": 1, "self_cost_unit": 100, "sale_price_unit": 130,
                      "sale_price_total": 130, "reviewed": True, "status": "completed"}],
            "project_costs": [{"object_key": "delivery", "sale_price_unit": 4}],
            "summary": {"project_price": 134, "vat": 24.12, "total": 158.12}}


@pytest.mark.parametrize("field,value", [("quantity", 2), ("self_cost_unit", 110), ("sale_price_unit", 150), ("sale_price_total", 150), ("reviewed", False)])
def test_confirmation_is_bound_to_the_current_review_and_commercial_basis(field, value):
    before = data()
    after = deepcopy(before)
    after["rows"][0][field] = value
    assert pricing_signature(before) != pricing_signature(after)


def test_project_allocation_changes_also_require_setting_prices_again():
    before = data()
    after = deepcopy(before)
    after["project_costs"][0]["sale_price_unit"] = 10
    assert pricing_signature(before) != pricing_signature(after)


def test_telemetry_and_progress_refresh_do_not_revoke_a_confirmation():
    before = data()
    after = deepcopy(before)
    after["rows"][0].update(progress_percent=100, progress_label="Ready", elapsed=2)
    after["timings"] = {"total": 4}
    after["summary"]["project_pricing_ready"] = True
    assert pricing_signature(before) == pricing_signature(after)


def test_three_stages_follow_real_review_confirmation_and_proposal():
    state = data()
    assert 'data-stage="2" data-state="current"' in objects_workflow.stages_html(state, prices_set=False, proposal_ready=False)
    assert 'data-stage="3" data-state="current"' in objects_workflow.stages_html(state, prices_set=True, proposal_ready=False)
    assert objects_workflow.stages_html(state, prices_set=True, proposal_ready=True).count('data-state="complete"') == 3
    state["rows"][0]["reviewed"] = False
    assert 'data-stage="1" data-state="current"' in objects_workflow.stages_html(state, prices_set=False, proposal_ready=False)


def test_set_prices_accepts_saved_values_without_changing_them(monkeypatch):
    saved = data()
    before = deepcopy(saved)
    session = {}
    monkeypatch.setattr(objects.st, "session_state", session)
    monkeypatch.setattr(objects, "_persisted_objects_state", lambda _: objects.ObjectsScreenState(data=saved))
    monkeypatch.setattr(objects, "_cache_routed_objects_data", lambda **_: None)
    objects._set_objects_prices(estimate_id="e")
    assert saved == before
    assert session["objects_set_price_basis"]["e"] == pricing_signature(saved)
    assert objects_workflow.prices_are_set("e", saved)


def test_failed_saved_read_cannot_confirm_prices(monkeypatch):
    session = {}
    monkeypatch.setattr(objects.st, "session_state", session)
    monkeypatch.setattr(objects, "_persisted_objects_state", lambda _: objects.ObjectsScreenState(data=data(), cache_warning="stale read"))
    objects._set_objects_prices(estimate_id="e")
    assert "e" not in session["objects_set_price_basis"]
    assert session["final_approval_error"]
