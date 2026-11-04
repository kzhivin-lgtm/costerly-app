from __future__ import annotations

FILE_REVIEW_MARKER_ID = "costerly-file-review-screen-active"
OBJECTS_MARKER_ID = "costerly-objects-screen-active"

# This marker is intentionally presentation-neutral.  The transition runtime
# uses it only to correlate an interaction with the Streamlit screen that was
# visible before the next rerun begins.
SCREEN_MARKER_PREFIX = "costerly-screen-"


def screen_transition_marker_html(
    screen: str, *, build_version: str | None = None,
) -> str:
    """Return a non-layout marker for every rendered application screen."""
    safe_screen = "".join(
        char for char in str(screen or "unknown").lower() if char.isalnum() or char == "_"
    ) or "unknown"
    safe_build = "".join(
        char for char in str(build_version or "unknown").lower()
        if char.isalnum() or char in {"_", "-", "."}
    ) or "unknown"
    return (
        f'<div id="{SCREEN_MARKER_PREFIX}{safe_screen}" '
        f'data-costerly-screen="{safe_screen}" '
        f'data-costerly-core-build="{safe_build}" style="display:none"></div>'
    )
