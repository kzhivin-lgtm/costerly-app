from pathlib import Path


def test_review_required_status_migration_preserves_existing_estimates():
    sql = (
        Path(__file__).parents[1]
        / "db/sql/2026_10_01_estimation_v2_review_status.sql"
    ).read_text().lower()

    assert "review_required" in sql
    assert "rfq_object_estimates_status_check" in sql
    assert "drop table" not in sql
    assert "truncate" not in sql
    assert "delete from" not in sql
