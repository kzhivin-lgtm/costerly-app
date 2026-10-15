from pathlib import Path


def test_israel_reference_standard_raw_mdf_20_migration_uses_mdf_19_plus_ten_percent():
    sql = Path("db/sql/2026_10_15_add_israel_reference_standard_raw_mdf_20.sql").read_text()

    assert "gcm_v1_mdf_standard_standard_mdf_raw_20_mm" in sql
    assert "gcm_v1_mdf_standard_standard_mdf_raw_19_mm" in sql
    assert "round(source_price.price_typical * 1.10, 6)" in sql
    assert "'board_type'::text, to_jsonb('mdf'::text)" in sql
    assert "'surface'::text, to_jsonb('raw'::text)" in sql
    assert "'thickness'::text, to_jsonb(20.0)" in sql
    assert "standard_2400x1220" not in sql
