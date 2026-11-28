from datetime import UTC, datetime, timedelta

from ui.objects_pricing import smooth_progress_percent
from use_cases import estimation_progress as progress
import pytest


def test_unconfirmed_geometry_progress_cannot_visually_reach_bom_checkpoint():
    row = {
        "progress_percent": 1,
        "progress_updated_at": (datetime.now(UTC) - timedelta(minutes=10)).isoformat(),
    }

    assert smooth_progress_percent(row) == 4


@pytest.mark.parametrize("base,next_mark", [(1, 5), (5, 8), (8, 40), (40, 50), (50, 65),
                                         (65, 66), (66, 67), (67, 74), (74, 82), (82, 88), (88, 90), (90, 94),
                                         (94, 96), (96, 98), (98, 99), (99, 100)])
def test_interpolation_stays_below_next_real_completed_stage(base, next_mark):
    row = {"progress_percent": base,
           "progress_updated_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat()}
    assert smooth_progress_percent(row) == next_mark - 1
    # The next real receipt never moves the displayed number backwards.
    assert smooth_progress_percent({"progress_percent": next_mark}) >= next_mark - 1


@pytest.mark.parametrize("timestamp", [None, "invalid", datetime.now(UTC).isoformat()])
def test_running_state_never_presents_premature_100(timestamp):
    assert smooth_progress_percent({"progress_percent": 100, "progress_updated_at": timestamp}) == 99


def test_batch_progress_is_monotonic_and_rejects_duplicate_stale_and_terminal_receipts():
    estimate = "progress-batch-test"
    try:
        token = progress.begin_estimate_progress(estimate, ["a", "b"])
        progress.set_estimate_stage(estimate, token, "inventory_ready")
        before = progress.get_estimate_progress(estimate)
        progress.set_estimate_stage(estimate, token, "understanding_ready")
        progress.set_estimate_stage(estimate, token, "inventory_ready")
        assert progress.get_estimate_progress(estimate) == before  # timestamp must not restart smoothing
        assert {row["percent"] for row in before["objects"].values()} == {65}
        progress.set_object_progress(estimate_id=estimate, object_id="a", percent=100, status="failed")
        progress.set_estimate_stage(estimate, token, "plan_published")
        rows = progress.get_estimate_progress(estimate)["objects"]
        assert rows["a"]["status"] == "failed" and rows["b"]["percent"] == 99
        replacement = progress.begin_estimate_progress(estimate, ["a"])
        progress.set_estimate_stage(estimate, token, "plan_published")
        assert progress.get_estimate_progress(estimate)["objects"]["a"]["percent"] == 5
        progress.clear_estimate_progress(estimate)
        progress.set_estimate_stage(estimate, replacement, "plan_published")
        assert progress.get_estimate_progress(estimate) is None
    finally:
        progress.clear_estimate_progress(estimate)


def test_batch_overlay_waits_for_final_worker_result_and_retains_completed_reopen(monkeypatch):
    from concurrent.futures import Future
    from screens import objects

    estimate = "progress-ui-test"
    state = {"estimation_batch_future": Future(), "objects_estimation_future_id": estimate}
    monkeypatch.setattr(objects.st, "session_state", state)
    data = {"rows": [{"object_key": oid, "status": "completed", "self_cost_unit": 100,
                       "sale_price_total": 200} for oid in ["a", "b"]], "summary": {}}
    try:
        token = progress.begin_estimate_progress(estimate, ["a", "b"])
        progress.set_estimate_stage(estimate, token, "allocations_published")
        rendered = objects._data_with_progress(data, estimate)
        assert [row["status"] for row in rendered["rows"]] == ["running", "running"]
        assert all(row["progress_percent"] == 98 for row in rendered["rows"])
        assert rendered["summary"]["project_pricing_ready"] is False
        state["estimation_batch_future"] = None
        # Another tab is also held while the final plan save is still in flight.
        assert objects._data_with_progress(data, estimate)["rows"][0]["status"] == "running"
        progress.finish_estimate_progress(estimate, token)
        # A stale in-process record cannot replace already usable saved results.
        assert [row["status"] for row in objects._data_with_progress(data, estimate)["rows"]] == [
            "completed", "completed"]
    finally:
        progress.clear_estimate_progress(estimate)


def test_progress_callback_failure_is_isolated_from_calculation(caplog):
    def broken(_):
        raise RuntimeError("display unavailable")
    progress.report_estimation_stage(broken, "geometry_ready")
    assert "Could not report estimation stage geometry_ready" in caplog.text


def test_real_checkpoint_catches_up_without_an_instant_jump_or_backwards_step():
    # The user's50-to60 jump is covered by a new confirmed boundary from a
    # lower visible value. At each existing1.5s refresh it catches up gradually.
    values = [progress.progress_display_value(50, tick * 1.5, 40) for tick in range(10)]
    assert values[:4] == [40, 43, 46, 49]
    assert values == sorted(values) and values[-1] < 65


@pytest.mark.parametrize("base", [67, 74, 82])
def test_twenty_second_material_phase_keeps_moving_before_its_cap(base):
    values = [progress.progress_display_value(base, tick * 1.5) for tick in range(14)]
    assert len(set(values)) >= 5
    assert values == sorted(values)
    cap, _ = progress.progress_display_curve(base)
    assert values[-1] < cap  # the narrow old band was spent in2.4-4.8 seconds


@pytest.mark.parametrize("finished,owned", [(False, True), (False, False), (True, True)])
def test_only_owned_pending_worker_can_render_progress_without_result_reads(monkeypatch, finished, owned):
    from concurrent.futures import Future
    from screens import objects
    future = Future()
    if finished:
        future.set_result({})
    state = {"estimation_batch_future": future, "objects_estimation_future_id": "e" if owned else "other",
             "objects_estimation_seed_rows": [{"object_key": "one", "status": "running", "progress_percent": 1}]}
    monkeypatch.setattr(objects.st, "session_state", state)
    reads = []
    monkeypatch.setattr(objects, "_load_objects_screen_data", lambda _: reads.append("scoped read") or ({"rows": []}, None))
    result = objects._persisted_objects_state("e")
    assert reads == ([] if owned and not finished else ["scoped read"])
    if owned and not finished:
        assert result.data["rows"][0]["object_key"] == "one"
