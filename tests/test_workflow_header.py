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


def test_workflow_header_alignment_guard_uses_title_position_for_workflow_sticky_state():
    source = open("ui/js_guards.py").read()

    assert "def install_workflow_header_alignment_guard" in source
    assert 'parentDoc.querySelector("h1.workflow-title")' in source
    assert "getBoundingClientRect()" in source
    assert "actionsBaseCenter" in source
    assert "- appliedOffset" in source
    assert "translateY(${Math.round(offset * 100) / 100}px)" in source
    guard_source = source.split(
        "def install_workflow_header_alignment_guard", 1
    )[1].split("def install_company_metrics_input_guard", 1)[0]
    assert "restingTitleTop" in guard_source
    assert "titleRect.top < restingTitleTop - 1" in guard_source
    assert 'actions.dataset.workflowHeaderPinned = "true"' in guard_source
    assert "delete actions.dataset.workflowHeaderPinned" in guard_source
    assert 'parentDoc.addEventListener("scroll", scheduleAlign' in guard_source
