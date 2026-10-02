from __future__ import annotations

from ui.layout import post_upload_header_html
from ui.object_detail_view import hero_html


def test_workflow_header_mark_precedes_the_full_title():
    html = post_upload_header_html("File Review")

    assert 'class="post-upload-title workflow-title"' in html
    assert 'class="workflow-title-primary"' in html
    assert 'class="workflow-title-mark"' in html
    assert 'class="workflow-title-text">File Review</span>' in html


def test_object_detail_keeps_black_label_and_lilac_object_name():
    html = hero_html({
        "name": "Display shelf",
        "quantity": 1,
        "confidence": "50",
        "preview_label": "Source preview",
    })

    assert 'class="workflow-title-text">Object:</span>' in html
    assert 'class="object-detail-object-name">Display shelf</span>' in html


def test_workflow_titles_use_brand_ink_and_only_object_names_use_accent():
    base_css = open("styles/base.py").read()
    review_css = open("styles/file_review.py").read()

    assert ".workflow-title" in base_css
    assert "color: var(--color-accent-dark) !important;" in base_css
    assert ".object-detail-object-name" in base_css
    assert "color: var(--color-accent) !important;" in base_css
    assert ".file-review-detected-title" in review_css


def test_authenticated_header_controls_are_fixed_at_the_top_without_workflow_scroll_code():
    base_css = open("styles/base.py").read()
    guard_source = open("ui/js_guards.py").read()

    controls_css = base_css.split(".st-key-costerly_header_controls {", 1)[1].split(
        ".st-key-costerly_header_controls:hover", 1
    )[0]
    assert "position: fixed !important;" in controls_css
    assert "top: 16px !important;" in controls_css
    assert "transform: none !important;" in controls_css
    assert "install_workflow_header_alignment_guard" not in guard_source
