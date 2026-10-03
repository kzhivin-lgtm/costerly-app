from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "costerly_object_detail_draft_bridge",
    path=str(Path(__file__).with_name("object_detail_draft_bridge_component")),
)


def object_detail_draft_bridge(*, key: str) -> str | None:
    """Return an Object Detail draft snapshot without a full page reload."""
    value = _COMPONENT(key=key, default=None)
    return value if isinstance(value, str) else None
