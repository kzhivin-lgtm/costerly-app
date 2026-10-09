from state import session


def test_deploy_reset_preserves_the_first_safe_header_navigation(monkeypatch):
    session.st.session_state.clear()
    session.st.session_state._app_boot_id = "previous-process"
    # This mirrors a header callback that ran just before a deployed process
    # entered init_state(). The remaining workflow state is deliberately stale.
    session.st.session_state.screen = "admin"
    session.st.session_state.current_run_id = "stale-run"

    monkeypatch.setattr(session, "_APP_BOOT_ID", "deployed-process")

    session.init_state()

    assert session.st.session_state.screen == "admin"
    assert session.st.session_state.current_run_id is None


def test_deploy_reset_does_not_restore_a_stale_workflow_route(monkeypatch):
    session.st.session_state.clear()
    session.st.session_state._app_boot_id = "previous-process"
    session.st.session_state.screen = "object_detail"

    monkeypatch.setattr(session, "_APP_BOOT_ID", "deployed-process")

    session.init_state()

    assert session.st.session_state.screen == "upload"
