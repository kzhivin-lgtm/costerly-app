from __future__ import annotations

from ui.layout import post_upload_header_html


FILE_REVIEW_MARKER_ID = "costerly-file-review-screen-active"
OBJECTS_MARKER_ID = "costerly-objects-screen-active"


def post_upload_transition_shell_html(
    *,
    title: str,
    subtitle: str | None = None,
    marker_id: str | None = None,
) -> str:
    """Return the shared post-upload header for client-side screen transitions."""
    return post_upload_header_html(
        title=title,
        subtitle=subtitle,
        marker_id=marker_id,
        class_name="post-upload-transition-header",
    )
