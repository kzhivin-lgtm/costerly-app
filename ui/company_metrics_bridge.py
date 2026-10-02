from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "costerly_company_metrics_bridge",
    path=str(Path(__file__).with_name("company_metrics_bridge_component")),
)


def company_metrics_bridge(*, key: str, mode: str = "metrics") -> str | None:
    """Return a company-settings snapshot without replacing the page."""
    value = _COMPONENT(key=key, default=None, mode=mode)
    return value if isinstance(value, str) else None
