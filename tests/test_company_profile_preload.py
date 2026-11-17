from concurrent.futures import Future
from types import SimpleNamespace

import pytest
import streamlit as st

from screens import company_profile
from state.company_auth import clear_auth_session


@pytest.fixture(autouse=True)
def clear_profile_session():
    st.session_state.clear()
    yield
    clear_auth_session()


def access(role="owner", company="company-a"):
    return SimpleNamespace(company_id=company, user_id="user-1", role=role)


@pytest.mark.parametrize("role, expected", [("owner", 4), ("member", 3)])
def test_preload_queues_once_without_running_readers_on_the_ui_thread(monkeypatch, role, expected):
    submitted = []

    def submit(loader):
        future = Future()
        submitted.append((loader, future))
        return future

    monkeypatch.setattr(company_profile, "_PROFILE_READ_EXECUTOR", SimpleNamespace(submit=submit))
    monkeypatch.setattr(company_profile, "_price_lists_projection_state", lambda _: {"futures": {}})
    owner = access(role)

    company_profile._start_post_overhead_warmup(owner)
    company_profile._start_post_overhead_warmup(owner)

    assert len(submitted) == expected
    assert all(not future.done() for _, future in submitted)
    state = company_profile._profile_preload_state(owner)
    assert ("employees" in state["entries"]) is (role == "owner")


def test_invalidating_a_running_read_prevents_old_values_after_save():
    owner = access()
    old = Future()
    old.set_running_or_notify_cancel()
    company_profile._profile_preload_state(owner)["entries"]["company"] = {
        "future": old, "started_at": company_profile.time.monotonic(),
    }

    company_profile._invalidate_profile_read(owner, "company")
    assert company_profile._profile_prepared_read(
        owner, "company", lambda: {"company_name": "Saved"},
    ) == {"company_name": "Saved"}
    old.set_result({"company_name": "Before save"})

    assert company_profile._profile_prepared_read(
        owner, "company", lambda: pytest.fail("The saved snapshot must be reused"),
    ) == {"company_name": "Saved"}


@pytest.mark.parametrize("next_access", [access("member"), access(company="company-b")])
def test_identity_change_discards_prepared_reads(next_access):
    pending = Future()
    company_profile._profile_preload_state(access())["entries"]["company"] = {
        "future": pending, "started_at": company_profile.time.monotonic(),
    }

    assert company_profile._profile_preload_state(next_access)["entries"] == {}
    assert pending.cancelled()


def test_prepared_data_is_copied_and_expires(monkeypatch):
    owner = access()
    clock = [100]
    monkeypatch.setattr(company_profile.time, "monotonic", lambda: clock[0])
    value = company_profile._profile_prepared_read(owner, "company", lambda: {"name": "Original"})
    value["name"] = "UI edit"
    assert company_profile._profile_prepared_read(owner, "company", lambda: None) == {"name": "Original"}

    clock[0] += company_profile._PROFILE_READ_TTL_SECONDS + 1
    assert company_profile._profile_prepared_read(owner, "company", lambda: {"name": "Refreshed"}) == {
        "name": "Refreshed",
    }


def test_sign_out_cancels_queued_reads():
    pending = Future()
    company_profile._profile_preload_state(access())["entries"]["members"] = {
        "future": pending, "started_at": company_profile.time.monotonic(),
    }

    clear_auth_session()

    assert pending.cancelled()
    assert st.session_state.get("company_profile_preload") is None
