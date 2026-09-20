from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "costerly_company_labor_bridge",
    path=str(Path(__file__).with_name("company_labor_bridge_component")),
)


def company_labor_bridge(*, key: str) -> str | None:
    """Return an edit or remove request from the worker table actions."""
    value = _COMPONENT(key=key, default=None)
    return value if isinstance(value, str) else None
