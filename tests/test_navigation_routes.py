from __future__ import annotations

import ast
from concurrent.futures import Future
from pathlib import Path

import streamlit as st

import app
from screens import file_review, objects


def test_profile_route_preserves_selected_tab():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Contacts"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "contacts",
    }


def test_profile_route_preserves_machinery_tab_in_app_and_wrapper():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Machinery"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "machinery",
    }
    wrapper = (Path(__file__).parents[1] / "cloudflare" / "index.html").read_text()
    assert '"machinery"' in wrapper


def test_profile_route_uses_bank_details_slug_and_accepts_legacy_slug():
    st.session_state.clear()
    st.session_state.company_profile_tab = "Bank Details"

    assert app._browser_route("account") == {
        "screen": "account",
        "profile_tab": "bank-details",
    }
    assert app._PROFILE_TAB_ROUTES["company-details"] == "Bank Details"
    wrapper = (Path(__file__).parents[1] / "cloudflare" / "index.html").read_text()
    assert '"bank-details"' in wrapper
    assert '"company-details"' in wrapper


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
    assert 'st.session_state.screen = "objects"' in detail_source
    assert 'data-streamlit-bridge-key="{navigation_key}"' in pricing_source
    assert 'data-streamlit-bridge-key="object_detail_back_bridge"' in detail_view_source


def test_processing_refresh_fails_safe_to_upload():
    st.session_state.clear()

    assert app._browser_route("processing") == {"screen": "upload"}


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
    assert "on_click=set_screen" in source
    assert "st.rerun()" not in continue_source


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


def test_workflow_screens_do_not_install_react_mutating_transition_shells():
    assert "install_post_upload_transition_guard" not in Path("screens/file_review.py").read_text()
    assert "install_post_upload_transition_guard" not in Path("screens/objects.py").read_text()


def test_objects_runtime_stops_dom_writers_before_workflow_navigation():
    source = Path("ui/js_guards.py").read_text()

    assert 'const NAVIGATION_CLEANUP_KEY = "__costerlyObjectsNavigationCleanup"' in source
    assert 'parentDoc.addEventListener("pointerdown", stopForWorkflowNavigation, true)' in source
    assert 'parentWindow[PRICE_INPUT_CLEANUP_KEY]();' in source
    assert 'observer.observe(parentDoc.documentElement, { childList: true, subtree: true })' in source


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
    assert "continue_metadata_save_ms" in source


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


def test_file_review_collects_completed_naming_without_a_timed_fragment():
    st.session_state.clear()
    future = Future()
    future.set_result({"status": "succeeded", "names": {}})
    st.session_state.current_naming_future = future

    assert file_review._collect_completed_naming() is True
    assert st.session_state.current_naming_future is None
    assert st.session_state.current_naming_result == {"status": "succeeded", "names": {}}
    assert "@st.fragment(run_every=0.5)" not in Path("screens/file_review.py").read_text()


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
    source = Path("screens/objects.py").read_text()
    state_index = source.index("screen_state = _current_objects_state(estimate_id)")
    live_index = source.index(
        'if estimate_id and isinstance(st.session_state.get("estimation_batch_future"), Future):'
    )

    assert state_index < live_index


def test_file_review_transitions_follow_the_current_editable_summary_marker():
    source = Path("ui/js_guards.py").read_text()

    assert 'return ".file-review-summary-card-marker"' in source
    assert 'parentDocument.querySelector(\n                            ".file-review-summary-card-marker"' in source
    assert 'cardStyle.borderTopLeftRadius === "16px"' in source
