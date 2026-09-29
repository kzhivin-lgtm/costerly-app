from pathlib import Path


def test_activation_is_guarded_and_switches_only_after_candidate_layer_is_complete():
    sql = Path("db/sql/2026_09_29_activate_material_pricing_identity_v1.sql").read_text()

    assert "identity_count <> 2807" in sql
    assert "member_count <> 4436" in sql
    assert "price_count <> 2807" in sql
    assert "'material_identity_v3'" in sql
    assert "set status = 'retired'" in sql
    assert "begin;" in sql
    assert "commit;" in sql
