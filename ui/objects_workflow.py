"""Objects V2 header and action feedback, independent of pricing-row rendering."""
from __future__ import annotations

from dataclasses import dataclass
import html
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1 as components

from ui.layout import post_upload_title_html
from ui.screen_transition import OBJECTS_MARKER_ID
from use_cases.final_approval import _json_safe


@dataclass(frozen=True)
class ObjectsHeaderSlots:
    metrics: object
    stages: object
    title: object = None


def project_title(name) -> str:
    name = str(name or '').strip()
    return 'Project' if not name or name.lower() in {'unknown', 'none', 'null', '—', '-'} else f'Project {name}'


def project_header_html(title, **kwargs):
    markup = post_upload_title_html(title, **kwargs)
    if title.startswith('Project '):
        markup = markup.replace(html.escape(title), '<span class="project-title-label">Project</span> '
                                '<span class="project-title-name">' + html.escape(title[8:]) + '</span>', 1)
    return markup


def prices_are_set(estimate_id: str | None, data: dict) -> bool:
    return bool(estimate_id) and st.session_state.get("objects_set_price_basis", {}).get(str(estimate_id)) == pricing_signature(data)


def stages_html(data: dict, *, prices_set: bool, proposal_ready: bool, confirmation_id: int = 0) -> str:
    rows = list(data.get("rows") or [])
    reviewed = sum(bool(row.get("reviewed")) for row in rows)
    all_reviewed = bool(rows) and reviewed == len(rows)
    current = 4 if proposal_ready else 1 if not all_reviewed else 3 if prices_set else 2
    labels = ("Review Objects", "Set Prices", "Generate Proposal")
    details = (f"{reviewed} of {len(rows)} reviewed" if rows else "", "", "")
    steps = []
    for number, (label, detail) in enumerate(zip(labels, details), 1):
        state = "complete" if number < current else "current" if number == current else "future"
        marker = "✓" if number < current else str(number)
        aria = ' aria-current="step"' if number == current else ""
        steps.append(f'<li data-stage="{number}" data-state="{state}"{aria}>'
                     f'<div class="objects-stage-group"><span class="objects-stage-marker">{marker}</span>'
                     f'<div><strong>{label}</strong>'
                     + (f'<small>{html.escape(detail)}</small>' if detail else "")
                     + '</div></div></li>')
    return f'<ol class="objects-workflow-stages" data-confirmation-id="{int(confirmation_id)}" aria-label="Proposal preparation">' + "".join(steps) + '</ol>'


def render_objects_header(title: str, render_header_controls: Callable[[], None] | None, *, show_metrics: bool = True) -> ObjectsHeaderSlots:
    # The exact existing title markup and primary container remain unchanged.
    with st.container(key="costerly_screen_header"):
        with st.container(key="costerly_screen_header_primary"):
            title_slot = st.empty()
            title_slot.markdown(project_header_html(title, class_name="objects-estimation-header", marker_id=OBJECTS_MARKER_ID, align_mark_left=True), unsafe_allow_html=True)
        with st.container(key="objects_header_toolbar", horizontal=True, vertical_alignment="center", gap=24):
            if render_header_controls is not None:
                with st.container(key="objects_header_controls", width="content"):
                    render_header_controls()
            metrics = None
            if show_metrics:
                with st.container(key="objects_header_metrics", width="content"):
                    metrics = st.empty()
        with st.container(key="objects_header_stages"):
            stages = st.empty()
            stages.html(stages_html({}, prices_set=False, proposal_ready=False))
    return ObjectsHeaderSlots(metrics, stages, title_slot)


def update_header(slots: ObjectsHeaderSlots, *, metrics_html: str, data: dict, estimate_id: str | None) -> None:
    if slots.title is not None:
        slots.title.markdown(project_header_html(project_title(data.get('project_name')), class_name='objects-estimation-header', marker_id=OBJECTS_MARKER_ID, align_mark_left=True), unsafe_allow_html=True)
    proposal_ready = bool(st.session_state.get("proposal_pdf_urls_by_estimate", {}).get(str(estimate_id)))
    if slots.metrics is not None:
        slots.metrics.html(
            '<div class="objects-technical-metrics">'
            + metrics_html +
            '<button type="button" class="objects-metrics-toggle" aria-expanded="true" '
            'aria-label="Collapse technical metrics"><span class="objects-metrics-chevron" aria-hidden="true"></span></button>'
            '</div>' if metrics_html else "", width="content",
        )
    slots.stages.html(stages_html(data, prices_set=prices_are_set(estimate_id, data), proposal_ready=proposal_ready,
                                 confirmation_id=st.session_state.get("objects_price_confirmation_id", 0)))


def install_actions_runtime(estimate_id: str) -> None:
    source = Path(__file__).with_name("objects_actions.js").read_text()
    source = source.replace("__ESTIMATE_ID__", json.dumps(estimate_id))
    components.html('<script>' + source + '</script>', height=0)


def pricing_signature(data: dict[str, Any]) -> str:
    """Identify the saved commercial basis, excluding progress/timing/UI state."""
    fields = ("object_key", "quantity", "self_cost_unit", "sale_price_unit", "sale_price_total", "reviewed", "status")
    basis = {
        "production_time_working_days": data.get('production_time_working_days'),
        "rows": [{field: row.get(field) for field in fields} for row in data.get("rows") or []],
        "project_costs": [{field: row.get(field) for field in ("object_key", "sale_price_unit", "sale_price_total")}
                          for row in data.get("project_costs") or []],
        "summary": {field: (data.get("summary") or {}).get(field) for field in ("project_price", "vat", "total", "vat_percent")},
    }
    return hashlib.sha256(json.dumps(_json_safe(basis), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
