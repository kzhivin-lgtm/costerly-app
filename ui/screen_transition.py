from __future__ import annotations

from ui.layout import post_upload_header_html


FILE_REVIEW_MARKER_ID = "costerly-file-review-screen-active"
OBJECTS_MARKER_ID = "costerly-objects-screen-active"

# This marker is intentionally presentation-neutral.  The transition runtime
# uses it only to correlate an interaction with the Streamlit screen that was
# visible before the next rerun begins.
SCREEN_MARKER_PREFIX = "costerly-screen-"


def screen_transition_marker_html(screen: str) -> str:
    """Return a non-layout marker for every rendered application screen."""
    safe_screen = "".join(
        char for char in str(screen or "unknown").lower() if char.isalnum() or char == "_"
    ) or "unknown"
    return (
        f'<div id="{SCREEN_MARKER_PREFIX}{safe_screen}" '
        f'data-costerly-screen="{safe_screen}" style="display:none"></div>'
    )


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
