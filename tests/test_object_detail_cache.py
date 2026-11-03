from concurrent.futures import Future

import streamlit as st

from screens import object_detail
from screens import objects
from state.session import invalidate_object_detail_cache, reset_new_estimate_session
from use_cases import object_detail_runtime


def test_object_detail_uses_ready_session_snapshot_without_a_second_read(monkeypatch):
    st.session_state.clear()
    context = object_detail.ObjectDetailContext(
        estimate_id="estimate-1", object_id="object-1", run_id="run-1",
    )
    expected = {"name": "Cabinet", "sections": []}
    st.session_state.object_detail_data_cache = {
        (context.estimate_id, context.object_id): expected,
    }
    st.session_state.object_detail_data_cache_dirty = set()

    monkeypatch.setattr(
        object_detail,
        "load_object_detail_data",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected database read")),
    )

    assert object_detail._load_object_detail_or_render_error(context) == expected


def test_object_detail_consumes_completed_prefetch_snapshot(monkeypatch):
    st.session_state.clear()
    context = object_detail.ObjectDetailContext(
        estimate_id="estimate-1", object_id="object-1", run_id="run-1",
    )
    prefetched = Future()
    prefetched.set_result({"name": "Cabinet", "sections": []})
    st.session_state.object_detail_prefetch_futures = {
        (context.estimate_id, context.object_id): prefetched,
    }

    monkeypatch.setattr(
        object_detail,
        "load_object_detail_data",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected fallback read")),
    )

    assert object_detail._load_object_detail_or_render_error(context)["name"] == "Cabinet"
    assert st.session_state.object_detail_data_cache[("estimate-1", "object-1")]["name"] == "Cabinet"
    assert st.session_state.object_detail_prefetch_futures == {}


def test_invalidating_estimate_discards_all_its_detail_cache_and_prefetches():
    st.session_state.clear()
    old_prefetch = Future()
    st.session_state.object_detail_data_cache = {
        ("estimate-old", "object-1"): {"name": "Old"},
        ("estimate-other", "object-2"): {"name": "Other"},
    }
    st.session_state.object_detail_prefetch_futures = {
        ("estimate-old", "object-1"): old_prefetch,
        ("estimate-other", "object-2"): Future(),
    }
    st.session_state.object_detail_prefetch_failed = {
        ("estimate-old", "object-1"),
        ("estimate-other", "object-2"),
    }

    invalidate_object_detail_cache("estimate-old")

    assert ("estimate-old", "object-1") not in st.session_state.object_detail_data_cache
    assert ("estimate-other", "object-2") in st.session_state.object_detail_data_cache
    assert ("estimate-old", "object-1") not in st.session_state.object_detail_prefetch_futures
    assert ("estimate-other", "object-2") in st.session_state.object_detail_prefetch_futures
    assert ("estimate-old", "object-1") not in st.session_state.object_detail_prefetch_failed
    assert ("estimate-other", "object-2") in st.session_state.object_detail_prefetch_failed


def test_new_estimate_reset_drops_object_detail_snapshots_and_prefetches():
    st.session_state.clear()
    st.session_state.current_run_id = "run-old"
    st.session_state.object_detail_data_cache = {("estimate-old", "object-1"): {}}
    st.session_state.object_detail_data_cache_dirty = {"estimate-old"}
    st.session_state.object_detail_prefetch_futures = {("estimate-old", "object-1"): Future()}
    st.session_state.object_detail_prefetch_failed = {("estimate-old", "object-1")}

    reset_new_estimate_session(clear_upload_widget=False)

    assert st.session_state.object_detail_data_cache == {}
    assert st.session_state.object_detail_data_cache_dirty == set()
    assert st.session_state.object_detail_prefetch_futures == {}
    assert st.session_state.object_detail_prefetch_failed == set()


def test_prefetch_runtime_passes_explicit_company_scope(monkeypatch):
    captured = {}

    def fake_load(**kwargs):
        captured.update(kwargs)
        return {"name": "Cabinet"}

    monkeypatch.setattr(object_detail_runtime, "load_object_detail_data", fake_load)

    result = object_detail_runtime.submit_object_detail_prefetch(
        estimate_id="estimate-1", object_id="object-1", company_id="610",
    ).result(timeout=2)

    assert result == {"name": "Cabinet"}
    assert captured == {
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }


def test_review_waits_for_object_detail_prefetch_not_the_global_material_plan(monkeypatch):
    """A terminal object becomes clickable only after its own detail is cached."""
    st.session_state.clear()
    prefetch = Future()
    submitted = []

    def submit(**kwargs):
        submitted.append(kwargs)
        return prefetch

    monkeypatch.setattr(objects, "submit_object_detail_prefetch", submit)
    data = {
        "material_plan_ready": False,
        "rows": [{"object_key": "object-1", "status": "completed"}],
    }

    preparing = objects._prepare_completed_object_detail_reviews(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    assert preparing["rows"][0]["review_ready"] is False
    assert submitted == [{
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }]

    prefetch.set_result({"name": "Cabinet", "sections": []})
    ready = objects._prepare_completed_object_detail_reviews(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    assert ready["rows"][0]["review_ready"] is True
    assert st.session_state.object_detail_data_cache[("estimate-1", "object-1")]["name"] == "Cabinet"


def test_review_action_is_disabled_until_its_prefetch_snapshot_is_ready():
    from ui import objects_pricing

    html = objects_pricing._review_action_html(
        {"object_key": "object-1", "status": "completed", "review_ready": False},
        estimate_id="estimate-1",
        run_id="run-1",
    )

    assert "Preparing Review" in html
    assert "aria-disabled=\"true\"" in html
    assert "href=" not in html


def test_failed_prefetch_falls_back_once_without_fragment_retry(monkeypatch):
    st.session_state.clear()
    prefetch = Future()
    prefetch.set_exception(RuntimeError("temporary database error"))
    submitted = []

    def submit(**kwargs):
        submitted.append(kwargs)
        return prefetch

    monkeypatch.setattr(objects, "submit_object_detail_prefetch", submit)
    data = {"rows": [{"object_key": "object-1", "status": "completed"}]}

    first = objects._prepare_completed_object_detail_reviews(
        estimate_id="estimate-1", company_id="610", data=data,
    )
    second = objects._prepare_completed_object_detail_reviews(
        estimate_id="estimate-1", company_id="610", data=data,
    )

    assert first["rows"][0]["review_ready"] is False
    assert second["rows"][0]["review_ready"] is True
    assert submitted == [{
        "estimate_id": "estimate-1", "object_id": "object-1", "company_id": "610",
    }]
