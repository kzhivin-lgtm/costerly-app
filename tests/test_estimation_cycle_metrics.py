from concurrent.futures import Future

from streamlit.testing.v1 import AppTest

from screens import objects
from ui.objects_pricing import cycle_metrics_html


def _mount_objects_table():
    import streamlit as st
    from screens import objects

    st.session_state.current_estimate_id = "estimate"
    objects._start_prepared_estimation_launch()
    objects._consume_estimation_future()
    objects._render_objects_table_content(
        estimate_id="estimate",
        run_id="run",
        screen_state=objects.ObjectsScreenState(
            objects.prepared_objects_data_from_seed_rows(st.session_state.test_rows)
        ),
    )


def test_cycle_reports_first_active_review_per_object_and_total_cost(monkeypatch):
    tick = [101.0]
    future = Future()
    monkeypatch.setattr(objects, "perf_counter", lambda: tick[0])
    monkeypatch.setattr(objects, "submit_prepared_estimation_job", lambda **_: future)
    app = AppTest.from_function(_mount_objects_table)
    app.session_state.objects_estimation_launch_request = {
        "estimate_id": "estimate", "run_id": "run", "company_id": "company",
        "file_name": "drawing.pdf", "file_bytes": b"pdf", "cycle_started_at": 100.0,
    }
    a = {"object_key": "a", "name": "Base & drawers", "status": "running", "quantity": 1}
    b = {"object_key": "b", "name": "Tall cabinet", "status": "pending", "quantity": 1}
    app.session_state["test_rows"] = [b, a]

    def render():
        app.run()
        assert not app.exception
        return next(item.value for item in app.markdown if 'aria-label="Estimation cycle"' in item.value)

    html = render()
    assert "Total lap <strong>1.0s" in html and "TC <strong>Pending" in html
    assert "R1 · Base &amp; drawers <strong>—" in html
    assert "R2 · Tall cabinet <strong>—" in html
    assert 'href="?screen=object_detail' not in html

    tick[0] = 107.25
    a["status"] = "review_required"
    app.session_state["test_rows"] = [a, b]
    html = render()
    assert "R1 · Base &amp; drawers <strong>7.2s" in html
    assert "R2 · Tall cabinet <strong>—" in html
    assert html.count('href="?screen=object_detail') == 1

    tick[0] = 115.5
    b["status"] = "completed"
    app.session_state["test_rows"] = [a, b]
    future.set_result({"estimate_id": "estimate", "estimation": {"status": "completed"}, "cost_usd": 0.2119})
    html = render()
    assert "Total lap <strong>15.5s" in html and "TC <strong>0.21</strong>" in html
    assert "R1 · Base &amp; drawers <strong>7.2s" in html
    assert "R2 · Tall cabinet <strong>15.5s" in html
    assert html.count('href="?screen=object_detail') == 2

    tick[0] = 200.0
    assert render() == html


def test_missing_usage_and_failed_object_are_not_reported_as_zero_or_ready():
    html = cycle_metrics_html(
        [{"object_key": "a", "name": "Base", "status": "failed"},
         {"object_key": "delivery", "name": "Delivery", "status": "completed"}],
        elapsed=4, ready_seconds={}, cost_usd=None, running=False,
    )
    assert "TC <strong>—" in html
    assert "R1 · Base <strong>Failed" in html
    assert "Delivery" not in html
