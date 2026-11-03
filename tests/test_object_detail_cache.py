from concurrent.futures import Future

import streamlit as st

from screens import object_detail
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

    invalidate_object_detail_cache("estimate-old")

    assert ("estimate-old", "object-1") not in st.session_state.object_detail_data_cache
    assert ("estimate-other", "object-2") in st.session_state.object_detail_data_cache
    assert ("estimate-old", "object-1") not in st.session_state.object_detail_prefetch_futures
    assert ("estimate-other", "object-2") in st.session_state.object_detail_prefetch_futures


def test_new_estimate_reset_drops_object_detail_snapshots_and_prefetches():
    st.session_state.clear()
    st.session_state.current_run_id = "run-old"
    st.session_state.object_detail_data_cache = {("estimate-old", "object-1"): {}}
    st.session_state.object_detail_data_cache_dirty = {"estimate-old"}
    st.session_state.object_detail_prefetch_futures = {("estimate-old", "object-1"): Future()}

    reset_new_estimate_session(clear_upload_widget=False)

    assert st.session_state.object_detail_data_cache == {}
    assert st.session_state.object_detail_data_cache_dirty == set()
    assert st.session_state.object_detail_prefetch_futures == {}


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
