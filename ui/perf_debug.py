from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import html
import time

import streamlit as st


PERF_DEBUG_ENABLED = True
PERF_DEBUG_SHOW_PANEL = False


def start_python_perf_run(screen: str) -> None:
    if not PERF_DEBUG_ENABLED:
        return

    st.session_state._perf_run_started_at = time.perf_counter()
    st.session_state._perf_entries = []
    mark_python_perf("python render start", screen=screen)


def mark_python_perf(label: str, **fields: object) -> None:
    if not PERF_DEBUG_ENABLED:
        return

    started_at = st.session_state.get("_perf_run_started_at")
    if started_at is None:
        started_at = time.perf_counter()
        st.session_state._perf_run_started_at = started_at

    entries = st.session_state.setdefault("_perf_entries", [])
    elapsed_ms = (time.perf_counter() - float(started_at)) * 1000
    entries.append(
        {
            "label": label,
            "elapsed_ms": round(elapsed_ms, 1),
            "fields": {
                key: str(value)
                for key, value in fields.items()
                if value is not None
            },
        }
    )


def get_python_perf_entries() -> list[dict[str, object]]:
    if not PERF_DEBUG_ENABLED:
        return []

    entries = st.session_state.get("_perf_entries", [])
    if not isinstance(entries, list):
        return []
    return entries[-18:]


@contextmanager
def measure_python_perf(label: str, **fields: object) -> Iterator[None]:
    if not PERF_DEBUG_ENABLED:
        yield
        return

    started_at = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - started_at) * 1000
        mark_python_perf(label, duration_ms=f"{duration_ms:.1f}", **fields)


def render_python_perf_panel(screen: str) -> None:
    if not PERF_DEBUG_ENABLED or not PERF_DEBUG_SHOW_PANEL:
        return

    entries = st.session_state.get("_perf_entries", [])
    if not entries:
        return

    rows = []
    for entry in entries[-18:]:
        fields = entry.get("fields", {})
        field_text = " ".join(
            f"{html.escape(str(key))}={html.escape(str(value))}"
            for key, value in fields.items()
        )
        rows.append(
            '<div class="costerly-perf-row">'
            f'<span>{html.escape(str(entry.get("elapsed_ms", "")))}ms</span>'
            f'<strong>{html.escape(str(entry.get("label", "")))}</strong>'
            f'<em>{field_text}</em>'
            '</div>'
        )

    st.markdown(
        """
        <style>
        .costerly-python-perf-panel {
            position: fixed;
            right: 12px;
            bottom: 12px;
            z-index: 2147483200;
            width: 360px;
            max-height: 44vh;
            overflow: auto;
            box-sizing: border-box;
            padding: 10px 12px;
            border: 1px solid rgba(42, 31, 44, 0.18);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.94);
            color: #17131C;
            box-shadow: 0 10px 30px rgba(42, 31, 44, 0.14);
            font-family: var(--font-mono, monospace);
            font-size: 11px;
            line-height: 1.35;
        }

        .costerly-python-perf-title {
            margin: 0 0 8px 0;
            color: #8049C6;
            font-weight: 700;
            text-transform: uppercase;
        }

        .costerly-perf-row {
            display: grid;
            grid-template-columns: 58px 1fr;
            gap: 6px;
            padding: 3px 0;
            border-top: 1px solid rgba(42, 31, 44, 0.08);
        }

        .costerly-perf-row span {
            color: rgba(42, 31, 44, 0.58);
        }

        .costerly-perf-row strong {
            color: #17131C;
            font-weight: 700;
        }

        .costerly-perf-row em {
            grid-column: 2;
            color: rgba(42, 31, 44, 0.62);
            font-style: normal;
            word-break: break-word;
        }
        </style>
        <div class="costerly-python-perf-panel">
            <div class="costerly-python-perf-title">Python perf: __SCREEN__</div>
            __ROWS__
        </div>
        """.replace("__SCREEN__", html.escape(screen)).replace("__ROWS__", "".join(rows)),
        unsafe_allow_html=True,
    )
