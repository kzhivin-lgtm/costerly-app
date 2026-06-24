from __future__ import annotations

import html


PROCESSING_TITLE = "Reading your RFQ package"
PROCESSING_SUBTITLE = "AI Detection is analyzing the uploaded file and detecting estimate-scope objects"
PROCESSING_MARKER_ID = "costerly-processing-screen-active"


def processing_stage_html(
    *,
    marker_id: str | None = None,
    include_progress: bool = True,
    progress_value: float = 0.04,
) -> str:
    """Return the shared Processing stage HTML for instant and real screens."""
    marker_html = ""
    if marker_id:
        marker_html = f'<div id="{html.escape(marker_id)}" style="display:none"></div>'

    progress_html = ""
    if include_progress:
        value = max(0.0, min(1.0, float(progress_value)))
        width = round(value * 100, 1)
        progress_html = (
            '<div class="custom-progress-track">'
            f'<div class="custom-progress-fill is-running" style="width:{width}%;"></div>'
            '</div>'
        )

    return (
        '<div class="post-upload-stage">'
        '<div class="post-upload-stage__inner">'
        '<div class="post-upload-shell">'
        f'{marker_html}'
        f'<h1 class="post-upload-title">{html.escape(PROCESSING_TITLE)}</h1>'
        f'<div class="post-upload-subtitle">{html.escape(PROCESSING_SUBTITLE)}</div>'
        '</div>'
        f'{progress_html}'
        '<div class="post-upload-stage__slow">'
        'Upload is taking longer than expected.'
        '</div>'
        '</div>'
        '</div>'
    )
