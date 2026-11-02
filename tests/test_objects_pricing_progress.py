from datetime import UTC, datetime, timedelta

from ui.objects_pricing import smooth_progress_percent


def test_unconfirmed_geometry_progress_cannot_visually_reach_bom_checkpoint():
    row = {
        "progress_percent": 1,
        "progress_updated_at": (datetime.now(UTC) - timedelta(minutes=10)).isoformat(),
    }

    assert smooth_progress_percent(row) == 45
