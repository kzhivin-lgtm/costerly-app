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


def test_review_editor_restricts_resolution_to_price_and_unit():
    source = SCREEN_PATH.read_text()
    editor = source[
        source.index("def _render_price_source_row_editor"):
        source.index("def _render_price_source_row_remove_confirmation")
    ]
    queue = source[
        source.index("def _render_price_source_review_queue"):
        source.index("def _render_price_source_details")
    ]

    assert "review_only: bool = False" in editor
    assert "Source price ({'incl' if fixed_values['vat_mode'] == 'included' else 'ex'} VAT)" in editor
    assert 'return "Unit" if _price_source_review_field(row) == "unit" else "Price"' in source
    assert "price-source-review-required-label" in editor
    assert "_render_price_source_row_editor(access, source, row, review_only=True)" in queue
