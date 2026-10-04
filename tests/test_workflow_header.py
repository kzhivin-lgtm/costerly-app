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


def test_file_review_object_preview_matches_the_name_and_ignore_control_stack():
    review_source = open("screens/file_review.py").read()
    review_css = open("styles/file_review.py").read()

    assert "'<div class=\"file-review-top-label\">Object name</div>'" not in review_source
    assert 'st.columns([7, 1.4], gap="small", vertical_alignment="top")' in review_source
    assert "width: 100px;\n            height: 100px;" in review_css


def test_file_review_does_not_need_a_stale_upload_navigation_override():
    review_css = open("styles/file_review.py").read()

    assert ".file-review-title-card-shell-marker" in review_css
    assert ".st-key-costerly_header_controls" not in review_css


def test_workflow_header_alignment_guard_uses_live_dom_centers_without_scroll_events():
    source = open("ui/js_guards.py").read()

    assert "def install_workflow_header_alignment_guard" in source
    assert "const titleSelector = __TITLE_SELECTOR__;" in source
    assert "title: activeElement(titleSelector)" in source
    assert "querySelectorAll(selector)" in source
    assert "element.closest('[data-stale=\"true\"]')" in source
    assert 'actions.style.removeProperty("transform")' in source
    assert 'attributeFilter: ["data-stale"]' in source
    assert "getBoundingClientRect()" in source
    assert "actionsBaseCenter" in source
    assert "- appliedOffset" in source
    assert "translateY(${Math.round(offset * 100) / 100}px)" in source
    assert 'addEventListener("scroll"' not in source.split(
        "def install_workflow_header_alignment_guard", 1
    )[1].split("def install_company_metrics_input_guard", 1)[0]


def test_each_post_detail_screen_aligns_to_its_own_title():
    objects_source = open("screens/objects.py").read()
    detail_source = open("screens/object_detail.py").read()

    assert '".objects-estimation-header h1.workflow-title"' in objects_source
    assert 'install_workflow_header_alignment_guard("h1.object-detail-title")' in detail_source
