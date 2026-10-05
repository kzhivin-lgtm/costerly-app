from pathlib import Path


SCREEN_PATH = Path(__file__).parents[1] / "screens/company_profile.py"


def test_review_queue_has_no_source_wide_vat_gate():
    source = SCREEN_PATH.read_text()
    queue = source[
        source.index("def _render_price_source_review_queue"):
        source.index("def _render_price_source_details")
    ]

    assert "Complete internal source settings" not in queue
    assert "price_source_defaults_form" not in queue
    assert "apply_price_source_defaults" not in queue
    assert "Needs review" in queue
