from __future__ import annotations

import html
import json


PROCESSING_TITLE = "Reading your RFQ file..."
PROCESSING_SUBTITLE = "Detecting scope items for estimation"
PROCESSING_MARKER_ID = "costerly-processing-screen-active"


def post_upload_stage_html(
    *,
    title: str,
    subtitle: str | None = None,
    marker_id: str | None = None,
    stage_class: str | None = None,
    include_progress: bool = True,
    progress_value: float = 0.0,
    include_slow_message: bool = False,
    elapsed_seconds: float | None = None,
    complete: bool = False,
    processing_phase: str | None = None,
    expected_file_review_seconds: float | None = None,
    processing_plan: dict | None = None,
    processing_stage_id: str | None = None,
    processing_stage_started_at_ms: int | None = None,
    processing_run_token: str | None = None,
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

    timer_html = ""
    if elapsed_seconds is not None:
        seconds = max(0, int(elapsed_seconds))
        forecast_html = ""
        forecast_attr = ""
        if expected_file_review_seconds is not None:
            forecast_seconds = max(0, int(round(expected_file_review_seconds)))
            forecast_label = f"F: {forecast_seconds // 60:02d}:{forecast_seconds % 60:02d}"
            forecast_attr = f' data-processing-forecast-label="{forecast_label}"'
            forecast_html = (
                ' <span class="post-upload-stage__forecast">'
                f'({forecast_label})'
                '</span>'
            )
        timer_html = (
            f'<div class="post-upload-stage__timer"{forecast_attr}>'
            '<span data-processing-elapsed-label>'
            f'Elapsed {seconds // 60:02d}:{seconds % 60:02d}'
            '</span>'
            f'{forecast_html}'
            '</div>'
        )

    complete_attr = ' data-processing-complete="true"' if complete else ""
    phase_attr = (
        f' data-processing-phase="{html.escape(processing_phase)}"'
        if processing_phase
        else ""
    )
    expected_file_review_attr = ""
    if expected_file_review_seconds is not None:
        seconds = max(1.0, float(expected_file_review_seconds))
        expected_file_review_attr = f' data-expected-file-review-seconds="{seconds:g}"'
    plan_attr = ""
    if isinstance(processing_plan, dict):
        plan_attr = f" data-processing-plan='{html.escape(json.dumps(processing_plan, separators=(',', ':')), quote=True)}'"
    stage_id_attr = (
        f' data-processing-stage-id="{html.escape(processing_stage_id)}"'
        if processing_stage_id else ""
    )
    stage_started_attr = (
        f' data-processing-stage-started-at-ms="{int(processing_stage_started_at_ms)}"'
        if processing_stage_started_at_ms is not None else ""
    )
    run_token_attr = (
        f' data-processing-run-token="{html.escape(processing_run_token)}"'
        if processing_run_token else ""
    )

    return (
        f'<div class="{stage_classes}"{complete_attr}{phase_attr}{expected_file_review_attr}{plan_attr}{stage_id_attr}{stage_started_attr}{run_token_attr}>'
        '<div class="post-upload-stage__inner">'
        '<div class="post-upload-shell">'
        f'{marker_html}'
        f'<h1 class="post-upload-title">{html.escape(title)}</h1>'
        f'{subtitle_html}'
        '</div>'
        f'{progress_html}'
        f'{timer_html}'
        f'{slow_html}'
        '</div>'
        '</div>'
    )


def processing_stage_html(
    *,
    marker_id: str | None = None,
    include_progress: bool = True,
    progress_value: float = 0.0,
    elapsed_seconds: float | None = None,
    complete: bool = False,
    processing_phase: str = "upload",
    expected_file_review_seconds: float | None = None,
    processing_plan: dict | None = None,
    processing_stage_id: str | None = None,
    processing_stage_started_at_ms: int | None = None,
    processing_run_token: str | None = None,
) -> str:
    """Return the shared Processing stage HTML for instant and real screens."""
    return post_upload_stage_html(
        title=PROCESSING_TITLE,
        subtitle=PROCESSING_SUBTITLE,
        marker_id=marker_id,
        include_progress=include_progress,
        progress_value=progress_value,
        include_slow_message=False,
        elapsed_seconds=elapsed_seconds,
        complete=complete,
        processing_phase=processing_phase,
        expected_file_review_seconds=expected_file_review_seconds,
        processing_plan=processing_plan,
        processing_stage_id=processing_stage_id,
        processing_stage_started_at_ms=processing_stage_started_at_ms,
        processing_run_token=processing_run_token,
    )
