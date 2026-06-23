from __future__ import annotations

def apply_post_upload_css() -> None:
    """Keep the post-upload layout helper explicit at call sites.

    The actual CSS lives in styles/base.py so it is available before any
    post-upload screen renders. That prevents a late CSS injection jump.
    """
    return None
