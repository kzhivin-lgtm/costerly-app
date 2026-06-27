from __future__ import annotations

import html


PROCESSING_TITLE = "Reading your RFQ package"
PROCESSING_SUBTITLE = "AI Detection is analyzing the uploaded file and detecting estimate-scope objects"
PROCESSING_MARKER_ID = "costerly-processing-screen-active"


def post_upload_stage_html(
    *,
    title: str,
    subtitle: str | None = None,
    marker_id: str | None = None,
    stage_class: str | None = None,
    include_progress: bool = True,
    progress_value: float = 0.04,
    include_slow_message: bool = True,
) -> str:
    """Return the shared fixed-origin post-upload stage HTML."""
    stage_classes = "post-upload-stage"
    if stage_class:
        stage_classes = f"{stage_classes} {html.escape(stage_class)}"

    marker_html = ""
    if marker_id:
        marker_html = f'<div id="{html.escape(marker_id)}" style="display:none"></div>'

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="post-upload-subtitle">{html.escape(subtitle)}</div>'

    progress_html = ""
    if include_progress:
        value = max(0.0, min(1.0, float(progress_value)))
        width = round(value * 100, 1)
        progress_html = (
            '<div class="custom-progress-track">'
            f'<div class="custom-progress-fill is-running" style="width:{width}%;"></div>'
            '</div>'
        )

    slow_html = ""
    if include_slow_message:
        slow_html = (
            '<div class="post-upload-stage__slow">'
            'Upload is taking longer than expected.'
            '</div>'
        )

    return (
        f'<div class="{stage_classes}">'
        '<div class="post-upload-stage__inner">'
        '<div class="post-upload-shell">'
        f'{marker_html}'
        f'<h1 class="post-upload-title">{html.escape(title)}</h1>'
        f'{subtitle_html}'
        '</div>'
        f'{progress_html}'
        f'{slow_html}'
        '</div>'
        '</div>'
    )


def processing_stage_html(
    *,
    marker_id: str | None = None,
    include_progress: bool = True,
    progress_value: float = 0.04,
) -> str:
    """Return the shared Processing stage HTML for instant and real screens."""
    return post_upload_stage_html(
        title=PROCESSING_TITLE,
        subtitle=PROCESSING_SUBTITLE,
        marker_id=marker_id,
        include_progress=include_progress,
        progress_value=progress_value,
        include_slow_message=True,
    )
