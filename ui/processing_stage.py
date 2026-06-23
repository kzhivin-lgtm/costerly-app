from __future__ import annotations

import html


PROCESSING_TITLE = "Reading your RFQ package"
PROCESSING_SUBTITLE = "AI Detection is analyzing the uploaded file and detecting estimate-scope objects"
PROCESSING_MARKER_ID = "costerly-processing-screen-active"


def processing_stage_html(*, marker_id: str | None = None) -> str:
    """Return the shared Processing stage HTML for instant and real screens."""
    marker_html = ""
    if marker_id:
        marker_html = f'<div id="{html.escape(marker_id)}" style="display:none"></div>'

    return (
        '<div class="post-upload-stage">'
        '<div class="post-upload-stage__inner">'
        '<div class="post-upload-shell">'
        f'{marker_html}'
        f'<h1 class="post-upload-title">{html.escape(PROCESSING_TITLE)}</h1>'
        f'<div class="post-upload-subtitle">{html.escape(PROCESSING_SUBTITLE)}</div>'
        '</div>'
        '<div class="custom-progress-track">'
        '<div class="custom-progress-fill is-running" style="width:4%;"></div>'
        '</div>'
        '<div class="post-upload-stage__slow">'
        'Upload is taking longer than expected.'
        '</div>'
        '</div>'
        '</div>'
    )
