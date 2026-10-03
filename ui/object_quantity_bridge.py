from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "costerly_object_quantity_bridge",
    path=str(Path(__file__).with_name("object_quantity_bridge_component")),
)


def object_quantity_bridge(*, key: str) -> str | None:
    """Return quantity edits from HTML workflow screens without direct DB access."""
    value = _COMPONENT(key=key, default=None)
    return value if isinstance(value, str) else None
