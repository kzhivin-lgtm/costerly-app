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
    assert "R1 <strong>—" in html
    assert "R2 <strong>—" in html
    assert 'href="?screen=object_detail' not in html

    tick[0] = 107.25
    a["status"] = "review_required"
    app.session_state["test_rows"] = [a, b]
    html = render()
    assert "R1 <strong>7.2s" in html
    assert "R2 <strong>—" in html
    assert html.count('href="?screen=object_detail') == 1

    tick[0] = 115.5
    b["status"] = "completed"
    app.session_state["test_rows"] = [a, b]
    future.set_result({"estimate_id": "estimate", "estimation": {"status": "completed"}, "cost_usd": 0.2119})
    html = render()
    assert "Total lap <strong>15.5s" in html and "TC <strong>0.21</strong>" in html
    assert "R1 <strong>7.2s" in html
    assert "R2 <strong>15.5s" in html
    assert html.count('href="?screen=object_detail') == 2

    tick[0] = 200.0
    assert render() == html

    # A ready receipt must not survive a later active row in the real view.
    tick[0] = 205.0
    a['status'] = 'running'
    app.session_state['test_rows'] = [a, b]
    html = render()
    assert 'Total lap <strong>105.0s' in html
    assert 'R1 <strong>—' in html and 'R2 <strong>15.5s' in html
    tick[0] = 210.0
    a['status'] = 'completed'
    app.session_state['test_rows'] = [a, b]
    html = render()
    assert 'Total lap <strong>110.0s' in html and 'R1 <strong>110.0s' in html


def test_missing_usage_and_failed_object_are_not_reported_as_zero_or_ready():
    html = cycle_metrics_html(
        [{"object_key": "a", "name": "Base", "status": "failed"},
         {"object_key": "delivery", "name": "Delivery", "status": "completed"}],
        elapsed=4, ready_seconds={}, cost_usd=None, running=False,
    )
    assert "TC <strong>—" in html
    assert "R1 <strong>Failed" in html
    assert "Delivery" not in html


def test_cycle_reopens_timing_when_a_later_render_resumes_work():
    from use_cases.estimation_progress import EstimationCycle
    cycle = EstimationCycle(started_at=100, worker_finished=True)
    assert cycle.observe(110, ready_ids=['a'], all_terminal=True) == 10
    assert cycle.observe(120, ready_ids=[], all_terminal=False) == 20
    assert cycle.total_seconds is None and cycle.ready_seconds == {}
    assert cycle.observe(135, ready_ids=['a'], all_terminal=True) == 35
    assert cycle.ready_seconds == {'a': 35}
    assert cycle.observe(200, ready_ids=['a'], all_terminal=True) == 35


def test_active_row_cannot_display_a_remembered_ready_time_and_labels_are_unbounded():
    rows = [{'object_key': f'{i:02}', 'name': f'Long object name {i}', 'status': 'completed'} for i in range(1, 13)]
    rows[0]['status'] = 'running'
    html = cycle_metrics_html(rows, elapsed=20, ready_seconds={'01': 10, '12': 19}, cost_usd=.2, running=True)
    assert 'R1 <strong>—</strong>' in html
    assert 'R12 <strong>19.0s</strong>' in html
    assert 'Long object name' not in html
