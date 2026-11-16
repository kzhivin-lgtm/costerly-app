from __future__ import annotations

import ast
import inspect
from concurrent.futures import Future
from pathlib import Path

import streamlit as st

import app
from screens import file_review, objects
from state import session
from use_cases import rfq_processing


def test_profile_route_stays_at_profile_level():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Contacts"

    assert app._browser_route("account") == {"screen": "account"}


def test_new_estimate_reset_clears_all_estimate_scoped_session_state():
    st.session_state.clear()
    st.session_state.update({
        "current_run_id": "run-old",
        "current_estimate_id": "estimate-old",
        "uploaded_file_name": "same.pdf",
        "uploaded_file_bytes": b"same-bytes",
        "processed_file_name": "same.pdf",
        "file_review_data_cache": {"run-old": {"objects": [{"name": "Object 3"}]}},
        "objects_estimation_data_cache": {"estimate-old": {"rows": []}},
        "objects_estimation_cache_dirty": {"estimate-old"},
        "file_review_naming_published.run-old": True,
        "file_review_naming_cache_synced.run-old": True,
        "current_document_identity_future": object(),
        "rfq_upload_input": "previous-file-widget-value",
    })

    session.reset_new_estimate_session(clear_upload_widget=True)

    assert st.session_state.current_run_id is None
    assert st.session_state.current_estimate_id is None
    assert st.session_state.uploaded_file_name is None
    assert st.session_state.uploaded_file_bytes is None
    assert st.session_state.file_review_data_cache == {
        "run-old": {"objects": [{"name": "Object 3"}]}
    }
    assert st.session_state.objects_estimation_data_cache == {}
    assert st.session_state.objects_estimation_cache_dirty == set()
    assert st.session_state.processed_file_name is None
    assert st.session_state.current_document_identity_future is None
    assert "file_review_naming_published.run-old" not in st.session_state
    assert "file_review_naming_cache_synced.run-old" not in st.session_state
    assert "rfq_upload_input" not in st.session_state
    assert st.session_state.rfq_upload_widget_generation == 1


def test_new_estimate_reset_discards_retained_review_widget_value():
    st.session_state.clear()
    run_id = "run-old"
    object_id = "object-3"
    widget_key = f"file_review_object_edits.{object_id}.name"
    st.session_state.update({
        "current_run_id": run_id,
        "file_review_data_cache": {
            run_id: {"objects": [{"object_id": object_id, "name": ""}]},
        },
        widget_key: "",
    })

    session.reset_new_estimate_session(clear_upload_widget=False)

    assert run_id in st.session_state.file_review_data_cache
    assert widget_key not in st.session_state


def test_restored_review_hydrates_durable_name_before_object_edit_state(monkeypatch):
    st.session_state.clear()
    run_id = "run-old"
    object_id = "object-3"
    st.session_state.update({
        "current_run_id": run_id,
        "file_review_data_cache": {
            run_id: {"objects": [{"object_id": object_id, "name": ""}]},
        },
        f"file_review_object_edits.{object_id}.name": "",
        "current_agent_timings": {},
    })
    session.reset_new_estimate_session(clear_upload_widget=False)
    st.session_state.current_run_id = run_id
    monkeypatch.setattr(
        file_review,
        "load_file_review_naming_publication",
        lambda _run_id: {
            "status": "succeeded", "names": {object_id: "Metal mesh panel"},
        },
    )

    data = file_review._load_file_review_screen_data(run_id)
    file_review._sync_durable_naming_once(run_id)
    file_review._sync_object_edit_state(run_id, data["objects"])

    assert data["objects"][0]["name"] == "Metal mesh panel"
    assert st.session_state.file_review_initial_object_names == {
        object_id: "Metal mesh panel",
    }
    assert file_review._ensure_object_edit(object_id, data["objects"][0]) == {
        "name": "Metal mesh panel", "expected_name": "Metal mesh panel",
        "quantity": "1", "ignored": False,
    }


def test_file_review_publishes_document_identity_before_metadata_widgets():
    st.session_state.clear()
    run_id = "run-identity"
    st.session_state.file_review_deferred_work = {
        "run_id": run_id, "document_identity": True,
    }
    st.session_state.file_review_data_cache = {
        run_id: {"run": {"project_name": "unknown", "partner": "unknown", "client": "unknown"}}
    }
    st.session_state.file_review_run_metadata = {
        "project_name": "unknown", "partner": "unknown", "client": "unknown",
    }

    published = file_review._publish_persisted_document_identity(
        run_id,
        {
            "status": "succeeded",
            "metadata": {"project_name": "ROOMS", "partner": "unknown", "client": "unknown"},
        },
    )

    assert published is True
    assert st.session_state.file_review_data_cache[run_id]["run"]["project_name"] == "ROOMS"
    assert st.session_state.file_review_run_metadata["project_name"] == "ROOMS"
    assert st.session_state["file_review_run_metadata.project_name"] == "ROOMS"


def test_file_quality_is_only_part_of_technical_metadata():
    metadata = file_review._metadata_rows_html({"file_quality": "detailed_drawings"})

    assert "File quality" in metadata
    assert not hasattr(file_review, "_review_card_quality_html")


def test_account_bootstrap_drops_legacy_profile_tab_parameter():
    source = (Path(__file__).parents[1] / "app.py").read_text()
    account_bootstrap = source.split('if requested_screen == "account":', 1)[1].split(
        "post_sign_in_terms_check", 1
    )[0]
    wrapper = (Path(__file__).parents[1] / "cloudflare" / "index.html").read_text()

    assert 'for route_key in ("screen", "profile_tab"):' in account_bootstrap
    assert 'nextUrl.searchParams.delete("profile_tab");' in wrapper


def test_file_review_route_preserves_run_context():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"

    assert app._browser_route("file_review") == {
        "screen": "file_review",
        "run_id": "run-123",
    }


def test_workflow_route_uses_a_short_token_when_company_context_is_available(monkeypatch):
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"
    monkeypatch.setattr(app, "_workflow_route_token", lambda **_kwargs: "short-route-1")

    assert app._browser_route("file_review", company_id="company-1") == {
        "screen": "file_review",
        "route_token": "short-route-1",
    }
    assert app._browser_route("objects", company_id="company-1") == {
        "screen": "objects",
        "route_token": "short-route-1",
    }


def test_prepared_objects_route_does_not_publish_an_unpersisted_estimate_id():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"
    st.session_state.prepared_estimate_access = {
        "run_id": "run-123",
        "estimate_id": "estimate-456",
        "company_id": "company-1",
    }

    assert app._browser_route("objects", company_id="company-1") == {
        "screen": "objects",
        "run_id": "run-123",
    }


def test_file_review_route_keeps_the_active_estimate_for_refresh_recovery():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"

    assert app._browser_route("file_review") == {
        "screen": "file_review",
        "run_id": "run-123",
        "estimate_id": "estimate-456",
    }


def test_object_detail_route_preserves_complete_context():
    st.session_state.clear()
    st.session_state.current_run_id = "run-123"
    st.session_state.current_estimate_id = "estimate-456"
    st.session_state.current_object_id = "object-789"

    assert app._browser_route("object_detail") == {
        "screen": "object_detail",
        "run_id": "run-123",
        "estimate_id": "estimate-456",
        "object_id": "object-789",
    }


def test_object_detail_table_navigation_uses_native_streamlit_bridges():
    objects_source = Path("screens/objects.py").read_text()
    detail_source = Path("screens/object_detail.py").read_text()
    pricing_source = Path("ui/objects_pricing.py").read_text()
    detail_view_source = Path("ui/object_detail_view.py").read_text()

    assert 'key=objects_pricing.object_detail_navigation_key(object_id)' in objects_source
    assert 'st.session_state.screen = "object_detail"' in objects_source
    assert 'key="object_detail_back_bridge"' in detail_source
    assert 'key="object_detail_approve_bridge"' in detail_source
    assert 'st.session_state.screen = "objects"' in detail_source
    assert 'data-streamlit-bridge-key="{navigation_key}"' in pricing_source
    assert 'data-streamlit-bridge-key="object_detail_back_bridge"' in detail_view_source
    assert 'data-streamlit-bridge-key="object_detail_approve_bridge"' in detail_view_source


def test_processing_refresh_fails_safe_to_upload():
    st.session_state.clear()

    assert app._browser_route("processing") == {"screen": "upload"}


def test_screen_change_schedules_target_side_scroll_reset():
    source = Path("app.py").read_text()

    assert 'st.session_state._reset_scroll_on_ready = True' in source
    assert 'reset_scroll=bool(st.session_state.pop("_reset_scroll_on_ready", False))' in source


def test_workflow_routes_do_not_render_the_central_logo_in_auth_disabled_mode():
    source = Path("app.py").read_text()

    assert 'if current_screen == "upload":' in source


def test_profile_route_is_restored_before_account_controls_render():
    source = Path("app.py").read_text()

    restore_position = source.index('if requested_screen == "account":')
    controls_position = source.index("render_account_control(")

    assert restore_position < controls_position


def test_widget_navigation_never_adds_a_second_explicit_rerun():
    """A widget click already reruns Streamlit; navigation must use on_click."""
    root = Path(__file__).parents[1]
    violations = []

    for path in root.rglob("*.py"):
        if any(part in {"tests", "tmp", ".venv"} for part in path.parts):
            continue
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.If) or not isinstance(node.test, ast.Call):
                continue
            function = node.test.func
            if not isinstance(function, ast.Attribute) or function.attr not in {
                "button",
                "form_submit_button",
            }:
                continue
            block = ast.get_source_segment(source, node) or ""
            changes_screen = "session_state.screen" in block or "session_state[\"screen\"]" in block
            if changes_screen and "st.rerun()" in block:
                violations.append(f"{path.relative_to(root)}:{node.lineno}")

    assert violations == []


def test_file_review_navigation_uses_widget_callbacks_not_a_second_rerun():
    source = Path("screens/file_review.py").read_text()
    continue_source = source.split("def _continue_to_objects_estimation", 1)[1].split(
        "def _mark_estimation_batch_started", 1
    )[0]

    assert "on_click=_continue_to_objects_estimation" in source
    assert "on_click=_back_to_upload_from_review" in source
    assert "st.rerun()" not in continue_source


def test_file_review_terminal_actions_precede_deferred_poll_fragment():
    """A terminal poll rerun must never prevent Continue from reaching the DOM."""
    source = Path("screens/file_review.py").read_text()
    review_screen = source.split("def render_file_review_screen", 1)[1].split(
        "def _object_edits_snapshot", 1
    )[0]

    assert review_screen.index('"CONTINUE TO OBJECTS ESTIMATION"') < review_screen.index(
        "_poll_file_review_deferred_work(run_id)"
    )


def test_active_estimation_opens_seeded_objects_without_waiting_for_supabase(monkeypatch):
    st.session_state.clear()
    st.session_state.estimation_batch_future = Future()
    st.session_state.objects_estimation_seed_rows = [
        {
            "object_key": "object-1",
            "name": "Cabinet",
            "quantity": 1,
            "status": "running",
            "self_cost_unit": "1%",
            "sale_price_unit": None,
            "sale_price_total": None,
            "suggestion": "suggested: SC + 30%",
            "reviewed": False,
        }
    ]
    monkeypatch.setattr(
        objects,
        "_load_objects_screen_data",
        lambda _estimate_id: (_ for _ in ()).throw(AssertionError("must not load")),
    )

    state = objects._current_objects_state("estimate-1")

    assert state.data_error is None
    assert state.data["rows"][0]["object_key"] == "object-1"


def test_objects_emits_its_target_header_before_starting_the_background_worker():
    source = Path("screens/objects.py").read_text()
    render_source = source.split("def render_objects_screen", 1)[1].split(
        "def _render_objects_table_content", 1
    )[0]

    assert render_source.index('"Objects Estimation"') < render_source.index(
        "_start_prepared_estimation_launch()"
    )


def test_validated_workflow_access_skips_a_repeat_ownership_read_for_same_session():
    st.session_state.clear()

    app._remember_validated_workflow_access(
        company_id="company-1",
        run_id="run-1",
    )

    assert app._has_validated_workflow_access(
        company_id="company-1",
        run_id="run-1",
    ) is True
    assert app._has_validated_workflow_access(
        company_id="company-2",
        run_id="run-1",
    ) is False
    assert app._has_validated_workflow_access(
        company_id="company-1",
        run_id="run-1",
        estimate_id="estimate-1",
    ) is False

    app._remember_validated_workflow_access(
        company_id="company-1",
        run_id="run-1",
        estimate_id="estimate-1",
    )

    assert app._has_validated_workflow_access(
        company_id="company-1",
        run_id="run-1",
        estimate_id="estimate-1",
    ) is True


def test_continue_uses_prepared_launch_without_sync_persistence(monkeypatch):
    st.session_state.clear()
    st.session_state.uploaded_file_name = "cabinet.pdf"
    st.session_state.uploaded_file_bytes = b"pdf"
    st.session_state.file_review_run_metadata = {
        "project_name": "Hall",
        "partner": "unknown",
        "client": "unknown",
    }
    objects_input = [{"object_id": "object-1", "name": "Cabinet", "quantity": 1}]
    monkeypatch.setattr(file_review, "build_estimate_id", lambda _run_id: "estimate-new")
    monkeypatch.setattr(
        file_review,
        "save_file_review_run_metadata",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("callback must not persist")),
    )

    plan = file_review._prepare_objects_launch_plan(
        company_id="company-1",
        run_id="run-1",
        objects=objects_input,
    )

    assert plan is not None
    assert plan["estimate_id"] == "estimate-new"
    assert plan["screen_state"]["data"]["rows"][0]["object_key"] == "object-1"

    file_review._continue_to_objects_estimation(
        company_id="company-1",
        run_id="run-1",
    )

    assert st.session_state.screen == "objects"
    assert st.session_state.current_estimate_id == "estimate-new"
    assert st.session_state.objects_estimation_seed_rows[0]["object_key"] == "object-1"
    request = st.session_state.objects_estimation_launch_request
    assert request["estimate_id"] == "estimate-new"
    assert request["file_bytes"] == b"pdf"
    assert st.session_state.prepared_estimate_access == {
        "estimate_id": "estimate-new",
        "run_id": "run-1",
        "company_id": "company-1",
    }
    assert st.session_state.objects_navigation_ready["data"]["rows"][0]["object_key"] == "object-1"


def test_continue_callback_only_consumes_the_ready_bundle():
    source = Path("screens/file_review.py").read_text()
    callback_source = source.split("def _continue_to_objects_estimation", 1)[1].split(
        "def _mark_estimation_batch_started", 1
    )[0]

    assert "_prepare_objects_launch_plan(" not in callback_source
    assert "objects_estimation_launch_plan" in callback_source
    assert "objects_navigation_ready" in callback_source


def test_reopen_completed_estimate_prepares_objects_without_source_bytes(monkeypatch):
    st.session_state.clear()
    st.session_state.current_estimate_id = "estimate-old"
    st.session_state.current_estimate_run_id = "run-1"
    st.session_state.file_review_run_metadata = {
        "project_name": "Hall", "partner": "unknown", "client": "unknown",
    }
    st.session_state.file_review_object_edits = {
        "object-1": {
            "name": "Cabinet", "expected_name": "Cabinet", "quantity": "1", "ignored": False,
        }
    }
    prepared = []
    monkeypatch.setattr(
        objects,
        "prepare_objects_navigation_state",
        lambda **kwargs: prepared.append(kwargs) or {
            "data": {"rows": [{"object_key": "object-1"}], "project_costs": [], "summary": {}},
            "data_error": None,
            "cache_warning": None,
        },
    )

    plan = file_review._prepare_objects_launch_plan(
        company_id="company-1",
        run_id="run-1",
        objects=[{"object_id": "object-1", "name": "Cabinet", "quantity": 1}],
    )

    assert plan is not None
    assert plan["reuse_existing_estimate"] is True
    assert plan["file_bytes"] is None
    assert prepared == [{
        "company_id": "company-1",
        "run_id": "run-1",
        "estimate_id": "estimate-old",
    }]


def test_reopen_active_estimate_resumes_its_worker_without_a_new_launch(monkeypatch):
    """Back/Continue must not turn one active estimate into a second job."""
    st.session_state.clear()
    active_worker = Future()
    st.session_state.current_estimate_id = "estimate-live"
    st.session_state.current_estimate_run_id = "run-1"
    st.session_state.estimation_batch_future = active_worker
    st.session_state.prepared_estimate_access = {
        "estimate_id": "estimate-live", "run_id": "run-1", "company_id": "company-1",
    }
    st.session_state.objects_estimation_seed_rows = [{
        "object_key": "object-1", "name": "Cabinet", "quantity": 1, "status": "running",
    }]
    st.session_state.file_review_object_edits = {
        "object-1": {
            "name": "Cabinet", "expected_name": "Cabinet", "quantity": "1", "ignored": False,
        }
    }
    prepared = []
    monkeypatch.setattr(
        file_review,
        "build_estimate_id",
        lambda _run_id: (_ for _ in ()).throw(AssertionError("must not create a second estimate")),
    )
    monkeypatch.setattr(
        objects,
        "prepare_objects_navigation_state",
        lambda **kwargs: prepared.append(kwargs) or {
            "data": {"rows": kwargs.get("seed_rows") or [], "project_costs": [], "summary": {}},
            "data_error": None,
            "cache_warning": None,
        },
    )

    plan = file_review._prepare_objects_launch_plan(
        company_id="company-1",
        run_id="run-1",
        objects=[{"object_id": "object-1", "name": "Cabinet", "quantity": 1}],
    )

    assert plan is not None
    assert plan["reuse_existing_estimate"] is True
    assert plan["estimate_id"] == "estimate-live"
    assert plan["file_bytes"] is None
    assert prepared[0]["seed_rows"] == st.session_state.objects_estimation_seed_rows

    file_review._continue_to_objects_estimation(company_id="company-1", run_id="run-1")

    assert st.session_state.screen == "objects"
    assert st.session_state.current_estimate_id == "estimate-live"
    assert st.session_state.estimation_batch_future is active_worker
    assert st.session_state.objects_estimation_launch_request is None
    assert st.session_state.prepared_estimate_access == {
        "estimate_id": "estimate-live", "run_id": "run-1", "company_id": "company-1",
    }


def test_reopen_pending_estimate_keeps_its_undispatched_launch(monkeypatch):
    """The callback-to-first-render request belongs to the current estimate."""
    st.session_state.clear()
    request = {
        "company_id": "company-1", "run_id": "run-1", "estimate_id": "estimate-live",
        "file_name": "cabinet.pdf", "file_bytes": b"pdf",
    }
    st.session_state.current_estimate_id = "estimate-live"
    st.session_state.current_estimate_run_id = "run-1"
    st.session_state.objects_estimation_launch_request = request
    st.session_state.prepared_estimate_access = {
        "estimate_id": "estimate-live", "run_id": "run-1", "company_id": "company-1",
    }
    st.session_state.objects_estimation_seed_rows = [{
        "object_key": "object-1", "name": "Cabinet", "quantity": 1, "status": "pending",
    }]
    st.session_state.file_review_object_edits = {
        "object-1": {
            "name": "Cabinet", "expected_name": "Cabinet", "quantity": "1", "ignored": False,
        }
    }
    prepared = []
    monkeypatch.setattr(
        file_review,
        "build_estimate_id",
        lambda _run_id: (_ for _ in ()).throw(AssertionError("must retain pending launch")),
    )
    monkeypatch.setattr(
        objects,
        "prepare_objects_navigation_state",
        lambda **kwargs: prepared.append(kwargs) or {
            "data": {"rows": kwargs.get("seed_rows") or [], "project_costs": [], "summary": {}},
            "data_error": None,
            "cache_warning": None,
        },
    )

    plan = file_review._prepare_objects_launch_plan(
        company_id="company-1",
        run_id="run-1",
        objects=[{"object_id": "object-1", "name": "Cabinet", "quantity": 1}],
    )
    assert plan is not None
    assert plan["reuse_existing_estimate"] is True
    assert prepared[0]["seed_rows"] == st.session_state.objects_estimation_seed_rows

    file_review._continue_to_objects_estimation(company_id="company-1", run_id="run-1")

    assert st.session_state.objects_estimation_launch_request is request
    assert st.session_state.prepared_estimate_access == {
        "estimate_id": "estimate-live", "run_id": "run-1", "company_id": "company-1",
    }


def test_terminal_worker_failure_replaces_the_local_running_progress():
    st.session_state.clear()
    st.session_state.estimation_terminal_failures = {"estimate-1": "handoff failed"}

    rendered = objects._data_with_progress({
        "rows": [{"object_key": "object-1", "status": "running", "progress_percent": 1}],
        "project_costs": [],
        "summary": {},
    }, "estimate-1")

    assert rendered["rows"] == [{
        "object_key": "object-1", "status": "failed", "progress_percent": 100,
        "progress_label": "estimation_handoff_failed", "self_cost_unit": None,
    }]


def test_objects_back_navigation_uses_the_cached_file_review_snapshot():
    st.session_state.clear()
    st.session_state.current_run_id = "run-1"
    review_data = {"run": {"run_id": "run-1"}, "objects": []}
    st.session_state.file_review_data_cache = {"run-1": review_data}

    objects._back_to_file_review_with_ready_cache("company-1")
    restored = file_review._consume_prepared_file_review_navigation(
        company_id="company-1", run_id="run-1",
    )

    assert st.session_state.screen == "file_review"
    assert restored is review_data


def test_restored_file_review_source_is_used_for_a_prepared_launch(monkeypatch):
    st.session_state.clear()
    st.session_state.file_review_run_metadata = {
        "project_name": "Hall", "partner": "unknown", "client": "unknown",
    }
    st.session_state.file_review_data_cache = {
        "run-1": {"run": {"file_name": "cabinet.pdf"}},
    }
    st.session_state["file_review_source_bytes.run-1"] = b"restored-pdf"
    plan = file_review._prepare_objects_launch_plan(
        company_id="company-1",
        run_id="run-1",
        objects=[{"object_id": "object-1", "name": "Cabinet", "quantity": 1}],
        source={"storage_ref": "storage://rfq-estimation-originals/company-1/a.pdf"},
    )

    assert plan is not None
    assert plan["file_name"] == "cabinet.pdf"
    assert plan["file_bytes"] == b"restored-pdf"


def test_objects_dispatches_prepared_launch_without_waiting_for_result(monkeypatch):
    st.session_state.clear()
    submitted = []
    future = Future()
    st.session_state.objects_estimation_launch_request = {
        "estimate_id": "estimate-new",
        "run_id": "run-1",
        "company_id": "company-1",
        "file_name": "cabinet.pdf",
        "file_bytes": b"pdf",
        "object_edits": {"object-1": {"name": "Cabinet"}},
        "metadata_values": {"project_name": "Hall"},
        "ignored_object_ids": {"object-2"},
        "edits_changed": True,
        "create_shell": True,
    }
    monkeypatch.setattr(
        objects,
        "submit_prepared_estimation_job",
        lambda **kwargs: submitted.append(kwargs) or future,
    )

    objects._start_prepared_estimation_launch()

    assert st.session_state.estimation_batch_future is future
    assert st.session_state.objects_estimation_launch_request is None
    assert submitted == [{
        "estimate_id": "estimate-new",
        "run_id": "run-1",
        "company_id": "company-1",
        "file_name": "cabinet.pdf",
        "file_bytes": b"pdf",
        "object_edits": {"object-1": {"name": "Cabinet"}},
        "metadata_values": {"project_name": "Hall"},
        "edits_changed": True,
        "ignored_object_ids": {"object-2"},
        "create_shell": True,
    }]


def test_workflow_screens_do_not_install_react_mutating_transition_shells():
    assert "install_post_upload_transition_guard" not in Path("screens/file_review.py").read_text()
    assert "install_post_upload_transition_guard" not in Path("screens/objects.py").read_text()


def test_app_retires_a_legacy_snapshot_transition_runtime_before_rendering():
    source = Path("app.py").read_text()
    guard_source = Path("ui/js_guards.py").read_text()

    assert "retire_legacy_post_upload_transition_guard()" in source
    assert 'removeEventListener("click", handler, true)' in guard_source
    assert '"costerly-post-upload-transition-shell"' in guard_source


def test_file_review_restores_blank_teardown_values_from_its_review_snapshot():
    st.session_state.clear()
    run_id = "run-1"
    st.session_state.file_review_run_metadata_run_id = run_id
    st.session_state.file_review_run_metadata = {
        "project_name": "",
        "partner": "Studio Oak",
        "client": "",
    }
    st.session_state.file_review_object_edits_run_id = run_id
    st.session_state.file_review_object_edits = {
        "object-1": {"name": "", "expected_name": "Cabinet", "quantity": ""},
    }

    file_review._sync_run_metadata_state(
        run_id,
        {"project_name": "Hall", "partner": "Studio Oak", "client": "Client One"},
    )
    file_review._sync_object_edit_state(
        run_id,
        [{"object_id": "object-1", "name": "Cabinet", "quantity": 1}],
    )

    assert st.session_state.file_review_run_metadata == {
        "project_name": "Hall",
        "partner": "Studio Oak",
        "client": "Client One",
    }
    assert st.session_state.file_review_object_edits["object-1"] == {
        "name": "Cabinet", "expected_name": "Cabinet", "quantity": "1",
    }


def test_retired_dom_mutating_objects_progress_runtime_is_not_shipped():
    source = Path("ui/js_guards.py").read_text()

    assert "def install_objects_progress_sync" not in source
    assert "def install_post_upload_transition_guard" not in source


def test_objects_screen_does_not_install_the_react_mutating_live_progress_runtime():
    source = Path("screens/objects.py").read_text()

    assert "install_objects_progress_sync" not in source
    assert "latest persisted progress snapshot" in source


def test_objects_screen_refreshes_active_estimation_in_a_server_fragment():
    source = Path("screens/objects.py").read_text()

    assert "@st.fragment(run_every=1.5)" in source
    assert "def _render_live_objects_content" in source
    assert "_persisted_objects_state(estimate_id)" in source
    assert 'st.container(key="objects_live_pricing")' in source
    assert 'st.session_state.pop("objects_live_poll_estimate_id", None)' in source

    fragment_source = source.split("def _render_live_objects_content", 1)[1].split(
        "def render_objects_screen", 1
    )[0]
    assert "_render_objects_table_content" in fragment_source
    assert "st.rerun()" not in fragment_source
    assert "_render_objects_actions" not in fragment_source
    assert "_install_objects_price_input_runtime" not in fragment_source


def test_objects_live_fragment_does_not_dim_stale_table_content():
    source = Path("styles/objects.py").read_text()

    assert '.st-key-objects_live_pricing[data-stale="true"]' in source
    assert '.st-key-objects_live_pricing [data-testid="stElementContainer"][data-stale="true"]' in source
    assert "opacity: 1 !important" in source
    assert "transition: none !important" in source


def test_file_review_ignores_an_empty_transient_name_commit(monkeypatch):
    st.session_state.clear()
    widget_key = "file_review_object_edits.object-1.name"
    st.session_state.file_review_object_edits = {"object-1": {"name": "Curtain track system"}}
    st.session_state[widget_key] = ""
    saved = []
    monkeypatch.setattr(
        file_review,
        "save_file_review_object_name",
        lambda **kwargs: saved.append(kwargs),
    )

    file_review._commit_object_name("run-1", "object-1", widget_key)

    assert saved == []
    assert st.session_state[widget_key] == "Curtain track system"
    assert st.session_state.file_review_object_edits["object-1"]["name"] == "Curtain track system"


def test_file_review_metadata_commit_updates_cache_and_preserves_empty_transient_value(monkeypatch):
    st.session_state.clear()
    run_id = "run-1"
    widget_key = "file_review_run_metadata.partner"
    st.session_state.file_review_run_metadata = {"partner": "Bureau Yolochka"}
    st.session_state.file_review_data_cache = {
        run_id: {"run": {"partner": "Bureau Yolochka"}}
    }
    st.session_state[widget_key] = "  Studio Oak  "
    saved = []
    monkeypatch.setattr(
        file_review,
        "save_file_review_run_metadata",
        lambda **kwargs: saved.append(kwargs) or {"partner": "Studio Oak"},
    )

    file_review._commit_run_metadata(run_id, "partner", widget_key)

    assert saved == [{"run_id": run_id, "values": {"partner": "Studio Oak"}}]
    assert st.session_state.file_review_run_metadata["partner"] == "Studio Oak"
    assert st.session_state.file_review_data_cache[run_id]["run"]["partner"] == "Studio Oak"

    st.session_state[widget_key] = ""
    file_review._commit_run_metadata(run_id, "partner", widget_key)
    assert len(saved) == 1
    assert st.session_state[widget_key] == "Studio Oak"


def test_file_review_renders_all_three_editable_project_fields():
    source = Path("screens/file_review.py").read_text()

    assert '"project_name": "Project name"' in source
    assert '"partner": "Partner"' in source
    assert '"client": "Client"' in source
    assert "save_file_review_run_metadata" in source
    assert "objects_navigation_ready" in source
    assert "objects_estimation_launch_plan" in source


def test_file_review_metadata_state_does_not_leak_between_runs():
    st.session_state.clear()
    st.session_state.file_review_run_metadata_run_id = "run-old"
    st.session_state["file_review_run_metadata.project_name"] = "Old project"
    st.session_state["file_review_run_metadata.partner"] = "Old partner"
    st.session_state["file_review_run_metadata.client"] = "Old client"

    file_review._sync_run_metadata_state(
        "run-new",
        {
            "project_name": "New project",
            "partner": "New partner",
            "client": "New client",
        },
    )

    assert st.session_state.file_review_run_metadata == {
        "project_name": "New project",
        "partner": "New partner",
        "client": "New client",
    }
    assert "file_review_run_metadata.project_name" not in st.session_state


def test_file_review_publishes_persisted_naming_once_without_reloading_review():
    st.session_state.clear()
    run_id = "run-1"
    object_id = "object-1"
    widget_key = f"file_review_object_edits.{object_id}.name"
    objects = [{"object_id": object_id, "name": "Object 1"}]
    st.session_state.file_review_data_cache = {run_id: {"objects": objects}}
    st.session_state.current_agent_timings = {}
    file_review._sync_object_edit_state(run_id, objects)
    st.session_state.file_review_object_edits[object_id] = {"name": "Object 1"}
    st.session_state[widget_key] = "Object 1"

    assert file_review._publish_persisted_naming(
        run_id,
        {"status": "succeeded", "names": {object_id: "Shelving unit"}, "naming_seconds": 1.2},
    ) is True
    assert objects[0]["name"] == "Shelving unit"
    assert st.session_state.file_review_object_edits[object_id]["name"] == "Shelving unit"
    assert st.session_state[widget_key] == "Shelving unit"
    assert st.session_state[f"file_review_deferred_name_echoes.{run_id}"] == {
        object_id: {"stale_name": "Object 1", "published_name": "Shelving unit"},
    }
    assert st.session_state.current_agent_timings["naming_seconds"] == 1.2
    assert "TC1 unavailable" in file_review._timing_html({"total_seconds": 1.2})
    assert "TC1 0.024" in file_review._timing_html({"total_seconds": 1.2, "token_cost": 0.024166})
    forecast_markup = file_review._timing_html({
        "total_seconds": 307.6,
        "forecast_seconds": 295,
        "token_cost": 0.1,
    })
    assert "308s (F: 295s)" in forecast_markup
    assert 'data-costerly-forecast-seconds="295"' in forecast_markup
    assert file_review._publish_persisted_naming(
        run_id,
        {"status": "succeeded", "names": {object_id: "Different name"}},
    ) is False


def test_file_review_ignores_one_stale_browser_name_echo_after_deferred_naming(monkeypatch):
    st.session_state.clear()
    run_id = "run-1"
    object_id = "object-3"
    widget_key = f"file_review_object_edits.{object_id}.name"
    objects = [{"object_id": object_id, "name": "Object 3"}]
    st.session_state.file_review_data_cache = {run_id: {"objects": objects}}
    file_review._sync_object_edit_state(run_id, objects)
    st.session_state.file_review_object_edits[object_id] = {
        "name": "Object 3",
        "expected_name": "Object 3",
    }
    st.session_state[widget_key] = "Object 3"
    file_review._publish_persisted_naming(
        run_id,
        {"status": "succeeded", "names": {object_id: "TV console"}},
    )
    saved = []
    monkeypatch.setattr(
        file_review,
        "save_file_review_object_name",
        lambda **kwargs: saved.append(kwargs),
    )

    # This is the delayed browser acknowledgement of the previously rendered
    # placeholder. It must not become a real write.
    st.session_state[widget_key] = "Object 3"
    file_review._commit_object_name(run_id, object_id, widget_key)

    assert saved == []
    assert st.session_state[widget_key] == "TV console"
    assert st.session_state.file_review_object_edits[object_id] == {
        "name": "TV console",
        "expected_name": "TV console",
    }
    assert f"file_review_deferred_name_echoes.{run_id}" not in st.session_state


def test_file_review_persisted_naming_does_not_overwrite_a_manual_name():
    st.session_state.clear()
    run_id = "run-1"
    object_id = "object-1"
    widget_key = f"file_review_object_edits.{object_id}.name"
    objects = [{"object_id": object_id, "name": "Object 1"}]
    st.session_state.file_review_data_cache = {run_id: {"objects": objects}}
    file_review._sync_object_edit_state(run_id, objects)
    st.session_state.file_review_object_edits[object_id] = {"name": "Custom shelf"}
    st.session_state[widget_key] = "Custom shelf"

    file_review._publish_persisted_naming(
        run_id,
        {"status": "succeeded", "names": {object_id: "Shelving unit"}},
    )

    assert objects[0]["name"] == "Shelving unit"
    assert st.session_state.file_review_object_edits[object_id]["name"] == "Custom shelf"
    assert st.session_state[widget_key] == "Custom shelf"


def test_file_review_syncs_durable_name_once_into_a_stale_session_cache(monkeypatch):
    st.session_state.clear()
    run_id = "run-1"
    object_id = "object-3"
    widget_key = f"file_review_object_edits.{object_id}.name"
    objects = [{"object_id": object_id, "name": "Object 3"}]
    st.session_state.file_review_data_cache = {run_id: {"objects": objects}}
    st.session_state.current_agent_timings = {}
    file_review._sync_object_edit_state(run_id, objects)
    st.session_state.file_review_object_edits[object_id] = {"name": "Object 3"}
    st.session_state[widget_key] = "Object 3"
    st.session_state[f"file_review_naming_published.{run_id}"] = True
    calls = []
    monkeypatch.setattr(
        file_review,
        "load_file_review_naming_publication",
        lambda _run_id: calls.append(_run_id) or {
            "status": "succeeded", "names": {object_id: "TV console"},
        },
    )

    file_review._sync_durable_naming_once(run_id)
    file_review._sync_durable_naming_once(run_id)

    assert calls == [run_id]
    assert objects[0]["name"] == "TV console"
    assert st.session_state.file_review_object_edits[object_id]["name"] == "TV console"
    assert st.session_state[widget_key] == "TV console"


def test_deferred_naming_publication_reads_only_the_terminal_name_snapshot(monkeypatch):
    monkeypatch.setattr(rfq_processing, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        rfq_processing,
        "fetch_deferred_naming_status",
        lambda _client, _run_id: {
            "status": "succeeded",
            "raw_usage": {"duration_seconds": 1.7},
        },
    )
    monkeypatch.setattr(
        rfq_processing,
        "fetch_rfq_detected_object_names",
        lambda _client, _run_id: [
            {"object_id": "object-1", "object_name": "Shelving unit"},
        ],
    )

    assert rfq_processing.load_file_review_naming_publication("run-1") == {
        "status": "succeeded",
        "names": {"object-1": "Shelving unit"},
        "naming_seconds": 1.7,
        "token_cost": None,
    }


def test_deferred_preview_publication_reads_only_the_terminal_preview_status(monkeypatch):
    monkeypatch.setattr(rfq_processing, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        rfq_processing,
        "fetch_deferred_preview_status",
        lambda _client, _run_id: {
            "status": "succeeded",
            "raw_usage": {"duration_seconds": 1.7},
        },
    )

    assert rfq_processing.load_file_review_preview_publication("run-1") == {
        "status": "succeeded",
        "preview_seconds": 1.7,
    }


def test_file_review_preview_publication_reloads_only_after_terminal_success(monkeypatch):
    st.session_state.clear()
    run_id = "run-1"
    st.session_state.file_review_data_cache = {run_id: {"objects": [{"preview_pending": True}]}}
    st.session_state.file_review_deferred_work = {
        "run_id": run_id,
        "naming": False,
        "preview": True,
    }

    assert file_review._publish_persisted_preview(
        run_id,
        {"status": "succeeded", "preview_seconds": 1.7},
    ) is True
    assert run_id not in st.session_state.file_review_data_cache
    assert file_review._has_deferred_work(run_id) is False

    stored = {"run": {}, "objects": [{"object_id": "object-1", "preview_ref": "previews/1.png"}]}
    monkeypatch.setattr(file_review, "load_file_review_data", lambda _run_id: stored)

    assert file_review._load_file_review_screen_data(run_id) is stored
    assert st.session_state.file_review_data_cache[run_id]["objects"][0]["preview_ref"] == "previews/1.png"


def test_file_review_preview_failure_reloads_saved_refs_then_stops_spinner():
    st.session_state.clear()
    run_id = "run-1"
    st.session_state.file_review_data_cache = {run_id: {"objects": [{"preview_pending": True}]}}
    st.session_state.file_review_deferred_work = {
        "run_id": run_id,
        "naming": False,
        "preview": True,
    }

    assert file_review._publish_persisted_preview(run_id, {"status": "partial"}) is True
    assert run_id not in st.session_state.file_review_data_cache
    assert st.session_state[f"file_review_preview_terminal.{run_id}"] == "partial"


def test_file_review_refreshes_only_object_cards_for_deferred_artifacts():
    source = (Path(__file__).parents[1] / "screens/file_review.py").read_text()

    dynamic = source.index("def _render_file_review_dynamic_content")
    navigation = source.index('"CONTINUE TO OBJECTS ESTIMATION"')

    poll = source.index("def _poll_file_review_deferred_work")
    rerun = source.index('st.rerun(scope="app")', poll)
    assert "@st.fragment(run_every=2.0)" in source[dynamic:poll]
    assert poll < rerun
    assert dynamic < navigation
    assert source.index("_publish_deferred_file_review_work(run_id)", dynamic) < source.index(
        "_render_object_card(item)", dynamic
    )


def test_file_review_back_to_upload_remembers_the_current_review_run():
    st.session_state.clear()
    st.session_state.current_run_id = "run-current"

    file_review._back_to_upload_from_review()

    assert st.session_state.return_file_review_run_id == "run-current"
    assert st.session_state.screen == "upload"


def test_return_route_is_not_overwritten_by_the_historic_estimate_lookup():
    source = Path("app.py").read_text()

    assert source.count(
        "latest_route is None and latest_route_cache_key not in st.session_state"
    ) == 2


def test_file_review_back_to_upload_is_never_disabled_after_an_input_event():
    source = Path("screens/file_review.py").read_text()

    assert '"BACK TO UPLOAD",\n            type="secondary",\n            use_container_width=True,\n            disabled=True' not in source


def test_projects_uses_existing_styled_transition_contract():
    source = Path("ui/js_guards.py").read_text()

    assert 'currentScreen() === "projects") return "projects_to_upload"' in source
    assert 'return "upload_to_projects"' in source
    assert 'projects_to_upload: "upload"' in source
    assert 'upload_to_projects: "projects"' in source
    assert 'return ".projects-screen-active"' in source
    assert 'parentDocument.querySelector(".projects-empty, .projects-table-card")' in source


def test_projects_workspace_loads_three_collections_concurrently():
    source = Path("use_cases/projects.py").read_text()

    assert "ThreadPoolExecutor(max_workers=3)" in source
    assert source.count("executor.submit(") == 3


def test_projects_is_one_page_with_native_partner_disclosure_rows():
    source = Path("screens/projects.py").read_text()

    assert '<details class="projects-partner">' in source
    assert "<div>Project</div><div>Client</div><div>Calculation</div><div>Total</div><div>PDF</div>" in source
    assert "st.button(" not in source
    assert "set_screen(" not in source
    assert '>Partners</h1>' in source
    assert 'version.get("proposal_pdf_url")' in source


def test_objects_initializes_action_state_before_live_fragment_branch():
    source = inspect.getsource(objects.render_objects_screen)
    state_index = source.index("screen_state = _current_objects_state(estimate_id)")
    live_index = source.index("_render_live_objects_content(")

    assert state_index < live_index


def test_file_review_transitions_follow_the_current_editable_summary_marker():
    source = Path("ui/js_guards.py").read_text()

    assert 'return ".file-review-summary-card-marker"' in source
    assert 'parentDocument.querySelector(\n                            ".file-review-summary-card-marker"' in source
    assert 'cardStyle.borderTopLeftRadius === "16px"' in source

    handoff_start = source.index("function reportFileReviewStyled")
    handoff_end = source.index("function startWatcher", handoff_start)
    handoff_source = source[handoff_start:handoff_end]
    assert "const fileReviewReady" in handoff_source
    assert "document.querySelectorAll('.file-review-summary-card-marker')" in handoff_source
    assert "marker.dataset.fileReviewRunId === expectedRunId" in handoff_source
    assert "document.querySelector('.file-review-card')" not in handoff_source
    assert "window.requestAnimationFrame(() => {" in handoff_source
    assert "window.requestAnimationFrame(removeShell);" in handoff_source
    assert "function beginFileReviewTransition(stage)" in source
    assert "beginFileReviewTransition(activeProcessingStage());" in source
    assert "if (fileReviewIsActive()) {\n                        removeShell();" not in source
